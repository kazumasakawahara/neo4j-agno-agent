"""
セマンティック検索ページ
Gemini Embedding 2 + Neo4j Vector Index による意味検索
"""

import streamlit as st

from lib.db_new_operations import get_clients_list, is_db_available


def main():
    st.header("🔍 セマンティック検索")
    st.caption("テキストの意味に基づいて支援記録・禁忌事項を検索します")

    if not is_db_available():
        st.error("Neo4j に接続できません。Docker が起動しているか確認してください。")
        return

    # --- 検索フォーム ---
    query = st.text_input(
        "検索クエリ",
        placeholder="例: 金銭管理に不安がある、パニック時の対応方法",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        search_target = st.radio(
            "検索対象",
            ["支援記録", "禁忌事項"],
            horizontal=True,
        )
    with col2:
        client_filter = None
        if search_target == "支援記録":
            clients = get_clients_list()
            client_options = ["（全員）"] + clients
            selected = st.selectbox("クライアント（任意）", client_options)
            if selected != "（全員）":
                client_filter = selected

    top_k = st.slider("表示件数", min_value=1, max_value=30, value=10)

    if st.button("検索", type="primary", disabled=not query):
        _run_search(query, search_target, top_k, client_filter)

    # --- Embedding 統計 ---
    with st.expander("📊 Embedding 統計", expanded=False):
        _show_stats()


def _run_search(query: str, target: str, top_k: int, client_name: str | None):
    """検索を実行して結果を表示"""
    try:
        if target == "支援記録":
            from lib.embedding import search_support_logs_semantic

            results = search_support_logs_semantic(query, top_k=top_k, client_name=client_name)
            if not results:
                st.info("該当する支援記録が見つかりませんでした。embeddingが付与されているか確認してください。")
                return

            st.subheader(f"検索結果: {len(results)} 件")
            for r in results:
                score = r.get("スコア", 0)
                color = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
                with st.container(border=True):
                    cols = st.columns([1, 3, 6])
                    cols[0].metric("スコア", f"{score:.3f}", label_visibility="collapsed")
                    cols[1].write(f"**{r.get('クライアント', '不明')}**")
                    cols[2].write(f"{r.get('日付', '')} / 支援者: {r.get('支援者', '')}")
                    st.write(f"{color} **状況:** {r.get('状況', '')}")
                    st.write(f"**対応:** {r.get('対応', '')}")
                    if r.get("効果"):
                        st.write(f"**効果:** {r['効果']}")
                    if r.get("メモ"):
                        st.caption(f"メモ: {r['メモ']}")
        else:
            from lib.embedding import search_ng_actions_semantic

            results = search_ng_actions_semantic(query, top_k=top_k)
            if not results:
                st.info("該当する禁忌事項が見つかりませんでした。embeddingが付与されているか確認してください。")
                return

            st.subheader(f"検索結果: {len(results)} 件")
            for r in results:
                score = r.get("スコア", 0)
                risk = r.get("リスクレベル", "")
                risk_icon = {"LifeThreatening": "🔴", "Panic": "🟠", "Discomfort": "🟡"}.get(risk, "⚪")
                with st.container(border=True):
                    cols = st.columns([1, 2, 7])
                    cols[0].metric("スコア", f"{score:.3f}", label_visibility="collapsed")
                    cols[1].write(f"**{r.get('クライアント', '')}**")
                    cols[2].write(f"{risk_icon} {risk}")
                    st.write(f"**禁忌:** {r.get('禁忌事項', '')}")
                    if r.get("理由"):
                        st.write(f"**理由:** {r['理由']}")
    except Exception as e:
        st.error(f"検索エラー: {e}")


def _show_stats():
    """embedding付与状況を表示"""
    try:
        from lib.embedding import get_embedding_stats

        stats = get_embedding_stats()
        cols = st.columns(len(stats))
        for col, (label, s) in zip(cols, stats.items()):
            total = s["total"]
            embedded = s["embedded"]
            pct = (embedded / total * 100) if total > 0 else 0
            col.metric(label, f"{embedded}/{total}", f"{pct:.0f}%")

        # バックフィルのヒント
        all_done = all(s["embedded"] == s["total"] for s in stats.values() if s["total"] > 0)
        if not all_done:
            st.info(
                "未付与のノードがあります。以下のコマンドで一括付与できます:\n\n"
                "```\nuv run python scripts/backfill_embeddings.py --all\n```"
            )
    except Exception as e:
        st.warning(f"統計取得エラー: {e}")


main()
