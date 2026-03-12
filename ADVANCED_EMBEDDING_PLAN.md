# 応用機能実装指示書: 音声面談記録検索 & クライアント類似度分析

> **対象ブランチ**: `feature/audio-and-similarity` (mainから分岐して新規作成)
> **起点**: `main` ブランチ最新 (`ee92089`)
> **前提**: `lib/embedding.py` に Gemini Embedding 2 基盤が実装済み
> **作成日**: 2026-03-12

---

## 全体像

2つの独立した機能を追加する。どちらも既存の `lib/embedding.py` を拡張する形で実装する。

| 機能 | 概要 | 主な変更箇所 |
|------|------|-------------|
| **A. 音声面談記録** | 面談音声をネイティブembeddingし、テキストクエリで検索可能にする | `lib/embedding.py`, `lib/db_new_operations.py`, `pages/semantic_search.py` |
| **B. クライアント類似度** | Clientの支援概要からembeddingを生成し、類似クライアントを自動検出する | `lib/embedding.py`, `lib/db_new_operations.py`, `scripts/backfill_embeddings.py` |

---

## 機能A: 音声面談記録の検索

### A.1 背景

支援会議や面談の録音（MP3/WAV等）を、文字起こしなしで直接embeddingし、テキストクエリで検索できるようにする。Gemini Embedding 2 は音声を最大80秒までネイティブにembeddingできる。

### A.2 データモデル

**新規ノード: `MeetingRecord`**

```
(:MeetingRecord {
    date: date,           // 面談日
    title: string,        // 面談タイトル（例: "第3回支援会議"）
    duration: integer,    // 録音時間（秒）
    filePath: string,     // 音声ファイルの保存パス
    mimeType: string,     // "audio/mp3", "audio/wav" 等
    transcript: string,   // Gemini で文字起こしした場合のテキスト（オプション）
    note: string,         // 支援者のメモ（オプション）
    embedding: list,      // 音声ネイティブembedding [768]
    textEmbedding: list,  // transcript/note テキストのembedding [768]（オプション）
})
```

**リレーション:**
```
(:Supporter)-[:RECORDED]->(:MeetingRecord)-[:ABOUT]->(:Client)
```

**命名規則チェック:**
- ノード: PascalCase ✅ `MeetingRecord`
- リレーション: UPPER_SNAKE_CASE ✅ `RECORDED`
- プロパティ: camelCase ✅ `filePath`, `mimeType`, `textEmbedding`

### A.3 実装ステップ

#### Step A-1: lib/embedding.py に音声embedding関数を追加

```python
def embed_audio(
    audio_path: str,
    dimensions: int = DEFAULT_DIMENSIONS,
) -> Optional[list[float]]:
    """
    音声ファイルからembeddingベクトルを生成（文字起こし不要）

    Args:
        audio_path: 音声ファイルパス（MP3, WAV 等。最大80秒）
        dimensions: 出力次元数

    Returns:
        float のリスト（embeddingベクトル）、失敗時は None
    """
```

**実装方針:**
- `embed_image()` と同じパターンで実装
- `mimetypes.guess_type()` で MIME タイプを推定
- フォールバック: 拡張子 → MIME マッピング（`.mp3` → `audio/mpeg`, `.wav` → `audio/wav`, `.m4a` → `audio/mp4`）
- `types.Part.from_bytes()` でバイナリデータを渡す
- Gemini Embedding 2 の音声制限: **最大80秒**, MP3/WAV 等

**MIME タイプのフォールバック用マッピング:**
```python
_AUDIO_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
}
```

#### Step A-2: lib/embedding.py に音声の文字起こし関数を追加

```python
def transcribe_audio(
    audio_path: str,
    instruction: str = "この音声を正確に文字起こししてください。話者が複数いる場合は区別してください。",
) -> Optional[str]:
    """
    Gemini 2.0 Flash で音声をテキストに文字起こし

    Args:
        audio_path: 音声ファイルパス
        instruction: 文字起こし指示

    Returns:
        文字起こしテキスト、失敗時は None
    """
```

**実装方針:**
- `ocr_with_gemini()` と同じパターン
- `client.models.generate_content()` に音声バイナリ＋指示テキストを渡す
- モデルは `gemini-2.0-flash` を使用（`EMBEDDING_MODEL` ではない）

