# 日本語最適化エンドツーエンドテストケース

本ファイルは `narrative-intake` スキルの日本語最適化ルール（元号変換・親族呼称統合・NFC正規化・相対時間解決）が正しく機能することを確認するためのテストケース集である。

各ケースは以下の要素を含む:
- **入力**: 原文ナラティブ
- **期待される前処理結果**: 正規化・元号変換・敬称処理の内部ステップ
- **期待される graph JSON（抜粋）**: Phase 1 出力の主要ノード
- **期待される warnings**: 曖昧表現や未解決項目
- **検証ポイント**: 手動確認のためのチェックリスト

---

## テストケース 1: 元号変換を含む短い生育歴（昭和・平成・令和すべて含む）

### 入力

> 佐藤健太さんは昭和58年3月15日生まれ。平成7年4月に小学校入学。令和2年からB型作業所に通所している。

### 期待される前処理結果

- **正規化**: 入力は既に NFC 正規化済み。変更なし。
- **元号変換**:
  - 昭和58年3月15日 → `1983-03-15`
  - 平成7年4月 → `1995-04`
  - 令和2年 → `2020`
- **敬称処理**: 「佐藤健太さん」→ mergeKey 用: `佐藤健太`、displayName: `佐藤健太さん`

### 期待される graph JSON（抜粋）

```json
{
  "nodes": [
    {
      "temp_id": "c1",
      "label": "Client",
      "mergeKey": {"name": "佐藤健太"},
      "properties": {
        "name": "佐藤健太",
        "displayName": "佐藤健太さん",
        "dob": "1983-03-15"
      }
    },
    {
      "temp_id": "lh1",
      "label": "LifeHistory",
      "properties": {
        "lifeStage": "学齢期前半",
        "period": "1995-04",
        "periodPrecision": "month",
        "description": "小学校入学"
      }
    },
    {
      "temp_id": "lh2",
      "label": "LifeHistory",
      "properties": {
        "lifeStage": "成人期",
        "period": "2020",
        "periodPrecision": "year",
        "description": "B型作業所に通所開始"
      }
    }
  ],
  "relationships": [
    {"source_temp_id": "c1", "target_temp_id": "lh1", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "lh2", "type": "HAS_HISTORY", "properties": {}}
  ],
  "warnings": []
}
```

### 期待される warnings

なし（3つの元号すべてが絶対日付に変換される）。

### 検証ポイント

- [ ] `dob` が `1983-03-15`（昭和58年=1983年）になっている
- [ ] 小学校入学が `1995-04`（平成7年=1995年）になっている
- [ ] B型作業所の `period` が `2020`（令和2年=2020年）になっている
- [ ] 原文に「昭和」「平成」「令和」の文字が残っていない
- [ ] warnings 配列が空

---

## テストケース 2: 親族呼称の統合が必要な家族聴き取り

### 入力

> 田中花子さん（1990年5月10日生まれ）の家族構成: お母さんは介護中で、実母は同居している。お父さんは他界。お兄さんが緊急連絡先で、090-1111-2222。

### 期待される前処理結果

- **親族呼称の統一**:
  - 「お母さん」「実母」→ 同一人物として `母` に統一
  - 「お父さん」→ `父`
  - 「お兄さん」→ `兄`
- **敬称処理**: 「田中花子さん」→ mergeKey: `田中花子`
- **整合性確認**: 「お母さん」と「実母」は文脈上同一人物と判定

### 期待される graph JSON（抜粋）

```json
{
  "nodes": [
    {
      "temp_id": "c1",
      "label": "Client",
      "mergeKey": {"name": "田中花子"},
      "properties": {"name": "田中花子", "dob": "1990-05-10"}
    },
    {
      "temp_id": "kp1",
      "label": "KeyPerson",
      "mergeKey": {"name": "母", "clientName": "田中花子"},
      "properties": {"name": "母", "relationship": "母", "note": "介護中、同居"}
    },
    {
      "temp_id": "kp2",
      "label": "KeyPerson",
      "mergeKey": {"name": "兄", "clientName": "田中花子"},
      "properties": {"name": "兄", "relationship": "兄", "phone": "090-1111-2222", "rank": 1}
    }
  ],
  "relationships": [
    {"source_temp_id": "c1", "target_temp_id": "kp1", "type": "HAS_KEY_PERSON", "properties": {"rank": 2}},
    {"source_temp_id": "c1", "target_temp_id": "kp2", "type": "HAS_KEY_PERSON", "properties": {"rank": 1}}
  ],
  "warnings": [
    "父は他界のため KeyPerson として登録していません"
  ]
}
```

