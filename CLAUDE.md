# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**親亡き後支援データベース (Post-Parent Support & Advocacy Graph)**

A Neo4j-based graph database system for managing support information for individuals with intellectual/developmental disabilities, designed to preserve parental tacit knowledge for emergency situations and post-parent care continuity.

### Core Manifesto (5 Values + 7 Pillars)

**5 Values:**
1. **Dignity (尊厳)**: Record individuals as humans with history and will
2. **Safety (安全)**: Emergency-first data structure with prohibition priorities
3. **Continuity (継続性)**: Maintain care quality across support staff transitions
4. **Resilience (強靭性)**: Visualize backup systems for parental function replacement
5. **Advocacy (権利擁護)**: Link voiceless voices to legal backing

**7 Data Pillars:**
1. Identity & Narrative (本人性)
2. Care Instructions (ケアの暗黙知)
3. Safety Net (危機管理ネットワーク)
4. Legal Basis (法的基盤)
5. Parental Transition (親の機能移行)
6. Financial Safety (金銭的安全)
7. Multi-Agency Collaboration (多機関連携)

See `agents/MANIFESTO.md` for the complete v4.0 manifesto.

## Architecture

### Next.js + FastAPI Architecture (v2.0)

| Layer | Tool | Port | Purpose |
|-------|------|------|---------|
| Frontend | Next.js + shadcn/ui | 3001 | モダン業務UI（全9画面） |
| API Server | FastAPI | 8001 | REST + WebSocket バックエンド |
| MCP Server | server.py | - | Claude Desktop 連携（既存） |
| SOS API | FastAPI | 8080 | 緊急通知 + LINE（既存） |
| Mobile API | FastAPI | 8080 | モバイル入力（既存） |

#### 起動方法（Next.js版）
```bash
# API サーバー
cd api && uv run uvicorn app.main:app --reload --port 8001

# フロントエンド
cd frontend && pnpm dev --port 3001

# ブラウザで http://localhost:3001 を開く
```

> **Note**: 旧 Streamlit UI (`app.py`, `app_narrative.py`, `app_quick_log.py`) は `archive/` に退避済み。

### 3-Layer Workflow (Legacy Reference)

| Layer | Tool | Purpose | Color |
|-------|------|---------|-------|
| 1 | `app_narrative.py` (Streamlit) | Initial registration, bulk data entry | Blue #1565C0 |
| 2 | `app_quick_log.py` (Streamlit) | Quick daily logging (30 seconds) | Orange #E65100 |
| 3 | Claude Desktop + Skills + Neo4j MCP | Analysis, proposals, complex operations | Purple #6A1B9A |

### System Components

1. **Dashboard UI** (`app.py`):
   - 4-section navigation: ホーム / 記録・登録 / 管理 / 活用
   - `pages/home.py`: Dashboard with stats, 3-layer cards, renewal alerts
   - `pages/client_list.py`: Searchable client list with detail cards
   - `pages/claude_guide.py`: Claude Desktop usage guide with copyable prompts

2. **Data Entry**:
   - `app_narrative.py`: Streamlit data entry with narrative-style input and file upload
   - `app_quick_log.py`: Mobile-friendly quick logging (exceptional events only)
   - `app_ui.py`: Agno/Gemini chat-based support

3. **Backend Services**:
   - `server.py`: MCP server for Claude Desktop integration (40+ tools)
   - `sos/api_server.py`: FastAPI for SOS emergency notifications with LINE integration
   - `mobile/api_server.py`: FastAPI for mobile narrative input (Gemini extraction + Neo4j)

4. **Shared Libraries** (`lib/`):
   - `db_operations.py`: Neo4j connection, query execution, data registration, dashboard stats
   - `ai_extractor.py`: Gemini 2.0-based text-to-structured-data extraction
   - `file_readers.py`: Multi-format file parsing (docx, xlsx, pdf, txt)
   - `utils.py`: Date parsing, session state management

