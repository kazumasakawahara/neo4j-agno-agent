#!/usr/bin/env python
"""
仮名化マイグレーションスクリプト

既存の Client ノードを仮名化スキーマに移行します。

使用方法:
    cd neo4j-agno-agent
    uv run python scripts/migrate_pseudonymization.py

処理内容:
    1. 各 Client ノードに clientId (UUID) を付与
    2. Identity ノードを作成し、name/dob を移動
    3. HAS_IDENTITY 関係を作成
    4. インデックスを作成

注意:
    - 既に clientId を持つ Client はスキップされます
    - 元の name プロパティは安全のため残されます
    - 本番移行前に必ずバックアップを取ってください
"""

import os
import sys

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from neo4j import GraphDatabase

from lib.pseudonymization import (
    migrate_to_pseudonymized_schema,
    create_name_index,
    list_clients_with_identity,
)

load_dotenv()


def main():
    print("=" * 60)
    print("🔐 仮名化マイグレーション")
    print("=" * 60)
    print()
    print("このスクリプトは既存の Client データを仮名化スキーマに移行します。")
    print()
    print("【変更内容】")
    print("  - Client ノードに clientId (UUID) を付与")
    print("  - Client ノードに displayCode (A-001形式) を付与")
    print("  - Identity ノードを作成（氏名・生年月日を分離）")
    print("  - HAS_IDENTITY 関係を作成")
    print()

    # Neo4j 接続
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    print(f"Neo4j: {uri}")
    print()

    # 確認プロンプト
    confirm = input("実行しますか？ (yes/no): ").strip().lower()
    if confirm != "yes":
        print("キャンセルしました。")
        return

    print()
    print("-" * 60)
    print("マイグレーション開始...")
    print("-" * 60)

    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))

        # 接続テスト
        with driver.session() as session:
            result = session.run("MATCH (c:Client) RETURN count(c) as count").single()
            client_count = result['count']
            print(f"現在の Client 数: {client_count}")

        if client_count == 0:
            print("移行対象の Client がありません。")
            driver.close()
            return

        # インデックス作成
        print()
        print("インデックス作成中...")
        create_name_index(driver)

        # マイグレーション実行
        print()
        print("データ移行中...")
        result = migrate_to_pseudonymized_schema(driver)

        print()
        print("-" * 60)
        print("📊 マイグレーション結果")
        print("-" * 60)
        print(f"  移行成功: {result['migrated']} 件")
        print(f"  スキップ: {result['skipped']} 件")
        print(f"  エラー:   {len(result['errors'])} 件")

        if result['errors']:
            print()
            print("⚠️ エラー詳細:")
            for error in result['errors']:
                print(f"  - {error}")

        # 結果確認
        print()
        print("-" * 60)
        print("📋 移行後のクライアント一覧")
        print("-" * 60)

        clients = list_clients_with_identity(driver, include_pii=True)
        for c in clients[:10]:  # 最初の10件のみ表示
            client_id = c.get('clientId', '(未設定)')
            display_code = c.get('displayCode', '(未設定)')
            name = c.get('name', '(不明)')
            print(f"  {display_code}: {name} ({client_id})")

        if len(clients) > 10:
            print(f"  ... 他 {len(clients) - 10} 件")

        driver.close()

        print()
        print("=" * 60)
        print("✅ マイグレーション完了")
        print("=" * 60)

    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
