from app.agents.safety_first import is_emergency


def test_emergency_detection():
    assert is_emergency("田中さんがパニックを起こしている")
    assert is_emergency("SOS 助けて")
    assert is_emergency("発作が起きた")


def test_non_emergency():
    assert not is_emergency("今日の支援記録を登録して")
    assert not is_emergency("こんにちは")
