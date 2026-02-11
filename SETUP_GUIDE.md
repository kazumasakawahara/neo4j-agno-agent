# はじめてのセットアップガイド

このガイドは、プログラミング経験がない方でも「親亡き後支援データベース」を自分のパソコンで動かせるように、一歩ずつ丁寧に説明しています。

> **対象**: Windows / Mac をお使いの方
> **所要時間**: 初回セットアップ 約30〜60分（ダウンロード時間を含む）

---

## 目次

1. [このシステムについて](#1-このシステムについて)
2. [必要なソフトウェアの準備](#2-必要なソフトウェアの準備)
3. [Gemini API キーの取得](#3-gemini-api-キーの取得)
4. [システムのダウンロード](#4-システムのダウンロード)
5. [環境設定](#5-環境設定)
6. [システムの起動](#6-システムの起動)
7. [ダッシュボードの使い方](#7-ダッシュボードの使い方)
8. [システムの停止・再起動](#8-システムの停止再起動)
9. [困ったときは（トラブルシューティング）](#9-困ったときはトラブルシューティング)

---

## 1. このシステムについて

「親亡き後支援データベース」は、知的障害・発達障害のある方の支援情報をグラフデータベースで管理するシステムです。ご家族の暗黙知（「この子にはこうすると落ち着く」「絶対にこれはしないで」など）を構造化し、緊急時やケア引き継ぎ時にすぐ参照できるようにします。

**3つのレイヤーで支援を記録・活用します:**

| レイヤー | 機能 | 使うタイミング |
|:--|:--|:--|
| Layer 1（青） | 初期登録 | 生育歴・家族構成をまとめて入力 |
| Layer 2（オレンジ） | クイック記録 | 日々の支援で気になったことを30秒で記録 |
| Layer 3（紫） | Claude Desktop | 高度な分析や支援計画の作成 |

---

## 2. 必要なソフトウェアの準備

以下の4つのソフトウェアを順番にインストールします。すべて無料です。

### 2-1. Git（ギット）のインストール

システムのソースコードをダウンロードするために使います。

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

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
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

1. **ターミナル**を開きます（Spotlight検索で「ターミナル」と入力）
2. 以下を入力して Enter:
```bash
git --version
```
3. まだインストールされていない場合、「コマンドラインデベロッパーツールをインストールしますか？」と聞かれるので **「インストール」** をクリック
4. インストール完了後、もう一度 `git --version` で確認

</details>

---

### 2-2. Docker Desktop（ドッカー デスクトップ）のインストール

データベース（Neo4j）を動かすためのソフトウェアです。

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

#### 事前準備: WSL2 のセットアップ

Docker Desktop は Windows 上で **WSL2**（Windows Subsystem for Linux 2）という仕組みを使います。まずこれを有効にします。

1. スタートメニューで **「PowerShell」** を検索
2. **右クリック** → **「管理者として実行」** を選択
3. 以下のコマンドを入力して Enter:
```powershell
wsl --install
```
4. **パソコンを再起動**してください（再起動を求められない場合もありますが、念のため再起動してください）
5. 再起動後、Ubuntuのセットアップ画面が出る場合があります。ユーザー名とパスワードを設定してください（忘れても問題ありません）

> **うまくいかない場合**: 「2-2補足: WSL2が有効にならない場合」（本ガイド末尾）を参照してください。

#### Docker Desktop のインストール

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) にアクセス
2. **「Download for Windows」** をクリック
3. ダウンロードされた `Docker Desktop Installer.exe` をダブルクリック
4. インストーラーの指示に従ってインストール（デフォルト設定のまま）
5. インストール完了後、**パソコンを再起動**
6. 再起動すると Docker Desktop が自動的に起動します

**確認方法**: 画面右下のタスクトレイ（時計の近く）に **🐳 クジラのアイコン** が表示されていればOKです。アイコンにマウスを合わせて **「Docker Desktop is running」** と出れば準備完了です。

> **注意**: Docker Desktop の初回起動時に「サインイン」や「サブスクリプション」の画面が表示されることがあります。個人利用・教育目的であれば **無料** で使えます。「Skip」や「Continue」で進んでください。

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) にアクセス
2. お使いのMacに合わせて **「Apple Chip」** または **「Intel Chip」** を選択してダウンロード
   - どちらか分からない場合: 画面左上の  マーク → **「このMacについて」** で「チップ」の欄を確認
3. ダウンロードされた `.dmg` ファイルをダブルクリック
4. Docker のアイコンを **Applications フォルダにドラッグ**
5. Applications フォルダから **Docker** を起動

**確認方法**: メニューバー（画面上部）に **🐳 クジラのアイコン** が表示され、クリックして **「Engine running」** と緑色で表示されればOKです。

</details>

---

### 2-3. Python（パイソン）のインストール

このシステムは Python 3.12 以上が必要です。

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

**方法A: Microsoft Store からインストール（推奨・簡単）**

1. スタートメニューから **「Microsoft Store」** を開く
2. 検索バーに **「Python 3.12」** と入力
3. **「Python 3.12」**（Python Software Foundation）をクリック
4. **「入手」** または **「インストール」** をクリック
5. インストール完了を待つ

**方法B: 公式サイトからインストール**

1. [Python公式サイト](https://www.python.org/downloads/) にアクセス
2. **「Download Python 3.12.x」** ボタンをクリック
3. ダウンロードされた `.exe` をダブルクリック
4. **⚠️ 重要**: インストーラーの最初の画面で **「Add python.exe to PATH」にチェック** を入れてください
5. **「Install Now」** をクリック

**確認方法**: PowerShell で以下を実行:
```powershell
python --version
```
`Python 3.12.x` のように表示されればOKです。

> **「python が認識されません」と出る場合**: パソコンを再起動してからもう一度試してください。それでもダメな場合は方法Aで再インストールしてください。

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

Mac には Python がプリインストールされていることが多いですが、バージョンが古い場合があります。

1. ターミナルで確認:
```bash
python3 --version
```
2. `Python 3.12.x` 以上であればそのままお使いいただけます
3. バージョンが古い場合は [Python公式サイト](https://www.python.org/downloads/) からダウンロード・インストールしてください

</details>

---

### 2-4. uv（パッケージマネージャー）のインストール

Python のライブラリ管理ツールです。このシステムの起動に必要です。

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

1. PowerShell を開く（スタートメニューで「PowerShell」と検索）
2. 以下のコマンドをコピーして貼り付け、Enter:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
3. 「Successfully installed uv」と表示されれば成功
4. **PowerShell を一度閉じて、開き直してください**（パスを反映するため）

**確認方法**: 新しいPowerShellで以下を実行:
```powershell
uv --version
```

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

1. ターミナルで以下を実行:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
2. ターミナルを一度閉じて開き直す

**確認方法**:
```bash
uv --version
```

</details>

---

## 3. Gemini API キーの取得

AI によるテキスト構造化機能を使うには、Google の Gemini API キーが必要です（無料枠あり）。

> **Gemini API キーがなくても**、データベースへの手動登録やダッシュボード閲覧は可能です。AI 自動構造化機能のみが利用できなくなります。

### 取得手順

1. [Google AI Studio](https://aistudio.google.com/) にアクセス
2. Google アカウントでログイン
3. 左側メニューの **「Get API key」** をクリック
4. **「Create API key」** をクリック
5. 表示されたキー（`AIza...` で始まる長い文字列）を **コピーしてメモ帳に保存**してください

> **⚠️ 注意**: API キーは他人に見せないでください。パスワードと同じように大切に管理してください。

---

## 4. システムのダウンロード

ソースコードを自分のパソコンにダウンロードします。

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

1. PowerShell を開く
2. 以下のコマンドを **1行ずつ** コピーして貼り付け、それぞれ Enter を押してください:

```powershell
cd $HOME\Documents
```
```powershell
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git
```
```powershell
cd neo4j-agno-agent
```
```powershell
uv sync
```

最後の `uv sync` は必要なライブラリをダウンロードするため、数分かかることがあります。

> **保存場所**: `C:\Users\あなたのユーザー名\Documents\neo4j-agno-agent` にダウンロードされます。

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

1. ターミナルを開く
2. 以下のコマンドを1行ずつ実行:

```bash
cd ~/Documents
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git
cd neo4j-agno-agent
uv sync
```

</details>

---

## 5. 環境設定

システムが使う設定情報（APIキーやデータベース接続先）を設定します。

### 方法A: セットアップウィザードを使う（推奨）

対話形式で設定できるウィザードが用意されています。

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

PowerShell で以下を実行（`neo4j-agno-agent` フォルダ内にいることを確認してください）:
```powershell
uv run python setup_wizard.py
```

質問に答えていきます:
1. **「Enter your Gemini API Key」**: 手順3でコピーした API キーを貼り付け
2. **「Neo4j URI」**: 何も入力せず Enter（デフォルト値が使われます）
3. **「Neo4j Username」**: 何も入力せず Enter
4. **「Neo4j Password」**: 何も入力せず Enter
5. **「LINE Channel Access Token」**: 何も入力せず Enter（後で設定可能）
6. **「LINE Group ID」**: 何も入力せず Enter

「🎉 Setup Complete!」と表示されれば成功です。

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

ターミナルで以下を実行:
```bash
uv run python setup_wizard.py
```

質問に答えていきます（Windows と同じ内容です）。

</details>

### 方法B: 手動で設定ファイルを作成する

ウィザードがうまく動かない場合は、手動で設定ファイルを作成します。

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

1. エクスプローラーで `C:\Users\あなたのユーザー名\Documents\neo4j-agno-agent` を開く
2. `.env.example` というファイルを探し、**右クリック** → **「コピー」** → 同じフォルダ内に **「貼り付け」**
3. コピーされたファイルの名前を **`.env`** に変更
   - 「拡張子を変更すると使えなくなる場合があります」と聞かれたら **「はい」** を選択
4. `.env` ファイルをメモ帳で開く（右クリック → 「プログラムから開く」→ 「メモ帳」）
5. `your_gemini_api_key_here` の部分を、手順3でコピーした API キーに書き換え
6. 保存して閉じる

**設定ファイルの内容（例）**:
```
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

> **⚠️ ファイルが見つからない場合**: エクスプローラーの「表示」メニューで **「隠しファイル」** と **「ファイル名拡張子」** にチェックを入れてください。`.`（ドット）で始まるファイルは初期設定では非表示になっています。

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

ターミナルで以下を実行:
```bash
cd ~/Documents/neo4j-agno-agent
cp .env.example .env
```

次に `.env` を開いて編集:
```bash
open -e .env
```

`your_gemini_api_key_here` の部分を API キーに書き換えて保存します。

</details>

---

## 6. システムの起動

### 手順 1: Docker Desktop を起動する

- **Windows**: スタートメニューから **「Docker Desktop」** を検索して起動。タスクトレイの🐳アイコンが **「running」** になるまで待つ（1〜2分）
- **Mac**: Applications から **Docker** を起動。メニューバーの🐳アイコンが緑色になるまで待つ

### 手順 2: データベースを起動する

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

PowerShell で以下を **1行ずつ** 実行:

```powershell
cd $HOME\Documents\neo4j-agno-agent
```
```powershell
docker-compose up -d neo4j
```

**初回のみ**、データベースのダウンロードに数分かかります。以下のように表示されればOK:
```
Creating support-db-neo4j ... done
```

データベースが完全に起動するまで **30秒ほど** 待ってください。

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

ターミナルで以下を実行:

```bash
cd ~/Documents/neo4j-agno-agent
docker-compose up -d neo4j
```

または、もっと簡単に `start.command` を使えます:
```bash
bash start.command
```

`start.command` を使うとデータベースの起動待ちから画面の立ち上げまで自動で行われます。

</details>

### 手順 3: ダッシュボードを起動する

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

PowerShell で以下を実行:
```powershell
uv run streamlit run app.py
```

以下のようなメッセージが表示されます:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

`start.command` を使った場合は自動で起動しています。手動で起動する場合:
```bash
uv run streamlit run app.py
```

</details>

### 手順 4: ブラウザで開く

お好みのブラウザ（Chrome、Edge、Safari など）で以下のアドレスにアクセスしてください:

```
http://localhost:8501
```

ダッシュボードが表示されれば **セットアップ完了** です！

> **「データベースに接続できません」と表示される場合**: データベースの起動にもう少し時間がかかっています。30秒ほど待ってから **「🔄 再接続を試みる」** ボタンを押してください。

---

### 手順 5（任意）: デモデータを入れてみる

初回はデータベースが空なので、動作確認用のデモデータを投入できます:

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

新しいPowerShellウィンドウを開いて以下を実行（ダッシュボードのPowerShellはそのまま動かしておいてください）:
```powershell
cd $HOME\Documents\neo4j-agno-agent
uv run python scripts/seed_demo_data.py
```

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

新しいターミナルウィンドウを開いて以下を実行:
```bash
cd ~/Documents/neo4j-agno-agent
uv run python scripts/seed_demo_data.py
```

</details>

3名分のデモデータ（山田健太さん、鈴木美咲さん、田中大輝さん）が投入されます。ブラウザのダッシュボードを再読み込みすると、統計カードに数値が表示されます。

> **注意**: デモデータは架空の人物です。実際の支援に使う前に削除してください。

---

## 7. ダッシュボードの使い方

ダッシュボードには4つのセクションがあります:

| セクション | ページ | 説明 |
|:--|:--|:--|
| **ホーム** | ダッシュボード | 統計情報、3層ワークフローの案内、更新期限アラート |
| **記録・登録** | 初期登録 | 生育歴・家族構成・ケア情報の一括入力（テキスト/ファイル） |
| | クイック記録 | 日々の支援で気になったことを30秒で記録 |
| **管理** | クライアント一覧 | 登録済みクライアントの検索・詳細確認 |
| **活用** | Claude活用ガイド | Claude Desktop での高度な分析プロンプト集 |
| | AIチャット | Agno/Gemini による対話型支援 |

### よくある操作

**新しいクライアントを登録したい**
→ 「記録・登録」→「初期登録」→ テキスト欄にご本人の情報を入力 → 「AIで構造化」ボタン

**日々の記録を追加したい**
→ 「記録・登録」→「クイック記録」→ クライアントを選択 → 状況を入力 → 保存

**登録済みのクライアントを確認したい**
→ 「管理」→「クライアント一覧」→ 名前で検索またはリストから選択

---

## 8. システムの停止・再起動

### 停止する

1. **ダッシュボードの停止**: PowerShell / ターミナルで **`Ctrl + C`** を押す
2. **データベースの停止**: 以下のコマンドを実行:

<details>
<summary><b>🪟 Windows</b></summary>

```powershell
cd $HOME\Documents\neo4j-agno-agent
docker-compose down
```

</details>

<details>
<summary><b>🍎 Mac</b></summary>

```bash
cd ~/Documents/neo4j-agno-agent
docker-compose down
```

</details>

3. **Docker Desktop** はそのまま起動していても問題ありません。終了したい場合はタスクトレイ/メニューバーのアイコンから終了できます。

### 再起動する

次回は手順6の「手順1」からやり直すだけでOKです。データは前回のまま保持されています。

---

## 9. 困ったときは（トラブルシューティング）

### 全 OS 共通

| 症状 | 対処方法 |
|------|---------|
| 「データベースに接続できません」 | Docker Desktop が起動しているか確認 → `docker-compose up -d neo4j` を再実行 → 30秒待つ |
| 「Gemini APIエラー」 | `.env` ファイルの `GEMINI_API_KEY` が正しいか確認。ネットワーク接続も確認 |
| データが表示されない | `uv run python scripts/seed_demo_data.py` でデモデータを投入 |
| ダッシュボードが固まった | `Ctrl + C` で停止 → `uv run streamlit run app.py` で再起動 |
| `uv: command not found` | 2-4の手順でuvを再インストール。その後 **PowerShell/ターミナルを閉じて開き直す** |

---

### 🪟 Windows 固有のトラブル

#### 「WSL 2 installation is incomplete」と表示される

Docker Desktop の起動時にこのエラーが出ることがあります。

1. スタートメニューで「PowerShell」を検索 → **右クリック** → **「管理者として実行」**
2. 以下を実行:
```powershell
wsl --update
```
3. 完了したら:
```powershell
wsl --set-default-version 2
```
4. パソコンを再起動

---

#### 「Virtualization must be enabled in the BIOS」と表示される

Docker を使うには、パソコンの BIOS/UEFI で仮想化機能を有効にする必要があります。

**手順（機種によって異なります）**:

1. パソコンを再起動
2. 起動直後に **F2キー**（または **Deleteキー** / **F10キー**）を連打して BIOS 画面に入る
   - メーカーによってキーが異なります。起動時に「Press F2 to enter setup」などと表示されることがあります
3. BIOS 画面で以下の項目を探して **Enabled** に変更:
   - Intel の場合: **「Intel Virtualization Technology」** または **「Intel VT-x」**
   - AMD の場合: **「SVM Mode」** または **「AMD-V」**
4. **「Save & Exit」** で保存して再起動

> **BIOS の操作が分からない場合**: お使いのパソコンのメーカー名と「BIOS 仮想化 有効」で検索してください（例:「Dell BIOS 仮想化 有効」）。

---

#### `docker-compose` が認識されない

Docker Desktop が正しくインストールされているのに `docker-compose` が使えない場合:

```powershell
docker compose up -d neo4j
```

と **ハイフンなし**で試してください（Docker Desktop の新しいバージョンでは `docker compose` がデフォルトです）。

---

#### PowerShell で「スクリプトの実行が無効」と表示される

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

を実行してから再度お試しください。

---

#### ファイアウォールの警告が表示される

Docker Desktop やStreamlit の起動時に「このアプリがネットワークにアクセスすることを許可しますか？」と聞かれた場合は、**「許可」** を選択してください。ローカルネットワーク内でのみ通信しています。

---

#### `python` コマンドが認識されない

Windows では `python` の代わりに `python3` で動く場合があります。以下を試してください:
```powershell
python3 --version
```

それでもダメな場合:
1. [Python公式サイト](https://www.python.org/downloads/) から再インストール
2. **⚠️ 必ず「Add python.exe to PATH」にチェック** を入れてインストール
3. パソコンを再起動

---

### 🍎 Mac 固有のトラブル

#### `docker-compose` が見つからない

Docker Desktop の新しいバージョンでは `docker compose`（ハイフンなし）が推奨されています:
```bash
docker compose up -d neo4j
```

---

#### 「ファイアウォールによってブロックされています」

システム設定 → プライバシーとセキュリティ で、Docker や Python の通信を許可してください。

---

## 付録: Claude Desktop との連携（応用）

Claude Desktop と連携すると、自然言語でデータベースに問いかけることができます。セットアップ方法は [ADVANCED_USAGE.md](./docs/ADVANCED_USAGE.md) を参照してください。

---

## 付録: SOS ボタン機能（応用）

本人や支援者がスマホからワンタップで SOS を発信できる機能です。

<details>
<summary><b>🪟 Windows の場合（クリックで開く）</b></summary>

新しい PowerShell ウィンドウを開いて:
```powershell
cd $HOME\Documents\neo4j-agno-agent
uv run python mobile/api_server.py
```

</details>

<details>
<summary><b>🍎 Mac の場合（クリックで開く）</b></summary>

新しいターミナルウィンドウで:
```bash
cd ~/Documents/neo4j-agno-agent
uv run python mobile/api_server.py
```

</details>

ブラウザで `http://localhost:8080/app/` にアクセスすると SOS ボタンが表示されます。LINE 通知の設定は `sos/README.md` を参照してください。

---

このガイドが、あなたの「親亡き後支援」活動の一助となれば幸いです。
ご不明な点がございましたら、お気軽にお問い合わせください。

作成者: Antigravity Team
