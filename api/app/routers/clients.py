"""Clients router — client list, detail, emergency info, and support logs."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from app.lib.db_operations import run_query
from app.lib.utils import calculate_age

_KANA_ROW_MAP = {
    "あ": "あいうえお",
    "か": "かきくけこがぎぐげご",
    "さ": "さしすせそざじずぜぞ",
    "た": "たちつてとだぢづでど",
    "な": "なにぬねの",
    "は": "はひふへほばびぶべぼぱぴぷぺぽ",
    "ま": "まみむめも",
    "や": "やゆよ",
    "ら": "らりるれろ",
    "わ": "わをん",
}

# ---------------------------------------------------------------------------
# アルファベット → 日本語読み（ひらがな）マッピング
# 例: M → えむ（あ行）、K → けー（か行）
# ---------------------------------------------------------------------------
_ALPHA_TO_KANA: dict[str, str] = {
    "A": "えー",    "B": "びー",    "C": "しー",    "D": "でぃー",
    "E": "いー",    "F": "えふ",    "G": "じー",    "H": "えいち",
    "I": "あい",    "J": "じぇー",  "K": "けー",    "L": "える",
    "M": "えむ",    "N": "えぬ",    "O": "おー",    "P": "ぴー",
    "Q": "きゅー",  "R": "あーる",  "S": "えす",    "T": "てぃー",
    "U": "ゆー",    "V": "ぶい",    "W": "だぶりゅー",
    "X": "えっくす", "Y": "わい",   "Z": "ぜっと",
}


def _name_to_kana(name: str) -> str:
    """漢字名・アルファベット名をひらがなに変換。

    - イニシャル表記（例: "M・K"）→ 各文字の日本語読みに変換（"えむ・けー"）
    - 漢字名 → pykakasi で変換
    """
    import re

    # 名前の先頭文字がアルファベットならイニシャル表記として処理
    if name and name[0].isascii() and name[0].isalpha():
        parts: list[str] = []
        for ch in name:
            upper = ch.upper()
            if upper in _ALPHA_TO_KANA:
                parts.append(_ALPHA_TO_KANA[upper])
            else:
                # 区切り文字（・、-、スペース等）はそのまま
                parts.append(ch)
        return "".join(parts)

    # 漢字名は pykakasi で変換
    from pykakasi import kakasi as Kakasi

    kks = Kakasi()
    result = kks.convert(name)
    return "".join(item["hira"] for item in result)


def _is_alpha_name(name: str) -> bool:
    """名前がアルファベット（イニシャル等）で始まるかを判定。"""
    return bool(name) and name[0].isascii() and name[0].isalpha()


def _matches_kana_row(kana: str, row_prefix: str) -> bool:
    """かな行の先頭文字でフィルタ（あ行→あいうえお のいずれかで始まるか）。

    row_prefix が "ABC" の場合は、元の名前がアルファベット始まりかで判定する
    （呼び出し元で別途処理）。
    """
    chars = _KANA_ROW_MAP.get(row_prefix, row_prefix)
    return any(kana.startswith(c) for c in chars)
from app.schemas.client import (
    CarePreference,
    ClientDetail,
    ClientSummary,
    EmergencyInfo,
    KeyPerson,
    NgAction,
    SupportLogEntry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clients", tags=["clients"])


# ---------------------------------------------------------------------------
# GET /api/clients
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ClientSummary])
def list_clients(
    kana_prefix: str | None = Query(default=None, description="かな行頭文字でフィルタ（例: あ）"),
) -> list[ClientSummary]:
    """クライアント一覧を返す。kana_prefix が指定されれば kana フィールドで前方一致フィルタ。"""
    try:
        rows = run_query(
            """
            MATCH (c:Client)
            OPTIONAL MATCH (c)-[:HAS_CONDITION]->(cond:Condition)
            RETURN c.name AS name,
                   c.dob AS dob,
                   c.bloodType AS blood_type,
                   c.kana AS kana,
                   collect(DISTINCT cond.name) AS conditions
            ORDER BY c.name
            """
        )

        summaries: list[ClientSummary] = []
        for row in rows:
            name = row["name"]
            # kana プロパティがなければ自動変換（アルファベット対応含む）
            kana: str | None = row.get("kana") or _name_to_kana(name)

            # フィルタ処理
            if kana_prefix:
                if kana_prefix == "ABC":
                    # 英字フィルタ: アルファベットで始まる名前のみ表示
                    if not _is_alpha_name(name):
                        continue
                else:
                    # かな行フィルタ: かな読みの先頭文字で判定
                    if not _matches_kana_row(kana, kana_prefix):
                        continue

            dob = row.get("dob")
            age = calculate_age(dob) if dob else None
            conditions = [c for c in (row.get("conditions") or []) if c]
            summaries.append(
                ClientSummary(
                    name=row["name"],
                    dob=str(dob) if dob else None,
                    age=age,
                    blood_type=row.get("blood_type"),
                    conditions=conditions,
                )
            )
        return summaries

    except Exception as exc:
        logger.error("list_clients failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /api/clients/{name}
# ---------------------------------------------------------------------------


@router.get("/{name}", response_model=ClientDetail)
def get_client(name: str) -> ClientDetail:
    """クライアントの詳細プロフィールを返す（1回の Cypher で全関連ノードを取得）。"""
    try:
        rows = run_query(
            """
            MATCH (c:Client {name: $name})
            OPTIONAL MATCH (c)-[:HAS_CONDITION]->(cond:Condition)
            OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
            OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
            OPTIONAL MATCH (c)-[kpRel:HAS_KEY_PERSON]->(kp:KeyPerson)
            OPTIONAL MATCH (c)-[:HAS_CERTIFICATE]->(cert:Certificate)
            OPTIONAL MATCH (c)-[:TREATED_AT]->(h:Hospital)
            OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)
            RETURN c.name AS name,
                   c.dob AS dob,
                   c.bloodType AS blood_type,
                   collect(DISTINCT {name: cond.name, diagnosedDate: cond.diagnosedDate}) AS conditions,
                   collect(DISTINCT {action: ng.action, reason: ng.reason, riskLevel: ng.riskLevel}) AS ng_actions,
                   collect(DISTINCT {category: cp.category, instruction: cp.instruction, priority: cp.priority}) AS care_preferences,
                   collect(DISTINCT {name: kp.name, relationship: kp.relationship, phone: kp.phone, rank: kpRel.rank}) AS key_persons,
                   collect(DISTINCT cert {.*}) AS certificates,
                   head(collect(DISTINCT h {.*})) AS hospital,
                   head(collect(DISTINCT g {.*})) AS guardian
            """,
            {"name": name},
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Client '{name}' not found")

        row = rows[0]
        dob = row.get("dob")
        age = calculate_age(dob) if dob else None

        # null エントリを除去（OPTIONAL MATCH で null プロパティが collect される）
        conditions = [c for c in (row.get("conditions") or []) if c.get("name")]

        ng_actions_raw = [n for n in (row.get("ng_actions") or []) if n.get("action")]
        # riskLevel でソート（LifeThreatening → Panic → その他）
        risk_order = {"LifeThreatening": 1, "Panic": 2}
        ng_actions_raw.sort(key=lambda n: risk_order.get(n.get("riskLevel", ""), 3))
        ng_actions = [
            NgAction(
                action=n["action"],
                reason=n.get("reason"),
                risk_level=n.get("riskLevel") or "Discomfort",
            )
            for n in ng_actions_raw
        ]

        care_preferences = [
            CarePreference(
                category=cp["category"],
                instruction=cp["instruction"],
                priority=cp.get("priority"),
            )
            for cp in (row.get("care_preferences") or [])
            if cp.get("category")
        ]

        kp_raw = [kp for kp in (row.get("key_persons") or []) if kp.get("name")]
        kp_raw.sort(key=lambda kp: kp.get("rank") or 999)
        key_persons = [
            KeyPerson(
                name=kp["name"],
                relationship=kp.get("relationship"),
                phone=kp.get("phone"),
                rank=kp.get("rank"),
            )
            for kp in kp_raw
        ]

        certificates = [c for c in (row.get("certificates") or []) if c]
        hospital = row.get("hospital")
        guardian = row.get("guardian")

        return ClientDetail(
            name=row["name"],
            dob=str(dob) if dob else None,
            age=age,
            blood_type=row.get("blood_type"),
            conditions=conditions,
            ng_actions=ng_actions,
            care_preferences=care_preferences,
            key_persons=key_persons,
            certificates=certificates,
            hospital=hospital,
            guardian=guardian,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_client failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /api/clients/{name}/emergency
# ---------------------------------------------------------------------------


@router.get("/{name}/emergency", response_model=EmergencyInfo)
def get_emergency(name: str) -> EmergencyInfo:
    """緊急時情報を返す（1回の Cypher で取得、NgAction 優先度順、Safety First）。"""
    try:
        rows = run_query(
            """
            MATCH (c:Client {name: $name})
            OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
            OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
            OPTIONAL MATCH (c)-[kpRel:HAS_KEY_PERSON]->(kp:KeyPerson)
            OPTIONAL MATCH (c)-[:TREATED_AT]->(h:Hospital)
            OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)
            RETURN c.name AS name,
                   collect(DISTINCT {action: ng.action, reason: ng.reason, riskLevel: ng.riskLevel}) AS ng_actions,
                   collect(DISTINCT {category: cp.category, instruction: cp.instruction, priority: cp.priority}) AS care_preferences,
                   collect(DISTINCT {name: kp.name, relationship: kp.relationship, phone: kp.phone, rank: kpRel.rank}) AS key_persons,
                   head(collect(DISTINCT h {.*})) AS hospital,
                   head(collect(DISTINCT g {.*})) AS guardian
            """,
            {"name": name},
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Client '{name}' not found")

        row = rows[0]

        # NgActions — riskLevel でソート（LifeThreatening → Panic → その他）
        ng_raw = [n for n in (row.get("ng_actions") or []) if n.get("action")]
        risk_order = {"LifeThreatening": 1, "Panic": 2}
        ng_raw.sort(key=lambda n: risk_order.get(n.get("riskLevel", ""), 3))
        ng_actions = [
            NgAction(
                action=n["action"],
                reason=n.get("reason"),
                risk_level=n.get("riskLevel") or "Discomfort",
            )
            for n in ng_raw
        ]

        care_preferences = [
            CarePreference(
                category=cp["category"],
                instruction=cp["instruction"],
                priority=cp.get("priority"),
            )
            for cp in (row.get("care_preferences") or [])
            if cp.get("category")
        ]

        kp_raw = [kp for kp in (row.get("key_persons") or []) if kp.get("name")]
        kp_raw.sort(key=lambda kp: kp.get("rank") or 999)
        key_persons = [
            KeyPerson(
                name=kp["name"],
                relationship=kp.get("relationship"),
                phone=kp.get("phone"),
                rank=kp.get("rank"),
            )
            for kp in kp_raw
        ]

        return EmergencyInfo(
            client_name=name,
            ng_actions=ng_actions,
            care_preferences=care_preferences,
            key_persons=key_persons,
            hospital=row.get("hospital"),
            guardian=row.get("guardian"),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_emergency failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /api/clients/{name}/logs
# ---------------------------------------------------------------------------


@router.get("/{name}/logs", response_model=list[SupportLogEntry])
def get_logs(name: str, limit: int = Query(default=50, ge=1, le=200)) -> list[SupportLogEntry]:
    """クライアントの支援記録を返す（デフォルト 50 件）。"""
    try:
        exists = run_query("MATCH (c:Client {name: $name}) RETURN c.name AS n LIMIT 1", {"name": name})
        if not exists:
            raise HTTPException(status_code=404, detail=f"Client '{name}' not found")

        rows = run_query(
            """
            MATCH (s:Supporter)-[:LOGGED]->(sl:SupportLog)-[:ABOUT]->(c:Client {name: $name})
            RETURN sl.date AS date,
                   sl.situation AS situation,
                   sl.action AS action,
                   sl.effectiveness AS effectiveness,
                   sl.note AS note,
                   s.name AS supporter_name
            ORDER BY sl.date DESC
            LIMIT $limit
            """,
            {"name": name, "limit": limit},
        )

        return [
            SupportLogEntry(
                date=str(r.get("date", "")) or None,
                situation=r.get("situation"),
                action=r.get("action"),
                effectiveness=r.get("effectiveness"),
                note=r.get("note"),
                supporter_name=r.get("supporter_name"),
            )
            for r in rows
        ]

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_logs failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
