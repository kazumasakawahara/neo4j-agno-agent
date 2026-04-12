---
name: narrative-intake
description: 支援記録・家族聴き取り・面談書き起こし・生育歴ナラティブなど、物語調テキストから4段階プロトコル（抽出→検証→プレビュー→登録）でNeo4jに構造化保存するスキル。EXTRACTION_PROMPT準拠、禁忌抵触チェック、監査ログ自動記録、冪等登録（sourceHash）、長文チャンキングに対応。
---

# narrative-intake スキル（ナラティブ一括構造化・登録）

## 0. 最優先ルール（必ず最初に読むこと）

1. **個人情報の外部送信厳禁**: 入力ナラティブは Neo4j へのローカル書き込み以外に送出しない。WebFetch / WebSearch / 外部 API は使用禁止。
2. **作業前の承認必須**: Phase 3（プレビュー）でユーザーの明示的承認を得てから Phase 4（登録）に進むこと。
3. **情報の創作禁止**: 入力テキストに明示的に書かれていない情報は絶対に推測・補完しない（`EXTRACTION_PROMPT` 規則と同じ）。
4. **スキーマは本スキル同梱ファイルを Single Source of Truth とせず**、`docs/NEO4J_SCHEMA_CONVENTION.md` および `lib/db_new_operations.py` の `ALLOWED_LABELS` / `ALLOWED_REL_TYPES` / `MERGE_KEYS` をマスターとする。本スキルの `schema/*.json` はそのミラー（乖離したらコード側を正とする）。
5. **緊急語検知で即離脱**: 「パニック進行中」「自傷」「事故」「急病」「失踪」など急迫ワードを検知したら、本スキルではなく `emergency-protocol` スキルへ即座に切り替える。

---

## 1. スキル概要

| 項目 | 内容 |
|---|---|
| 対象入力 | 物語調テキスト（支援日報、家族からの聴き取り、面談書き起こし、生育歴、ケース記録等） |
| 対象DB | 障害福祉支援DB（Neo4j port 7687） — `nest-support-db` / 汎用 `neo4j` MCP |
| 出力 | `{nodes, relationships}` 形式の検証済みグラフJSON → Neo4jへUPSERT |
| MCPツール | `neo4j:read_neo4j_cypher`, `neo4j:write_neo4j_cypher` |
| 関連スキル | `neo4j-support-db`（読み取り中心）、`emergency-protocol`（急迫時）、`ecomap-generator`（可視化） |

---

## 2. 4段階プロトコル（必ず順守）

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Phase 1   │ → │Phase 2   │ → │Phase 3   │ → │Phase 4   │
│抽出       │   │検証       │   │プレビュー  │   │登録+監査  │
│Extraction│   │Validation│   │Preview   │   │Write+Audit│
└──────────┘   └──────────┘   └──────────┘   └──────────┘
                                    ↑
                            ユーザー承認ゲート
