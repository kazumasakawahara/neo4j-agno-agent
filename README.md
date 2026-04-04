# Post-Parent Support System (親亡き後支援システム)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status: Production](https://img.shields.io/badge/Status-Production-green)

**「親がいなくなったら、誰がこの子のことを一番に考えてくれるの？」**

このシステムは、そんな切実な問いに応えるために開発された、オープンソースの支援情報管理プラットフォームです。
Neo4jグラフデータベースとAIを活用し、障害のある当事者のための「デジタル後見人」を構築・運用できるように設計されています。

---

## Next.js UI (v2.0)

Streamlit UI に代わる新しいモダン UI です。

### 起動方法

```bash
# Neo4j
docker-compose up -d

# API サーバー (port 8000)
cd api && uv run uvicorn app.main:app --reload --port 8000

# フロントエンド (port 3001)
cd frontend && pnpm dev --port 3001
```

### 画面一覧

| 画面 | パス | 説明 |
|------|------|------|
| ダッシュボード | `/` | 統計・更新期限アラート・最近の活動 |
| ナラティブ入力 | `/narrative` | テキスト/ファイル→AI抽出→確認→登録 |
| クイックログ | `/quicklog` | 30秒で日常記録 |
| クライアント一覧 | `/clients` | あかさたなフィルタ付き検索 |
| AIチャット | `/chat` | Gemini + Safety First対話 |
| セマンティック検索 | `/search` | ベクトル類似度検索 |
| エコマップ | `/ecomap` | Neo4j Browser風ネットワーク可視化 |
| 面談記録 | `/meetings` | 音声→Gemini文字起こし→登録 |
| システム設定 | `/settings` | Gemini/Neo4j接続状態 |

---

## 特徴：3層ワークフロー（レガシー参照）

> [!WARNING]
> **免責事項**: 本システムは支援者の意思決定をサポートするためのものであり、**医療行為や診断を行うものではありません**。
> 医学的な判断が必要な場合は、必ず有資格者（医師・看護師等）に相談してください。

本システムは、用途に応じた3つのレイヤーで構成されています。

### Layer 1: 初期登録（Streamlit UI）
生育歴、家族構成、ケアの配慮事項、証明書情報などをまとめて入力します。
ファイルアップロード（Word/Excel/PDF）にも対応し、AIが自動的にデータを構造化してNeo4jに保存します。

### Layer 2: クイック記録（Streamlit UI）
日々の支援で気になったことだけを30秒で記録します。
「良い日」「気になること」だけの簡易記録で、現場の負担を最小限にします。

### Layer 3: Claude Desktop + MCP（分析・提案）
Claude Desktop Skills + Neo4j MCP を使って、自然言語でデータベースに問いかけます。
パターン分析、訪問前ブリーフィング、引き継ぎサマリー、エコマップ生成、支援記録の全文検索など、
高度な分析と提案をAIに任せることができます。

### セマンティック検索（意味検索）
Gemini Embedding 2 と Neo4j Vector Index により、**テキストの意味に基づいた検索**が可能です。
「金銭管理に不安がある利用者」のような意味的なクエリで支援記録や禁忌事項を横断検索できます。
スキャンPDFや手書きアセスメントシートの画像からもGemini OCRを通じてテキストを抽出し、検索対象に含められます。

ダッシュボードの「活用」→「セマンティック検索」から利用できます。

### 音声面談記録
面談や支援会議の録音（MP3/WAV等、最大80秒）を**文字起こしなしで直接embedding**し、テキストクエリで検索できます。
Gemini 2.0 Flash による自動文字起こしにも対応し、テキスト検索と音声ネイティブ検索の両方が可能です。

ダッシュボードの「記録・登録」→「面談記録」からアップロード・登録できます。

### クライアント類似度分析
クライアントの支援概要（障害・禁忌・ケアの要点・支援記録）からembeddingを生成し、**支援特性が似ているクライアントを自動検出**します。
新規利用者が来たときに過去の成功事例を参照したり、テキスト説明から類似ケースを探すことができます。

ダッシュボードの「活用」→「セマンティック検索」→「類似クライアント」から利用できます。

### エコマップ（支援ネットワーク図）
ダッシュボードの「可視化」メニューから、クライアントの支援ネットワークを**draw.io形式**で生成・ダウンロードできます。
4種類のテンプレート（全体像・支援会議用・緊急時・引き継ぎ用）に対応し、ダウンロード後は[draw.io](https://app.diagrams.net/)で自由に編集可能です。

---

## 5つの理念

1. **Dignity（尊厳）**: 管理対象ではなく、歴史と意思を持つ一人の人間として記録する
2. **Safety（安全）**: 緊急時に「誰が」「何を」すべきか、迷わせない構造を作る
3. **Continuity（継続性）**: 支援者が入れ替わっても、ケアの質と文脈を断絶させない
4. **Resilience（強靭性）**: 親が倒れた際、その機能を即座に代替できるバックアップ体制を可視化する
5. **Advocacy（権利擁護）**: 本人の声なき声を拾い上げ、法的な後ろ盾と紐づける

詳しくは [agents/MANIFESTO.md](./agents/MANIFESTO.md) をご覧ください。

---

## 導入方法

### 必要環境
- Docker Desktop（Neo4jデータベース用）
- Python 3.12+、uv（パッケージマネージャー）
- Google AI API キー（Gemini 2.0 Flash：データ構造化、Gemini Embedding 2：セマンティック検索）
- Claude Desktop（Layer 3 の分析・提案用、任意）

### 起動手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git
cd neo4j-agno-agent

# 2. 依存関係のインストール
uv sync

# 3. .env ファイルを設定
cp .env.example .env  # 編集して API キーなどを設定

# 4. Neo4j データベースを起動
docker-compose up -d

# 5. ダッシュボードを起動
uv run streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセスすると、ダッシュボードが表示されます。

---

## 使い方ガイド

- **はじめてのセットアップ**: [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- **Claude Desktop との連携**: [docs/ADVANCED_USAGE.md](./docs/ADVANCED_USAGE.md)
- **開発者メモ**: [docs/DEV_NOTES.md](./docs/DEV_NOTES.md)

---

## プライバシーと安全性

- **ローカル完結**: データはすべてあなたのPC内（Dockerコンテナ内）のNeo4jデータベースに保存されます
- **匿名化機能**: AIが処理する前に、自動的に個人名や電話番号をマスキングする機能を備えています

---

## ライセンスと理念

このソフトウェアは **MITライセンス** の下で無償公開されています。

---
*Produced by Antigravity Team*
