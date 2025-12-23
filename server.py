"""
親亡き後支援データベース - MCPサーバー
Manifesto: Post-Parent Support & Advocacy Graph 準拠

Version: 2.0
マニフェストの4つの価値を最優先:
1. Dignity (尊厳) - 歴史と意思を持つ人間として記録
2. Safety (安全) - 緊急時に迷わせない構造
3. Continuity (継続性) - 支援者が替わってもケアの質を維持
4. Advocacy (権利擁護) - 本人の声なき声を法的後ろ盾と紐づける
"""

import os
import sys
import json
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from neo4j import GraphDatabase

# 環境変数の読み込み
load_dotenv()

# 年齢計算用ヘルパー関数
def calculate_age(birth_date) -> int | None:
    """生年月日から年齢を計算"""
    if birth_date is None:
        return None

    # Neo4jのdate型またはdatetimeから変換
    if hasattr(birth_date, 'to_native'):
        birth_date = birth_date.to_native()
    elif isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    if not isinstance(birth_date, date):
        return None

    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age if age >= 0 else None


def format_dob_with_age(dob) -> str:
    """生年月日と年齢をフォーマット"""
    if dob is None:
        return "不明"

    # Neo4jのdate型から変換
    if hasattr(dob, 'to_native'):
        dob = dob.to_native()

    age = calculate_age(dob)

    if isinstance(dob, date):
        dob_str = dob.strftime("%Y-%m-%d")
    else:
        dob_str = str(dob)

    if age is not None:
        return f"{dob_str}（{age}歳）"
    return dob_str

# MCPサーバーの定義
mcp = FastMCP("ParentSupportDB")

# --- ログ出力（標準エラー出力のみ使用）---
def log(message):
    sys.stderr.write(f"[ServerLog] {message}\n")
    sys.stderr.flush()

# --- Neo4j接続管理 ---
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"), 
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

# =============================================================================
# スキーマ定義（マニフェスト完全準拠）
# =============================================================================

