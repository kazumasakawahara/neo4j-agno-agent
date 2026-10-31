# 例: 生育歴ナラティブの取り込み（長文チャンキング）

## 入力（家族聴き取りマニュアルの抜粋）

```
（対象: 田中隆、昭和63年4月生まれ）

■ 幼児期
3歳頃から言葉の遅れを家族が気にし始めた。集団保育に馴染めず、
音や光の刺激に過敏反応を示した。4歳で療育センターを紹介され、
5歳時に自閉スペクトラム症の診断を受けた。

■ 学齢期前半
小学校は地域の通常学級に入学したが、教室のざわめきや給食の匂いで
頻繁にパニックを起こした。2年生から特別支援学級に移り、
個別対応を受けるようになった。この頃、絵を描くことが
気持ちを落ち着ける手段として確立した。

■ 学齢期後半
中学校でも特別支援学級を継続。担任の佐藤先生との
相性が良く、この時期は比較的安定していた。卒業後の
進路相談を母親と一緒に繰り返した。

■ 青年期
高等特別支援学校を経て、20歳から地域の就労継続支援B型事業所
「ひだまり」に通い始めた。現在も継続中。
```

---

## チャンキング戦略

この入力は章見出し（■で始まる）で自然に分割できるため、**4チャンクに分割して処理**する:

| チャンク | 章 | era（LifeHistory.era） |
|---|---|---|
| 1 | 幼児期 | 幼児期 |
| 2 | 学齢期前半 | 学齢期前半 |
| 3 | 学齢期後半 | 学齢期後半 |
| 4 | 青年期 | 青年期 |

各チャンクの抽出時、先頭に `【対象クライアント: 田中隆】` を付与し、`temp_id` は `ch01_*`, `ch02_*` のように接頭辞を付ける。

---

## 統合後のグラフ JSON（概要）

```json
{
  "nodes": [
    {"temp_id": "c1", "label": "Client", "mergeKey": {"name": "田中隆"}, "properties": {"name": "田中隆", "dob": "1988-04-01"}},

    {"temp_id": "con1", "label": "Condition", "mergeKey": {"name": "自閉スペクトラム症"}, "properties": {"name": "自閉スペクトラム症", "diagnosisDate": "1993-01-01", "status": "Active"}},

    {"temp_id": "ch01_lh1", "label": "LifeHistory", "properties": {"era": "幼児期", "episode": "3歳頃から言葉の遅れを家族が気にし始めた"}},
    {"temp_id": "ch01_lh2", "label": "LifeHistory", "properties": {"era": "幼児期", "episode": "4歳で療育センターを紹介、5歳で自閉スペクトラム症診断"}},

    {"temp_id": "ch02_lh1", "label": "LifeHistory", "properties": {"era": "学齢期前半", "episode": "小学校2年生から特別支援学級に移り個別対応"}},
    {"temp_id": "ch02_lh2", "label": "LifeHistory", "properties": {"era": "学齢期前半", "episode": "絵を描くことが気持ちを落ち着ける手段として確立"}},

    {"temp_id": "ch03_lh1", "label": "LifeHistory", "properties": {"era": "学齢期後半", "episode": "中学校は特別支援学級、担任の佐藤先生と相性が良く安定していた"}},

    {"temp_id": "ch04_lh1", "label": "LifeHistory", "properties": {"era": "青年期", "episode": "20歳から就労継続支援B型事業所「ひだまり」に通所（現在継続中）"}},

    {"temp_id": "ng1", "label": "NgAction", "mergeKey": {"action": "ざわめきや給食の匂いなど強い感覚刺激"}, "properties": {"action": "ざわめきや給食の匂いなど強い感覚刺激", "reason": "パニックを誘発", "riskLevel": "Panic"}},

    {"temp_id": "cp1", "label": "CarePreference", "mergeKey": {"category": "情緒安定", "instruction": "絵を描く時間を確保する"}, "properties": {"category": "情緒安定", "instruction": "絵を描く時間を確保する", "priority": "Medium"}},

    {"temp_id": "org1", "label": "Organization", "mergeKey": {"name": "ひだまり"}, "properties": {"name": "ひだまり", "type": "就労継続支援B型"}}
  ],
  "relationships": [
    {"source_temp_id": "c1", "target_temp_id": "con1", "type": "HAS_CONDITION", "properties": {"diagnosedDate": "1993-01-01"}},
    {"source_temp_id": "c1", "target_temp_id": "ch01_lh1", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "ch01_lh2", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "ch02_lh1", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "ch02_lh2", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "ch03_lh1", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "ch04_lh1", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "ng1", "type": "MUST_AVOID", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "cp1", "type": "REQUIRES", "properties": {}},
    {"source_temp_id": "ng1", "target_temp_id": "con1", "type": "IN_CONTEXT", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "org1", "type": "REGISTERED_AT", "properties": {}}
  ],
  "warnings": [
    "『担任の佐藤先生』は実在の個人名として抽出されていますが、KeyPerson としての登録は明示されていないため Person ノード化を見送りました。必要であれば別途登録を推奨します。"
  ]
}
```

---

## プレビュー概要

```
▼ チャンキング情報
  総チャンク数: 4（幼児期/学齢期前半/学齢期後半/青年期）
  重複統合: Condition×1（自閉スペクトラム症）をチャンク間統合

▼ 新規/更新ノード
  [MERGE] Client × 1
  [MERGE] Condition × 1
  [NEW]   LifeHistory × 6
  [MERGE] NgAction × 1
  [MERGE] CarePreference × 1
  [MERGE] Organization × 1

▼ リレーション
  HAS_CONDITION × 1, HAS_HISTORY × 6, MUST_AVOID × 1,
  REQUIRES × 1, IN_CONTEXT × 1, REGISTERED_AT × 1

▼ 注意事項（warnings）
  - 『担任の佐藤先生』は個人名ですが KeyPerson 化は見送り
```