#### Step A-3: lib/embedding.py にベクトルインデックスを追加

`VECTOR_INDEXES` 辞書に以下を追加:

```python
"meeting_record_embedding": {
    "label": "MeetingRecord",
    "property": "embedding",
    "dimensions": DEFAULT_DIMENSIONS,
},
"meeting_record_text_embedding": {
    "label": "MeetingRecord",
    "property": "textEmbedding",
    "dimensions": DEFAULT_DIMENSIONS,
},
```

#### Step A-4: lib/embedding.py に面談記録のセマンティック検索を追加

```python
def search_meeting_records_semantic(
    query_text: str,
    top_k: int = 10,
    client_name: Optional[str] = None,
    index_name: str = "meeting_record_text_embedding",
) -> list[dict]:
    """
    面談記録のセマンティック検索

    Args:
        query_text: 検索クエリ（例: "服薬の飲み忘れ"）
        top_k: 返す結果の最大数
        client_name: クライアント名でフィルタ（オプション）
        index_name: 使用するインデックス
            - "meeting_record_text_embedding": テキスト（transcript/note）ベースの検索
            - "meeting_record_embedding": 音声ネイティブembeddingベースの検索

    Returns:
        面談記録のリスト（スコア付き）
    """
```

**Cypherクエリ:**
```cypher
CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
YIELD node, score
MATCH (s:Supporter)-[:RECORDED]->(node)-[:ABOUT]->(c:Client)
WHERE $client_name = '' OR c.name CONTAINS $client_name
RETURN node.date AS 日付,
       node.title AS タイトル,
       node.duration AS 秒数,
       s.name AS 記録者,
       c.name AS クライアント,
       node.note AS メモ,
       COALESCE(left(node.transcript, 100), '') AS 文字起こし抜粋,
       score AS スコア
ORDER BY score DESC
```

#### Step A-5: lib/db_new_operations.py にスキーマ更新

以下を追加:

```python
# ALLOWED_CREATE_LABELS に追加
ALLOWED_CREATE_LABELS = {
    "SupportLog", "LifeHistory", "Wish", "AuditLog", "PublicAssistance",
    "MeetingRecord",  # ← 追加
}

# ALLOWED_REL_TYPES に追加
ALLOWED_REL_TYPES = {
    ...,
    "RECORDED",  # ← 追加
}
```

#### Step A-6: lib/embedding.py に面談記録の登録ヘルパーを追加

```python
def register_meeting_record(
    audio_path: str,
    client_name: str,
    supporter_name: str,
    date: str,
    title: str = "",
    note: str = "",
    auto_transcribe: bool = True,
) -> dict:
    """
    音声ファイルから面談記録を登録

    1. 音声ファイルを embed_audio() でネイティブembedding
    2. auto_transcribe=True なら transcribe_audio() で文字起こし
    3. transcript/note のテキストを embed_text() でテキストembedding
    4. MeetingRecord ノードを作成し、embedding/textEmbedding を付与
    5. Supporter→RECORDED→MeetingRecord→ABOUT→Client のリレーションを作成

    Returns:
        {"status": "success", "transcript": str, ...} または {"status": "error", ...}
    """
```

**実装方針:**
- `_run_query()` で直接Cypherを実行（`register_to_database()` は使わない。MeetingRecord固有のロジックが多いため）
- 音声embedding生成が失敗しても、テキストembeddingだけで登録する（ベストエフォート）
- `filePath` には音声ファイルの**絶対パス**を保存（後からの再embeddingやダウンロードに使用）
- 長い音声（80秒超）の場合は、embeddingはスキップし文字起こし＋テキストembeddingのみ行う

**音声ファイルの長さチェック:**
```python
import subprocess
def _get_audio_duration(path: str) -> float:
    """ffprobe で音声の長さ（秒）を取得。ffprobe がなければ -1 を返す"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return -1  # 不明の場合はembedding試行に任せる
```

**注意:** `ffprobe` がインストールされていない環境では長さチェックをスキップし、API側のエラーに任せる。

#### Step A-7: pages/semantic_search.py に面談記録タブを追加

検索対象の選択肢に「面談記録」を追加:

```python
search_target = st.radio(
    "検索対象",
    ["支援記録", "禁忌事項", "面談記録"],  # ← "面談記録" 追加
    horizontal=True,
)
```

面談記録選択時の結果表示には、音声再生ボタン（`st.audio()`）を含める:

```python
if target == "面談記録":
    # ... 検索実行 ...
    for r in results:
        with st.container(border=True):
            st.write(f"**{r.get('タイトル', '')}** ({r.get('日付', '')})")
            st.write(f"クライアント: {r.get('クライアント', '')} / 記録者: {r.get('記録者', '')}")
            if r.get("文字起こし抜粋"):
                st.caption(f"文字起こし: {r['文字起こし抜粋']}...")
            # 音声ファイルが存在すれば再生ボタン
            # st.audio(file_path) は Streamlit がファイルパスからの再生をサポート
```

#### Step A-8: Streamlit に面談記録の登録UI（オプション）

`pages/` に新規ファイルを作る場合は `pages/meeting_record.py` として作成。
最低限必要な入力:
- 音声ファイルアップロード（`st.file_uploader(type=["mp3", "wav", "m4a"])`)
- クライアント選択（セレクトボックス）
- 面談日付（`st.date_input()`）
- タイトル（テキスト入力）
- メモ（テキストエリア、任意）
- 「自動文字起こし」チェックボックス（デフォルトON）

`app.py` のナビゲーション「記録・登録」セクションに追加:

```python
st.Page("pages/meeting_record.py", title="面談記録", icon="🎙️"),
```

---

## 機能B: クライアント類似度分析

### B.1 背景

Client ノードに `summaryEmbedding` を付与し、利用者同士の類似度を自動検出する。新規利用者が来たときに「この方と支援特性が似ているクライアント」を提示し、過去の成功事例を参照できるようにする。

ベクトルインデックス `client_summary_embedding` は既に `VECTOR_INDEXES` に定義済みだが、`summaryEmbedding` を生成・付与するロジックがまだない。

### B.2 クライアント概要テキストの構築

類似度分析の品質は「何をembeddingするか」で決まる。Client ノード自体のプロパティ（name, dob, bloodType）だけでなく、関連するノードの情報を統合した「支援概要テキスト」を作る。

**概要テキストの構築ルール:**

```
[基本情報] {name}、{dob}、血液型{bloodType}
[障害・疾患] {Condition.name を連結}
[禁忌事項] {NgAction.action を連結}
[ケアの要点] {CarePreference.instruction を連結}
[主な支援状況] {直近SupportLog のsituation/actionを数件連結}
```

例:
```
山田太郎、1990-05-15、血液型A。
障害・疾患: 自閉症スペクトラム、感覚過敏。
禁忌: 突然の大きな音（パニック誘発）、食事中の強制。
ケアの要点: パニック時は静かな別室に移動、好きな音楽で落ち着く。
主な支援状況: 食事場面でイライラ→窓際席に移動で落ち着く。外出時に感覚過敏で固まる→イヤーマフ使用で改善。
```

### B.3 実装ステップ

#### Step B-1: lib/embedding.py にクライアント概要テキスト構築関数を追加

```python
def build_client_summary_text(client_name: str) -> Optional[str]:
    """
    Neo4j から Client の関連情報を集約し、embedding用の概要テキストを構築

    Args:
        client_name: クライアント名

    Returns:
        構築された概要テキスト、データ不足の場合は None
    """
```

**Cypherクエリ:**
```cypher
MATCH (c:Client {name: $client_name})
OPTIONAL MATCH (c)-[:HAS_CONDITION]->(con:Condition)
OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
OPTIONAL MATCH (log:SupportLog)-[:ABOUT]->(c)
WITH c,
     collect(DISTINCT con.name) AS conditions,
     collect(DISTINCT ng.action) AS ngActions,
     collect(DISTINCT cp.instruction) AS careInstructions
OPTIONAL MATCH (log:SupportLog)-[:ABOUT]->(c)
WITH c, conditions, ngActions, careInstructions, log
ORDER BY log.date DESC
LIMIT 5
WITH c, conditions, ngActions, careInstructions,
     collect(log.situation + '→' + COALESCE(log.action, '')) AS recentLogs
RETURN c.name AS name,
       c.dob AS dob,
       c.bloodType AS bloodType,
       conditions,
       ngActions,
       careInstructions,
       recentLogs
```

