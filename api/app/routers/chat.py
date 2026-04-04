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
    # Gemini の会話履歴（function calling 対応のため chat() 内で管理）
    history: list[dict] = []

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                user_text = msg.get("content", "")
                session_id = msg.get("session_id", session_id)

                if not user_text:
                    await websocket.send_json({"type": "done", "session_id": session_id})
                    continue

                # Safety First: 現在進行中の危機のみ（情報照会は Gemini に回す）
                if is_emergency(user_text):
                    await websocket.send_json({
                        "type": "routing",
                        "agent": "safety_first",
                        "decision": "emergency_search",
                        "reason": "現在進行中の危機を検知",
                    })
                    response = handle_emergency(user_text)
                else:
                    await websocket.send_json({
                        "type": "routing",
                        "agent": "gemini",
                        "decision": "chat",
                        "reason": "Gemini 2.0 Flash（DB検索ツール付き）",
                    })
                    response = await chat(user_text, history)
                    # 会話履歴に追加（次のターンでコンテキストとして使用）
                    history.append({"role": "user", "parts": [user_text]})
                    history.append({"role": "model", "parts": [response]})

                # ストリーミング送信
                for i in range(0, len(response), 30):
                    await websocket.send_json({
                        "type": "stream",
                        "content": response[i:i + 30],
                        "agent": "gemini",
                    })

                await websocket.send_json({"type": "done", "session_id": session_id})
            except json.JSONDecodeError:
                await websocket.send_json({"type": "stream", "content": "無効なメッセージ形式です。", "agent": "system"})
                await websocket.send_json({"type": "done", "session_id": session_id})
            except Exception as e:
                logger.error(f"Chat processing error: {e}", exc_info=True)
                await websocket.send_json({"type": "stream", "content": "エラーが発生しました。もう一度お試しください。", "agent": "system"})
                await websocket.send_json({"type": "done", "session_id": session_id})

    except WebSocketDisconnect:
        logger.info(f"Chat session {session_id} disconnected")
