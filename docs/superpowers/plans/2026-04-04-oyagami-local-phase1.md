# oyagami-local Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local LLM-powered support database system with multi-agent architecture (Agno + Ollama) and modern frontend (Next.js + shadcn/ui), replicating the core functionality of neo4j-agno-agent.

**Architecture:** Monorepo with `backend/` (FastAPI + Agno agents + Ollama) and `frontend/` (Next.js 15 + shadcn/ui + Tailwind CSS v4). Communication via REST + WebSocket. Existing Neo4j Docker container shared from sibling project.

**Tech Stack:** Python 3.12, FastAPI, Agno, Ollama (mistral-small, deepseek-r1:70b, llama4, qwen3-coder:30b, nomic-embed-text), Neo4j 5.15, Next.js 15, TypeScript, shadcn/ui, TanStack Query, Vercel AI SDK

**Spec:** `docs/superpowers/specs/2026-04-04-oyagami-local-design.md`

**Reference project:** `~/Dev-Work/neo4j-agno-agent/` (current codebase to migrate from)

---

## File Map

### Backend (`~/Dev-Work/oyagami-local/backend/`)

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Dependencies and project metadata |
| `app/__init__.py` | Package init |
| `app/main.py` | FastAPI app, CORS, router includes, lifespan |
| `app/config.py` | Settings from .env (Pydantic BaseSettings) |
| `app/lib/db_operations.py` | Neo4j connection, query execution, registration |
| `app/lib/file_readers.py` | docx/xlsx/pdf/txt/image text extraction |
| `app/lib/utils.py` | Date parsing (wareki→seireki), age calculation |
| `app/lib/embedding.py` | Ollama embedding generation, Neo4j vector search |
| `app/lib/model_manager.py` | Ollama model load/unload lifecycle management |
| `app/schemas/client.py` | Client-related Pydantic models |
| `app/schemas/narrative.py` | Extraction/validation Pydantic models |
| `app/schemas/agent.py` | Agent routing/chat Pydantic models |
| `app/agents/prompts/manifesto.md` | 5-value manifesto (copied from agents/MANIFESTO.md) |
| `app/agents/prompts/extraction.md` | EXTRACTION_PROMPT for Intake agent |
| `app/agents/prompts/safety.md` | Safety compliance check prompt |
| `app/agents/coordinator.py` | Intent classification + routing (mistral-small) |
| `app/agents/intake.py` | Text→JSON extraction (deepseek-r1:70b) |
| `app/agents/validator.py` | Schema/logic/safety validation (mistral-small) |
| `app/agents/cypher_gen.py` | Cypher query generation (qwen3-coder:30b) |
| `app/agents/analyst.py` | Analysis + case comparison (llama4) |
| `app/agents/team.py` | Agno Team composition and orchestration |
| `app/routers/dashboard.py` | GET stats, alerts, activity |
| `app/routers/clients.py` | GET list, detail, emergency, logs |
| `app/routers/narratives.py` | POST extract, validate, register, upload |
| `app/routers/quicklog.py` | POST quick log |
| `app/routers/chat.py` | WebSocket chat endpoint |
| `app/routers/search.py` | GET fulltext search |
| `app/routers/system.py` | GET status, POST model load/unload |
| `tests/conftest.py` | Shared fixtures (Neo4j test session, FastAPI test client) |
| `tests/lib/test_model_manager.py` | ModelManager unit tests |
| `tests/lib/test_db_operations.py` | DB operation tests |
| `tests/lib/test_utils.py` | Date parsing tests |
| `tests/lib/test_embedding.py` | Embedding tests |
| `tests/agents/test_coordinator.py` | Routing accuracy tests |
| `tests/agents/test_intake.py` | Extraction quality tests |
| `tests/agents/test_validator.py` | Validation logic tests |
| `tests/routers/test_dashboard.py` | Dashboard API tests |
| `tests/routers/test_clients.py` | Clients API tests |
| `tests/routers/test_narratives.py` | Narratives API tests |
| `tests/routers/test_system.py` | System API tests |

### Frontend (`~/Dev-Work/oyagami-local/frontend/`)

| File | Responsibility |
|------|---------------|
| `src/app/layout.tsx` | Root layout with sidebar navigation |
| `src/app/page.tsx` | Dashboard page |
| `src/app/clients/page.tsx` | Client list |
| `src/app/clients/[name]/page.tsx` | Client detail |
| `src/app/narrative/page.tsx` | Narrative input wizard |
| `src/app/quicklog/page.tsx` | Quick log form |
| `src/app/chat/page.tsx` | AI chat with WebSocket |
| `src/app/settings/page.tsx` | LLM model management |
| `src/components/domain/Sidebar.tsx` | Navigation sidebar + status bar |
| `src/components/domain/StatsCards.tsx` | Dashboard stat cards |
| `src/components/domain/RenewalAlerts.tsx` | Certificate renewal alerts |
| `src/components/domain/RecentActivity.tsx` | Recent activity feed |
| `src/components/domain/ClientTable.tsx` | Searchable client table |
| `src/components/domain/ClientDetail.tsx` | Client detail card |
| `src/components/domain/KanaFilter.tsx` | あかさたな filter buttons |
| `src/components/domain/NarrativeWizard.tsx` | 3-step wizard controller |
| `src/components/domain/ExtractionPreview.tsx` | Extracted data tree view |
| `src/components/domain/ChatPanel.tsx` | Chat message display |
| `src/components/domain/AgentStatus.tsx` | Agent/model status indicator |
| `src/lib/api.ts` | Backend API client (fetch wrappers) |
| `src/lib/types.ts` | Shared TypeScript types |
| `src/hooks/useSystemStatus.ts` | System status polling hook |
| `src/hooks/useChat.ts` | WebSocket chat hook |

---

## Task 1: Project Skeleton + Configuration

**Files:**
- Create: `~/Dev-Work/oyagami-local/backend/pyproject.toml`
- Create: `~/Dev-Work/oyagami-local/backend/app/__init__.py`
- Create: `~/Dev-Work/oyagami-local/backend/app/config.py`
- Create: `~/Dev-Work/oyagami-local/backend/app/main.py`
- Create: `~/Dev-Work/oyagami-local/.env`
- Create: `~/Dev-Work/oyagami-local/.gitignore`

- [ ] **Step 1: Create project directory and initialize git**

```bash
cd ~/Dev-Work
mkdir -p oyagami-local
cd oyagami-local
git init
```

- [ ] **Step 2: Create backend with uv**

```bash
cd ~/Dev-Work/oyagami-local
mkdir -p backend
cd backend
uv init --python 3.12
uv add fastapi uvicorn neo4j agno httpx \
       pydantic pydantic-settings python-dotenv websockets \
       fugashi unidic-lite pykakasi \
       python-docx openpyxl pdfplumber
uv add --dev pytest pytest-asyncio httpx
```

- [ ] **Step 3: Create .env at project root**

```bash
cat > ~/Dev-Work/oyagami-local/.env << 'ENVEOF'
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
OLLAMA_BASE_URL=http://localhost:11434
COORDINATOR_MODEL=mistral-small:latest
INTAKE_MODEL=deepseek-r1:70b
VALIDATOR_MODEL=mistral-small:latest
ANALYST_MODEL=llama4:latest
CYPHER_MODEL=qwen3-coder:30b
EMBEDDING_MODEL=nomic-embed-text
BACKEND_PORT=8000
FRONTEND_PORT=3000
ENVEOF
```

- [ ] **Step 4: Create .gitignore**

```gitignore
__pycache__/
*.pyc
.venv/
.env
node_modules/
.next/
*.lock
.DS_Store
```

- [ ] **Step 5: Create app/config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    ollama_base_url: str = "http://localhost:11434"
    coordinator_model: str = "mistral-small:latest"
    intake_model: str = "deepseek-r1:70b"
    validator_model: str = "mistral-small:latest"
    analyst_model: str = "llama4:latest"
    cypher_model: str = "qwen3-coder:30b"
    embedding_model: str = "nomic-embed-text"

    backend_port: int = 8000
    frontend_port: int = 3000

    model_config = {"env_file": str(Path(__file__).resolve().parents[2] / ".env")}


settings = Settings()
```

- [ ] **Step 6: Create app/__init__.py**

```python
# backend/app/__init__.py
```

- [ ] **Step 7: Create app/main.py**

```python
# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify Neo4j + Ollama connectivity
    from app.lib.db_operations import is_db_available
    from app.lib.model_manager import model_manager

    if is_db_available():
        print(f"Neo4j connected: {settings.neo4j_uri}")
    else:
        print(f"WARNING: Neo4j not available at {settings.neo4j_uri}")

    await model_manager.initialize()
    yield
    # Shutdown
    from app.lib.db_operations import close_driver

    close_driver()


