# 親亡き後支援データベース（Neo4j Agno Agent）

**Manifesto: Post-Parent Support & Advocacy Graph**

知的障害・発達障害のある方の「親亡き後」を見据えた支援情報を一元管理し、緊急時に必要な情報を即座に取得できるシステムです。

## 🎯 コンセプト

> 「この子のことを一番知っているのは私たち親です。でも、私たちがいなくなったら...」

この切実な声に応えるため、**親御さんの暗黙知**を構造化データとして保存し、支援者が自然言語で検索できるシステムを構築しました。

## 🏗️ 4本柱のデータモデル

| 柱 | 内容 | 例 |
|----|------|-----|
| **第1の柱：本人性** | 基本情報、生育歴、願い | 「水遊びが大好き」「穏やかに暮らしたい」 |
| **第2の柱：ケアの暗黙知** | 特性、禁忌事項、推奨ケア | 「後ろから声をかけるとパニック」 |
| **第3の柱：法的基盤** | 手帳、受給者証、更新日 | 「療育手帳A1、来年6月更新」 |
| **第4の柱：危機管理ネットワーク** | キーパーソン、後見人、医療機関 | 「母が倒れたら弟に連絡」 |

## ✨ 特徴（Autonomous Agent Team）

**Agnoフレームワーク**を用いた自律型エージェントチームが、24時間365日、親御さんの代わりに判断と調整を行います。

1.  **Input Agent（情報構造化）**:
    - 日々のナラティブ（物語）を受け取り、Gemini 2.0を用いて構造化データへ変換。
    - 入力時点で安全性を一次チェック。

2.  **Emergency Watchdog（緊急監視）**:
    - 「SOS」「救急車」などのキーワードを常時監視。
    - **Fast-path機能**: 危険を検知すると、複雑な推論をスキップし、即座に禁忌事項と緊急連絡先を出力。

3.  **Support Agent（代替支援計画）**:
    - **第5の柱（Resilience）**を担う中核エージェント。
    - 親が入院するなど、支援機能が不全になった際、Neo4j知識グラフを探索。
    - 「誰がキーパーソンか」「今の状況で禁忌は何か」を判断し、**代替プラン（Plan B）**を自律的に策定。
    - 人間（ユーザー）に承認を求め、実行に移す（Human-in-the-loop）。

## 🛠️ 技術スタック

-   **Autonomous Agents**: Agno Framework
-   **Database**: Neo4j 5.15 (Graph DB)
-   **AI Models**: Google Gemini 2.0 Flash (Reasoning & Extraction)
-   **Backend**: Python 3.12+, FastAPI
-   **Frontend**: Streamlit, HTML/JS
-   **Package Manager**: uv

## 📁 プロジェクト構成

```
neo4j-agno-agent/
├── agents/                # Agno Autonomous Agents
│   ├── base.py            # Base Agent (Manifesto & Governance)
│   ├── input_agent.py     # Narrative Processing
│   ├── support_agent.py   # Planning & Resilience
│   └── watchdog.py        # Emergency Override (Fast-path)
├── tools/                 # Agent Toolkits
│   ├── neo4j_toolkit.py   # Neo4j Operations
│   └── extraction_toolkit.py # AI Extraction
├── scripts/               # Scripts & Simulations
│   ├── simulate_team.py   # Agent Team Simulation Script
│   └── ...
├── app_narrative.py       # Admin UI (Streamlit)
├── server.py              # MCP Server (Legacy/Claude Integration)
├── mobile/                # Mobile API & App
├── sos/                   # SOS System
├── docker-compose.yml     # Neo4j Config
└── pyproject.toml         # Dependencies
```

## 🚀 セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git
cd neo4j-agno-agent
```

### 2. 環境変数を設定

`.env`ファイルを作成：

```env
# データベース接続
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# AI構造化
GEMINI_API_KEY=your_gemini_api_key

# SOS緊急通知（オプション）
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_GROUP_ID=your_line_group_id

# セキュリティ（本番環境では必須）
# SOSアプリからのアクセスを許可するオリジン（カンマ区切り）
CORS_ORIGINS=https://your-app-domain.com
```

### 3. Neo4jを起動

```bash
docker-compose up -d
```

### 4. 依存関係をインストール

```bash
uv sync
```

### 5. アプリを起動

```bash
# 管理者用データ登録（詳細な登録・編集）
uv run streamlit run app_narrative.py

