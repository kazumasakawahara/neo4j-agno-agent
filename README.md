# 親なき後支援データベース (Post-Parent Support DB)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status: Production](https://img.shields.io/badge/Status-Production-green)

> 知的障害・精神障害のある方の支援情報をグラフデータベースで管理し、
> 親亡き後の支援継続を守るシステム

**「親がいなくなったら、誰がこの子のことを一番に考えてくれるの？」**

このシステムは、そんな切実な問いに応えるために開発されたオープンソースの支援情報管理プラットフォームです。

---

## 特徴

| 機能 | 説明 |
|------|------|
| 音声対話インテーク | 7本柱に基づく構造化聞き取り（マイク入力対応） |
| マルチLLM対応 | Gemini / Claude / Ollama（gemma4）をチャット中に動的切替 |
| セマンティック検索 | Gemini Embedding 2 + Neo4j ベクトルインデックスで意味検索 |
| Safety First | 緊急時は禁忌事項・連絡先をLLM不要で即時表示 |
| エコマップ | 支援ネットワークのインタラクティブ可視化 |
| ナラティブ抽出 | 自然文・ファイルからグラフデータを自動構造化 |
| 音声面談記録 | 録音ファイルから文字起こし・embedding・DB登録を一括処理 |

> [!WARNING]
> **免責事項**: 本システムは支援者の意思決定をサポートするためのものであり、医療行為や診断を行うものではありません。医学的な判断が必要な場合は、必ず有資格者（医師・看護師等）に相談してください。

---

## アーキテクチャ

| レイヤー | 技術 | ポート | 役割 |
|----------|------|--------|------|
| フロントエンド | Next.js 16 + shadcn/ui | 3001 | 全画面の業務UI |
| APIサーバー | FastAPI + Agno | 8001 | REST + WebSocket |
| データベース | Neo4j 5.x (Docker) | 7687 | グラフDB + ベクトルインデックス |
| LLM | Gemini / Claude / Ollama | - | チャット・抽出・embedding |
| MCP Server | server.py | - | Claude Desktop連携 |

```
┌─────────────┐    ┌──────────────┐    ┌─────────┐
│  Next.js UI │───>│  FastAPI API  │───>│  Neo4j  │
│  :3001      │<───│  :8001       │<───│  :7687  │
└─────────────┘    └──────┬───────┘    └─────────┘
                          │
                   ┌──────┴───────┐
                   │  LLM Layer   │
                   │ Gemini/Claude│
                   │ Ollama       │
                   └──────────────┘
```

---

## クイックスタート

### 前提条件

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Docker Desktop | 最新 | Neo4j データベース |
| Python | 3.12+ | APIサーバー |
| uv | 最新 | Python パッケージ管理 |
| Node.js | 22+ | フロントエンド |
| pnpm | 最新 | Node.js パッケージ管理 |

### セットアップ

```bash
git clone https://github.com/kazumasakawahara/neo4j-agno-agent.git
cd neo4j-agno-agent

# 1. Neo4j 起動
docker compose up -d

# 2. 環境変数を設定
cp .env.example .env
# .env を編集（GEMINI_API_KEY, ANTHROPIC_API_KEY 等を設定）

# 3. バックエンド起動（別ターミナル）
cd api && uv sync && uv run uvicorn app.main:app --reload --port 8001

# 4. フロントエンド起動（別ターミナル）
cd frontend && pnpm install && pnpm dev --port 3001

# 5. ブラウザで開く
open http://localhost:3001
```

### ワンクリック起動（Mac）

デスクトップの **「親なき後支援DB.app」** をダブルクリックで Neo4j・API・フロントエンドを一括起動。

---

## 画面一覧

