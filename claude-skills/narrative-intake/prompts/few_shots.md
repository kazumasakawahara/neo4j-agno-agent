# 抽出 Few-Shot 例集

> `extraction_core.md` を補足する多様な抽出例。実運用で Claude が参照しやすいよう、短文・長文・複合ケースをカバー。

---

## 例1: 最小日報（1イベント）

**入力**:
> 山田健太さん、2026/4/12、パニックになったがイヤーマフで5分で落ち着いた。担当: 佐藤。

**出力**:
```json
{
  "nodes": [
    {"temp_id": "c1", "label": "Client", "mergeKey": {"name": "山田健太"}, "properties": {"name": "山田健太"}},
    {"temp_id": "s1", "label": "Supporter", "mergeKey": {"name": "佐藤"}, "properties": {"name": "佐藤"}},
    {"temp_id": "log1", "label": "SupportLog", "properties": {"date": "2026-04-12", "situation": "パニック時", "action": "イヤーマフ装着", "effectiveness": "Effective", "note": "5分で落ち着いた"}},
    {"temp_id": "cp1", "label": "CarePreference", "mergeKey": {"category": "パニック時", "instruction": "イヤーマフを装着させる"}, "properties": {"category": "パニック時", "instruction": "イヤーマフを装着させる", "priority": "High"}}
  ],
  "relationships": [
    {"source_temp_id": "s1", "target_temp_id": "log1", "type": "LOGGED", "properties": {}},
    {"source_temp_id": "log1", "target_temp_id": "c1", "type": "ABOUT", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "cp1", "type": "REQUIRES", "properties": {}}
  ],
  "warnings": []
}
```

---

## 例2: 家族聴き取り（複合情報）

**入力**:
> 田中美咲（平成8年5月1日生まれ）は自閉スペクトラム症。療育手帳B1、次回更新は2027年5月。母親の田中花子（電話 090-1234-5678）が主たる支援者。成年後見人は佐々木弁護士（佐々木法律事務所、03-1111-2222）。かかりつけは中央病院の小児科、担当医は高橋先生。大きな音と明るすぎる光が苦手で、これらでパニックを起こすことがある。音楽を聴かせると落ち着く傾向がある。

**出力**:
```json
{
  "nodes": [
    {"temp_id": "c1", "label": "Client", "mergeKey": {"name": "田中美咲"}, "properties": {"name": "田中美咲", "dob": "1996-05-01"}},
    {"temp_id": "con1", "label": "Condition", "mergeKey": {"name": "自閉スペクトラム症"}, "properties": {"name": "自閉スペクトラム症", "status": "Active"}},
    {"temp_id": "cert1", "label": "Certificate", "mergeKey": {"type": "療育手帳"}, "properties": {"type": "療育手帳", "grade": "B1", "nextRenewalDate": "2027-05-01"}},
    {"temp_id": "kp1", "label": "KeyPerson", "mergeKey": {"name": "田中花子"}, "properties": {"name": "田中花子", "relationship": "母", "phone": "090-1234-5678", "role": "主たる支援者"}},
    {"temp_id": "g1", "label": "Guardian", "mergeKey": {"name": "佐々木弁護士"}, "properties": {"name": "佐々木弁護士", "type": "成年後見人", "phone": "03-1111-2222", "organization": "佐々木法律事務所"}},
    {"temp_id": "h1", "label": "Hospital", "mergeKey": {"name": "中央病院"}, "properties": {"name": "中央病院", "specialty": "小児科", "doctor": "高橋"}},
    {"temp_id": "ng1", "label": "NgAction", "mergeKey": {"action": "大きな音"}, "properties": {"action": "大きな音", "reason": "パニックを誘発", "riskLevel": "Panic"}},
    {"temp_id": "ng2", "label": "NgAction", "mergeKey": {"action": "明るすぎる光"}, "properties": {"action": "明るすぎる光", "reason": "パニックを誘発", "riskLevel": "Panic"}},
    {"temp_id": "cp1", "label": "CarePreference", "mergeKey": {"category": "落ち着かせる", "instruction": "音楽を聴かせる"}, "properties": {"category": "落ち着かせる", "instruction": "音楽を聴かせる", "priority": "Medium"}}
  ],
  "relationships": [
    {"source_temp_id": "c1", "target_temp_id": "con1", "type": "HAS_CONDITION", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "cert1", "type": "HAS_CERTIFICATE", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "kp1", "type": "HAS_KEY_PERSON", "properties": {"rank": 1}},
    {"source_temp_id": "c1", "target_temp_id": "g1", "type": "HAS_LEGAL_REP", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "h1", "type": "TREATED_AT", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "ng1", "type": "MUST_AVOID", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "ng2", "type": "MUST_AVOID", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "cp1", "type": "REQUIRES", "properties": {}},
    {"source_temp_id": "ng1", "target_temp_id": "con1", "type": "IN_CONTEXT", "properties": {}},
    {"source_temp_id": "ng2", "target_temp_id": "con1", "type": "IN_CONTEXT", "properties": {}}
  ],
  "warnings": []
}
```

