# oyagami-local 設計仕様書

ローカルLLMによる親亡き後支援データベースシステム。現行 neo4j-agno-agent の機能をローカル環境で再現する。

## 1. プロジェクト概要

### 名称
**oyagami-local**（親神ローカル）— 親の知恵をローカルに守る

### 目的
- 現行システム（Gemini + Claude Desktop）の機能をローカルLLM（Ollama）で再現
- Streamlit → Next.js + FastAPI に刷新し、高速かつ見栄えの良いUIを実現
- マルチエージェント構成（Agno Team）で役割分担を最適化

### スコープ
- **Phase 1**: ダッシュボード + クライアント管理 + ナラティブ入力 + AIチャット + クイックログ + LLM設定
- **Phase 2**: セマンティック検索 + エコマップ + 面談記録

### プロジェクト配置
```
~/Dev-Work/
├── neo4j-agno-agent/    # 現行プロジェクト（参照元）
└── oyagami-local/       # 新プロジェクト（ここが作業ディレクトリ）
```

### 制約
- マシン: Mac 128GB 統合メモリ
- データベース: 既存 Neo4j Docker コンテナ（port 7687）を共用（~/Dev-Work/neo4j-agno-agent/docker-compose.yml で起動）
- ネットワーク: 完全ローカル動作（クラウドAPI不使用）

---

## 2. アーキテクチャ

### 全体構成: モノリポ統合型

```
oyagami-local/
├── backend/                    # Python (FastAPI + Agno)
│   ├── app/
│   │   ├── main.py             # FastAPI エントリーポイント
│   │   ├── routers/            # APIルーター
│   │   │   ├── clients.py
│   │   │   ├── narratives.py
│   │   │   ├── chat.py         # WebSocket
│   │   │   ├── search.py
│   │   │   ├── dashboard.py
│   │   │   ├── quicklog.py
│   │   │   └── system.py
│   │   ├── agents/             # Agno マルチエージェント
│   │   │   ├── coordinator.py  # ルーティング (mistral-small)
│   │   │   ├── intake.py       # 抽出 (deepseek-r1:70b)
│   │   │   ├── validator.py    # 検証 (mistral-small)
│   │   │   ├── analyst.py      # 分析 (llama4)
│   │   │   ├── cypher_gen.py   # Cypher生成 (qwen3-coder:30b)
│   │   │   ├── team.py         # Agno Team 構成
│   │   │   └── prompts/        # システムプロンプト
│   │   │       ├── manifesto.md
│   │   │       ├── extraction.md
│   │   │       └── safety.md
│   │   ├── lib/                # 共有ライブラリ
│   │   │   ├── db_operations.py
│   │   │   ├── embedding.py
│   │   │   ├── chunking.py     # 日本語チャンキング (fugashi)
│   │   │   ├── file_readers.py
│   │   │   └── model_manager.py
│   │   └── schemas/            # Pydantic モデル
│   │       ├── client.py
│   │       ├── narrative.py
│   │       └── agent.py
│   ├── tests/
│   │   ├── agents/
│   │   ├── lib/
│   │   └── routers/
│   └── pyproject.toml
├── frontend/                   # Next.js + TypeScript
│   ├── src/
│   │   ├── app/                # App Router
│   │   │   ├── page.tsx        # ダッシュボード
│   │   │   ├── clients/
│   │   │   ├── narrative/
│   │   │   ├── quicklog/
│   │   │   ├── chat/
│   │   │   ├── search/         # Phase 2
│   │   │   ├── ecomap/         # Phase 2
│   │   │   ├── meetings/       # Phase 2
│   │   │   └── settings/
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui
│   │   │   └── domain/         # 業務コンポーネント
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   └── hooks/
│   ├── package.json
│   └── tsconfig.json
├── .env
├── .env                        # 環境変数
├── README.md
├── scripts/
└── docs/
```

### システム構成図