### 期待される warnings

- 父が他界のため KeyPerson に含めない旨の記録

### 検証ポイント

- [ ] 「お母さん」「実母」が1つの KeyPerson ノード（name: "母"）にまとまっている
- [ ] 「お兄さん」が KeyPerson（name: "兄"）として rank:1 で登録されている
- [ ] 父（他界）が KeyPerson として生成されていない
- [ ] 電話番号が `090-1111-2222` の形式で保存されている

---

## テストケース 3: 半角カタカナ・全角数字混在の支援記録

### 入力

> ２０２６年３月９日、ﾔﾏﾀﾞ ﾀﾛｳさんの記録。ﾊﾟﾆｯｸ時にイヤーマフを装着したところ、５分で落ち着いた。ＡＢＣ事業所での対応。

### 期待される前処理結果

- **NFC 正規化**:
  - 全角数字 `２０２６` → `2026`、`３` → `3`、`９` → `9`、`５` → `5`
  - 半角カタカナ `ﾔﾏﾀﾞ ﾀﾛｳ` → `ヤマダ タロウ`
  - 半角カタカナ `ﾊﾟﾆｯｸ` → `パニック`
  - 全角英字 `ＡＢＣ` → `ABC`
  - 記号（全角スペース等）はそのまま維持

### 期待される graph JSON（抜粋）

```json
{
  "nodes": [
    {
      "temp_id": "c1",
      "label": "Client",
      "mergeKey": {"name": "ヤマダ タロウ"},
      "properties": {"name": "ヤマダ タロウ"}
    },
    {
      "temp_id": "log1",
      "label": "SupportLog",
      "properties": {
        "date": "2026-03-09",
        "situation": "パニック時",
        "action": "イヤーマフを装着",
        "effectiveness": "Effective",
        "note": "5分で落ち着いた。ABC事業所での対応。"
      }
    }
  ],
  "relationships": [
    {"source_temp_id": "log1", "target_temp_id": "c1", "type": "ABOUT", "properties": {}}
  ],
  "warnings": []
}
```

### 期待される warnings

なし。

### 検証ポイント

- [ ] 日付が `2026-03-09`（全角数字→半角変換済み）になっている
- [ ] 氏名が「ヤマダ タロウ」（半角カナ→全角カナ変換済み）になっている
- [ ] 「パニック」が全角カタカナで統一されている
- [ ] 「ABC」が半角英字になっている
- [ ] situation/action に半角カナや全角数字が残っていない

---

## テストケース 4: 相対時間表現「翌年」「同月」「3歳の時」を含む長文

### 入力

> 鈴木一郎さん（昭和55年10月20日生まれ）の生育歴。3歳の時、発達検査で広汎性発達障害と診断された。平成10年4月、A型作業所に通所開始。翌年、体調不良で一時中断した。同月、主治医が交代した。

### 期待される前処理結果

- **元号変換**:
  - 昭和55年10月20日 → `1980-10-20`（Client.dob）
  - 平成10年4月 → `1998-04`（アンカー1）
- **相対時間解決**:
  - 「3歳の時」→ カテゴリ C（年齢ベース）: `1980 + 3 = 1983`（precision: approximate）
  - 「翌年」→ カテゴリ A（直接相対）: アンカー `1998-04` + 1年 = `1999`
  - 「同月」→ カテゴリ B（同一基準）: 直前の「翌年」= `1999` → 月情報なしのため `1999`

### 期待される graph JSON（抜粋）

```json
{
  "nodes": [
    {
      "temp_id": "c1",
      "label": "Client",
      "mergeKey": {"name": "鈴木一郎"},
      "properties": {"name": "鈴木一郎", "dob": "1980-10-20"}
    },
    {
      "temp_id": "cond1",
      "label": "Condition",
      "mergeKey": {"name": "広汎性発達障害"},
      "properties": {
        "name": "広汎性発達障害",
        "diagnosedDate": "1983",
        "diagnosedDatePrecision": "approximate",
        "notes": "原文: 『3歳の時』"
      }
    },
    {
      "temp_id": "lh1",
      "label": "LifeHistory",
      "properties": {
        "lifeStage": "成人期",
        "period": "1998-04",
        "periodPrecision": "month",
        "description": "A型作業所に通所開始"
      }
    },
    {
      "temp_id": "lh2",
      "label": "LifeHistory",
      "properties": {
        "lifeStage": "成人期",
        "period": "1999",
        "periodPrecision": "year",
        "description": "体調不良で一時中断",
        "notes": "原文: 『翌年、体調不良で一時中断した』"
      }
    }
  ],
  "relationships": [
    {"source_temp_id": "c1", "target_temp_id": "cond1", "type": "HAS_CONDITION", "properties": {"diagnosedDate": "1983"}},
    {"source_temp_id": "c1", "target_temp_id": "lh1", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "lh2", "type": "HAS_HISTORY", "properties": {}},
    {"source_temp_id": "lh1", "target_temp_id": "lh2", "type": "FOLLOWS", "properties": {}}
  ],
  "warnings": []
}
```