SCHEMA_DOCUMENTATION = """
【データベーススキーマ - マニフェスト完全準拠】

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 第1の柱：本人性 (Identity & Narrative)
  「その人は誰か」を定義。属性だけでなく人生の物語を含む。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:Client (本人)
  - name: string        // 氏名
  - dob: date           // 生年月日
  - bloodType: string   // 血液型
  - clientId: string    // 管理用ID（任意）

:LifeHistory (生育歴・エピソード)
  - era: string         // 時期（例: '幼少期', '学齢期', '成人後'）
  - episode: string     // エピソード内容
  - emotion: string     // その時の感情・反応（任意）

:Wish (本人・家族の願い)
  - content: string     // 願いの内容
  - status: string      // 'Active' / 'Archived'
  - date: date          // 記録日

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 第2の柱：ケアの暗黙知 (Care Instructions)
  「どう接すべきか」を定義。親の頭の中にあったマニュアルを形式知化。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:CarePreference (具体的配慮・推奨ケア)
  - category: string    // カテゴリ（食事/睡眠/パニック/移動/入浴等）
  - instruction: string // 具体的な手順・方法
  - priority: string    // 'High' / 'Medium' / 'Low'

:NgAction (禁忌事項) ★最重要★
  - action: string      // 絶対にしてはいけないこと
  - reason: string      // 理由（なぜ危険か）
  - riskLevel: string   // 'LifeThreatening'(命に関わる) / 'Panic'(パニック誘発) / 'Discomfort'(不快)

:Condition (特性・医学的診断)
  - name: string        // 診断名・特性名
  - diagnosisDate: date // 診断日（任意）
  - status: string      // 'Active' / 'Resolved'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 第3の柱：法的基盤 (Legal Basis)
  「何の権利があるか」を定義。支援を受けるための資格と行政の決定。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:Certificate (手帳・受給者証)
  - type: string            // '療育手帳' / '精神障害者保健福祉手帳' / '身体障害者手帳' / '受給者証'
  - grade: string           // 等級（例: 'A1', 'B1', '1級', '区分5'）
  - issueDate: date         // 交付日
  - nextRenewalDate: date   // 次回更新日 ★期限管理重要★

:PublicAssistance (公的扶助・給付)
  - type: string        // '生活保護' / '特別障害者手当' / '障害年金' 等
  - grade: string       // 等級（該当する場合）
  - startDate: date     // 開始日

:Organization (関係機関)
  - name: string        // 機関名
  - type: string        // '行政' / '医療' / '福祉' / '教育'
  - contact: string     // 連絡先
  - address: string     // 住所

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 第4の柱：危機管理ネットワーク (Safety Net)
  「誰が守るか」を定義。緊急時の指揮命令系統と法的権限。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:KeyPerson (キーパーソン・緊急連絡先)
  - name: string        // 氏名
  - relationship: string// 続柄（叔父, 姉, 友人等）
  - phone: string       // 電話番号
  - role: string        // '緊急連絡先' / '医療同意' / '金銭管理' 等
  - rank: integer       // 優先順位（1が最優先）

:Guardian (成年後見人等)
  - name: string        // 氏名または法人名
  - type: string        // '成年後見' / '保佐' / '補助' / '任意後見'
  - phone: string       // 連絡先
  - organization: string// 所属（法人後見の場合）

:Supporter (支援者)
  - name: string        // 氏名
  - role: string        // '相談支援専門員' / 'サービス管理責任者' / 'ヘルパー' 等
  - organization: string// 所属事業所
  - phone: string       // 連絡先

:Hospital (医療機関)
  - name: string        // 病院名
  - specialty: string   // 診療科・専門
  - phone: string       // 電話番号
  - address: string     // 住所
  - doctor: string      // 担当医名（任意）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ リレーション定義
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【第1の柱】
(:Client)-[:HAS_HISTORY]->(:LifeHistory)
(:Client)-[:HAS_WISH]->(:Wish)

【第2の柱】
(:Client)-[:HAS_CONDITION]->(:Condition)
(:Client)-[:REQUIRES]->(:CarePreference)
(:Client)-[:MUST_AVOID]->(:NgAction)
(:CarePreference)-[:ADDRESSES]->(:Condition)  // このケアはこの特性に対応
(:NgAction)-[:IN_CONTEXT]->(:Condition)       // この禁忌はこの特性に関連

【第3の柱】
(:Client)-[:HAS_CERTIFICATE]->(:Certificate)
(:Client)-[:RECEIVES]->(:PublicAssistance)
(:Client)-[:REGISTERED_AT]->(:Organization)

【第4の柱】
(:Client)-[:HAS_KEY_PERSON {rank: 1}]->(:KeyPerson)
(:Client)-[:HAS_LEGAL_REP]->(:Guardian)
(:Client)-[:SUPPORTED_BY]->(:Supporter)
(:Client)-[:TREATED_AT]->(:Hospital)
"""

# =============================================================================
# ツール1: 汎用Cypherクエリ実行
# =============================================================================

@mcp.tool()
def run_cypher_query(cypher: str) -> str:
    """
    Neo4jデータベースに対して、任意のCypherクエリを実行し、結果をJSON形式で返します。
    検索、データの確認、登録などに使用してください。
    
    """ + SCHEMA_DOCUMENTATION
    try:
        log(f"Cypher受信: {cypher}")
        with driver.session() as session:
            result = session.run(cypher)
            data = [record.data() for record in result]
            
            if not data:
                return "検索結果: 0件"
            
            return json.dumps(data, ensure_ascii=False, indent=2, default=str)
            
    except Exception as e:
        log(f"エラー: {e}")
        return f"Cypher実行エラー: {e}"

# =============================================================================
# ツール2: 緊急時情報検索（Safety First プロトコル）
# =============================================================================

