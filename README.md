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

## ✨ 特徴

- **物語形式での入力**: フォームではなく、ヒアリング内容をそのまま入力
- **AI自動構造化**: Gemini 2.0がテキストからデータを抽出
- **ファイルアップロード対応**: Word/Excel/PDF/テキストファイルから直接読み込み
- **自然言語検索**: Claude Desktopから「〇〇さんの禁忌事項は？」と質問可能
- **Safety First**: 緊急時は禁忌事項を最優先で返答

## 🛠️ 技術スタック

- **データベース**: Neo4j 5.15（グラフDB）
- **AI**: Google Gemini 2.0 Flash（構造化）、Claude Desktop（検索）
- **バックエンド**: Python 3.12+、MCP（Model Context Protocol）
- **フロントエンド**: Streamlit
- **パッケージ管理**: uv

## 📁 プロジェクト構成

```
neo4j-agno-agent/
├── app_narrative.py       # メインUI（Streamlit）
├── server.py              # MCPサーバー（Claude Desktop用）
├── lib/                   # 共通ライブラリ
│   ├── __init__.py
│   ├── db_operations.py   # Neo4j操作
│   ├── ai_extractor.py    # AI構造化
│   ├── utils.py           # ユーティリティ
│   └── file_readers.py    # ファイル読み込み
├── docker-compose.yml     # Neo4jコンテナ設定
├── pyproject.toml         # 依存関係
└── .env                   # 環境変数（非公開）
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
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
GEMINI_API_KEY=your_gemini_api_key
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
uv run streamlit run app_narrative.py
```

ブラウザで http://localhost:8501 にアクセス

## 📖 使い方

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

計画相談支援専門員として、知的障害・発達障害のある方の支援に携わる中で開発しました。

---

**「親亡き後」の不安を、テクノロジーで少しでも和らげたい。**
# neo4j-agno-agent