5. **Agent Protocols** (`agents/`):
   - `MANIFESTO.md`: Unified manifesto v4.0 (5 values, 7 pillars, 4 AI rules)
   - `ROUTING.md`: Guide for choosing between skills and Neo4j MCP
   - `protocols/`: Emergency, Parent Down, Onboarding, Handover
   - `workflows/`: Visit Preparation, Resilience Report, Renewal Check
   - `base.py`, `unified_support_agent.py`: Agno/Gemini agent (used by app_ui.py)

6. **Skills** (`claude-skills/` → `~/.claude/skills/` via symlink):
   - `neo4j-support-db/`: 障害福祉DB用Cypherテンプレート（8種、port 7687）
   - `livelihood-support/`: 生活困窮者DB用Cypherテンプレート（12種、port 7688）
   - `provider-search/`: 事業所検索・口コミ用Cypherテンプレート（9種、port 7687）
   - `emergency-protocol/`: 緊急時対応プロトコル（DB非依存）
   - `ecomap-generator/`: エコマップ生成（Mermaid/SVG）
   - Install: `./setup.sh --skills` creates symlinks from repo to `~/.claude/skills/`

7. **Ecomap Generator** (`skills/ecomap_generator/`):
   - `drawio_engine.py`: draw.io XML generation with radial layout algorithm
   - 4 templates: full_view, support_meeting, emergency, handover
   - 9 category styles with color-coded nodes
   - Fallback to sample data when DB unavailable

### AI Models

- **Gemini 2.0 Flash**: Narrative text structuring (extraction) via `lib/ai_extractor.py`
- **Gemini Embedding 2** (`gemini-embedding-2-preview`): Multimodal embedding generation via `lib/embedding.py`
- **Claude Desktop**: Natural language database queries via Skills + Neo4j MCP (see `agents/ROUTING.md`)

### Embedding & Semantic Search (`lib/embedding.py`)

Gemini Embedding 2 によるマルチモーダルセマンティック検索機能。768次元ベクトルを Neo4j Vector Index に格納。

**主要関数:**
- `embed_text(text, task_type, dimensions)` — テキスト → 768次元ベクトル
- `embed_texts_batch(texts)` — 複数テキスト一括embedding
- `embed_image(image_path)` — 画像 → ベクトル
- `ocr_with_gemini(file_path)` — Gemini 2.0 Flash でスキャンPDF/手書きOCR
- `semantic_search(query_text, index_name, top_k)` — 汎用セマンティック検索
- `search_support_logs_semantic(query_text, top_k, client_name)` — 支援記録検索
- `search_ng_actions_semantic(query_text, top_k)` — 禁忌事項検索
- `embed_audio(audio_path)` — 音声ファイル → ネイティブembedding（最大80秒、文字起こし不要）
- `transcribe_audio(audio_path)` — Gemini 2.0 Flash で音声→テキスト文字起こし
- `search_meeting_records_semantic(query_text, top_k, client_name)` — 面談記録検索（テキスト/音声インデックス切替可）
- `register_meeting_record(audio_path, client_name, ...)` — 音声→embedding+文字起こし+Neo4j登録の一括パイプライン
- `ensure_vector_indexes()` — ベクトルインデックス一括作成（冪等）
- `get_embedding_stats()` — embedding付与率の統計
- `build_client_summary_text(client_name)` — Client関連ノード（Condition, NgAction, CarePreference, SupportLog）を集約して概要テキスト構築
- `embed_client_summary(client_name)` — 概要テキストからtask_type="CLUSTERING"でsummaryEmbedding生成・付与
- `find_similar_clients(client_name, top_k)` — summaryEmbeddingベクトルインデックスで類似クライアント検索
- `search_similar_clients_by_text(description, top_k)` — テキスト説明から類似クライアント検索（新規利用者の特徴入力用）

**自動付与:** `register_to_database()` / `register_support_log()` でノード登録時に SupportLog, NgAction, CarePreference に自動付与（ベストエフォート）。Client関連ノード（Client, Condition, NgAction, CarePreference）登録時にはsummaryEmbeddingも自動再計算。

