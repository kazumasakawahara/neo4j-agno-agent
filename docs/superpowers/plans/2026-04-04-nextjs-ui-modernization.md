# Next.js UI モダン化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Streamlit UI with Next.js + shadcn/ui, adding a FastAPI backend that uses existing lib/ with Gemini API, while preserving MCP/SOS/Mobile services untouched.

**Architecture:** New `api/` (FastAPI + Gemini agent) and `frontend/` (Next.js copied from oyagami-local, adjusted for Gemini). Streamlit files archived. Existing services unchanged.

**Tech Stack:** Python 3.12, FastAPI, Gemini 2.0 Flash, Gemini Embedding 2, Neo4j 5.15, Next.js 15, TypeScript, shadcn/ui, TanStack Query, React Flow

**Spec:** `docs/superpowers/specs/2026-04-04-nextjs-ui-modernization-design.md`

**Reference:** `~/Dev-Work/oyagami-local/` (source for frontend copy and API patterns)

---

## File Map

### api/ (New — FastAPI backend)

| File | Responsibility |
|------|---------------|
| `api/pyproject.toml` | Dependencies |
| `api/app/__init__.py` | Package init |
| `api/app/main.py` | FastAPI app, CORS, lifespan, router registration |
| `api/app/config.py` | Settings from .env (Gemini API key, Neo4j, ports) |
| `api/app/lib/db_operations.py` | Neo4j operations (migrated from lib/db_new_operations.py) |
| `api/app/lib/embedding.py` | Gemini Embedding 2 (migrated from lib/embedding.py) |
| `api/app/lib/file_readers.py` | File text extraction (migrated from lib/file_readers.py) |
| `api/app/lib/utils.py` | Date parsing (migrated from lib/utils.py) |
| `api/app/lib/ecomap.py` | Ecomap data fetch (copied from oyagami-local) |
| `api/app/lib/chunking.py` | Japanese chunking (copied from oyagami-local) |
| `api/app/agents/gemini_agent.py` | Gemini 2.0 Flash: extraction, chat, safety check |
| `api/app/agents/safety_first.py` | Emergency keyword detection + direct DB search |
| `api/app/agents/prompts/manifesto.md` | Copied from agents/MANIFESTO.md |
| `api/app/agents/prompts/extraction.md` | EXTRACTION_PROMPT from lib/ai_extractor.py |
| `api/app/agents/prompts/safety.md` | Safety compliance prompt |
| `api/app/schemas/client.py` | Client Pydantic models (from oyagami-local) |
| `api/app/schemas/narrative.py` | Narrative models (from oyagami-local) |
| `api/app/schemas/agent.py` | Agent/system models (simplified for Gemini) |
| `api/app/schemas/ecomap.py` | Ecomap models (from oyagami-local) |
| `api/app/schemas/meeting.py` | Meeting models (from oyagami-local) |
| `api/app/schemas/search.py` | Search models (from oyagami-local) |
| `api/app/routers/dashboard.py` | Dashboard endpoints (from oyagami-local) |
| `api/app/routers/clients.py` | Client endpoints (from oyagami-local) |
| `api/app/routers/narratives.py` | Narrative endpoints (from oyagami-local) |
| `api/app/routers/quicklog.py` | Quick log endpoint (from oyagami-local) |
| `api/app/routers/chat.py` | WebSocket chat (simplified for Gemini) |
| `api/app/routers/search.py` | Search endpoints (from oyagami-local) |
| `api/app/routers/ecomap.py` | Ecomap endpoints (from oyagami-local) |
| `api/app/routers/meetings.py` | Meeting endpoints (adapted for Gemini transcription) |
| `api/app/routers/system.py` | System status (Gemini/Neo4j, no Ollama) |
| `api/tests/conftest.py` | Test fixtures |
| `api/tests/routers/test_*.py` | API tests (adapted from oyagami-local) |

### frontend/ (Copied from oyagami-local, adjusted)

