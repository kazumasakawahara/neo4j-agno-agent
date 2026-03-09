"""
ホームダッシュボード
3層ワークフローの可視化 + 統計 + 期限管理
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.db_new_operations import (
    get_client_stats,
    get_dashboard_stats,
    get_upcoming_renewals,
    is_db_available,
)

# =============================================================================
# カスタムCSS
# =============================================================================
st.markdown("""
<style>
    /* 統計カード */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #4CAF50;
    }
    .stat-number {
        font-size: 2.2rem;
        font-weight: 700;
        color: #212529;
        margin: 4px 0;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #6c757d;
    }

    /* 3層カード共通 */
    .layer-card {
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        border-left: 5px solid;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .layer-card h3 {
        margin: 0 0 8px 0;
        font-size: 1.15rem;
    }
    .layer-card p {
        margin: 4px 0;
        color: #495057;
        font-size: 0.95rem;
    }
    .layer-meta {
        font-size: 0.82rem;
        color: #868e96;
        margin-top: 8px;
    }

    /* レイヤー色 */
    .layer1 { border-left-color: #1565C0; }
    .layer1 h3 { color: #1565C0; }
    .layer2 { border-left-color: #E65100; }
    .layer2 h3 { color: #E65100; }
    .layer3 { border-left-color: #6A1B9A; }
    .layer3 h3 { color: #6A1B9A; }

    /* アラート帯 */
    .alert-banner {
        background: #FFF3E0;
        border: 1px solid #FF9800;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 0.9rem;
    }
    .alert-urgent {
        background: #FFEBEE;
        border-color: #F44336;
    }

    /* 期限リスト */
    .renewal-item {
        padding: 10px 14px;
        border-radius: 8px;
        margin: 6px 0;
        background: white;
        border-left: 4px solid;
        font-size: 0.9rem;
    }
    .renewal-urgent { border-left-color: #F44336; background: #FFF5F5; }
    .renewal-warn { border-left-color: #FF9800; background: #FFFBF0; }
    .renewal-ok { border-left-color: #4CAF50; background: #F5FFF5; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# ヘッダー
# =============================================================================
# デモモードバナー
if os.getenv("DEMO_MODE", "").lower() == "true":
    st.markdown("""
    <div style="background: #FFF8E1; border: 1px solid #FFC107; border-radius: 8px;
                padding: 8px 16px; margin-bottom: 16px; text-align: center; font-size: 0.9rem;">
        🎓 デモ環境 — 表示されているデータは架空のものです
    </div>
    """, unsafe_allow_html=True)

st.markdown("## 支援ダッシュボード")
st.caption("3つのワークレイヤーで効果的に支援を進めましょう")

st.divider()

# =============================================================================
# DB接続チェック
# =============================================================================
db_available = is_db_available()

if not db_available:
    st.warning("データベースに接続できません。Neo4jが起動しているか確認してください。")
    if st.button("🔄 再接続を試みる"):
        st.rerun()

# =============================================================================
# 統計カード
# =============================================================================
try:
    client_stats = get_client_stats()
    dash_stats = get_dashboard_stats()
    client_count = client_stats.get('client_count', 0)
    monthly_logs = dash_stats.get('monthly_logs', 0)
    upcoming_count = dash_stats.get('upcoming_renewals', 0)
    total_ng = dash_stats.get('total_ng_actions', 0)
except Exception as e:
    client_count = monthly_logs = upcoming_count = total_ng = 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">登録クライアント</div>
        <div class="stat-number">{client_count}</div>
        <div class="stat-label">名</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card" style="border-left-color: #1565C0;">
        <div class="stat-label">今月の支援記録</div>
        <div class="stat-number">{monthly_logs}</div>
        <div class="stat-label">件</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    color = "#F44336" if upcoming_count > 0 else "#4CAF50"
    st.markdown(f"""
    <div class="stat-card" style="border-left-color: {color};">
        <div class="stat-label">期限注意(30日以内)</div>
        <div class="stat-number" style="color: {color};">{upcoming_count}</div>
        <div class="stat-label">件</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card" style="border-left-color: #E65100;">
        <div class="stat-label">登録済み禁忌事項</div>
        <div class="stat-number">{total_ng}</div>
        <div class="stat-label">件</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# アラート帯（期限注意があれば表示）
# =============================================================================
if upcoming_count > 0:
    st.markdown(f"""
    <div class="alert-banner alert-urgent">
        ⚠️ <strong>{upcoming_count}件</strong>の証明書が30日以内に更新期限を迎えます。
        下部の「期限が近い証明書」を確認してください。
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# 3つのワークレイヤー
# =============================================================================
st.markdown("### 3つのワークレイヤー")
st.caption("目的に応じて最適なツールを使い分けます")

st.markdown("")

# --- レイヤー1 ---
st.markdown("""
<div class="layer-card layer1">
    <h3>📋 レイヤー1：初期登録（Narrative Archive）</h3>
    <p>新しいクライアントの基本情報・支援計画を構造化して一括入力します。</p>
    <p>Word / Excel / PDF からの取り込みにも対応。AIが自動で情報を抽出します。</p>
    <div class="layer-meta">
        🕐 所要時間: 20〜30分 ｜ 📌 使うタイミング: 新規クライアント受入時
    </div>
</div>
""", unsafe_allow_html=True)

if st.button("📋 初期登録を始める", key="goto_narrative", use_container_width=True):
    st.switch_page("app_narrative.py")

st.markdown("")

# --- レイヤー2 ---
st.markdown("""
<div class="layer-card layer2">
    <h3>⚡ レイヤー2：クイック記録（Quick Log）</h3>
    <p>訪問・支援のあとに「良かったこと」「気になること」を素早く記録します。</p>
    <p>音声入力・モバイル対応。30秒で記録完了。普通の日は記録不要です。</p>
    <div class="layer-meta">
        🕐 所要時間: 30秒〜2分 ｜ 📌 使うタイミング: 毎回の支援後
    </div>
</div>
""", unsafe_allow_html=True)

if st.button("⚡ クイック記録する", key="goto_quicklog", use_container_width=True):
    st.switch_page("app_quick_log.py")

st.markdown("")

# --- レイヤー3 ---
st.markdown("""
<div class="layer-card layer3">
    <h3>🤖 レイヤー3：分析・提案（Claude Desktop）</h3>
    <p>蓄積されたデータをAIが分析し、ケアパターンの発見やリスク検出を行います。</p>
    <p>レジリエンス報告書の生成、担当者引き継ぎ、多機関連携の最適化など。</p>
    <div class="layer-meta">
        🕐 所要時間: 5〜30分 ｜ 📌 使うタイミング: 月1回の振り返り、緊急対応時
    </div>
</div>
""", unsafe_allow_html=True)

if st.button("🤖 Claude活用ガイドを見る", key="goto_claude", use_container_width=True):
    st.switch_page("pages/claude_guide.py")


# =============================================================================
# 期限が近い証明書
# =============================================================================
st.divider()
st.markdown("### 📅 期限が近い証明書")

try:
    renewals = get_upcoming_renewals(days_ahead=90, limit=10)
except Exception:
    renewals = []

if renewals:
    for r in renewals:
        days = r.get('days_left', 999)
        name = r.get('client_name', '不明')
        cert = r.get('cert_type', '不明')
        grade = r.get('grade', '')

        if days <= 7:
            css_class = "renewal-urgent"
            icon = "🔴"
        elif days <= 30:
            css_class = "renewal-warn"
            icon = "🟡"
        else:
            css_class = "renewal-ok"
            icon = "🟢"

        grade_str = f"（{grade}）" if grade else ""
        st.markdown(f"""
        <div class="renewal-item {css_class}">
            {icon} <strong>{name}</strong> — {cert}{grade_str}
            ｜ 残り <strong>{days}日</strong>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("90日以内に更新が必要な証明書はありません。")
