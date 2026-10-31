# Preview Report テンプレート

Phase 3（プレビュー）でユーザーに提示する書式。Claude は以下の骨組みを埋めて出力する。

---

## 標準プレビュー書式

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【登録プレビュー】narrative-intake v{version}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▼ 入力情報
  対象クライアント : {client_name}（{dob} / {age}歳）
  処理日時         : {now}
  入力ナラティブ   : {char_count}文字
  sourceHash       : {hash_short}...
  入力ソース       : {source_type}  ※narrative / meeting / handover 等

▼ 新規/更新ノード（検証済み）
  ┌────────────┬────┬──────────────────────────────────┐
  │ ラベル       │件数│ 内容サマリー                       │
  ├────────────┼────┼──────────────────────────────────┤
  │[NEW]  SupportLog   │ 2  │ パニック時対応 / 食事介助         │
  │[NEW]  NgAction     │ 1  │ 突然の大きな音 (Panic)            │
  │[MERGE] CarePreference│ 1│ パニック時: 静かな別室へ          │
  │[MERGE] Client       │ 1 │ 山田太郎（プロパティ更新: dob追加）│
  └────────────┴────┴──────────────────────────────────┘

▼ 新規リレーション
  (Supporter:鈴木)-[:LOGGED]->(SupportLog:log1)
  (SupportLog:log1)-[:ABOUT]->(Client:山田太郎)
  (Client:山田太郎)-[:MUST_AVOID]->(NgAction:突然の大きな音)
  (Client:山田太郎)-[:REQUIRES]->(CarePreference:パニック時)
  (NgAction:突然の大きな音)-[:IN_CONTEXT]->(Condition:自閉スペクトラム症)

▼ ⚠️ 安全性チェック結果
  既存禁忌事項      : {existing_ng_count}件
  抵触判定          : {violation_summary}
  {violation_details or "詳細: 問題なし"}

▼ 冪等性チェック
  同一 sourceHash の既存ノード : {duplicate_status}
  {duplicate_details or "重複なし（新規登録可）"}

▼ 検証で落とした項目（warnings）
  {warnings_list or "なし"}

▼ 監査ログ
  記録予定: AuditLog × 1（クライアント「{client_name}」に紐付け）
  operator : {user}
  sessionId: {session_id}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
この内容で Neo4j に登録してよろしいですか？

  [1] はい、登録する
  [2] 一部修正する（修正箇所を指定してください）
  [3] キャンセル
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 違反検出時の強調表示

安全性チェックで `is_violation: true` が返った場合は、プレビュー冒頭に**警告ブロック**を追加する:

```
🚨🚨🚨 安全性警告 🚨🚨🚨
既存の禁忌事項「{ng_action}」(Risk: {risk_level}) に抵触する可能性があります。
該当箇所: "{matched_narrative}"
推奨対応: {recommendation}

この警告を確認の上で、登録を継続するか判断してください。
```

---

## チャンク統合時の追加情報

長文ナラティブを複数チャンクに分割して処理した場合、プレビューに以下を追加:

```
▼ チャンキング情報
  総チャンク数    : 4
  チャンク境界    : [章1(幼児期), 章2(学齢期), 章3(青年期), 章4(現在)]
  重複統合        : NgAction×2, CarePreference×1 が重複統合されました
```

---

## 情報不足時の対応

抽出結果が空または極めて不足している場合は、登録を行わずに以下を表示:

```
▼ 登録対象なし
  入力ナラティブからは構造化できる情報が見つかりませんでした。

  推奨: 以下の情報を追加してください
  - 具体的な日付
  - 誰が（支援者名）
  - 何が起きたか（状況）
  - どう対応したか（対応）
  - 効果があったか（効果性）
```
