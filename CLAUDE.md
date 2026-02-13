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

### 3-Layer Workflow

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

### AI Models

- **Gemini 2.0 Flash**: Narrative text structuring (extraction) via `lib/ai_extractor.py`
- **Claude Desktop**: Natural language database queries via Skills + Neo4j MCP (see `agents/ROUTING.md`)

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
| neo4j-support-db | 7687 | 8 read | 障害福祉クライアント管理 |
| livelihood-support | 7688 | 12 read | 生活困窮者自立支援 |
| provider-search | 7687 | 6 read + 3 write | 事業所検索・口コミ |
| emergency-protocol | N/A | N/A | 緊急時プロトコル |
| ecomap-generator | N/A | N/A | エコマップ生成 |

See `agents/ROUTING.md` for guidance on choosing between skills.

## Database Schema Notes

### Node Types

**Core Entities**:
- `:Client`: Central node (name, dob, bloodType)
- `:NgAction`: Prohibited actions with risk levels (safety-critical)
- `:CarePreference`: Recommended care instructions
- `:Condition`: Medical diagnoses/characteristics

**Support Network**:
- `:KeyPerson`: Emergency contacts with priority and relationship
- `:Guardian`: Legal guardians
- `:Hospital`: Medical providers
- `:Supporter`: Support staff who log daily care records
- `:SupportLog`: Daily support records with effectiveness tracking

**Legal Documentation**:
- `:Certificate`: 手帳・受給者証 with `nextRenewalDate`
- `:PublicAssistance`: 公的扶助

**Financial Safety** (livelihood-support, port 7688):
- `:EconomicRisk`: Economic exploitation risks
- `:MoneyManagement`: Financial management capability records

### Relationship Patterns

```cypher
(:Client)-[:HAS_CONDITION]->(:Condition)
(:Client)-[:PROHIBITED]->(:NgAction)-[:RELATES_TO]->(:Condition)
(:Client)-[:PREFERS]->(:CarePreference)
(:Client)-[:EMERGENCY_CONTACT]->(:KeyPerson)
(:Client)-[:HAS_GUARDIAN]->(:Guardian)
(:Client)-[:HOLDS]->(:Certificate)
(:Supporter)-[:LOGGED]->(:SupportLog)-[:ABOUT]->(:Client)
```

## File Organization

```
neo4j-agno-agent/
├── app.py                  # Dashboard entry point (st.navigation)
├── app_narrative.py        # Layer 1: Initial registration UI
├── app_quick_log.py        # Layer 2: Quick logging UI
├── app_ui.py               # Agno/Gemini chat UI
├── server.py               # MCP server for Claude Desktop
├── main.py                 # CLI agent entry point (legacy)
├── pages/                  # Dashboard sub-pages
│   ├── home.py             # Dashboard home with stats & workflow cards
│   ├── client_list.py      # Searchable client list
│   └── claude_guide.py     # Claude Desktop usage guide
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
│   ├── file_readers.py     # File format parsers
│   ├── voice_input.py      # Web Speech API component
│   └── utils.py            # Utilities and session state
├── mobile/                 # Mobile narrative input system
├── sos/                    # Emergency notification system
├── scripts/                # Utility scripts (backup.sh)
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

### Neo4j Query Patterns

- Use `MERGE` for idempotent client/node creation
- Always use parameterized queries (`$param`) to prevent Cypher injection
- Handle optional fields with `COALESCE()` or `CASE WHEN ... ELSE ... END`
- Check existence before creating relationships to avoid duplicates

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
