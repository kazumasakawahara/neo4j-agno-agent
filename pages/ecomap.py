"""
エコマップ生成
draw.io形式の支援ネットワーク図を生成・ダウンロード
"""

import streamlit as st
import sys
import os
import base64
import zlib
import urllib.parse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.db_operations import get_clients_list, is_db_available
from skills.ecomap_generator.drawio_engine import (
    generate_drawio_bytes,
    generate_drawio_xml,
    TEMPLATE_CONFIGS,
    CATEGORY_STYLES,
    fetch_ecomap_data,
)

def _render_drawio_web_button(xml_str: str) -> None:
    """draw.io Web版で直接開くボタンを表示する。

    draw.io の URL ハッシュ形式 (#R...) を使い、ワンクリックで
    ブラウザの draw.io エディタにエコマップを読み込む。
    エンコード: encodeURIComponent(xml) → deflateRaw → base64
    """
    if not xml_str:
        return

    encoded = urllib.parse.quote(xml_str, safe="")
    compressed = zlib.compress(encoded.encode("utf-8"), 9)[2:-4]  # raw deflate
    b64 = base64.b64encode(compressed).decode("ascii")
    drawio_url = f"https://app.diagrams.net/#R{b64}"

    st.markdown(
        f'<a href="{drawio_url}" target="_blank" rel="noopener noreferrer">'
        f'<button style="'
        f"width:100%;padding:0.5rem 1rem;border-radius:0.5rem;"
        f"background:#4CAF50;color:white;border:none;"
        f"font-size:0.95rem;font-weight:600;cursor:pointer;"
        f"margin-top:0.5rem;"
        f'">'
        f"🌐 draw.io Web版で開く"
        f"</button></a>",
        unsafe_allow_html=True,
    )


# =============================================================================
# カスタムCSS
# =============================================================================
st.markdown("""
<style>
    .template-card {
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 8px;
    }
    .template-card .name {
        font-weight: 600;
        font-size: 0.95rem;
        color: #333;
    }
    .template-card .desc {
        font-size: 0.82rem;
        color: #666;
        margin-top: 2px;
    }
    .category-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 2px 4px 2px 0;
    }
    .preview-section {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ヘッダー
# =============================================================================
st.markdown("## 🗺️ エコマップ生成")
st.caption("draw.io形式の支援ネットワーク図を生成します。ダウンロード後、draw.ioアプリで編集できます。")

st.divider()

# =============================================================================
# DB接続チェック
# =============================================================================
db_available = is_db_available()

if not db_available:
    st.warning(
        "Neo4jデータベースに接続できません。サンプルデータでデモ生成が可能です。\n\n"
        "`docker-compose up -d` でNeo4jを起動してください。"
    )

# =============================================================================
# クライアント選択
# =============================================================================
col_client, col_template = st.columns([1, 1])

with col_client:
    st.markdown("### クライアント選択")

    if db_available:
        try:
            clients = get_clients_list()
        except Exception:
            clients = []

        if clients:
            selected_client = st.selectbox(
                "クライアント",
                options=clients,
                label_visibility="collapsed",
            )
        else:
            st.info("登録済みクライアントがいません。")
            selected_client = st.text_input(
                "クライアント名を入力",
                value="テスト太郎",
                label_visibility="collapsed",
            )
    else:
        selected_client = st.text_input(
            "クライアント名を入力（デモ）",
            value="テスト太郎",
            label_visibility="collapsed",
        )

# =============================================================================
# テンプレート選択
# =============================================================================
with col_template:
    st.markdown("### テンプレート選択")

    template_options = list(TEMPLATE_CONFIGS.keys())
    template_labels = {
        k: f"{v.name}" for k, v in TEMPLATE_CONFIGS.items()
    }

    selected_template = st.radio(
        "テンプレート",
        options=template_options,
        format_func=lambda x: template_labels[x],
        label_visibility="collapsed",
    )

    config = TEMPLATE_CONFIGS[selected_template]
    st.caption(f"📝 {config.description}")
    st.caption(f"💡 用途: {config.use_case}")

st.divider()

# =============================================================================
# プレビュー情報
# =============================================================================
if selected_client:
    st.markdown("### プレビュー")

    data = fetch_ecomap_data(selected_client, selected_template)

    # カテゴリ別データ数を表示
    badges_html = ""
    for cat in config.categories:
        items = data.get(cat, [])
        style = CATEGORY_STYLES.get(cat, {})
        label = style.get("label", cat)
        fill = style.get("fill", "#f0f0f0")
        stroke = style.get("stroke", "#999")
        count = len(items)
        badges_html += (
            f'<span class="category-badge" '
            f'style="background:{fill};color:{stroke};border:1px solid {stroke};">'
            f'{label} {count}件</span>'
        )

    st.markdown(f'<div class="preview-section">{badges_html}</div>', unsafe_allow_html=True)

    total = sum(len(data.get(cat, [])) for cat in config.categories)

    if total == 0 and db_available:
        st.info(
            f"「{selected_client}」にはこのテンプレートに該当するデータがありません。"
            "別のテンプレートを試すか、データを登録してください。"
        )

    st.markdown("")

    # =============================================================================
    # 生成 & ダウンロード
    # =============================================================================
    col_gen, col_dl = st.columns([1, 1])

    with col_gen:
        generate_clicked = st.button(
            "🗺️ エコマップ生成",
            type="primary",
            use_container_width=True,
        )

    if generate_clicked:
        with st.spinner("draw.io XMLを生成中..."):
            drawio_bytes = generate_drawio_bytes(selected_client, selected_template)
            drawio_xml = generate_drawio_xml(selected_client, selected_template)

        st.session_state["ecomap_bytes"] = drawio_bytes
        st.session_state["ecomap_xml"] = drawio_xml
        st.session_state["ecomap_client"] = selected_client
        st.session_state["ecomap_template"] = selected_template
        st.success(f"生成完了（{len(drawio_bytes):,} bytes）")

    if "ecomap_bytes" in st.session_state:
        today_str = date.today().strftime("%Y%m%d")
        filename = f"{st.session_state['ecomap_client']}_ecomap_{st.session_state['ecomap_template']}_{today_str}.drawio"

        with col_dl:
            st.download_button(
                label="📥 .drawio ファイルをダウンロード",
                data=st.session_state["ecomap_bytes"],
                file_name=filename,
                mime="application/xml",
                use_container_width=True,
            )

        # draw.io Web版で開くボタン
        _render_drawio_web_button(st.session_state.get("ecomap_xml", ""))

# =============================================================================
# draw.io 案内
# =============================================================================
st.divider()

with st.expander("📖 draw.io でエコマップを開く方法"):
    st.markdown("""
**Web版（インストール不要）**
1. [app.diagrams.net](https://app.diagrams.net/) にアクセス
2. 「ファイル」→「開く」→ ダウンロードした `.drawio` ファイルを選択
3. ノードをドラッグして位置を変更、ダブルクリックでテキスト編集

**デスクトップ版**
1. [draw.io Desktop](https://github.com/jgraph/drawio-desktop/releases) からインストール
2. `.drawio` ファイルをダブルクリックで開く

**編集のヒント**
- ノードをドラッグ＆ドロップで位置調整
- ダブルクリックでテキスト編集
- 右クリックでスタイル変更
- 「ファイル」→「エクスポート」でPNG/PDF/SVGに変換可能
""")