# モバイル用APIサーバー（アプリ・SOS機能・AI分析）
uv run python mobile/api_server.py
```

- 管理者画面: http://localhost:8501
- モバイルアプリ: http://localhost:8080/app/

### 6. エージェントチームのシミュレーション

自律型エージェントチームの動作を確認するために、シミュレーションスクリプトが用意されています。

```bash
uv run python scripts/simulate_team.py
```

このスクリプトは以下のシナリオを実行します：
1.  **SOS検知**: 「山田花子」さんからの緊急メッセージを受け取る。
2.  **Fast-path発動**: Watchdogが緊急性を検知し、即座にアラートと検索を実行。
3.  **構造化**: Input Agentがナラティブを解析。
4.  **代替計画策定**: Support AgentがNeo4jを検索し、母親（山田花子）への連絡や支援者派遣を含む「Plan B」を策定。
5.  **承認**: ユーザーに実行の許可を求める。

## 📖 使い方

### モバイルアプリ（支援者・本人向け）

現場で「気づき」や「危機」を直感的に入力するWebアプリです。

1. **ナラティブ入力**: 「今日、母が急に倒れて...」のように自然な言葉で入力（音声入力推奨）
2. **リアルタイムAI分析**:
   - **Safety Check**: 入力内容が登録された「禁忌事項（NgAction）」に触れる場合、即座に**Red Alert**を表示。
   - **Resilience Report**: 「親の入院」などの危機的キーワードを検知すると、**「今誰が困るか」「代替手段は何か」**を即座にレポート表示。
3. **かんたん登録**: 確認してボタンを押すだけでDBに記録。

### データ登録（Streamlit UI）

1. **テキスト入力** または **ファイルアップロード** を選択
2. ヒアリング内容や面談記録を入力/アップロード
3. 「AIで構造化する」をクリック
4. 抽出されたデータを確認・修正
5. データベースに登録

### データ検索（Claude Desktop）

Claude Desktopに`support-db`サーバーを設定後、以下のような質問が可能：

- 「山田健太さんの禁忌事項を教えて」
- 「健太さんがパニックを起こしたらどうすれば？」
- 「緊急連絡先は誰？」
- 「更新期限が近い手帳はある？」

## ⚙️ Claude Desktop設定

`claude_desktop_config.json`に以下を追加：

```json
{
  "mcpServers": {
    "support-db": {
      "command": "/path/to/neo4j-agno-agent/.venv/bin/python",
      "args": ["/path/to/neo4j-agno-agent/server.py"]
    }
  }
}
```

## 🔧 MCPサーバー機能

| ツール | 説明 |
|--------|------|
| `search_emergency_info` | 緊急時の情報を優先順位付きで取得 |
| `get_client_profile` | クライアントの全体像を取得 |
| `check_renewal_dates` | 更新期限が近い証明書を検索 |
| `list_clients` | クライアント一覧を取得 |
| `get_database_stats` | データベース統計を取得 |
| `run_cypher_query` | カスタムCypherクエリを実行 |
| `add_support_log` | 物語風テキストから支援記録を自動登録 |
| `get_support_logs` | クライアントの支援記録履歴を取得 |
| `discover_care_patterns` | 効果的なケアパターンを自動発見 |
| `get_audit_logs` | 操作履歴（監査ログ）を取得 |
| `get_client_change_history` | クライアント別の変更履歴を取得 |

## 🔒 監査ログ・バックアップ

### 監査ログ

データの変更履歴を自動記録します（誰が・いつ・何を変更したか）：

```
「山田健太さんの変更履歴を確認」
→ 2024-01-15 田中 CREATE NgAction "後ろから声をかけない"
→ 2024-01-14 佐藤 CREATE Client 基本情報登録
```

### バックアップ

```bash
# 手動バックアップ
./scripts/backup.sh

# 定期バックアップ（cron設定例：毎日AM3時）
0 3 * * * cd /path/to/neo4j-agno-agent && ./scripts/backup.sh
```

バックアップは `neo4j_backup/` ディレクトリに保存され、30日間保持されます。

## 📋 対応ファイル形式

| 形式 | 拡張子 | ライブラリ |
|------|--------|-----------|
| Word文書 | .docx | python-docx |
| Excelファイル | .xlsx | openpyxl |
| PDFファイル | .pdf | pdfplumber |
| テキストファイル | .txt | 標準ライブラリ |

## 🎨 マニフェスト

このシステムは以下の価値を大切にしています：

- **Dignity（尊厳）**: 本人の人格と歴史を尊重
- **Safety（安全）**: 禁忌事項を最優先で保護
- **Continuity（継続性）**: 親亡き後も支援が途切れない
- **Advocacy（権利擁護）**: 本人の声なき声を代弁

## 📄 ライセンス

MIT License

## 👤 開発者

知的障害のあるお子さんを持つ親御さんたちが立ち上げたNPO法人に関わる弁護士として、法的支援の現場で感じた課題を解決するために開発しました。

開発にあたっては、**Gemini 3 Pro（Google）** と **Claude Opus 4.5（Anthropic）** に全面的に支援してもらいました。プログラミングの専門家でなくても、AIの力を借りることで、現場の課題を解決するシステムを構築できる時代になったことを実感しています。

---

**「親亡き後」の不安を、テクノロジーで少しでも和らげたい。**
