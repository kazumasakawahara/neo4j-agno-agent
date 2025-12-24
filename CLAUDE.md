# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**親亡き後支援データベース (Post-Parent Support & Advocacy Graph)**

A Neo4j-based graph database system for managing support information for individuals with intellectual/developmental disabilities, designed to preserve parental tacit knowledge for emergency situations and post-parent care continuity.

### Core Manifesto (4 Pillars)

1. **Dignity (尊厳)**: Record individuals as humans with history and will
2. **Safety (安全)**: Emergency-first data structure with prohibition priorities
3. **Continuity (継続性)**: Maintain care quality across support staff transitions
4. **Advocacy (権利擁護)**: Link voiceless voices to legal backing

## Architecture

### System Components

1. **Data Model**: 4-pillar Neo4j graph structure
   - Pillar 1: Identity & Narrative (Client, LifeHistory, Wish)
   - Pillar 2: Care Instructions (CarePreference, NgAction, Condition)
   - Pillar 3: Legal Basis (Certificate, PublicAssistance)
   - Pillar 4: Crisis Network (KeyPerson, Guardian, MedicalProvider)

2. **UI Applications**:
   - `app_narrative.py`: Streamlit data entry UI with narrative-style input and file upload
   - `app_quick_log.py`: Mobile-friendly quick logging UI (record only exceptional events)
   - `sos/app/`: Mobile SOS button app for emergency notifications

3. **Backend Services**:
   - `server.py`: MCP server for Claude Desktop integration (natural language queries)
   - `sos/api_server.py`: FastAPI server for SOS emergency notifications with LINE integration

4. **Shared Libraries** (`lib/`):
   - `db_operations.py`: Neo4j connection, query execution, data registration
   - `ai_extractor.py`: Gemini 2.0-based text-to-structured-data extraction
   - `file_readers.py`: Multi-format file parsing (docx, xlsx, pdf, txt)
   - `utils.py`: Date parsing, session state management

### AI Models

- **Gemini 2.0 Flash**: Narrative text structuring (extraction)
- **Claude Desktop**: Natural language database queries (via MCP)

## Common Development Tasks

### Environment Setup

```bash
# Install dependencies
uv sync

# Start Neo4j database (Docker required)
docker-compose up -d

# Create .env file with credentials
cat > .env << EOF
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
GEMINI_API_KEY=your_api_key_here
EOF
```

### Running Applications

```bash
# Main Streamlit UI (port 8501)
uv run streamlit run app_narrative.py

# MCP Server for Claude Desktop
# Configure in claude_desktop_config.json:
# {
#   "mcpServers": {
#     "support-db": {
#       "command": "/absolute/path/.venv/bin/python",
#       "args": ["/absolute/path/server.py"]
#     }
#   }
# }

# SOS Emergency API Server (port 8000)
cd sos
uv run python api_server.py
```

### Database Operations

```bash
# Access Neo4j Browser (after docker-compose up)
open http://localhost:7474

# Run Cypher queries via Python
from lib.db_operations import run_query
result = run_query("MATCH (c:Client) RETURN c.name LIMIT 10")
```

### Testing SOS System

```bash
# Start Neo4j
docker-compose up -d

# Start SOS API server
cd sos && uv run python api_server.py

# Access mobile app (replace IP and client name)
# http://192.168.1.100:8000/app/?id=山田健太
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

### MCP Server Tools (server.py)

Available Claude Desktop commands:

**検索・閲覧系:**
- `search_emergency_info`: Priority-ordered emergency data retrieval
- `get_client_profile`: Complete client overview
- `check_renewal_dates`: Certificate expiration monitoring
- `list_clients`: Client roster
- `get_database_stats`: Database statistics
- `run_cypher_query`: Custom Cypher execution

**支援記録系:**
- `add_support_log`: 物語風テキストから支援記録を自動抽出・登録
- `get_support_logs`: クライアントの支援記録履歴を取得
- `discover_care_patterns`: 効果的なケアパターンを自動発見

**監査ログ系:**
- `get_audit_logs`: 操作履歴（誰が・いつ・何を変更）を取得
- `get_client_change_history`: クライアント別の変更履歴を取得

### SOS Emergency Notification Flow

1. Mobile app (`sos/app/`) sends POST to `/api/sos`
2. `api_server.py` queries Neo4j for client NgActions and emergency contacts
3. Formats message with geolocation and prohibited actions
4. Sends LINE notification to configured group

## Database Schema Notes

### Node Types

**Core Entities**:
- `:Client`: Central node (name, dob, bloodType)
- `:NgAction`: **Most critical** - prohibited actions with risk levels
- `:CarePreference`: Recommended care instructions
- `:Condition`: Medical diagnoses/characteristics

**Support Network**:
- `:KeyPerson`: Emergency contacts with priority and relationship
- `:Guardian`: Legal guardians (成年後見人)
- `:Lawyer`: Legal representation
- `:Supporter`: **NEW** - Support staff who log daily care records
- `:SupportLog`: **NEW** - Daily support records with effectiveness tracking

**Legal Documentation**:
- `:Certificate`: 手帳・受給者証 with `nextRenewalDate`
- `:PublicAssistance`: 公的扶助 (生活保護、障害年金)

### Relationship Patterns

```cypher
(:Client)-[:HAS_CONDITION]->(:Condition)
(:Client)-[:PROHIBITED]->(:NgAction)-[:RELATES_TO]->(:Condition)
(:Client)-[:PREFERS]->(:CarePreference)
(:Client)-[:EMERGENCY_CONTACT]->(:KeyPerson)
(:Client)-[:HAS_GUARDIAN]->(:Guardian)
(:Client)-[:HOLDS]->(:Certificate)