---

## 例3: 生育歴（LifeHistory + 因果）

**入力**:
> 鈴木隆さんは幼児期（3歳頃）に高熱でけいれんを起こしたことがあり、その後言葉の発達が遅れた。小学校入学時に知的障害と診断された。中学時代は不登校気味で、特別支援学級に在籍していた。

**出力**:
```json
{
  "nodes": [
    {"temp_id": "c1", "label": "Client", "mergeKey": {"name": "鈴木隆"}, "properties": {"name": "鈴木隆"}},
    {"temp_id": "lh1", "label": "LifeHistory", "properties": {"era": "幼児期", "episode": "3歳頃に高熱でけいれんを起こした"}},
    {"temp_id": "lh2", "label": "LifeHistory", "properties": {"era": "幼児期", "episode": "けいれん後、言葉の発達が遅れた"}},
    {"temp_id": "lh3", "label": "LifeHistory", "properties": {"era": "学齢期前半", "episode": "小学校入学時に知的障害と診断"}},
    {"temp_id": "lh4", "label": "LifeHistory", "properties": {"era": "学齢期後半", "episode": "中学時代は不登校気味、特別支援学級在籍"}},
    {"temp_id": "con1", "label": "Condition", "mergeKey": {"name": "知的障害"}, "properties": {"name": "知的障害", "status": "Active"}}
  ],
  "relationships": [
    {"source_temp_id": "c1", "target_temp_id": "lh1", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "lh2", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "lh3", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "lh4", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "con1", "type": "HAS_CONDITION", "properties": {}}
  ],
  "warnings": [
    "けいれんと言葉の発達遅延の因果関係は『その後〜』という記述から推定されていますが、医学的確定ではありません。診断名の確認を推奨します。"
  ]
}
```

---

## 例4: 願い（Wish）を含む面談

**入力**:
> 面談記録（2026-04-10、担当: 山本相談員）。本人（佐藤健一）から「将来はひとり暮らしをしたい」「料理を自分でできるようになりたい」と希望の表明があった。母親は心配しているが、本人の意思を尊重したいと言っている。

**出力**:
```json
{
  "nodes": [
    {"temp_id": "c1", "label": "Client", "mergeKey": {"name": "佐藤健一"}, "properties": {"name": "佐藤健一"}},
    {"temp_id": "s1", "label": "Supporter", "mergeKey": {"name": "山本"}, "properties": {"name": "山本", "role": "相談員"}},
    {"temp_id": "w1", "label": "Wish", "properties": {"content": "将来はひとり暮らしをしたい", "status": "Active", "date": "2026-04-10"}},
    {"temp_id": "w2", "label": "Wish", "properties": {"content": "料理を自分でできるようになりたい", "status": "Active", "date": "2026-04-10"}},
    {"temp_id": "log1", "label": "SupportLog", "properties": {"date": "2026-04-10", "situation": "面談", "action": "本人の希望を聴取", "effectiveness": "Unknown", "note": "母親は心配だが本人の意思を尊重する方針", "type": "会議"}}
  ],
  "relationships": [
    {"source_temp_id": "c1", "target_temp_id": "w1", "type": "HAS_WISH", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "w2", "type": "HAS_WISH", "properties": {}},
    {"source_temp_id": "s1", "target_temp_id": "log1", "type": "LOGGED", "properties": {}},
    {"source_temp_id": "log1", "target_temp_id": "c1", "type": "ABOUT", "properties": {}}
  ],
  "warnings": []
}
```

---

## 例5: 情報不足で NgAction 生成を見送るケース

**入力**:
> 鈴木さん、今日もいつもの感じで過ごしました。

**出力**:
```json
{
  "nodes": [
    {"temp_id": "c1", "label": "Client", "mergeKey": {"name": "鈴木"}, "properties": {"name": "鈴木"}}
  ],
  "relationships": [],
  "warnings": [
    "入力が情報量不足のため SupportLog を生成していません。具体的な状況・対応・効果を記載した入力を推奨します。",
    "『いつもの感じ』の具体的内容が不明のため、既存 CarePreference との照合も行えません。"
  ]
}
```

この場合、Phase 3 のプレビューでは「登録対象なし」と表示し、ユーザーに追記を促すこと。