テキスト構築は Python 側で行う（Cypher で文字列結合するより柔軟）。

#### Step B-2: lib/embedding.py にクライアントsummaryEmbedding付与関数を追加

```python
def embed_client_summary(
    client_name: str,
    dimensions: int = DEFAULT_DIMENSIONS,
) -> bool:
    """
    特定クライアントの summaryEmbedding を生成・付与

    1. build_client_summary_text() で概要テキスト構築
    2. embed_text(text, task_type="CLUSTERING") でembedding生成
    3. Neo4j の Client ノードに summaryEmbedding を付与

    Args:
        client_name: クライアント名
        dimensions: 出力次元数

    Returns:
        成功なら True
    """
```

**注意:**
- `task_type="CLUSTERING"` を使用（類似度比較に最適化）
- `db.create.setNodeVectorProperty()` で `summaryEmbedding` を設定

#### Step B-3: lib/embedding.py に類似クライアント検索関数を追加

```python
def find_similar_clients(
    client_name: str,
    top_k: int = 5,
    exclude_self: bool = True,
) -> list[dict]:
    """
    指定クライアントに支援特性が似ているクライアントを検索

    Args:
        client_name: 基準となるクライアント名
        top_k: 返す結果の最大数
        exclude_self: 自分自身を除外するか

    Returns:
        [{"name": str, "score": float, "conditions": list, ...}, ...]
    """
```

**実装方針:**
1. 基準クライアントの `summaryEmbedding` を取得
2. `db.index.vector.queryNodes('client_summary_embedding', ...)` で検索
3. `exclude_self=True` なら自分を除外

**Cypherクエリ:**
```cypher
MATCH (base:Client {name: $client_name})
WHERE base.summaryEmbedding IS NOT NULL
WITH base.summaryEmbedding AS query_vec
CALL db.index.vector.queryNodes('client_summary_embedding', $top_k_plus, query_vec)
YIELD node, score
WHERE node.name <> $client_name
OPTIONAL MATCH (node)-[:HAS_CONDITION]->(con:Condition)
RETURN node.name AS name,
       node.dob AS dob,
       collect(DISTINCT con.name) AS conditions,
       score AS スコア
ORDER BY score DESC
LIMIT $top_k
```

（`$top_k_plus` は `top_k + 1`。自分自身を除外する分を多めに取得）

#### Step B-4: テキストベースの類似クライアント検索も追加

summaryEmbedding がまだ付与されていないクライアントに対しても、テキストクエリで類似クライアントを検索できるようにする:

```python
def search_similar_clients_by_text(
    description: str,
    top_k: int = 5,
) -> list[dict]:
    """
    テキスト説明から類似クライアントを検索

    Args:
        description: 支援特性の説明（例: "金銭管理が困難、訪問販売の被害歴あり"）
        top_k: 返す結果の最大数

    Returns:
        類似クライアントのリスト（スコア付き）
    """
```

これは新規利用者の情報を入力して、既存クライアントから類似ケースを探す用途に使える。

#### Step B-5: scripts/backfill_embeddings.py に Client の summaryEmbedding バックフィルを追加

既存の `--label` オプションに `Client` を追加:

```python
parser.add_argument(
    "--label", choices=["SupportLog", "NgAction", "CarePreference", "Client"],  # ← Client 追加
    ...
)
```

Client のバックフィルロジック:
```python
elif label == "Client":
    return _backfill_loop(
        label="Client",
        fetch_fn=lambda bs: _fetch_clients(bs),
        text_fn=None,  # Client は特殊（build_client_summary_text を使う）
        batch_size=batch_size,
        dry_run=dry_run,
    )
```

**注意:** Client のバックフィルは他と異なり、`build_client_summary_text()` でクライアントごとにCypherクエリを実行する必要がある。そのためバッチ処理ではなく、1件ずつ処理するループとして実装する。