**バックフィル:** `uv run python scripts/backfill_embeddings.py --all`（Client含む）

**ベクトルインデックス（6つ）:**

| Index Name | Label | Property | Dimensions |
|------------|-------|----------|------------|
| `support_log_embedding` | SupportLog | embedding | 768 |
| `care_preference_embedding` | CarePreference | embedding | 768 |
| `ng_action_embedding` | NgAction | embedding | 768 |
| `client_summary_embedding` | Client | summaryEmbedding | 768 |
| `meeting_record_embedding` | MeetingRecord | embedding | 768 |
| `meeting_record_text_embedding` | MeetingRecord | textEmbedding | 768 |

## Common Development Tasks

### Environment Setup

```bash
uv sync
docker-compose up -d
cat > .env << EOF
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
GEMINI_API_KEY=your_api_key_here
EOF
```

### Running Applications

```bash
# Dashboard (port 8501) - primary entry point
uv run streamlit run app.py

# MCP Server for Claude Desktop
# Configure in claude_desktop_config.json (see docs/ADVANCED_USAGE.md)

# SOS Emergency API Server (port 8000)
cd sos && uv run python api_server.py

# Mobile Narrative API (port 8080)
uv run python mobile/api_server.py
```

### Database Operations

```bash
# Access Neo4j Browser
open http://localhost:7474

# Run Cypher queries via Python
from lib.db_operations import run_query
result = run_query("MATCH (c:Client) RETURN c.name LIMIT 10")
```

## Key Implementation Patterns

### AI Data Extraction Flow

1. User inputs narrative text or uploads file (Word/Excel/PDF)
2. `lib/file_readers.py` extracts raw text
3. `lib/ai_extractor.py` uses Gemini with `EXTRACTION_PROMPT` to structure data
4. `lib/db_operations.py::register_to_database()` writes to Neo4j with Cypher

### Emergency Information Priority

**Critical**: NgAction (禁忌事項) nodes with `riskLevel` are queried first in emergency scenarios:
- `LifeThreatening`: Highest priority (life-threatening)
- `Panic`: Medium priority (panic triggers)
- `Discomfort`: Lower priority (discomfort causes)

### Skills & Neo4j MCP (Layer 3)

Five skills provide Cypher templates executed via the generic neo4j MCP:

| Skill | Neo4j Port | Templates | Purpose |
|-------|-----------|-----------|---------|
| neo4j-support-db | 7687 | 10 read | 障害福祉クライアント管理 |
| livelihood-support | 7688 | 12 read | 生活困窮者自立支援 |
| provider-search | 7687 | 6 read + 3 write | 事業所検索・口コミ |
| emergency-protocol | N/A | N/A | 緊急時プロトコル |
| ecomap-generator | N/A | N/A | エコマップ生成 |

See `agents/ROUTING.md` for guidance on choosing between skills.
See `docs/NEO4J_SCHEMA_CONVENTION.md` for Neo4j naming conventions (required for all LLMs/agents).

## Database Schema Notes

### Node Types

**Core Entities**:
- `:Client`: Central node (name, dob, bloodType, summaryEmbedding[768])
- `:NgAction`: Prohibited actions with risk levels (safety-critical, embedding[768])
- `:CarePreference`: Recommended care instructions (embedding[768])
- `:Condition`: Medical diagnoses/characteristics

**Support Network**:
- `:KeyPerson`: Emergency contacts with priority and relationship
- `:Guardian`: Legal guardians
- `:Hospital`: Medical providers
- `:Supporter`: Support staff who log daily care records
- `:SupportLog`: Daily support records with effectiveness tracking, type, duration, nextAction, embedding[768]
- `:MeetingRecord`: 面談音声記録 (date, title, duration, filePath, mimeType, transcript, note, embedding[768], textEmbedding[768])

**Legal Documentation**:
- `:Certificate`: 手帳・受給者証 with `nextRenewalDate`
- `:PublicAssistance`: 公的扶助