| File | Action |
|------|--------|
| `frontend/` (entire directory) | Copy from oyagami-local |
| `frontend/src/lib/api.ts` | Modify: port 3001, remove loadModel/unloadModel |
| `frontend/src/lib/types.ts` | Modify: simplify ModelStatus |
| `frontend/src/app/settings/page.tsx` | Rewrite: Gemini status instead of Ollama |
| `frontend/src/app/chat/page.tsx` | Modify: remove model loading display |
| `frontend/src/hooks/useChat.ts` | Modify: remove model_status handler |
| `frontend/src/components/domain/Sidebar.tsx` | Modify: title change |
| `frontend/src/app/layout.tsx` | Modify: metadata |

### archive/ (Streamlit files moved here)

| File | Source |
|------|--------|
| `archive/app.py` | `app.py` |
| `archive/app_narrative.py` | `app_narrative.py` |
| `archive/app_quick_log.py` | `app_quick_log.py` |
| `archive/app_ui.py` | `app_ui.py` |
| `archive/pages/` | `pages/` |

---

## Task 1: Archive Streamlit + Create API Skeleton

**Files:**
- Move: `app.py`, `app_narrative.py`, `app_quick_log.py`, `app_ui.py`, `pages/` → `archive/`
- Create: `api/pyproject.toml`, `api/app/__init__.py`, `api/app/config.py`, `api/app/main.py`

- [ ] **Step 1: Move Streamlit files to archive**

```bash
cd ~/Dev-Work/neo4j-agno-agent
mkdir -p archive/pages
mv app.py archive/
mv app_narrative.py archive/
mv app_quick_log.py archive/
mv app_ui.py archive/
mv pages/home.py pages/client_list.py pages/claude_guide.py pages/ecomap.py pages/meeting_record.py pages/semantic_search.py archive/pages/
```

- [ ] **Step 2: Create API with uv**

```bash
cd ~/Dev-Work/neo4j-agno-agent
mkdir -p api
cd api
uv init --python 3.12
uv add fastapi uvicorn neo4j google-genai google-generativeai httpx \
       pydantic pydantic-settings python-dotenv websockets \
       fugashi unidic-lite pykakasi \
       python-docx openpyxl pdfplumber
uv add --dev pytest pytest-asyncio httpx
```

- [ ] **Step 3: Create directory structure**

```bash
cd ~/Dev-Work/neo4j-agno-agent/api
mkdir -p app/lib app/agents/prompts app/schemas app/routers
mkdir -p tests/lib tests/agents tests/routers
touch app/__init__.py app/lib/__init__.py app/agents/__init__.py app/schemas/__init__.py app/routers/__init__.py
touch tests/__init__.py tests/lib/__init__.py tests/agents/__init__.py tests/routers/__init__.py
```

- [ ] **Step 4: Create config.py**

```python
# api/app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    gemini_api_key: str = ""
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "gemini-embedding-2-preview"

    backend_port: int = 8000
    frontend_port: int = 3001

    model_config = {"env_file": str(Path(__file__).resolve().parents[2] / ".env")}


settings = Settings()
```

- [ ] **Step 5: Create main.py**

