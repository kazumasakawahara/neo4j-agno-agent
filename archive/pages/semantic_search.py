"""
セマンティック検索ページ
Gemini Embedding 2 + Neo4j Vector Index による意味検索
"""

import os

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
            ["支援記録", "禁忌事項", "面談記録", "類似クライアント"],
            horizontal=True,
        )
    with col2:
        client_filter = None
        similarity_method = None
        if search_target == "支援記録":
            clients = get_clients_list()
            client_options = ["（全員）"] + clients
            selected = st.selectbox("クライアント（任意）", client_options)
            if selected != "（全員）":
                client_filter = selected
        elif search_target == "面談記録":
            clients = get_clients_list()
            client_options = ["（全員）"] + clients
            selected = st.selectbox("クライアント（任意）", client_options, key="mr_client")
            if selected != "（全員）":
                client_filter = selected
        elif search_target == "類似クライアント":
            similarity_method = st.radio(
                "検索方法",
                ["既存クライアントから", "テキストで検索"],
                horizontal=True,
            )

    top_k = st.slider("表示件数", min_value=1, max_value=30, value=10)

    if search_target == "面談記録":
        if st.button("検索", type="primary", disabled=not query, key="mr_search"):
            _run_meeting_record_search(query, top_k, client_filter)
    elif search_target == "類似クライアント":
        _run_similar_client_search(similarity_method, top_k)
    elif st.button("検索", type="primary", disabled=not query):
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


def _run_meeting_record_search(query: str, top_k: int, client_name: str | None):
    """面談記録のセマンティック検索"""
    try:
        from lib.embedding import search_meeting_records_semantic

        results = search_meeting_records_semantic(query, top_k=top_k, client_name=client_name)
        if not results:
            st.info("該当する面談記録が見つかりませんでした。embeddingが付与されているか確認してください。")
            return

        st.subheader(f"検索結果: {len(results)} 件")
        for r in results:
            score = r.get("スコア", 0)
            color = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
            with st.container(border=True):
                cols = st.columns([1, 3, 6])
                cols[0].metric("スコア", f"{score:.3f}", label_visibility="collapsed")
                cols[1].write(f"**{r.get('クライアント', '不明')}**")
                cols[2].write(f"{r.get('日付', '')} / 記録者: {r.get('記録者', '')}")
                st.write(f"{color} **{r.get('タイトル', '無題')}**")
                if r.get("秒数"):
                    st.caption(f"録音時間: {r['秒数']}秒")
                if r.get("文字起こし抜粋"):
                    st.write(f"**文字起こし:** {r['文字起こし抜粋']}...")
                if r.get("メモ"):
                    st.caption(f"メモ: {r['メモ']}")
                # 音声ファイルが存在すれば再生ボタン
                file_path = r.get("ファイルパス")
                if file_path and os.path.exists(file_path):
                    st.audio(file_path)
    except Exception as e:
        st.error(f"検索エラー: {e}")


def _run_similar_client_search(method: str | None, top_k: int):
    """類似クライアント検索の UI と実行"""
    if method == "既存クライアントから":
        clients = get_clients_list()
        if not clients:
            st.info("クライアントが登録されていません。")
            return
        selected = st.selectbox("基準クライアント", clients, key="sim_client")
        if st.button("類似クライアントを検索", type="primary"):
            try:
                from lib.embedding import find_similar_clients

                results = find_similar_clients(selected, top_k=top_k)
                if not results:
                    st.info(
                        "類似クライアントが見つかりませんでした。"
                        "summaryEmbeddingが付与されているか確認してください。\n\n"
                        "```\nuv run python scripts/backfill_embeddings.py --label Client\n```"
                    )
                    return
                _display_similar_clients(results)
            except Exception as e:
                st.error(f"検索エラー: {e}")
    else:
        description = st.text_area(
            "支援特性の説明",
            placeholder="例: 金銭管理が困難、訪問販売の被害歴あり、感覚過敏",
        )
        if st.button("類似クライアントを検索", type="primary", disabled=not description):
            try:
                from lib.embedding import search_similar_clients_by_text

                results = search_similar_clients_by_text(description, top_k=top_k)
                if not results:
                    st.info(
                        "類似クライアントが見つかりませんでした。"
                        "summaryEmbeddingが付与されているか確認してください。"
                    )
                    return
                _display_similar_clients(results)
            except Exception as e:
                st.error(f"検索エラー: {e}")


def _display_similar_clients(results: list[dict]):
    """類似クライアントの結果を表示"""
    st.subheader(f"類似クライアント: {len(results)} 件")
    for r in results:
        score = r.get("スコア", 0)
        color = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
        with st.container(border=True):
            cols = st.columns([1, 3, 6])
            cols[0].metric("類似度", f"{score:.3f}", label_visibility="collapsed")
            cols[1].write(f"**{r.get('name', '不明')}**")
            dob = r.get("dob", "")
            cols[2].write(f"生年月日: {dob}" if dob else "")
            conditions = r.get("conditions", [])
            if conditions:
                filtered = [c for c in conditions if c]
                if filtered:
                    st.write(f"{color} **障害・疾患:** {', '.join(filtered)}")


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