**Financial Safety** (livelihood-support, port 7688):
- `:EconomicRisk`: Economic exploitation risks
- `:MoneyManagement`: Financial management capability records

### Relationship Patterns

> **命名規則の詳細は `docs/NEO4J_SCHEMA_CONVENTION.md` を参照してください。**
> 複数 LLM がデータベースに書き込むため、命名規則の厳守が必要です。

```cypher
(:Client)-[:HAS_CONDITION {diagnosedDate}]->(:Condition)
(:Client)-[:MUST_AVOID]->(:NgAction)-[:IN_CONTEXT]->(:Condition)
(:Client)-[:REQUIRES]->(:CarePreference)
(:Client)-[:HAS_KEY_PERSON {rank: 1}]->(:KeyPerson)
(:Client)-[:HAS_LEGAL_REP]->(:Guardian)
(:Client)-[:HAS_CERTIFICATE {issuedDate, status}]->(:Certificate)
(:Client)-[:TREATED_AT {since, status}]->(:Hospital)
(:Supporter)-[:LOGGED]->(:SupportLog)-[:ABOUT]->(:Client)
(:SupportLog)-[:FOLLOWS]->(:SupportLog)
(:Supporter)-[:RECORDED]->(:MeetingRecord)-[:ABOUT]->(:Client)
(:AuditLog)-[:AUDIT_FOR]->(:Client)
```

**命名規則**: ノード=PascalCase / リレーション=UPPER_SNAKE_CASE / プロパティ=camelCase

## File Organization

```
neo4j-agno-agent/
├── api/                    # NEW: FastAPI + Gemini バックエンド
│   ├── app/
│   │   ├── agents/         # Gemini Agent + Safety First
│   │   ├── routers/        # 9 API ルーター
│   │   ├── lib/            # 共有ライブラリ（lib/から移植）
│   │   └── schemas/        # Pydantic スキーマ
│   └── tests/
├── frontend/               # NEW: Next.js + shadcn/ui
│   ├── src/app/            # 9ページ
│   └── src/components/     # UIコンポーネント
├── archive/                # 旧Streamlit UI（退避済み）
├── server.py               # MCP server for Claude Desktop
├── main.py                 # CLI agent entry point (legacy)
├── pages/                  # Dashboard sub-pages (archived)
│   ├── home.py             # Dashboard home with stats & workflow cards
│   ├── client_list.py      # Searchable client list
│   ├── claude_guide.py     # Claude Desktop usage guide
│   └── ecomap.py           # Ecomap generation (draw.io)
├── agents/                 # Agent protocols & manifesto
│   ├── MANIFESTO.md        # Unified manifesto v4.0
│   ├── ROUTING.md          # MCP server selection guide
│   ├── protocols/          # Emergency, Parent Down, Onboarding, Handover
│   ├── workflows/          # Visit Prep, Resilience Report, Renewal Check
│   ├── base.py             # Agno agent base class
│   └── unified_support_agent.py  # Unified support agent
├── lib/                    # Shared libraries
│   ├── db_operations.py    # Neo4j operations + dashboard stats
│   ├── ai_extractor.py     # Gemini extraction logic
│   ├── embedding.py        # Gemini Embedding 2 + Neo4j vector search
│   ├── file_readers.py     # File format parsers
│   ├── voice_input.py      # Web Speech API component
│   └── utils.py            # Utilities and session state
├── mobile/                 # Mobile narrative input system
├── sos/                    # Emergency notification system
├── scripts/                # Utility scripts (backup.sh, migrate_schema_v2.py)
├── skills/                 # Internal skills (Python packages)
│   └── ecomap_generator/   # draw.io ecomap XML generation
│       ├── __init__.py
│       └── drawio_engine.py
├── claude-skills/          # Claude Desktop Skills (bundled)
│   ├── neo4j-support-db/   # 障害福祉DB (4-pillar, port 7687)
│   ├── livelihood-support/ # 生活困窮者DB (7-pillar, port 7688)
│   ├── provider-search/    # 事業所検索・口コミ (port 7687)
│   ├── emergency-protocol/ # 緊急時対応プロトコル (read-only)
│   └── ecomap-generator/   # エコマップ生成 (Mermaid/SVG)
├── configs/                # Claude Desktop config templates
│   ├── claude_desktop_config.skills.json  # Skills方式（推奨）
│   └── claude_desktop_config.mcp.json     # レガシーMCP方式
├── docs/                   # Documentation
│   ├── QUICK_START.md      # Quick start guide (5-min setup)
│   ├── ADVANCED_USAGE.md   # Skills detailed usage & prompts
│   └── DEV_NOTES.md        # Developer notes & troubleshooting
├── setup.sh                # Setup script (Neo4j + Skills install)
├── archive/                # Archived legacy files
├── docker-compose.yml      # Neo4j container config
└── pyproject.toml          # Dependencies (uv-managed)
```

