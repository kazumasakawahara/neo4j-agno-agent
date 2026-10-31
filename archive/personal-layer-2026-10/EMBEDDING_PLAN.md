# Multimodal Embedding 実装指示書

> **対象ブランチ**: `feature/multimodal-embedding`
> **起点コミット**: `a499a8a` (lib/embedding.py 作成済み)
> **作成日**: 2026-03-12
> **作成者**: Claude (claude.ai) との協働で策定

---

## 1. 背景と目的

### 1.1 何を作るか

Gemini Embedding 2（`gemini-embedding-2-preview`）を使い、既存の親亡き後支援データベースに**マルチモーダルセマンティック検索**機能を追加する。テキストだけでなく、スキャンPDFや手書きアセスメントシートの画像からも意味的な検索を可能にする。

### 1.2 なぜ必要か

- 現行の `search_support_logs()` は**全文検索**（キーワードマッチ）のみ
- 「金銭管理に不安がある利用者」のような**意味的なクエリ**に対応できない
- 紙のアセスメントシートやPDF資料は検索対象外になっている
- 事業所間の引き継ぎで「似たケースの過去事例を探す」ニーズがある

### 1.3 技術選定の理由

| 技術 | 理由 |
|------|------|
| Gemini Embedding 2 | テキスト/画像/PDF/音声を単一ベクトル空間に統合。既存の `google-genai` 依存をそのまま利用可能 |
| Neo4j Vector Index | 既に Neo4j 5.15 を使用中。別途ベクトルDBを立てる必要がない |
| 768次元 (MRL) | Matryoshka Representation Learning により最小限のストレージで十分な精度。3072次元の約1/4 |

---

## 2. 現在の状態（Step 1 完了済み）

### 2.1 完了済みの作業

`lib/embedding.py` (833行) が作成済み。以下の機能を含む：

**Embedding生成:**
- `embed_text(text, task_type, dimensions)` — テキスト → 768次元ベクトル
- `embed_image(image_path, dimensions)` — 画像 → ベクトル（OCR不要）
- `embed_multimodal(text, image_path, dimensions)` — テキスト＋画像 → 統合ベクトル
- `embed_texts_batch(texts, task_type, dimensions)` — 複数テキスト一括

**手書き/スキャン対応:**
- `ocr_with_gemini(file_path, instruction)` — Gemini 2.0 Flash で OCR
- `ocr_and_embed(file_path, dimensions)` — OCR → embedding パイプライン

**Neo4jベクトルインデックス管理:**
- `ensure_vector_indexes()` — 4つのインデックス一括作成（冪等）
- `show_vector_indexes()` — インデックス一覧取得

**セマンティック検索:**
- `semantic_search(query_text, index_name, top_k)` — 汎用検索
- `search_support_logs_semantic(query_text, top_k, client_name)` — 支援記録検索
- `search_ng_actions_semantic(query_text, top_k)` — 禁忌事項検索

**バッチ処理:**
- `backfill_support_log_embeddings(client_name, batch_size)` — 既存SupportLog一括付与
- `backfill_ng_action_embeddings(batch_size)` — 既存NgAction一括付与
- `get_embedding_stats()` — embedding付与率の統計

### 2.2 設計上の重要な決定事項

- **次元数は768固定**（`DEFAULT_DIMENSIONS = 768`）。ストレージ効率とのバランスで選択
- **Neo4jの `db.create.setNodeVectorProperty()` を使用**。通常のプロパティ設定ではなくベクトル専用API
- **ベクトルインデックスは4つ**: `support_log_embedding`, `care_preference_embedding`, `ng_action_embedding`, `client_summary_embedding`
- **既存の `run_query()` を遅延インポートで利用**（`lib.db_new_operations` から）
- **`google-genai` の `Client` をシングルトンで管理**（`get_genai_client()`）
- **タスクタイプを使い分ける**: ドキュメント登録時は `RETRIEVAL_DOCUMENT`、検索クエリ時は `RETRIEVAL_QUERY`

---

## 3. 残りの実装ステップ