app = FastAPI(
    title="oyagami-local",
    description="親亡き後支援データベース（ローカルLLM版）",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{settings.frontend_port}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 8: Create directory structure**

```bash
cd ~/Dev-Work/oyagami-local/backend
mkdir -p app/lib app/agents/prompts app/schemas app/routers
mkdir -p tests/lib tests/agents tests/routers
touch app/lib/__init__.py app/agents/__init__.py app/schemas/__init__.py app/routers/__init__.py
touch tests/__init__.py tests/lib/__init__.py tests/agents/__init__.py tests/routers/__init__.py
```

- [ ] **Step 9: Verify the server starts**

```bash
cd ~/Dev-Work/oyagami-local/backend
uv run uvicorn app.main:app --port 8000
# Expected: Uvicorn running on http://0.0.0.0:8000
# Visit http://localhost:8000/api/health → {"status": "ok"}
```

- [ ] **Step 10: Commit**

```bash
cd ~/Dev-Work/oyagami-local
git add -A
git commit -m "feat: project skeleton with FastAPI, config, and health endpoint"
```

---

## Task 2: ModelManager (Ollama Lifecycle)

**Files:**
- Create: `backend/app/lib/model_manager.py`
- Create: `backend/tests/lib/test_model_manager.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/lib/test_model_manager.py
import pytest
from app.lib.model_manager import ModelManager


@pytest.fixture
def manager():
    return ModelManager(
        resident_models=["mistral-small:latest", "nomic-embed-text"],
        exclusive_models=["deepseek-r1:70b", "llama4:latest", "qwen3-coder:30b"],
        ollama_base_url="http://localhost:11434",
    )


def test_resident_model_always_available(manager):
    assert manager.is_resident("mistral-small:latest")
    assert not manager.is_resident("deepseek-r1:70b")


def test_exclusive_model_tracking(manager):
    assert manager.current_exclusive is None


def test_needs_switch_when_different_exclusive(manager):
    manager._current_exclusive = "deepseek-r1:70b"
    assert manager.needs_switch("llama4:latest")
    assert not manager.needs_switch("deepseek-r1:70b")
    assert not manager.needs_switch("mistral-small:latest")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/Dev-Work/oyagami-local/backend
uv run pytest tests/lib/test_model_manager.py -v
# Expected: FAIL - ModuleNotFoundError
```

- [ ] **Step 3: Implement ModelManager**

```python
# backend/app/lib/model_manager.py
import httpx

from app.config import settings


class ModelManager:
    """Manages Ollama model lifecycle within 128GB memory budget.

    Resident models (mistral-small, nomic-embed-text) stay loaded.
    Exclusive models (deepseek-r1, llama4, qwen3-coder) are mutually exclusive.
    """

    def __init__(
        self,
        resident_models: list[str] | None = None,
        exclusive_models: list[str] | None = None,
        ollama_base_url: str | None = None,
    ):
        self._resident = set(resident_models or [])
        self._exclusive = set(exclusive_models or [])
        self._current_exclusive: str | None = None
        self._base_url = ollama_base_url or settings.ollama_base_url

    @property
    def current_exclusive(self) -> str | None:
        return self._current_exclusive

    def is_resident(self, model: str) -> bool:
        return model in self._resident

    def needs_switch(self, model: str) -> bool:
        if self.is_resident(model):
            return False
        return model != self._current_exclusive

    async def ensure_model(self, model: str) -> None:
        """Ensure the given model is loaded. Unloads conflicting exclusive model if needed."""
        if self.is_resident(model):
            return
        if not self.needs_switch(model):
            return

        async with httpx.AsyncClient(base_url=self._base_url, timeout=300) as client:
            # Unload current exclusive model
            if self._current_exclusive:
                await client.post(
                    "/api/generate",
                    json={
                        "model": self._current_exclusive,
                        "prompt": "",
                        "keep_alive": 0,
                    },
                )

            # Load new model with warmup
            await client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": "ready",
                    "keep_alive": "10m",
                },
            )
            self._current_exclusive = model

    async def unload_model(self, model: str) -> None:
        """Manually unload a model."""
        async with httpx.AsyncClient(base_url=self._base_url, timeout=60) as client:
            await client.post(
                "/api/generate",
                json={"model": model, "prompt": "", "keep_alive": 0},
            )
        if self._current_exclusive == model:
            self._current_exclusive = None

    async def get_status(self) -> dict:
        """Get current model loading status from Ollama."""
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=10) as client:
                resp = await client.get("/api/ps")
                resp.raise_for_status()
                data = resp.json()
                loaded = [m["name"] for m in data.get("models", [])]
                return {
                    "ollama_available": True,
                    "loaded_models": loaded,
                    "current_exclusive": self._current_exclusive,
                }
        except Exception:
            return {
                "ollama_available": False,
                "loaded_models": [],
                "current_exclusive": None,
            }

    async def initialize(self) -> None:
        """Startup: ensure resident models are loaded."""
        for model in self._resident:
            try:
                async with httpx.AsyncClient(
                    base_url=self._base_url, timeout=300
                ) as client:
                    await client.post(
                        "/api/generate",
                        json={"model": model, "prompt": "ready", "keep_alive": "24h"},
                    )
                print(f"Resident model loaded: {model}")
            except Exception as e:
                print(f"WARNING: Failed to load resident model {model}: {e}")


# Module-level singleton
model_manager = ModelManager(
    resident_models=[settings.coordinator_model, settings.embedding_model],
    exclusive_models=[
        settings.intake_model,
        settings.analyst_model,
        settings.cypher_model,
    ],
)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Dev-Work/oyagami-local/backend
uv run pytest tests/lib/test_model_manager.py -v
# Expected: 3 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/lib/model_manager.py backend/tests/lib/test_model_manager.py
git commit -m "feat: add ModelManager for Ollama model lifecycle management"
```

---

## Task 3: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/client.py`
- Create: `backend/app/schemas/narrative.py`
- Create: `backend/app/schemas/agent.py`

- [ ] **Step 1: Create client schemas**

```python
# backend/app/schemas/client.py
from pydantic import BaseModel


class ClientSummary(BaseModel):
    name: str
    dob: str | None = None
    age: int | None = None
    blood_type: str | None = None
    conditions: list[str] = []


class NgAction(BaseModel):
    action: str
    reason: str | None = None
    risk_level: str = "Discomfort"  # LifeThreatening | Panic | Discomfort


class CarePreference(BaseModel):
    category: str
    instruction: str
    priority: str | None = None


class KeyPerson(BaseModel):
    name: str
    relationship: str | None = None
    phone: str | None = None
    rank: int | None = None


class EmergencyInfo(BaseModel):
    client_name: str
    ng_actions: list[NgAction] = []
    care_preferences: list[CarePreference] = []
    key_persons: list[KeyPerson] = []
    hospital: dict | None = None
    guardian: dict | None = None


class SupportLogEntry(BaseModel):
    date: str | None = None
    situation: str | None = None
    action: str | None = None
    effectiveness: str | None = None
    note: str | None = None
    supporter_name: str | None = None


class ClientDetail(BaseModel):
    name: str
    dob: str | None = None
    age: int | None = None
    blood_type: str | None = None
    conditions: list[dict] = []
    ng_actions: list[NgAction] = []
    care_preferences: list[CarePreference] = []
    key_persons: list[KeyPerson] = []
    certificates: list[dict] = []
    hospital: dict | None = None
    guardian: dict | None = None


class DashboardStats(BaseModel):
    client_count: int = 0
    log_count_this_month: int = 0
    renewal_alerts: int = 0


class RenewalAlert(BaseModel):
    client_name: str
    certificate_type: str
    next_renewal_date: str
    days_remaining: int


class ActivityEntry(BaseModel):
    date: str
    client_name: str
    action: str
    summary: str
```

- [ ] **Step 2: Create narrative schemas**

```python
# backend/app/schemas/narrative.py
from pydantic import BaseModel


class GraphNode(BaseModel):
    temp_id: str
    label: str
    properties: dict


class GraphRelationship(BaseModel):
    source_temp_id: str
    target_temp_id: str
    type: str
    properties: dict = {}


class ExtractedGraph(BaseModel):
    nodes: list[GraphNode] = []
    relationships: list[GraphRelationship] = []


class ExtractionRequest(BaseModel):
    text: str
    client_name: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    corrected_graph: ExtractedGraph | None = None


class SafetyCheckResult(BaseModel):
    is_violation: bool
    warning: str | None = None
    risk_level: str = "None"  # High | Medium | Low | None


class RegistrationResult(BaseModel):
    status: str  # success | error
    client_name: str | None = None
    registered_count: int = 0
    registered_types: list[str] = []
    message: str | None = None


class QuickLogRequest(BaseModel):
    client_name: str
    note: str
    situation: str | None = None
    supporter_name: str = "system"
```

- [ ] **Step 3: Create agent schemas**

```python
# backend/app/schemas/agent.py
from pydantic import BaseModel
from enum import Enum


class IntentCategory(str, Enum):
    EMERGENCY = "emergency"
    DATA_REGISTRATION = "data_registration"
    QUERY = "query"
    ANALYSIS = "analysis"
    GENERAL = "general"


class RoutingDecision(BaseModel):
    intent: IntentCategory
    target_agent: str
    reason: str
    requires_model_switch: bool = False
    target_model: str | None = None


class ChatMessage(BaseModel):
    type: str  # message | routing | model_status | stream | metadata | done
    content: str | None = None
    agent: str | None = None
    session_id: str | None = None


class ChatRequest(BaseModel):
    content: str
    session_id: str


class ModelStatusResponse(BaseModel):
    ollama_available: bool
    neo4j_available: bool
    loaded_models: list[str] = []
    current_exclusive: str | None = None
    memory_usage_gb: float | None = None
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas for client, narrative, and agent models"
```

---

## Task 4: DB Operations (Migrate from current project)

**Files:**
- Create: `backend/app/lib/db_operations.py`
- Create: `backend/tests/lib/test_db_operations.py`
- Reference: `~/Dev-Work/neo4j-agno-agent/lib/db_new_operations.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/lib/test_db_operations.py
import pytest
from app.lib.db_operations import (
    ALLOWED_LABELS,
    ALLOWED_REL_TYPES,
    MERGE_KEYS,
    is_db_available,
)


def test_allowed_labels_include_core_types():
    assert "Client" in ALLOWED_LABELS
    assert "NgAction" in ALLOWED_LABELS
    assert "SupportLog" in ALLOWED_LABELS
    assert "CarePreference" in ALLOWED_LABELS


def test_allowed_rel_types_include_core_types():
    assert "MUST_AVOID" in ALLOWED_REL_TYPES
    assert "REQUIRES" in ALLOWED_REL_TYPES
    assert "LOGGED" in ALLOWED_REL_TYPES
    assert "ABOUT" in ALLOWED_REL_TYPES


def test_merge_keys_defined_for_core_labels():
    assert "Client" in MERGE_KEYS
    assert MERGE_KEYS["Client"] == ["name"]
    assert "NgAction" in MERGE_KEYS
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/Dev-Work/oyagami-local/backend
uv run pytest tests/lib/test_db_operations.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement db_operations.py**

Migrate from `~/Dev-Work/neo4j-agno-agent/lib/db_new_operations.py`. Key changes:
- Remove all `import streamlit` references
- Use `app.config.settings` instead of `os.getenv()` for Neo4j credentials
- Keep all Cypher query patterns, MERGE_KEYS, ALLOWED_LABELS, ALLOWED_REL_TYPES
- Keep `register_to_database()`, `run_query()`, `get_driver()`, `is_db_available()`
- Keep `create_audit_log()`, `get_audit_logs()`
- Add `close_driver()` for clean shutdown
- Remove pseudonymization (simplify for Phase 1)

```python
# backend/app/lib/db_operations.py
import logging
from datetime import datetime

from neo4j import GraphDatabase

from app.config import settings

logger = logging.getLogger(__name__)

_driver = None

MERGE_KEYS = {
    "Client": ["name"],
    "Supporter": ["name"],
    "NgAction": ["action"],
    "CarePreference": ["category", "instruction"],
    "Condition": ["name"],
    "KeyPerson": ["name"],
    "Organization": ["name"],
    "ServiceProvider": ["name"],
    "Hospital": ["name"],
    "Guardian": ["name"],
    "Certificate": ["type"],
}

ALLOWED_CREATE_LABELS = {
    "SupportLog", "LifeHistory", "Wish", "AuditLog", "PublicAssistance", "MeetingRecord",
}

ALLOWED_LABELS = set(MERGE_KEYS.keys()) | ALLOWED_CREATE_LABELS

ALLOWED_REL_TYPES = {
    "HAS_CONDITION", "MUST_AVOID", "IN_CONTEXT", "REQUIRES", "ADDRESSES",
    "HAS_KEY_PERSON", "HAS_LEGAL_REP", "HAS_CERTIFICATE", "RECEIVES",
    "REGISTERED_AT", "TREATED_AT", "SUPPORTED_BY", "LOGGED", "ABOUT",
    "FOLLOWS", "USES_SERVICE", "HAS_HISTORY", "HAS_WISH", "AUDIT_FOR",
    "HAS_IDENTITY", "RECORDED",
}


def get_driver():
    global _driver
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
            )
            _driver.verify_connectivity()
            logger.info(f"Neo4j connected: {settings.neo4j_uri}")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            _driver = None
    return _driver


def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def is_db_available() -> bool:
    driver = get_driver()
    if not driver:
        return False
    try:
        driver.verify_connectivity()
        return True
    except Exception:
        return False


