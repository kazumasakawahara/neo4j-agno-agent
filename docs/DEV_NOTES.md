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
-   ~~**Embedding Model**: `models/text-embedding-004` (768 dimensions)~~ → **現在は `gemini-embedding-2-preview` を使用**（`lib/embedding.py`）
-   ~~**Vector Index**: `support_log_vector_index` on `:SupportLog(embedding)`~~ → **現在は4つのベクトルインデックス**（`docs/NEO4J_SCHEMA_CONVENTION.md` 参照）

---

## Feature: Multimodal Embedding & Semantic Search - 2026-03-12

### Summary
Gemini Embedding 2（`gemini-embedding-2-preview`）を使ったマルチモーダルセマンティック検索を実装。テキスト・画像・PDFを768次元の単一ベクトル空間に統合し、Neo4j Vector Index で検索可能にした。

### アーキテクチャ
- **Embedding生成**: `lib/embedding.py` — テキスト/画像/マルチモーダル embedding、OCR、バッチ処理
- **自動付与**: `lib/db_new_operations.py` — `register_to_database()` / `register_support_log()` でノード登録時にベストエフォートで自動付与
- **OCRフォールバック**: `lib/file_readers.py` — pdfplumber でテキストが少ないPDFは Gemini OCR にフォールバック。画像ファイル（jpg/png/webp/heic）も対応
- **バックフィル**: `scripts/backfill_embeddings.py` — 既存ノードへの一括付与CLI
- **検索UI**: `pages/semantic_search.py` — Streamlit ページ

### 設計判断
- **768次元**を選択（MRL: Matryoshka Representation Learning）。ストレージ効率と精度のバランス
- **`db.create.setNodeVectorProperty()`** を使用。通常の `SET n.embedding = $vec` ではベクトルインデックスに認識されない
- **ベストエフォート**: embedding生成失敗は登録処理全体をブロックしない
- **タスクタイプ使い分け**: ドキュメント登録時は `RETRIEVAL_DOCUMENT`、検索クエリ時は `RETRIEVAL_QUERY`

### 注意点
- `GEMINI_API_KEY` または `GOOGLE_API_KEY` が `.env` に必要
- バックフィル時はレートリミットに注意（`--batch-size` で調整可能）
