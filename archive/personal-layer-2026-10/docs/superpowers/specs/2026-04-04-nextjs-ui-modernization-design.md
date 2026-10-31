# neo4j-agno-agent UI モダン化 設計仕様書

Streamlit UI を Next.js + shadcn/ui に完全置き換え。oyagami-local のフロントエンドをベースに Gemini API 版として調整。

## 1. 概要

### 目的
- Streamlit → Next.js + shadcn/ui で高速かつ見栄えの良い業務 UI を実現
- 既存の `lib/`、MCP サーバー、SOS/Mobile API は一切変更しない
- oyagami-local で構築済みのフロントエンドを最大限再利用

### スコープ
- `api/` ディレクトリに FastAPI バックエンドを新規作成
- `frontend/` ディレクトリに Next.js フロントエンドを配置（oyagami-local からコピー＆調整）
- Streamlit ファイル（`app.py`, `app_narrative.py`, `app_quick_log.py`, `app_ui.py`, `pages/`）を `archive/` に退避

### 対象外（変更しない）
- `server.py` — MCP サーバー
- `sos/` — SOS 緊急通知 API
- `mobile/` — モバイル入力 API
- `agents/` — マニフェスト、プロトコル、ワークフロー
- `docker-compose.yml` — Neo4j コンテナ
- `claude-skills/` — Claude Desktop スキル

---

## 2. アーキテクチャ

### ディレクトリ構成

```
neo4j-agno-agent/
├── frontend/                # NEW: Next.js + shadcn/ui
│   ├── src/
│   │   ├── app/             # 9ページ
│   │   ├── components/      # ui/ + domain/
│   │   ├── hooks/
│   │   └── lib/             # api.ts, types.ts
│   ├── e2e/                 # Playwright E2Eテスト
│   └── package.json
├── api/                     # NEW: FastAPI バックエンド
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/         # 9ルーター
│   │   ├── agents/          # Gemini単体 + Safety First
│   │   │   ├── gemini_agent.py
│   │   │   ├── safety_first.py
│   │   │   └── prompts/
│   │   ├── lib/             # 既存lib/から移植
│   │   └── schemas/
│   ├── tests/
│   └── pyproject.toml
├── agents/                  # 既存（変更なし）
├── lib/                     # 既存（参照用に残す）
├── server.py                # 既存（変更なし）
├── sos/                     # 既存（変更なし）
├── mobile/                  # 既存（変更なし）
├── archive/                 # Streamlit UI を退避
│   ├── app.py
│   ├── app_narrative.py
│   ├── app_quick_log.py
│   ├── app_ui.py
│   └── pages/
├── docker-compose.yml       # 既存（変更なし）
└── .env                     # 既存（GEMINI_API_KEY 等）
```

### システム構成図

```
┌──────────────────────────────────────────────────────┐
│              Frontend (Next.js :3001)                 │
│  Dashboard | Clients | Narrative | Chat | Ecomap ... │
└───────────────────────┬──────────────────────────────┘
                        │ REST + WebSocket
                        ▼
┌──────────────────────────────────────────────────────┐
│               API Server (FastAPI :8000)              │
│  ┌──────────────────────────────────────────────┐    │
│  │  Gemini Agent (単体) + Safety First          │    │
│  └────────────────────┬─────────────────────────┘    │
│  ┌────────────────────▼─────────────────────────┐    │
│  │  lib/ (db_ops, embedding, file_readers, utils)│    │
│  └────────────────────┬─────────────────────────┘    │
└───────────────────────┼──────────────────────────────┘
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   ┌────────────┐ ┌──────────┐ ┌──────────┐
   │ Gemini API │ │  Neo4j   │ │  Files   │
   │ (Google)   │ │  :7687   │ │ (uploads)│
   └────────────┘ └──────────┘ └──────────┘

既存サービス（変更なし）:
  MCP Server (server.py)
  SOS API (sos/api_server.py)
  Mobile API (mobile/api_server.py)
```

---

## 3. エージェント設計

### Gemini 単体 + Safety First

oyagami-local のマルチエージェント構成とは異なり、Gemini 2.0 Flash 単体で処理。

| コンポーネント | 役割 | 使用 AI |
|-------------|------|---------|
| gemini_agent.py | テキスト抽出、チャット応答、安全性チェック | Gemini 2.0 Flash |
| safety_first.py | 緊急キーワード検知→直接DB検索 | LLM不使用 |

**gemini_agent.py の機能:**
- `extract_from_text(text, client_name)` — 現行 `ai_extractor.py` と同一ロジック
- `chat(message, history)` — Gemini でストリーミング応答
- `check_safety_compliance(narrative, ng_actions)` — 現行と同一

**safety_first.py の機能:**
- `is_emergency(text)` — 緊急キーワード検知（パニック, SOS, 事故, 発作, 倒れた, 救急, 助けて, 緊急）
- `handle_emergency(text)` — LLM 不使用で直接 Neo4j 検索、NgAction 優先で返却

### チャットフロー

```
ユーザー入力
    │
    ├─ 緊急キーワード検知? → safety_first.handle_emergency() → 即時応答
    │
    └─ 通常 → gemini_agent.chat() → ストリーミング応答
```

---

## 4. バックエンド API

### config.py

```python
class Settings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "gemini-embedding-2-preview"
    backend_port: int = 8000
    frontend_port: int = 3001
```