def run_query(query: str, params: dict | None = None) -> list[dict]:
    driver = get_driver()
    if not driver:
        return []
    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Query failed: {e}\nQuery: {query}")
        return []


def register_to_database(extracted_graph: dict, user_name: str = "system") -> dict:
    """Register extracted graph to Neo4j.

    Args:
        extracted_graph: {"nodes": [...], "relationships": [...]}
        user_name: User performing the registration

    Returns:
        {"status": "success/error", "client_name": str, "registered_count": int, ...}
    """
    driver = get_driver()
    if not driver:
        return {"status": "error", "message": "Neo4j not available"}

    nodes = extracted_graph.get("nodes", [])
    relationships = extracted_graph.get("relationships", [])

    # Validate labels and relationship types
    for node in nodes:
        if node["label"] not in ALLOWED_LABELS:
            return {"status": "error", "message": f"Invalid label: {node['label']}"}
    for rel in relationships:
        if rel["type"] not in ALLOWED_REL_TYPES:
            return {"status": "error", "message": f"Invalid rel type: {rel['type']}"}

    temp_id_map = {}
    client_name = None
    registered_types = []

    try:
        with driver.session() as session:
            # Create/merge nodes
            for node in nodes:
                label = node["label"]
                props = node["properties"]
                temp_id = node.get("temp_id", "")

                if label == "Client":
                    client_name = props.get("name", "")

                if label in MERGE_KEYS:
                    keys = MERGE_KEYS[label]
                    merge_props = {k: props[k] for k in keys if k in props}
                    set_props = {k: v for k, v in props.items() if k not in keys}

                    where_clause = " AND ".join(
                        [f"n.{k} = ${k}" for k in merge_props]
                    )
                    set_clause = ", ".join(
                        [f"n.{k} = $set_{k}" for k in set_props]
                    )
                    params = {**merge_props}
                    params.update({f"set_{k}": v for k, v in set_props.items()})

                    query = f"MERGE (n:{label} {{{where_clause.replace(' AND ', ', ').replace('$', '').split('=')[0].strip() + ': $' + list(merge_props.keys())[0] if len(merge_props) == 1 else ''}}}"

                    # Simplified MERGE
                    merge_dict = ", ".join([f"{k}: ${k}" for k in merge_props])
                    query = f"MERGE (n:{label} {{{merge_dict}}})"
                    if set_props:
                        set_parts = ", ".join(
                            [f"n.{k} = $set_{k}" for k in set_props]
                        )
                        query += f" SET {set_parts}"
                    query += " RETURN elementId(n) AS eid"

                    result = session.run(query, params)
                    record = result.single()
                    if record:
                        temp_id_map[temp_id] = record["eid"]
                else:
                    # CREATE for SupportLog, LifeHistory, etc.
                    props_str = ", ".join([f"{k}: ${k}" for k in props])
                    query = f"CREATE (n:{label} {{{props_str}}}) RETURN elementId(n) AS eid"
                    result = session.run(query, props)
                    record = result.single()
                    if record:
                        temp_id_map[temp_id] = record["eid"]

                if label not in registered_types:
                    registered_types.append(label)

            # Create relationships
            for rel in relationships:
                src_eid = temp_id_map.get(rel["source_temp_id"])
                tgt_eid = temp_id_map.get(rel["target_temp_id"])
                if not src_eid or not tgt_eid:
                    continue

                rel_type = rel["type"]
                rel_props = rel.get("properties", {})
                props_str = ""
                if rel_props:
                    props_str = " {" + ", ".join(
                        [f"{k}: $rel_{k}" for k in rel_props]
                    ) + "}"
                    params = {f"rel_{k}": v for k, v in rel_props.items()}
                else:
                    params = {}

                params["src_eid"] = src_eid
                params["tgt_eid"] = tgt_eid

                query = (
                    f"MATCH (a) WHERE elementId(a) = $src_eid "
                    f"MATCH (b) WHERE elementId(b) = $tgt_eid "
                    f"MERGE (a)-[r:{rel_type}]->(b)"
                )
                if rel_props:
                    set_parts = ", ".join(
                        [f"r.{k} = $rel_{k}" for k in rel_props]
                    )
                    query += f" SET {set_parts}"

                session.run(query, params)

            # Audit log
            if client_name:
                create_audit_log(
                    user_name=user_name,
                    action="REGISTER",
                    target_type="Graph",
                    target_name=client_name,
                    details=f"Registered {len(nodes)} nodes, {len(relationships)} relationships",
                    client_name=client_name,
                )

        return {
            "status": "success",
            "client_name": client_name,
            "registered_count": len(nodes),
            "registered_types": registered_types,
        }

    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return {"status": "error", "message": str(e)}


def create_audit_log(
    user_name: str,
    action: str,
    target_type: str,
    target_name: str,
    details: str = "",
    client_name: str | None = None,
) -> dict:
    now = datetime.now().isoformat()
    query = """
    CREATE (a:AuditLog {
        userName: $user_name,
        action: $action,
        targetType: $target_type,
        targetName: $target_name,
        details: $details,
        timestamp: $timestamp
    })
    """
    params = {
        "user_name": user_name,
        "action": action,
        "target_type": target_type,
        "target_name": target_name,
        "details": details,
        "timestamp": now,
    }

    if client_name:
        query += """
        WITH a
        MATCH (c:Client {name: $client_name})
        MERGE (a)-[:AUDIT_FOR]->(c)
        """
        params["client_name"] = client_name

    query += " RETURN elementId(a) AS eid"
    records = run_query(query, params)
    return {"status": "ok"} if records else {"status": "error"}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd ~/Dev-Work/oyagami-local/backend
uv run pytest tests/lib/test_db_operations.py -v
# Expected: 3 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/lib/db_operations.py backend/tests/lib/test_db_operations.py
git commit -m "feat: add Neo4j db_operations (migrated from current project)"
```

---

## Task 5: Utils + File Readers (Migrate)

**Files:**
- Create: `backend/app/lib/utils.py`
- Create: `backend/app/lib/file_readers.py`
- Create: `backend/tests/lib/test_utils.py`
- Reference: `~/Dev-Work/neo4j-agno-agent/lib/utils.py`, `~/Dev-Work/neo4j-agno-agent/lib/file_readers.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/lib/test_utils.py
from datetime import date

from app.lib.utils import calculate_age, convert_wareki_to_seireki, safe_date_parse


def test_wareki_showa():
    assert convert_wareki_to_seireki("昭和50年3月15日") == "1975-03-15"


def test_wareki_reiwa():
    assert convert_wareki_to_seireki("令和5年1月10日") == "2023-01-10"


def test_wareki_alpha():
    assert convert_wareki_to_seireki("S50.3.15") == "1975-03-15"


def test_safe_date_parse_iso():
    result = safe_date_parse("2026-04-04")
    assert result == date(2026, 4, 4)


def test_safe_date_parse_wareki():
    result = safe_date_parse("令和8年4月4日")
    assert result == date(2026, 4, 4)


def test_calculate_age():
    age = calculate_age("2000-01-01", reference_date=date(2026, 4, 4))
    assert age == 26
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/lib/test_utils.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement utils.py**

Copy from `~/Dev-Work/neo4j-agno-agent/lib/utils.py`. Remove `init_session_state()`, `reset_session_state()`, `get_input_example()` (Streamlit-specific). Keep `convert_wareki_to_seireki()`, `safe_date_parse()`, `calculate_age()`, `format_date_with_age()`, `GENGO_MAP`.

```bash
# Copy and adapt
cp ~/Dev-Work/neo4j-agno-agent/lib/utils.py ~/Dev-Work/oyagami-local/backend/app/lib/utils.py
```

Then edit to remove Streamlit imports and functions (`init_session_state`, `reset_session_state`, `get_input_example`). Remove `import streamlit as st`.

- [ ] **Step 4: Implement file_readers.py**

Copy from `~/Dev-Work/neo4j-agno-agent/lib/file_readers.py`. Change `read_uploaded_file()` to accept `BinaryIO` + `filename: str` instead of Streamlit UploadedFile. Remove Gemini OCR fallback (use simple extraction only for Phase 1).

```bash
cp ~/Dev-Work/neo4j-agno-agent/lib/file_readers.py ~/Dev-Work/oyagami-local/backend/app/lib/file_readers.py
```

Then edit: replace `read_uploaded_file(uploaded_file)` signature with:

```python
def read_file(file: BinaryIO, filename: str) -> str:
    """Extract text from uploaded file based on extension."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".docx":
        return read_docx(file)
    elif suffix == ".xlsx":
        return read_xlsx(file)
    elif suffix == ".pdf":
        return read_pdf(file)
    elif suffix == ".txt":
        return read_txt(file)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
```

Remove `import streamlit` and Gemini OCR references.

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/lib/test_utils.py -v
# Expected: 6 passed
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/lib/utils.py backend/app/lib/file_readers.py backend/tests/lib/test_utils.py
git commit -m "feat: add utils (wareki/date) and file_readers (docx/xlsx/pdf/txt)"
```

---

## Task 6: Embedding (Ollama Adaptation)

**Files:**
- Create: `backend/app/lib/embedding.py`
- Create: `backend/tests/lib/test_embedding.py`
- Reference: `~/Dev-Work/neo4j-agno-agent/lib/embedding.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/lib/test_embedding.py
from app.lib.embedding import VECTOR_INDEXES, DEFAULT_DIMENSIONS


def test_default_dimensions():
    assert DEFAULT_DIMENSIONS == 768


def test_vector_indexes_defined():
    assert "support_log_embedding" in VECTOR_INDEXES
    assert "ng_action_embedding" in VECTOR_INDEXES
    assert "client_summary_embedding" in VECTOR_INDEXES


def test_vector_index_structure():
    idx = VECTOR_INDEXES["support_log_embedding"]
    assert idx["label"] == "SupportLog"
    assert idx["property"] == "embedding"
    assert idx["dimensions"] == 768
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/lib/test_embedding.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement embedding.py (Ollama version)**