```

### Phase 1: 抽出（Extraction）

`prompts/extraction_core.md` の抽出プロンプトに従い、ナラティブから `{nodes, relationships}` を生成する。

**主な抽出ルール**（詳細は `prompts/extraction_core.md`）:
- Client / Supporter / SupportLog / NgAction / CarePreference / Condition / KeyPerson / Guardian / Hospital / Certificate / LifeHistory / Wish 等の許可ノードに分類
- 「〜すると落ち着く」「〜が好き」→ `CarePreference` + `REQUIRES`
- 「〜は嫌がる」「〜するとパニック」→ `NgAction` + `MUST_AVOID`（★最重要★）
- 「今日〜した」「〜の対応で効果があった」→ `SupportLog` + `LOGGED`/`ABOUT`
- 和暦は必ず西暦 `YYYY-MM-DD` に変換（昭和50年3月15日 → 1975-03-15）
- 各ノードに `temp_id`（例: `c1`, `s1`, `log1`）と `mergeKey`（MERGE対象ノードのみ）を付与

**生成JSONの拡張スキーマ**（本スキル固有）:

```json
{
  "nodes": [
    {
      "temp_id": "c1",
      "label": "Client",
      "mergeKey": {"name": "山田太郎"},
      "properties": {"name": "山田太郎", "dob": "1995-03-15"}
    },
    {
      "temp_id": "log1",
      "label": "SupportLog",
      "properties": {
        "date": "2026-04-12",
        "situation": "パニック時",
        "action": "イヤーマフを装着",
        "effectiveness": "Effective",
        "note": "5分で落ち着いた",
        "sourceHash": "sha256:<入力ナラティブのハッシュ>"
      }
    }
  ],
  "relationships": [
    {"source_temp_id": "s1", "target_temp_id": "log1", "type": "LOGGED", "properties": {}},
    {"source_temp_id": "log1", "target_temp_id": "c1", "type": "ABOUT", "properties": {}}
  ],
  "auditContext": {
    "user": "<ユーザー名>",
    "sessionId": "<session-id>",
    "sourceType": "narrative",
    "sourceHash": "sha256:..."
  }
}
```

### Phase 2: 検証（Validation）

Claude 自身が以下を順次チェックし、違反ノード・リレーションは落として warnings 配列に残す:

1. **ラベル allowlist**: `schema/allowed_labels.json` と照合
2. **リレーション allowlist**: `schema/allowed_rels.json` と照合
3. **プロパティキー**: camelCase + 正規表現 `^[a-zA-Z_][a-zA-Z0-9_]*$`（日本語キー禁止）
4. **列挙値**: `schema/enum_values.json` と照合
5. **mergeKey**: `schema/merge_keys.json` 記載のラベルには `mergeKey` 必須
6. **必須プロパティ**: Client には `name` 必須、Certificate には `type` 必須など
7. **日付型**: すべて `YYYY-MM-DD` 形式

### Phase 3: プレビュー（Preview）— ユーザー承認ゲート

#### 3a. 既存データ参照

登録前に、対象クライアントの既存情報を読み取る:

```cypher
// 既存NgAction取得（安全性チェック用）
MATCH (c:Client)-[:MUST_AVOID]->(ng:NgAction)
WHERE c.name CONTAINS $clientName
RETURN ng.action AS action, ng.riskLevel AS riskLevel, ng.reason AS reason
```

```cypher
// 重複SupportLogチェック（冪等性用）
MATCH (l:SupportLog {sourceHash: $sourceHash})
RETURN l.date AS date LIMIT 1
```

#### 3b. 安全性コンプライアンスチェック

`prompts/safety_check.md` に従い、ナラティブ内の行動が既存NgActionに抵触しないか Claude 自身で判定する。抵触があれば警告を強調表示。

#### 3c. プレビュー表示（`templates/preview_report.md` 書式）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【登録プレビュー】narrative-intake
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
対象クライアント: 山田太郎（1995-03-15 / 31歳）
処理日時: 2026-04-12 14:30
入力ナラティブ: 342文字 (sourceHash: abc123...)

▼ 新規/更新ノード（検証済み）
  [NEW] SupportLog × 1
        date: 2026-04-12 / situation: パニック時
        action: イヤーマフ装着 / effectiveness: Effective
  [NEW] NgAction × 1
        action: 突然の大きな音 / riskLevel: Panic
  [MERGE] CarePreference × 1
        category: パニック時 / instruction: 静かな別室へ移動

▼ 新規リレーション
  (Supporter:鈴木)-[:LOGGED]->(SupportLog)
  (SupportLog)-[:ABOUT]->(Client:山田太郎)
  (Client)-[:MUST_AVOID]->(NgAction)

▼ ⚠️ 安全性チェック結果
  既存禁忌事項: 3件 / 抵触: なし

▼ 冪等性チェック
  同一sourceHashの既存SupportLog: なし（新規登録OK）

▼ 検証で落とした項目
  なし

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
この内容でNeo4jに登録してよろしいですか？ [はい / 修正 / キャンセル]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Phase 4: 登録＋監査（Write & Audit）

承認後、`templates/upsert_graph.cypher` を**単一トランザクション**で実行。実行後、`templates/audit_log.cypher` で AuditLog を記録。

---

## 3. スキーマ参照ファイル

| ファイル | 内容 | マスターの所在 |
|---|---|---|
| `schema/allowed_labels.json` | ノードラベル許可リスト | `lib/db_new_operations.py::ALLOWED_LABELS` |
| `schema/allowed_rels.json` | リレーション型許可リスト | `lib/db_new_operations.py::ALLOWED_REL_TYPES` |
| `schema/merge_keys.json` | MERGEキー定義 | `lib/db_new_operations.py::MERGE_KEYS` |
| `schema/enum_values.json` | 列挙値リスト | `docs/NEO4J_SCHEMA_CONVENTION.md` |

**同期方法**: プロジェクトルートで以下を実行（`setup.sh --sync-schema` として追加予定）:

```bash
uv run python scripts/sync_narrative_intake_schema.py
```

---

## 4. 長文ナラティブのチャンキング戦略

家族聴き取りマニュアル（docx）や面談書き起こしなど、数千〜数万文字の入力に対しては以下の手順:

1. **章見出し優先分割**: 「第○章」「幼児期」「学齢期」などの見出しで分割
   - 生育歴は `docs/LIFE_HISTORY_TO_NEO4J_LULES.md` の LifeStage 標準値（胎児期/乳児期/幼児期/学齢期前半/後半/青年期/成人期/壮年期/高齢期）に沿わせる
2. **文脈ヘッダ必須**: 各チャンクの先頭に `【対象クライアント: 〇〇】` を付与
3. **temp_id 名前空間**: チャンク番号を接頭辞にする（`ch01_c1`, `ch02_log3` 等）
4. **チャンク境界での同一ノード統合**: 最終マージ時に `mergeKey` が同一のノードを1つに集約
5. **`FOLLOWS` リレーションはチャンクを跨って時系列順**に生成

### 日本語最適化ルール（バージョン 1.0）

チャンキング・正規化・相対時間解決のルールは以下のファイルに分離されている。Phase 1 実行時に必ず参照すること。

| ファイル | 役割 |
|---------|-----|
| `schema/ja_text_rules.json` | 文境界・引用括弧・分割禁止位置・NFC正規化ルール |
| `schema/era_conversion.json` | 明治〜令和の元号→西暦変換表 |
| `schema/honorific_dict.json` | 敬称・親族呼称・職業的呼称の正規化辞書 |
| `prompts/relative_time_resolver.md` | 相対時間表現の解決アルゴリズム |

これらのファイルは相互に参照可能で、`prompts/extraction_core.md` の「日本語前処理」セクションからも呼び出される。
ルール更新時は `version` と `updatedAt` を必ずインクリメントすること。

**実装上の注意**:
- 元号変換は **抽出段階で必ず実施**し、graph JSON 出力時には ISO 8601 形式に統一する
- 敬称は `mergeKey` 生成時に除去するが、`displayName` プロパティとして原表記を保持する
- 相対時間表現は解決できない場合、日付プロパティに入れず `warnings` と `notes` に残す

---

## 5. 冪等性（idempotency）

同一ナラティブの二重登録を防ぐため、以下を必ず実施:

1. 入力ナラティブ全文の SHA256 ハッシュを計算
2. 生成される `SupportLog` / `LifeHistory` / `MeetingRecord` ノードに `sourceHash` プロパティを付与
3. Phase 3a で `MATCH (l:SupportLog {sourceHash:$h})` による重複チェック
4. ヒット時はプレビューで「既に登録済み」と表示し、ユーザーに新規/スキップを選択させる

---

## 6. 正規化ルール

| 対象 | 正規化内容 |
|---|---|
| 日付 | 和暦→西暦、`YYYY-MM-DD` 形式、Neo4j `date()` で保存 |
| 氏名 | NFC正規化、前後空白除去、全角半角の揺れ統一 |
| 電話番号 | ハイフン統一（例: 090-1234-5678） |
| 医療機関名 | 略称→正式名称（明示されている場合のみ。推測は禁止） |
| 列挙値 | riskLevel/effectiveness/priority は英語 PascalCase に強制 |

---

## 7. 監査ログと書き込み者トレース

登録時、`auditContext` を元に以下を必ず記録:

```cypher
// templates/audit_log.cypher
CREATE (al:AuditLog {
    timestamp: datetime(),
    user: $user,
    action: "NARRATIVE_INTAKE",
    targetType: $targetType,
    targetName: $targetName,
    details: $details,
    clientName: $clientName,
    sourceHash: $sourceHash,
    sessionId: $sessionId
})
WITH al
OPTIONAL MATCH (c:Client {name: $clientName})
FOREACH (_ IN CASE WHEN c IS NOT NULL THEN [1] ELSE [] END |
    CREATE (al)-[:AUDIT_FOR]->(c)
)
RETURN al.timestamp AS 記録日時
```

特に **`NgAction` 追加時**は `details` に元ナラティブの該当部分を残し、事後に判断根拠を追跡できるようにする。

---

## 8. 典型ユースケース

### ケース1: 短い日報
```
ユーザー: 「山田太郎の記録: 今日パニックになったけど、イヤーマフをつけたら5分で落ち着いた」