### Step 2: 登録フローへのembedding自動付与

**目的**: データ登録時に自動的にembeddingを生成・付与する。

**変更対象ファイル**: `lib/db_new_operations.py`

**やること:**
1. `register_to_database()` 関数の末尾（ノード登録完了後）に、embedding付与のフックを追加
2. 対象ノードラベル: `SupportLog`, `NgAction`, `CarePreference`
3. embedding生成はオプショナル（`GEMINI_API_KEY` が未設定の場合はスキップ）
4. embedding生成失敗は登録処理全体のエラーにしない（ベストエフォート）

**実装方針:**
```python
# register_to_database() の末尾に追加するイメージ:
try:
    from lib.embedding import embed_text, DEFAULT_DIMENSIONS
    # SupportLog, NgAction, CarePreference のテキスト表現を構築して embed_text() で生成
    # db.create.setNodeVectorProperty() で付与
except Exception as e:
    log(f"embedding付与スキップ: {e}", "WARN")
    # 登録自体は成功扱い
```

**注意点:**
- `embed_text()` はAPI呼び出しを伴うため、多数ノード同時登録時にレートリミットに注意
- `embed_texts_batch()` で可能な限りバッチ処理する
- `GEMINI_API_KEY` が `.env` に設定されていない環境でもエラーにならないようにする

### Step 3: file_readers.py の拡張（スキャンPDF/手書き対応）

**目的**: `pdfplumber` では読み取れないスキャンPDF・手書きPDFへの対応を追加する。

**変更対象ファイル**: `lib/file_readers.py`

**やること:**
1. `read_pdf()` に「pdfplumber でテキストが取れなかった場合、Gemini OCR にフォールバック」するロジックを追加
2. 画像ファイル（`.jpg`, `.png`）のOCR読み取り対応を追加
3. `SUPPORTED_EXTENSIONS` に画像拡張子を追加

**実装方針:**
```python
def read_pdf(file: BinaryIO) -> str:
    # 1. まず pdfplumber で試行（既存処理）
    text = _read_pdf_pdfplumber(file)
    # 2. テキストが少ない場合（スキャンPDFの可能性）
    if len(text.strip()) < 50:
        # Gemini OCR にフォールバック
        from lib.embedding import ocr_with_gemini
        # file を一時ファイルに保存して ocr_with_gemini() に渡す
        text = ocr_with_gemini(temp_path)
    return text
```

**注意点:**
- `BinaryIO` → 一時ファイルへの変換が必要（`ocr_with_gemini` はファイルパスを受け取る）
- `tempfile` モジュールを使用
- Gemini APIが利用できない場合は元のpdfplumber結果をそのまま返す

### Step 4: セマンティック検索UI（Streamlit）

**目的**: ユーザーがテキストクエリでセマンティック検索を実行できるUIを提供する。

**新規ファイル**: `pages/semantic_search.py`

**やること:**
1. テキスト入力欄（検索クエリ）
2. 検索対象の選択（支援記録 / 禁忌事項 / 全て）
3. クライアント名でのフィルタ（オプション）
4. 検索結果の表示（スコア付き）
5. embedding付与状況の統計表示

**UIコンポーネント:**
```
┌──────────────────────────────────┐
│ 🔍 セマンティック検索             │
├──────────────────────────────────┤
│ 検索クエリ: [________________]   │
│ 対象: ◉支援記録 ○禁忌 ○全て    │
│ クライアント: [▼ 選択(任意)]     │
│ [検索]                           │
├──────────────────────────────────┤
│ 結果（スコア順）:                │
│ 0.89 | 田中太郎 | 食事場面で...  │
│ 0.85 | 山田花子 | パニック時に... │
│ ...                              │
├──────────────────────────────────┤
│ 📊 Embedding統計                  │
│ SupportLog: 45/120 (37.5%)       │
│ NgAction: 30/30 (100%)           │
└──────────────────────────────────┘
```

**既存UIへの統合:**
- `app.py` のナビゲーションに「セマンティック検索」ページを追加
- `pages/home.py` のダッシュボードに embedding 統計カードを追加（オプション）

