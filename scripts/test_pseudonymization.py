#!/usr/bin/env python
"""
仮名化機能テストスクリプト

仮名化モジュールと関連APIの動作確認を行います。

使用方法:
    cd neo4j-agno-agent
    uv run python scripts/test_pseudonymization.py

テスト内容:
    1. ID生成関数のテスト
    2. クライアント解決関数のテスト
    3. 一覧取得関数のテスト
    4. 後方互換性のテスト
"""

import os
import sys

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def test_id_generation():
    """ID生成関数のテスト"""
    print("=" * 60)
    print("📝 テスト 1: ID生成関数")
    print("=" * 60)

    from lib.pseudonymization import generate_client_id, generate_display_code

    # clientId 生成テスト
    client_id1 = generate_client_id()
    client_id2 = generate_client_id()

    print(f"  生成された clientId #1: {client_id1}")
    print(f"  生成された clientId #2: {client_id2}")

    assert client_id1.startswith("c-"), "clientId は 'c-' で始まる必要があります"
    assert len(client_id1) == 10, "clientId は 10文字です（c- + 8文字）"
    assert client_id1 != client_id2, "clientId はユニークである必要があります"
    print("  ✅ clientId 生成: OK")

    # displayCode 生成テスト
    display_code1 = generate_display_code(1)
    display_code2 = generate_display_code(10)
    display_code3 = generate_display_code(999)

    print(f"  生成された displayCode: {display_code1}, {display_code2}, {display_code3}")

    assert display_code1 == "A-001", f"期待: A-001, 実際: {display_code1}"
    assert display_code2 == "A-010", f"期待: A-010, 実際: {display_code2}"
    assert display_code3 == "A-999", f"期待: A-999, 実際: {display_code3}"
    print("  ✅ displayCode 生成: OK")

    print()
    return True


def test_client_resolution():
    """クライアント解決関数のテスト"""
    print("=" * 60)
    print("📝 テスト 2: クライアント解決関数")
    print("=" * 60)

    from lib.db_operations import (
        resolve_client,
        get_clients_list,
        get_clients_list_extended,
        match_client_clause,
        is_pseudonymization_enabled,
    )

    # 仮名化有効状態の確認
    pseudonymization = is_pseudonymization_enabled()
    print(f"  仮名化スキーマ: {'有効' if pseudonymization else '無効（未マイグレーション）'}")

    # クライアント一覧取得
    clients = get_clients_list()
    print(f"  登録クライアント数: {len(clients)}")

    if not clients:
        print("  ⚠️ クライアントが登録されていません。スキップします。")
        print()
        return True

    # 最初のクライアントで解決テスト
    test_client = clients[0]
    print(f"  テスト対象: {test_client}")

    resolved = resolve_client(test_client)
    if resolved:
        print(f"    → clientId: {resolved.get('clientId', '(なし)')}")
        print(f"    → displayCode: {resolved.get('displayCode', '(なし)')}")
        print(f"    → name: {resolved.get('name', '(なし)')}")
        print("  ✅ 名前での解決: OK")
    else:
        print("  ⚠️ クライアント解決に失敗しました")

    # 拡張一覧取得テスト
    extended = get_clients_list_extended(include_pii=True)
    print(f"  拡張一覧（PII含む）: {len(extended)} 件")
    if extended:
        sample = extended[0]
        print(f"    サンプル: {sample}")

    extended_no_pii = get_clients_list_extended(include_pii=False)
    print(f"  拡張一覧（PII除外）: {len(extended_no_pii)} 件")
    if extended_no_pii:
        sample = extended_no_pii[0]
        print(f"    サンプル: {sample}")
        # 名前が含まれていないことを確認
        assert 'name' not in sample or sample.get('name') is None, "PII除外時に名前が含まれています"
    print("  ✅ 拡張一覧取得: OK")

    # マッチ句生成テスト
    match_clause, params = match_client_clause(test_client)
    print(f"  マッチ句: {match_clause}")
    print(f"  パラメータ: {params}")
    print("  ✅ マッチ句生成: OK")

    print()
    return True


def test_backward_compatibility():
    """後方互換性のテスト"""
    print("=" * 60)
    print("📝 テスト 3: 後方互換性")
    print("=" * 60)

    from lib.db_operations import get_clients_list, get_support_logs, get_client_stats

    # 既存のAPI関数が動作することを確認
    try:
        clients = get_clients_list()
        print(f"  get_clients_list(): {len(clients)} 件 ✅")
    except Exception as e:
        print(f"  get_clients_list(): エラー ❌ - {e}")
        return False

    try:
        stats = get_client_stats()
        print(f"  get_client_stats(): {stats.get('client_count', 0)} クライアント ✅")
    except Exception as e:
        print(f"  get_client_stats(): エラー ❌ - {e}")
        return False

    if clients:
        try:
            logs = get_support_logs(clients[0], limit=5)
            print(f"  get_support_logs(): {len(logs)} 件 ✅")
        except Exception as e:
            print(f"  get_support_logs(): エラー ❌ - {e}")
            return False

    print("  ✅ 後方互換性: OK")
    print()
    return True


def main():
    print()
    print("🔐 仮名化機能テスト")
    print("=" * 60)
    print()

    results = []

    # テスト 1: ID生成
    try:
        results.append(("ID生成", test_id_generation()))
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        results.append(("ID生成", False))

    # テスト 2: クライアント解決
    try:
        results.append(("クライアント解決", test_client_resolution()))
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        results.append(("クライアント解決", False))

    # テスト 3: 後方互換性
    try:
        results.append(("後方互換性", test_backward_compatibility()))
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        results.append(("後方互換性", False))

    # 結果サマリー
    print("=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 すべてのテストに合格しました！")
    else:
        print("⚠️ 一部のテストに失敗しました。")

    print()
    print("=" * 60)
    print("📝 次のステップ")
    print("=" * 60)
    print("  1. マイグレーション実行:")
    print("     uv run python scripts/migrate_pseudonymization.py")
    print()
    print("  2. API サーバー起動:")
    print("     uv run python mobile/api_server.py")
    print()
    print("  3. Streamlit UI 起動:")
    print("     uv run streamlit run app_quick_log.py")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
