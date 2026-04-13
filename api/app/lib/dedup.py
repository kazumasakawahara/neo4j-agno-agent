"""Text normalization utilities for Neo4j MERGE key consistency.

These functions ensure that names and text from different input sources
(UI forms, voice intake, narrative extraction) produce identical keys
before being written to or matched against the graph database.
"""
import logging
import re
import unicodedata
from typing import Any

from app.lib.embedding import embed_text
from app.lib.db_operations import run_query

logger = logging.getLogger(__name__)

# Map label → text property used in vector index
_LABEL_TEXT_PROPERTY: dict[str, str] = {
    "NgAction": "action",
    "CarePreference": "instruction",
    "SupportLog": "action",
}

# Japanese honorific suffixes to strip from the end of names.
# Ordered longest-first so "先生" is tried before single-char suffixes.
_HONORIFIC_SUFFIXES = ["先生", "ちゃん", "さん", "くん", "様", "氏"]

# Regex range for fullwidth ASCII: U+FF01 (！) to U+FF5E (～)
_FULLWIDTH_OFFSET = 0xFF01 - 0x21  # = 65248


def normalize_text(text: str | None) -> str:
    """Normalize a text string for consistent storage and comparison.

    Steps applied in order:
    1. Return "" for None or empty input.
    2. Unicode NFC normalization (combines decomposed characters).
    3. Fullwidth ASCII (U+FF01–U+FF5E) → halfwidth (U+0021–U+007E).
    4. Collapse consecutive whitespace to a single ASCII space.
    5. Strip leading/trailing whitespace.
    """
    if not text:
        return ""

    # NFC normalization: NFD "か" + combining dakuten → NFC "が"
    text = unicodedata.normalize("NFC", text)

    # Fullwidth ASCII → halfwidth using character-by-character translation
    chars = []
    for ch in text:
        cp = ord(ch)
        if 0xFF01 <= cp <= 0xFF5E:
            chars.append(chr(cp - _FULLWIDTH_OFFSET))
        else:
            chars.append(ch)
    text = "".join(chars)

    # Collapse whitespace and strip
    text = re.sub(r"\s+", " ", text).strip()

    return text


CONDITION_ALIASES: dict[str, list[str]] = {
    "自閉症スペクトラム障害": [
        "ASD",
        "自閉スペクトラム",
        "自閉スペクトラム症",
        "自閉症",
        "アスペルガー症候群",
        "アスペルガー",
        "広汎性発達障害",
        "PDD",
    ],
    "注意欠如多動症": ["ADHD", "注意欠陥多動性障害", "ADD", "注意欠如多動性障害"],
    "知的障害": ["知的発達症", "精神遅滞", "知的発達障害"],
    "てんかん": ["癲癇", "epilepsy"],
    "ダウン症候群": ["ダウン症", "21トリソミー", "Down症候群"],
    "脳性麻痺": ["CP", "脳性まひ"],
}

# Reverse lookup: alias.lower() → canonical name
_CONDITION_ALIAS_LOOKUP: dict[str, str] = {
    alias.lower(): canonical
    for canonical, aliases in CONDITION_ALIASES.items()
    for alias in aliases
}
# Also map canonical names to themselves (case-insensitive lookup)
_CONDITION_ALIAS_LOOKUP.update(
    {canonical.lower(): canonical for canonical in CONDITION_ALIASES}
)


def normalize_condition(name: str | None) -> str:
    """Normalize a medical condition name to its canonical Japanese term.

    Applies normalize_text() first, then resolves known aliases (case-insensitive)
    to their canonical names using CONDITION_ALIASES. Unknown names pass through
    unchanged after text normalization.

    Examples:
        "ASD"             → "自閉症スペクトラム障害"
        "asd"             → "自閉症スペクトラム障害"
        "自閉スペクトラム" → "自閉症スペクトラム障害"
        "ADHD"            → "注意欠如多動症"
        "希少疾患X"        → "希少疾患X"
    """
    text = normalize_text(name)
    if not text:
        return ""
    return _CONDITION_ALIAS_LOOKUP.get(text.lower(), text)


def normalize_name(name: str | None) -> str:
    """Normalize a Japanese personal name for MERGE key consistency.

    Applies normalize_text() first, then strips common honorific suffixes
    (さん, 様, くん, ちゃん, 氏, 先生) from the end of the string only.

    Examples:
        "田中さん"  → "田中"
        "田中様"    → "田中"
        "さんま"    → "さんま"   (さん is not at the very end)
        "ＡＢＣさん" → "ABC"
    """
    text = normalize_text(name)
    if not text:
        return ""

    for suffix in _HONORIFIC_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break  # strip at most one suffix

    return text


async def find_semantic_duplicates(
    text: str,
    label: str,
    index_name: str,
    threshold: float = 0.85,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Search for semantically similar existing nodes using vector index.

    Returns list of dicts with keys: text, score, nodeId.
    Only results with score >= threshold are returned.

    Args:
        text: The input text to search for duplicates of.
        label: The Neo4j node label (e.g. "NgAction", "CarePreference").
        index_name: The name of the Neo4j vector index to query.
        threshold: Minimum cosine similarity score (0–1). Defaults to 0.85.
        top_k: Maximum candidates to retrieve from the index. Defaults to 5.

    Returns:
        List of matching node dicts, ordered by score descending. Empty list
        on empty input, missing embedding, or any error.
    """
    if not text:
        return []

    try:
        embedding = await embed_text(text, task_type="SEMANTIC_SIMILARITY")
        if embedding is None:
            return []

        text_prop = _LABEL_TEXT_PROPERTY.get(label, "text")
        cypher = (
            "CALL db.index.vector.queryNodes($index_name, $top_k, $embedding) "
            "YIELD node, score "
            "WHERE score >= $threshold "
            f"RETURN node.{text_prop} AS text, score, elementId(node) AS nodeId "
            "ORDER BY score DESC"
        )
        rows = run_query(
            cypher,
            {
                "index_name": index_name,
                "top_k": top_k,
                "embedding": embedding,
                "threshold": threshold,
            },
        )
        # Filter by threshold in Python as a safety net (Cypher WHERE also filters,
        # but this guards against driver versions that may not pass parameters to YIELD)
        return [r for r in (rows or []) if r.get("score", 0) >= threshold]

    except Exception as exc:
        logger.warning(
            "find_semantic_duplicates failed for label=%s index=%s: %s",
            label,
            index_name,
            exc,
        )
        return []