```
┌─────────────────────────────────────────────────────────┐
│                 Frontend (Next.js :3000)                 │
│  Dashboard | Clients | Narrative | Chat | QuickLog      │
└───────────────────────┬─────────────────────────────────┘
                        │ REST + WebSocket
                        ▼
┌─────────────────────────────────────────────────────────┐
│                Backend (FastAPI :8000)                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Agno Team (coordinator)               │ │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────────┐ │ │
│  │  │ Intake   │ │ Validator│ │ Analyst            │ │ │
│  │  │deepseek  │ │ mistral  │ │ llama4             │ │ │
│  │  │-r1:70b   │ │ -small   │ │   └─ CypherGen    │ │ │
│  │  └──────────┘ └──────────┘ │      qwen3-coder  │ │ │
│  │                            └────────────────────┘ │ │
│  └────────────────────┬───────────────────────────────┘ │
│  ┌────────────────────▼───────────────────────────────┐ │
│  │  lib/ (db_ops, embedding, chunking, model_manager) │ │
│  └────────────────────┬───────────────────────────────┘ │
└───────────────────────┼─────────────────────────────────┘
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   ┌────────────┐ ┌──────────┐ ┌──────────┐
   │  Ollama    │ │  Neo4j   │ │  Files   │
   │  :11434    │ │  :7687   │ │ (uploads)│
   └────────────┘ └──────────┘ └──────────┘
```

---

## 3. マルチエージェント設計

### エージェント構成

| エージェント | モデル | サイズ | 役割 | 常駐/排他 |
|------------|--------|--------|------|-----------|
| Coordinator | mistral-small | 14GB | 意図分類・ルーティング | 常駐 |
| Intake | deepseek-r1:70b | 42GB | テキスト→JSON抽出 | 排他 |
| Validator | mistral-small | 14GB | 論理検証・安全性チェック | 常駐（Coordinatorと共有） |
| Analyst | llama4 | 67GB | 分析・支援方針策定 | 排他 |
| CypherGen | qwen3-coder:30b | 18GB | Cypher クエリ生成 | 排他 |
| Embedding | nomic-embed-text | 0.3GB | ベクトル生成 | 常駐 |

### ルーティングルール

| 意図カテゴリ | 判定例 | ルーティング先 | モデル切替 |
|-------------|--------|---------------|-----------|
| 緊急 | パニック、SOS、事故、発作 | DB直接検索（LLM不使用） | なし |
| データ登録 | 登録、記録して、入力した | Intake → Validator | deepseek-r1 ロード |
| 質問・検索 | 教えて、一覧、検索、確認 | CypherGen → DB検索 | qwen3-coder ロード |
| 分析・考察 | 分析、比較、方針、傾向、なぜ | Analyst (→ CypherGen) | llama4 ロード |
| 雑談・ヘルプ | 使い方、ありがとう | Coordinator自身で応答 | なし |

### ModelManager（メモリ管理）

```python
class ModelManager:
    常駐モデル: [mistral-small, nomic-embed-text]  # 常にロード (~14GB)
    排他グループ: [deepseek-r1:70b, llama4, qwen3-coder:30b]  # 1つだけ

    async def ensure_model(model_name):
        if model_name in 常駐モデル:
            return  # 常にロード済み
        if model_name == 現在ロード中の排他モデル:
            return  # 既にロード済み
        # 現在の排他モデルをアンロード (keep_alive=0)
        # 新しいモデルをロード (keep_alive="10m")
```

メモリ予算:

| シナリオ | ロードするモデル | 合計 |
|---------|----------------|------|
| データ登録 | deepseek-r1:70b + mistral-small | ~56GB |
| 分析・質問応答 | llama4 + mistral-small | ~81GB |
| Cypher生成 | qwen3-coder:30b + mistral-small | ~32GB |
| 軽量作業 | mistral-small + nomic-embed-text | ~14GB |