@mcp.tool()
def search_emergency_info(client_name: str, situation: str = "") -> str:
    """
    【緊急時専用】クライアントの安全に関わる情報を優先順位付きで取得します。
    
    ★ AI運用プロトコル「Safety First」に基づき、以下の順序で情報を返します：
    1. NgAction（禁忌事項）- 二次被害を防ぐため最優先
    2. CarePreference（具体的対処）- その場を落ち着かせるため
    3. KeyPerson（緊急連絡先）- ランク順
    4. Hospital（かかりつけ医）
    5. Guardian（法的代理人）
    
    Args:
        client_name: クライアントの名前（部分一致可）
        situation: 状況キーワード（例: 'パニック', '食事', '入浴'）※任意
    
    Returns:
        優先順位付きの緊急対応情報（JSON形式）
    """
    try:
        log(f"緊急検索: {client_name}, 状況: {situation}")

        # パラメータ化されたクエリ（Cypherインジェクション対策）
        # situation が指定された場合は関連フィルタを適用
        query = """
        // 1. 禁忌事項（最優先）
        MATCH (c:Client)
        WHERE c.name CONTAINS $name
        OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
        WHERE $situation = '' OR ng.action CONTAINS $situation
        OPTIONAL MATCH (ng)-[:IN_CONTEXT]->(ngCon:Condition)
        WITH c, collect(DISTINCT {
            action: ng.action,
            reason: ng.reason,
            riskLevel: ng.riskLevel,
            context: ngCon.name
        }) AS ngActions

        // 2. 推奨ケア
        OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
        WHERE $situation = '' OR cp.category CONTAINS $situation
        OPTIONAL MATCH (cp)-[:ADDRESSES]->(cpCon:Condition)
        WITH c, ngActions, collect(DISTINCT {
            category: cp.category,
            instruction: cp.instruction,
            priority: cp.priority,
            forCondition: cpCon.name
        }) AS carePrefs

        // 3. 緊急連絡先（ランク順）
        OPTIONAL MATCH (c)-[kpRel:HAS_KEY_PERSON]->(kp:KeyPerson)
        WITH c, ngActions, carePrefs, collect(DISTINCT {
            rank: kpRel.rank,
            name: kp.name,
            relationship: kp.relationship,
            phone: kp.phone,
            role: kp.role
        }) AS keyPersons

        // 4. かかりつけ医
        OPTIONAL MATCH (c)-[:TREATED_AT]->(h:Hospital)
        WITH c, ngActions, carePrefs, keyPersons, collect(DISTINCT {
            name: h.name,
            specialty: h.specialty,
            phone: h.phone,
            doctor: h.doctor
        }) AS hospitals

        // 5. 法的代理人
        OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)

        RETURN
            c.name AS client,
            c.dob AS dob,
            c.bloodType AS bloodType,
            ngActions AS 禁忌事項_最優先,
            carePrefs AS 推奨ケア,
            keyPersons AS 緊急連絡先,
            hospitals AS かかりつけ医,
            collect(DISTINCT {
                name: g.name,
                type: g.type,
                phone: g.phone
            }) AS 法的代理人
        """

        with driver.session() as session:
            result = session.run(query, name=client_name, situation=situation or '')
            data = [record.data() for record in result]
            
            if not data or not data[0].get('client'):
                return f"'{client_name}' に該当するクライアントが見つかりませんでした。"

            # 年齢計算
            dob = data[0].get('dob')
            dob_with_age = format_dob_with_age(dob)

            # 結果を整形
            response = {
                "⚠️ 緊急対応情報": data[0].get('client'),
                "生年月日（年齢）": dob_with_age,
                "血液型": data[0].get('bloodType'),
                "🚫 1. 禁忌事項（絶対にしないこと）": [x for x in data[0].get('禁忌事項_最優先', []) if x.get('action')],
                "✅ 2. 推奨ケア（こうすると落ち着く）": [x for x in data[0].get('推奨ケア', []) if x.get('instruction')],
                "📞 3. 緊急連絡先": sorted([x for x in data[0].get('緊急連絡先', []) if x.get('name')], key=lambda x: x.get('rank', 99)),
                "🏥 4. かかりつけ医": [x for x in data[0].get('かかりつけ医', []) if x.get('name')],
                "⚖️ 5. 法的代理人": [x for x in data[0].get('法的代理人', []) if x.get('name')]
            }
            
            return json.dumps(response, ensure_ascii=False, indent=2, default=str)
            
    except Exception as e:
        log(f"緊急検索エラー: {e}")
        return f"エラーが発生しました: {e}"

# =============================================================================
# ツール3: 更新期限チェック
# =============================================================================

