"""Text normalization utilities for Neo4j MERGE key consistency.

These functions ensure that names and text from different input sources
(UI forms, voice intake, narrative extraction) produce identical keys
before being written to or matched against the graph database.
"""
import re
import unicodedata

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