### データフロー

**ナラティブ登録:**
1. ユーザーがテキスト/ファイルを投入
2. Coordinator: 意図=「データ登録」と判定
3. ModelManager: deepseek-r1:70b をロード
4. Intake Agent: EXTRACTION_PROMPT でテキスト解析 → JSON生成
5. Validator Agent (mistral-small): スキーマ検証 + 論理整合性 + 安全性チェック（修正必要なら Intake に差し戻し、最大2回）
6. フロントに検証済みデータを返却、ユーザーが確認画面でレビュー
7. ユーザー承認 → db_operations.register_to_database()
8. Embedding 自動付与 (nomic-embed-text)

**分析・質問応答:**
1. ユーザーが質問を入力
2. Coordinator: 意図=「分析」と判定
3. Analyst Agent (llama4): 分析方針を策定
4. ModelManager: llama4 アンロード → qwen3-coder ロード
5. CypherGen Agent: Cypher 生成 → Validator が検証 → Neo4j 実行
6. ModelManager: qwen3-coder アンロード → llama4 再ロード
7. Analyst Agent: データを基に分析・考察 → 回答返却

**緊急検索（Safety First）:**
1. Coordinator: 緊急キーワード検知
2. LLM不使用で直接 DB 検索
3. NgAction（リスクレベル順） → CarePreference → KeyPerson → Hospital → Guardian の順で返却

---

## 4. フロントエンド設計

### 技術スタック

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| フレームワーク | Next.js 15 (App Router) | SSR, ルーティング |
| 言語 | TypeScript 5.x | 型安全 |
| UIライブラリ | shadcn/ui + Radix UI | アクセシブルなコンポーネント |
| スタイリング | Tailwind CSS v4 | ユーティリティCSS |
| 状態管理 | TanStack Query (React Query) | サーバー状態の管理・キャッシュ |
| フォーム | React Hook Form + Zod | バリデーション |
| チャットUI | Vercel AI SDK (ai) | ストリーミング応答 |
| グラフ描画 | D3.js / React Flow | エコマップ (Phase 2) |

### 画面一覧

**Phase 1 (6画面):**

| 画面 | パス | 現行対応 | 主要コンポーネント |
|------|------|---------|-------------------|
| ダッシュボード | `/` | pages/home.py | StatsCards, RenewalAlerts, RecentActivity |
| ナラティブ入力 | `/narrative` | app_narrative.py | NarrativeWizard, ExtractionPreview, ConfirmDialog |
| クイックログ | `/quicklog` | app_quick_log.py | QuickLogForm, ClientSelector |
| クライアント管理 | `/clients` | pages/client_list.py | ClientTable, ClientDetail, KanaFilter |
| AIチャット | `/chat` | app_ui.py | ChatPanel, MessageBubble, AgentStatus |
| LLM設定 | `/settings` | (新規) | ModelStatus, MemoryMonitor, OllamaConfig |

**Phase 2 (3画面):**

| 画面 | パス | 現行対応 |
|------|------|---------|
| セマンティック検索 | `/search` | pages/semantic_search.py |
| エコマップ | `/ecomap` | pages/ecomap.py |
| 面談記録 | `/meetings` | pages/meeting_record.py |

### ナビゲーション

サイドバー常時表示。下部にシステムステータスバー（Ollama/Neo4j接続状態、メモリ使用量）。

### AIチャット画面の特徴

- エージェント状態のリアルタイム表示（稼働中エージェント、モデルロード進捗）
- ストリーミング応答（WebSocket経由）
- 使用した Cypher クエリ・推論過程の折りたたみ表示
- 手動ルーティング切替（ドロップダウン）

### app_narrative.py の分解

現行の831行を以下に責務分離:

| 機能 | 移植先 |
|------|--------|
| テキスト入力・ファイルアップロードUI | `frontend/src/app/narrative/page.tsx` |
| 4ステップウィザード制御 | `frontend/src/components/domain/NarrativeWizard.tsx` |
| 抽出プレビュー・編集UI | `frontend/src/components/domain/ExtractionPreview.tsx` |
| Gemini呼び出し（AI抽出） | `backend/app/agents/intake.py` |
| 安全性チェック | `backend/app/agents/validator.py` |
| DB登録処理 | `backend/app/lib/db_operations.py` |
| ファイル読み込み | `backend/app/lib/file_readers.py` |
| APIとしての窓口 | `backend/app/routers/narratives.py` |

---

## 5. バックエンド API 設計

### エンドポイント一覧

**Dashboard:**
- `GET /api/dashboard/stats` — 統計情報
- `GET /api/dashboard/alerts` — 更新期限アラート
- `GET /api/dashboard/activity` — 直近の活動ログ

**Clients:**
- `GET /api/clients` — クライアント一覧（かな絞り込み対応）
- `GET /api/clients/{name}` — クライアント詳細（全関連ノード）
- `GET /api/clients/{name}/emergency` — 緊急情報（NgAction優先）
- `GET /api/clients/{name}/logs` — 支援記録一覧

**Narratives:**
- `POST /api/narratives/extract` — テキスト/ファイル → AI抽出 → JSON返却
- `POST /api/narratives/validate` — 抽出データの検証
- `POST /api/narratives/register` — 検証済みデータをNeo4jに登録
- `POST /api/narratives/upload` — ファイルアップロード → テキスト抽出

**Quick Log:**
- `POST /api/quicklog` — 簡易支援記録の登録

**Chat:**
- `WS /api/chat/ws` — AIチャット（ストリーミング応答）
- `GET /api/chat/history` — チャット履歴取得

**Search:**
- `POST /api/search/semantic` — セマンティック検索 (Phase 2)
- `GET /api/search/fulltext` — 全文検索 (Phase 1)

**Ecomap:**
- `GET /api/ecomap/{name}` — エコマップデータ生成 (Phase 2)

**Meetings:**
- `POST /api/meetings/upload` — 音声ファイルアップロード (Phase 2)
- `GET /api/meetings/{name}` — 面談記録一覧 (Phase 2)

**System:**
- `GET /api/system/status` — Ollama/Neo4j接続状態、メモリ使用量
- `POST /api/system/models/{name}/load` — モデル手動ロード
- `POST /api/system/models/{name}/unload` — モデル手動アンロード

### WebSocket チャットプロトコル

```jsonc
// クライアント → サーバー
{"type": "message", "content": "田中さんの禁忌事項を教えて", "session_id": "abc-123"}

// サーバー → クライアント (ルーティング通知)
{"type": "routing", "agent": "coordinator", "decision": "emergency_search", "reason": "..."}

// サーバー → クライアント (モデルロード状態)
{"type": "model_status", "action": "loading", "model": "qwen3-coder:30b", "progress": 0.6}

// サーバー → クライアント (ストリーミング応答)
{"type": "stream", "content": "田中太郎さんの", "agent": "coordinator"}

// サーバー → クライアント (メタデータ)
{"type": "metadata", "cypher_query": "MATCH ...", "agents_used": ["coordinator"], "elapsed_ms": 1230}

// サーバー → クライアント (応答完了)
{"type": "done", "session_id": "abc-123"}
```

---

## 6. Embedding & 日本語チャンキング

### Embedding

- モデル: `nomic-embed-text`（Ollama経由、768次元）
- API: `POST http://localhost:11434/api/embed`
- 既存 Neo4j ベクトルインデックス（6つ）をそのまま利用
- 登録時に自動付与（SupportLog, NgAction, CarePreference, Client summaryEmbedding）

### 日本語チャンキング