```python
# api/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.lib.db_operations import is_db_available

    if is_db_available():
        print(f"Neo4j connected: {settings.neo4j_uri}")
    else:
        print(f"WARNING: Neo4j not available at {settings.neo4j_uri}")

    if settings.gemini_api_key:
        print("Gemini API key configured")
    else:
        print("WARNING: GEMINI_API_KEY not set")

    yield

    from app.lib.db_operations import close_driver
    close_driver()


app = FastAPI(
    title="neo4j-agno-agent API",
    description="親亡き後支援データベース API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.frontend_port}",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Verify server starts**

```bash
cd ~/Dev-Work/neo4j-agno-agent/api
uv run uvicorn app.main:app --port 8000
# Expected: Uvicorn running, /api/health returns {"status": "ok"}
```

- [ ] **Step 7: Commit**

```bash
cd ~/Dev-Work/neo4j-agno-agent
git add archive/ api/
git commit -m "feat: archive Streamlit UI, create FastAPI skeleton for Next.js migration"
```

---

## Task 2: Schemas + lib/ Migration

**Files:**
- Create: `api/app/schemas/` (6 files — copy from oyagami-local, adjust)
- Create: `api/app/lib/` (6 files — migrate from existing lib/ + copy from oyagami-local)

- [ ] **Step 1: Copy schemas from oyagami-local**

```bash
cp ~/Dev-Work/oyagami-local/backend/app/schemas/client.py ~/Dev-Work/neo4j-agno-agent/api/app/schemas/
cp ~/Dev-Work/oyagami-local/backend/app/schemas/narrative.py ~/Dev-Work/neo4j-agno-agent/api/app/schemas/
cp ~/Dev-Work/oyagami-local/backend/app/schemas/ecomap.py ~/Dev-Work/neo4j-agno-agent/api/app/schemas/
cp ~/Dev-Work/oyagami-local/backend/app/schemas/meeting.py ~/Dev-Work/neo4j-agno-agent/api/app/schemas/
cp ~/Dev-Work/oyagami-local/backend/app/schemas/search.py ~/Dev-Work/neo4j-agno-agent/api/app/schemas/
```

- [ ] **Step 2: Create simplified agent schema (no ModelManager)**

```python
# api/app/schemas/agent.py
from pydantic import BaseModel


class ChatMessage(BaseModel):
    type: str
    content: str | None = None
    agent: str | None = None
    session_id: str | None = None


class ChatRequest(BaseModel):
    content: str
    session_id: str


class SystemStatus(BaseModel):
    gemini_available: bool
    neo4j_available: bool
    gemini_model: str = ""
    embedding_model: str = ""
```

- [ ] **Step 3: Migrate lib/ files**

Copy from oyagami-local and adapt:

```bash
# These are Gemini-independent, copy directly from oyagami-local
cp ~/Dev-Work/oyagami-local/backend/app/lib/utils.py ~/Dev-Work/neo4j-agno-agent/api/app/lib/
cp ~/Dev-Work/oyagami-local/backend/app/lib/file_readers.py ~/Dev-Work/neo4j-agno-agent/api/app/lib/
cp ~/Dev-Work/oyagami-local/backend/app/lib/chunking.py ~/Dev-Work/neo4j-agno-agent/api/app/lib/
cp ~/Dev-Work/oyagami-local/backend/app/lib/ecomap.py ~/Dev-Work/neo4j-agno-agent/api/app/lib/
```

For `db_operations.py`: copy from oyagami-local, then change the Neo4j URI default to match this project's `.env` (`neo4j://localhost:7687` instead of `bolt://localhost:7687`). Read the oyagami-local version first, then write with adjusted defaults.

For `embedding.py`: migrate from existing `~/Dev-Work/neo4j-agno-agent/lib/embedding.py`. Keep Gemini Embedding 2 API calls. Remove Streamlit dependencies. Keep all VECTOR_INDEXES, `embed_text()`, `semantic_search()`, `ensure_vector_indexes()`. Adapt to use `app.config.settings` for API key.

- [ ] **Step 4: Copy tests from oyagami-local**

```bash
cp ~/Dev-Work/oyagami-local/backend/tests/conftest.py ~/Dev-Work/neo4j-agno-agent/api/tests/
cp ~/Dev-Work/oyagami-local/backend/tests/lib/test_utils.py ~/Dev-Work/neo4j-agno-agent/api/tests/lib/
cp ~/Dev-Work/oyagami-local/backend/tests/lib/test_db_operations.py ~/Dev-Work/neo4j-agno-agent/api/tests/lib/
cp ~/Dev-Work/oyagami-local/backend/tests/lib/test_chunking.py ~/Dev-Work/neo4j-agno-agent/api/tests/lib/
```

Update `conftest.py`: remove ModelManager mocking (not needed for Gemini version).

- [ ] **Step 5: Run tests**

