# 設定テンプレート

Claude Desktop の設定ファイルテンプレートです。

## テンプレート一覧

| ファイル | 方式 | 対象ユーザー |
|---------|------|------------|
| `claude_desktop_config.skills.json` | Skills + Neo4j MCP | 推奨（上級者向け） |
| `claude_desktop_config.mcp.json` | レガシー MCP Server | Docker利用者向け |

## 使い方

### Skills方式（推奨）

1. `setup.sh` を実行してSkillsをインストール
2. `claude_desktop_config.skills.json` の内容を Claude Desktop の設定に追加
3. Neo4j を起動: `docker-compose up -d`

設定ファイルの場所:
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### レガシーMCP方式

1. `claude_desktop_config.mcp.json` の `/PATH/TO/` をプロジェクトの実際のパスに置換
2. `YOUR_GEMINI_API_KEY` を Gemini API キーに置換
3. Claude Desktop の設定に追加

## 注意

- 既に Claude Desktop の設定ファイルに他の MCP サーバーが登録されている場合は、`mcpServers` オブジェクト内にマージしてください
- 両方の方式を同時に使用することも可能ですが、機能が重複するため推奨しません