```python
# backend/app/lib/embedding.py
import logging

import httpx

from app.config import settings
from app.lib.db_operations import run_query

logger = logging.getLogger(__name__)

DEFAULT_DIMENSIONS = 768

VECTOR_INDEXES = {
    "support_log_embedding": {
        "label": "SupportLog",
        "property": "embedding",
        "dimensions": DEFAULT_DIMENSIONS,
    },
    "care_preference_embedding": {
        "label": "CarePreference",
        "property": "embedding",
        "dimensions": DEFAULT_DIMENSIONS,
    },
    "ng_action_embedding": {
        "label": "NgAction",
        "property": "embedding",
        "dimensions": DEFAULT_DIMENSIONS,
    },
    "client_summary_embedding": {
        "label": "Client",
        "property": "summaryEmbedding",
        "dimensions": DEFAULT_DIMENSIONS,
    },
    "meeting_record_embedding": {
        "label": "MeetingRecord",
        "property": "embedding",
        "dimensions": DEFAULT_DIMENSIONS,
    },
    "meeting_record_text_embedding": {
        "label": "MeetingRecord",
        "property": "textEmbedding",
        "dimensions": DEFAULT_DIMENSIONS,
    },
}


async def embed_text(text: str) -> list[float] | None:
    """Generate embedding for text using Ollama nomic-embed-text."""
    try:
        async with httpx.AsyncClient(
            base_url=settings.ollama_base_url, timeout=30
        ) as client:
            resp = await client.post(
                "/api/embed",
                json={"model": settings.embedding_model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["embeddings"][0]
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return None


async def embed_texts_batch(texts: list[str]) -> list[list[float] | None]:
    """Batch embedding generation."""
    try:
        async with httpx.AsyncClient(
            base_url=settings.ollama_base_url, timeout=60
        ) as client:
            resp = await client.post(
                "/api/embed",
                json={"model": settings.embedding_model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["embeddings"]
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        return [None] * len(texts)


def semantic_search(
    query_embedding: list[float],
    index_name: str = "support_log_embedding",
    top_k: int = 10,
) -> list[dict]:
    """Search Neo4j vector index with pre-computed query embedding."""
    idx = VECTOR_INDEXES.get(index_name)
    if not idx:
        return []

    query = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
    YIELD node, score
    RETURN node, score
    ORDER BY score DESC
    """
    records = run_query(
        query,
        {
            "index_name": index_name,
            "top_k": top_k,
            "query_embedding": query_embedding,
        },
    )
    return [{"node": dict(r["node"]), "score": r["score"]} for r in records]


def ensure_vector_indexes() -> None:
    """Create vector indexes if they don't exist (idempotent)."""
    for name, idx in VECTOR_INDEXES.items():
        query = f"""
        CREATE VECTOR INDEX {name} IF NOT EXISTS
        FOR (n:{idx['label']})
        ON (n.{idx['property']})
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {idx['dimensions']},
            `vector.similarity_function`: 'cosine'
        }}}}
        """
        run_query(query)
    logger.info(f"Ensured {len(VECTOR_INDEXES)} vector indexes")
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/lib/test_embedding.py -v
# Expected: 3 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/lib/embedding.py backend/tests/lib/test_embedding.py
git commit -m "feat: add embedding module with Ollama nomic-embed-text support"
```

---

## Task 7: Agent Prompts

**Files:**
- Create: `backend/app/agents/prompts/manifesto.md`
- Create: `backend/app/agents/prompts/extraction.md`
- Create: `backend/app/agents/prompts/safety.md`

- [ ] **Step 1: Copy manifesto from current project**

```bash
cp ~/Dev-Work/neo4j-agno-agent/agents/MANIFESTO.md ~/Dev-Work/oyagami-local/backend/app/agents/prompts/manifesto.md
```

- [ ] **Step 2: Create extraction.md**

Extract EXTRACTION_PROMPT from `~/Dev-Work/neo4j-agno-agent/lib/ai_extractor.py` (lines 27-123) and save as `backend/app/agents/prompts/extraction.md`. This is the complete prompt that defines the Neo4j schema, naming conventions, and extraction rules. Copy the exact content from the EXTRACTION_PROMPT variable — it is critical for maintaining data schema compatibility with the existing Neo4j database.

- [ ] **Step 3: Create safety.md**

```markdown
# Safety Compliance Check Prompt

あなたは障害福祉支援の安全チェック担当です。
以下のナラティブテキストが、既知の禁忌事項（NgAction）に違反していないかを確認してください。

## 禁忌事項一覧
{ng_actions}

## 確認するテキスト
{narrative}

## 出力形式（JSONのみ）
{
  "is_violation": true/false,
  "warning": "違反内容の説明（違反がない場合はnull）",
  "risk_level": "High/Medium/Low/None"
}

## ルール
- 禁忌事項と矛盾する行為が記述されていれば is_violation=true
- LifeThreatening レベルの禁忌は risk_level=High
- Panic レベルの禁忌は risk_level=Medium
- 違反がなければ is_violation=false, risk_level=None
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/prompts/
git commit -m "feat: add agent prompts (manifesto, extraction, safety)"
```

---

## Task 8: Coordinator Agent

**Files:**
- Create: `backend/app/agents/coordinator.py`
- Create: `backend/tests/agents/test_coordinator.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/agents/test_coordinator.py
import pytest
from app.agents.coordinator import classify_intent
from app.schemas.agent import IntentCategory


@pytest.mark.parametrize(
    "text,expected",
    [
        ("田中さんがパニックを起こしている", IntentCategory.EMERGENCY),
        ("SOS 助けて", IntentCategory.EMERGENCY),
        ("昨日の通所の様子を記録して", IntentCategory.DATA_REGISTRATION),
        ("以下の内容を登録してください", IntentCategory.DATA_REGISTRATION),
        ("佐藤さんの禁忌事項の一覧を教えて", IntentCategory.QUERY),
        ("クライアント一覧を見せて", IntentCategory.QUERY),
        ("最近の支援傾向を分析して", IntentCategory.ANALYSIS),
        ("田中さんと佐藤さんを比較して", IntentCategory.ANALYSIS),
        ("こんにちは", IntentCategory.GENERAL),
        ("使い方を教えて", IntentCategory.GENERAL),
    ],
)
def test_classify_intent_keyword_fallback(text, expected):
    """Test keyword-based fallback classification (no LLM needed)."""
    result = classify_intent(text)
    assert result.intent == expected
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/agents/test_coordinator.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement coordinator.py**

```python
# backend/app/agents/coordinator.py
import json
import logging
import re

import httpx

from app.config import settings
from app.schemas.agent import IntentCategory, RoutingDecision

logger = logging.getLogger(__name__)

EMERGENCY_KEYWORDS = {"パニック", "SOS", "事故", "発作", "倒れた", "救急", "助けて", "緊急"}
REGISTRATION_KEYWORDS = {"登録", "記録して", "入力", "保存して", "記載して"}
ANALYSIS_KEYWORDS = {"分析", "比較", "方針", "傾向", "なぜ", "考察", "評価"}
QUERY_KEYWORDS = {"教えて", "一覧", "検索", "確認", "見せて", "表示", "リスト"}

ROUTING_MAP = {
    IntentCategory.EMERGENCY: ("direct_db", None),
    IntentCategory.DATA_REGISTRATION: ("intake", settings.intake_model),
    IntentCategory.QUERY: ("cypher_gen", settings.cypher_model),
    IntentCategory.ANALYSIS: ("analyst", settings.analyst_model),
    IntentCategory.GENERAL: ("self", None),
}

COORDINATOR_SYSTEM_PROMPT = """あなたはユーザーの意図を分類するルーティングエージェントです。
以下の5つのカテゴリから最も適切なものを1つ選び、JSONで回答してください。

カテゴリ:
- emergency: 緊急事態（パニック、事故、SOS、発作、救急）
- data_registration: データの登録・記録の依頼
- query: 情報の検索・一覧表示・確認
- analysis: 分析・比較・方針策定・傾向分析
- general: 挨拶、ヘルプ、雑談

出力形式（JSONのみ）:
{"intent": "カテゴリ名", "reason": "判定理由（10文字以内）"}
"""


def classify_intent(text: str) -> RoutingDecision:
    """Classify user intent using keyword matching (fast, no LLM).

    This is the fallback classifier. For production use,
    route_with_llm() uses mistral-small for better accuracy.
    """
    text_lower = text.lower()

    # Emergency has highest priority
    if any(kw in text for kw in EMERGENCY_KEYWORDS):
        return _build_decision(IntentCategory.EMERGENCY, "緊急キーワード検知")

    if any(kw in text for kw in REGISTRATION_KEYWORDS):
        return _build_decision(IntentCategory.DATA_REGISTRATION, "登録キーワード検知")

    if any(kw in text for kw in ANALYSIS_KEYWORDS):
        return _build_decision(IntentCategory.ANALYSIS, "分析キーワード検知")

    if any(kw in text for kw in QUERY_KEYWORDS):
        return _build_decision(IntentCategory.QUERY, "検索キーワード検知")

    return _build_decision(IntentCategory.GENERAL, "一般的な発言")


async def route_with_llm(text: str) -> RoutingDecision:
    """Classify user intent using mistral-small LLM for better accuracy."""
    # First try keyword-based for emergency (speed critical)
    if any(kw in text for kw in EMERGENCY_KEYWORDS):
        return _build_decision(IntentCategory.EMERGENCY, "緊急キーワード検知")

    try:
        async with httpx.AsyncClient(
            base_url=settings.ollama_base_url, timeout=30
        ) as client:
            resp = await client.post(
                "/api/chat",
                json={
                    "model": settings.coordinator_model,
                    "messages": [
                        {"role": "system", "content": COORDINATOR_SYSTEM_PROMPT},
                        {"role": "user", "content": text},
                    ],
                    "stream": False,
                    "options": {"temperature": 0},
                },
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]

            # Parse JSON from response
            match = re.search(r"\{[^}]+\}", content)
            if match:
                data = json.loads(match.group())
                intent = IntentCategory(data["intent"])
                reason = data.get("reason", "LLM分類")
                return _build_decision(intent, reason)
    except Exception as e:
        logger.warning(f"LLM routing failed, falling back to keywords: {e}")

    # Fallback to keyword-based
    return classify_intent(text)


def _build_decision(intent: IntentCategory, reason: str) -> RoutingDecision:
    target_agent, target_model = ROUTING_MAP[intent]
    return RoutingDecision(
        intent=intent,
        target_agent=target_agent,
        reason=reason,
        requires_model_switch=target_model is not None,
        target_model=target_model,
    )
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/agents/test_coordinator.py -v
# Expected: 10 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/coordinator.py backend/tests/agents/test_coordinator.py
git commit -m "feat: add Coordinator agent with intent classification and LLM routing"
```

---

## Task 9: Intake Agent

**Files:**
- Create: `backend/app/agents/intake.py`
- Create: `backend/tests/agents/test_intake.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/agents/test_intake.py
from app.agents.intake import parse_json_from_response, get_extraction_prompt


def test_parse_json_direct():
    raw = '{"nodes": [], "relationships": []}'
    result = parse_json_from_response(raw)
    assert result == {"nodes": [], "relationships": []}


def test_parse_json_markdown_block():
    raw = '```json\n{"nodes": [{"temp_id": "c1", "label": "Client", "properties": {"name": "田中"}}], "relationships": []}\n```'
    result = parse_json_from_response(raw)
    assert result is not None
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["label"] == "Client"


def test_parse_json_invalid():
    assert parse_json_from_response("not json at all") is None


def test_extraction_prompt_exists():
    prompt = get_extraction_prompt()
    assert "ノードラベル" in prompt
    assert "Client" in prompt
    assert "NgAction" in prompt
    assert "MUST_AVOID" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/agents/test_intake.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement intake.py**

