# Developer Notes & Troubleshooting

## Feature: Deepening Memory (Vector RAG) - 2026-02-02

### Summary
Implemented semantic search using Neo4j Vector Index and Google Gemini Embeddings (`text-embedding-004`). This allows agents to recall past logs based on context (e.g., "refused bath") even if exact keywords differ.

### 🐛 Challenges & Solutions

#### 1. Gemini SDK API Key
**Issue**: `google.generativeai` SDK strictly requires the environment variable `GOOGLE_API_KEY`. Our project was using `GEMINI_API_KEY`.
**Fix**: Added an alias in `.env`.
```bash
GOOGLE_API_KEY=${GEMINI_API_KEY}
```

#### 2. Neo4j Toolkit Imports
**Issue**: Circular imports or incorrect path referencing when importing `Neo4jToolkit` inside new tools (`LogToolkit`, `MemoryToolkit`).
**Fix**: Always use the full package path `from tools.neo4j_toolkit import Neo4jToolkit`. Also, instantiate the toolkit (`neo4j = Neo4jToolkit()`) to access the driver wrapper properly, rather than trying to import un-static methods directly.

#### 3. Data Consistency (Client Names)
**Issue**: Vector search queries returned 0 results even after successful logging.
**Cause**: The verification script used "Yamada Kenta" (English), but the database contained "山田健太" (Japanese). `MATCH (c:Client)` failed silently, so the log was never linked to a client node, making it unretrievable by the standard search query.
**Fix**:
-   Always verify the exact `c.name` in the database (`check_clients.py`).
-   Added `print(record)` debugging in `LogToolkit` to catch empty creation results immediately.

#### 4. Agent Instruction Drift
**Issue**: During `InputAgent` update, the critical instruction `extract_narrative_data` was accidentally overwritten.
**Fix**: Restored the missing instruction.
**Lesson**: When updating agent instructions, always `diff` against the previous version to ensure core capabilities aren't lost.

### 📚 Resource
-   **Embedding Model**: `models/text-embedding-004` (768 dimensions)
-   **Vector Index**: `support_log_vector_index` on `:SupportLog(embedding)`
