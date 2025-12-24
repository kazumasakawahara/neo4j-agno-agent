# 親亡き後支援システム - 団体向けセットアップガイド

このガイドでは、**nest SOS緊急通知システム**と**支援データベース**のセットアップ方法を説明します。

---

## 📋 目次

1. [必要なソフトウェアのインストール](#1-必要なソフトウェアのインストール)
2. [システムのダウンロード](#2-システムのダウンロード)
3. [データベースの起動](#3-データベースの起動)
4. [LINE連携の設定](#4-line連携の設定)
5. [システムの起動](#5-システムの起動)
6. [本人用SOSアプリの設定](#6-本人用sosアプリの設定)
7. [日常の運用](#7-日常の運用)

---

## 1. 必要なソフトウェアのインストール

### 1-1. Docker Desktop（データベース用）

**Windowsの場合:**
1. https://www.docker.com/products/docker-desktop/ にアクセス
2. 「Download for Windows」をクリック
3. ダウンロードしたファイルを実行してインストール
4. PCを再起動
5. Docker Desktopを起動

**Macの場合:**
1. https://www.docker.com/products/docker-desktop/ にアクセス
2. 「Download for Mac」をクリック（Intel/Apple Siliconを選択）
3. ダウンロードした.dmgファイルを開く
4. Docker.appをApplicationsフォルダにドラッグ
5. Docker Desktopを起動

### 1-2. uv（Python環境管理）

**Windowsの場合（PowerShell）:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Macの場合（ターミナル）:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

インストール後、ターミナル/PowerShellを再起動してください。

### 1-3. Git（リポジトリ取得用）

**Windowsの場合:**
1. https://git-scm.com/download/win にアクセス
2. 「Click here to download」をクリック
3. インストーラーを実行（設定はすべてデフォルトでOK）

**Macの場合:**
Gitは通常プリインストールされています。ターミナルで以下を実行して確認:
```bash
git --version
```

---

## 2. システムのダウンロード

ターミナル（Mac）またはPowerShell（Windows）で以下を実行:

```bash
# 任意の場所に移動（例：ドキュメント）
cd ~/Documents

# システムをダウンロード
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git

# フォルダに移動
cd neo4j-agno-agent

# Pythonパッケージをインストール
uv sync
```

---

## 3. データベースの起動

### 3-1. Docker Desktopを起動

Docker Desktopアプリを起動し、左下に「Engine running」と表示されるまで待ちます。

### 3-2. Neo4jを起動

```bash
cd ~/Documents/neo4j-agno-agent
docker-compose up -d
```

### 3-3. 起動確認

ブラウザで以下にアクセス:
```
http://localhost:7474
```

Neo4jのログイン画面が表示されればOKです。

**初回ログイン:**
- Username: `neo4j`
- Password: `password`（docker-compose.ymlで設定した値）

---

## 4. LINE連携の設定

### 4-1. LINE公式アカウントの作成

1. https://developers.line.biz/ にアクセス
2. 団体のLINEアカウントでログイン
3. 「プロバイダー作成」→ 団体名を入力
4. 「チャネル作成」→「Messaging API」を選択
5. 必要事項を入力して作成

### 4-2. Channel Access Tokenの取得

1. 作成したチャネルの「Messaging API設定」
2. 「チャネルアクセストークン（長期）」→「発行」
3. 表示されたトークンをコピー

### 4-3. グループLINEに公式アカウントを招待

1. 通知を受けたいグループLINEを開く
2. 設定 → メンバー → 招待
3. 作成した公式アカウントを招待

### 4-4. 設定ファイルの作成

```bash
cd ~/Documents/neo4j-agno-agent/sos
cp .env.example .env
```

`.env`ファイルをテキストエディタで開き、以下を設定:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

LINE_CHANNEL_ACCESS_TOKEN=ここに取得したトークンを貼り付け
LINE_GROUP_ID=ここにグループIDを貼り付け

# セキュリティ設定（本番環境では必ず設定）
# SOSアプリからのアクセスを許可するオリジン（カンマ区切りで複数指定可）
# 例: https://example.com,https://app.example.com
CORS_ORIGINS=
```

> ⚠️ **セキュリティ注意**: `CORS_ORIGINS`を設定しない場合、すべてのオリジンからのアクセスが許可されます。
> 本番環境では、SOSアプリをホスティングするドメインを指定してください。

**グループIDの取得方法:**
グループIDは、公式アカウントがグループに参加した際のWebhookイベントから取得できます。
詳細は `sos/README.md` を参照してください。

---

## 5. システムの起動

### 5-1. データベースが起動していることを確認

```bash
docker ps
```

`neo4j`が表示されていればOK。

### 5-2. SOSサーバーを起動

```bash
cd ~/Documents/neo4j-agno-agent/sos
uv run python api_server.py
```

以下が表示されれば成功:
```
==================================================
🆘 nest SOS API サーバー
==================================================
Neo4j: bolt://localhost:7687
LINE設定: ✅ 設定済み
==================================================
```

### 5-3. データ登録UIを起動（別のターミナルで）

```bash
cd ~/Documents/neo4j-agno-agent
uv run streamlit run app_narrative.py
```

ブラウザで http://localhost:8501 が開きます。

---

## 6. 本人用SOSアプリの設定

### 6-1. サーバーのIPアドレスを確認

**Windowsの場合:**
```cmd
ipconfig
```

**Macの場合:**
```bash
ifconfig | grep "inet "
```

例: `192.168.1.100`

### 6-2. 本人用URLを作成

```
http://192.168.1.100:8000/app/?id=クライアント名
```

例:
- `http://192.168.1.100:8000/app/?id=山田健太`
- `http://192.168.1.100:8000/app/?id=佐々木真理`

### 6-3. QRコードを作成

以下のサイトでURLをQRコードに変換:
- https://qr.quel.jp/
- https://www.cman.jp/QRcode/

### 6-4. スマホにインストール

1. 本人のスマホでQRコードを読み取る
2. ブラウザでURLを開く
3. 「ホーム画面に追加」でアプリ化

**iPhoneの場合:**
共有ボタン → 「ホーム画面に追加」

**Androidの場合:**
メニュー → 「ホーム画面に追加」

---

## 7. 日常の運用

### 毎日の起動手順

1. **Docker Desktopを起動**
2. **SOSサーバーを起動**
   ```bash
   cd ~/Documents/neo4j-agno-agent/sos
   uv run python api_server.py
   ```

### 自動起動の設定（任意）

PCを起動したときに自動でサーバーを起動するには、以下を参考にしてください:

**Windowsの場合:**
スタートアップフォルダにバッチファイルを配置

**Macの場合:**
システム環境設定 → ユーザとグループ → ログイン項目

---

## ❓ トラブルシューティング

### 「このサイトにアクセスできません」と表示される

- SOSサーバーが起動しているか確認
- 同じWi-Fiネットワークに接続しているか確認
- ファイアウォールでポート8000が許可されているか確認

### LINE通知が届かない

- LINE_CHANNEL_ACCESS_TOKENが正しいか確認
- LINE_GROUP_IDが正しいか確認
- 公式アカウントがグループに参加しているか確認

### Neo4jに接続できない

- Docker Desktopが起動しているか確認
- `docker ps`でneo4jコンテナが動いているか確認
- `.env`のNEO4J_PASSWORDが正しいか確認

---

## 📞 サポート

技術的な問題がある場合は、開発者にお問い合わせください。