### Step 5: バックフィルスクリプト

**新規ファイル**: `scripts/backfill_embeddings.py`

**やること:**
1. 既存の全 `SupportLog` ノードにembeddingを一括付与するCLIスクリプト
2. 既存の全 `NgAction` ノードにも同様
3. 進捗表示（プログレスバー）
4. `--client` オプションで特定クライアントに絞り込み
5. `--dry-run` で件数確認のみ

```bash
# 使用例
uv run python scripts/backfill_embeddings.py --all
uv run python scripts/backfill_embeddings.py --client "田中太郎"
uv run python scripts/backfill_embeddings.py --dry-run
```

### Step 6: ドキュメント・テスト

**変更対象ファイル:**
- `CLAUDE.md` — Embedding関連の記述を追加（スキーマ、関数一覧、ベクトルインデックス）
- `docs/` — セマンティック検索の使い方ドキュメント
- `pyproject.toml` — 追加依存があれば（現時点では不要のはず）

**テスト:**
- `lib/embedding.py` の各関数の単体テスト
- Neo4j ベクトルインデックスの作成・検索の統合テスト
- OCRパイプラインのテスト（サンプル画像/PDF使用）

---

## 4. 技術的な補足情報

### 4.1 Gemini Embedding 2 API の使い方

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# テキストembedding
response = client.models.embed_content(
    model="gemini-embedding-2-preview",
    contents="テキスト",
    config=types.EmbedContentConfig(
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=768,
    ),
)
values = response.embeddings[0].values  # list[float]

# 画像embedding
response = client.models.embed_content(
    model="gemini-embedding-2-preview",
    contents=[
        types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
    ],
    config=types.EmbedContentConfig(output_dimensionality=768),
)

# マルチモーダル（テキスト＋画像 → 統合ベクトル）
response = client.models.embed_content(
    model="gemini-embedding-2-preview",
    contents=[
        "テキスト説明",
        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
    ],
    config=types.EmbedContentConfig(output_dimensionality=768),
)

# バッチ（複数テキスト）
response = client.models.embed_content(
    model="gemini-embedding-2-preview",
    contents=["テキスト1", "テキスト2", "テキスト3"],
    config=types.EmbedContentConfig(output_dimensionality=768),
)
# response.embeddings はリスト
```

**task_type の使い分け:**
| task_type | 用途 |
|-----------|------|
| `RETRIEVAL_DOCUMENT` | ドキュメント登録時 |
| `RETRIEVAL_QUERY` | 検索クエリ時 |
| `SEMANTIC_SIMILARITY` | 類似度比較 |
| `CLUSTERING` | クラスタリング |

**制限事項（gemini-embedding-2-preview）:**
- テキスト: 最大8,192トークン
- 画像: 最大6枚/リクエスト（PNG, JPEG, WebP, HEIC）
- 動画: 最大120秒（MP4, MOV）
- 音声: 最大80秒（MP3, WAV）
- PDF: 最大6ページ
- 出力次元: デフォルト3,072。768, 1,536 に縮小可能（MRL）
- 768次元は**コサイン類似度使用時に手動正規化が必要**（3,072次元は正規化済み）

### 4.2 Neo4j ベクトルインデックスの操作

```cypher
-- インデックス作成
CREATE VECTOR INDEX `support_log_embedding` IF NOT EXISTS
FOR (s:SupportLog) ON (s.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 768,
  `vector.similarity_function`: 'cosine'
}}

-- ベクトルプロパティの設定（専用API）
MATCH (n:SupportLog {date: date('2026-03-09'), situation: '食事'})
CALL db.create.setNodeVectorProperty(n, 'embedding', $vector)

-- ベクトル検索
CALL db.index.vector.queryNodes('support_log_embedding', 10, $query_embedding)
YIELD node, score
RETURN node, score ORDER BY score DESC

-- インデックス確認
SHOW VECTOR INDEXES

