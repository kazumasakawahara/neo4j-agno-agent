"""Multi-provider chat agent using Agno framework.

Supports Gemini, Claude, OpenAI, and any future provider via Agno's
unified Agent interface. Tools (DB search functions) work identically
across all providers — Agno handles the protocol differences.

Provider is selected by CHAT_PROVIDER in .env.
"""
import json
import logging
import re
from pathlib import Path
from typing import Iterator

from agno.agent import Agent, RunEvent, RunOutputEvent

from app.config import settings

logger = logging.getLogger(__name__)
PROMPT_DIR = Path(__file__).parent / "prompts"

# ---------------------------------------------------------------------------
# DB Search Tools (provider-agnostic — Agno wraps them automatically)
# ---------------------------------------------------------------------------


def search_client_info(client_name: str) -> str:
    """クライアントの基本情報（名前、生年月日、血液型、障害・状態）を検索します。

    Args:
        client_name: クライアント名
    """
    from app.lib.db_operations import run_query

    records = run_query("""
        MATCH (c:Client {name: $name})
        OPTIONAL MATCH (c)-[:HAS_CONDITION]->(cond:Condition)
        RETURN c.name AS name, c.dob AS dob, c.bloodType AS bloodType,
               collect(DISTINCT cond.name) AS conditions
    """, {"name": client_name})
    if not records:
        return json.dumps({"error": f"「{client_name}」さんの情報が見つかりません。"}, ensure_ascii=False)
    r = records[0]
    return json.dumps({k: str(v) if v is not None else None for k, v in r.items()}, ensure_ascii=False)


def search_emergency_contacts(client_name: str) -> str:
    """クライアントの緊急連絡先（キーパーソン：家族・親族等）を検索します。

    Args:
        client_name: クライアント名
    """
    from app.lib.db_operations import run_query

    records = run_query("""
        MATCH (c:Client {name: $name})-[rel:HAS_KEY_PERSON]->(kp:KeyPerson)
        RETURN kp.name AS name, kp.relationship AS relationship,
               kp.phone AS phone, rel.rank AS rank
        ORDER BY rel.rank ASC
    """, {"name": client_name})
    return json.dumps({"client_name": client_name, "contacts": [dict(r) for r in records]}, ensure_ascii=False, default=str)


def search_ng_actions(client_name: str) -> str:
    """クライアントの禁忌事項（絶対にしてはいけないこと）を検索します。パニック時・危険時に重要。

    Args:
        client_name: クライアント名
    """
    from app.lib.db_operations import run_query

    records = run_query("""
        MATCH (c:Client {name: $name})-[:MUST_AVOID]->(ng:NgAction)
        RETURN ng.action AS action, ng.reason AS reason, ng.riskLevel AS riskLevel
        ORDER BY CASE ng.riskLevel
            WHEN 'LifeThreatening' THEN 1 WHEN 'Panic' THEN 2 ELSE 3 END
    """, {"name": client_name})
    return json.dumps({"client_name": client_name, "ng_actions": [dict(r) for r in records]}, ensure_ascii=False)


def search_care_preferences(client_name: str) -> str:
    """クライアントの推奨ケア（こうすると落ち着く、こうするとよい）を検索します。

    Args:
        client_name: クライアント名
    """
    from app.lib.db_operations import run_query

    records = run_query("""
        MATCH (c:Client {name: $name})-[:REQUIRES]->(cp:CarePreference)
        RETURN cp.category AS category, cp.instruction AS instruction, cp.priority AS priority
    """, {"name": client_name})
    return json.dumps({"client_name": client_name, "care_preferences": [dict(r) for r in records]}, ensure_ascii=False)


def search_hospital(client_name: str) -> str:
    """クライアントのかかりつけ病院・医療機関を検索します。体調不良時に必要。

    Args:
        client_name: クライアント名
    """
    from app.lib.db_operations import run_query

    records = run_query("""
        MATCH (c:Client {name: $name})-[:TREATED_AT]->(h:Hospital)
        RETURN h.name AS name, h.phone AS phone, h.address AS address
    """, {"name": client_name})
    return json.dumps({"client_name": client_name, "hospitals": [dict(r) for r in records]}, ensure_ascii=False, default=str)


def search_guardian(client_name: str) -> str:
    """クライアントの後見人・法的代理人を検索します。金銭トラブルや法的問題時に必要。

    Args:
        client_name: クライアント名
    """
    from app.lib.db_operations import run_query

    records = run_query("""
        MATCH (c:Client {name: $name})-[:HAS_LEGAL_REP]->(g:Guardian)
        RETURN g.name AS name, g.type AS type, g.phone AS phone, g.organization AS organization
    """, {"name": client_name})
    return json.dumps({"client_name": client_name, "guardians": [dict(r) for r in records]}, ensure_ascii=False, default=str)


def search_support_logs(client_name: str, limit: int = 5) -> str:
    """クライアントの最近の支援記録を検索します。最近の様子や支援傾向の確認に使用。

    Args:
        client_name: クライアント名
        limit: 取得件数（デフォルト5）
    """
    from app.lib.db_operations import run_query

    records = run_query("""
        MATCH (s:Supporter)-[:LOGGED]->(sl:SupportLog)-[:ABOUT]->(c:Client {name: $name})
        RETURN sl.date AS date, sl.situation AS situation, sl.action AS action,
               sl.effectiveness AS effectiveness, sl.note AS note, s.name AS supporter
        ORDER BY sl.date DESC LIMIT $limit
    """, {"name": client_name, "limit": limit})
    return json.dumps({"client_name": client_name, "logs": [{k: str(v) if v else None for k, v in r.items()} for r in records]}, ensure_ascii=False)