| パス | 画面名 | 機能 |
|------|--------|------|
| `/` | ダッシュボード | 統計・更新アラート・最近の活動 |
| `/clients` | クライアント一覧 | かな行フィルタ・詳細表示 |
| `/narrative` | ナラティブ入力 | テキスト/ファイル → AI抽出 → DB登録 |
| `/quicklog` | クイックログ | 30秒で支援記録 |
| `/intake` | インテーク | マイク音声対話で7本柱情報収集 |
| `/chat` | AIチャット | マイク音声入力対応、DB検索ツール付き |
| `/search` | セマンティック検索 | ベクトル類似検索・クライアント類似度分析 |
| `/ecomap` | エコマップ | 支援ネットワーク可視化 |
| `/meetings` | 面談記録 | 音声アップロード・文字起こし・登録 |
| `/settings` | LLM設定 | プロバイダー接続状態・切替 |

---

## LLM設定

`.env` の `CHAT_PROVIDER` でデフォルトプロバイダーを設定。チャット中に「gemma4を使って」「claudeに切り替えて」で動的切替も可能。

| プロバイダー | モデル | 用途 | 備考 |
|-------------|--------|------|------|
| `gemini` | Gemini 2.0 Flash | チャット・抽出・embedding | デフォルト、高速 |
| `claude` | Claude Haiku 4.5 | チャット・インテーク | API key必要 |
| `ollama` | gemma4:26b | チャット | ローカル実行、オフライン可 |

> **Embedding**: セマンティック検索には `GEMINI_API_KEY` が必須です（Gemini Embedding 2 を使用）。

---

## 5つの理念と7本柱

### 5つの理念

1. **Dignity（尊厳）** -- 管理対象ではなく、歴史と意思を持つ一人の人間として記録する
2. **Safety（安全）** -- 緊急時に「誰が」「何を」すべきか、迷わせない構造を作る
3. **Continuity（継続性）** -- 支援者が入れ替わっても、ケアの質と文脈を断絶させない
4. **Resilience（強靭性）** -- 親が倒れた際、その機能を即座に代替できるバックアップ体制を可視化する
5. **Advocacy（権利擁護）** -- 本人の声なき声を拾い上げ、法的な後ろ盾と紐づける

### 7本柱（データ構造の基盤）

1. 本人性（Identity & Narrative）
2. ケアの暗黙知（Care Instructions）
3. 危機管理ネットワーク（Safety Net）
4. 法的基盤（Legal Basis）
5. 親の機能移行（Parental Transition）
6. 金銭的安全（Financial Safety）
7. 多機関連携（Multi-Agency Collaboration）

詳細は [agents/MANIFESTO.md](./agents/MANIFESTO.md) を参照。

---

## プライバシーと安全性

- **ローカル完結**: データはすべて自分のPC内（Docker コンテナ内の Neo4j）に保存
- **匿名化機能**: AI処理前に個人名・電話番号を自動マスキング
- **Ollama対応**: クラウドに一切データを送らないオフライン運用が可能

---

## 開発

```bash
# テスト実行（DB不要）
cd api && uv run pytest tests/ -q

# TypeScript 型チェック
cd frontend && pnpm exec tsc --noEmit

# デモデータ投入
uv run python scripts/seed_demo_data.py

# Embedding バックフィル
uv run python scripts/backfill_embeddings.py --all
```

---

## ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [SETUP_GUIDE.md](./SETUP_GUIDE.md) | はじめてのセットアップガイド（初心者向け） |
| [docs/ADVANCED_USAGE.md](./docs/ADVANCED_USAGE.md) | Claude Desktop との連携 |
| [docs/DEV_NOTES.md](./docs/DEV_NOTES.md) | 開発者メモ |
| [docs/NEO4J_SCHEMA_CONVENTION.md](./docs/NEO4J_SCHEMA_CONVENTION.md) | Neo4j 命名規則 |
| [agents/MANIFESTO.md](./agents/MANIFESTO.md) | 5理念・7本柱マニフェスト v4.0 |

---

## ライセンス

このソフトウェアは **MIT ライセンス** の下で無償公開されています。

---

## 開発コンテキスト

このシステムは、知的障害児の家族を支援するNPOと連携する弁護士が開発しました。
親が倒れた時に支援者がすぐに必要な情報にアクセスできることを最優先に設計されています。

*Produced by Antigravity Team*
