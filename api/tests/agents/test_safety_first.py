from app.agents.safety_first import is_emergency


def test_crisis_detection():
    """現在進行中の危機 → Safety First"""
    assert is_emergency("助けて！田中さんが倒れた")
    assert is_emergency("SOS 山田健太")
    assert is_emergency("発作が起きた")
    assert is_emergency("田中さんがパニック中です")


def test_inquiry_goes_to_gemini():
    """情報照会 → Gemini に回す（Safety First を発動しない）"""
    assert not is_emergency("緊急連絡先を教えてください")
    assert not is_emergency("山田健太さんの緊急連絡先を調べてください")
    assert not is_emergency("禁忌事項の一覧を確認したい")


def test_general_goes_to_gemini():
    """一般的な発言 → Gemini"""
    assert not is_emergency("今日の支援記録を登録して")
    assert not is_emergency("こんにちは")
    assert not is_emergency("山田健太さんの様子を教えて")