```bash
cd ~/Dev-Work/neo4j-agno-agent/api
uv run pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add api/app/schemas/ api/app/lib/ api/tests/
git commit -m "feat: add schemas and lib/ (migrated from existing + oyagami-local)"
```

---

## Task 3: Gemini Agent + Safety First

**Files:**
- Create: `api/app/agents/gemini_agent.py`
- Create: `api/app/agents/safety_first.py`
- Create: `api/app/agents/prompts/manifesto.md`
- Create: `api/app/agents/prompts/extraction.md`
- Create: `api/app/agents/prompts/safety.md`

- [ ] **Step 1: Copy prompts**

```bash
cp ~/Dev-Work/neo4j-agno-agent/agents/MANIFESTO.md ~/Dev-Work/neo4j-agno-agent/api/app/agents/prompts/manifesto.md
cp ~/Dev-Work/oyagami-local/backend/app/agents/prompts/extraction.md ~/Dev-Work/neo4j-agno-agent/api/app/agents/prompts/
cp ~/Dev-Work/oyagami-local/backend/app/agents/prompts/safety.md ~/Dev-Work/neo4j-agno-agent/api/app/agents/prompts/
```

- [ ] **Step 2: Implement gemini_agent.py**

```python
# api/app/agents/gemini_agent.py
"""Gemini 2.0 Flash agent for text extraction, chat, and safety checks."""
import json
import logging
import re
from pathlib import Path

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"

_model = None


def _get_model():
    global _model
    if _model is None:
        genai.configure(api_key=settings.gemini_api_key or settings.google_api_key)
        _model = genai.GenerativeModel(settings.gemini_model)
    return _model


def get_extraction_prompt() -> str:
    return (PROMPT_DIR / "extraction.md").read_text(encoding="utf-8")


def parse_json_from_response(response_text: str) -> dict | None:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


async def extract_from_text(text: str, client_name: str | None = None) -> dict | None:
    """Extract structured graph data from narrative text using Gemini."""
    prompt = get_extraction_prompt()
    user_message = text
    if client_name:
        user_message = f"【対象クライアント: {client_name}】\n\n{text}"
    try:
        model = _get_model()
        response = model.generate_content(
            [{"role": "user", "parts": [prompt + "\n\n" + user_message]}],
            generation_config={"temperature": 0},
        )
        return parse_json_from_response(response.text)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None


async def chat(message: str, history: list[dict] | None = None) -> str:
    """Chat with Gemini using conversation history."""
    manifesto = (PROMPT_DIR / "manifesto.md").read_text(encoding="utf-8")
    try:
        model = _get_model()
        messages = [{"role": "user", "parts": [manifesto + "\n\nあなたは障害福祉支援のアシスタントです。日本語で回答してください。"]}]
        if history:
            for h in history:
                messages.append({"role": h.get("role", "user"), "parts": [h.get("content", "")]})
        messages.append({"role": "user", "parts": [message]})
        response = model.generate_content(messages)
        return response.text
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return f"エラーが発生しました: {e}"


async def check_safety_compliance(narrative: str, ng_actions: list) -> dict:
    """Check if narrative violates existing NgActions."""
    if not ng_actions:
        return {"is_violation": False, "warning": None, "risk_level": "None"}
    safety_prompt = (PROMPT_DIR / "safety.md").read_text(encoding="utf-8")
    safety_prompt = safety_prompt.replace("{ng_actions}", json.dumps(ng_actions, ensure_ascii=False))
    safety_prompt = safety_prompt.replace("{narrative}", narrative)
    try:
        model = _get_model()
        response = model.generate_content(
            [{"role": "user", "parts": [safety_prompt]}],
            generation_config={"temperature": 0},
        )
        match = re.search(r"\{[^}]+\}", response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        logger.warning(f"Safety check failed: {e}")
    return {"is_violation": False, "warning": None, "risk_level": "None"}
```

- [ ] **Step 3: Implement safety_first.py**