```python
# backend/app/agents/intake.py
import json
import logging
import re
from pathlib import Path

import httpx

from app.config import settings
from app.lib.model_manager import model_manager

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"


def get_extraction_prompt() -> str:
    """Load extraction prompt from file."""
    return (PROMPT_DIR / "extraction.md").read_text(encoding="utf-8")


def parse_json_from_response(response_text: str) -> dict | None:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try direct parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first { ... } block
    match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


async def extract_from_text(
    text: str, client_name: str | None = None
) -> dict | None:
    """Extract structured graph data from narrative text using deepseek-r1:70b.

    Args:
        text: Input narrative text
        client_name: Existing client name (for append mode)

    Returns:
        {"nodes": [...], "relationships": [...]} or None
    """
    await model_manager.ensure_model(settings.intake_model)

    prompt = get_extraction_prompt()
    user_message = text
    if client_name:
        user_message = f"【対象クライアント: {client_name}】\n\n{text}"

    try:
        async with httpx.AsyncClient(
            base_url=settings.ollama_base_url, timeout=300
        ) as client:
            resp = await client.post(
                "/api/chat",
                json={
                    "model": settings.intake_model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "stream": False,
                    "options": {"temperature": 0},
                },
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            return parse_json_from_response(content)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/agents/test_intake.py -v
# Expected: 4 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/intake.py backend/tests/agents/test_intake.py
git commit -m "feat: add Intake agent for text-to-JSON extraction via deepseek-r1"
```

---

## Task 10: Validator Agent

**Files:**
- Create: `backend/app/agents/validator.py`
- Create: `backend/tests/agents/test_validator.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/agents/test_validator.py
from app.agents.validator import validate_schema
from app.lib.db_operations import ALLOWED_LABELS, ALLOWED_REL_TYPES


def test_valid_graph_passes():
    graph = {
        "nodes": [
            {"temp_id": "c1", "label": "Client", "properties": {"name": "田中太郎"}},
            {"temp_id": "ng1", "label": "NgAction", "properties": {"action": "大きな音", "riskLevel": "Panic"}},
        ],
        "relationships": [
            {"source_temp_id": "c1", "target_temp_id": "ng1", "type": "MUST_AVOID", "properties": {}},
        ],
    }
    result = validate_schema(graph)
    assert result.is_valid
    assert len(result.errors) == 0


def test_invalid_label_fails():
    graph = {
        "nodes": [
            {"temp_id": "x1", "label": "InvalidLabel", "properties": {"name": "test"}},
        ],
        "relationships": [],
    }
    result = validate_schema(graph)
    assert not result.is_valid
    assert any("InvalidLabel" in e for e in result.errors)


def test_invalid_rel_type_fails():
    graph = {
        "nodes": [
            {"temp_id": "c1", "label": "Client", "properties": {"name": "田中"}},
            {"temp_id": "ng1", "label": "NgAction", "properties": {"action": "test"}},
        ],
        "relationships": [
            {"source_temp_id": "c1", "target_temp_id": "ng1", "type": "PROHIBITED", "properties": {}},
        ],
    }
    result = validate_schema(graph)
    assert not result.is_valid
    assert any("PROHIBITED" in e for e in result.errors)


def test_missing_temp_id_warning():
    graph = {
        "nodes": [
            {"temp_id": "c1", "label": "Client", "properties": {"name": "田中"}},
        ],
        "relationships": [
            {"source_temp_id": "c1", "target_temp_id": "missing_id", "type": "MUST_AVOID", "properties": {}},
        ],
    }
    result = validate_schema(graph)
    assert len(result.warnings) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/agents/test_validator.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement validator.py**

```python
# backend/app/agents/validator.py
import json
import logging
import re
from pathlib import Path

import httpx

from app.config import settings
from app.lib.db_operations import ALLOWED_LABELS, ALLOWED_REL_TYPES, MERGE_KEYS, run_query
from app.schemas.narrative import SafetyCheckResult, ValidationResult

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"


def validate_schema(graph: dict) -> ValidationResult:
    """Validate extracted graph against Neo4j schema rules.

    Checks:
    - Node labels are in ALLOWED_LABELS
    - Relationship types are in ALLOWED_REL_TYPES
    - temp_id references are consistent
    - Required properties are present for MERGE_KEYS labels
    """
    errors = []
    warnings = []
    nodes = graph.get("nodes", [])
    relationships = graph.get("relationships", [])
    temp_ids = {n["temp_id"] for n in nodes}

    for node in nodes:
        label = node.get("label", "")
        if label not in ALLOWED_LABELS:
            errors.append(f"Invalid node label: {label}")

        if label in MERGE_KEYS:
            required = MERGE_KEYS[label]
            props = node.get("properties", {})
            for key in required:
                if key not in props or not props[key]:
                    errors.append(f"{label} node missing required property: {key}")

    for rel in relationships:
        rel_type = rel.get("type", "")
        if rel_type not in ALLOWED_REL_TYPES:
            errors.append(f"Invalid relationship type: {rel_type}")

        if rel["source_temp_id"] not in temp_ids:
            warnings.append(f"Relationship source '{rel['source_temp_id']}' not found in nodes")
        if rel["target_temp_id"] not in temp_ids:
            warnings.append(f"Relationship target '{rel['target_temp_id']}' not found in nodes")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


