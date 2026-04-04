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