```python
# api/app/agents/safety_first.py
"""Safety First: emergency keyword detection + direct DB search (no LLM)."""
import re

from app.lib.db_operations import run_query

EMERGENCY_KEYWORDS = {"パニック", "SOS", "事故", "発作", "倒れた", "救急", "助けて", "緊急"}


def is_emergency(text: str) -> bool:
    return any(kw in text for kw in EMERGENCY_KEYWORDS)


def handle_emergency(text: str) -> str:
    """Direct DB search for emergency info, no LLM involved."""
    name_match = re.search(r"([一-龯]{2,4})\s?さん", text)
    if not name_match:
        return "クライアント名を特定できません。「〇〇さんの緊急情報」のように指定してください。"

    client_name = name_match.group(1)
    records = run_query(
        """
        MATCH (c:Client {name: $name})
        OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
        OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
        OPTIONAL MATCH (c)-[:HAS_KEY_PERSON]->(kp:KeyPerson)
        OPTIONAL MATCH (c)-[:TREATED_AT]->(h:Hospital)
        OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)
        RETURN c, collect(DISTINCT ng) AS ng_actions,
               collect(DISTINCT cp) AS care_prefs,
               collect(DISTINCT kp) AS key_persons, h, g
        """,
        {"name": client_name},
    )

    if not records:
        return f"「{client_name}」さんの情報が見つかりません。"

    r = records[0]
    parts = [f"## {client_name}さんの緊急情報\n"]

    ng_actions = r.get("ng_actions", [])
    if ng_actions:
        parts.append("### 禁忌事項（最優先）")
        for ng in ng_actions:
            ng = dict(ng)
            parts.append(f"- **{ng.get('action', '')}** [{ng.get('riskLevel', '')}]: {ng.get('reason', '')}")

    care_prefs = r.get("care_prefs", [])
    if care_prefs:
        parts.append("\n### 推奨ケア")
        for cp in care_prefs:
            cp = dict(cp)
            parts.append(f"- {cp.get('category', '')}: {cp.get('instruction', '')}")

    key_persons = r.get("key_persons", [])
    if key_persons:
        parts.append("\n### 緊急連絡先")
        for kp in key_persons:
            kp = dict(kp)
            parts.append(f"- {kp.get('name', '')} ({kp.get('relationship', '')}): {kp.get('phone', 'N/A')}")

    return "\n".join(parts)
```

- [ ] **Step 4: Write tests**

```python
# api/tests/agents/test_safety_first.py
from app.agents.safety_first import is_emergency, EMERGENCY_KEYWORDS


def test_emergency_detection():
    assert is_emergency("田中さんがパニックを起こしている")
    assert is_emergency("SOS 助けて")
    assert is_emergency("発作が起きた")


def test_non_emergency():
    assert not is_emergency("今日の支援記録を登録して")
    assert not is_emergency("こんにちは")
```

```python
# api/tests/agents/test_gemini_agent.py
from app.agents.gemini_agent import parse_json_from_response, get_extraction_prompt


def test_parse_json_direct():
    assert parse_json_from_response('{"nodes":[],"relationships":[]}') == {"nodes": [], "relationships": []}


def test_parse_json_markdown():
    raw = '```json\n{"nodes":[{"temp_id":"c1","label":"Client","properties":{"name":"田中"}}],"relationships":[]}\n```'
    result = parse_json_from_response(raw)
    assert result is not None
    assert result["nodes"][0]["label"] == "Client"


def test_parse_json_invalid():
    assert parse_json_from_response("not json") is None


def test_extraction_prompt_exists():
    prompt = get_extraction_prompt()
    assert "Client" in prompt
    assert "NgAction" in prompt
```

- [ ] **Step 5: Run tests**

```bash
cd ~/Dev-Work/neo4j-agno-agent/api
uv run pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add api/app/agents/ api/tests/agents/
git commit -m "feat: add Gemini agent and Safety First emergency handler"
```

---

## Task 4: API Routers (All)

**Files:**
- Create: all 9 routers in `api/app/routers/`
- Modify: `api/app/main.py` (register routers)

