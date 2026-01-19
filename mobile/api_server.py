"""
親亡き後支援データベース - モバイルナラティブ入力API
支援者がスマホから音声でナラティブ入力 → Gemini構造化 → Neo4jグラフ登録

使用方法:
    cd neo4j-agno-agent
    uv run python mobile/api_server.py

アクセス:
    API: http://localhost:8080/api/narrative
    アプリ: http://localhost:8080/app/
"""

import os
import sys
from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# 親ディレクトリをパスに追加（lib/からインポートするため）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.ai_extractor import extract_from_text
from lib.db_operations import (
    register_to_database,
    get_clients_list,
    get_clients_list_extended,
    resolve_client,
    get_display_name,
    create_audit_log,
    get_support_logs,
)

load_dotenv()

# --- FastAPI ---
app = FastAPI(
    title="ナラティブ入力API",
    description="音声・テキストからナラティブ入力 → AI構造化 → グラフ登録",
    version="1.0.0"
)

# CORS設定
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")
cors_origins = CORS_ORIGINS.split(",") if CORS_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- リクエスト/レスポンスモデル ---
class NarrativeRequest(BaseModel):
    """ナラティブ入力リクエスト"""
    text: str  # ナラティブテキスト（音声認識結果など）
    client_name: Optional[str] = None  # クライアント名（指定時は追記モード）
    supporter_name: str  # 支援者名


class ExtractedData(BaseModel):
    """抽出されたデータ"""
    client_name: Optional[str] = None
    conditions: list = []
    ng_actions: list = []
    care_preferences: list = []
    support_logs: list = []
    certificates: list = []
    key_persons: list = []


class NarrativeResponse(BaseModel):
    """ナラティブ処理レスポンス"""
    success: bool
    message: str
    extracted: Optional[ExtractedData] = None
    raw_extraction: Optional[dict] = None  # デバッグ用


class RegisterRequest(BaseModel):
    """登録確定リクエスト"""
    extracted_data: dict  # extract_from_textの結果をそのまま
    supporter_name: str


class RegisterResponse(BaseModel):
    """登録レスポンス"""
    success: bool
    message: str
    client_name: Optional[str] = None
    registered_count: int = 0


class ClientInfo(BaseModel):
    """クライアント情報"""
    clientId: Optional[str] = None
    displayCode: Optional[str] = None
    name: str


class ClientListResponse(BaseModel):
    """クライアント一覧レスポンス"""
    clients: list[str]  # 後方互換性のため残す
    clients_extended: list[ClientInfo] = []  # 仮名化対応版


# --- ヘルパー関数 ---
def format_extracted_data(raw: dict) -> ExtractedData:
    """抽出データを整形"""
    return ExtractedData(
        client_name=raw.get("client", {}).get("name"),
        conditions=[c.get("name", "") for c in raw.get("conditions", []) if c.get("name")],
        ng_actions=[
            {
                "action": ng.get("action", ""),
                "reason": ng.get("reason", ""),
                "risk_level": ng.get("riskLevel", "Panic")
            }
            for ng in raw.get("ngActions", []) if ng.get("action")
        ],
        care_preferences=[
            {
                "category": cp.get("category", "その他"),
                "instruction": cp.get("instruction", ""),
                "priority": cp.get("priority", "Medium")
            }
            for cp in raw.get("carePreferences", []) if cp.get("instruction")
        ],
        support_logs=[
            {
                "date": sl.get("date", date.today().isoformat()),
                "supporter": sl.get("supporter", ""),
                "situation": sl.get("situation", ""),
                "action": sl.get("action", ""),
                "effectiveness": sl.get("effectiveness", "Neutral"),
                "note": sl.get("note", "")
            }
            for sl in raw.get("supportLogs", []) if sl.get("action")
        ],
        certificates=[
            {
                "type": cert.get("type", ""),
                "grade": cert.get("grade", ""),
                "renewal_date": cert.get("nextRenewalDate")
            }
            for cert in raw.get("certificates", []) if cert.get("type")
        ],
        key_persons=[
            {
                "name": kp.get("name", ""),
                "relationship": kp.get("relationship", ""),
                "phone": kp.get("phone", ""),
                "role": kp.get("role", "")
            }
            for kp in raw.get("keyPersons", []) if kp.get("name")
        ]
    )


# --- エンドポイント ---
@app.get("/")
async def root():
    """ヘルスチェック"""
    return {"status": "ok", "service": "Narrative Input API"}


