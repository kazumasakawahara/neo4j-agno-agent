import streamlit as st

# =============================================================================
# 統合ナビゲーション エントリポイント
# 3層ワークフロー: 初期登録 → クイック記録 → Claude分析
# =============================================================================

st.set_page_config(
    page_title="親亡き後支援システム",
    layout="wide",
    page_icon="🏠"
)

# ページ定義（セクション分けしたナビゲーション）
pg = st.navigation({
    "ホーム": [
        st.Page("pages/home.py", title="ダッシュボード", icon="🏠", default=True),
    ],
    "記録・登録": [
        st.Page("app_narrative.py", title="初期登録", icon="📋"),
        st.Page("app_quick_log.py", title="クイック記録", icon="⚡"),
        st.Page("pages/meeting_record.py", title="面談記録", icon="🎙️"),
    ],
    "管理": [
        st.Page("pages/client_list.py", title="クライアント一覧", icon="👥"),
    ],
    "可視化": [
        st.Page("pages/ecomap.py", title="エコマップ", icon="🗺️"),
    ],
    "活用": [
        st.Page("pages/semantic_search.py", title="セマンティック検索", icon="🔍"),
        st.Page("pages/claude_guide.py", title="Claude活用ガイド", icon="🤖"),
        st.Page("app_ui.py", title="AIチャット", icon="🛡️"),
    ],
})

# 選択されたページを実行
pg.run()