- [ ] **Step 1: Copy routers from oyagami-local and adapt**

Most routers are identical. Copy all from oyagami-local:

```bash
cp ~/Dev-Work/oyagami-local/backend/app/routers/dashboard.py ~/Dev-Work/neo4j-agno-agent/api/app/routers/
cp ~/Dev-Work/oyagami-local/backend/app/routers/clients.py ~/Dev-Work/neo4j-agno-agent/api/app/routers/
cp ~/Dev-Work/oyagami-local/backend/app/routers/narratives.py ~/Dev-Work/neo4j-agno-agent/api/app/routers/
cp ~/Dev-Work/oyagami-local/backend/app/routers/quicklog.py ~/Dev-Work/neo4j-agno-agent/api/app/routers/
cp ~/Dev-Work/oyagami-local/backend/app/routers/search.py ~/Dev-Work/neo4j-agno-agent/api/app/routers/
cp ~/Dev-Work/oyagami-local/backend/app/routers/ecomap.py ~/Dev-Work/neo4j-agno-agent/api/app/routers/
```

- [ ] **Step 2: Adapt narratives.py imports**

In `api/app/routers/narratives.py`, change intake agent import:
```python
# Change from:
from app.agents.intake import extract_from_text
# To:
from app.agents.gemini_agent import extract_from_text
```

Change validator import:
```python
# Change from:
from app.agents.validator import check_safety_compliance, validate_schema
# To:
from app.agents.gemini_agent import check_safety_compliance
# validate_schema stays (it's in the same file or create a simple one)
```

Note: `validate_schema` can be copied from oyagami-local's `validator.py` as a standalone function (it doesn't use LLM).

- [ ] **Step 3: Create simplified chat.py (Gemini version)**

```python
# api/app/routers/chat.py
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.gemini_agent import chat
from app.agents.safety_first import handle_emergency, is_emergency

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    history = []

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_text = msg.get("content", "")
            session_id = msg.get("session_id", session_id)

            # Safety First check
            if is_emergency(user_text):
                await websocket.send_json({
                    "type": "routing",
                    "agent": "safety_first",
                    "decision": "emergency_search",
                    "reason": "緊急キーワード検知",
                })
                response = handle_emergency(user_text)
            else:
                await websocket.send_json({
                    "type": "routing",
                    "agent": "gemini",
                    "decision": "chat",
                    "reason": "通常応答",
                })
                response = await chat(user_text, history)
                history.append({"role": "user", "content": user_text})
                history.append({"role": "model", "content": response})

            # Stream response in chunks
            for i in range(0, len(response), 20):
                await websocket.send_json({
                    "type": "stream",
                    "content": response[i:i + 20],
                    "agent": "gemini",
                })

            await websocket.send_json({"type": "done", "session_id": session_id})

    except WebSocketDisconnect:
        logger.info(f"Chat session {session_id} disconnected")
```

- [ ] **Step 4: Create meetings.py (Gemini transcription version)**

