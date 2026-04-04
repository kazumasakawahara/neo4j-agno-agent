"""
親亡き後支援データベース - ナラティブ・アーカイブ
Manifesto: Post-Parent Support & Advocacy Graph 準拠

Version: 4.0
- モジュール分割による軽量化
- ファイルアップロード機能追加（Word/Excel/PDF/TXT対応）
"""

import streamlit as st
import json
from datetime import date

# --- ライブラリからインポート ---
from lib.db_new_operations import run_query, register_to_database, get_clients_list, get_client_stats, get_support_logs, discover_care_patterns
from lib.ai_extractor import extract_from_text, check_safety_compliance, graph_to_tree, tree_to_graph
from lib.utils import safe_date_parse, init_session_state, reset_session_state, get_input_example
from lib.file_readers import read_uploaded_file, get_supported_extensions, check_dependencies
from skills.report_generator.excel_exporter import export_client_data_to_excel
from skills.report_generator.pdf_exporter import generate_emergency_sheet_pdf
import os

# --- 初期設定 ---
# Page Config handled by app.py
# st.set_page_config(...) commented out for unified navigation

init_session_state()

# =============================================================================
# サイドバー
# =============================================================================

with st.sidebar:
    st.header("📖 親亡き後支援DB")
    st.caption("ナラティブ・アーカイブ v4.0")
    
    st.divider()
    
    # 現在のステップ表示
    steps = {
        'input': '1️⃣ データ入力',
        'edit': '2️⃣ 確認・修正',
        'confirm': '3️⃣ 最終確認',
        'done': '✅ 完了'
    }
    
    st.subheader("📍 現在のステップ")
    for key, label in steps.items():
        if key == st.session_state.step:
            st.markdown(
                f'<div style="background-color: #1E3A5F; padding: 8px 12px; border-radius: 8px; '
                f'border-left: 4px solid #4DA6FF; margin: 4px 0;">'
                f'<strong style="color: #4DA6FF;">→ {label}</strong></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"<span style='color: #888;'>　{label}</span>", unsafe_allow_html=True)
    
    st.divider()
    
    # 統計表示
    st.subheader("📊 登録状況")
    try:
        stats = get_client_stats()
        st.metric(label="👤 クライアント数", value=stats['client_count'])
        
        if stats['ng_by_client']:
            st.markdown("**🚫 禁忌事項**")
            for row in stats['ng_by_client']:
                if row['ng_count'] > 0:
                    st.markdown(f"　・{row['name']}: **{row['ng_count']}件**")
                else:
                    st.markdown(f"　・{row['name']}: 0件")
    except Exception as e:
        st.warning("データベース未接続（AI構造化は利用できます）")
    
    st.divider()
    
    # リセットボタン
    if st.button("🔄 最初からやり直す", use_container_width=True):
        reset_session_state()
        st.rerun()

# =============================================================================
# Step 1: データ入力（テキスト or ファイル）
# =============================================================================

def render_input_step():
    st.title("📖 データを入力")
    st.markdown("""
    **親御さんへのヒアリング内容、支援記録、相談メモ**などを入力してください。  
    AIが自動的に必要な情報を抽出・構造化します。
    """)
    
    # 既存クライアント選択
    existing_clients = get_clients_list()
    append_mode = st.checkbox("既存クライアントに追記する")
    selected_client = None
    
    if append_mode and existing_clients:
        selected_client = st.selectbox("クライアントを選択", existing_clients)
    
    # 入力方式の選択
    st.subheader("📝 入力方式を選択")
    input_method = st.radio(
        "入力方式",
        ["✍️ テキスト入力", "📁 ファイルアップロード"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    input_text = ""
    
    # --- テキスト入力 ---
    if input_method == "✍️ テキスト入力":
        with st.expander("💡 入力例を見る"):
            st.code(get_input_example(), language=None)
        
        input_text = st.text_area(
            "ここに文章を入力してください",
            height=400,
            value=st.session_state.narrative_text,
            placeholder="親御さんからの聞き取り内容、支援記録などを自由に記述..."
        )
        st.session_state.narrative_text = input_text
    
    # --- ファイルアップロード ---
    else:
        # 対応形式の説明
        extensions = get_supported_extensions()
        ext_list = ', '.join([f"{v}({k})" for k, v in extensions.items()])
        st.info(f"📂 対応形式: {ext_list}")
        
        # 依存関係チェック
        deps = check_dependencies()
        missing = [k for k, v in deps.items() if not v]
        if missing:
            st.warning(f"⚠️ 一部のライブラリがインストールされていません: {', '.join(missing)}\n"
                      f"ターミナルで `uv add {' '.join(missing)}` を実行してください。")
        
        uploaded_file = st.file_uploader(
            "ファイルをアップロード",
            type=['docx', 'xlsx', 'pdf', 'txt'],
            help="Word、Excel、PDF、テキストファイルに対応"
        )
        
        if uploaded_file:
            with st.spinner(f"📄 {uploaded_file.name} を読み込み中..."):
                try:
                    input_text = read_uploaded_file(uploaded_file)
                    st.session_state.uploaded_file_text = input_text
                    
                    st.success(f"✅ {uploaded_file.name} を読み込みました（{len(input_text):,}文字）")
                    
                    with st.expander("📄 抽出されたテキストを確認", expanded=False):
                        st.text_area("抽出内容", value=input_text, height=300, disabled=True)
                        
                except ImportError as e:
                    st.error(f"❌ ライブラリエラー: {e}")
                except ValueError as e:
                    st.error(f"❌ 読み込みエラー: {e}")
        else:
            input_text = st.session_state.uploaded_file_text
    
    # AI構造化ボタン
    st.divider()
    
    if st.button("🧠 AIで構造化する", type="primary", use_container_width=True, disabled=not input_text):
        with st.spinner("テキストを分析中..."):
            extracted = extract_from_text(input_text, selected_client)
            
            if extracted:
                # グラフ形式をツリー形式に変換（UI編集用）
                st.session_state.extracted_graph = extracted  # グラフ形式を保持
                tree_data = graph_to_tree(extracted)
                st.session_state.extracted_data = tree_data
                st.session_state.edited_data = json.loads(json.dumps(tree_data))

                # --- Safety Check (Rule 1) ---
                client_name = tree_data.get('client', {}).get('name')
                st.session_state.safety_warning = None # Reset
                
                if client_name:
                    try:
                        # Fetch NgActions
                        ng_results = run_query("""
                            MATCH (c:Client {name: $name})-[:MUST_AVOID]->(ng:NgAction)
                            RETURN ng.action as action, ng.riskLevel as riskLevel
                        """, {"name": client_name})
                        
                        # Check compliance
                        check_result = check_safety_compliance(input_text, ng_results)
                        if check_result.get("is_violation"):
                            st.session_state.safety_warning = check_result.get('warning')
                    except Exception as e:
                        print(f"Safety check error: {e}")
                # -----------------------------

                st.session_state.step = 'edit'
                st.rerun()
            else:
                st.error("データの抽出に失敗しました。もう一度お試しください。")

# =============================================================================
# Step 2: 確認・修正
# =============================================================================

def render_edit_step():
    st.title("✏️ 抽出データの確認・修正")
    st.markdown("AIが抽出した内容を確認し、必要に応じて修正してください。**特に日付・電話番号・等級は正確に確認してください。**")
    
    if not st.session_state.edited_data:
        st.error("データがありません")
        return
    
    # --- Safety Warning Display ---
    if st.session_state.get('safety_warning'):
        st.error(f"⚠️ **安全性警告**: {st.session_state.safety_warning}")
        st.markdown("---")
    # ------------------------------
    
    data = st.session_state.edited_data
    
    # タブで4本柱を表示
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 本人性", "💊 ケアの暗黙知", "📜 法的基盤", "🆘 危機管理"
    ])
    
    # --- 第1の柱: 本人性 ---
    with tab1:
        st.subheader("👤 基本情報")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            data['client']['name'] = st.text_input(
                "氏名 *", 
                value=data.get('client', {}).get('name', ''),
                key="client_name"
            )
            data['client']['kana'] = st.text_input(
                "ふりがな", 
                value=data.get('client', {}).get('kana', ''),
                placeholder="例: やまだけんた",
                key="client_kana"
            )
            
            # Aliases Input
            aliases_str = st.text_input(
                "通称・表記揺れ (カンマ区切り)",
                value=", ".join(data.get('client', {}).get('aliases', [])),
                placeholder="例: 佐々木まり, まりちゃん",
                key="client_aliases"
            )
            data['client']['aliases'] = [a.strip() for a in aliases_str.split(',') if a.strip()]
        with col2:
            dob_value = safe_date_parse(data.get('client', {}).get('dob'))
            dob = st.date_input(
                "生年月日",
                value=dob_value,
                min_value=date(1920, 1, 1),
                max_value=date.today(),
                key="client_dob"
            )
            data['client']['dob'] = dob.isoformat() if dob else None
        with col3:
            blood_options = ["不明", "A型", "B型", "O型", "AB型"]
            current_blood = data.get('client', {}).get('bloodType', '不明')
            if current_blood not in blood_options:
                current_blood = "不明"
            blood = st.selectbox("血液型", blood_options, index=blood_options.index(current_blood), key="client_blood")
            data['client']['bloodType'] = blood if blood != "不明" else None
        
        # 生育歴
        st.subheader("📖 生育歴")
        histories = data.get('lifeHistories', [])
        
        for i, hist in enumerate(histories):
            with st.expander(f"エピソード {i+1}: {hist.get('era', '時期不明')}", expanded=True):
                col1, col2 = st.columns([1, 3])
                with col1:
                    era_options = ["幼少期", "学齢期", "青年期", "成人後", "その他"]
                    current_era = hist.get('era', 'その他')
                    if current_era not in era_options:
                        era_options.append(current_era)
                    hist['era'] = st.selectbox("時期", era_options, index=era_options.index(current_era), key=f"hist_era_{i}")
                with col2:
                    hist['episode'] = st.text_area("エピソード", value=hist.get('episode', ''), key=f"hist_ep_{i}")
        
        if st.button("➕ 生育歴を追加", key="add_history"):
            data.setdefault('lifeHistories', []).append({'era': '', 'episode': '', 'emotion': ''})
            st.rerun()
        
        # 願い
        st.subheader("💭 願い")
        wishes = data.get('wishes', [])
        
        for i, wish in enumerate(wishes):
            col1, col2 = st.columns([3, 1])
            with col1:
                wish['content'] = st.text_input(f"願い {i+1}", value=wish.get('content', ''), key=f"wish_{i}")
            with col2:
                wish_date = safe_date_parse(wish.get('date')) or date.today()
                wish['date'] = st.date_input("記録日", value=wish_date, key=f"wish_date_{i}").isoformat()
        
        if st.button("➕ 願いを追加", key="add_wish"):
            data.setdefault('wishes', []).append({'content': '', 'date': date.today().isoformat()})
            st.rerun()
    
    # --- 第2の柱: ケアの暗黙知 ---
    with tab2:
        st.subheader("🏥 特性・診断")
        conditions = data.get('conditions', [])
        
        for i, cond in enumerate(conditions):
            col1, col2 = st.columns([3, 1])
            with col1:
                cond['name'] = st.text_input(f"特性 {i+1}", value=cond.get('name', ''), key=f"cond_{i}")
            with col2:
                status_options = ["Active", "Resolved"]
                current_status = cond.get('status', 'Active')
                cond['status'] = st.selectbox("状態", status_options, index=status_options.index(current_status) if current_status in status_options else 0, key=f"cond_status_{i}")
        
        if st.button("➕ 特性を追加", key="add_cond"):
            data.setdefault('conditions', []).append({'name': '', 'status': 'Active'})
            st.rerun()
        
        # 禁忌事項
        st.subheader("🚫 禁忌事項（NgAction）")
        st.error("⚠️ **最重要**: 内容を必ず確認してください")
        
        ng_actions = data.get('ngActions', [])
        
        for i, ng in enumerate(ng_actions):
            with st.expander(f"禁忌 {i+1}: {ng.get('action', '未入力')[:30]}...", expanded=True):
                ng['action'] = st.text_area("してはいけないこと *", value=ng.get('action', ''), key=f"ng_action_{i}")
                ng['reason'] = st.text_area("理由（なぜ危険か）*", value=ng.get('reason', ''), key=f"ng_reason_{i}")
                
                risk_options = ["Panic", "LifeThreatening", "Discomfort"]
                risk_labels = {"Panic": "Panic（パニック誘発）", "LifeThreatening": "LifeThreatening（命に関わる）", "Discomfort": "Discomfort（不快）"}
                current_risk = ng.get('riskLevel', 'Panic')
                if current_risk not in risk_options:
                    current_risk = 'Panic'
                ng['riskLevel'] = st.selectbox(
                    "リスクレベル",
                    risk_options,
                    format_func=lambda x: risk_labels.get(x, x),
                    index=risk_options.index(current_risk),
                    key=f"ng_risk_{i}"
                )
        
        if st.button("➕ 禁忌事項を追加", key="add_ng"):
            data.setdefault('ngActions', []).append({'action': '', 'reason': '', 'riskLevel': 'Panic'})
            st.rerun()
        
        # 推奨ケア
        st.subheader("✅ 推奨ケア（CarePreference）")
        care_prefs = data.get('carePreferences', [])
        
        for i, care in enumerate(care_prefs):
            with st.expander(f"ケア {i+1}: {care.get('category', 'カテゴリ不明')}", expanded=True):
                col1, col2 = st.columns([1, 1])
                with col1:
                    cat_options = ["食事", "入浴", "睡眠", "移動", "パニック時", "服薬", "コミュニケーション", "その他"]
                    current_cat = care.get('category', 'その他')
                    if current_cat not in cat_options:
                        cat_options.append(current_cat)
                    care['category'] = st.selectbox("カテゴリ", cat_options, index=cat_options.index(current_cat), key=f"care_cat_{i}")
                with col2:
                    pri_options = ["High", "Medium", "Low"]
                    current_pri = care.get('priority', 'Medium')
                    if current_pri not in pri_options:
                        current_pri = 'Medium'
                    care['priority'] = st.selectbox("優先度", pri_options, index=pri_options.index(current_pri), key=f"care_pri_{i}")
                
                care['instruction'] = st.text_area("具体的な方法 *", value=care.get('instruction', ''), key=f"care_inst_{i}")
        
        if st.button("➕ 推奨ケアを追加", key="add_care"):
            data.setdefault('carePreferences', []).append({'category': 'その他', 'instruction': '', 'priority': 'Medium'})
            st.rerun()
    
    # --- 第3の柱: 法的基盤 ---
    with tab3:
        st.subheader("🎫 手帳・受給者証")
        st.warning("📅 **更新日は正確に確認してください**")
        
        certificates = data.get('certificates', [])
        
        for i, cert in enumerate(certificates):
            with st.expander(f"証明書 {i+1}: {cert.get('type', '種類不明')}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    type_options = ["療育手帳", "精神障害者保健福祉手帳", "身体障害者手帳", "障害福祉サービス受給者証", "自立支援医療受給者証", "その他"]
                    current_type = cert.get('type', 'その他')
                    if current_type not in type_options:
                        type_options.append(current_type)
                    cert['type'] = st.selectbox("種類", type_options, index=type_options.index(current_type), key=f"cert_type_{i}")
                with col2:
                    cert['grade'] = st.text_input("等級 *", value=cert.get('grade', ''), placeholder="例: A1, 2級, 区分5", key=f"cert_grade_{i}")
                
                renewal = safe_date_parse(cert.get('nextRenewalDate'))
                cert['nextRenewalDate'] = st.date_input(
                    "次回更新日 *",
                    value=renewal or (date.today().replace(year=date.today().year + 1)),
                    key=f"cert_renewal_{i}"
                ).isoformat()
        
        if st.button("➕ 手帳・受給者証を追加", key="add_cert"):
            data.setdefault('certificates', []).append({'type': '', 'grade': '', 'nextRenewalDate': ''})
            st.rerun()
    
    # --- 第4の柱: 危機管理 ---
    with tab4:
        st.subheader("📞 キーパーソン（緊急連絡先）")
        st.info("🔢 rank（優先順位）: 1が最優先。緊急時この順番で連絡します。")
        
        key_persons = data.get('keyPersons', [])
        
        for i, kp in enumerate(key_persons):
            with st.expander(f"連絡先 {i+1}: {kp.get('name', '未入力')}（{kp.get('relationship', '')}）", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    kp['name'] = st.text_input("氏名 *", value=kp.get('name', ''), key=f"kp_name_{i}")
                    kp['relationship'] = st.text_input("続柄 *", value=kp.get('relationship', ''), placeholder="例: 母, 叔父", key=f"kp_rel_{i}")
                with col2:
                    kp['phone'] = st.text_input("電話番号 *", value=kp.get('phone', ''), key=f"kp_phone_{i}")
                    kp['rank'] = st.number_input("優先順位", min_value=1, max_value=10, value=kp.get('rank', i+1), key=f"kp_rank_{i}")
                
                kp['role'] = st.text_input("役割", value=kp.get('role', '緊急連絡先'), placeholder="例: 緊急連絡先, 医療同意", key=f"kp_role_{i}")
        
        if st.button("➕ キーパーソンを追加", key="add_kp"):
            data.setdefault('keyPersons', []).append({'name': '', 'relationship': '', 'phone': '', 'role': '緊急連絡先', 'rank': len(key_persons)+1})
            st.rerun()
        
        # 後見人
        st.subheader("⚖️ 後見人等")
        guardians = data.get('guardians', [])
        
        for i, g in enumerate(guardians):
            col1, col2 = st.columns(2)
            with col1:
                g['name'] = st.text_input("氏名/法人名", value=g.get('name', ''), key=f"g_name_{i}")
                type_options = ["成年後見", "保佐", "補助", "任意後見", "予定"]
                current_type = g.get('type', '成年後見')
                if current_type not in type_options:
                    type_options.append(current_type)
                g['type'] = st.selectbox("種別", type_options, index=type_options.index(current_type), key=f"g_type_{i}")
            with col2:
                g['phone'] = st.text_input("連絡先", value=g.get('phone', ''), key=f"g_phone_{i}")
                g['organization'] = st.text_input("所属", value=g.get('organization', ''), key=f"g_org_{i}")
        
        if st.button("➕ 後見人を追加", key="add_guardian"):
            data.setdefault('guardians', []).append({'name': '', 'type': '成年後見', 'phone': '', 'organization': ''})
            st.rerun()
        
        # 医療機関
        st.subheader("🏥 医療機関")
        hospitals = data.get('hospitals', [])
        
        for i, h in enumerate(hospitals):
            col1, col2 = st.columns(2)
            with col1:
                h['name'] = st.text_input("病院名", value=h.get('name', ''), key=f"h_name_{i}")
                h['specialty'] = st.text_input("診療科", value=h.get('specialty', ''), key=f"h_spec_{i}")
            with col2:
                h['phone'] = st.text_input("電話番号", value=h.get('phone', ''), key=f"h_phone_{i}")
                h['doctor'] = st.text_input("担当医", value=h.get('doctor', ''), key=f"h_doc_{i}")
        
        if st.button("➕ 医療機関を追加", key="add_hospital"):
            data.setdefault('hospitals', []).append({'name': '', 'specialty': '', 'phone': '', 'doctor': ''})
            st.rerun()
    
    # 更新されたデータを保存
    st.session_state.edited_data = data
    
    # ナビゲーションボタン
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← 入力に戻る", use_container_width=True):
            st.session_state.step = 'input'
            st.rerun()
    
    with col3:
        if st.button("最終確認へ →", type="primary", use_container_width=True):
            if not data.get('client', {}).get('name'):
                st.error("クライアント名は必須です")
            else:
                st.session_state.step = 'confirm'
                st.rerun()

# =============================================================================
# Step 3: 最終確認
# =============================================================================

def render_confirm_step():
    st.title("✅ 最終確認")
    st.markdown("以下の内容でデータベースに登録します。内容を確認してください。")
    
    data = st.session_state.edited_data
    
    if not data:
        st.error("データがありません")
        return
    
    client_name = data.get('client', {}).get('name', '不明')
    
    st.header(f"👤 {client_name} さんの登録内容")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 基本情報")
        st.write(f"**生年月日**: {data.get('client', {}).get('dob', '未設定')}")
        st.write(f"**血液型**: {data.get('client', {}).get('bloodType', '未設定')}")
        
        if data.get('conditions'):
            st.subheader("🏥 特性・診断")
            for c in data['conditions']:
                if c.get('name'):
                    st.write(f"- {c['name']}")
        
        if data.get('ngActions'):
            st.subheader("🚫 禁忌事項")
            for ng in data['ngActions']:
                if ng.get('action'):
                    risk_emoji = {"LifeThreatening": "🔴", "Panic": "🟠", "Discomfort": "🟡"}.get(ng.get('riskLevel'), "⚪")
                    st.write(f"{risk_emoji} **{ng['action']}**")
                    st.write(f"　理由: {ng.get('reason', '未設定')}")
        
        if data.get('carePreferences'):
            st.subheader("✅ 推奨ケア")
            for cp in data['carePreferences']:
                if cp.get('instruction'):
                    st.write(f"- **[{cp.get('category', '')}]** {cp['instruction']}")
    
    with col2:
        if data.get('certificates'):
            st.subheader("🎫 手帳・受給者証")
            for cert in data['certificates']:
                if cert.get('type'):
                    st.write(f"- {cert['type']} ({cert.get('grade', '等級不明')})")
                    st.write(f"　更新日: {cert.get('nextRenewalDate', '未設定')}")
        
        if data.get('keyPersons'):
            st.subheader("📞 キーパーソン")
            sorted_kp = sorted(data['keyPersons'], key=lambda x: x.get('rank', 99))
            for kp in sorted_kp:
                if kp.get('name'):
                    st.write(f"{kp.get('rank', '-')}. **{kp['name']}**（{kp.get('relationship', '')}）")
                    st.write(f"　📱 {kp.get('phone', '未設定')}")
        
        if data.get('guardians'):
            st.subheader("⚖️ 後見人等")
            for g in data['guardians']:
                if g.get('name'):
                    st.write(f"- {g['name']}（{g.get('type', '')}）")
        
        if data.get('hospitals'):
            st.subheader("🏥 医療機関")
            for h in data['hospitals']:
                if h.get('name'):
                    st.write(f"- {h['name']}（{h.get('specialty', '')}）")
    
    # ナビゲーションボタン
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← 修正に戻る", use_container_width=True):
            st.session_state.step = 'edit'
            st.rerun()
    
    with col3:
        if st.button("✅ データベースに登録", type="primary", use_container_width=True):
            with st.spinner("登録中..."):
                try:
                    # 編集済みツリー形式をグラフ形式に変換してDB登録
                    graph_data = tree_to_graph(data)
                    register_to_database(graph_data)
                    st.session_state.step = 'done'
                    st.rerun()
                except Exception as e:
                    st.error(f"登録エラー: {e}")

# =============================================================================
# Step 4: 完了
# =============================================================================

def render_done_step():
    st.title("🎉 登録完了")
    
    st.success("データベースへの登録が完了しました！")
    st.balloons()
    
    client_name = st.session_state.edited_data.get('client', {}).get('name', '')
    
    st.markdown(f"""
    ### {client_name}さんの情報が登録されました
    
    **Claude Desktop**から以下のような質問ができます：
    - 「{client_name}さんの禁忌事項を教えて」
    - 「{client_name}さんがパニックを起こしたらどうすれば？」
    - 「{client_name}さんの緊急連絡先は？」
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 続けて登録する", use_container_width=True, type="primary"):
            reset_session_state()
            st.rerun()
    
    with col2:
        if st.button("📊 登録データを確認", use_container_width=True):
            st.session_state.show_data = True
            st.rerun()
    
    # データ確認表示
    if st.session_state.get('show_data'):
        st.divider()
        st.subheader(f"📋 {client_name}さんの登録データ")
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["禁忌事項", "推奨ケア", "支援記録", "キーパーソン", "手帳", "📊 データ出力"])
        
        with tab1:
            ng_data = run_query("""
                MATCH (c:Client {name: $name})-[:MUST_AVOID]->(ng:NgAction)
                RETURN ng.action as 禁忌, ng.reason as 理由, ng.riskLevel as リスク
            """, {"name": client_name})
            if ng_data:
                st.dataframe(ng_data, use_container_width=True)
            else:
                st.info("登録なし")
        
        with tab2:
            care_data = run_query("""
                MATCH (c:Client {name: $name})-[:REQUIRES]->(cp:CarePreference)
                RETURN cp.category as カテゴリ, cp.instruction as 内容, cp.priority as 優先度
            """, {"name": client_name})
            if care_data:
                st.dataframe(care_data, use_container_width=True)
            else:
                st.info("登録なし")

        with tab3:
            st.markdown("#### 📝 支援記録履歴")

            # 支援記録を取得
            support_logs = get_support_logs(client_name, limit=50)

            if support_logs:
                # 効果別に色分け表示
                st.markdown(f"**全{len(support_logs)}件の記録**")

                for log in support_logs:
                    # 効果に応じて色分け
                    if log['効果'] == 'Effective':
                        badge_color = "#28a745"  # 緑
                        badge_icon = "✅"
                    elif log['効果'] == 'Ineffective':
                        badge_color = "#dc3545"  # 赤
                        badge_icon = "❌"
                    else:
                        badge_color = "#6c757d"  # グレー
                        badge_icon = "➖"

                    with st.container():
                        col1, col2, col3 = st.columns([2, 3, 1])

                        with col1:
                            st.markdown(f"**📅 {log['日付']}**")
                            st.caption(f"記録者: {log['支援者']}")

                        with col2:
                            st.markdown(f"**状況**: {log['状況']}")
                            st.text(f"対応: {log['対応'][:100]}{'...' if len(log['対応']) > 100 else ''}")

                        with col3:
                            st.markdown(
                                f'<div style="background-color: {badge_color}; color: white; '
                                f'padding: 4px 8px; border-radius: 4px; text-align: center;">'
                                f'{badge_icon} {log["効果"]}</div>',
                                unsafe_allow_html=True
                            )

                        # 詳細メモがあれば表示
                        if log.get('メモ'):
                            with st.expander("📎 詳細メモを見る"):
                                st.info(log['メモ'])

                        st.divider()

                # パターン発見セクション
                st.markdown("---")
                st.markdown("#### 🔍 効果的なケアパターンの発見")

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption("複数回効果があった対応を自動検出します")
                with col2:
                    min_freq = st.number_input("最小回数", min_value=1, max_value=10, value=2, key="min_freq")

                if st.button("🔍 パターンを発見", use_container_width=True):
                    patterns = discover_care_patterns(client_name, min_frequency=min_freq)

                    if patterns:
                        st.success(f"✅ {len(patterns)}件のパターンを発見しました")

                        for i, pattern in enumerate(patterns, 1):
                            with st.container():
                                st.markdown(
                                    f'<div style="background-color: #e7f3ff; padding: 12px; '
                                    f'border-left: 4px solid #0066cc; border-radius: 4px; margin: 8px 0;">'
                                    f'<strong>パターン {i}</strong><br>'
                                    f'<strong>状況:</strong> {pattern["状況"]}<br>'
                                    f'<strong>対応:</strong> {pattern["対応方法"]}<br>'
                                    f'<strong>効果的だった回数:</strong> {pattern["効果的だった回数"]}回'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                    else:
                        st.warning(f"⚠️ {min_freq}回以上効果的だったパターンは見つかりませんでした")
            else:
                st.info("支援記録はまだ登録されていません")
                st.markdown("""
                **支援記録を追加するには:**
                - 日常の支援内容を物語風に入力してください
                - 「今日〜した」「〜の対応で落ち着いた」などの表現が自動抽出されます
                """)

        with tab4:
            kp_data = run_query("""
                MATCH (c:Client {name: $name})-[r:HAS_KEY_PERSON]->(kp:KeyPerson)
                RETURN r.rank as 順位, kp.name as 氏名, kp.relationship as 続柄, kp.phone as 電話
                ORDER BY r.rank
            """, {"name": client_name})
            if kp_data:
                st.dataframe(kp_data, use_container_width=True)
            else:
                st.info("登録なし")

        with tab5:
            cert_data = run_query("""
                MATCH (c:Client {name: $name})-[:HAS_CERTIFICATE]->(cert:Certificate)
                RETURN cert.type as 種類, cert.grade as 等級, cert.nextRenewalDate as 更新日
            """, {"name": client_name})
            if cert_data:
                st.dataframe(cert_data, use_container_width=True)
            else:
                st.info("登録なし")

        with tab6:
            st.subheader("📥 データの出力")
            st.markdown("登録された内容をファイル形式でダウンロードできます。")
            
            # Excel Export
            st.markdown("##### 📊 Excel データ出力")
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("Excelファイルを生成", key="generate_excel", use_container_width=True):
                    with st.spinner("生成中..."):
                        try:
                            path = export_client_data_to_excel(client_name)
                            st.session_state['generated_excel_path'] = path
                            st.rerun()
                        except Exception as e:
                            st.error(f"エラーが発生しました: {e}")
            
            with col2:
                if st.session_state.get('generated_excel_path'):
                    path = st.session_state['generated_excel_path']
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            st.download_button(
                                label="📥 Excelをダウンロード",
                                data=f,
                                file_name=os.path.basename(path),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        st.caption(f"生成済み: {os.path.basename(path)}")
                    else:
                        st.warning("ファイルが見つかりません。再生成してください。")

            st.divider()

            # PDF Export
            st.markdown("##### 🚑 緊急時情報シート (PDF)")
            st.caption("救急隊や医療機関に手渡すためのA4シートです。")
            
            col3, col4 = st.columns([1, 2])
            with col3:
                if st.button("PDFシートを生成", key="generate_pdf", use_container_width=True):
                    with st.spinner("生成中..."):
                        try:
                            path = generate_emergency_sheet_pdf(client_name)
                            st.session_state['generated_pdf_path'] = path
                            st.rerun()
                        except Exception as e:
                            st.error(f"エラーが発生しました: {e}")
            
            with col4:
                if st.session_state.get('generated_pdf_path'):
                    path = st.session_state['generated_pdf_path']
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            st.download_button(
                                label="📥 PDFをダウンロード",
                                data=f,
                                file_name=os.path.basename(path),
                                mime="application/pdf",
                                use_container_width=True
                            )
                        st.caption(f"生成済み: {os.path.basename(path)}")
                    else:
                        st.warning("ファイルが見つかりません。再生成してください。")


# =============================================================================
# メイン: ステップに応じた画面表示
# =============================================================================

if st.session_state.step == 'input':
    render_input_step()
elif st.session_state.step == 'edit':
    render_edit_step()
elif st.session_state.step == 'confirm':
    render_confirm_step()
elif st.session_state.step == 'done':
    render_done_step()
