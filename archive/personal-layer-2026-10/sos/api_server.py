"""
nest SOS - APIサーバー
知的障害のある方が緊急時にSOSを送信するためのAPIサーバー

機能:
- SOSリクエストを受信
- Neo4jからクライアント情報を取得
- LINE Messaging APIでグループLINEに通知
"""

import os
import sys
import httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from neo4j import GraphDatabase

# 親ディレクトリをパスに追加（lib/からインポートするため）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.db_new_operations import resolve_client, get_display_name, run_query
from lib.ai_extractor import get_agent

# 環境変数読み込み
load_dotenv()

# --- 設定 ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID", "")

# CORS設定（カンマ区切りで複数指定可能、未設定時は全許可）
# 例: "https://example.com,https://app.example.com"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")

# --- Neo4j接続 ---
# lib/db_operations.py から run_query を使用するため、ここでは定義不要
# 古い関数が呼ばれている箇所があれば run_query に置き換える



# --- FastAPI ---
app = FastAPI(
    title="nest SOS API",
    description="知的障害のある方向けの緊急通知システム",
    version="1.0.0"
)

# CORS設定（スマホアプリからのアクセスを許可）
# CORS_ORIGINS環境変数が設定されている場合はそれを使用、未設定時は全許可（開発用）
cors_origins = CORS_ORIGINS.split(",") if CORS_ORIGINS else ["*"]
if CORS_ORIGINS:
    print(f"✅ CORS許可オリジン: {cors_origins}")
else:
    print("⚠️ CORS_ORIGINSが未設定のため全オリジンを許可（本番環境では設定推奨）")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
    mock_mode: bool = False
    sent_message: str | None = None


# --- LINE Messaging API ---

# --- LINE Messaging API ---
_mock_mode = False

async def send_line_message(message: str) -> bool:
    """LINE Messaging APIでメッセージ送信（モック対応）"""
    global _mock_mode
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.getenv("LINE_GROUP_ID")

    if not token or token == "YOUR_ACCESS_TOKEN" or not group_id:
        _mock_mode = True
        print("\n📱 [模擬送信モード] LINE認証情報が未設定のためモック送信します")
        print(f"📱 [模擬送信] 送信先グループ: {group_id or '未設定'}")
        print(f"📱 [模擬送信] メッセージ内容:\n{'='*40}\n{message}\n{'='*40}")
        return True

    _mock_mode = False
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "to": group_id,
        "messages": [{"type": "text", "text": message}]
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
    Neo4jからクライアント情報を取得（仮名化対応）

    対応する識別子:
    - clientId (c-xxxx)
    - displayCode (A-001)
    - name (山田健太)
    """
    # まず仮名化対応の解決を試みる
    resolved = resolve_client(client_id)

    if resolved:
        # 仮名化スキーマで見つかった場合
        client_name = resolved.get('name')
        client_id_internal = resolved.get('clientId')

        # キーパーソンを取得（clientId または name で検索）
        if client_id_internal:
            kp_results = run_query("""
                MATCH (c:Client {clientId: $clientId})
                OPTIONAL MATCH (c)-[r:HAS_KEY_PERSON]->(kp:KeyPerson)
                WITH kp, r
                ORDER BY r.rank
                RETURN collect({
                    name: kp.name,
                    relationship: kp.relationship,
                    phone: kp.phone,
                    rank: r.rank
                }) as keyPersons
            """, {"clientId": client_id_internal})
        else:
            kp_results = run_query("""
                MATCH (c:Client {name: $name})
                OPTIONAL MATCH (c)-[r:HAS_KEY_PERSON]->(kp:KeyPerson)
                WITH kp, r
                ORDER BY r.rank
                RETURN collect({
                    name: kp.name,
                    relationship: kp.relationship,
                    phone: kp.phone,
                    rank: r.rank
                }) as keyPersons
            """, {"name": client_name})

        return {
            "name": client_name,
            "clientId": client_id_internal,
            "displayCode": resolved.get('displayCode'),
            "dob": resolved.get('dob'),
            "keyPersons": kp_results[0]['keyPersons'] if kp_results else []
        }

    # 後方互換性: 旧スキーマでの検索
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


def get_client_cautions(client_identifier: str) -> list:
    """
    クライアントの禁忌事項（注意点）を取得（仮名化対応）

    Args:
        client_identifier: clientId, displayCode, または name
    """
    # まず仮名化対応の解決を試みる
    resolved = resolve_client(client_identifier)

    if resolved and resolved.get('clientId'):
        # clientId で検索
        results = run_query("""
            MATCH (c:Client {clientId: $clientId})-[:MUST_AVOID]->(ng:NgAction)
            WHERE ng.riskLevel IN ['LifeThreatening', 'Panic']
            RETURN ng.action as action, ng.riskLevel as risk
            ORDER BY CASE ng.riskLevel
                WHEN 'LifeThreatening' THEN 1
                WHEN 'Panic' THEN 2
                ELSE 3 END
            LIMIT 3
        """, {"clientId": resolved['clientId']})
        return results

    # 後方互換性: name で検索
    client_name = resolved.get('name') if resolved else client_identifier
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


# --- SOSメッセージ作成 (AI Agent) ---

SMART_SOS_PROMPT = """
あなたは「親亡き後支援データベース」の緊急対応コーディネーター（AI）です。
知的障害のあるクライアントからSOSが発信されました。
登録されているデータベース情報を元に、支援者グループ（LINE）へ送る**緊急メッセージ**を作成してください。