```python
def _backfill_clients(batch_size: int, dry_run: bool) -> dict:
    """Client の summaryEmbedding を一括付与"""
    from lib.embedding import build_client_summary_text, embed_text
    from lib.db_new_operations import run_query

    clients = run_query("""
        MATCH (c:Client)
        WHERE c.summaryEmbedding IS NULL
        RETURN c.name AS name
        LIMIT $batch_size
    """, {"batch_size": batch_size})

    if dry_run:
        return {"processed": len(clients), "success": 0, "failed": 0}

    success = 0
    failed = 0
    for client in clients:
        name = client["name"]
        text = build_client_summary_text(name)
        if not text:
            failed += 1
            continue
        embedding = embed_text(text, task_type="CLUSTERING")
        if embedding is None:
            failed += 1
            continue
        try:
            run_query("""
                MATCH (c:Client {name: $name})
                CALL db.create.setNodeVectorProperty(c, 'summaryEmbedding', $embedding)
            """, {"name": name, "embedding": embedding})
            success += 1
        except Exception as e:
            log(f"Client summaryEmbedding 付与失敗 ({name}): {e}", "WARN")
            failed += 1
    return {"processed": len(clients), "success": success, "failed": failed}
```

#### Step B-6: pages/semantic_search.py にクライアント類似度タブを追加

UIに「類似クライアント検索」モードを追加。2つの検索方法を提供:

1. **クライアント選択 → 類似検索**: 既存クライアントを選んで「この方に似たクライアントは？」
2. **テキスト入力 → 類似検索**: 新規利用者の特徴を入力して「似た既存クライアントは？」

```python
search_target = st.radio(
    "検索対象",
    ["支援記録", "禁忌事項", "面談記録", "類似クライアント"],  # ← 追加
    horizontal=True,
)
```

類似クライアント選択時の UI:
```python
if target == "類似クライアント":
    method = st.radio("検索方法", ["既存クライアントから", "テキストで検索"], horizontal=True)
    if method == "既存クライアントから":
        selected_client = st.selectbox("基準クライアント", clients)
        # → find_similar_clients(selected_client) を呼ぶ
    else:
        description = st.text_area("支援特性の説明", placeholder="例: 金銭管理が困難、訪問販売の被害歴あり")
        # → search_similar_clients_by_text(description) を呼ぶ
```

結果表示:
```
┌─────────────────────────────────────┐
│ 類似度 0.92 | 佐藤花子              │
│ 障害: 軽度知的障害、金銭管理困難    │
│ 類似点: 消費者被害リスク、後見検討  │
├─────────────────────────────────────┤
│ 類似度 0.85 | 鈴木一郎              │
│ 障害: 知的障害                      │
│ 類似点: 訪問販売被害歴              │
└─────────────────────────────────────┘
```

#### Step B-7: register_to_database() で Client 登録時に summaryEmbedding 自動付与

`lib/db_new_operations.py` の `_attach_embeddings()` で、Client ノードの登録・更新時に summaryEmbedding を付与するフックを追加:

```python
# _attach_embeddings() 内に追加
if "Client" in registered_items:
    try:
        from lib.embedding import embed_client_summary
        embed_client_summary(client_name_context)
    except Exception as e:
        log(f"Client summaryEmbedding 付与スキップ: {e}", "WARN")
```

**注意:** `embed_client_summary()` は内部で `build_client_summary_text()` を呼ぶため、Client と同時に登録された Condition, NgAction 等の関連ノードも概要テキストに反映される（`register_to_database()` のノード登録は全て完了した後に呼ばれるため）。

---

## CLAUDE.md 更新内容

以下を追記:

1. **Node Types** セクションに `MeetingRecord` を追加
2. **Relationship Patterns** に `(:Supporter)-[:RECORDED]->(:MeetingRecord)-[:ABOUT]->(:Client)` を追加
3. **Embedding & Semantic Search** セクションに新関数を追加:
   - `embed_audio()`, `transcribe_audio()`, `search_meeting_records_semantic()`
   - `build_client_summary_text()`, `embed_client_summary()`, `find_similar_clients()`, `search_similar_clients_by_text()`
4. **ベクトルインデックス** 表に `meeting_record_embedding`, `meeting_record_text_embedding` を追加

---

## 技術的な補足

### Gemini Embedding 2 の音声embedding

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

with open("meeting.mp3", "rb") as f:
    audio_bytes = f.read()