async def check_safety_compliance(
    narrative: str, client_name: str | None = None
) -> SafetyCheckResult:
    """Check if narrative violates existing NgActions for the client."""
    if not client_name:
        return SafetyCheckResult(is_violation=False, risk_level="None")

    # Fetch existing NgActions from DB
    records = run_query(
        "MATCH (c:Client {name: $name})-[:MUST_AVOID]->(ng:NgAction) RETURN ng",
        {"name": client_name},
    )
    if not records:
        return SafetyCheckResult(is_violation=False, risk_level="None")

    ng_actions = [dict(r["ng"]) for r in records]

    # Use mistral-small to check for violations
    safety_prompt = (PROMPT_DIR / "safety.md").read_text(encoding="utf-8")
    safety_prompt = safety_prompt.replace("{ng_actions}", json.dumps(ng_actions, ensure_ascii=False))
    safety_prompt = safety_prompt.replace("{narrative}", narrative)

    try:
        async with httpx.AsyncClient(
            base_url=settings.ollama_base_url, timeout=30
        ) as client:
            resp = await client.post(
                "/api/chat",
                json={
                    "model": settings.validator_model,
                    "messages": [
                        {"role": "system", "content": safety_prompt},
                        {"role": "user", "content": "安全性を確認してください。"},
                    ],
                    "stream": False,
                    "options": {"temperature": 0},
                },
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            match = re.search(r"\{[^}]+\}", content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return SafetyCheckResult(**data)
    except Exception as e:
        logger.warning(f"Safety check failed: {e}")

    return SafetyCheckResult(is_violation=False, risk_level="None")
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/agents/test_validator.py -v
# Expected: 4 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/validator.py backend/tests/agents/test_validator.py
git commit -m "feat: add Validator agent for schema validation and safety compliance"
```

---

## Task 11: CypherGen Agent

**Files:**
- Create: `backend/app/agents/cypher_gen.py`

- [ ] **Step 1: Implement cypher_gen.py**

```python
# backend/app/agents/cypher_gen.py
import json
import logging
import re

import httpx

from app.config import settings
from app.lib.db_operations import run_query
from app.lib.model_manager import model_manager

logger = logging.getLogger(__name__)

CYPHER_SYSTEM_PROMPT = """あなたはNeo4jのCypherクエリ生成の専門家です。
ユーザーの自然言語リクエストを正確なCypherクエリに変換してください。

## Neo4jスキーマ
ノード: Client, Condition, NgAction, CarePreference, KeyPerson, Guardian, Hospital,
        Certificate, Supporter, SupportLog, Organization, ServiceProvider

リレーション: HAS_CONDITION, MUST_AVOID, REQUIRES, HAS_KEY_PERSON, HAS_LEGAL_REP,
             HAS_CERTIFICATE, TREATED_AT, LOGGED, ABOUT, FOLLOWS

プロパティ命名: camelCase (name, dob, riskLevel, nextRenewalDate, effectiveness)

## 出力形式（JSONのみ）
{"cypher": "MATCH (c:Client)...", "params": {"key": "value"}, "description": "クエリの説明"}

## ルール
- パラメータ化クエリを使用（$param形式、Cypher injection防止）
- OPTIONAL MATCHを適切に使用（欠損データへの耐性）
- LIMIT句を含める（デフォルト50件）
- 読み取りクエリのみ生成（MERGE/CREATE/DELETE禁止）
"""


async def generate_cypher(question: str) -> dict | None:
    """Generate a Cypher query from natural language question.

    Args:
        question: Natural language question about the database

    Returns:
        {"cypher": str, "params": dict, "description": str} or None
    """
    await model_manager.ensure_model(settings.cypher_model)

    try:
        async with httpx.AsyncClient(
            base_url=settings.ollama_base_url, timeout=120
        ) as client:
            resp = await client.post(
                "/api/chat",
                json={
                    "model": settings.cypher_model,
                    "messages": [
                        {"role": "system", "content": CYPHER_SYSTEM_PROMPT},
                        {"role": "user", "content": question},
                    ],
                    "stream": False,
                    "options": {"temperature": 0},
                },
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]

            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
    except Exception as e:
        logger.error(f"Cypher generation failed: {e}")

    return None


async def query_with_cypher(question: str) -> dict:
    """Generate Cypher from question, execute it, and return results."""
    cypher_data = await generate_cypher(question)
    if not cypher_data:
        return {"error": "Failed to generate Cypher query", "results": []}

    cypher = cypher_data.get("cypher", "")
    params = cypher_data.get("params", {})

    # Safety check: reject write queries
    upper = cypher.upper()
    if any(kw in upper for kw in ["CREATE", "MERGE", "DELETE", "SET ", "REMOVE"]):
        return {"error": "Write queries are not allowed", "results": []}

    results = run_query(cypher, params)
    return {
        "cypher": cypher,
        "params": params,
        "description": cypher_data.get("description", ""),
        "results": results,
        "count": len(results),
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/agents/cypher_gen.py
git commit -m "feat: add CypherGen agent for natural language to Cypher translation"
```

---

## Task 12: Analyst Agent + Team Composition

**Files:**
- Create: `backend/app/agents/analyst.py`
- Create: `backend/app/agents/team.py`

- [ ] **Step 1: Implement analyst.py**

```python
# backend/app/agents/analyst.py
import logging

import httpx

from app.config import settings
from app.lib.model_manager import model_manager

logger = logging.getLogger(__name__)

ANALYST_SYSTEM_PROMPT = """あなたは障害福祉支援の専門アナリストです。
グラフデータベースから取得した支援データを分析し、支援方針を策定します。

## 分析の観点
1. 支援記録の傾向分析（effectiveness の推移、situation の分布）
2. リスク評価（NgAction の重要度と頻度）
3. ケアの改善提案（CarePreference の見直し）
4. 類似事例との比較分析
5. 親の機能移行の進捗確認

## 出力ルール
- 日本語で回答
- 根拠となるデータを引用
- 具体的なアクション提案を含める
- 安全に関する警告は最優先で表示
"""


async def analyze(question: str, context_data: list[dict]) -> str:
    """Analyze data and provide support insights.

    Args:
        question: User's analysis question
        context_data: Data retrieved from Neo4j by CypherGen

    Returns:
        Analysis text in Japanese
    """
    await model_manager.ensure_model(settings.analyst_model)

    context_str = "\n".join(
        [f"- {str(record)}" for record in context_data[:20]]  # Limit context size
    )

    try:
        async with httpx.AsyncClient(
            base_url=settings.ollama_base_url, timeout=300
        ) as client:
            resp = await client.post(
                "/api/chat",
                json={
                    "model": settings.analyst_model,
                    "messages": [
                        {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": f"## 質問\n{question}\n\n## データ\n{context_str}",
                        },
                    ],
                    "stream": False,
                    "options": {"temperature": 0.3},
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return f"分析中にエラーが発生しました: {e}"
```

- [ ] **Step 2: Implement team.py (orchestration)**

```python
# backend/app/agents/team.py
import logging

from app.agents.analyst import analyze
from app.agents.coordinator import route_with_llm
from app.agents.cypher_gen import query_with_cypher
from app.agents.intake import extract_from_text
from app.agents.validator import check_safety_compliance, validate_schema
from app.lib.db_operations import run_query
from app.schemas.agent import IntentCategory, RoutingDecision

logger = logging.getLogger(__name__)


async def process_message(text: str, session_id: str | None = None) -> dict:
    """Main entry point: route user message to appropriate agent(s).

    Returns:
        {
            "routing": RoutingDecision,
            "response": str,
            "metadata": dict,
        }
    """
    # Step 1: Route
    decision = await route_with_llm(text)
    metadata = {"agents_used": [decision.target_agent], "model_switches": 0}

    # Step 2: Execute based on intent
    if decision.intent == IntentCategory.EMERGENCY:
        response = await _handle_emergency(text)

    elif decision.intent == IntentCategory.DATA_REGISTRATION:
        response = await _handle_registration(text)
        metadata["model_switches"] = 1

    elif decision.intent == IntentCategory.QUERY:
        response = await _handle_query(text)
        metadata["model_switches"] = 1
        metadata["agents_used"].append("cypher_gen")

    elif decision.intent == IntentCategory.ANALYSIS:
        response = await _handle_analysis(text)
        metadata["model_switches"] = 2  # llama4 → qwen3 → llama4
        metadata["agents_used"].extend(["analyst", "cypher_gen"])

    else:
        response = "何かお手伝いできることはありますか？支援記録の登録、クライアント情報の検索、支援傾向の分析などが可能です。"

    return {
        "routing": decision,
        "response": response,
        "metadata": metadata,
    }


async def _handle_emergency(text: str) -> str:
    """Safety First: direct DB search, no LLM needed."""
    # Extract client name from text (simple heuristic)
    import re
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
               collect(DISTINCT kp) AS key_persons,
               h, g
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


async def _handle_registration(text: str) -> str:
    """Extract → Validate → return preview (registration waits for user confirmation)."""
    extracted = await extract_from_text(text)
    if not extracted:
        return "テキストからデータを抽出できませんでした。入力内容を確認してください。"

    validation = validate_schema(extracted)
    if not validation.is_valid:
        errors_str = "\n".join(validation.errors)
        return f"抽出データにエラーがあります:\n{errors_str}\n\n入力内容を修正してください。"

    # Return preview for user confirmation (actual registration happens via /api/narratives/register)
    import json
    preview = json.dumps(extracted, ensure_ascii=False, indent=2)
    node_count = len(extracted.get("nodes", []))
    rel_count = len(extracted.get("relationships", []))
    return f"以下のデータを抽出しました（ノード{node_count}件、リレーション{rel_count}件）。\n登録画面で確認・承認してください。\n\n```json\n{preview}\n```"


async def _handle_query(text: str) -> str:
    """Generate Cypher and execute query."""
    result = await query_with_cypher(text)
    if "error" in result:
        return f"クエリの生成に失敗しました: {result['error']}"

    import json
    results_str = json.dumps(result["results"][:10], ensure_ascii=False, indent=2)
    return f"{result.get('description', '')}\n\n結果（{result['count']}件）:\n```json\n{results_str}\n```"


async def _handle_analysis(text: str) -> str:
    """Analyst generates plan → CypherGen fetches data → Analyst analyzes."""
    # Step 1: Use CypherGen to get relevant data
    query_result = await query_with_cypher(text)
    data = query_result.get("results", [])

    if not data:
        return "分析に必要なデータが見つかりませんでした。質問を具体的にしてください。"

    # Step 2: Analyst analyzes the data
    analysis = await analyze(text, data)
    return analysis
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/agents/analyst.py backend/app/agents/team.py
git commit -m "feat: add Analyst agent and Team orchestration with full routing pipeline"
```

---

## Task 13: API Routers (Dashboard, Clients, System)

**Files:**
- Create: `backend/app/routers/dashboard.py`
- Create: `backend/app/routers/clients.py`
- Create: `backend/app/routers/system.py`

- [ ] **Step 1: Implement dashboard.py**

```python
# backend/app/routers/dashboard.py
from datetime import datetime, timedelta

from fastapi import APIRouter

from app.lib.db_operations import is_db_available, run_query
from app.schemas.client import ActivityEntry, DashboardStats, RenewalAlert

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats():
    if not is_db_available():
        return DashboardStats()

    client_count = run_query("MATCH (c:Client) RETURN count(c) AS cnt")
    now = datetime.now()
    first_of_month = now.replace(day=1).strftime("%Y-%m-%d")
    log_count = run_query(
        "MATCH (s:SupportLog) WHERE s.date >= $start RETURN count(s) AS cnt",
        {"start": first_of_month},
    )
    cutoff = (now + timedelta(days=60)).strftime("%Y-%m-%d")
    alerts = run_query(
        "MATCH (c:Client)-[:HAS_CERTIFICATE]->(cert:Certificate) "
        "WHERE cert.nextRenewalDate <= $cutoff AND cert.nextRenewalDate >= $today "
        "RETURN count(cert) AS cnt",
        {"cutoff": cutoff, "today": now.strftime("%Y-%m-%d")},
    )
    return DashboardStats(
        client_count=client_count[0]["cnt"] if client_count else 0,
        log_count_this_month=log_count[0]["cnt"] if log_count else 0,
        renewal_alerts=alerts[0]["cnt"] if alerts else 0,
    )


@router.get("/alerts", response_model=list[RenewalAlert])
async def get_alerts():
    now = datetime.now()
    cutoff = (now + timedelta(days=90)).strftime("%Y-%m-%d")
    records = run_query(
        """
        MATCH (c:Client)-[:HAS_CERTIFICATE]->(cert:Certificate)
        WHERE cert.nextRenewalDate <= $cutoff AND cert.nextRenewalDate >= $today
        RETURN c.name AS client_name, cert.type AS certificate_type,
               cert.nextRenewalDate AS next_renewal_date
        ORDER BY cert.nextRenewalDate
        """,
        {"cutoff": cutoff, "today": now.strftime("%Y-%m-%d")},
    )
    result = []
    for r in records:
        renewal = datetime.strptime(r["next_renewal_date"], "%Y-%m-%d")
        days = (renewal - now).days
        result.append(RenewalAlert(
            client_name=r["client_name"],
            certificate_type=r["certificate_type"],
            next_renewal_date=r["next_renewal_date"],
            days_remaining=days,
        ))
    return result


@router.get("/activity", response_model=list[ActivityEntry])
async def get_activity():
    records = run_query(
        """
        MATCH (a:AuditLog)
        OPTIONAL MATCH (a)-[:AUDIT_FOR]->(c:Client)
        RETURN a.timestamp AS date, coalesce(c.name, 'system') AS client_name,
               a.action AS action, a.details AS summary
        ORDER BY a.timestamp DESC LIMIT 20
        """
    )
    return [ActivityEntry(**r) for r in records]
```

- [ ] **Step 2: Implement clients.py**

```python
# backend/app/routers/clients.py
from fastapi import APIRouter, Query

from app.lib.db_operations import run_query
from app.lib.utils import calculate_age
from app.schemas.client import ClientDetail, ClientSummary, EmergencyInfo, SupportLogEntry

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientSummary])
async def list_clients(kana_prefix: str | None = Query(None)):
    query = "MATCH (c:Client) "
    params = {}
    if kana_prefix:
        query += "WHERE c.kana STARTS WITH $prefix "
        params["prefix"] = kana_prefix
    query += """
    OPTIONAL MATCH (c)-[:HAS_CONDITION]->(cond:Condition)
    RETURN c.name AS name, c.dob AS dob, c.bloodType AS blood_type,
           collect(DISTINCT cond.name) AS conditions
    ORDER BY c.name
    """
    records = run_query(query, params)
    result = []
    for r in records:
        age = calculate_age(r["dob"]) if r.get("dob") else None
        result.append(ClientSummary(
            name=r["name"], dob=r.get("dob"), age=age,
            blood_type=r.get("blood_type"), conditions=r.get("conditions", []),
        ))
    return result


@router.get("/{name}", response_model=ClientDetail)
async def get_client(name: str):
    records = run_query(
        """
        MATCH (c:Client {name: $name})
        OPTIONAL MATCH (c)-[:HAS_CONDITION]->(cond:Condition)
        OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
        OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
        OPTIONAL MATCH (c)-[:HAS_KEY_PERSON]->(kp:KeyPerson)
        OPTIONAL MATCH (c)-[:HAS_CERTIFICATE]->(cert:Certificate)
        OPTIONAL MATCH (c)-[:TREATED_AT]->(h:Hospital)
        OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)
        RETURN c, collect(DISTINCT cond) AS conditions,
               collect(DISTINCT ng) AS ng_actions,
               collect(DISTINCT cp) AS care_prefs,
               collect(DISTINCT kp) AS key_persons,
               collect(DISTINCT cert) AS certificates,
               h, g
        """,
        {"name": name},
    )
    if not records:
        return ClientDetail(name=name)

    r = records[0]
    c = dict(r["c"])
    age = calculate_age(c.get("dob")) if c.get("dob") else None
    return ClientDetail(
        name=c.get("name", name),
        dob=c.get("dob"),
        age=age,
        blood_type=c.get("bloodType"),
        conditions=[dict(x) for x in r.get("conditions", [])],
        ng_actions=[dict(x) for x in r.get("ng_actions", [])],
        care_preferences=[dict(x) for x in r.get("care_prefs", [])],
        key_persons=[dict(x) for x in r.get("key_persons", [])],
        certificates=[dict(x) for x in r.get("certificates", [])],
        hospital=dict(r["h"]) if r.get("h") else None,
        guardian=dict(r["g"]) if r.get("g") else None,
    )


@router.get("/{name}/emergency", response_model=EmergencyInfo)
async def get_emergency_info(name: str):
    records = run_query(
        """
        MATCH (c:Client {name: $name})
        OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
        OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
        OPTIONAL MATCH (c)-[:HAS_KEY_PERSON]->(kp:KeyPerson)
        OPTIONAL MATCH (c)-[:TREATED_AT]->(h:Hospital)
        OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)
        RETURN collect(DISTINCT ng) AS ng_actions,
               collect(DISTINCT cp) AS care_prefs,
               collect(DISTINCT kp) AS key_persons,
               h, g
        """,
        {"name": name},
    )
    if not records:
        return EmergencyInfo(client_name=name)

    r = records[0]
    return EmergencyInfo(
        client_name=name,
        ng_actions=[dict(x) for x in r.get("ng_actions", [])],
        care_preferences=[dict(x) for x in r.get("care_prefs", [])],
        key_persons=sorted(
            [dict(x) for x in r.get("key_persons", [])],
            key=lambda x: x.get("rank", 99),
        ),
        hospital=dict(r["h"]) if r.get("h") else None,
        guardian=dict(r["g"]) if r.get("g") else None,
    )


@router.get("/{name}/logs", response_model=list[SupportLogEntry])
async def get_support_logs(name: str, limit: int = Query(50)):
    records = run_query(
        """
        MATCH (s:SupportLog)-[:ABOUT]->(c:Client {name: $name})
        OPTIONAL MATCH (sup:Supporter)-[:LOGGED]->(s)
        RETURN s.date AS date, s.situation AS situation, s.action AS action,
               s.effectiveness AS effectiveness, s.note AS note,
               sup.name AS supporter_name
        ORDER BY s.date DESC LIMIT $limit
        """,
        {"name": name, "limit": limit},
    )
    return [SupportLogEntry(**r) for r in records]
```

- [ ] **Step 3: Implement system.py**

```python
# backend/app/routers/system.py
from fastapi import APIRouter

from app.lib.db_operations import is_db_available
from app.lib.model_manager import model_manager
from app.schemas.agent import ModelStatusResponse

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status", response_model=ModelStatusResponse)
async def get_system_status():
    ollama_status = await model_manager.get_status()
    return ModelStatusResponse(
        ollama_available=ollama_status["ollama_available"],
        neo4j_available=is_db_available(),
        loaded_models=ollama_status["loaded_models"],
        current_exclusive=ollama_status["current_exclusive"],
    )


@router.post("/models/{model_name}/load")
async def load_model(model_name: str):
    await model_manager.ensure_model(model_name)
    return {"status": "loaded", "model": model_name}


@router.post("/models/{model_name}/unload")
async def unload_model(model_name: str):
    await model_manager.unload_model(model_name)
    return {"status": "unloaded", "model": model_name}
```

- [ ] **Step 4: Register routers in main.py**

Add to `backend/app/main.py` after the `app` definition:

```python
from app.routers import dashboard, clients, system

app.include_router(dashboard.router)
app.include_router(clients.router)
app.include_router(system.router)
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/ backend/app/main.py
git commit -m "feat: add Dashboard, Clients, and System API routers"
```

---

## Task 14: API Routers (Narratives, QuickLog, Chat)

**Files:**
- Create: `backend/app/routers/narratives.py`
- Create: `backend/app/routers/quicklog.py`
- Create: `backend/app/routers/chat.py`
- Create: `backend/app/routers/search.py`

- [ ] **Step 1: Implement narratives.py**

```python
# backend/app/routers/narratives.py
import json
from io import BytesIO

from fastapi import APIRouter, File, UploadFile

from app.agents.intake import extract_from_text
from app.agents.validator import check_safety_compliance, validate_schema
from app.lib.db_operations import register_to_database
from app.lib.file_readers import read_file
from app.schemas.narrative import (
    ExtractionRequest,
    ExtractedGraph,
    RegistrationResult,
    SafetyCheckResult,
    ValidationResult,
)

router = APIRouter(prefix="/api/narratives", tags=["narratives"])


@router.post("/extract", response_model=ExtractedGraph | None)
async def extract(request: ExtractionRequest):
    result = await extract_from_text(request.text, request.client_name)
    if result:
        return ExtractedGraph(**result)
    return None


@router.post("/validate", response_model=ValidationResult)
async def validate(graph: ExtractedGraph):
    return validate_schema(graph.model_dump())


@router.post("/register", response_model=RegistrationResult)
async def register(graph: ExtractedGraph):
    result = register_to_database(graph.model_dump())
    return RegistrationResult(**result)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    text = read_file(BytesIO(content), file.filename)
    return {"filename": file.filename, "text": text}


@router.post("/safety-check", response_model=SafetyCheckResult)
async def safety_check(request: ExtractionRequest):
    return await check_safety_compliance(request.text, request.client_name)
```

- [ ] **Step 2: Implement quicklog.py**

```python
# backend/app/routers/quicklog.py
from datetime import datetime

from fastapi import APIRouter

from app.lib.db_operations import register_to_database
from app.schemas.narrative import QuickLogRequest, RegistrationResult

router = APIRouter(prefix="/api/quicklog", tags=["quicklog"])


@router.post("", response_model=RegistrationResult)
async def create_quicklog(request: QuickLogRequest):
    graph = {
        "nodes": [
            {"temp_id": "c1", "label": "Client", "properties": {"name": request.client_name}},
            {"temp_id": "s1", "label": "Supporter", "properties": {"name": request.supporter_name}},
            {
                "temp_id": "log1",
                "label": "SupportLog",
                "properties": {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "note": request.note,
                    "situation": request.situation or "日常記録",
                },
            },
        ],
        "relationships": [
            {"source_temp_id": "s1", "target_temp_id": "log1", "type": "LOGGED", "properties": {}},
            {"source_temp_id": "log1", "target_temp_id": "c1", "type": "ABOUT", "properties": {}},
        ],
    }
    result = register_to_database(graph, user_name=request.supporter_name)
    return RegistrationResult(**result)
```

- [ ] **Step 3: Implement chat.py (WebSocket)**

```python
# backend/app/routers/chat.py
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.team import process_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_text = msg.get("content", "")
            session_id = msg.get("session_id", session_id)

            # Process through agent team
            result = await process_message(user_text, session_id)

            # Send routing info
            await websocket.send_json({
                "type": "routing",
                "agent": result["routing"].target_agent,
                "decision": result["routing"].intent.value,
                "reason": result["routing"].reason,
            })

            # Send response as stream (simulated for non-streaming models)
            response_text = result["response"]
            for i in range(0, len(response_text), 20):
                chunk = response_text[i : i + 20]
                await websocket.send_json({
                    "type": "stream",
                    "content": chunk,
                    "agent": result["routing"].target_agent,
                })

            # Send metadata
            await websocket.send_json({
                "type": "metadata",
                "agents_used": result["metadata"]["agents_used"],
                "model_switches": result["metadata"]["model_switches"],
            })

            # Send done
            await websocket.send_json({
                "type": "done",
                "session_id": session_id,
            })

    except WebSocketDisconnect:
        logger.info(f"Chat session {session_id} disconnected")
```

- [ ] **Step 4: Implement search.py**

```python
# backend/app/routers/search.py
from fastapi import APIRouter, Query

from app.lib.db_operations import run_query

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/fulltext")
async def fulltext_search(q: str = Query(...), limit: int = Query(20)):
    records = run_query(
        """
        CALL db.index.fulltext.queryNodes('idx_supportlog_fulltext', $query)
        YIELD node, score
        OPTIONAL MATCH (node)-[:ABOUT]->(c:Client)
        RETURN node.date AS date, node.note AS note, node.situation AS situation,
               c.name AS client_name, score
        ORDER BY score DESC LIMIT $limit
        """,
        {"query": q, "limit": limit},
    )
    return records
```

- [ ] **Step 5: Register remaining routers in main.py**

Add to `backend/app/main.py`:

```python
from app.routers import narratives, quicklog, chat, search

app.include_router(narratives.router)
app.include_router(quicklog.router)
app.include_router(chat.router)
app.include_router(search.router)
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/ backend/app/main.py
git commit -m "feat: add Narratives, QuickLog, Chat (WebSocket), and Search routers"
```

---

## Task 15: Frontend Skeleton + Layout

**Files:**
- Create: `frontend/` via create-next-app
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/components/domain/Sidebar.tsx`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/types.ts`

- [ ] **Step 1: Create Next.js project**

```bash
cd ~/Dev-Work/oyagami-local
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint \
  --app --src-dir --use-pnpm
```

- [ ] **Step 2: Install dependencies**

```bash
cd ~/Dev-Work/oyagami-local/frontend
pnpm add @tanstack/react-query ai zod react-hook-form @hookform/resolvers
pnpm dlx shadcn@latest init
# Select: default style, zinc base color, CSS variables
pnpm dlx shadcn@latest add button card input textarea table badge alert tabs dialog select separator scroll-area
```

- [ ] **Step 3: Create types.ts**

```typescript
// frontend/src/lib/types.ts
export interface ClientSummary {
  name: string;
  dob: string | null;
  age: number | null;
  blood_type: string | null;
  conditions: string[];
}

export interface NgAction {
  action: string;
  reason: string | null;
  risk_level: string;
}

export interface DashboardStats {
  client_count: number;
  log_count_this_month: number;
  renewal_alerts: number;
}

export interface RenewalAlert {
  client_name: string;
  certificate_type: string;
  next_renewal_date: string;
  days_remaining: number;
}

export interface ActivityEntry {
  date: string;
  client_name: string;
  action: string;
  summary: string;
}

export interface ModelStatus {
  ollama_available: boolean;
  neo4j_available: boolean;
  loaded_models: string[];
  current_exclusive: string | null;
  memory_usage_gb: number | null;
}

export interface ChatMessage {
  type: "routing" | "stream" | "model_status" | "metadata" | "done";
  content?: string;
  agent?: string;
  decision?: string;
  reason?: string;
  session_id?: string;
}

export interface ExtractedGraph {
  nodes: { temp_id: string; label: string; properties: Record<string, unknown> }[];
  relationships: { source_temp_id: string; target_temp_id: string; type: string; properties: Record<string, unknown> }[];
}
```

- [ ] **Step 4: Create api.ts**

```typescript
// frontend/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  dashboard: {
    stats: () => fetchApi<import("./types").DashboardStats>("/api/dashboard/stats"),
    alerts: () => fetchApi<import("./types").RenewalAlert[]>("/api/dashboard/alerts"),
    activity: () => fetchApi<import("./types").ActivityEntry[]>("/api/dashboard/activity"),
  },
  clients: {
    list: (kanaPrefix?: string) =>
      fetchApi<import("./types").ClientSummary[]>(
        `/api/clients${kanaPrefix ? `?kana_prefix=${kanaPrefix}` : ""}`
      ),
    get: (name: string) => fetchApi(`/api/clients/${encodeURIComponent(name)}`),
    emergency: (name: string) => fetchApi(`/api/clients/${encodeURIComponent(name)}/emergency`),
    logs: (name: string) => fetchApi(`/api/clients/${encodeURIComponent(name)}/logs`),
  },
  system: {
    status: () => fetchApi<import("./types").ModelStatus>("/api/system/status"),
    loadModel: (name: string) => fetchApi(`/api/system/models/${name}/load`, { method: "POST" }),
    unloadModel: (name: string) => fetchApi(`/api/system/models/${name}/unload`, { method: "POST" }),
  },
  narratives: {
    extract: (text: string, clientName?: string) =>
      fetchApi("/api/narratives/extract", {
        method: "POST",
        body: JSON.stringify({ text, client_name: clientName }),
      }),
    register: (graph: import("./types").ExtractedGraph) =>
      fetchApi("/api/narratives/register", {
        method: "POST",
        body: JSON.stringify(graph),
      }),
  },
  quicklog: {
    create: (data: { client_name: string; note: string; situation?: string }) =>
      fetchApi("/api/quicklog", { method: "POST", body: JSON.stringify(data) }),
  },
};
```

- [ ] **Step 5: Create Sidebar.tsx**

```tsx
// frontend/src/components/domain/Sidebar.tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "ホーム", section: "ホーム" },
  { href: "/narrative", label: "ナラティブ入力", section: "記録" },
  { href: "/quicklog", label: "クイックログ", section: "記録" },
  { href: "/clients", label: "クライアント一覧", section: "管理" },
  { href: "/chat", label: "AIチャット", section: "活用" },
  { href: "/settings", label: "LLM設定", section: "設定" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: status } = useQuery({
    queryKey: ["system-status"],
    queryFn: api.system.status,
    refetchInterval: 10000,
  });

  let currentSection = "";

  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-card">
      <div className="border-b p-4">
        <h1 className="text-lg font-bold">OYAGAMI LOCAL</h1>
      </div>
      <nav className="flex-1 overflow-y-auto p-2">
        {NAV_ITEMS.map((item) => {
          const showSection = item.section !== currentSection;
          if (showSection) currentSection = item.section;
          return (
            <div key={item.href}>
              {showSection && (
                <p className="mt-4 mb-1 px-3 text-xs font-medium text-muted-foreground uppercase">
                  {item.section}
                </p>
              )}
              <Link
                href={item.href}
                className={`block rounded-md px-3 py-2 text-sm ${
                  pathname === item.href
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                }`}
              >
                {item.label}
              </Link>
            </div>
          );
        })}
      </nav>
      <div className="border-t p-3 text-xs text-muted-foreground space-y-1">
        <div>
          Ollama: {status?.ollama_available ? "●" : "○"}{" "}
          {status?.current_exclusive || "待機中"}
        </div>
        <div>Neo4j: {status?.neo4j_available ? "●" : "○"}</div>
      </div>
    </aside>
  );
}
```

- [ ] **Step 6: Update layout.tsx**

```tsx
// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/domain/Sidebar";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "oyagami-local",
  description: "親亡き後支援データベース（ローカルLLM版）",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className={inter.className}>
        <Providers>
          <div className="flex h-screen">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-6">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