- **通常ノード**（SupportLog, NgAction等）: ノード単位でそのまま embedding（現行踏襲）
- **長文テキスト**（面談文字起こし、長いナラティブ）: fugashi で文境界を認識してチャンク分割
  - 閾値: 512トークン超のテキストを分割対象
  - オーバーラップ: 文単位（トークン境界で日本語が壊れない）
  - ライブラリ: `fugashi` + `unidic-lite`

---

## 7. 現行コードからの移植マッピング

| 現行ファイル | 新プロジェクト | 変更内容 |
|-------------|---------------|---------|
| `lib/db_operations.py` (db_new_operations.py) | `backend/app/lib/db_operations.py` | Streamlit依存を除去 |
| `lib/ai_extractor.py` | `backend/app/agents/intake.py` | Gemini→Ollama。プロンプトは保持 |
| `lib/embedding.py` | `backend/app/lib/embedding.py` | Gemini→Ollama (nomic-embed-text) |
| `lib/file_readers.py` | `backend/app/lib/file_readers.py` | そのまま移植 |
| `lib/utils.py` | `backend/app/lib/utils.py` | Streamlit依存を除去 |
| `app_narrative.py` | フロント3ファイル + バック4ファイルに分解（Section 4参照） |
| `app_quick_log.py` | `frontend/src/app/quicklog/` + `backend/app/routers/quicklog.py` |
| `app_ui.py` | `frontend/src/app/chat/` + `backend/app/routers/chat.py` |
| `pages/home.py` | `frontend/src/app/page.tsx` + `backend/app/routers/dashboard.py` |
| `pages/client_list.py` | `frontend/src/app/clients/` + `backend/app/routers/clients.py` |
| `agents/MANIFESTO.md` | `backend/app/agents/prompts/manifesto.md` | そのまま移植 |
| `agents/ROUTING.md` | `backend/app/agents/coordinator.py` のプロンプトに統合 |
| (新規) | `backend/app/lib/chunking.py` | fugashi による日本語チャンキング |
| (新規) | `backend/app/lib/model_manager.py` | Ollama モデルロード/アンロード管理 |
| (新規) | `backend/app/agents/cypher_gen.py` | Cypher 生成エージェント |

---

## 8. テスト戦略