# 音声をネイティブにembedding（文字起こし不要）
response = client.models.embed_content(
    model="gemini-embedding-2-preview",
    contents=[
        types.Part.from_bytes(data=audio_bytes, mime_type="audio/mpeg"),
    ],
    config=types.EmbedContentConfig(output_dimensionality=768),
)
values = response.embeddings[0].values  # list[float], 768次元
```

**制限事項:**
- 音声: 最大80秒（MP3, WAV, M4A, OGG, FLAC, AAC）
- 80秒を超える場合は分割するか、テキストembeddingのみ使用

### Gemini 2.0 Flash による音声文字起こし

```python
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[
        types.Part.from_bytes(data=audio_bytes, mime_type="audio/mpeg"),
        "この音声を正確に文字起こししてください。",
    ],
)
transcript = response.text
```

### task_type の使い分け（再掲＋追加）

| task_type | 用途 | 本プロジェクトでの使用箇所 |
|-----------|------|--------------------------|
| `RETRIEVAL_DOCUMENT` | ドキュメント登録時 | SupportLog, NgAction, CarePreference, MeetingRecord |
| `RETRIEVAL_QUERY` | 検索クエリ時 | semantic_search 系関数 |
| `CLUSTERING` | クラスタリング・類似度比較 | **Client の summaryEmbedding**（新規） |
| `SEMANTIC_SIMILARITY` | 類似度比較 | 必要に応じて |

---

## 実装の優先順位

### 必須

1. **Step B-1〜B-3**: クライアント概要テキスト構築、summaryEmbedding付与、類似検索
2. **Step B-5**: バックフィルスクリプトに Client 追加
3. **Step B-6**: 類似クライアント検索 UI

### 推奨

4. **Step A-1〜A-2**: 音声embedding、文字起こし関数
5. **Step A-3〜A-4**: ベクトルインデックス、検索関数
6. **Step A-5〜A-6**: スキーマ更新、登録ヘルパー
7. **Step A-7**: 検索UIに面談記録タブ追加

### オプション

8. **Step A-8**: 面談記録の登録UI
9. **Step B-4**: テキストベースの類似クライアント検索
10. **Step B-7**: register_to_database() での summaryEmbedding 自動付与

---

## テスト手順

### 前提条件
```bash
cd ~/Dev-Work/neo4j-agno-agent
git checkout -b feature/audio-and-similarity
docker compose up -d
uv sync
```

### 機能B のテスト（類似クライアント）
```python
from lib.embedding import (
    ensure_vector_indexes, build_client_summary_text,
    embed_client_summary, find_similar_clients,
    search_similar_clients_by_text, get_embedding_stats
)

# 1. インデックス作成
ensure_vector_indexes()

# 2. 概要テキスト確認
text = build_client_summary_text("山田太郎")
print(text)

# 3. summaryEmbedding 付与
embed_client_summary("山田太郎")

# 4. 全クライアントにバックフィル
# uv run python scripts/backfill_embeddings.py --label Client

# 5. 類似クライアント検索
results = find_similar_clients("山田太郎", top_k=3)
for r in results:
    print(f"  {r.get('スコア', 0):.3f} | {r['name']} | {r.get('conditions', [])}")

# 6. テキストベース検索
results = search_similar_clients_by_text("金銭管理が困難、消費者被害のリスク")
```

### 機能A のテスト（音声面談記録）
```python
from lib.embedding import (
    embed_audio, transcribe_audio, register_meeting_record,
    search_meeting_records_semantic
)

# 1. 音声embedding テスト
vec = embed_audio("/path/to/test_meeting.mp3")
print(f"次元数: {len(vec)}")

# 2. 文字起こしテスト
transcript = transcribe_audio("/path/to/test_meeting.mp3")
print(transcript[:200])

# 3. 面談記録登録
result = register_meeting_record(
    audio_path="/path/to/test_meeting.mp3",
    client_name="山田太郎",
    supporter_name="鈴木",
    date="2026-03-12",
    title="第3回支援会議",
    auto_transcribe=True
)
print(result)

# 4. 検索テスト
results = search_meeting_records_semantic("服薬の管理について")
```

---

## コミットメッセージ例

```
feat: add client summary embedding and similarity search
feat: add audio meeting record embedding and transcription
feat: add similar clients UI to semantic search page
feat: extend backfill script with Client summaryEmbedding
docs: update CLAUDE.md with MeetingRecord schema and similarity functions
```