```python
# api/app/routers/meetings.py
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from app.lib.db_operations import register_to_database, run_query
from app.lib.embedding import embed_text
from app.schemas.meeting import MeetingRecord, MeetingUploadResponse

router = APIRouter(prefix="/api/meetings", tags=["meetings"])
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "meetings"


async def _transcribe_with_gemini(file_path: str) -> str | None:
    """Transcribe audio using Gemini 2.0 Flash."""
    try:
        import google.generativeai as genai
        from app.config import settings

        genai.configure(api_key=settings.gemini_api_key or settings.google_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        audio_file = genai.upload_file(file_path)
        response = model.generate_content(
            ["この音声を正確に日本語で文字起こししてください。", audio_file],
        )
        return response.text
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Gemini transcription failed: {e}")
        return None


@router.post("/upload", response_model=MeetingUploadResponse)
async def upload_meeting(
    file: UploadFile = File(...),
    client_name: str = Form(...),
    title: str = Form(""),
    note: str = Form(""),
):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:8]
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    content = await file.read()
    file_path.write_bytes(content)

    transcript = await _transcribe_with_gemini(str(file_path))

    graph = {
        "nodes": [
            {"temp_id": "c1", "label": "Client", "properties": {"name": client_name}},
            {"temp_id": "mr1", "label": "MeetingRecord", "properties": {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "title": title or file.filename,
                "filePath": str(file_path),
                "transcript": transcript or "",
                "note": note,
            }},
        ],
        "relationships": [
            {"source_temp_id": "mr1", "target_temp_id": "c1", "type": "ABOUT", "properties": {}},
        ],
    }
    register_to_database(graph)

    if transcript:
        embedding = await embed_text(transcript)
        if embedding:
            run_query(
                "MATCH (mr:MeetingRecord {filePath: $path}) SET mr.textEmbedding = $embedding",
                {"path": str(file_path), "embedding": embedding},
            )

    return MeetingUploadResponse(status="success", transcript=transcript, meeting_id=file_id)


@router.get("/{client_name}", response_model=list[MeetingRecord])
async def list_meetings(client_name: str):
    records = run_query("""
        MATCH (mr:MeetingRecord)-[:ABOUT]->(c:Client {name: $name})
        RETURN mr.date AS date, mr.title AS title, mr.duration AS duration,
               mr.transcript AS transcript, mr.note AS note,
               mr.filePath AS file_path, c.name AS client_name
        ORDER BY mr.date DESC
    """, {"name": client_name})
    return [MeetingRecord(**r) for r in records]
```

- [ ] **Step 5: Create system.py (Gemini version)**

```python
# api/app/routers/system.py
from fastapi import APIRouter

from app.config import settings
from app.lib.db_operations import is_db_available
from app.schemas.agent import SystemStatus

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    gemini_available = bool(settings.gemini_api_key or settings.google_api_key)
    return SystemStatus(
        gemini_available=gemini_available,
        neo4j_available=is_db_available(),
        gemini_model=settings.gemini_model,
        embedding_model=settings.embedding_model,
    )
```

- [ ] **Step 6: Register all routers in main.py**

Add to `api/app/main.py`:

```python
from app.routers import dashboard, clients, narratives, quicklog, chat, search, ecomap, meetings, system

app.include_router(dashboard.router)
app.include_router(clients.router)
app.include_router(narratives.router)
app.include_router(quicklog.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(ecomap.router)
app.include_router(meetings.router)
app.include_router(system.router)
```

- [ ] **Step 7: Copy and run tests**

```bash
cp ~/Dev-Work/oyagami-local/backend/tests/routers/test_dashboard.py ~/Dev-Work/neo4j-agno-agent/api/tests/routers/
cp ~/Dev-Work/oyagami-local/backend/tests/routers/test_clients.py ~/Dev-Work/neo4j-agno-agent/api/tests/routers/
cp ~/Dev-Work/oyagami-local/backend/tests/routers/test_health.py ~/Dev-Work/neo4j-agno-agent/api/tests/routers/
cp ~/Dev-Work/oyagami-local/backend/tests/routers/test_narratives.py ~/Dev-Work/neo4j-agno-agent/api/tests/routers/
cp ~/Dev-Work/oyagami-local/backend/tests/routers/test_system.py ~/Dev-Work/neo4j-agno-agent/api/tests/routers/
cp ~/Dev-Work/oyagami-local/backend/tests/routers/test_ecomap.py ~/Dev-Work/neo4j-agno-agent/api/tests/routers/
cp ~/Dev-Work/oyagami-local/backend/tests/routers/test_meetings.py ~/Dev-Work/neo4j-agno-agent/api/tests/routers/
```

Adapt `conftest.py` for Gemini version (no ModelManager mocking needed). Run tests:

```bash
cd ~/Dev-Work/neo4j-agno-agent/api
uv run pytest tests/ -v
```

- [ ] **Step 8: Commit**

