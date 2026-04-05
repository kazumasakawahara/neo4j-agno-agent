"""Chat router — WebSocket chat with emergency routing.

プロバイダー非依存: Gemini / Claude / OpenAI を設定で切り替え可能。
セッション対応: Agno の InMemoryDb で会話履歴を自動管理し、
2ターン目以降も「山田健太さん」などのクライアント名を保持する。
"""
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.gemini_agent import chat, create_session_agent
from app.agents.safety_first import extract_client_name, handle_emergency, is_emergency
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def _provider_label() -> str:
    """現在のチャットプロバイダー名を返す（ルーティング表示用）。"""
    labels = {
        "gemini": "Gemini",
        "claude": "Claude",
        "openai": "OpenAI",
        "ollama": "Ollama (ローカル)",
    }
    return labels.get(settings.chat_provider, settings.chat_provider)


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())

    # セッション対応エージェントを作成（WebSocket接続中は同一インスタンスを再利用）
    agent = create_session_agent(session_id)

    # 会話履歴テキスト（Safety First でクライアント名を抽出するために保持）
    message_history: list[str] = []

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

                # Safety First: 一刻を争う危機のみ（それ以外はエージェントが判断）
                if is_emergency(user_text):
                    await websocket.send_json({
                        "type": "routing",
                        "agent": "safety_first",
                        "decision": "emergency_search",
                        "reason": "現在進行中の危機を検知",
                    })
                    # 現在のメッセージにクライアント名がなければ履歴から探す
                    response = handle_emergency(user_text, message_history)
                else:
                    await websocket.send_json({
                        "type": "routing",
                        "agent": settings.chat_provider,
                        "decision": "chat",
                        "reason": f"{_provider_label()}（DB検索ツール付き）",
                    })
                    # セッション対応エージェントを使用（履歴は Agno が自動管理）
                    response = await chat(user_text, agent=agent)

                # 履歴にユーザーメッセージを保存（Safety First 用）
                message_history.append(user_text)

                # ストリーミング送信
                for i in range(0, len(response), 30):
                    await websocket.send_json({
                        "type": "stream",
                        "content": response[i:i + 30],
                        "agent": settings.chat_provider,
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