### API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/dashboard/stats` | 統計情報 |
| GET | `/api/dashboard/alerts` | 更新期限アラート |
| GET | `/api/dashboard/activity` | 最近の活動ログ |
| GET | `/api/clients` | クライアント一覧（かな絞り込み対応） |
| GET | `/api/clients/{name}` | クライアント詳細 |
| GET | `/api/clients/{name}/emergency` | 緊急情報（NgAction優先） |
| GET | `/api/clients/{name}/logs` | 支援記録一覧 |
| POST | `/api/narratives/extract` | Gemini でテキスト→JSON抽出 |
| POST | `/api/narratives/validate` | スキーマ検証 |
| POST | `/api/narratives/register` | Neo4jに登録 |
| POST | `/api/narratives/upload` | ファイルアップロード→テキスト抽出 |
| POST | `/api/narratives/safety-check` | 安全性チェック |
| POST | `/api/quicklog` | 簡易記録登録 |
| WS | `/api/chat/ws` | Gemini チャット（ストリーミング） |
| POST | `/api/search/semantic` | Gemini Embedding 2 でベクトル検索 |
| GET | `/api/search/fulltext` | 全文検索 |
| GET | `/api/ecomap/templates` | テンプレート一覧 |
| GET | `/api/ecomap/colors` | カテゴリカラー |
| GET | `/api/ecomap/{name}` | エコマップデータ |
| POST | `/api/meetings/upload` | 音声→Gemini文字起こし→登録 |
| GET | `/api/meetings/{name}` | 面談記録一覧 |
| GET | `/api/system/status` | Gemini/Neo4j接続状態 |

### WebSocket チャットプロトコル

```jsonc
// クライアント → サーバー
{"type": "message", "content": "...", "session_id": "abc-123"}

// Safety First 検知時
{"type": "routing", "agent": "safety_first", "decision": "emergency_search", "reason": "緊急キーワード検知"}

// ストリーミング応答
{"type": "stream", "content": "...", "agent": "gemini"}

// 応答完了
{"type": "done", "session_id": "abc-123"}
```

oyagami-local との差分: `model_status` メッセージタイプ不要（Gemini はクラウドなのでロード待ちなし）。

---

## 5. lib/ 移植マッピング

| 現行ファイル | api/app/lib/ | 変更内容 |
|-------------|-------------|---------|
| `lib/db_new_operations.py` | `db_operations.py` | Streamlit依存除去 |
| `lib/ai_extractor.py` | `agents/gemini_agent.py` に統合 | Gemini維持、Agno依存除去 |
| `lib/embedding.py` | `embedding.py` | Gemini Embedding 2 維持、Streamlit依存除去 |
| `lib/file_readers.py` | `file_readers.py` | `read_uploaded_file` → `read_file` |
| `lib/utils.py` | `utils.py` | session state除去 |
| (新規) | `ecomap.py` | oyagami-local から移植 |
| (新規) | `chunking.py` | oyagami-local から移植 |

---

## 6. フロントエンド差分

### oyagami-local からコピー → 変更が必要なファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/lib/api.ts` | `system.loadModel` / `unloadModel` 削除。ポート 3001 |
| `src/lib/types.ts` | `ModelStatus` から `current_exclusive`, `memory_usage_gb` 削除 |
| `src/app/settings/page.tsx` | Ollama管理 → Gemini API/Neo4j/MCP接続状態 + Embedding統計 |
| `src/app/chat/page.tsx` | 「モデルロード中」表示を削除 |
| `src/hooks/useChat.ts` | `model_status` ハンドリング削除 |
| `src/components/domain/Sidebar.tsx` | タイトル「OYAGAMI LOCAL」→「親亡き後支援DB」 |
| `src/app/layout.tsx` | メタデータを本家用に変更 |

### 変更不要（そのまま流用）

Dashboard, Clients, ClientDetail, Narrative, QuickLog, Search, Ecomap, Meetings, 全 domain コンポーネント, 全 ui コンポーネント

---

## 7. テスト戦略

| レイヤー | ツール | 方針 |
|---------|--------|------|
| ユニットテスト | pytest | スキーマ定数、日付変換（oyagami-local から流用） |
| API統合テスト | pytest + httpx | エンドポイント単位（oyagami-local から流用） |
| フロントビルド | pnpm build | TypeScript コンパイルエラー検出 |
| E2E | Playwright | oyagami-local の e2e/ を流用 |

---

## 8. 実装ステップ

| Step | 内容 | 依存 |
|------|------|------|
| 1 | Streamlit ファイルを `archive/` に退避 | なし |
| 2 | `api/` ディレクトリ作成 + FastAPI 基盤 + config | なし |
| 3 | `api/app/lib/` 移植 | 2 |
| 4 | Gemini エージェント + Safety First | 2, 3 |
| 5 | API ルーター (Dashboard, Clients, System) | 3 |
| 6 | API ルーター (Narratives, QuickLog, Chat, Search) | 3, 4 |
| 7 | API ルーター (Ecomap, Meetings) | 3 |
| 8 | frontend/ コピー (oyagami-local から) | なし (並行可) |
| 9 | frontend/ 差分調整 | 5-7, 8 |
| 10 | 統合テスト + ビルド確認 | 全て |

---

## 9. ポート割り当て

| サービス | ポート | 備考 |
|---------|--------|------|
| Neo4j Browser | 7474 | 既存 |
| Neo4j Bolt | 7687 | 既存 |
| API Server (FastAPI) | 8000 | 新規 |
| Frontend (Next.js) | 3001 | 新規（MCP の 3000 と競合回避） |
| MCP Server | 3000 | 既存（変更なし） |
| SOS API | 8080 | 既存（変更なし） |

---

## 10. セットアップ・起動

```bash
# Neo4j
docker-compose up -d

# API サーバー
cd api && uv run uvicorn app.main:app --reload --port 8000

# フロントエンド
cd frontend && pnpm dev --port 3001
```