@mcp.tool()
def check_renewal_dates(days_ahead: int = 90, client_name: str = "") -> str:
    """
    手帳・受給者証の更新期限が近いクライアントを検索します。
    
    期限管理は権利擁護の基本です。更新漏れは本人の不利益に直結します。
    
    Args:
        days_ahead: 何日先までをチェックするか（デフォルト: 90日）
        client_name: 特定のクライアントのみ検索する場合に指定（任意）
    
    Returns:
        更新期限が近い証明書のリスト
    """
    try:
        log(f"期限チェック: {days_ahead}日以内, クライアント: {client_name or '全員'}")

        # パラメータ化されたクエリ（Cypherインジェクション対策）
        query = """
        MATCH (c:Client)-[:HAS_CERTIFICATE]->(cert:Certificate)
        WHERE cert.nextRenewalDate IS NOT NULL
          AND ($client_name = '' OR c.name CONTAINS $client_name)
        WITH c, cert,
             duration.inDays(date(), cert.nextRenewalDate).days AS daysUntilRenewal
        WHERE daysUntilRenewal <= $days AND daysUntilRenewal >= 0
        RETURN
            c.name AS クライアント,
            cert.type AS 証明書種類,
            cert.grade AS 等級,
            cert.nextRenewalDate AS 更新期限,
            daysUntilRenewal AS 残り日数
        ORDER BY daysUntilRenewal ASC
        """

        with driver.session() as session:
            result = session.run(query, days=days_ahead, client_name=client_name or '')
            data = [record.data() for record in result]
            
            if not data:
                return f"{days_ahead}日以内に更新期限を迎える証明書はありません。"
            
            # 緊急度でグループ化
            urgent = [x for x in data if x['残り日数'] <= 30]
            warning = [x for x in data if 30 < x['残り日数'] <= 60]
            notice = [x for x in data if x['残り日数'] > 60]
            
            response = {
                "🔴 緊急（30日以内）": urgent,
                "🟡 注意（31-60日）": warning,
                "🟢 確認（61日以上）": notice
            }
            
            return json.dumps(response, ensure_ascii=False, indent=2, default=str)
            
    except Exception as e:
        log(f"期限チェックエラー: {e}")
        return f"エラーが発生しました: {e}"

# =============================================================================
# ツール4: クライアント全体像の取得
# =============================================================================

