"""
Claude Desktop 活用ガイド
プロンプト集 + 使い方の説明
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.db_operations import get_clients_list

# =============================================================================
# カスタムCSS
# =============================================================================
st.markdown("""
<style>
    .prompt-card {
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 18px;
        margin: 10px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .prompt-title {
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 8px;
        color: #212529;
    }
    .prompt-desc {
        font-size: 0.88rem;
        color: #6c757d;
        margin-bottom: 10px;
    }
    .auto-actions {
        background: #F3E5F5;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
        font-size: 0.85rem;
    }
    .auto-actions strong {
        color: #6A1B9A;
    }
    .intro-box {
        background: linear-gradient(135deg, #F3E5F5 0%, #EDE7F6 100%);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border-left: 4px solid #6A1B9A;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# ヘッダー
# =============================================================================
st.markdown("## 🤖 Claude Desktop 活用ガイド")

st.markdown("""
<div class="intro-box">
    <strong>レイヤー3：分析・提案</strong><br>
    Streamlitで登録・記録したデータを、Claude Desktopが分析し、
    ケアパターンの発見・リスク検出・支援改善の提案を行います。<br><br>
    以下のプロンプトをコピーして、Claude Desktopに貼り付けてください。
</div>
""", unsafe_allow_html=True)


# =============================================================================
# クライアント選択
# =============================================================================
try:
    clients = get_clients_list()
except Exception:
    clients = []

client_name = st.selectbox(
    "対象クライアントを選択（プロンプトに自動挿入されます）",
    options=["（選択してください）"] + clients,
    index=0
)

if client_name == "（選択してください）":
    client_name = "〇〇"

st.divider()


# =============================================================================
# プロンプトカード生成ヘルパー
# =============================================================================
def prompt_card(title: str, description: str, prompt_text: str,
                auto_actions: list, time_estimate: str, key: str):
    """プロンプトカードを表示"""
    st.markdown(f'<div class="prompt-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="prompt-desc">{description}</div>', unsafe_allow_html=True)

    st.code(prompt_text, language=None)

    actions_html = "<br>".join([f"・{a}" for a in auto_actions])
    st.markdown(f"""
    <div class="auto-actions">
        <strong>💡 Claudeが自動で行うこと:</strong><br>
        {actions_html}<br><br>
        🕐 所要時間: {time_estimate}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")


# =============================================================================
# タブ別プロンプト集
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 日常の支援",
    "🆘 緊急対応",
    "📋 計画の見直し",
    "🤝 引き継ぎ"
])


# --- タブ1: 日常の支援 ---
with tab1:
    st.markdown("#### 日常業務で使えるプロンプト")

    prompt_card(
        title="🔍 支援パターン分析",
        description="蓄積された支援記録から、効果的だったケア方法のパターンを発見します。",
        prompt_text=f"{client_name}さんの支援記録を分析して、効果的だったケア方法のパターンを教えてください",
        auto_actions=[
            "過去の支援記録をすべて検索",
            "「効果的」と記録された対応のパターンを抽出",
            "状況別・時間帯別の傾向を分析",
            "今後のケア改善案を提案",
        ],
        time_estimate="5〜10分",
        key="pattern"
    )

    prompt_card(
        title="📋 訪問前ブリーフィング",
        description="訪問前に確認すべき情報（禁忌・効果的対応・最近の変化）をまとめます。",
        prompt_text=f"{client_name}さんの訪問前ブリーフィングをお願いします",
        auto_actions=[
            "禁忌事項（避けるべき関わり方）を最優先で表示",
            "効果的だった対応方法を提示",
            "最近の支援記録から変化を確認",
            "緊急連絡先をランク順に表示",
        ],
        time_estimate="3〜5分",
        key="briefing"
    )

    prompt_card(
        title="📝 詳細な支援記録の登録",
        description="物語的なテキストから、AIが自動で構造化データを抽出して登録します。",
        prompt_text=f"{client_name}さんの支援記録を追加してください。今日の訪問で、急な音に驚いてパニックになりましたが、テレビを消して静かにしたら5分で落ち着きました。この対応は効果的でした。",
        auto_actions=[
            "テキストから支援記録（状況・対応・効果）を抽出",
            "禁忌事項の候補を検出",
            "効果的ケア方法として登録提案",
            "データベースに構造化して保存",
        ],
        time_estimate="2〜5分",
        key="log_detail"
    )


# --- タブ2: 緊急対応 ---
with tab2:
    st.markdown("#### 緊急時にすぐ使えるプロンプト")

    st.warning("緊急時は短いプロンプトで素早く情報を取得できます。")

    prompt_card(
        title="🆘 パニック・緊急対応",
        description="パニック状態やSOS時に、禁忌→対処→連絡先の順で即座に情報を取得します。",
        prompt_text=f"{client_name}さんがパニック状態です",
        auto_actions=[
            "⛔ 禁忌事項を最優先で表示（二次被害防止）",
            "✅ 効果的な対処法を提示",
            "📞 緊急連絡先をランク順に表示",
            "🏥 かかりつけ医の情報を表示",
        ],
        time_estimate="1〜2分",
        key="sos"
    )

    prompt_card(
        title="🏥 医療緊急時",
        description="意識不明・けいれん・出血などの医療緊急時の情報を取得します。",
        prompt_text=f"{client_name}さんが倒れました。救急情報を教えてください",
        auto_actions=[
            "血液型・既往症・服薬情報を表示",
            "かかりつけ医の連絡先",
            "アレルギー情報",
            "緊急連絡先と法的代理人の情報",
        ],
        time_estimate="1〜2分",
        key="medical"
    )


# --- タブ3: 計画の見直し ---
with tab3:
    st.markdown("#### 支援計画の見直し・将来の備え")

    prompt_card(
        title="🏠 親の機能不全シナリオ（レジリエンス）",
        description="親が入院・介護状態になった場合に必要な代替支援を事前に検討します。",
        prompt_text=f"{client_name}さんのお母さんが入院した場合、どのような代替支援が必要か提案してください",
        auto_actions=[
            "親が現在担っている役割（食事・通院同行など）を特定",
            "各役割の代替手段（サービス・人物）を提示",
            "優先順位付きの対応計画を提案",
            "必要な手続きのチェックリストを生成",
        ],
        time_estimate="10〜15分",
        key="parent_down"
    )

    prompt_card(
        title="📅 更新期限チェック",
        description="手帳・受給者証の更新期限を確認し、対応の優先順位を提案します。",
        prompt_text="今後90日以内に更新が必要な手帳・受給者証を確認してください",
        auto_actions=[
            "全クライアントの証明書期限を一括チェック",
            "緊急度で3段階に分類（7日/30日/90日）",
            "各証明書の更新手続き手順を提示",
            "65歳問題（介護保険移行）の該当者を検出",
        ],
        time_estimate="5〜10分",
        key="renewal"
    )

    prompt_card(
        title="🔄 事業所の代替検索",
        description="現在利用中のサービスの代替事業所を、口コミ情報を含めて検索します。",
        prompt_text=f"{client_name}さんの生活介護事業所の代替を探してください",
        auto_actions=[
            "現在利用中のサービスを確認",
            "同種の空きがある事業所を検索",
            "口コミ・評価情報を確認",
            "本人の特性に合った事業所を提案",
        ],
        time_estimate="5〜10分",
        key="alternative"
    )


# --- タブ4: 引き継ぎ ---
with tab4:
    st.markdown("#### 担当者交代・情報共有")

    prompt_card(
        title="🤝 担当者引き継ぎサマリー",
        description="担当者交代時に新担当者に渡す情報を、安全優先で自動生成します。",
        prompt_text=f"{client_name}さんの引き継ぎサマリーを作成してください",
        auto_actions=[
            "⛔ 避けるべき関わり方を最優先で記載",
            "⚠️ 経済的リスクがあれば警告",
            "✅ 効果的だった関わり方をパターンで提示",
            "📞 連携機関・キーパーソンの一覧",
            "📋 法的基盤（手帳・後見人）の確認",
        ],
        time_estimate="10〜15分",
        key="handover"
    )

    prompt_card(
        title="📊 エコマップの作成",
        description="クライアントの支援ネットワークを図で可視化します。",
        prompt_text=f"{client_name}さんのエコマップ（支援関係図）を作成してください",
        auto_actions=[
            "キーパーソン・支援機関を一覧化",
            "関係性の強弱を可視化",
            "支援の空白地帯を特定",
            "Mermaid形式またはSVG形式で出力",
        ],
        time_estimate="5〜10分",
        key="ecomap"
    )


# =============================================================================
# フッター
# =============================================================================
st.divider()
st.markdown("### 💡 Claude Desktopの設定方法")
st.markdown("""
1. **Claude Desktop** アプリを開く
2. 設定から **MCP サーバー** を有効化
3. `neo4j` MCP と `neo4j-livelihood` MCP の接続を確認
4. 上のプロンプトをコピーして会話を始める

MCP接続の詳細は、プロジェクト内の `README.md` を参照してください。
""")
