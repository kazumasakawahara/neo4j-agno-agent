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

> 📌 **Windows ユーザーの方へ**
>
> 以下のソフトウェアをインストールするには **管理者権限** が必要な場合があります。
> 職場のPCで管理者権限がない場合は、IT部門に相談してください。
>
> | ソフトウェア | 管理者権限 | 備考 |
> |------------|:--------:|------|
> | WSL 2 | **必須** | Docker の前提条件 |
> | Docker Desktop | **必須** | データベース実行用 |
> | Git | 推奨 | ユーザーフォルダにインストールすれば不要 |
> | uv | 不要 | ユーザー領域にインストール |

### 1-1. Docker Desktop（データベース用）

**Windowsの場合:**

> ⚠️ **管理者権限が必要です**
> Docker Desktop のインストールには管理者権限が必要です。
> 職場のPCの場合は、IT部門に相談してください。

**【前提条件】WSL 2（Windows Subsystem for Linux）について**

Docker Desktop は内部で **WSL 2** という技術を使用します。
WSL 2 は Windows 上で Linux を動かす仕組みで、Docker が効率的に動作するために必要です。

**WSL 2 のインストール手順:**

1. **PowerShell を管理者として実行**
   - スタートメニューで「PowerShell」を検索
   - 右クリック →「管理者として実行」

2. **WSL をインストール**
   ```powershell
   wsl --install
   ```
   このコマンドで WSL 2 と Ubuntu が自動的にインストールされます。

3. **PC を再起動**
   インストール完了後、PC を再起動してください。

4. **再起動後の初期設定**
   - Ubuntu のターミナルが自動で開きます
   - ユーザー名とパスワードを設定（Windows のパスワードとは別でOK）
   - 設定したパスワードは忘れないようにメモしてください

> 💡 **WSL のバージョン確認**
> ```powershell
> wsl --version
> ```
> バージョン 2.x 以上であればOKです。

**Docker Desktop のインストール:**

1. https://www.docker.com/products/docker-desktop/ にアクセス
2. 「Download for Windows」をクリック
3. ダウンロードした `Docker Desktop Installer.exe` を **右クリック →「管理者として実行」**
4. インストール画面で以下を確認:
   - ✅「Use WSL 2 instead of Hyper-V」にチェック（推奨）
   - ✅「Add shortcut to desktop」にチェック（任意）
5. 「OK」をクリックしてインストール
6. インストール完了後、PC を再起動
7. Docker Desktop を起動

**初回起動時の確認事項:**
- 利用規約に同意する画面が表示されたら「Accept」をクリック
- 左下に「Engine running」（緑色）と表示されれば正常に動作しています
- 「WSL 2 is not installed」と表示された場合は、上記の WSL インストール手順を実行してください

> 🔧 **よくあるトラブル**
> - 「Virtualization must be enabled」→ BIOS で仮想化を有効にする必要があります（IT部門に相談）
> - 「WSL 2 installation is incomplete」→ WSL のインストール手順を再実行してください

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

> ⚠️ **管理者権限が必要な場合があります**
> 「Program Files」にインストールする場合は管理者権限が必要です。

1. https://git-scm.com/download/win にアクセス
2. 「Click here to download」をクリック
3. ダウンロードした `Git-x.xx.x-64-bit.exe` を実行
   - 管理者権限を求められたら「はい」をクリック
4. インストール画面の設定:
   - **Select Destination Location**: そのまま「Next」
   - **Select Components**: そのまま「Next」
   - **Choosing the default editor**: お好みで選択（わからなければ「Nano」推奨）
   - **Adjusting the name of the initial branch**: 「Let Git decide」のまま「Next」
   - **Adjusting your PATH environment**: 「Git from the command line and also from 3rd-party software」（推奨）
   - 以降はすべて「Next」→「Install」→「Finish」
5. インストール後、**PowerShell を再起動**して以下を実行:
   ```powershell
   git --version
   ```
   バージョンが表示されればOKです。

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

### 【Windows】Docker Desktop が起動しない

**「WSL 2 installation is incomplete」エラー:**
1. PowerShell を管理者として実行
2. 以下を実行:
   ```powershell
   wsl --update
   wsl --set-default-version 2
   ```
3. PC を再起動

**「Virtualization must be enabled」エラー:**
- BIOS/UEFI で仮想化（Intel VT-x または AMD-V）を有効にする必要があります
- PC によって設定方法が異なるため、IT部門またはPCメーカーのサポートに相談してください
- 一般的な手順:
  1. PC を再起動し、起動時に F2/F10/Delete キーを押して BIOS に入る
  2. 「Virtualization」「Intel VT-x」「SVM Mode」などの項目を「Enabled」に変更
  3. 保存して終了

**「Docker Desktop requires a newer WSL kernel version」エラー:**
```powershell
wsl --update
```

### 【Windows】ファイアウォールでブロックされる

初回起動時に「Windows セキュリティの重要な警告」が表示された場合:
1. 「プライベート ネットワーク」にチェック ✅
2. 「パブリック ネットワーク」はチェックを外す（セキュリティのため）
3. 「アクセスを許可する」をクリック

手動でファイアウォールを設定する場合:
1. 「Windows セキュリティ」を開く
2. 「ファイアウォールとネットワーク保護」→「詳細設定」
3. 「受信の規則」→「新しい規則」
4. 「ポート」を選択 → TCP ポート 8000, 7474, 7687 を許可

### 【Windows】PowerShell でコマンドが実行できない

**「このシステムではスクリプトの実行が無効になっている」エラー:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**「〇〇 は認識されていません」エラー:**
- PowerShell を再起動してください
- それでも解決しない場合、環境変数 PATH が正しく設定されているか確認

---

## 📞 サポート

技術的な問題がある場合は、開発者にお問い合わせください。