@mcp.tool()
def get_client_profile(client_name: str) -> str:
    """
    クライアントの全体像（プロフィール）を取得します。
    
    マニフェストの4本柱すべての情報を統合して返します：
    - 第1の柱：本人性（基本情報、生育歴、願い）
    - 第2の柱：ケアの暗黙知（特性、配慮事項、禁忌）
    - 第3の柱：法的基盤（手帳、公的扶助）
    - 第4の柱：危機管理ネットワーク（キーパーソン、後見人、支援者）
    
    Args:
        client_name: クライアントの名前（部分一致可）
    
    Returns:
        クライアントの包括的なプロフィール情報
    """
    try:
        log(f"プロフィール取得: {client_name}")
        
        query = """
        MATCH (c:Client)
        WHERE c.name CONTAINS $name
        
        // 第1の柱：本人性
        OPTIONAL MATCH (c)-[:HAS_HISTORY]->(h:LifeHistory)
        OPTIONAL MATCH (c)-[:HAS_WISH]->(w:Wish)
        
        // 第2の柱：ケアの暗黙知
        OPTIONAL MATCH (c)-[:HAS_CONDITION]->(con:Condition)
        OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
        OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
        
        // 第3の柱：法的基盤
        OPTIONAL MATCH (c)-[:HAS_CERTIFICATE]->(cert:Certificate)
        OPTIONAL MATCH (c)-[:RECEIVES]->(pa:PublicAssistance)
        
        // 第4の柱：危機管理ネットワーク
        OPTIONAL MATCH (c)-[kpRel:HAS_KEY_PERSON]->(kp:KeyPerson)
        OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)
        OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(s:Supporter)
        OPTIONAL MATCH (c)-[:TREATED_AT]->(hosp:Hospital)
        
        RETURN 
            c.name AS 氏名,
            c.dob AS 生年月日,
            c.bloodType AS 血液型,
            
            collect(DISTINCT {era: h.era, episode: h.episode}) AS 生育歴,
            collect(DISTINCT {content: w.content, status: w.status}) AS 願い,
            
            collect(DISTINCT {name: con.name, status: con.status}) AS 特性_診断,
            collect(DISTINCT {category: cp.category, instruction: cp.instruction, priority: cp.priority}) AS 配慮事項,
            collect(DISTINCT {action: ng.action, reason: ng.reason, riskLevel: ng.riskLevel}) AS 禁忌事項,
            
            collect(DISTINCT {type: cert.type, grade: cert.grade, nextRenewalDate: cert.nextRenewalDate}) AS 手帳_受給者証,
            collect(DISTINCT {type: pa.type, grade: pa.grade}) AS 公的扶助,
            
            collect(DISTINCT {rank: kpRel.rank, name: kp.name, relationship: kp.relationship, phone: kp.phone, role: kp.role}) AS キーパーソン,
            collect(DISTINCT {name: g.name, type: g.type, phone: g.phone}) AS 後見人等,
            collect(DISTINCT {name: s.name, role: s.role, organization: s.organization}) AS 支援者,
            collect(DISTINCT {name: hosp.name, specialty: hosp.specialty, phone: hosp.phone}) AS 医療機関
        """
        
        with driver.session() as session:
            result = session.run(query, name=client_name)
            data = [record.data() for record in result]
            
            if not data or not data[0].get('氏名'):
                return f"'{client_name}' に該当するクライアントが見つかりませんでした。"
            
            # 空のデータをフィルタリング
            profile = data[0]

            # 年齢計算
            dob = profile.get('生年月日')
            dob_with_age = format_dob_with_age(dob)

            clean_profile = {
                "【基本情報】": {
                    "氏名": profile.get('氏名'),
                    "生年月日（年齢）": dob_with_age,
                    "血液型": profile.get('血液型')
                },
                "【第1の柱：本人性】": {
                    "生育歴": [x for x in profile.get('生育歴', []) if x.get('episode')],
                    "願い": [x for x in profile.get('願い', []) if x.get('content')]
                },
                "【第2の柱：ケアの暗黙知】": {
                    "特性・診断": [x for x in profile.get('特性_診断', []) if x.get('name')],
                    "配慮事項": [x for x in profile.get('配慮事項', []) if x.get('instruction')],
                    "🚫 禁忌事項": [x for x in profile.get('禁忌事項', []) if x.get('action')]
                },
                "【第3の柱：法的基盤】": {
                    "手帳・受給者証": [x for x in profile.get('手帳_受給者証', []) if x.get('type')],
                    "公的扶助": [x for x in profile.get('公的扶助', []) if x.get('type')]
                },
                "【第4の柱：危機管理ネットワーク】": {
                    "キーパーソン": sorted([x for x in profile.get('キーパーソン', []) if x.get('name')], key=lambda x: x.get('rank', 99)),
                    "後見人等": [x for x in profile.get('後見人等', []) if x.get('name')],
                    "支援者": [x for x in profile.get('支援者', []) if x.get('name')],
                    "医療機関": [x for x in profile.get('医療機関', []) if x.get('name')]
                }
            }
            
            return json.dumps(clean_profile, ensure_ascii=False, indent=2, default=str)
            
    except Exception as e:
        log(f"プロフィール取得エラー: {e}")
        return f"エラーが発生しました: {e}"

# =============================================================================
# ツール5: 登録済みクライアント一覧
# =============================================================================

@mcp.tool()
def list_clients() -> str:
    """
    登録されているすべてのクライアントの一覧と、各クライアントの情報登録状況を取得します。

    Returns:
        クライアント一覧と登録状況のサマリー（年齢表示付き）
    """
    try:
        log("クライアント一覧取得")

        query = """
        MATCH (c:Client)
        OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
        OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
        OPTIONAL MATCH (c)-[:HAS_KEY_PERSON]->(kp:KeyPerson)
        OPTIONAL MATCH (c)-[:HAS_CERTIFICATE]->(cert:Certificate)
        OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)

        RETURN
            c.name AS 氏名,
            c.dob AS 生年月日,
            count(DISTINCT ng) AS 禁忌登録数,
            count(DISTINCT cp) AS 配慮事項数,
            count(DISTINCT kp) AS キーパーソン数,
            count(DISTINCT cert) AS 手帳数,
            count(DISTINCT g) AS 後見人
        ORDER BY c.name
        """

        with driver.session() as session:
            result = session.run(query)
            data = [record.data() for record in result]

            if not data:
                return "登録されているクライアントはいません。"

            # 年齢を追加
            for item in data:
                dob = item.get('生年月日')
                item['生年月日（年齢）'] = format_dob_with_age(dob)
                # 元の生年月日フィールドは削除（重複を避ける）
                if '生年月日' in item:
                    del item['生年月日']

            return json.dumps({
                "登録クライアント数": len(data),
                "一覧": data
            }, ensure_ascii=False, indent=2, default=str)
            
    except Exception as e:
        log(f"一覧取得エラー: {e}")
        return f"エラーが発生しました: {e}"

