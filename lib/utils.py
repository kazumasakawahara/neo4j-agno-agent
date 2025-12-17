"""
親亡き後支援データベース - ユーティリティモジュール
共通ヘルパー関数
"""

import streamlit as st
from datetime import datetime, date


def safe_date_parse(date_str: str) -> date | None:
    """
    日付文字列を安全にパース
    
    Args:
        date_str: YYYY-MM-DD形式の日付文字列
        
    Returns:
        dateオブジェクト、またはパース失敗時はNone
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def init_session_state():
    """Streamlitセッション状態の初期化"""
    if 'step' not in st.session_state:
        st.session_state.step = 'input'  # input → edit → confirm → done
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    if 'edited_data' not in st.session_state:
        st.session_state.edited_data = None
    if 'narrative_text' not in st.session_state:
        st.session_state.narrative_text = ""
    if 'uploaded_file_text' not in st.session_state:
        st.session_state.uploaded_file_text = ""


def reset_session_state():
    """セッション状態をリセット"""
    st.session_state.step = 'input'
    st.session_state.extracted_data = None
    st.session_state.edited_data = None
    st.session_state.narrative_text = ""
    st.session_state.uploaded_file_text = ""


def get_input_example() -> str:
    """入力例テキストを取得"""
    return """健太は1995年3月15日生まれです。血液型はA型。

幼少期は小倉南区の療育センターに通っていました。
水遊びが大好きで、北九州市立特別支援学校のプールでは
とても楽しそうでした。

自閉スペクトラム症と診断されています。
大きな音が苦手で聴覚過敏があります。

【絶対にしてはいけないこと】
・後ろから急に声をかけたり触れたりしないでください。
　パニックになって自分の頭を叩いてしまいます。
・食事中はテレビを絶対につけないでください。
　気が散って食べなくなります。

パニックになった時は、静かな部屋に移動して
背中をゆっくりさすると5分くらいで落ち着きます。
イヤーマフは常にリュックに入っています。

療育手帳はA判定で、来年の6月に更新があります。
障害基礎年金1級を受給しています。

私（母・山田花子 090-1234-5678）が倒れたら、
弟の佐藤一郎（090-8765-4321）に連絡してください。
佐藤は成年後見人になる予定です。

かかりつけは産業医科大学病院の中村先生（精神科）です。

将来は、今の八幡東区のグループホームで
ずっと穏やかに暮らしてほしいと願っています。"""