```bash
git add api/app/routers/ api/app/main.py api/tests/
git commit -m "feat: add all API routers (9 endpoints, Gemini-based)"
```

---

## Task 5: Frontend Copy + Adjustment

**Files:**
- Copy: `~/Dev-Work/oyagami-local/frontend/` → `~/Dev-Work/neo4j-agno-agent/frontend/`
- Modify: 7 files for Gemini adaptation

- [ ] **Step 1: Copy entire frontend from oyagami-local**

```bash
cp -r ~/Dev-Work/oyagami-local/frontend ~/Dev-Work/neo4j-agno-agent/
rm -rf ~/Dev-Work/neo4j-agno-agent/frontend/.git
rm -rf ~/Dev-Work/neo4j-agno-agent/frontend/node_modules
rm -rf ~/Dev-Work/neo4j-agno-agent/frontend/.next
```

- [ ] **Step 2: Install dependencies**

```bash
cd ~/Dev-Work/neo4j-agno-agent/frontend
pnpm install
```

- [ ] **Step 3: Update api.ts**

In `frontend/src/lib/api.ts`:
- Change `API_BASE` default to port 8000 (same)
- Remove `system.loadModel` and `system.unloadModel` functions
- Update `system.status` return type to match `SystemStatus` (gemini_available, not ollama_available)

- [ ] **Step 4: Update types.ts**

In `frontend/src/lib/types.ts`:
- Replace `ModelStatus` with:
```typescript
export interface SystemStatus {
  gemini_available: boolean;
  neo4j_available: boolean;
  gemini_model: string;
  embedding_model: string;
}
```

- [ ] **Step 5: Rewrite settings/page.tsx**

Replace the Ollama model management page with Gemini status page showing:
- Gemini API / Neo4j connection badges
- Model names (gemini-2.0-flash, gemini-embedding-2-preview)
- No load/unload buttons (cloud API doesn't need them)

- [ ] **Step 6: Update chat/page.tsx and useChat.ts**

In `useChat.ts`: remove `model_status` message type handling.
In `chat/page.tsx`: remove `AgentStatus` model loading progress display. Keep routing info display (Safety First detection).

- [ ] **Step 7: Update Sidebar.tsx and layout.tsx**

In `Sidebar.tsx`: Change title from "OYAGAMI LOCAL" to "親亡き後支援DB". Update status display to show `gemini_available` instead of `ollama_available`.

In `layout.tsx`: Update metadata title and description.

- [ ] **Step 8: Verify build**

```bash
cd ~/Dev-Work/neo4j-agno-agent/frontend
pnpm build
```

- [ ] **Step 9: Commit**

```bash
cd ~/Dev-Work/neo4j-agno-agent
git add frontend/
git commit -m "feat: add Next.js frontend (adapted from oyagami-local for Gemini)"
```

---

## Task 6: Integration Test + Documentation

**Files:**
- Modify: `README.md`, `CLAUDE.md`

- [ ] **Step 1: Run all backend tests**

```bash
cd ~/Dev-Work/neo4j-agno-agent/api
uv run pytest tests/ -v
```

- [ ] **Step 2: Verify frontend build**

```bash
cd ~/Dev-Work/neo4j-agno-agent/frontend
pnpm build
```

- [ ] **Step 3: Update CLAUDE.md**

Add section about new API server and frontend:
- `api/` directory: FastAPI backend on port 8000
- `frontend/` directory: Next.js on port 3001
- `archive/` directory: retired Streamlit UI
- New startup commands:
```bash
# API Server
cd api && uv run uvicorn app.main:app --reload --port 8000
# Frontend
cd frontend && pnpm dev --port 3001
```

- [ ] **Step 4: Update README.md**

Add new architecture section reflecting the Next.js + FastAPI stack alongside existing MCP/SOS/Mobile services.

- [ ] **Step 5: Final commit and push**

```bash
cd ~/Dev-Work/neo4j-agno-agent
git add -A
git commit -m "docs: update documentation for Next.js UI modernization"
git push
```