```

- [ ] **Step 7: Create providers.tsx**

```tsx
// frontend/src/app/providers.tsx
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

- [ ] **Step 8: Verify frontend starts**

```bash
cd ~/Dev-Work/oyagami-local/frontend
pnpm dev
# Expected: Next.js running on http://localhost:3000
```

- [ ] **Step 9: Commit**

```bash
cd ~/Dev-Work/oyagami-local
git add frontend/
git commit -m "feat: add Next.js frontend skeleton with sidebar, layout, and API client"
```

---

## Task 16: Dashboard Page

**Files:**
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/domain/StatsCards.tsx`
- Create: `frontend/src/components/domain/RenewalAlerts.tsx`
- Create: `frontend/src/components/domain/RecentActivity.tsx`

- [ ] **Step 1: Create StatsCards, RenewalAlerts, RecentActivity components**

Each component uses `useQuery` from TanStack Query to fetch data from the backend API. StatsCards displays 3 stat cards (client count, monthly logs, renewal alerts). RenewalAlerts shows a table of upcoming certificate renewals. RecentActivity shows a feed of recent audit log entries.

Use shadcn/ui `Card`, `Table`, and `Badge` components. See `frontend/src/lib/api.ts` for the API calls and `frontend/src/lib/types.ts` for the response types.

- [ ] **Step 2: Create dashboard page.tsx**

```tsx
// frontend/src/app/page.tsx
import { StatsCards } from "@/components/domain/StatsCards";
import { RenewalAlerts } from "@/components/domain/RenewalAlerts";
import { RecentActivity } from "@/components/domain/RecentActivity";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">ダッシュボード</h2>
      <StatsCards />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RenewalAlerts />
        <RecentActivity />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add Dashboard page with stats, alerts, and activity feed"