# NEW: Support Log Relationships
(:Supporter)-[:LOGGED]->(:SupportLog)-[:ABOUT]->(:Client)
(:SupportLog).effectiveness = 'Effective' | 'Neutral' | 'Ineffective'
```

## File Organization

```
neo4j-agno-agent/
├── app_narrative.py        # Main Streamlit UI
├── app_quick_log.py        # Quick logging UI (mobile-friendly)
├── server.py               # MCP server for Claude Desktop
├── lib/                    # Shared libraries (import from here)
│   ├── db_operations.py    # All Neo4j operations (+ audit logging)
│   ├── ai_extractor.py     # Gemini extraction logic
│   ├── file_readers.py     # File format parsers
│   └── utils.py            # Utilities and session state
├── sos/                    # Emergency notification system
│   ├── api_server.py       # FastAPI server
│   └── app/                # Mobile app static files
├── scripts/                # Utility scripts
│   └── backup.sh           # Database backup script
├── docker-compose.yml      # Neo4j container config
├── pyproject.toml          # Dependencies (uv-managed)
└── docs/                   # Documentation
```

### Backup & Recovery

```bash
# Manual backup
./scripts/backup.sh

# Scheduled backup (cron example: daily at 3 AM)
0 3 * * * cd /path/to/neo4j-agno-agent && ./scripts/backup.sh
```

Backups are stored in `neo4j_backup/` and retained for 30 days.

## Important Constraints

### Data Integrity

- **Never fabricate data**: AI extraction must not infer missing information
- **Prohibition priority**: NgAction nodes are safety-critical, treat with highest importance
- **Date validation**: Use `lib/utils.py::safe_date_parse()` for all date inputs
- **Session state**: Streamlit apps must call `lib/utils.py::init_session_state()` on startup

### Neo4j Query Patterns

- Use `MERGE` for idempotent client/node creation
- Always use parameterized queries (`$param`) to prevent Cypher injection
- Handle optional fields with `COALESCE()` or `CASE WHEN ... ELSE ... END`
- Check existence before creating relationships to avoid duplicates

### AI Extraction

- Gemini prompt (`EXTRACTION_PROMPT`) is authoritative for JSON schema
- Always call `parse_json_from_response()` to handle markdown code blocks
- Validate extracted data structure before database registration
- Preserve original narrative text in `:LifeHistory` nodes when possible

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

- **LINE Messaging API**: Required for SOS notifications (get `LINE_CHANNEL_ACCESS_TOKEN` and `LINE_GROUP_ID`)
- **Google AI API**: Required for Gemini extraction (get `GEMINI_API_KEY`)

## Development Context

This system was developed by a lawyer working with NPOs supporting families of children with intellectual disabilities. The design prioritizes **real-world emergency scenarios** where staff need immediate access to critical care information (especially prohibitions) when primary caregivers are unavailable.

**Design Philosophy**: Preserve parental tacit knowledge in structured format, queryable in natural language during crisis situations.

## NEW: Support Log System (Living Database)

### Concept
The database evolves with daily support experiences. Support staff record interactions in natural language, and AI extracts:
- What happened (situation)
- What they did (action)
- Whether it worked (effectiveness)

Over time, the system discovers patterns: "When X happens, Y works best."

### Usage Workflow

**Option 1: Quick Log (Mobile-Friendly)**
```bash
uv run streamlit run app_quick_log.py
# 30秒で記録完了。「普通の日」は記録不要。
# 「😊 とても良い日！」or「🤔 気になることあり」のみ記録
```

**Option 2: Streamlit UI (Detailed)**
```bash
uv run streamlit run app_narrative.py
# Input narrative text → AI extracts support logs → View in "支援記録" tab
```

**Option 3: Claude Desktop (MCP)**
```
User: "山田健太さんの記録を追加: 今日、サイレンで驚いてパニック。テレビを消して5分見守ったら落ち着いた。効果的でした。"
Claude: add_support_log(client_name="山田健太", narrative_text="...")
→ ✅ 1件の支援記録を登録しました

User: "山田健太さんの効果的なケアパターンは？"
Claude: discover_care_patterns(client_name="山田健太")
→ パニック時: 静かな環境を作り、5分間見守る（3回効果的）
```

### Test Script
```bash
uv run python test_support_log.py
# Tests 3 scenarios: daily support, emergency response, comprehensive info
```
