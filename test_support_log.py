"""
支援記録機能のテストスクリプト
使用駆動開発: シナリオベースでの動作検証
"""

from lib.ai_extractor import extract_from_text
from lib.db_operations import register_to_database, get_support_logs, discover_care_patterns

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# シナリオA: 日常支援の記録（ヘルパー）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO_A = """
【2024年12月21日 記録者: 田中ヘルパー】

今日、山田健太さんの自宅訪問でした。
お昼ご飯の準備をしていたら、急に外から救急車のサイレンが聞こえて、
健太さんが耳を塞いで固まってしまいました。

以前の引き継ぎで「大きな音が苦手」とは聞いていたので、
すぐにテレビを消して、カーテンを閉めて静かな環境にしました。
5分ほどそっと見守っていたら、自然と落ち着いて食事に戻れました。

無理に声をかけたり触ったりしなくて良かったです。
この対応は効果的だと思います。
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# シナリオB: 緊急対応の振り返り（施設職員）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO_B = """
【2024年12月20日 佐藤施設長】

昨日の夜、佐々木真理さんが突然パニックを起こしました。
新人スタッフの鈴木さんが、真理さんの後ろから「お風呂の時間ですよ」と
肩を叩いたのがきっかけでした。

真理さんは自傷行為（頭を壁に打ち付ける）を始めてしまい、
ベテランの伊藤さんが駆けつけて、真理さんの視界に入る位置から
静かに「大丈夫だよ」と声をかけ続けました。
10分ほどで落ち着きましたが、額に軽い打撲ができてしまいました。

【重要】真理さんには絶対に後ろから声をかけたり触ったりしてはいけません。
これは生命に関わる禁忌です。必ず視界に入ってから、ゆっくり話しかけること。

全スタッフに再度周知します。
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# シナリオC: 親御さんからの包括的な情報提供
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO_C = """
【2024年12月15日 記録者: 母】

息子の健太は、急な予定変更があるとフリーズします。
その時は5分ほど静かに待ってあげると落ち着きます。

絶対に大声で急かしたり腕を引っ張ったりしないでください。
パニックが悪化して自傷につながります。

あと、食事の時は必ずテレビを消してください。
気が散って食べなくなります。

水遊びが大好きで、プールに行くと3時間でも遊んでいます。
落ち込んでいる時は、お風呂に長めに入れてあげると機嫌が良くなります。

療育手帳はA1で、来年の6月に更新です。
緊急時は私の携帯に連絡してください: 090-1234-5678
私が出られない時は、弟の太郎（080-9876-5432）に連絡お願いします。
"""


def test_scenario(scenario_text: str, scenario_name: str):
    """
    シナリオをテスト

    Args:
        scenario_text: テストするテキスト
        scenario_name: シナリオ名
    """
    print(f"\n{'='*60}")
    print(f"  {scenario_name}")
    print(f"{'='*60}\n")

    # AI抽出
    print("🤖 AIで構造化中...")
    extracted_data = extract_from_text(scenario_text)

    if not extracted_data:
        print("❌ 抽出失敗")
        return

    print("✅ 構造化完了\n")

    # 結果表示
    import json
    print("📋 抽出結果:")
    print(json.dumps(extracted_data, ensure_ascii=False, indent=2))

    # データベース登録
    print("\n💾 データベースに登録中...")
    try:
        register_to_database(extracted_data)
        print("✅ 登録完了")

        # 支援記録が登録されていれば表示
        if extracted_data.get('supportLogs'):
            client_name = extracted_data['client']['name']
            print(f"\n📊 {client_name}さんの支援記録:")
            logs = get_support_logs(client_name, limit=5)
            for log in logs:
                print(f"  - {log['日付']}: {log['状況']} → {log['効果']}")
                print(f"    対応: {log['対応'][:50]}...")

    except Exception as e:
        print(f"❌ 登録エラー: {e}")


def test_pattern_discovery():
    """
    パターン発見機能のテスト
    """
    print(f"\n{'='*60}")
    print(f"  パターン発見テスト")
    print(f"{'='*60}\n")

    # 山田健太さんのパターンを発見
    print("🔍 山田健太さんの効果的なケアパターンを発見中...")
    patterns = discover_care_patterns("山田健太", min_frequency=1)

    if patterns:
        print(f"✅ {len(patterns)}件のパターンを発見:\n")
        for p in patterns:
            print(f"  📌 {p['状況']}")
            print(f"     対応: {p['対応方法']}")
            print(f"     効果的だった回数: {p['効果的だった回数']}回\n")
    else:
        print("⚠️ パターンが見つかりませんでした（記録数が少ない可能性）")


if __name__ == "__main__":
    print("\n🚀 支援記録機能テスト開始")
    print("=" * 60)

    # 各シナリオをテスト
    test_scenario(SCENARIO_A, "シナリオA: 日常支援記録")
    test_scenario(SCENARIO_B, "シナリオB: 緊急対応記録")
    test_scenario(SCENARIO_C, "シナリオC: 包括的情報提供")

    # パターン発見テスト
    test_pattern_discovery()

    print("\n" + "=" * 60)
    print("✅ テスト完了")
    print("=" * 60)
