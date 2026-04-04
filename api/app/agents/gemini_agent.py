"""Gemini 2.0 Flash agent for text extraction, chat, and safety checks.

Chat mode uses function calling to access Neo4j client data contextually.
"""
import json
import logging
import re
from pathlib import Path

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)
PROMPT_DIR = Path(__file__).parent / "prompts"
_model = None
_chat_model = None


def _get_model():
    global _model
    if _model is None:
        genai.configure(api_key=settings.gemini_api_key or settings.google_api_key)
        _model = genai.GenerativeModel(settings.gemini_model)
    return _model


# ---------------------------------------------------------------------------
# DB 検索ツール（Gemini Function Calling 用）
# ---------------------------------------------------------------------------

def _search_client_info(client_name: str) -> dict:
    """クライアントの基本情報を取得"""
    from app.lib.db_operations import run_query
    records = run_query("""
        MATCH (c:Client {name: $name})
        OPTIONAL MATCH (c)-[:HAS_CONDITION]->(cond:Condition)
        RETURN c.name AS name, c.dob AS dob, c.bloodType AS bloodType,
               collect(DISTINCT cond.name) AS conditions
    """, {"name": client_name})
    if not records:
        return {"error": f"「{client_name}」さんの情報が見つかりません。"}
    r = records[0]
    return {k: str(v) if v is not None else None for k, v in r.items()}


def _search_emergency_contacts(client_name: str) -> dict:
    """緊急連絡先（キーパーソン）を取得"""
    from app.lib.db_operations import run_query
    records = run_query("""
        MATCH (c:Client {name: $name})-[rel:HAS_KEY_PERSON]->(kp:KeyPerson)
        RETURN kp.name AS name, kp.relationship AS relationship,
               kp.phone AS phone, rel.rank AS rank
        ORDER BY rel.rank ASC
    """, {"name": client_name})
    return {"client_name": client_name, "contacts": [dict(r) for r in records]}


def _search_ng_actions(client_name: str) -> dict:
    """禁忌事項（してはいけないこと）を取得"""
    from app.lib.db_operations import run_query
    records = run_query("""
        MATCH (c:Client {name: $name})-[:MUST_AVOID]->(ng:NgAction)
        RETURN ng.action AS action, ng.reason AS reason, ng.riskLevel AS riskLevel
        ORDER BY CASE ng.riskLevel
            WHEN 'LifeThreatening' THEN 1
            WHEN 'Panic' THEN 2
            ELSE 3 END
    """, {"name": client_name})
    return {"client_name": client_name, "ng_actions": [dict(r) for r in records]}


def _search_care_preferences(client_name: str) -> dict:
    """推奨ケア（こうするとよい）を取得"""
    from app.lib.db_operations import run_query
    records = run_query("""
        MATCH (c:Client {name: $name})-[:REQUIRES]->(cp:CarePreference)
        RETURN cp.category AS category, cp.instruction AS instruction, cp.priority AS priority
    """, {"name": client_name})
    return {"client_name": client_name, "care_preferences": [dict(r) for r in records]}


def _search_hospital(client_name: str) -> dict:
    """かかりつけ病院を取得"""
    from app.lib.db_operations import run_query
    records = run_query("""
        MATCH (c:Client {name: $name})-[:TREATED_AT]->(h:Hospital)
        RETURN h.name AS name, h.phone AS phone, h.address AS address, h.department AS department
    """, {"name": client_name})
    return {"client_name": client_name, "hospitals": [dict(r) for r in records]}


def _search_guardian(client_name: str) -> dict:
    """後見人・法的代理人を取得"""
    from app.lib.db_operations import run_query
    records = run_query("""
        MATCH (c:Client {name: $name})-[:HAS_LEGAL_REP]->(g:Guardian)
        RETURN g.name AS name, g.type AS type, g.phone AS phone, g.organization AS organization
    """, {"name": client_name})
    return {"client_name": client_name, "guardians": [dict(r) for r in records]}


def _search_support_logs(client_name: str, limit: int = 5) -> dict:
    """最近の支援記録を取得"""
    from app.lib.db_operations import run_query
    records = run_query("""
        MATCH (s:Supporter)-[:LOGGED]->(sl:SupportLog)-[:ABOUT]->(c:Client {name: $name})
        RETURN sl.date AS date, sl.situation AS situation, sl.action AS action,
               sl.effectiveness AS effectiveness, sl.note AS note, s.name AS supporter
        ORDER BY sl.date DESC LIMIT $limit
    """, {"name": client_name, "limit": limit})
    return {"client_name": client_name, "logs": [{k: str(v) if v else None for k, v in r.items()} for r in records]}