### 期待される warnings

なし（すべての相対時間が解決可能）。

### 検証ポイント

- [ ] 「3歳の時」が `1983` に変換されている（dob ベース）
- [ ] `diagnosedDatePrecision` が `approximate` になっている
- [ ] 「翌年」が `1999`（1998 + 1）に変換されている
- [ ] 「同月」が直前のアンカーから解決されている
- [ ] 時系列順に `FOLLOWS` リレーションが生成されている

---

## テストケース 5: 解決不可な曖昧表現（「最近」「若い頃」）を含む記録

### 入力

> 山田花子さんの記録。最近、作業所の人間関係で悩んでいる様子。若い頃は音楽が好きだったとお母さんが話していた。

### 期待される前処理結果

- **親族呼称**: 「お母さん」→ `母`
- **相対時間解決**:
  - 「最近」→ カテゴリ E（曖昧表現）: 解決不可、warnings 記録
  - 「若い頃」→ カテゴリ E（曖昧表現）: 解決不可、warnings 記録

### 期待される graph JSON（抜粋）

```json
{
  "nodes": [
    {
      "temp_id": "c1",
      "label": "Client",
      "mergeKey": {"name": "山田花子"},
      "properties": {"name": "山田花子"}
    },
    {
      "temp_id": "log1",
      "label": "SupportLog",
      "properties": {
        "situation": "対人関係",
        "note": "作業所の人間関係で悩んでいる様子",
        "notes": "原文の記載時期不明"
      }
    },
    {
      "temp_id": "cp1",
      "label": "CarePreference",
      "mergeKey": {"category": "趣味", "instruction": "音楽"},
      "properties": {
        "category": "趣味",
        "instruction": "音楽が好き",
        "priority": "Low",
        "notes": "母からの情報、若い頃の記憶"
      }
    }
  ],
  "relationships": [
    {"source_temp_id": "log1", "target_temp_id": "c1", "type": "ABOUT", "properties": {}},
    {"source_temp_id": "c1", "target_temp_id": "cp1", "type": "REQUIRES", "properties": {}}
  ],
  "warnings": [
    "曖昧表現『最近』: 絶対日付への変換を保留しました",
    "曖昧表現『若い頃』: 絶対日付への変換を保留しました"
  ]
}
```

### 期待される warnings

- 「最近」の解決不可の記録
- 「若い頃」の解決不可の記録

### 検証ポイント

- [ ] 「最近」「若い頃」が日付プロパティに入っていない
- [ ] warnings に2件の曖昧表現記録が含まれている
- [ ] SupportLog の `notes` に原文の時期不明である旨が残っている
- [ ] 「お母さん」が話し手として文脈的に認識されている（直接 KeyPerson 化するかは抽出判断）

---

## 共通検証コマンド

各テストケースを Claude Desktop で実行後、以下を確認する:

```bash
# JSON 構文が valid か
python3 -c "import json; json.loads('''<Phase 1 出力>''')"

# 元号文字が残っていないか（昭和・平成・令和を除き、変換済みのはず）
grep -E '(昭和|平成|令和)' <output.json>
# → 空出力であれば OK（残っていれば警告）

# 日付形式の確認
grep -oE '"dob":\s*"[0-9]{4}-[0-9]{2}-[0-9]{2}"' <output.json>
```

## 期待される全体挙動

1. **5ケースすべてで**、元号が西暦に変換され、原文表記が `notes` や `displayName` として保持されること
2. **5ケースすべてで**、親族呼称が `schema/honorific_dict.json` の canonical 形に統一されること
3. **ケース3**で、半角カタカナ・全角数字・全角英字が正しく NFC 正規化されること
4. **ケース4**で、直接相対・同一基準・年齢ベースの相対時間がすべて解決されること
5. **ケース5**で、曖昧表現が warnings に記録され、日付プロパティに誤って入らないこと
