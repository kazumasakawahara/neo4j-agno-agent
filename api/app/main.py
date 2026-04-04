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

    if settings.gemini_api_key or settings.google_api_key:
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
