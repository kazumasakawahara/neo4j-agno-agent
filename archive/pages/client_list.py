"""
クライアント一覧
検索・フィルタ・詳細展開
"""

import streamlit as st
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.db_new_operations import (
    get_clients_list_extended,
    get_client_detail,
    get_client_stats,
)

# =============================================================================
# カスタムCSS
# =============================================================================
st.markdown("""
<style>
    .client-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-left: 6px;
    }
    .badge-ng { background: #FFEBEE; color: #C62828; }
    .badge-care { background: #E8F5E9; color: #2E7D32; }
    .badge-cert { background: #E3F2FD; color: #1565C0; }
    .detail-section {
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .detail-section:last-child {
        border-bottom: none;
    }
    .detail-title {
        font-weight: 600;
        font-size: 0.85rem;
        color: #495057;
        margin-bottom: 4px;
    }
    .ng-item {
        background: #FFF5F5;
        border-left: 3px solid #F44336;
        padding: 6px 10px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 0.88rem;
    }
    .care-item {
        background: #F5FFF5;
        border-left: 3px solid #4CAF50;
        padding: 6px 10px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 0.88rem;
    }
    .kp-item {
        padding: 4px 0;
        font-size: 0.88rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# ヘッダー
# =============================================================================
st.markdown("## 👥 クライアント一覧")

# 検索
search_query = st.text_input(
    "🔍 名前で検索",
    placeholder="クライアント名を入力...",
    label_visibility="collapsed"
)

st.divider()

# =============================================================================
# クライアント一覧取得
# =============================================================================
try:
    clients = get_clients_list_extended(include_pii=True)
except Exception as e:
    st.error(f"データベース接続エラー: {e}")
    clients = []

if not clients:
    st.info("登録されたクライアントがいません。「初期登録」からクライアントを登録してください。")
    st.stop()

# フィルタリング
if search_query:
    filtered = [
        c for c in clients
        if search_query.lower() in (c.get('name', '') or '').lower()
        or search_query.lower() in (c.get('kana', '') or '').lower()
    ]
else:
    filtered = clients

st.caption(f"{len(filtered)}名 表示中（全{len(clients)}名）")


# =============================================================================
# クライアントカード
# =============================================================================
def calc_age(dob):
    """生年月日から年齢を計算"""
    if not dob:
        return None
    try:
        if hasattr(dob, 'year'):
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None
    except Exception:
        return None


for client in filtered:
    name = client.get('name', '不明')
    kana = client.get('kana', '')
    display_code = client.get('displayCode', '')

    # サブヘッダー情報
    header_parts = [f"**{name}**"]
    if kana:
        header_parts.append(f"（{kana}）")
    if display_code:
        header_parts.append(f" `{display_code}`")

    header = " ".join(header_parts)

    with st.expander(header, expanded=False):
        # 詳細データ取得
        try:
            detail = get_client_detail(name)
        except Exception:
            st.warning("詳細情報の取得に失敗しました")
            continue

        basic = detail.get('basic', {})
        ng_actions = detail.get('ng_actions', [])
        care_prefs = detail.get('care_prefs', [])
        key_persons = detail.get('key_persons', [])
        recent_logs = detail.get('recent_logs', [])

        # --- 基本情報 ---
        age = calc_age(basic.get('dob'))
        info_parts = []
        if age is not None:
            info_parts.append(f"{age}歳")
        if basic.get('bloodType'):
            info_parts.append(f"血液型: {basic['bloodType']}")

        conditions = [c for c in basic.get('conditions', []) if c]
        if conditions:
            info_parts.append(f"特性: {', '.join(conditions)}")

        if info_parts:
            st.caption(" ｜ ".join(info_parts))

        # バッジ
        badges_html = ""
        if ng_actions:
            badges_html += f'<span class="badge badge-ng">⛔ 禁忌 {len(ng_actions)}件</span>'
        if care_prefs:
            badges_html += f'<span class="badge badge-care">✅ ケア推奨 {len(care_prefs)}件</span>'

        certs = [c for c in basic.get('certificates', []) if c.get('type')]
        if certs:
            badges_html += f'<span class="badge badge-cert">📜 証明書 {len(certs)}件</span>'

        if badges_html:
            st.markdown(badges_html, unsafe_allow_html=True)

        # --- 禁忌事項 ---
        if ng_actions:
            st.markdown('<div class="detail-section">', unsafe_allow_html=True)
            st.markdown('<div class="detail-title">⛔ 禁忌事項（避けるべき関わり方）</div>',
                        unsafe_allow_html=True)
            for ng in ng_actions:
                reason = f" — {ng['reason']}" if ng.get('reason') else ""
                st.markdown(
                    f'<div class="ng-item"><strong>{ng["action"]}</strong>{reason}</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # --- 効果的ケア ---
        if care_prefs:
            st.markdown('<div class="detail-section">', unsafe_allow_html=True)
            st.markdown('<div class="detail-title">✅ 効果的なケア方法</div>',
                        unsafe_allow_html=True)
            for cp in care_prefs:
                cat = f"[{cp['category']}] " if cp.get('category') else ""
                st.markdown(
                    f'<div class="care-item">{cat}{cp["instruction"]}</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # --- 緊急連絡先 ---
        if key_persons:
            st.markdown('<div class="detail-section">', unsafe_allow_html=True)
            st.markdown('<div class="detail-title">📞 緊急連絡先</div>',
                        unsafe_allow_html=True)
            for kp in key_persons:
                rank = kp.get('rank', '-')
                rel = f"（{kp['relationship']}）" if kp.get('relationship') else ""
                phone = kp.get('phone', '未登録')
                st.markdown(
                    f'<div class="kp-item">{rank}位: <strong>{kp["name"]}</strong>{rel} {phone}</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # --- 最近の支援記録 ---
        if recent_logs:
            st.markdown('<div class="detail-section">', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-title">📝 最近の支援記録（直近{len(recent_logs)}件）</div>',
                        unsafe_allow_html=True)
            for log in recent_logs:
                d = log.get('date', '?')
                eff = log.get('effectiveness', '')
                eff_icon = "✅" if eff == 'Effective' else "⚠️" if eff == 'Ineffective' else "—"
                sit = log.get('situation', '')
                sup = log.get('supporter', '')
                st.caption(f"{d} ｜ {eff_icon} {sit} ｜ 記録者: {sup}")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- 証明書 ---
        if certs:
            st.markdown('<div class="detail-section">', unsafe_allow_html=True)
            st.markdown('<div class="detail-title">📜 手帳・証明書</div>',
                        unsafe_allow_html=True)
            for cert in certs:
                grade = f" ({cert['grade']})" if cert.get('grade') else ""
                renewal = ""
                if cert.get('renewal'):
                    renewal = f" ｜ 更新期限: {cert['renewal']}"
                st.caption(f"・{cert['type']}{grade}{renewal}")
            st.markdown('</div>', unsafe_allow_html=True)
