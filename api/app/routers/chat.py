"""Chat router — Gemini-based WebSocket chat with emergency routing."""
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

            for i in range(0, len(response), 20):
                await websocket.send_json({
                    "type": "stream",
                    "content": response[i:i + 20],
                    "agent": "gemini",
                })

            await websocket.send_json({"type": "done", "session_id": session_id})

    except WebSocketDisconnect:
        logger.info(f"Chat session {session_id} disconnected")
