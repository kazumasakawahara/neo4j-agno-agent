"""Deduplication utilities for Neo4j nodes.

Text normalization functions (normalize_name, normalize_text, normalize_condition)
are defined in app.lib.normalize to avoid circular imports with db_operations.
They are re-exported here for backward compatibility.
"""
import logging
from typing import Any

from app.lib.embedding import embed_text
from app.lib.db_operations import run_query

# Re-export normalization functions from normalize module for backward compat.
from app.lib.normalize import (  # noqa: F401
    normalize_name,
    normalize_text,
    normalize_condition,
    CONDITION_ALIASES,
)

logger = logging.getLogger(__name__)

# Map label → text property used in vector index
_LABEL_TEXT_PROPERTY: dict[str, str] = {
    "NgAction": "action",
    "CarePreference": "instruction",
    "SupportLog": "action",
}


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
