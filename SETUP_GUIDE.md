# はじめてのセットアップガイド

このガイドは、プログラミング経験がない方でも「親なき後支援データベース」を自分のパソコンで動かせるように、一歩ずつ丁寧に説明しています。

> **対象**: Windows / Mac をお使いの方
> **所要時間**: 初回セットアップ 約30〜60分（ダウンロード時間を含む）

---

## 目次

1. [このシステムについて](#1-このシステムについて)
2. [必要なソフトウェアの準備](#2-必要なソフトウェアの準備)
3. [APIキーの取得](#3-apiキーの取得)
4. [システムのダウンロード](#4-システムのダウンロード)
5. [環境設定](#5-環境設定)
6. [システムの起動](#6-システムの起動)
7. [画面の使い方](#7-画面の使い方)
8. [システムの停止・再起動](#8-システムの停止再起動)
9. [困ったときは（トラブルシューティング）](#9-困ったときはトラブルシューティング)

---

## 1. このシステムについて

「親亡き後支援データベース」は、知的障害・発達障害のある方の支援情報をグラフデータベースで管理するシステムです。ご家族の暗黙知（「この子にはこうすると落ち着く」「絶対にこれはしないで」など）を構造化し、緊急時やケア引き継ぎ時にすぐ参照できるようにします。

### システム構成

| 構成要素 | 技術 | 役割 |
|----------|------|------|
| 画面（フロントエンド） | Next.js + shadcn/ui | ブラウザで操作する業務画面 |
| サーバー（バックエンド） | FastAPI | データの処理・AIとの連携 |
| データベース | Neo4j (Docker) | 支援情報の保存・検索 |
| AI | Gemini / Claude / Ollama | チャット・テキスト構造化・検索 |

---

## 2. 必要なソフトウェアの準備

以下の5つのソフトウェアを順番にインストールします。すべて無料です。

### 2-1. Git（ギット）のインストール

システムのソースコードをダウンロードするために使います。

<details>
<summary><b>Windows の場合（クリックで開く）</b></summary>

1. [Git for Windows](https://gitforwindows.org/) にアクセス
2. **「Download」** ボタンをクリック
3. ダウンロードされた `.exe` ファイルをダブルクリック
4. インストーラーが起動します。**すべてデフォルト設定のまま「Next」を押し続けて**ください
5. 最後に **「Install」** → **「Finish」** をクリック

**確認方法**: スタートメニューから **「PowerShell」** を検索して開き、以下を入力して Enter:
```powershell
git --version
```
`git version 2.xx.x` のように表示されればOKです。

</details>

<details>
<summary><b>Mac の場合（クリックで開く）</b></summary>

1. **ターミナル**を開きます（Spotlight検索で「ターミナル」と入力）
2. 以下を入力して Enter:
```bash
git --version
```
3. まだインストールされていない場合、「コマンドラインデベロッパーツールをインストールしますか？」と聞かれるので **「インストール」** をクリック

</details>

---

### 2-2. Docker Desktop（ドッカー デスクトップ）のインストール

データベース（Neo4j）を動かすためのソフトウェアです。

<details>
<summary><b>Windows の場合（クリックで開く）</b></summary>

#### 事前準備: WSL2 のセットアップ

1. スタートメニューで **「PowerShell」** を検索 → **右クリック** → **「管理者として実行」**
2. 以下のコマンドを入力して Enter:
```powershell
wsl --install
```
3. **パソコンを再起動**してください

#### Docker Desktop のインストール

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) にアクセス
2. **「Download for Windows」** をクリック
3. ダウンロードされたファイルをダブルクリックしてインストール（デフォルト設定のまま）
4. インストール完了後、**パソコンを再起動**

**確認方法**: タスクトレイ（画面右下）に **クジラのアイコン** が表示され、「Docker Desktop is running」と出ればOK。

</details>

<details>
<summary><b>Mac の場合（クリックで開く）</b></summary>

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) にアクセス
2. **「Apple Chip」** または **「Intel Chip」** を選択してダウンロード
   - 確認方法: 画面左上の Apple マーク → **「このMacについて」** → 「チップ」の欄
3. ダウンロードされた `.dmg` ファイルをダブルクリック
4. Docker のアイコンを **Applications フォルダにドラッグ**
5. Applications フォルダから **Docker** を起動

**確認方法**: メニューバーにクジラのアイコンが表示され、「Engine running」と緑色で表示されればOK。

</details>

---

### 2-3. Python 3.12+ と uv のインストール

<details>
<summary><b>Windows の場合（クリックで開く）</b></summary>

#### Python のインストール

1. [Python公式サイト](https://www.python.org/downloads/) から **Python 3.12** 以上をダウンロード
2. インストーラーを実行。**「Add python.exe to PATH」に必ずチェック**を入れること
3. **「Install Now」** をクリック

#### uv のインストール

1. PowerShell を開き、以下を実行:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
2. PowerShell を閉じて開き直す

**確認方法**:
```powershell
python --version   # Python 3.12.x
uv --version       # uv 0.x.x
```

</details>

<details>
<summary><b>Mac の場合（クリックで開く）</b></summary>

#### Python の確認

```bash
python3 --version
```
3.12以上ならOK。古い場合は [Python公式サイト](https://www.python.org/downloads/) からインストール。

#### uv のインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
ターミナルを閉じて開き直す。

</details>

---

### 2-4. Node.js 22+ と pnpm のインストール

フロントエンド画面の実行に必要です。

<details>
<summary><b>Windows の場合（クリックで開く）</b></summary>

1. [Node.js公式サイト](https://nodejs.org/) から **LTS版**（22以上）をダウンロード・インストール
2. PowerShell を開いて pnpm をインストール:
```powershell
npm install -g pnpm
```

**確認方法**:
```powershell
node --version   # v22.x.x
pnpm --version   # 9.x.x
```

</details>

<details>
<summary><b>Mac の場合（クリックで開く）</b></summary>

1. [Node.js公式サイト](https://nodejs.org/) から **LTS版**をダウンロード・インストール
2. ターミナルで pnpm をインストール:
```bash
npm install -g pnpm
```

**確認方法**:
```bash
node --version   # v22.x.x
pnpm --version   # 9.x.x
```

</details>

---

## 3. APIキーの取得

AI機能を使うには、最低1つのAPIキーが必要です。

### 必須: Gemini API キー（セマンティック検索・embedding）

1. [Google AI Studio](https://aistudio.google.com/) にアクセス
2. Google アカウントでログイン
3. 左側メニューの **「Get API key」** → **「Create API key」**
4. 表示されたキー（`AIza...`）をメモ帳に保存

### 任意: Anthropic API キー（Claudeでチャット）

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. アカウント作成・ログイン後、APIキーを作成
3. キーをメモ帳に保存

### 任意: Ollama（ローカルLLM、オフライン対応）

1. [Ollama公式サイト](https://ollama.com/) からインストール
2. ターミナルでモデルをダウンロード:
```bash
ollama pull gemma4:26b
```

> **APIキーがなくても** データベースの閲覧やSafety First表示は利用可能です。AI自動構造化やチャットのみが制限されます。

---

## 4. システムのダウンロード

<details>
<summary><b>Windows の場合（クリックで開く）</b></summary>

PowerShell で以下を1行ずつ実行:

```powershell
cd $HOME\Documents
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git
cd neo4j-agno-agent
```

</details>

<details>
<summary><b>Mac の場合（クリックで開く）</b></summary>

ターミナルで以下を実行:

```bash
cd ~/Documents
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git
cd neo4j-agno-agent
```

</details>

---

## 5. 環境設定

### .env ファイルの作成

```bash
cp .env.example .env
```

テキストエディタで `.env` を開き、取得したAPIキーを設定します:

```env
# 必須: Gemini（セマンティック検索・embedding）
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx

# 任意: Claude（チャットプロバイダー）
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx

# Neo4j（デフォルトのまま変更不要）
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# チャットで使うAI: gemini / claude / ollama
CHAT_PROVIDER=gemini

# サーバーポート（デフォルトのまま変更不要）
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

> **API キーは他人に見せないでください。** パスワードと同じように管理してください。

---

## 6. システムの起動

3つのサービスを順番に起動します。それぞれ別のターミナル（PowerShell）で実行してください。

### 手順 1: Docker Desktop を起動する

- **Windows**: スタートメニューから「Docker Desktop」を起動。クジラアイコンが「running」になるまで待つ
- **Mac**: Applications から Docker を起動。メニューバーのクジラアイコンが緑色になるまで待つ

### 手順 2: Neo4j データベースを起動する

```bash
cd neo4j-agno-agent
docker compose up -d
```

初回はダウンロードに数分かかります。完了後、30秒ほど待ってください。

### 手順 3: API サーバーを起動する（ターミナル1）

```bash
cd neo4j-agno-agent/api
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

`Uvicorn running on http://0.0.0.0:8001` と表示されればOK。

### 手順 4: フロントエンドを起動する（ターミナル2）

```bash
cd neo4j-agno-agent/frontend
pnpm install   # 初回のみ
pnpm dev --port 3001
```

`Ready` と表示されればOK。

### 手順 5: ブラウザで開く

```
http://localhost:3001
```

ダッシュボードが表示されれば **セットアップ完了** です。

<!-- TODO: ダッシュボードのスクリーンショットを追加 -->

---

### ワンクリック起動（Mac のみ）

デスクトップに **「親なき後支援DB.app」** がある場合、ダブルクリックだけで Neo4j・API・フロントエンドをまとめて起動できます。

---

### デモデータの投入（任意）

初回はデータベースが空なので、動作確認用のデモデータを入れられます:

```bash
cd neo4j-agno-agent
uv run python scripts/seed_demo_data.py
```

ブラウザを再読み込みすると、統計カードに数値が表示されます。

> **注意**: デモデータは架空の人物です。実際の支援に使う前に削除してください。

---

## 7. 画面の使い方

### よくある操作

| やりたいこと | 操作手順 |
|-------------|---------|
| 新しいクライアントを登録 | `/narrative` → テキスト入力 → 「AIで構造化」 → 確認 → 登録 |
| 音声でインテーク | `/intake` → マイクボタン → 7本柱に沿って対話 |
| 日々の記録を追加 | `/quicklog` → クライアント選択 → 状況入力 → 保存 |
| AIに質問 | `/chat` → テキストまたはマイク入力 → DB検索ツール自動利用 |
| 類似ケースを探す | `/search` → キーワード入力 → セマンティック検索 |
| 支援ネットワーク確認 | `/ecomap` → クライアント選択 → グラフ表示 |
| 面談を記録 | `/meetings` → 音声ファイルアップロード → 文字起こし → 登録 |
| LLMを切り替え | `/settings` → プロバイダー選択、またはチャットで「claudeに切り替えて」 |

---

## 8. システムの停止・再起動

### 停止する

1. **フロントエンド**: ターミナル2で `Ctrl + C`
2. **APIサーバー**: ターミナル1で `Ctrl + C`
3. **データベース**:
```bash
cd neo4j-agno-agent
docker compose down
```

### 再起動する

手順6の「手順1」からやり直すだけです。データは前回のまま保持されています。

---

## 9. 困ったときは（トラブルシューティング）

### 共通の問題

| 症状 | 対処方法 |
|------|---------|
| 「データベースに接続できません」 | Docker Desktop が起動しているか確認 → `docker compose up -d` を再実行 → 30秒待つ |
| 「Gemini APIエラー」 | `.env` の `GEMINI_API_KEY` が正しいか確認。ネットワーク接続も確認 |
| フロントエンドが真っ白 | APIサーバー（port 8001）が起動しているか確認 |
| 「uv: command not found」 | uv を再インストール後、ターミナルを閉じて開き直す |
| 「pnpm: command not found」 | `npm install -g pnpm` を再実行 |

### ポート競合

他のアプリがポートを使っている場合:

```bash
# ポート使用状況の確認
lsof -i :8001  # API
lsof -i :3001  # フロントエンド
lsof -i :7687  # Neo4j
```

`.env` でポート番号を変更可能:
```env
BACKEND_PORT=8002
FRONTEND_PORT=3002
```

### Neo4j に接続できない

```bash
# コンテナの状態確認
docker compose ps

# ログ確認
docker compose logs neo4j

# コンテナを再作成
docker compose down && docker compose up -d
```

Neo4j Browser（`http://localhost:7474`）にアクセスして接続状態を確認することもできます。

### Ollama が応答しない

```bash
# Ollama が起動しているか確認
curl http://localhost:11434/api/tags

# モデルがダウンロード済みか確認
ollama list

# モデルをダウンロード
ollama pull gemma4:26b
```

### Windows 固有の問題

| 症状 | 対処方法 |
|------|---------|
| 「WSL 2 installation is incomplete」 | 管理者PowerShellで `wsl --update` → 再起動 |
| 「Virtualization must be enabled」 | BIOSでIntel VT-x/AMD-Vを有効化 |
| `docker-compose` が認識されない | `docker compose`（ハイフンなし）を使う |
| 「スクリプトの実行が無効」 | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `python` が認識されない | `python3` を試す、またはPATHにチェックを入れて再インストール |

### Mac 固有の問題

| 症状 | 対処方法 |
|------|---------|
| 「ファイアウォールでブロック」 | システム設定 → プライバシーとセキュリティ で通信を許可 |
| `docker-compose` がない | `docker compose`（ハイフンなし）を使う |

---

## 付録: Claude Desktop との連携（応用）

Claude Desktop と連携すると、自然言語でデータベースに問いかけることができます。セットアップ方法は [docs/ADVANCED_USAGE.md](./docs/ADVANCED_USAGE.md) を参照してください。

---

## 付録: SOS ボタン機能（応用）

本人や支援者がスマホからワンタップで SOS を発信できる機能です。LINE通知にも対応しています。

```bash
cd neo4j-agno-agent
uv run python mobile/api_server.py
```

ブラウザで `http://localhost:8080/app/` にアクセスするとSOSボタンが表示されます。
LINE通知の設定は `sos/README.md` を参照してください。

---

このガイドが、あなたの「親なき後支援」活動の一助となれば幸いです。

*Produced by Antigravity Team*
