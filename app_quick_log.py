"""
親亡き後支援データベース - かんたん記録
支援者がスマホから30秒で記録できるシンプルUI

設計思想:
- 「普通」は記録しない（データの肥大化防止）
- 両極端な事象のみ記録（とても良い / 気になる）
- 最小限のタップで完了
"""

import streamlit as st
from datetime import date, datetime
from functools import lru_cache

import pykakasi

# --- ライブラリからインポート ---
from lib.db_operations import (
    run_query,
    get_clients_list,
    get_clients_list_extended,
    resolve_client,
    match_client_clause,
    create_audit_log,
)
from lib.utils import init_session_state
from lib.voice_input import render_voice_input

# --- 漢字→ひらがな変換 ---
_kakasi = pykakasi.kakasi()


@lru_cache(maxsize=128)
def to_hiragana(text: str) -> str:
    """漢字テキストをひらがなに変換（検索用）"""
    result = _kakasi.convert(text)
    return "".join(item["hira"] for item in result)

# --- ページ設定 ---
# Page Config handled by app.py (unified navigation)
# st.set_page_config(
#     page_title="かんたん記録",
#     layout="centered",
#     page_icon="📝",
#     initial_sidebar_state="collapsed"
# )

# --- スタイル（モバイル最適化） ---
st.markdown("""
<style>
    /* 大きなボタン */
    .stButton > button {
        width: 100%;
        height: 80px;
        font-size: 1.3rem;
        margin: 8px 0;
        border-radius: 16px;
    }

    /* 良い日ボタン */
    .good-btn > button {
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
    }

    /* 気になるボタン */
    .concern-btn > button {
        background-color: #FF9800 !important;
        color: white !important;
        border: none !important;
    }

    /* セレクトボックス */
    .stSelectbox > div > div {
        font-size: 1.2rem;
        padding: 12px;
    }

    /* テキストエリア */
    .stTextArea > div > div > textarea {
        font-size: 1.1rem;
    }

    /* 成功メッセージ */
    .success-message {
        background-color: #E8F5E9;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin: 20px 0;
    }

    /* ヘッダー */
    h1 {
        text-align: center;
        font-size: 1.8rem !important;
    }

    /* サブヘッダー */
    h3 {
        text-align: center;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)


# --- セッション状態の初期化 ---
if 'quick_log_step' not in st.session_state:
    st.session_state.quick_log_step = 'select_client'
if 'selected_client' not in st.session_state:
    st.session_state.selected_client = None
if 'log_type' not in st.session_state:
    st.session_state.log_type = None


def reset_state():
    """状態をリセット"""
    st.session_state.quick_log_step = 'select_client'
    st.session_state.selected_client = None
    st.session_state.log_type = None


def save_quick_log(client_identifier: str, log_type: str, detail: str, supporter_name: str):
    """
    クイックログを保存（仮名化対応）

    Args:
        client_identifier: クライアント識別子（clientId, displayCode, または name）
        log_type: 'good' または 'concern'
        detail: 詳細メモ
        supporter_name: 支援者名
    """
    # SupportLogとして保存
    situation = "良好" if log_type == 'good' else "気になる点"
    effectiveness = "Effective" if log_type == 'good' else "Neutral"

    # クライアント識別子を解決
    resolved = resolve_client(client_identifier)
    client_name = resolved.get('name') if resolved else client_identifier

    # Supporterノードを作成/取得
    run_query("""
        MERGE (s:Supporter {name: $supporter})
    """, {"supporter": supporter_name})

    # クライアントマッチ句を生成（仮名化対応）
    match_clause, match_params = match_client_clause(client_identifier)

    # SupportLogノードを作成
    query = f"""
        {match_clause}
        MATCH (s:Supporter {{name: $supporter}})

        CREATE (log:SupportLog {{
            date: date($date),
            situation: $situation,
            action: $detail,
            effectiveness: $effectiveness,
            note: $note,
            logType: $log_type
        }})

        CREATE (s)-[:LOGGED]->(log)-[:ABOUT]->(c)

        RETURN log.date as date
    """

    params = {
        **match_params,
        "supporter": supporter_name,
        "date": date.today().isoformat(),
        "situation": situation,
        "detail": detail,
        "effectiveness": effectiveness,
        "note": f"クイック記録: {log_type}",
        "log_type": log_type
    }

    result = run_query(query, params)

    # 監査ログ
    create_audit_log(
        user_name=supporter_name,
        action="CREATE",
        target_type="SupportLog",
        target_name=f"{situation}: {detail[:30]}..." if len(detail) > 30 else f"{situation}: {detail}",
        details=f"クイック記録（{log_type}）",
        client_name=client_name
    )

    return len(result) > 0


# =============================================================================
# メイン画面
# =============================================================================

st.title("📝 かんたん記録")

# --- Step 1: クライアント選択 ---
if st.session_state.quick_log_step == 'select_client':
    st.markdown("### 誰の記録？")

    # 仮名化対応版でクライアント一覧を取得
    clients_extended = get_clients_list_extended(include_pii=True)

    if not clients_extended:
        st.warning("クライアントが登録されていません")
        st.stop()

    # 表示用リストを作成（displayCode があれば表示、なければ name のみ）
    def format_client(c):
        if c.get('displayCode'):
            return f"{c['displayCode']}: {c.get('name', '不明')}"
        return c.get('name', '不明')

    # --- あかさたなボタンで絞り込み（テキスト入力不要・IME問題なし） ---
    # 各クライアントの読みの先頭行を事前計算
    KANA_ROWS = {
        "あ": "あいうえお", "か": "かきくけこ", "さ": "さしすせそ",
        "た": "たちつてと", "な": "なにぬねの", "は": "はひふへほ",
        "ま": "まみむめも", "や": "やゆよ", "ら": "らりるれろ",
        "わ": "わをん",
    }

    def get_kana_row(name: str) -> str:
        """名前の先頭文字が属するかな行を返す"""
        hira = to_hiragana(name)
        if not hira:
            return ""
        first = hira[0]
        for row_key, row_chars in KANA_ROWS.items():
            if first in row_chars:
                return row_key
        return ""

    # セッション状態の初期化
    if 'kana_filter' not in st.session_state:
        st.session_state.kana_filter = None

    # あかさたなボタン行
    st.caption("🔍 頭文字で絞り込み")
    filter_cols = st.columns(6)
    kana_keys = ["全員", "あ", "か", "さ", "た", "な"]
    for i, key in enumerate(kana_keys):
        with filter_cols[i]:
            is_active = (key == "全員" and st.session_state.kana_filter is None) or \
                        (st.session_state.kana_filter == key)
            btn_type = "primary" if is_active else "secondary"
            if st.button(key, key=f"kana_{key}", use_container_width=True, type=btn_type):
                st.session_state.kana_filter = None if key == "全員" else key
                st.rerun()

    filter_cols2 = st.columns(5)
    kana_keys2 = ["は", "ま", "や", "ら", "わ"]
    for i, key in enumerate(kana_keys2):
        with filter_cols2[i]:
            is_active = st.session_state.kana_filter == key
            btn_type = "primary" if is_active else "secondary"
            if st.button(key, key=f"kana_{key}", use_container_width=True, type=btn_type):
                st.session_state.kana_filter = key
                st.rerun()

    # フィルタリング
    if st.session_state.kana_filter:
        filtered = [
            c for c in clients_extended
            if get_kana_row(c.get('name', '') or '') == st.session_state.kana_filter
        ]
    else:
        filtered = clients_extended

    # 候補リスト
    if not filtered:
        st.info("該当するクライアントがいません。別の行を選んでください。")
    else:
        client_map = {
            c.get('clientId') or c.get('name'): format_client(c)
            for c in filtered
        }
        selected = st.radio(
            "クライアントを選択",
            options=list(client_map.keys()),
            format_func=lambda x: client_map.get(x, x),
            label_visibility="collapsed",
        )

        if st.button("▶ この人の記録をつける", type="primary", use_container_width=True):
            st.session_state.selected_client = selected
            st.session_state.quick_log_step = 'select_type'
            st.rerun()

# --- Step 2: 記録タイプ選択 ---
elif st.session_state.quick_log_step == 'select_type':
    client = st.session_state.selected_client
    # 識別子から表示名を取得
    resolved = resolve_client(client)
    display_name = resolved.get('name') if resolved else client

    st.markdown(f"### {display_name} さん")
    st.markdown("#### 今日はどうでしたか？")

    st.markdown("")

    # 良い日ボタン
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="good-btn">', unsafe_allow_html=True)
        if st.button("😊\nとても良い日！", key="good_btn", use_container_width=True):
            st.session_state.log_type = 'good'
            st.session_state.quick_log_step = 'input_detail'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="concern-btn">', unsafe_allow_html=True)
        if st.button("🤔\n気になることあり", key="concern_btn", use_container_width=True):
            st.session_state.log_type = 'concern'
            st.session_state.quick_log_step = 'input_detail'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("💡 「普通の日」は記録不要です。特別なことがあった時だけ記録しましょう。")

    # 戻るボタン
    if st.button("← 戻る", key="back_to_select"):
        reset_state()
        st.rerun()

# --- Step 3: 詳細入力 ---
elif st.session_state.quick_log_step == 'input_detail':
    client = st.session_state.selected_client
    log_type = st.session_state.log_type
    # 識別子から表示名を取得
    resolved = resolve_client(client)
    display_name = resolved.get('name') if resolved else client

    if log_type == 'good':
        st.markdown(f"### 😊 {display_name} さん")
        st.markdown("#### 良かったこと")
        placeholder = "例：笑顔がたくさん見られた、食事を完食した、新しいことに挑戦できた"
        required = False
    else:
        st.markdown(f"### 🤔 {display_name} さん")
        st.markdown("#### 気になったこと")
        placeholder = "例：いつもより元気がなかった、食欲がなかった、パニックがあった"
        required = True

    # 詳細入力
    detail = st.text_area(
        "詳細（音声入力も使えます）",
        placeholder=placeholder,
        height=120,
        label_visibility="collapsed"
    )

    # 音声入力コンポーネント
    with st.expander("🎤 音声入力を使う", expanded=False):
        st.caption("音声で入力し、コピーして上のテキストエリアに貼り付けてください")
        render_voice_input(target_key="quick_log_voice", height=180)

    # 支援者名
    supporter = st.text_input(
        "あなたの名前",
        placeholder="例：田中",
        key="supporter_name"
    )

    st.markdown("")

    # 保存ボタン
    can_save = (detail.strip() or not required) and supporter.strip()

    if st.button("✅ 記録する", disabled=not can_save, use_container_width=True, type="primary"):
        with st.spinner("保存中..."):
            success = save_quick_log(
                client_name=client,
                log_type=log_type,
                detail=detail.strip() or "（詳細なし）",
                supporter_name=supporter.strip()
            )

        if success:
            st.session_state.quick_log_step = 'done'
            st.rerun()
        else:
            st.error("保存に失敗しました。クライアント名を確認してください。")

    if not can_save:
        if required and not detail.strip():
            st.caption("⚠️ 気になることの詳細を入力してください")
        if not supporter.strip():
            st.caption("⚠️ あなたの名前を入力してください")

    st.markdown("---")

    # 戻るボタン
    if st.button("← 戻る", key="back_to_type"):
        st.session_state.quick_log_step = 'select_type'
        st.rerun()

# --- Step 4: 完了 ---
elif st.session_state.quick_log_step == 'done':
    client = st.session_state.selected_client
    log_type = st.session_state.log_type
    # 識別子から表示名を取得
    resolved = resolve_client(client)
    display_name = resolved.get('name') if resolved else client

    emoji = "😊" if log_type == 'good' else "📝"
    message = "良い記録" if log_type == 'good' else "気になる点"

    st.markdown(f"""
    <div class="success-message">
        <h1>{emoji}</h1>
        <h2>記録しました！</h2>
        <p>{display_name} さんの{message}を保存しました</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 続けて記録", use_container_width=True):
            reset_state()
            st.rerun()

    with col2:
        if st.button("👋 終了", use_container_width=True):
            st.markdown("### お疲れさまでした！")
            st.balloons()


# --- フッター ---
st.markdown("---")
st.caption("💡 ヒント: 「🎤 音声入力を使う」を開くと、ブラウザの音声認識で入力できます")
