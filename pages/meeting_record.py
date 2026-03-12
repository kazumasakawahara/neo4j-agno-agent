"""
面談記録の登録ページ
音声ファイルをアップロードして面談記録を Neo4j に登録
"""

import os
import tempfile

import streamlit as st

from lib.db_new_operations import get_clients_list, is_db_available


def main():
    st.header("🎙️ 面談記録の登録")
    st.caption("音声ファイルをアップロードして面談記録を登録します（Gemini で自動文字起こし対応）")

    if not is_db_available():
        st.error("Neo4j に接続できません。Docker が起動しているか確認してください。")
        return

    # --- 入力フォーム ---
    uploaded = st.file_uploader(
        "音声ファイル",
        type=["mp3", "wav", "m4a", "ogg", "flac", "aac"],
        help="最大80秒の音声ファイル（80秒超は文字起こし＋テキストembeddingのみ）",
    )

    col1, col2 = st.columns(2)
    with col1:
        clients = get_clients_list()
        if clients:
            client_name = st.selectbox("クライアント", clients)
        else:
            client_name = st.text_input("クライアント名")

    with col2:
        date = st.date_input("面談日")

    title = st.text_input("タイトル", placeholder="例: 第3回支援会議")
    supporter_name = st.text_input("記録者名", placeholder="支援者の名前")
    note = st.text_area("メモ（任意）", placeholder="面談に関するメモ")
    auto_transcribe = st.checkbox("自動文字起こし", value=True, help="Gemini 2.0 Flash で音声をテキスト化")

    # 音声プレビュー
    if uploaded:
        st.audio(uploaded)

    # --- 登録実行 ---
    can_submit = uploaded and client_name and supporter_name
    if st.button("登録", type="primary", disabled=not can_submit):
        if not uploaded or not client_name or not supporter_name:
            st.warning("音声ファイル、クライアント、記録者名は必須です。")
            return

        with st.spinner("面談記録を登録中..."):
            # 一時ファイルに保存
            suffix = os.path.splitext(uploaded.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name

            try:
                from lib.embedding import register_meeting_record

                result = register_meeting_record(
                    audio_path=tmp_path,
                    client_name=client_name,
                    supporter_name=supporter_name,
                    date=str(date),
                    title=title,
                    note=note,
                    auto_transcribe=auto_transcribe,
                )

                if result["status"] == "success":
                    st.success("面談記録を登録しました。")
                    col_a, col_b = st.columns(2)
                    col_a.metric("音声embedding", "✅" if result.get("audio_embedding") else "⏭️")
                    col_b.metric("テキストembedding", "✅" if result.get("text_embedding") else "⏭️")
                    if result.get("transcript"):
                        with st.expander("文字起こし結果", expanded=True):
                            st.write(result["transcript"])
                else:
                    st.error(f"登録エラー: {result.get('message', '不明なエラー')}")
            finally:
                os.unlink(tmp_path)


main()