【状況】
- 発信者: {client_name}
- 現在時刻: {time}
- 現在地: {location_url} （{accuracy}）
- **発生状況**: {situation_context}

【クライアント情報】
{context_info}

【作成指示】
1. **冷静かつ緊急に**: 危機感を伝えつつ、読み手がパニックにならないように。
2. **状況に応じた判断**: 「発生状況」と「クライアント情報」を突き合わせ、最適な対応を指示する。
3. **指示は明確に**: 誰が何をすべきか（特にキーパーソンの役割）を強調する。
4. **禁忌事項（NG）を警告**: 二次被害を防ぐため、絶対にしてはいけないことを目立たせる。
5. **推奨ケア（Care）を提案**: どうすれば本人が落ち着くかを具体的に伝える。

【メッセージ形式（プレーンテキスト）】
================================
🆘 緊急SOS: {client_name}さんからの発信
================================

【現在地】
{location_url}

【状況: {situation_context}】
[プロフェッショナルな緊急対応アドバイスをここに記述]

【⚠️ 注意事項・禁忌】
[NgActionに基づく注意点]

【📞 連絡先・キーパーソン】
[KeyPersonsのリスト]

================================
※このメッセージはAIにより自動生成されています。
"""


# Import the new skill
from skills.sos_orchestrator.smart_sos import smart_sos_decision

def create_smart_sos_message(
    client_name: str,
    key_persons: list,
    cautions: list,
    care_preferences: list = [],
    hospitals: list = [],
    latitude: float | None = None,
    longitude: float | None = None,
    accuracy: float | None = None,
    situation_context: str = "緊急SOS"
) -> str:
    """
    Use the SOS Orchestrator Skill to generate the message.
    """
    try:
        # Use the deterministic skill decision logic
        # Note: The skill internally fetches data, but here we can pass context.
        # Ideally, we should refactor the skill to accept data or just use the skill's fetch logic.
        # For consistency with the verification, we'll let the skill fetch fresh data based on client_name.
        
        decision = smart_sos_decision(client_name, situation_context)
        
        # Override the message body with location info if available
        base_message = decision.get('message', "SOS Generation Failed")
        
        location_info = ""
        if latitude and longitude:
            map_url = f"https://www.google.com/maps?q={latitude},{longitude}"
            acc_text = f"（精度: 約{int(accuracy)}m）" if accuracy else ""
            location_info = f"\n📍 現在地:\n{map_url}\n{acc_text}\n"
        else:
            location_info = "\n📍 位置情報: 取得できませんでした\n"

        # Combine
        final_message = base_message + "\n" + location_info
        
        # Add timestamp if not present in skill output (it isn't)
        now_str = datetime.now().strftime("%Y/%m/%d %H:%M")
        final_message = f"⏰ 発信時刻: {now_str}\n\n" + final_message
        
        return final_message

    except Exception as e:
        print(f"❌ Smart SOS generation failed: {e}")
        # Foldback to legacy
        return create_sos_message(client_name, key_persons, cautions, latitude, longitude, accuracy)


# --- SOSメッセージ作成 (Legacy) ---
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
            client_name=None,
            mock_mode=_mock_mode,
            sent_message=message
        )
    
    client_name = client_info['name']
    key_persons = client_info.get('keyPersons', [])
    
    # 禁忌事項を取得
    cautions = get_client_cautions(client_name)
    
    # ケア情報とかかりつけ医も取得してコンテキストを強化
    care_preferences = run_query("""
        MATCH (c:Client {name: $name})-[:REQUIRES]->(cp:CarePreference)
        RETURN cp.category as category, cp.instruction as instruction, cp.priority as priority
    """, {"name": client_name})

    hospitals = run_query("""
        MATCH (c:Client {name: $name})-[:TREATED_AT]->(h:Hospital)
        RETURN h.name as name, h.specialty as specialty, h.phone as phone
    """, {"name": client_name})

    # メッセージ作成 (Smart)
    message = create_smart_sos_message(
        client_name=client_name,
        key_persons=key_persons,
        cautions=cautions,
        care_preferences=care_preferences,
        hospitals=hospitals,
        latitude=request.latitude,
        longitude=request.longitude,
        accuracy=request.accuracy
    )
    
    print(f"📝 Generated SOS Message:\n{message}")
    
    # LINE送信
    success = await send_line_message(message)
    
    if success:
        return SOSResponse(
            success=True,
            message="SOSを送信しました",
            client_name=client_name,
            mock_mode=_mock_mode,
            sent_message=message
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