```

---

## Task 17: Client Pages

**Files:**
- Create: `frontend/src/app/clients/page.tsx`
- Create: `frontend/src/app/clients/[name]/page.tsx`
- Create: `frontend/src/components/domain/ClientTable.tsx`
- Create: `frontend/src/components/domain/ClientDetail.tsx`
- Create: `frontend/src/components/domain/KanaFilter.tsx`

- [ ] **Step 1: Implement KanaFilter, ClientTable, and client list page**

KanaFilter renders あ〜わ buttons. ClientTable shows name, age, conditions. Client list page combines them. Use `useQuery` with `kana_prefix` parameter for filtering.

- [ ] **Step 2: Implement client detail page**

Client detail page at `/clients/[name]` fetches full client data including NgActions, CarePreferences, KeyPersons. Display in tabs (基本情報 / 禁忌事項 / ケア指示 / 連絡先 / 更新期限). Use shadcn/ui `Tabs`, `Badge` (red for LifeThreatening, yellow for Panic).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add Client list and detail pages with kana filter"
```

---

## Task 18: Narrative Input Page

**Files:**
- Create: `frontend/src/app/narrative/page.tsx`
- Create: `frontend/src/components/domain/NarrativeWizard.tsx`
- Create: `frontend/src/components/domain/ExtractionPreview.tsx`

- [ ] **Step 1: Implement NarrativeWizard (3-step controller)**

State machine with 3 steps: input → preview → confirm. Step 1: textarea + file upload. Step 2: show extracted JSON as collapsible tree. Step 3: confirmation dialog + register button. Use React Hook Form for the text input. Call `api.narratives.extract()` on step transition 1→2, then `api.narratives.register()` on step 3 confirmation.

- [ ] **Step 2: Implement ExtractionPreview**

Renders extracted graph nodes as expandable cards grouped by label (Client, NgAction, SupportLog, etc.). Each node shows its properties in a key-value list. Highlight NgAction nodes with red border.

- [ ] **Step 3: Create narrative page.tsx**

```tsx
// frontend/src/app/narrative/page.tsx
import { NarrativeWizard } from "@/components/domain/NarrativeWizard";

export default function NarrativePage() {
  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">ナラティブ入力</h2>
      <NarrativeWizard />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: add Narrative input page with 3-step wizard and extraction preview"
```

---

## Task 19: AI Chat Page

**Files:**
- Create: `frontend/src/app/chat/page.tsx`
- Create: `frontend/src/components/domain/ChatPanel.tsx`
- Create: `frontend/src/components/domain/AgentStatus.tsx`
- Create: `frontend/src/hooks/useChat.ts`

- [ ] **Step 1: Implement useChat hook (WebSocket)**

```typescript
// frontend/src/hooks/useChat.ts
"use client";
import { useCallback, useRef, useState } from "react";
import type { ChatMessage } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  metadata?: Record<string, unknown>;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [agentInfo, setAgentInfo] = useState<{ agent: string; decision: string } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    const ws = new WebSocket("ws://localhost:8000/api/chat/ws");
    wsRef.current = ws;

    let currentResponse = "";

    ws.onmessage = (event) => {
      const msg: ChatMessage = JSON.parse(event.data);

      if (msg.type === "routing") {
        setAgentInfo({ agent: msg.agent!, decision: msg.decision! });
      } else if (msg.type === "stream") {
        currentResponse += msg.content || "";
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant") {
            last.content = currentResponse;
          } else {
            updated.push({ role: "assistant", content: currentResponse });
          }
          return updated;
        });
      } else if (msg.type === "done") {
        currentResponse = "";
        setIsLoading(false);
        setAgentInfo(null);
      }
    };
  }, []);

  const sendMessage = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connect();
      }
      setMessages((prev) => [...prev, { role: "user", content }]);
      setIsLoading(true);
      wsRef.current?.send(JSON.stringify({ type: "message", content }));
    },
    [connect]
  );

  return { messages, isLoading, agentInfo, sendMessage, connect };
}
```

- [ ] **Step 2: Implement ChatPanel and AgentStatus**

ChatPanel displays message bubbles (user on right, assistant on left). AgentStatus shows the current routing decision and model loading state. Input bar at bottom with send button.

- [ ] **Step 3: Create chat page.tsx**

```tsx
// frontend/src/app/chat/page.tsx
"use client";
import { ChatPanel } from "@/components/domain/ChatPanel";
import { AgentStatus } from "@/components/domain/AgentStatus";
import { useChat } from "@/hooks/useChat";

export default function ChatPage() {
  const { messages, isLoading, agentInfo, sendMessage, connect } = useChat();

  return (
    <div className="flex h-full flex-col">
      <h2 className="text-2xl font-bold mb-4">AIチャット</h2>
      <AgentStatus agentInfo={agentInfo} isLoading={isLoading} />
      <ChatPanel
        messages={messages}
        isLoading={isLoading}
        onSend={(text) => {
          connect();
          sendMessage(text);
        }}
      />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: add AI Chat page with WebSocket streaming and agent status display"
```

---

## Task 20: QuickLog + Settings Pages

**Files:**
- Create: `frontend/src/app/quicklog/page.tsx`
- Create: `frontend/src/app/settings/page.tsx`

- [ ] **Step 1: Implement QuickLog page**

Simple form with client selector (dropdown from `api.clients.list()`), note textarea, optional situation field. Submit calls `api.quicklog.create()`. Use React Hook Form + Zod validation. Show success toast on registration.

- [ ] **Step 2: Implement Settings page**

Display model status from `api.system.status()` with `useQuery` (10s refetch). Show resident models (always green), exclusive models with load/unload buttons. Memory usage progress bar. Neo4j/Ollama connection status badges.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add QuickLog and LLM Settings pages"
```

---

## Task 21: Backend Integration Tests

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/routers/test_dashboard.py`
- Create: `backend/tests/routers/test_system.py`

- [ ] **Step 1: Create conftest.py with FastAPI test client**

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

- [ ] **Step 2: Write dashboard API tests**

```python
# backend/tests/routers/test_dashboard.py
def test_stats_endpoint(client):
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "client_count" in data
    assert "log_count_this_month" in data


def test_alerts_endpoint(client):
    resp = client.get("/api/dashboard/alerts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

- [ ] **Step 3: Write system API tests**

```python
# backend/tests/routers/test_system.py
def test_system_status(client):
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "ollama_available" in data
    assert "neo4j_available" in data
```

- [ ] **Step 4: Run all tests**

```bash
cd ~/Dev-Work/oyagami-local/backend
uv run pytest tests/ -v
# Expected: all tests pass
```

- [ ] **Step 5: Commit**

```bash
git add backend/tests/
git commit -m "test: add integration tests for Dashboard and System API endpoints"
```

---

## Task 22: Final Wiring + Smoke Test

- [ ] **Step 1: Ensure Neo4j is running**

```bash
cd ~/Dev-Work/neo4j-agno-agent && docker-compose up -d
```

- [ ] **Step 2: Start backend**

```bash
cd ~/Dev-Work/oyagami-local/backend
uv run uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 3: Start frontend**

```bash
cd ~/Dev-Work/oyagami-local/frontend
pnpm dev
```

- [ ] **Step 4: Verify end-to-end**

1. Open http://localhost:3000 — Dashboard should show stats from Neo4j
2. Navigate to /clients — Client list should display
3. Navigate to /chat — WebSocket should connect, test "こんにちは"
4. Navigate to /settings — Model status should show Ollama state
5. Check http://localhost:8000/api/health — Should return `{"status": "ok"}`
6. Check http://localhost:8000/api/system/status — Should show Neo4j/Ollama status

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete Phase 1 - oyagami-local with multi-agent architecture"
```