# All tools available to the agent
TOOLS = [
    search_client_info,
    search_emergency_contacts,
    search_ng_actions,
    search_care_preferences,
    search_hospital,
    search_guardian,
    search_support_logs,
]

CHAT_SYSTEM_PROMPT = """あなたは障害福祉支援の専門アシスタントです。
利用者（クライアント）の支援情報がNeo4jグラフデータベースに格納されており、
ツール（関数）を使ってデータベースから情報を取得できます。

## 行動指針

1. **まず状況を確認する**: 「緊急連絡先を教えて」と言われたら、すぐに情報を出すのではなく
   「何かありましたか？状況を教えていただけますか？」とまず確認してください。
   状況に応じて最適な情報を提供するためです。

2. **状況に応じた情報提供**:
   - パニック・行動障害 → search_ng_actions + search_care_preferences + search_emergency_contacts
   - 体調不良・怪我 → search_hospital + search_emergency_contacts
   - 金銭トラブル・法的問題 → search_guardian + search_emergency_contacts
   - 一般的な質問 → search_client_info + search_support_logs

3. **Safety First**: ただし「今パニック中」「倒れた」など切迫した状況では、
   質問せずに直ちに必要な情報を全て提供してください。

4. **日本語で回答**: 常に日本語で、わかりやすく回答してください。

5. **データにない情報は推測しない**: データベースに存在しない情報は「登録されていません」と回答してください。
"""


# ---------------------------------------------------------------------------
# Agent Factory — provider selection via config
# ---------------------------------------------------------------------------

def _create_model():
    """Create the appropriate model based on CHAT_PROVIDER config."""
    provider = settings.chat_provider

    if provider == "claude":
        from agno.models.anthropic import Claude
        return Claude(
            id=settings.claude_model,
            api_key=settings.anthropic_api_key,
        )
    elif provider == "openai":
        from agno.models.openai import OpenAIChat
        return OpenAIChat(
            id=settings.openai_model if hasattr(settings, "openai_model") else "gpt-4.1-mini",
            api_key=settings.openai_api_key if hasattr(settings, "openai_api_key") else "",
        )
    else:  # default: gemini
        from agno.models.google import Gemini
        return Gemini(
            id=settings.gemini_model,
            api_key=settings.gemini_api_key or settings.google_api_key,
        )


def _get_chat_agent() -> Agent:
    """Create a chat agent with the configured model and DB tools."""
    return Agent(
        model=_create_model(),
        tools=TOOLS,
        instructions=[CHAT_SYSTEM_PROMPT],
        markdown=True,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
    """Extract structured graph data from narrative text.

    Uses Gemini directly (not Agno) for extraction since this requires
    a specific JSON schema prompt, not conversational tools.
    """
    import google.generativeai as genai

    prompt = get_extraction_prompt()
    user_message = text
    if client_name:
        user_message = f"【対象クライアント: {client_name}】\n\n{text}"
    try:
        genai.configure(api_key=settings.gemini_api_key or settings.google_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(
            [{"role": "user", "parts": [prompt + "\n\n" + user_message]}],
            generation_config={"temperature": 0},
        )
        return parse_json_from_response(response.text)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None


async def chat(message: str, history: list[dict] | None = None) -> str:
    """Chat using Agno Agent with the configured provider.

    Agno handles function calling / tool_use protocol differences
    automatically — same tools work with Gemini, Claude, OpenAI, etc.
    """
    try:
        agent = _get_chat_agent()

        # Run agent (non-streaming for WebSocket chunking)
        response = agent.run(message)

        # Extract text content
        if response and response.content:
            return response.content
        return "回答を生成できませんでした。"

    except Exception as e:
        logger.error(f"Chat failed ({settings.chat_provider}): {e}", exc_info=True)
        return f"エラーが発生しました: {e}"


async def chat_stream(message: str) -> Iterator[str]:
    """Stream chat response using Agno Agent.

    Yields text chunks as they arrive from the model.
    """
    try:
        agent = _get_chat_agent()
        stream: Iterator[RunOutputEvent] = agent.run(message, stream=True)
        for chunk in stream:
            if chunk.event == RunEvent.run_content and chunk.content:
                yield chunk.content
    except Exception as e:
        logger.error(f"Stream chat failed: {e}", exc_info=True)
        yield f"エラーが発生しました: {e}"


async def check_safety_compliance(narrative: str, ng_actions: list) -> dict:
    """Check if narrative violates existing NgActions.

    Uses Gemini directly (simple prompt, no tools needed).
    """
    if not ng_actions:
        return {"is_violation": False, "warning": None, "risk_level": "None"}

    import google.generativeai as genai

    safety_prompt = (PROMPT_DIR / "safety.md").read_text(encoding="utf-8")
    safety_prompt = safety_prompt.replace("{ng_actions}", json.dumps(ng_actions, ensure_ascii=False))
    safety_prompt = safety_prompt.replace("{narrative}", narrative)
    try:
        genai.configure(api_key=settings.gemini_api_key or settings.google_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
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