## Important Constraints

### Data Integrity

- **Never fabricate data**: AI extraction must not infer missing information
- **Prohibition priority**: NgAction nodes are safety-critical, treat with highest importance
- **Date validation**: Use `lib/utils.py::safe_date_parse()` for all date inputs
- **Session state**: Streamlit apps must call `lib/utils.py::init_session_state()` on startup
- **Client uniqueness**: `Client.name` に UNIQUE 制約あり。name+dob の複合一意性は `lib/db_operations.py::validate_client_uniqueness()` で検証

### Neo4j Query Patterns

- **命名規則**: `docs/NEO4J_SCHEMA_CONVENTION.md` に厳密に従うこと
  - ノード: PascalCase (`Client`, `NgAction`)
  - リレーション: UPPER_SNAKE_CASE (`MUST_AVOID`, `HAS_KEY_PERSON`)
  - プロパティ: camelCase (`riskLevel`, `nextRenewalDate`)
  - 廃止名 (`PROHIBITED`, `PREFERS`, `EMERGENCY_CONTACT`, `RELATES_TO`) は書き込み禁止
- Use `MERGE` for idempotent client/node creation
- Always use parameterized queries (`$param`) to prevent Cypher injection
- Handle optional fields with `COALESCE()` or `CASE WHEN ... ELSE ... END`
- Check existence before creating relationships to avoid duplicates
- 読み取りクエリでは旧名との後方互換性を `[:NEW|OLD]` 構文で確保する
- **全文検索**: `search_support_logs()` で SupportLog のテキスト検索が可能（`idx_supportlog_fulltext`）
- **インデックス・制約**: `docs/NEO4J_SCHEMA_CONVENTION.md` の「インデックスと制約」セクションを参照

### AI Extraction

- Gemini prompt (`EXTRACTION_PROMPT`) is authoritative for JSON schema
- Always call `parse_json_from_response()` to handle markdown code blocks
- Validate extracted data structure before database registration

## Dependencies

### Core Technologies

- **Database**: Neo4j 5.15+ (via Docker)
- **Python**: 3.12+ (enforced by `.python-version`)
- **Package Manager**: uv (required, not pip)
- **AI Models**: Gemini 2.0 Flash (Google), Claude (Anthropic)

### Key Python Libraries

- `agno`: AI agent framework for Gemini integration
- `neo4j`: Python driver for Neo4j
- `streamlit`: Web UI framework
- `mcp[cli]`: Model Context Protocol for Claude Desktop
- `fastapi`: SOS API server
- `python-docx`, `openpyxl`, `pdfplumber`: File format parsers

### External Services

- **LINE Messaging API**: SOS notifications
- **Google AI API**: Gemini extraction

## Development Context

This system was developed by a lawyer working with NPOs supporting families of children with intellectual disabilities. The design prioritizes **real-world emergency scenarios** where staff need immediate access to critical care information when primary caregivers are unavailable.

**Design Philosophy**: Preserve parental tacit knowledge in structured format, queryable in natural language during crisis situations.
