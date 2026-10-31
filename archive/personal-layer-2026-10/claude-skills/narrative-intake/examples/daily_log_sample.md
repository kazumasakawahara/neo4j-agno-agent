# 例: 日常支援記録の取り込み

## 入力（ユーザー発話）

```
山田健太さんの記録を登録して。

2026年4月10日、午前中の作業時間にパニックになった。
工事の音がきっかけ。別室に移動してヘッドホンで音楽を聴かせたら
10分くらいで落ち着いた。担当は鈴木。今後は工事予定を
事前確認する必要がある。
```

---

## Phase 1: 抽出結果（Claude が生成する JSON）

```json
{
  "nodes": [
    {
      "temp_id": "c1",
      "label": "Client",
      "mergeKey": {"name": "山田健太"},
      "properties": {"name": "山田健太"}
    },
    {
      "temp_id": "s1",
      "label": "Supporter",
      "mergeKey": {"name": "鈴木"},
      "properties": {"name": "鈴木"}
    },
    {
      "temp_id": "log1",
      "label": "SupportLog",
      "properties": {
        "date": "2026-04-10",
        "situation": "作業時間中のパニック",
        "action": "別室に移動してヘッドホンで音楽を聴かせた",
        "effectiveness": "Effective",
        "note": "工事音がきっかけ。約10分で落ち着いた。",
        "type": "日常記録",
        "duration": 10,
        "nextAction": "工事予定の事前確認",
        "sourceHash": "sha256:abc123..."
      }
    },
    {
      "temp_id": "ng1",
      "label": "NgAction",
      "mergeKey": {"action": "工事音などの大きな騒音"},
      "properties": {
        "action": "工事音などの大きな騒音",
        "reason": "パニックを誘発",
        "riskLevel": "Panic"
      }
    },
    {
      "temp_id": "cp1",
      "label": "CarePreference",
      "mergeKey": {
        "category": "パニック時",
        "instruction": "別室に移動してヘッドホンで音楽を聴かせる"
      },
      "properties": {
        "category": "パニック時",
        "instruction": "別室に移動してヘッドホンで音楽を聴かせる",
        "priority": "High"
      }
    }
  ],
  "relationships": [
    {"source_temp_id": "s1", "target_temp_id": "log1", "type": "LOGGED", "properties": {}},
    {"source_temp_id": "log1", "target_temp_id": "c1", "type": "ABOUT", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "ng1", "type": "MUST_AVOID", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "cp1", "type": "REQUIRES", "properties": {}}
  ],
  "warnings": []
}
```

---

## Phase 2: 検証結果

- すべてのラベル → allowlist OK
- すべてのリレーション → allowlist OK
- プロパティキー → 全て camelCase、正規表現適合 OK
- 列挙値 → effectiveness=Effective ✓, riskLevel=Panic ✓, priority=High ✓
- mergeKey → Client/Supporter/NgAction/CarePreference に全て付与済み ✓
- 日付 → 2026-04-10 (YYYY-MM-DD) ✓

検証結果: **全項目 PASS**

---

## Phase 3: プレビュー

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【登録プレビュー】narrative-intake v0.1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▼ 入力情報
  対象クライアント : 山田健太
  処理日時         : 2026-04-12 14:30
  入力ナラティブ   : 112文字
  sourceHash       : abc123...

▼ 新規/更新ノード（検証済み）
  [MERGE] Client         × 1 （既存、更新なし）
  [MERGE] Supporter      × 1 （鈴木、既存想定）
  [NEW]   SupportLog     × 1 （2026-04-10 作業時間中のパニック）
  [NEW]   NgAction       × 1 （工事音などの大きな騒音 / Panic）
  [MERGE] CarePreference × 1 （パニック時: 別室+音楽）

▼ 新規リレーション × 4
  Supporter-[:LOGGED]->SupportLog
  SupportLog-[:ABOUT]->Client
  Client-[:MUST_AVOID]->NgAction
  Client-[:REQUIRES]->CarePreference

▼ ⚠️ 安全性チェック結果
  既存禁忌事項: 0件（新規クライアントまたは未登録）
  抵触判定: なし

▼ 冪等性チェック
  同一 sourceHash の既存 SupportLog: なし（新規登録可）

▼ 検証で落とした項目: なし

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
この内容で登録してよろしいですか？
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Phase 4: 登録後の結果

ユーザーが「はい」と承認した後:

1. `templates/upsert_graph.cypher` を $graph パラメータで実行
2. `templates/audit_log.cypher` で AuditLog を記録
3. 結果を表示:

```
✅ 登録完了

登録されたノード: 5件（新規3件、MERGE 2件）
作成されたリレーション: 4件
監査ログ記録: 1件

▼ フォローアップ推奨
- 工事予定の事前確認手順を Organization ノードに登録することを検討
- 次回発生時は `FOLLOWS` リレーションで時系列追跡が可能
```
