# 🧠 発展的運用ガイド: ハイブリッド・オペレーション

このシステムは「自動エージェント」と「手動分析（Claude Desktop）」を組み合わせた**ハイブリッド運用**が可能です。
日々の定型業務はエージェントに任せ、深い分析や意思決定のサポートが必要な時は、あなた自身がAI（Claude）と共にデータベースを探求できます。

---

## 🌓 2つのモード

### 1. 自律エージェントモード (Autonomous Mode)
**「守り」の支援**
*   **役割**: 日々の記録見守り、安全チェック、定型的なSOS対応。
*   **ツール**: `start.bat` / `start.command` で起動する `main.py`。
*   **ユーザー**: 現場の支援者、ご家族。
*   **特徴**: 24時間365日、休まずに監視し、設定されたルール（禁忌など）に従って即座に反応します。

### 2. 分析モード (Analytic Mode)
**「攻め」の支援**
*   **役割**: 傾向分析、プラン策定、過去の類似ケース検索、自由なディスカッション。
*   **ツール**: **Claude Desktop** + MCPサーバー (`server.py`)。
*   **ユーザー**: ケースワーカー、管理者、ケアマネージャー。
*   **特徴**: あなたの「問い」に対して、データベース内の膨大な知識を検索・統合して答えます。

---

## 🛠 Claude Desktop との連携方法

Claude Desktop（Anthropic社公式アプリ）にこのデータベースを接続することで、自然言語でデータを検索・分析できるようになります。

### 手順 1: Claude Desktop のインストール
[Claude Desktop 公式サイト](https://claude.ai/download) からアプリをダウンロード・インストールします。

### 手順 2: 設定ファイルの編集
Claude Desktop の設定ファイルを開きます。

*   **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
*   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

ファイルが存在しない場合は作成し、以下のように記述します。
**※注意: パスはあなたの環境に合わせて書き換えてください。**

#### Mac の設定例
```json
{
  "mcpServers": {
    "post-parent-db": {
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
    "post-parent-db": {
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

### 手順 3: 分析の開始
Claude Desktop を再起動すると、右上の🔌マーク（またはツールアイコン）に `post-parent-db` が表示されます。
これで、以下のような高度な依頼が可能になります。

**分析プロンプトの例:**

> 「山田さんの過去1年間の支援記録を分析して。特にパニックが起きた時の共通点と、効果的だった対応パターンを見つけて。」

> 「新しいショートステイ先を探したい。データベースにある法人の中で、知的障害の受け入れ実績があり、かつ（...）という条件に合う事業所をリストアップして。」

> 「私が記入した『生育歴』のデータを元に、自治体に提出するための『相談支援利用計画案』のドラフトを作成して。」

---

## 🧩 カスタムMCM/Skills の追加

このシステムは **MCP (Model Context Protocol)** に準拠しているため、他のMCPサーバーや、あなたが作成したカスタムツールと組み合わせることができます。

例えば：
- **ウェブ検索MCP**: 最新の福祉制度や法律改正情報をネットから検索し、データベース内のクライアント情報と照らし合わせる。
- **カレンダーMCP**: 抽出した「更新期限」を、Googleカレンダーに自動登録する。
- **Slack/Teams MCP**: 分析結果をチームのチャットに投稿する。

これらを組み合わせることで、単なる「データベース」を超えた、**「専属の敏腕アシスタント」** として機能します。
