# クイックスタートガイド

5分で始められるセットアップ手順です。

---

## 前提条件

| ツール | 必須 | 用途 |
|-------|------|------|
| Docker Desktop | ○ | Neo4j データベース |
| Claude Desktop | ○ | AI 分析・操作 |
| Node.js (npx) | ○ | Neo4j MCP サーバー |
| Git | △ | リポジトリの取得 |

---

## ステップ 1: リポジトリの取得

```bash
git clone https://github.com/YOUR_USERNAME/neo4j-agno-agent.git
cd neo4j-agno-agent
```

---

## ステップ 2: セットアップの実行

```bash
chmod +x setup.sh
./setup.sh
```

このスクリプトが以下を実行します:

1. **Neo4j の起動** — Docker コンテナでデータベースを立ち上げ
2. **Skills のインストール** — `claude-skills/` から `~/.claude/skills/` にシンボリックリンクを作成
3. **設定ガイダンスの表示** — 次に行うべきことを案内

> Neo4j のブラウザ UI は http://localhost:7474 でアクセスできます（認証: neo4j / password）

---

## ステップ 3: Claude Desktop の設定

Claude Desktop の設定ファイルを開きます:

**Mac:**
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

以下の内容を追加（または `configs/claude_desktop_config.skills.json` からコピー）:

```json
{
  "mcpServers": {
    "neo4j": {
      "command": "npx",
      "args": ["-y", "@anthropic/neo4j-mcp-server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
      }
    }
  }
}
```

> 既に他の MCP サーバーが設定されている場合は、`mcpServers` オブジェクト内に `"neo4j": {...}` を追加してください。

---

## ステップ 4: Claude Desktop の再起動

設定を保存した後、Claude Desktop を完全に終了して再起動します。

起動後、ツールアイコンに `neo4j` が表示されていれば成功です。

---

## 動作確認

Claude Desktop で以下のように話しかけてみましょう:

```
データベースの統計情報を教えて
```

初回は空のデータベースなので、ダミーデータを登録してみましょう:

```
テスト用のクライアント「田中太郎」さんを登録して。
生年月日は1990年4月15日、血液型はA型。
```

---

## 2つのデータベースを使う場合

生活困窮者自立支援（livelihood-support）も使う場合は、2つ目の Neo4j インスタンスが必要です。

### docker-compose.override.yml を作成:

```yaml
services:
  neo4j-livelihood:
    image: neo4j:5.15-community
    container_name: livelihood-db-neo4j
    ports:
      - "7475:7474"
      - "7688:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_server_memory_pagecache_size=512M
      - NEO4J_server_memory_heap_initial__size=512M
      - NEO4J_server_memory_heap_max__size=512M
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - ./neo4j_livelihood_data:/data
      - ./neo4j_livelihood_logs:/logs
    restart: unless-stopped
```

### Claude Desktop 設定に追加:

```json
{
  "mcpServers": {
    "neo4j": {
      "command": "npx",
      "args": ["-y", "@anthropic/neo4j-mcp-server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
      }
    },
    "neo4j-livelihood": {
      "command": "npx",
      "args": ["-y", "@anthropic/neo4j-mcp-server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7688",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password"
      }
    }
  }
}
```

---

## Skills の一覧

セットアップで以下の 5 つの Skills がインストールされます:

| Skill | 用途 | Neo4j ポート |
|-------|------|-------------|
| `neo4j-support-db` | 障害福祉クライアント管理 | 7687 |
| `livelihood-support` | 生活困窮者自立支援 | 7688 |
| `provider-search` | 事業所検索・口コミ | 7687 |
| `emergency-protocol` | 緊急時対応プロトコル | 7687（読取専用）|
| `ecomap-generator` | エコマップ（支援関係図）生成 | 7687 |

---

## よくある質問

### Q: Skills方式とMCP方式の違いは？

**Skills方式（推奨）**:  Claude が SKILL.md のテンプレートに従い、汎用 neo4j MCP 経由で Cypher を実行します。軽量でメンテナンスが容易です。

**MCP方式（レガシー）**: `server.py` が 40+ のカスタムツールを提供します。Python + uv + Gemini API キーが必要です。

### Q: npx コマンドでエラーが出る

Node.js がインストールされていることを確認してください:
```bash
node --version  # v18以上推奨
npm --version
```

### Q: Neo4j に接続できない

```bash
# コンテナの状態確認
docker ps

# ログ確認
docker logs support-db-neo4j

# 再起動
docker compose restart neo4j
```

---

## 次のステップ

- [ADVANCED_USAGE.md](./ADVANCED_USAGE.md) — Skills の詳細な使い方とプロンプト例
- [Neo4j Browser](http://localhost:7474) — データの直接確認・操作