# Gemini Function Calling 用のツール定義
TOOLS = [
    genai.protos.Tool(function_declarations=[
        genai.protos.FunctionDeclaration(
            name="search_client_info",
            description="クライアントの基本情報（名前、生年月日、血液型、障害・状態）を検索します。",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={"client_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="クライアント名")},
                required=["client_name"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="search_emergency_contacts",
            description="クライアントの緊急連絡先（キーパーソン：家族・親族等）を検索します。",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={"client_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="クライアント名")},
                required=["client_name"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="search_ng_actions",
            description="クライアントの禁忌事項（絶対にしてはいけないこと）を検索します。パニック時・危険時に重要。",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={"client_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="クライアント名")},
                required=["client_name"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="search_care_preferences",
            description="クライアントの推奨ケア（こうすると落ち着く、こうするとよい）を検索します。",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={"client_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="クライアント名")},
                required=["client_name"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="search_hospital",
            description="クライアントのかかりつけ病院・医療機関を検索します。体調不良時に必要。",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={"client_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="クライアント名")},
                required=["client_name"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="search_guardian",
            description="クライアントの後見人・法的代理人を検索します。金銭トラブルや法的問題時に必要。",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={"client_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="クライアント名")},
                required=["client_name"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="search_support_logs",
            description="クライアントの最近の支援記録を検索します。最近の様子や支援傾向の確認に使用。",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "client_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="クライアント名"),
                    "limit": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="取得件数（デフォルト5）"),
                },
                required=["client_name"],
            ),
        ),
    ])
]

TOOL_DISPATCH = {
    "search_client_info": _search_client_info,
    "search_emergency_contacts": _search_emergency_contacts,
    "search_ng_actions": _search_ng_actions,
    "search_care_preferences": _search_care_preferences,
    "search_hospital": _search_hospital,
    "search_guardian": _search_guardian,
    "search_support_logs": _search_support_logs,
}

CHAT_SYSTEM_PROMPT = """あなたは障害福祉支援の専門アシスタントです。
利用者（クライアント）の支援情報がNeo4jグラフデータベースに格納されており、
ツール（関数）を使ってデータベースから情報を取得できます。

## 行動指針

1. **まず状況を確認する**: 「緊急連絡先を教えて」と言われたら、すぐに情報を出すのではなく
   「何かありましたか？状況を教えていただけますか？」とまず確認してください。
   状況に応じて最適な情報を提供するためです。

2. **状況に応じた情報提供**:
   - パニック・行動障害 → 禁忌事項(search_ng_actions) + 推奨ケア(search_care_preferences) + 家族連絡先(search_emergency_contacts)
   - 体調不良・怪我 → かかりつけ病院(search_hospital) + 家族連絡先(search_emergency_contacts)
   - 金銭トラブル・法的問題 → 後見人(search_guardian) + 家族連絡先(search_emergency_contacts)
   - 一般的な質問 → 基本情報(search_client_info) + 支援記録(search_support_logs)

3. **Safety First**: ただし「今パニック中」「倒れた」など切迫した状況では、
   質問せずに直ちに必要な情報を全て提供してください。

4. **日本語で回答**: 常に日本語で、わかりやすく回答してください。

5. **データにない情報は推測しない**: データベースに存在しない情報は「登録されていません」と回答してください。
"""


def _get_chat_model():
    global _chat_model
    if _chat_model is None:
        genai.configure(api_key=settings.gemini_api_key or settings.google_api_key)
        _chat_model = genai.GenerativeModel(
            settings.gemini_model,
            tools=TOOLS,
            system_instruction=CHAT_SYSTEM_PROMPT,
        )
    return _chat_model


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
    """Chat with Gemini using function calling for DB access.

    Gemini can call tools to search the Neo4j database for client information,
    then synthesize a contextual response.
    """
    try:
        model = _get_chat_model()
        chat_session = model.start_chat(history=history or [])

        response = chat_session.send_message(message)

        # Function calling loop: Gemini may call tools, we execute and return results
        max_rounds = 5
        for _ in range(max_rounds):
            # Check if Gemini wants to call a function
            func_calls = [
                part.function_call
                for part in response.candidates[0].content.parts
                if part.function_call.name
            ]

            if not func_calls:
                # No function calls — return the text response
                break

            # Execute each function call
            func_responses = []
            for fc in func_calls:
                fn_name = fc.name
                fn_args = dict(fc.args) if fc.args else {}
                logger.info(f"Tool call: {fn_name}({fn_args})")

                fn = TOOL_DISPATCH.get(fn_name)
                if fn:
                    result = fn(**fn_args)
                else:
                    result = {"error": f"Unknown function: {fn_name}"}

                func_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fn_name,
                            response={"result": json.dumps(result, ensure_ascii=False, default=str)},
                        )
                    )
                )

            # Send function results back to Gemini
            response = chat_session.send_message(func_responses)

        # Extract text from final response
        text_parts = [
            part.text
            for part in response.candidates[0].content.parts
            if part.text
        ]
        return "\n".join(text_parts) if text_parts else "回答を生成できませんでした。"

    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        return f"エラーが発生しました: {e}"


async def check_safety_compliance(narrative: str, ng_actions: list) -> dict:
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