# =============================================================================
# ツール6: データベース統計情報
# =============================================================================

@mcp.tool()
def get_database_stats() -> str:
    """
    データベース全体の統計情報を取得します。
    各ノードタイプの登録数、リレーション数などを確認できます。
    
    Returns:
        データベースの統計情報
    """
    try:
        log("統計情報取得")
        
        queries = {
            "クライアント数": "MATCH (n:Client) RETURN count(n) AS count",
            "禁忌事項数": "MATCH (n:NgAction) RETURN count(n) AS count",
            "配慮事項数": "MATCH (n:CarePreference) RETURN count(n) AS count",
            "特性・診断数": "MATCH (n:Condition) RETURN count(n) AS count",
            "キーパーソン数": "MATCH (n:KeyPerson) RETURN count(n) AS count",
            "手帳・受給者証数": "MATCH (n:Certificate) RETURN count(n) AS count",
            "後見人数": "MATCH (n:Guardian) RETURN count(n) AS count",
            "生育歴エピソード数": "MATCH (n:LifeHistory) RETURN count(n) AS count",
            "願い数": "MATCH (n:Wish) RETURN count(n) AS count",
            "医療機関数": "MATCH (n:Hospital) RETURN count(n) AS count",
            "支援者数": "MATCH (n:Supporter) RETURN count(n) AS count",
            "支援記録数": "MATCH (n:SupportLog) RETURN count(n) AS count"
        }

        stats = {}
        with driver.session() as session:
            for label, query in queries.items():
                result = session.run(query)
                stats[label] = result.single()['count']

        return json.dumps({
            "📊 データベース統計": stats,
            "更新日時": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        log(f"統計取得エラー: {e}")
        return f"エラーが発生しました: {e}"


@mcp.tool()
def add_support_log(
    client_name: str,
    narrative_text: str
) -> str:
    """
    支援記録を物語風テキストから自動抽出して登録します。

    日常の支援内容を自由なテキストで記録し、AIが自動的に構造化データとして保存します。
    「今日〜した」「〜の対応で落ち着いた」などの表現から、支援記録を抽出します。

    Args:
        client_name: クライアント名
        narrative_text: 支援記録の物語風テキスト（例: 「今日、健太さんがパニックを起こしたので、静かに見守りました。5分で落ち着きました。」）

    Returns:
        登録結果のメッセージ

    使用例:
        - 「山田健太さんの支援記録を追加: 今日の訪問で、急な音に驚いてパニックになりました。テレビを消して静かにしたら、5分で落ち着きました。この対応は効果的でした。」
        - 「佐々木真理さんの記録: 後ろから声をかけたらパニックになった。次からは必ず視界に入ってから話しかけるようにします。」
    """
    try:
        log(f"支援記録追加: {client_name}")

        # AI抽出を使って構造化
        # 動的にプロジェクトルートをパスに追加（ハードコードを回避）
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from lib.ai_extractor import extract_from_text
        from lib.db_operations import register_to_database

        extracted_data = extract_from_text(narrative_text, client_name=client_name)

        if not extracted_data:
            return "❌ テキストからデータを抽出できませんでした。もう少し詳しく記述してください。"

        # データベースに登録
        register_to_database(extracted_data)

        # 登録内容をサマリー
        summary = []

        if extracted_data.get('supportLogs'):
            summary.append(f"✅ {len(extracted_data['supportLogs'])}件の支援記録を登録しました")

        if extracted_data.get('ngActions'):
            summary.append(f"⚠️ {len(extracted_data['ngActions'])}件の禁忌事項を抽出しました")

        if extracted_data.get('carePreferences'):
            summary.append(f"💡 {len(extracted_data['carePreferences'])}件の推奨ケアを抽出しました")

        return "\n".join(summary) if summary else "✅ データを登録しました"

    except Exception as e:
        log(f"支援記録追加エラー: {e}")
        return f"❌ エラーが発生しました: {e}"


@mcp.tool()
def get_support_logs(
    client_name: str,
    limit: int = 10
) -> str:
    """
    クライアントの支援記録履歴を取得します。

    過去の支援内容と効果を時系列で確認できます。
    効果的だった対応を参考にしたり、逆効果だった対応を避けるために使用します。

    Args:
        client_name: クライアント名
        limit: 取得件数（デフォルト: 10件、最大50件）

    Returns:
        支援記録の履歴（JSON形式）

    使用例:
        - 「山田健太さんの最近の支援記録を見せて」
        - 「佐々木真理さんの過去20件の支援記録」
    """
    try:
        log(f"支援記録取得: {client_name}, 件数: {limit}")

        # 上限設定
        limit = min(limit, 50)

        query = """
        MATCH (s:Supporter)-[:LOGGED]->(log:SupportLog)-[:ABOUT]->(c:Client)
        WHERE c.name CONTAINS $client_name
        RETURN log.date as 日付,
               s.name as 支援者,
               log.situation as 状況,
               log.action as 対応,
               log.effectiveness as 効果,
               log.note as メモ
        ORDER BY log.date DESC
        LIMIT $limit
        """

        with driver.session() as session:
            result = session.run(query, client_name=client_name, limit=limit)
            logs = [record.data() for record in result]

            if not logs:
                return f"'{client_name}' さんの支援記録が見つかりませんでした。"

            return json.dumps({
                "クライアント": client_name,
                "支援記録件数": len(logs),
                "履歴": logs
            }, ensure_ascii=False, indent=2, default=str)

    except Exception as e:
        log(f"支援記録取得エラー: {e}")
        return f"エラーが発生しました: {e}"


@mcp.tool()
def discover_care_patterns(
    client_name: str,
    min_frequency: int = 2
) -> str:
    """
    効果的だった支援パターンを発見します。

    複数回効果があった対応方法を自動検出し、ベストプラクティスとして提示します。
    経験知を蓄積し、新しい支援者への引き継ぎに活用できます。

    Args:
        client_name: クライアント名
        min_frequency: 最小出現回数（デフォルト: 2回以上）

    Returns:
        発見されたパターンのリスト（JSON形式）

    使用例:
        - 「山田健太さんの効果的なケアパターンを教えて」
        - 「佐々木真理さんで3回以上効果があった対応方法は？」
    """
    try:
        log(f"パターン発見: {client_name}, 最小頻度: {min_frequency}")

        query = """
        MATCH (c:Client)<-[:ABOUT]-(log:SupportLog)
        WHERE c.name CONTAINS $client_name
          AND log.effectiveness = 'Effective'
        WITH c, log.situation as situation, log.action as action, count(*) as frequency
        WHERE frequency >= $min_frequency
        RETURN situation as 状況,
               action as 対応方法,
               frequency as 効果的だった回数
        ORDER BY frequency DESC
        """

        with driver.session() as session:
            result = session.run(query, client_name=client_name, min_frequency=min_frequency)
            patterns = [record.data() for record in result]

            if not patterns:
                return f"'{client_name}' さんで{min_frequency}回以上効果的だったパターンは見つかりませんでした。"

            return json.dumps({
                "クライアント": client_name,
                "発見されたパターン数": len(patterns),
                "効果的なケアパターン": patterns,
                "💡 活用方法": "これらのパターンを新しい支援者への引き継ぎや、マニュアル作成に活用してください。"
            }, ensure_ascii=False, indent=2)

    except Exception as e:
        log(f"パターン発見エラー: {e}")
        return f"エラーが発生しました: {e}"


# =============================================================================
# メイン実行
# =============================================================================

if __name__ == "__main__":
    mcp.run()
