# 🔰 はじめてのセットアップガイド

このガイドは、プログラミング経験がない方でも「親亡き後支援システム」を自分のパソコンで動かせるように、一歩ずつ丁寧に説明した解説書です。

---

## 💻 1. 準備するもの

このシステムを動かすには、以下の3つの「道具（ソフトウェア）」が必要です。まずはこれらをインストールしましょう。

### ① Docker（ドッカー）の準備
このシステムは「データベース」という情報の保管庫を使います。その保管庫を動かすためのエンジンが **Docker** です。

#### Macをお使いの方 🍎
1. [Dockerのダウンロードページ](https://www.docker.com/products/docker-desktop/)へアクセス
2. **"Download for Mac"** をクリックしてダウンロード
   - M1/M2/M3チップ搭載のMacなら「Apple Chip」
   - それ以前のMacなら「Intel Chip」を選んでください
3. ダウンロードしたファイルをダブルクリックして、画面の指示に従ってインストール
4. インストールが終わったら、アプリケーション一覧から **Docker** をクリックして起動します
   - 画面左下に「Engine running」と緑色で表示されれば準備OKです！✅

#### Windowsをお使いの方 🪟
1. [Dockerのダウンロードページ](https://www.docker.com/products/docker-desktop/)へアクセス
2. **"Download for Windows"** をクリックしてダウンロード
3. ダウンロードしたファイルをダブルクリックしてインストール
   - 管理者権限（パスワード）を求められる場合があります
4. インストールが終わったらPCを再起動し、Dockerを起動してください

---

### ② 魔法のコマンドツール `uv` の準備
このシステムは Python（パイソン）というプログラム言語で作られています。それを簡単に動かすための魔法の杖が **uv** です。

#### Macをお使いの方 🍎
1. **「ターミナル」** というアプリを開きます（Spotlight検索で「ターミナル」と入力すると見つかります）
2. 黒い画面が出てきます。そこに以下の呪文（コマンド）をコピーして貼り付け、エンターキーを押してください
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

#### Windowsをお使いの方 🪟
1. **「PowerShell」** というアプリを開きます
2. 青い画面が出てきます。そこに以下の呪文をコピーして貼り付け、エンターキーを押してください
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

---

## 📥 2. システムを手に入れる

道具が揃ったら、システム本体をあなたのパソコンに持ってきましょう。

1. **ターミナル（またはPowerShell）** を開きます
2. 以下のコマンドを順番に入力してエンターキーを押します

まずは「ドキュメント」フォルダに移動します：
```bash
cd ~/Documents
```

システムをインターネットからコピーします：
```bash
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git
```

システムのフォルダの中に入ります：
```bash
cd neo4j-agno-agent
```

必要な部品を自動で組み立てます（少し時間がかかります）：
```bash
uv sync
```

---

## 🚀 3. システムを起動する

さあ、いよいよ起動です！

### 手順1: データベースのスイッチオン
まずは情報の保管庫（データベース）を起動します。

```bash
docker-compose up -d
```
> ※ 初回は必要なデータをダウンロードするため、数分かかることがあります。

### 手順2: エージェントチームの呼び出し
次に、あなたをサポートしてくれるAIエージェントチームを呼び出します。

```bash
uv run python main.py
```

### 成功の合図 🎉
画面に以下のような表示が出れば成功です！

```text
============================================================
🛡️  Post-Parent Support Team - Autonomous Agents Active 🛡️
============================================================

📝 Enter narrative/report (or 'exit'):
>> 
```

ここに、日々の記録や、緊急時のSOSを入力してみてください。

**例:**
- 「今日の山田さんはとても落ち着いていました」
- 「緊急！田中さんが発作を起こしました！」

---

## 📱 (応用) スマホでSOSボタンを使う

このシステムには、本人や支援者がスマホからワンタップでSOSを発信できる機能もあります。

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

### 5-2. モバイルAPIサーバーを起動

```bash
cd ~/Documents/neo4j-agno-agent
uv run python mobile/api_server.py
```

以下が表示されれば成功:
```
==================================================
🚀 Mobile & SOS API Server
==================================================
Neo4j: bolt://localhost:7687
...
App URL: http://localhost:8080/app/
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
http://192.168.1.100:8080/app/
```

※IDはアプリ内で選択するため、URLパラメータは不要になりました。

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
   cd ~/Documents/neo4j-agno-agent
   uv run python sos/api_server.py
   ```

2. **アプリを開く**
   ブラウザで `http://localhost:8000/app/` にアクセスすると、SOSボタンが表示されます。

---

## ❓ 困ったときは？

**Q. エラーが出て動かない！**
A. Dockerが起動しているか確認してください。画面上のメニューバー（Mac）やタスクトレイ（Windows）にクジラのアイコン 🐳 があれば起動しています。

- SOSサーバーが起動しているか確認
- 同じWi-Fiネットワークに接続しているか確認
- ファイアウォールでポート8080が許可されているか確認

### LINE通知が届かない

- LINE_CHANNEL_ACCESS_TOKENが正しいか確認
- LINE_GROUP_IDが正しいか確認
- 公式アカウントがグループに参加しているか確認

### Neo4jに接続できない

- Docker Desktopが起動しているか確認
- `docker ps`でneo4jコンテナが動いているか確認
- `.env`のNEO4J_PASSWORDが正しいか確認

### 終了したいときは？
A. ターミナルで `exit` と入力するか、`Ctrl` キーを押しながら `C` キーを押すと終了します。

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

このガイドが、あなたの「親亡き後支援」活動の一助となれば幸いです。
作成者: Antigravity Team