| レイヤー | 対象 | ツール | 方針 |
|---------|------|--------|------|
| ユニットテスト | lib/*, schemas/* | pytest | DB操作、チャンキング、Pydanticスキーマ |
| エージェントテスト | Coordinator, Intake, Validator | pytest + Ollama | 固定入力→期待出力。ルーティング精度90%目標 |
| API統合テスト | FastAPI routers | pytest + httpx | エンドポイント単位 |
| フロントテスト | React コンポーネント | Vitest + Testing Library | UI操作・フォームバリデーション |
| E2Eテスト | ナラティブ登録フロー | Playwright | Phase 2。クリティカルパスのみ |

---

## 9. セットアップ手順

```bash
# ① プロジェクト作成（neo4j-agno-agent と同階層）
cd ~/Dev-Work
mkdir oyagami-local && cd oyagami-local
git init

# バックエンド
mkdir -p backend && cd backend
uv init --python 3.12
uv add fastapi uvicorn neo4j agno httpx \
       pydantic python-dotenv websockets \
       fugashi unidic-lite pykakasi \
       python-docx openpyxl pdfplumber
cd ..

# フロントエンド
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint \
  --app --src-dir --use-pnpm
cd frontend
pnpm add @tanstack/react-query ai zod
pnpm dlx shadcn@latest init
cd ..

# ② Ollama モデルの確認
ollama pull nomic-embed-text
# deepseek-r1:70b, llama4, mistral-small, qwen3-coder:30b は既にインストール済み

# ③ 環境設定（プロジェクトルート: ~/Dev-Work/oyagami-local/）
cat > .env << 'EOF'
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
OLLAMA_BASE_URL=http://localhost:11434
COORDINATOR_MODEL=mistral-small:latest
INTAKE_MODEL=deepseek-r1:70b
VALIDATOR_MODEL=mistral-small:latest
ANALYST_MODEL=llama4:latest
CYPHER_MODEL=qwen3-coder:30b
EMBEDDING_MODEL=nomic-embed-text
BACKEND_PORT=8000
FRONTEND_PORT=3000
EOF
```

起動:
```bash
# ターミナル1: Neo4j（既存プロジェクトの docker-compose を使用）
cd ~/Dev-Work/neo4j-agno-agent && docker-compose up -d

# ターミナル2: バックエンド
cd ~/Dev-Work/oyagami-local/backend && uv run uvicorn app.main:app --reload --port 8000

# ターミナル3: フロントエンド
cd ~/Dev-Work/oyagami-local/frontend && pnpm dev
```

ディレクトリ構成:
```
~/Dev-Work/
├── neo4j-agno-agent/          # 既存（Neo4j Docker + 参照用コード）
│   ├── docker-compose.yml     # Neo4j コンテナはここから起動
│   ├── neo4j_data/            # DB データ（共有）
│   └── ...
└── oyagami-local/             # 新プロジェクト（作業ディレクトリ）
    ├── backend/
    ├── frontend/
    ├── .env
    └── ...
```

---

## 10. フェーズ計画

### Phase 1: コアワークフロー

| Step | 内容 | 依存 |
|------|------|------|
| 1-1 | プロジェクト骨格 + FastAPI基盤 + ModelManager | なし |
| 1-2 | lib/ 移植 (db_operations, file_readers, embedding) | 1-1 |
| 1-3 | Coordinator + ルーティングロジック | 1-1 |
| 1-4 | Intake Agent (テキスト→JSON抽出) | 1-2, 1-3 |
| 1-5 | Validator Agent + 安全性チェック | 1-2, 1-3 |
| 1-6 | CypherGen Agent | 1-2, 1-3 |
| 1-7 | Analyst Agent + モデル切替連携 | 1-3, 1-6 |
| 1-8 | API ルーター実装 | 1-4 ~ 1-7 |
| 1-9 | Next.js 基盤 + shadcn/ui + レイアウト | なし (並行可) |
| 1-10 | ダッシュボード + クライアント管理画面 | 1-8, 1-9 |
| 1-11 | ナラティブ入力画面 (3ステップウィザード) | 1-8, 1-9 |
| 1-12 | AIチャット画面 (WebSocket + ストリーミング) | 1-8, 1-9 |
| 1-13 | クイックログ + LLM設定画面 | 1-8, 1-9 |
| 1-14 | 統合テスト + エージェント回帰テスト | 1-8 ~ 1-13 |

### Phase 2: フルセット拡張

| Step | 内容 |
|------|------|
| 2-1 | 日本語チャンキング (fugashi) + embedding バックフィル |
| 2-2 | セマンティック検索画面 |
| 2-3 | エコマップ画面 (D3.js / React Flow) |
| 2-4 | 面談記録画面 (音声文字起こしはローカルWhisper検討) |
| 2-5 | E2Eテスト (Playwright) |

---

## 11. リスクと緩和策

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| deepseek-r1:70b の JSON 抽出精度 | 不正な JSON、スキーマ違反 | Validator で検証 + 最大2回リトライ。精度不足なら qwen3-coder に切替も検討 |
| モデル切替の待ち時間 | UX低下（30-60秒の遅延） | プログレスバー表示 + 利用パターン学習で先読みロード（将来検討） |
| Coordinator の意図分類精度 | 誤ルーティング | 回帰テスト + few-shot例をプロンプトに含める。手動ルーティング切替もUI上で可能に |
| nomic-embed-text の日本語精度 | セマンティック検索の精度低下 | Phase 2 で評価。不足なら multilingual-e5 等に差替 |
| 128GB メモリ上限 | 大型モデル同時ロード不可 | ModelManager の排他制御で対応済み |