Phase 1: SupportLog + NgAction + CarePreference を抽出
Phase 2: 全件 allowlist 適合
Phase 3: プレビュー表示 → 既存NgAction照合 → 承認
Phase 4: 1トランザクションで登録 + 監査ログ
```

### ケース2: 家族聴き取りマニュアル（長文docx）
```
ユーザー: 「この聴き取りマニュアルを山田太郎さんの情報として登録して」

手順:
1. 章見出しで分割（生育歴/ケア/危機管理/法的基盤の4セクション想定）
2. 各チャンクで抽出→検証
3. 全チャンク統合時に mergeKey で重複ノード集約
4. 統合プレビュー表示（ノード種別×件数のサマリー）
5. 承認後、全ノード・リレーションを単一トランザクションで登録
```

### ケース3: 面談書き起こし（MeetingRecord 付き）
```
手順:
1. MeetingRecord ノードを1件生成（title, date, transcript, sourceHash）
2. 文中に現れる NgAction / CarePreference / Wish / LifeHistory を抽出
3. (Supporter)-[:RECORDED]->(MeetingRecord)-[:ABOUT]->(Client) を構築
4. プレビューで MeetingRecord の要約を表示
5. 登録
```

---

## 9. 関連スキルとの連携

| スキル | 連携タイミング |
|---|---|
| `neo4j-support-db` | 登録後の参照・レポート生成に利用 |
| `emergency-protocol` | 急迫ワード検知時に即座に切替 |
| `ecomap-generator` | 登録したKeyPerson/Guardian/Supporter/Hospitalを可視化 |
| `provider-search` | ServiceProviderとの紐付けが必要な場合 |
| `pdf` / `xlsx` | 登録結果のレポート出力 |

---

## 10. バージョン

- v0.1.0 (2026-04-12) - 初版。4段階プロトコル、安全性チェック、冪等性、チャンキング戦略を定義
