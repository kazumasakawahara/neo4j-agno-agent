"""Safety First: emergency keyword detection + direct DB search (no LLM)."""
import re
from app.lib.db_operations import run_query

# 現在進行中の危機を示すキーワードのみ（情報照会は Gemini に任せる）
CRISIS_KEYWORDS = {"パニック中", "倒れた", "倒れている", "SOS", "発作が", "救急車", "助けて", "意識がない"}

# 情報照会として Gemini に回すべきキーワード（Safety First を発動しない）
INQUIRY_INDICATORS = {"教えて", "調べて", "確認", "一覧", "リスト", "知りたい"}


def is_emergency(text: str) -> bool:
    """現在進行中の危機かどうかを判定。情報照会は除外。"""
    # まず情報照会かどうかを確認
    if any(kw in text for kw in INQUIRY_INDICATORS):
        return False
    return any(kw in text for kw in CRISIS_KEYWORDS)


def handle_emergency(text: str) -> str:
    name_match = re.search(r"([一-龯]{2,4})\s?さん", text)
    if not name_match:
        return "クライアント名を特定できません。「〇〇さんの緊急情報」のように指定してください。"
    client_name = name_match.group(1)
    records = run_query("""
        MATCH (c:Client {name: $name})
        OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
        OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
        OPTIONAL MATCH (c)-[:HAS_KEY_PERSON]->(kp:KeyPerson)
        OPTIONAL MATCH (c)-[:TREATED_AT]->(h:Hospital)
        OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)
        RETURN c, collect(DISTINCT ng) AS ng_actions,
               collect(DISTINCT cp) AS care_prefs,
               collect(DISTINCT kp) AS key_persons, h, g
    """, {"name": client_name})
    if not records:
        return f"「{client_name}」さんの情報が見つかりません。"
    r = records[0]
    parts = [f"## {client_name}さんの緊急情報\n"]
    for ng in r.get("ng_actions", []):
        ng = dict(ng)
        parts.append(f"- **{ng.get('action','')}** [{ng.get('riskLevel','')}]: {ng.get('reason','')}")
    if r.get("care_prefs"):
        parts.append("\n### 推奨ケア")
        for cp in r.get("care_prefs", []):
            cp = dict(cp)
            parts.append(f"- {cp.get('category','')}: {cp.get('instruction','')}")
    if r.get("key_persons"):
        parts.append("\n### 緊急連絡先")
        for kp in r.get("key_persons", []):
            kp = dict(kp)
            parts.append(f"- {kp.get('name','')} ({kp.get('relationship','')}): {kp.get('phone','N/A')}")
    return "\n".join(parts)
