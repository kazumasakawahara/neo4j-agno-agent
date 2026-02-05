# 発展的運用ガイド: Claude Desktop との連携

このシステムは、ダッシュボードUIでの記録・管理に加え、**Claude Desktop + MCP**を活用した高度な分析・提案が可能です。

---

## 3層ワークフローにおけるClaude Desktopの位置づけ

| レイヤー | ツール | 役割 |
|:--|:--|:--|
| Layer 1（青） | Streamlit: 初期登録 | 生育歴・家族構成の一括入力 |
| Layer 2（オレンジ） | Streamlit: クイック記録 | 日々の気づきを30秒で記録 |
| **Layer 3（紫）** | **Claude Desktop + MCP** | **分析・提案・複雑な操作** |

Layer 3では、自然言語でデータベースに問いかけ、40以上のMCPツールを使った高度な分析が可能です。

---

## Claude Desktop のセットアップ

### 手順 1: Claude Desktop のインストール
[Claude Desktop 公式サイト](https://claude.ai/download) からアプリをダウンロード・インストールします。

### 手順 2: 設定ファイルの編集

Claude Desktop の設定ファイルを開きます。

- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

ファイルが存在しない場合は作成し、以下のように記述します。
**※パスはあなたの環境に合わせて書き換えてください。**

#### Mac の設定例
```json
{
  "mcpServers": {
    "support-db": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/Users/YOUR_USERNAME/Documents/neo4j-agno-agent/server.py"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password",
        "GEMINI_API_KEY": "あなたのGeminiAPIキー"
      }
    }
  }
}
```

#### Windows の設定例
```json
{
  "mcpServers": {
    "support-db": {
      "command": "cmd.exe",
      "args": [
        "/c",
        "uv run python C:\\Users\\YOUR_USERNAME\\Documents\\neo4j-agno-agent\\server.py"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password",
        "GEMINI_API_KEY": "あなたのGeminiAPIキー"
      }
    }
  }
}
```

### 手順 3: 起動確認
Claude Desktop を再起動すると、ツールアイコンに `support-db` が表示されます。

---

## 主なMCPツール

### 緊急対応
- `search_emergency_info`: 禁忌事項・緊急連絡先を優先順位付きで取得
- `get_visit_briefing`: 訪問前ブリーフィング（NG・効果的な関わり方）

### 日常支援
- `add_support_log`: 物語風テキストから支援記録を自動抽出・登録
- `get_support_logs`: 支援記録履歴の取得
- `discover_care_patterns`: 効果的なケアパターンの自動発見

### 分析・計画
- `get_client_profile`: クライアントの全体像を統合表示
- `get_handover_summary`: 引き継ぎサマリーの生成
- `check_renewal_dates`: 証明書更新期限のチェック
- `find_similar_cases`: 類似ケースの検索
- `find_alternative_providers`: 代替事業所の検索

### 監査
- `get_audit_logs`: 操作履歴の取得
- `get_client_change_history`: クライアント別の変更履歴

---

## プロンプト例

### 日常の支援
```
山田健太さんの最近の支援記録を分析して、効果的だったケアパターンを教えて。
```

```
佐藤さんの訪問前ブリーフィングをお願いします。避けるべき関わり方を最初に教えて。
```

### 緊急対応
```
田中さんがパニックを起こしています。緊急対応情報をください。
```

### 計画の見直し
```
更新期限が近い証明書を全クライアント分チェックして。
```

```
山田さんの代替事業所を探して。現在の就労B型と同じカテゴリで、空きのある事業所を一覧にして。
```

### 引き継ぎ
```
佐藤さんの引き継ぎサマリーを作成して。新しい担当者に渡す用です。
```

---

## MCP Skills の追加

このシステムは MCP（Model Context Protocol）に準拠しているため、他のMCPサーバーと組み合わせることができます。

例えば：
- **ウェブ検索MCP**: 最新の福祉制度や法律改正情報を検索
- **カレンダーMCP**: 更新期限をGoogleカレンダーに自動登録
- **エコマップ生成スキル**: 支援ネットワークを視覚的に可視化

ダッシュボードの「活用」→「Claude活用ガイド」ページにも、コピー可能なプロンプト例が用意されています。