-- インデックス削除
DROP INDEX `support_log_embedding`
```

### 4.3 プロジェクト固有の注意事項

- **パッケージマネージャは `uv`** を使用（pipではない）
- **Neo4j は Docker で起動**: `docker compose up -d`（ポート7687）
- **命名規則を厳守**: `docs/NEO4J_SCHEMA_CONVENTION.md` を参照
  - ノード: PascalCase
  - リレーション: UPPER_SNAKE_CASE
  - プロパティ: camelCase（`embedding`, `summaryEmbedding`）
- **Cypherインジェクション防止**: `ALLOWED_LABELS`, `ALLOWED_REL_TYPES` のホワイトリストを更新する場合は `db_new_operations.py` で
- **ログ出力パターン**: `sys.stderr.write(f"[モジュール名:レベル] メッセージ\n")` を使用
- **シングルトンパターン**: ドライバー/クライアントは `get_xxx()` 関数でシングルトン管理
- **環境変数**: `.env` に `GEMINI_API_KEY` が必要。`.env.example` にも追記済み

### 4.4 依存関係の確認

```toml
# pyproject.toml に既にある（追加不要）
"google-genai>=1.55.0"   # Gemini Embedding 2 API
"neo4j>=6.0.3"           # ベクトルインデックス対応
"streamlit>=1.33.0"      # UI

# 追加が必要になる可能性があるもの（Step 4以降で判断）
# なし（現時点の依存関係で十分）
```

---

## 5. 優先順位とスコープ

### 必須（この feature ブランチで完了すべき）

1. **Step 2**: 登録フローへのembedding自動付与
2. **Step 5**: バックフィルスクリプト
3. **Step 6**: CLAUDE.md 更新

### 推奨（できればこのブランチで）

4. **Step 4**: セマンティック検索UI

### 将来（別ブランチでもよい）

5. **Step 3**: file_readers.py のスキャンPDF対応拡張

> **Phase 2 実装済み**: 音声面談記録（機能A）とクライアント類似度分析（機能B）は
> `feature/audio-and-similarity` ブランチで実装完了。
> 詳細は `ADVANCED_EMBEDDING_PLAN.md` を参照。

---

## 6. テスト手順

### 6.1 前提条件
```bash
cd ~/Dev-Work/neo4j-agno-agent
git checkout feature/multimodal-embedding
docker compose up -d          # Neo4j起動
uv sync                       # 依存関係インストール
```

### 6.2 動作確認スクリプト
```python
# test_embedding.py（手動実行用）
import os
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USERNAME", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "password")

from lib.embedding import (
    embed_text, ensure_vector_indexes, get_embedding_stats,
    search_support_logs_semantic, backfill_support_log_embeddings
)

# 1. ベクトルインデックス作成
print("=== インデックス作成 ===")
result = ensure_vector_indexes()
print(result)

# 2. テキストembedding生成テスト
print("\n=== テキストembedding ===")
vec = embed_text("食事中にパニックを起こした場合の対応方法")
print(f"次元数: {len(vec)}, 先頭5値: {vec[:5]}")

# 3. バックフィル
print("\n=== バックフィル ===")
result = backfill_support_log_embeddings(batch_size=5)
print(result)

# 4. セマンティック検索
print("\n=== セマンティック検索 ===")
results = search_support_logs_semantic("パニック時の対応", top_k=3)
for r in results:
    print(f"  スコア: {r.get('スコア', 'N/A'):.3f} | {r.get('クライアント')} | {r.get('状況')}")

# 5. 統計
print("\n=== Embedding統計 ===")
stats = get_embedding_stats()
for label, s in stats.items():
    print(f"  {label}: {s['embedded']}/{s['total']}")
```

---

## 7. コミットメッセージの規約

このプロジェクトでは以下のprefixを使用:

```
feat:     新機能
fix:      バグ修正
refactor: リファクタリング
docs:     ドキュメント
chore:    雑務（依存関係更新等）
test:     テスト追加
```

例:
```
feat: auto-embed SupportLog/NgAction on registration
feat: add semantic search UI page
feat: add backfill script for existing nodes
docs: update CLAUDE.md with embedding schema and functions
```
