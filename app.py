"""
親亡き後支援データベース - フォーム登録システム（Streamlit UI）
Manifesto: Post-Parent Support & Advocacy Graph 準拠

Version: 2.0
4本柱すべてに対応したデータ登録インターフェース
"""

import streamlit as st
import os
from datetime import date, timedelta
from dotenv import load_dotenv
from neo4j import GraphDatabase

# --- 初期設定 ---
st.set_page_config(
    page_title="親亡き後支援DB 登録システム", 
    layout="wide",
    page_icon="🛡️"
)
load_dotenv()

# --- Neo4j接続 ---
@st.cache_resource
def get_driver():
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(uri, auth=(username, password))

driver = get_driver()

def run_query(query, params=None):
    """Cypherクエリ実行ヘルパー"""
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]

# =============================================================================
# サイドバー: データベース状況 & ナビゲーション
# =============================================================================

with st.sidebar:
    st.header("🛡️ 親亡き後支援DB")
    st.caption("マニフェスト v2.0 準拠")
    
    st.divider()
    
    # ナビゲーション
    page = st.radio(
        "📑 登録カテゴリを選択",
        [
            "👤 第1の柱: 本人性",
            "💊 第2の柱: ケアの暗黙知",
            "📜 第3の柱: 法的基盤",
            "🆘 第4の柱: 危機管理",
            "📊 データ確認"
        ],
        index=0
    )
    
    st.divider()
    
    # 統計表示
    st.subheader("📈 登録状況")
    if st.button("🔄 更新", use_container_width=True):
        st.rerun()
    
    try:
        stats = {
            "クライアント": run_query("MATCH (n:Client) RETURN count(n) as c")[0]['c'],
            "禁忌事項": run_query("MATCH (n:NgAction) RETURN count(n) as c")[0]['c'],
            "配慮事項": run_query("MATCH (n:CarePreference) RETURN count(n) as c")[0]['c'],
            "キーパーソン": run_query("MATCH (n:KeyPerson) RETURN count(n) as c")[0]['c'],
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("👤", stats["クライアント"])
            st.metric("🚫", stats["禁忌事項"])
        with col2:
            st.metric("✅", stats["配慮事項"])
            st.metric("📞", stats["キーパーソン"])
    except Exception as e:
        st.error(f"DB接続エラー")

# =============================================================================
# 共通: クライアント選択コンポーネント
# =============================================================================

def client_selector(key_prefix=""):
    """クライアント選択UIコンポーネント"""
    existing_clients = [r['name'] for r in run_query("MATCH (c:Client) RETURN c.name as name ORDER BY c.name")]
    
    client_mode = st.radio(
        "対象者", 
        ["既存クライアントを選択", "新規クライアントを登録"], 
        horizontal=True,
        key=f"{key_prefix}_mode"
    )
    
    if client_mode == "既存クライアントを選択":
        if existing_clients:
            return st.selectbox("クライアントを選択", existing_clients, key=f"{key_prefix}_select"), False
        else:
            st.warning("登録されているクライアントがいません。新規登録してください。")
            return None, False
    else:
        return st.text_input("新規クライアントの氏名", placeholder="例: 山田 健太", key=f"{key_prefix}_new"), True

# =============================================================================
# 第1の柱: 本人性 (Identity & Narrative)
# =============================================================================

def page_pillar1():
    st.title("👤 第1の柱: 本人性 (Identity & Narrative)")
    st.markdown("「その人は誰か」を定義します。属性だけでなく、人生の物語を含みます。")
    
    tab1, tab2, tab3 = st.tabs(["🆔 基本情報", "📖 生育歴", "💭 願い"])
    
    # --- 基本情報タブ ---
    with tab1:
        st.subheader("🆔 クライアント基本情報の登録")
        
        with st.form("client_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("氏名 *", placeholder="山田 健太")
                dob = st.date_input("生年月日", value=date(1990, 1, 1), min_value=date(1920, 1, 1))
            
            with col2:
                blood_type = st.selectbox("血液型", ["不明", "A型", "B型", "O型", "AB型"])
                client_id = st.text_input("管理ID（任意）", placeholder="KK-001")
            
            submitted = st.form_submit_button("登録する", use_container_width=True)
            
            if submitted:
                if not name:
                    st.error("氏名は必須です")
                else:
                    try:
                        run_query("""
                            MERGE (c:Client {name: $name})
                            SET c.dob = date($dob),
                                c.bloodType = $blood,
                                c.clientId = $cid
                        """, {
                            "name": name,
                            "dob": dob.isoformat(),
                            "blood": blood_type if blood_type != "不明" else None,
                            "cid": client_id if client_id else None
                        })
                        st.success(f"✅ {name}さんを登録しました")
                        st.balloons()
                    except Exception as e:
                        st.error(f"登録エラー: {e}")
    
    # --- 生育歴タブ ---
    with tab2:
        st.subheader("📖 生育歴・エピソードの登録")
        
        client_name, is_new = client_selector("history")
        
        if client_name:
            with st.form("history_form"):
                era = st.selectbox("時期", ["幼少期", "学齢期", "青年期", "成人後", "その他"])
                if era == "その他":
                    era = st.text_input("時期を入力", placeholder="例: 転居後")
                
                episode = st.text_area("エピソード *", placeholder="どんな出来事があったか、何が好きだったか等")
                emotion = st.text_input("その時の感情・反応（任意）", placeholder="例: 自信を持てるようになった")
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    if not episode:
                        st.error("エピソードは必須です")
                    else:
                        try:
                            run_query("""
                                MERGE (c:Client {name: $name})
                                CREATE (h:LifeHistory {era: $era, episode: $episode, emotion: $emotion})
                                CREATE (c)-[:HAS_HISTORY]->(h)
                            """, {"name": client_name, "era": era, "episode": episode, "emotion": emotion or None})
                            st.success("✅ 生育歴を登録しました")
                        except Exception as e:
                            st.error(f"登録エラー: {e}")
    
    # --- 願いタブ ---
    with tab3:
        st.subheader("💭 本人・家族の願いの登録")
        
        client_name, is_new = client_selector("wish")
        
        if client_name:
            with st.form("wish_form"):
                content = st.text_area("願いの内容 *", placeholder="例: 今のグループホームで穏やかに暮らし続けたい")
                wish_date = st.date_input("記録日", value=date.today())
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    if not content:
                        st.error("願いの内容は必須です")
                    else:
                        try:
                            run_query("""
                                MERGE (c:Client {name: $name})
                                CREATE (w:Wish {content: $content, status: 'Active', date: date($date)})
                                CREATE (c)-[:HAS_WISH]->(w)
                            """, {"name": client_name, "content": content, "date": wish_date.isoformat()})
                            st.success("✅ 願いを登録しました")
                        except Exception as e:
                            st.error(f"登録エラー: {e}")

# =============================================================================
# 第2の柱: ケアの暗黙知 (Care Instructions)
# =============================================================================

def page_pillar2():
    st.title("💊 第2の柱: ケアの暗黙知 (Care Instructions)")
    st.markdown("「どう接すべきか」を定義します。親の頭の中にあったマニュアルを形式知化します。")
    
    tab1, tab2, tab3 = st.tabs(["🏥 特性・診断", "🚫 禁忌事項", "✅ 推奨ケア"])
    
    # --- 特性・診断タブ ---
    with tab1:
        st.subheader("🏥 特性・医学的診断の登録")
        
        client_name, is_new = client_selector("condition")
        
        if client_name:
            with st.form("condition_form"):
                cond_name = st.text_input("特性・診断名 *", placeholder="例: 自閉スペクトラム症、聴覚過敏")
                diagnosis_date = st.date_input("診断日（任意）", value=None)
                status = st.selectbox("状態", ["Active（現在も該当）", "Resolved（解消・改善）"])
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    if not cond_name:
                        st.error("特性・診断名は必須です")
                    else:
                        try:
                            run_query("""
                                MERGE (c:Client {name: $name})
                                MERGE (con:Condition {name: $cond_name})
                                SET con.status = $status,
                                    con.diagnosisDate = CASE WHEN $diag_date IS NOT NULL THEN date($diag_date) ELSE NULL END
                                MERGE (c)-[:HAS_CONDITION]->(con)
                            """, {
                                "name": client_name,
                                "cond_name": cond_name,
                                "status": "Active" if "Active" in status else "Resolved",
                                "diag_date": diagnosis_date.isoformat() if diagnosis_date else None
                            })
                            st.success("✅ 特性・診断を登録しました")
                        except Exception as e:
                            st.error(f"登録エラー: {e}")
    
    # --- 禁忌事項タブ ---
    with tab2:
        st.subheader("🚫 禁忌事項（NgAction）の登録")
        st.error("⚠️ **最重要**: 絶対にしてはいけないことを登録します")
        
        client_name, is_new = client_selector("ng")
        
        if client_name:
            # 関連する特性を取得
            conditions = [r['name'] for r in run_query("""
                MATCH (c:Client {name: $name})-[:HAS_CONDITION]->(con:Condition)
                RETURN con.name as name
            """, {"name": client_name})]
            
            with st.form("ng_form"):
                action = st.text_area("禁忌行動 *", placeholder="例: 後ろから急に声をかける、食事中にテレビをつける")
                reason = st.text_area("理由（なぜ危険か）*", placeholder="例: パニックを誘発し、自傷行為につながる")
                
                risk_level = st.selectbox(
                    "リスクレベル *",
                    ["Panic（パニック誘発）", "LifeThreatening（命に関わる）", "Discomfort（不快・ストレス）"]
                )
                
                if conditions:
                    related_condition = st.selectbox("関連する特性（任意）", ["なし"] + conditions)
                else:
                    related_condition = "なし"
                    st.info("特性が登録されていません。先に「特性・診断」タブで登録することをお勧めします。")
                
                submitted = st.form_submit_button("🚫 禁忌事項を登録", use_container_width=True, type="primary")
                
                if submitted:
                    if not action or not reason:
                        st.error("禁忌行動と理由は必須です")
                    else:
                        try:
                            # リスクレベルを抽出
                            risk = risk_level.split("（")[0]
                            
                            run_query("""
                                MERGE (c:Client {name: $name})
                                CREATE (ng:NgAction {action: $action, reason: $reason, riskLevel: $risk})
                                CREATE (c)-[:MUST_AVOID]->(ng)
                            """, {"name": client_name, "action": action, "reason": reason, "risk": risk})
                            
                            # 関連特性があれば紐付け
                            if related_condition != "なし":
                                run_query("""
                                    MATCH (ng:NgAction {action: $action})
                                    MATCH (con:Condition {name: $cond})
                                    MERGE (ng)-[:IN_CONTEXT]->(con)
                                """, {"action": action, "cond": related_condition})
                            
                            st.success("✅ 禁忌事項を登録しました")
                            st.balloons()
                        except Exception as e:
                            st.error(f"登録エラー: {e}")
    
    # --- 推奨ケアタブ ---
    with tab3:
        st.subheader("✅ 推奨ケア（CarePreference）の登録")
        st.success("💡 「こうすると落ち着く」「こうしてほしい」を登録します")
        
        client_name, is_new = client_selector("care")
        
        if client_name:
            conditions = [r['name'] for r in run_query("""
                MATCH (c:Client {name: $name})-[:HAS_CONDITION]->(con:Condition)
                RETURN con.name as name
            """, {"name": client_name})]
            
            with st.form("care_form"):
                category = st.selectbox(
                    "カテゴリ *",
                    ["食事", "入浴", "睡眠", "移動", "パニック時", "服薬", "コミュニケーション", "その他"]
                )
                if category == "その他":
                    category = st.text_input("カテゴリを入力")
                
                instruction = st.text_area("具体的な手順・方法 *", placeholder="例: 静かな部屋に移動し、背中をゆっくりさする。5分ほど待つと落ち着く。")
                priority = st.selectbox("優先度", ["High（必ず守る）", "Medium（推奨）", "Low（参考）"])
                
                if conditions:
                    related_condition = st.selectbox("対応する特性（任意）", ["なし"] + conditions)
                else:
                    related_condition = "なし"
                
                submitted = st.form_submit_button("✅ 推奨ケアを登録", use_container_width=True, type="primary")
                
                if submitted:
                    if not instruction:
                        st.error("具体的な手順・方法は必須です")
                    else:
                        try:
                            pri = priority.split("（")[0]
                            
                            run_query("""
                                MERGE (c:Client {name: $name})
                                CREATE (cp:CarePreference {category: $cat, instruction: $inst, priority: $pri})
                                CREATE (c)-[:REQUIRES]->(cp)
                            """, {"name": client_name, "cat": category, "inst": instruction, "pri": pri})
                            
                            if related_condition != "なし":
                                run_query("""
                                    MATCH (cp:CarePreference {instruction: $inst})
                                    MATCH (con:Condition {name: $cond})
                                    MERGE (cp)-[:ADDRESSES]->(con)
                                """, {"inst": instruction, "cond": related_condition})
                            
                            st.success("✅ 推奨ケアを登録しました")
                        except Exception as e:
                            st.error(f"登録エラー: {e}")

# =============================================================================
# 第3の柱: 法的基盤 (Legal Basis)
# =============================================================================

def page_pillar3():
    st.title("📜 第3の柱: 法的基盤 (Legal Basis)")
    st.markdown("「何の権利があるか」を定義します。支援を受けるための資格と行政の決定。")
    
    tab1, tab2, tab3 = st.tabs(["🎫 手帳・受給者証", "💰 公的扶助", "🏛️ 関係機関"])
    
    # --- 手帳・受給者証タブ ---
    with tab1:
        st.subheader("🎫 手帳・受給者証の登録")
        st.warning("📅 **更新期限の管理は権利擁護の基本です**")
        
        client_name, is_new = client_selector("cert")
        
        if client_name:
            with st.form("cert_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    cert_type = st.selectbox(
                        "証明書の種類 *",
                        ["療育手帳", "精神障害者保健福祉手帳", "身体障害者手帳", 
                         "障害福祉サービス受給者証", "自立支援医療受給者証", "その他"]
                    )
                    if cert_type == "その他":
                        cert_type = st.text_input("証明書名を入力")
                    
                    grade = st.text_input("等級・区分", placeholder="例: A1, 2級, 区分5")
                
                with col2:
                    issue_date = st.date_input("交付日", value=None)
                    renewal_date = st.date_input("次回更新日 *", value=date.today() + timedelta(days=365))
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    try:
                        run_query("""
                            MERGE (c:Client {name: $name})
                            CREATE (cert:Certificate {
                                type: $type,
                                grade: $grade,
                                issueDate: CASE WHEN $issue IS NOT NULL THEN date($issue) ELSE NULL END,
                                nextRenewalDate: date($renewal)
                            })
                            CREATE (c)-[:HAS_CERTIFICATE]->(cert)
                        """, {
                            "name": client_name,
                            "type": cert_type,
                            "grade": grade or None,
                            "issue": issue_date.isoformat() if issue_date else None,
                            "renewal": renewal_date.isoformat()
                        })
                        st.success("✅ 手帳・受給者証を登録しました")
                    except Exception as e:
                        st.error(f"登録エラー: {e}")
    
    # --- 公的扶助タブ ---
    with tab2:
        st.subheader("💰 公的扶助・給付の登録")
        
        client_name, is_new = client_selector("assist")
        
        if client_name:
            with st.form("assist_form"):
                assist_type = st.selectbox(
                    "扶助の種類 *",
                    ["障害基礎年金", "障害厚生年金", "特別障害者手当", "生活保護", 
                     "重度心身障害者医療費助成", "その他"]
                )
                if assist_type == "その他":
                    assist_type = st.text_input("扶助名を入力")
                
                grade = st.text_input("等級（該当する場合）", placeholder="例: 1級, 2級")
                start_date = st.date_input("開始日", value=None)
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    try:
                        run_query("""
                            MERGE (c:Client {name: $name})
                            CREATE (pa:PublicAssistance {
                                type: $type,
                                grade: $grade,
                                startDate: CASE WHEN $start IS NOT NULL THEN date($start) ELSE NULL END
                            })
                            CREATE (c)-[:RECEIVES]->(pa)
                        """, {
                            "name": client_name,
                            "type": assist_type,
                            "grade": grade or None,
                            "start": start_date.isoformat() if start_date else None
                        })
                        st.success("✅ 公的扶助を登録しました")
                    except Exception as e:
                        st.error(f"登録エラー: {e}")
    
    # --- 関係機関タブ ---
    with tab3:
        st.subheader("🏛️ 関係機関の登録")
        
        client_name, is_new = client_selector("org")
        
        if client_name:
            with st.form("org_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    org_name = st.text_input("機関名 *", placeholder="例: 北九州市 八幡東区役所 保健福祉課")
                    org_type = st.selectbox("種別", ["行政", "福祉", "医療", "教育", "その他"])
                
                with col2:
                    contact = st.text_input("連絡先", placeholder="電話番号")
                    address = st.text_input("住所", placeholder="住所")
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    if not org_name:
                        st.error("機関名は必須です")
                    else:
                        try:
                            run_query("""
                                MERGE (c:Client {name: $name})
                                MERGE (org:Organization {name: $org_name})
                                SET org.type = $type, org.contact = $contact, org.address = $address
                                MERGE (c)-[:REGISTERED_AT]->(org)
                            """, {
                                "name": client_name,
                                "org_name": org_name,
                                "type": org_type,
                                "contact": contact or None,
                                "address": address or None
                            })
                            st.success("✅ 関係機関を登録しました")
                        except Exception as e:
                            st.error(f"登録エラー: {e}")

# =============================================================================
# 第4の柱: 危機管理ネットワーク (Safety Net)
# =============================================================================

def page_pillar4():
    st.title("🆘 第4の柱: 危機管理ネットワーク (Safety Net)")
    st.markdown("「誰が守るか」を定義します。緊急時の指揮命令系統と法的権限。")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📞 キーパーソン", "⚖️ 後見人等", "👥 支援者", "🏥 医療機関"])
    
    # --- キーパーソンタブ ---
    with tab1:
        st.subheader("📞 キーパーソン（緊急連絡先）の登録")
        st.info("🔢 **rank（優先順位）**: 1が最優先です。緊急時、この順番で連絡します。")
        
        client_name, is_new = client_selector("kp")
        
        if client_name:
            # 現在のキーパーソン一覧を表示
            existing_kp = run_query("""
                MATCH (c:Client {name: $name})-[r:HAS_KEY_PERSON]->(kp:KeyPerson)
                RETURN kp.name as 氏名, kp.relationship as 続柄, r.rank as 順位, kp.phone as 電話
                ORDER BY r.rank
            """, {"name": client_name})
            
            if existing_kp:
                st.markdown("**現在の登録:**")
                st.dataframe(existing_kp, use_container_width=True)
            
            with st.form("kp_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    kp_name = st.text_input("氏名 *", placeholder="山田 花子")
                    relationship = st.text_input("続柄 *", placeholder="例: 母, 叔父, 姉")
                    rank = st.number_input("優先順位 *", min_value=1, max_value=10, value=len(existing_kp) + 1)
                
                with col2:
                    phone = st.text_input("電話番号 *", placeholder="090-1234-5678")
                    role = st.multiselect(
                        "役割",
                        ["緊急連絡先", "医療同意", "金銭管理", "日常連絡"],
                        default=["緊急連絡先"]
                    )
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    if not kp_name or not relationship or not phone:
                        st.error("氏名、続柄、電話番号は必須です")
                    else:
                        try:
                            run_query("""
                                MERGE (c:Client {name: $client})
                                MERGE (kp:KeyPerson {name: $kp_name, phone: $phone})
                                SET kp.relationship = $rel, kp.role = $role
                                MERGE (c)-[r:HAS_KEY_PERSON]->(kp)
                                SET r.rank = $rank
                            """, {
                                "client": client_name,
                                "kp_name": kp_name,
                                "phone": phone,
                                "rel": relationship,
                                "role": "・".join(role),
                                "rank": rank
                            })
                            st.success("✅ キーパーソンを登録しました")
                            st.rerun()
                        except Exception as e:
                            st.error(f"登録エラー: {e}")
    
    # --- 後見人等タブ ---
    with tab2:
        st.subheader("⚖️ 成年後見人等の登録")
        
        client_name, is_new = client_selector("guardian")
        
        if client_name:
            with st.form("guardian_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    g_name = st.text_input("氏名または法人名 *", placeholder="例: 社会福祉法人 ○○会")
                    g_type = st.selectbox("種別 *", ["成年後見", "保佐", "補助", "任意後見", "未定（予定）"])
                
                with col2:
                    g_phone = st.text_input("連絡先", placeholder="電話番号")
                    g_org = st.text_input("所属（法人の場合）", placeholder="例: 権利擁護センター")
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    if not g_name:
                        st.error("氏名または法人名は必須です")
                    else:
                        try:
                            run_query("""
                                MERGE (c:Client {name: $client})
                                CREATE (g:Guardian {
                                    name: $name,
                                    type: $type,
                                    phone: $phone,
                                    organization: $org
                                })
                                CREATE (c)-[:HAS_LEGAL_REP]->(g)
                            """, {
                                "client": client_name,
                                "name": g_name,
                                "type": g_type,
                                "phone": g_phone or None,
                                "org": g_org or None
                            })
                            st.success("✅ 後見人等を登録しました")
                        except Exception as e:
                            st.error(f"登録エラー: {e}")
    
    # --- 支援者タブ ---
    with tab3:
        st.subheader("👥 支援者の登録")
        
        client_name, is_new = client_selector("supporter")
        
        if client_name:
            with st.form("supporter_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    s_name = st.text_input("氏名 *", placeholder="鈴木 太郎")
                    s_role = st.selectbox(
                        "役割 *",
                        ["相談支援専門員", "サービス管理責任者", "生活支援員", 
                         "ヘルパー", "看護師", "その他"]
                    )
                    if s_role == "その他":
                        s_role = st.text_input("役割を入力")
                
                with col2:
                    s_org = st.text_input("所属事業所 *", placeholder="例: 相談支援事業所 あおぞら")
                    s_phone = st.text_input("連絡先", placeholder="電話番号")
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    if not s_name or not s_org:
                        st.error("氏名と所属事業所は必須です")
                    else:
                        try:
                            run_query("""
                                MERGE (c:Client {name: $client})
                                CREATE (s:Supporter {
                                    name: $name,
                                    role: $role,
                                    organization: $org,
                                    phone: $phone
                                })
                                CREATE (c)-[:SUPPORTED_BY]->(s)
                            """, {
                                "client": client_name,
                                "name": s_name,
                                "role": s_role,
                                "org": s_org,
                                "phone": s_phone or None
                            })
                            st.success("✅ 支援者を登録しました")
                        except Exception as e:
                            st.error(f"登録エラー: {e}")
    
    # --- 医療機関タブ ---
    with tab4:
        st.subheader("🏥 医療機関（かかりつけ医）の登録")
        
        client_name, is_new = client_selector("hospital")
        
        if client_name:
            with st.form("hospital_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    h_name = st.text_input("病院名 *", placeholder="例: 産業医科大学病院")
                    specialty = st.text_input("診療科・専門 *", placeholder="例: 精神科、内科")
                    doctor = st.text_input("担当医名（任意）", placeholder="例: 中村医師")
                
                with col2:
                    h_phone = st.text_input("電話番号 *", placeholder="093-XXX-XXXX")
                    h_address = st.text_input("住所", placeholder="北九州市○○区...")
                
                submitted = st.form_submit_button("登録する", use_container_width=True)
                
                if submitted:
                    if not h_name or not specialty or not h_phone:
                        st.error("病院名、診療科、電話番号は必須です")
                    else:
                        try:
                            run_query("""
                                MERGE (c:Client {name: $client})
                                MERGE (h:Hospital {name: $name, phone: $phone})
                                SET h.specialty = $specialty, h.address = $address, h.doctor = $doctor
                                MERGE (c)-[:TREATED_AT]->(h)
                            """, {
                                "client": client_name,
                                "name": h_name,
                                "phone": h_phone,
                                "specialty": specialty,
                                "address": h_address or None,
                                "doctor": doctor or None
                            })
                            st.success("✅ 医療機関を登録しました")
                        except Exception as e:
                            st.error(f"登録エラー: {e}")

# =============================================================================
# データ確認ページ
# =============================================================================

def page_data_view():
    st.title("📊 登録データの確認")
    
    # クライアント選択
    clients = [r['name'] for r in run_query("MATCH (c:Client) RETURN c.name as name ORDER BY c.name")]
    
    if not clients:
        st.info("登録されているクライアントがいません")
        return
    
    selected = st.selectbox("クライアントを選択", clients)
    
    if selected:
        st.divider()
        
        # 4本柱のタブ
        tab1, tab2, tab3, tab4 = st.tabs([
            "👤 本人性", "💊 ケアの暗黙知", "📜 法的基盤", "🆘 危機管理"
        ])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**基本情報**")
                basic = run_query("""
                    MATCH (c:Client {name: $name})
                    RETURN c.name as 氏名, c.dob as 生年月日, c.bloodType as 血液型
                """, {"name": selected})
                if basic:
                    st.dataframe(basic, use_container_width=True)
                
                st.markdown("**生育歴**")
                history = run_query("""
                    MATCH (c:Client {name: $name})-[:HAS_HISTORY]->(h:LifeHistory)
                    RETURN h.era as 時期, h.episode as エピソード
                """, {"name": selected})
                if history:
                    st.dataframe(history, use_container_width=True)
            
            with col2:
                st.markdown("**願い**")
                wishes = run_query("""
                    MATCH (c:Client {name: $name})-[:HAS_WISH]->(w:Wish)
                    WHERE w.status = 'Active'
                    RETURN w.content as 内容, w.date as 記録日
                """, {"name": selected})
                if wishes:
                    st.dataframe(wishes, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🚫 禁忌事項**")
                ng = run_query("""
                    MATCH (c:Client {name: $name})-[:MUST_AVOID]->(ng:NgAction)
                    RETURN ng.action as 禁忌, ng.reason as 理由, ng.riskLevel as リスク
                """, {"name": selected})
                if ng:
                    st.dataframe(ng, use_container_width=True)
                else:
                    st.info("登録なし")
            
            with col2:
                st.markdown("**✅ 推奨ケア**")
                care = run_query("""
                    MATCH (c:Client {name: $name})-[:REQUIRES]->(cp:CarePreference)
                    RETURN cp.category as カテゴリ, cp.instruction as 内容, cp.priority as 優先度
                """, {"name": selected})
                if care:
                    st.dataframe(care, use_container_width=True)
                else:
                    st.info("登録なし")
            
            st.markdown("**特性・診断**")
            cond = run_query("""
                MATCH (c:Client {name: $name})-[:HAS_CONDITION]->(con:Condition)
                RETURN con.name as 特性, con.status as 状態
            """, {"name": selected})
            if cond:
                st.dataframe(cond, use_container_width=True)
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎫 手帳・受給者証**")
                cert = run_query("""
                    MATCH (c:Client {name: $name})-[:HAS_CERTIFICATE]->(cert:Certificate)
                    RETURN cert.type as 種類, cert.grade as 等級, cert.nextRenewalDate as 更新期限
                """, {"name": selected})
                if cert:
                    st.dataframe(cert, use_container_width=True)
                else:
                    st.info("登録なし")
            
            with col2:
                st.markdown("**💰 公的扶助**")
                assist = run_query("""
                    MATCH (c:Client {name: $name})-[:RECEIVES]->(pa:PublicAssistance)
                    RETURN pa.type as 種類, pa.grade as 等級
                """, {"name": selected})
                if assist:
                    st.dataframe(assist, use_container_width=True)
                else:
                    st.info("登録なし")
        
        with tab4:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📞 キーパーソン**")
                kp = run_query("""
                    MATCH (c:Client {name: $name})-[r:HAS_KEY_PERSON]->(kp:KeyPerson)
                    RETURN r.rank as 順位, kp.name as 氏名, kp.relationship as 続柄, kp.phone as 電話
                    ORDER BY r.rank
                """, {"name": selected})
                if kp:
                    st.dataframe(kp, use_container_width=True)
                else:
                    st.info("登録なし")
                
                st.markdown("**⚖️ 後見人等**")
                guardian = run_query("""
                    MATCH (c:Client {name: $name})-[:HAS_LEGAL_REP]->(g:Guardian)
                    RETURN g.name as 氏名, g.type as 種別, g.phone as 連絡先
                """, {"name": selected})
                if guardian:
                    st.dataframe(guardian, use_container_width=True)
                else:
                    st.info("登録なし")
            
            with col2:
                st.markdown("**🏥 医療機関**")
                hosp = run_query("""
                    MATCH (c:Client {name: $name})-[:TREATED_AT]->(h:Hospital)
                    RETURN h.name as 病院, h.specialty as 診療科, h.phone as 電話, h.doctor as 担当医
                """, {"name": selected})
                if hosp:
                    st.dataframe(hosp, use_container_width=True)
                else:
                    st.info("登録なし")
                
                st.markdown("**👥 支援者**")
                supp = run_query("""
                    MATCH (c:Client {name: $name})-[:SUPPORTED_BY]->(s:Supporter)
                    RETURN s.name as 氏名, s.role as 役割, s.organization as 所属
                """, {"name": selected})
                if supp:
                    st.dataframe(supp, use_container_width=True)
                else:
                    st.info("登録なし")

# =============================================================================
# メイン: ページルーティング
# =============================================================================

if "第1の柱" in page:
    page_pillar1()
elif "第2の柱" in page:
    page_pillar2()
elif "第3の柱" in page:
    page_pillar3()
elif "第4の柱" in page:
    page_pillar4()
elif "データ確認" in page:
    page_data_view()