@app.get("/api/clients", response_model=ClientListResponse)
async def list_clients():
    """登録済みクライアント一覧を取得（仮名化対応）"""
    try:
        # 後方互換性のため名前リストも返す
        clients = get_clients_list()

        # 仮名化対応版（clientId, displayCode, name）
        extended = get_clients_list_extended(include_pii=True)
        clients_extended = [
            ClientInfo(
                clientId=c.get('clientId'),
                displayCode=c.get('displayCode'),
                name=c.get('name', '不明')
            )
            for c in extended
        ]

        return ClientListResponse(clients=clients, clients_extended=clients_extended)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"クライアント取得エラー: {str(e)}")


@app.post("/api/narrative/extract", response_model=NarrativeResponse)
async def extract_narrative(request: NarrativeRequest):
    """
    ナラティブテキストからデータを抽出（プレビュー用）
    登録は行わず、抽出結果のみ返す
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="テキストが空です")

    print(f"📝 ナラティブ抽出開始: {len(request.text)}文字, 支援者: {request.supporter_name}")

    try:
        # Gemini で構造化
        extracted = extract_from_text(request.text, request.client_name)

        if not extracted:
            return NarrativeResponse(
                success=False,
                message="テキストから情報を抽出できませんでした。もう少し詳しく入力してください。",
                extracted=None
            )

        # 支援記録に支援者名を設定
        for log in extracted.get("supportLogs", []):
            if not log.get("supporter"):
                log["supporter"] = request.supporter_name

        # 日付が未設定の支援記録に今日の日付を設定
        today = date.today().isoformat()
        for log in extracted.get("supportLogs", []):
            if not log.get("date"):
                log["date"] = today

        formatted = format_extracted_data(extracted)

        print(f"✅ 抽出成功: クライアント={formatted.client_name}, "
              f"禁忌={len(formatted.ng_actions)}, ケア={len(formatted.care_preferences)}, "
              f"記録={len(formatted.support_logs)}")

        return NarrativeResponse(
            success=True,
            message="抽出完了。内容を確認して登録してください。",
            extracted=formatted,
            raw_extraction=extracted  # 登録時に使用
        )

    except Exception as e:
        print(f"❌ 抽出エラー: {e}")
        raise HTTPException(status_code=500, detail=f"抽出処理エラー: {str(e)}")


@app.post("/api/narrative/register", response_model=RegisterResponse)
async def register_narrative(request: RegisterRequest):
    """
    抽出済みデータをNeo4jに登録
    """
    if not request.extracted_data:
        raise HTTPException(status_code=400, detail="登録データがありません")

    client_name = request.extracted_data.get("client", {}).get("name")
    if not client_name:
        raise HTTPException(status_code=400, detail="クライアント名が特定できません")

    print(f"💾 登録開始: クライアント={client_name}, 支援者={request.supporter_name}")

    try:
        # Neo4j に登録
        result = register_to_database(request.extracted_data, request.supporter_name)

        print(f"✅ 登録完了: {result}")

        return RegisterResponse(
            success=True,
            message=f"{client_name}さんの情報を登録しました",
            client_name=result.get("client_name"),
            registered_count=result.get("registered_count", 0)
        )

    except Exception as e:
        print(f"❌ 登録エラー: {e}")
        raise HTTPException(status_code=500, detail=f"登録エラー: {str(e)}")


@app.get("/api/clients/{client_name}/logs")
async def get_client_logs(client_name: str, limit: int = 10):
    """クライアントの支援記録を取得"""
    try:
        logs = get_support_logs(client_name, limit)
        return {"client_name": client_name, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得エラー: {str(e)}")


# --- 静的ファイル配信（モバイルアプリ） ---
app_dir = os.path.join(os.path.dirname(__file__), "app")
if os.path.exists(app_dir):
    app.mount("/app", StaticFiles(directory=app_dir, html=True), name="app")


# --- 起動 ---
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("📝 ナラティブ入力API サーバー")
    print("=" * 60)
    print("音声・テキスト → Gemini構造化 → Neo4jグラフ登録")
    print("=" * 60)
    print()
    print("🌐 アプリURL: http://localhost:8080/app/")
    print("🔌 API URL:   http://localhost:8080/api/narrative/extract")
    print()
    print("📱 スマホからは同一WiFi内で:")
    print("   http://<このPCのIP>:8080/app/")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8080)
