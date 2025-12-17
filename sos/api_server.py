"""
nest SOS - APIサーバー
知的障害のある方が緊急時にSOSを送信するためのAPIサーバー

機能:
- SOSリクエストを受信
- Neo4jからクライアント情報を取得
- LINE Messaging APIでグループLINEに通知
"""

import os
import httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from neo4j import GraphDatabase

# 環境変数読み込み
load_dotenv()

# --- 設定 ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "")

# --- Neo4j接続 ---
driver = None

def get_driver():
    global driver
    if driver is None:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
    return driver


def run_query(query, params=None):
    """Cypherクエリ実行"""
    d = get_driver()
    with d.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]


# --- FastAPI ---
app = FastAPI(
    title="nest SOS API",
    description="知的障害のある方向けの緊急通知システム",
    version="1.0.0"
)

# CORS設定（スマホアプリからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では制限推奨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- リクエストモデル ---
class SOSRequest(BaseModel):
    client_id: str  # クライアント識別子（名前またはID）
    latitude: float | None = None
    longitude: float | None = None
    accuracy: float | None = None


class SOSResponse(BaseModel):
    success: bool
    message: str
    client_name: str | None = None


# --- LINE Messaging API ---
async def send_line_message(message: str) -> bool:
    """
    LINE Messaging APIでグループにメッセージを送信
    """
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_GROUP_ID:
        print("⚠️ LINE設定が不完全です")
        return False
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_GROUP_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                print("✅ LINE送信成功")
                return True
            else:
                print(f"❌ LINE送信失敗: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"❌ LINE送信エラー: {e}")
        return False


# --- クライアント情報取得 ---
def get_client_info(client_id: str) -> dict | None:
    """
    Neo4jからクライアント情報を取得
    """
    # 名前で検索（部分一致）
    results = run_query("""
        MATCH (c:Client)
        WHERE c.name CONTAINS $name OR c.id = $name
        OPTIONAL MATCH (c)-[r:HAS_KEY_PERSON]->(kp:KeyPerson)
        WITH c, kp, r
        ORDER BY r.rank
        RETURN c.name as name,
               c.dob as dob,
               collect({
                   name: kp.name,
                   relationship: kp.relationship,
                   phone: kp.phone,
                   rank: r.rank
               }) as keyPersons
        LIMIT 1
    """, {"name": client_id})
    
    if results:
        return results[0]
    return None


def get_client_cautions(client_name: str) -> list:
    """
    クライアントの禁忌事項（注意点）を取得
    """
    results = run_query("""
        MATCH (c:Client {name: $name})-[:MUST_AVOID]->(ng:NgAction)
        WHERE ng.riskLevel IN ['LifeThreatening', 'Panic']
        RETURN ng.action as action, ng.riskLevel as risk
        ORDER BY CASE ng.riskLevel 
            WHEN 'LifeThreatening' THEN 1 
            WHEN 'Panic' THEN 2 
            ELSE 3 END
        LIMIT 3
    """, {"name": client_name})
    
    return results


# --- SOSメッセージ作成 ---
def create_sos_message(
    client_name: str,
    key_persons: list,
    cautions: list,
    latitude: float | None = None,
    longitude: float | None = None,
    accuracy: float | None = None
) -> str:
    """
    SOSメッセージを作成
    """
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    # 基本メッセージ
    message = f"""🆘【緊急SOS】

{client_name}さんから助けを求めています！

⏰ 発信時刻: {now}
"""
    
    # 位置情報
    if latitude and longitude:
        map_url = f"https://www.google.com/maps?q={latitude},{longitude}"
        acc_text = f"（精度: 約{int(accuracy)}m）" if accuracy else ""
        message += f"""
📍 現在地:
{map_url}
{acc_text}
"""
    else:
        message += "\n📍 位置情報: 取得できませんでした\n"
    
    # キーパーソン（緊急連絡先）
    if key_persons and key_persons[0].get('name'):
        message += "\n📞 緊急連絡先:\n"
        for kp in key_persons[:3]:  # 上位3名まで
            if kp.get('name'):
                rel = kp.get('relationship', '')
                phone = kp.get('phone', '番号未登録')
                message += f"　・{kp['name']}（{rel}）{phone}\n"
    
    # 注意事項（禁忌事項）
    if cautions:
        message += "\n⚠️ 対応時の注意:\n"
        for c in cautions:
            risk_mark = "🔴" if c.get('risk') == 'LifeThreatening' else "🟠"
            message += f"　{risk_mark} {c['action']}\n"
    
    return message


# --- エンドポイント ---
@app.get("/")
async def root():
    """ヘルスチェック"""
    return {"status": "ok", "service": "nest SOS API"}


@app.post("/api/sos", response_model=SOSResponse)
async def receive_sos(request: SOSRequest):
    """
    SOSリクエストを受信し、LINEグループに通知
    """
    print(f"🆘 SOS受信: {request.client_id}")
    
    # クライアント情報を取得
    client_info = get_client_info(request.client_id)
    
    if not client_info:
        # クライアントが見つからない場合も通知は送る
        message = f"""🆘【緊急SOS】

不明なユーザー（ID: {request.client_id}）からSOSがありました。

⏰ 発信時刻: {datetime.now().strftime("%Y/%m/%d %H:%M")}
"""
        if request.latitude and request.longitude:
            message += f"\n📍 現在地:\nhttps://www.google.com/maps?q={request.latitude},{request.longitude}"
        
        await send_line_message(message)
        
        return SOSResponse(
            success=True,
            message="SOSを送信しました（未登録ユーザー）",
            client_name=None
        )
    
    client_name = client_info['name']
    key_persons = client_info.get('keyPersons', [])
    
    # 禁忌事項を取得
    cautions = get_client_cautions(client_name)
    
    # メッセージ作成
    message = create_sos_message(
        client_name=client_name,
        key_persons=key_persons,
        cautions=cautions,
        latitude=request.latitude,
        longitude=request.longitude,
        accuracy=request.accuracy
    )
    
    # LINE送信
    success = await send_line_message(message)
    
    if success:
        return SOSResponse(
            success=True,
            message="SOSを送信しました",
            client_name=client_name
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="LINE送信に失敗しました"
        )


@app.get("/api/client/{client_id}")
async def get_client(client_id: str):
    """
    クライアント情報を取得（アプリ起動時の確認用）
    """
    client_info = get_client_info(client_id)
    
    if client_info:
        return {
            "found": True,
            "name": client_info['name']
        }
    else:
        return {
            "found": False,
            "name": None
        }


# --- 静的ファイル配信（スマホアプリ） ---
# appフォルダが存在する場合、静的ファイルとして配信
import os.path
app_dir = os.path.join(os.path.dirname(__file__), "app")
if os.path.exists(app_dir):
    app.mount("/app", StaticFiles(directory=app_dir, html=True), name="app")


# --- 起動 ---
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🆘 nest SOS API サーバー")
    print("=" * 50)
    print(f"Neo4j: {NEO4J_URI}")
    print(f"LINE設定: {'✅ 設定済み' if LINE_CHANNEL_ACCESS_TOKEN else '❌ 未設定'}")
    print("=" * 50)
    print("アプリURL: http://localhost:8000/app/?id=クライアント名")
    print("API URL: http://localhost:8000/api/sos")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
