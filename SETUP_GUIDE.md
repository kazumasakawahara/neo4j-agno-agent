# はじめてのセットアップガイド

このガイドは、プログラミング経験がない方でも「親亡き後支援システム」を自分のパソコンで動かせるように、一歩ずつ丁寧に説明した解説書です。

---

## 1. 準備するもの

このシステムを動かすには、以下のソフトウェアが必要です。

### Docker（ドッカー）の準備
データベース（Neo4j）を動かすためのエンジンです。

**Mac**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) をダウンロードし、「Apple Chip」または「Intel Chip」を選択してインストールしてください。起動後、画面左下に「Engine running」と緑色で表示されれば準備OKです。

**Windows**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) をダウンロードし、インストール後にPCを再起動してください。

### uv（パッケージマネージャー）の準備
Pythonの依存関係を管理するツールです。

**Mac**: ターミナルを開いて以下を実行してください。
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows**: PowerShellを開いて以下を実行してください。
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 2. システムを手に入れる

ターミナル（またはPowerShell）で以下のコマンドを順番に実行します。

```bash
cd ~/Documents
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git
cd neo4j-agno-agent
uv sync
```

---

## 3. 環境設定

`.env` ファイルを作成し、必要な情報を設定します。

```bash
cat > .env << EOF
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
GEMINI_API_KEY=あなたのGeminiAPIキー
EOF
```

---

## 4. システムを起動する

### 手順1: データベースの起動
```bash
docker-compose up -d
```
初回は必要なデータをダウンロードするため、数分かかることがあります。

### 手順2: ダッシュボードの起動
```bash
uv run streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセスすると、ダッシュボードが表示されます。

### ダッシュボードの画面構成

ダッシュボードには4つのセクションがあります：

| セクション | ページ | 説明 |
|:--|:--|:--|
| **ホーム** | ダッシュボード | 統計情報、3層ワークフローの案内、更新期限アラート |
| **記録・登録** | 初期登録 | 生育歴・家族構成・ケア情報の一括入力 |
| | クイック記録 | 日々の支援で気になったことを30秒で記録 |
| **管理** | クライアント一覧 | 登録済みクライアントの検索・詳細確認 |
| **活用** | Claude活用ガイド | Claude Desktopでの高度な分析プロンプト集 |
| | AIチャット | Agno/Geminiによる対話型支援 |

---

## 5. 日常の使い方（3層ワークフロー）

### Layer 1: 初期登録（青）
新しいクライアントの情報をまとめて入力する際に使います。
「記録・登録」→「初期登録」から、テキスト入力やファイルアップロード（Word/Excel/PDF）で情報を登録できます。

### Layer 2: クイック記録（オレンジ）
日々の支援の中で気になったことを短く記録します。
「記録・登録」→「クイック記録」から、30秒で記録を追加できます。

### Layer 3: Claude Desktop（紫）
複雑な分析や提案は、Claude Desktop + MCPに任せます。
「活用」→「Claude活用ガイド」にコピー可能なプロンプト例が用意されています。

---

## 6. スマホでSOSボタンを使う（応用）

本人や支援者がスマホからワンタップでSOSを発信できる機能もあります。

### SOSサーバーの起動
```bash
uv run python mobile/api_server.py
```
ブラウザで `http://localhost:8080/app/` にアクセスすると、SOSボタンが表示されます。

### LINE通知の設定
LINE Messaging APIを利用して緊急時にグループLINEに通知を送れます。
詳細は `sos/README.md` を参照してください。

---

## 7. Claude Desktop との連携（応用）

Claude Desktopを使うと、自然言語でデータベースに問いかけることができます。
セットアップ方法は [docs/ADVANCED_USAGE.md](./docs/ADVANCED_USAGE.md) を参照してください。

---

## 困ったときは？

**Q. エラーが出て動かない**
→ Docker Desktopが起動しているか確認してください。メニューバー（Mac）やタスクトレイ（Windows）にクジラのアイコンがあれば起動しています。

**Q. Neo4jに接続できない**
→ `docker ps` でneo4jコンテナが動いているか確認してください。`.env`のNEO4J_PASSWORDが正しいか確認してください。

**Q. 終了したいときは？**
→ ターミナルで `Ctrl + C` を押すと終了します。

### Windows固有のトラブル

**「WSL 2 installation is incomplete」**: PowerShellを管理者として開き `wsl --update && wsl --set-default-version 2` を実行後、PCを再起動してください。

**「Virtualization must be enabled」**: BIOS/UEFIで仮想化（Intel VT-x / AMD-V）を有効にする必要があります。

---

このガイドが、あなたの「親亡き後支援」活動の一助となれば幸いです。
作成者: Antigravity Team
