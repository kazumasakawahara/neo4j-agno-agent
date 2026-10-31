# Neo4jブラウザ可視化ガイド

親亡き後支援データベースのNeo4jブラウザでの可視化方法を解説します。

## 📋 目次

1. [初期セットアップ](#初期セットアップ)
2. [.grassスタイリングの適用](#grassスタイリングの適用)
3. [ノードの色分け一覧](#ノードの色分け一覧)
4. [探索用クエリの使い方](#探索用クエリの使い方)
5. [よくある可視化パターン](#よくある可視化パターン)

---

## 初期セットアップ

### 1. スキーマとインデックスの作成

Neo4jブラウザで以下のファイルを実行してください：

```bash
# queries/schema_setup.cypher の内容を実行
```

このスクリプトは以下を実行します：
- **インデックス作成**: クライアント名、禁忌リスクレベル、支援記録日付などの高速検索
- **ユニーク制約**: クライアント名の重複防止
- **サンプルデータ**: 「サンプル太郎」さんのテストデータ投入

実行後、以下のコマンドでインデックスを確認：
```cypher
SHOW INDEXES;
```

---

## .grassスタイリングの適用

### ステップ1: .grassファイルを開く

Neo4jブラウザの画面で：
1. 左下の **⚙️ 設定アイコン** をクリック
2. **Graph Stylesheet** セクションを探す
3. テキストエリアをクリック

### ステップ2: スタイルを貼り付け

`queries/neo4j_browser_style.grass` の内容を全てコピーして、Graph Stylesheetエリアに貼り付けます。

### ステップ3: 適用を確認

簡単なクエリで確認：
```cypher
MATCH (c:Client)-[r]->(n)
RETURN c, r, n
LIMIT 25
```

正しく適用されていれば、ノードが色分けされて表示されます。

---

## ノードの色分け一覧

### 🔵 第1の柱：本人性（Identity & Narrative）

| ノードタイプ | 色 | サイズ | 意味 |
|-------------|-----|--------|------|
| **Client** | 青 (#4A90E2) | 80px | 最重要・中心ノード |
| **LifeHistory** | 紫 (#7B68EE) | 45px | 人生の歴史 |
| **Wish** | 金 (#FFD700) | 45px | 本人の願い |

### 🟢 第2の柱：ケアの暗黙知（Care Instructions）

| ノードタイプ | 色 | サイズ | 意味 |
|-------------|-----|--------|------|
| **NgAction** | 赤 (#E74C3C) | 60px | **禁忌事項（最重要）** |
| **CarePreference** | 緑 (#2ECC71) | 55px | 推奨ケア |
| **Condition** | 紫 (#9B59B6) | 50px | 特性・診断 |

### 🟠 Living Database（経験値蓄積）

| ノードタイプ | 色 | サイズ | 意味 |
|-------------|-----|--------|------|
| **SupportLog** | オレンジ (#F39C12) | 50px | 支援記録 |
| **Supporter** | ティール (#1ABC9C) | 50px | 支援者 |
| **CarePattern** | 青 (#3498DB) | 55px | 発見されたパターン |

### ⚪ 第3の柱：法的基盤（Legal Basis）

| ノードタイプ | 色 | サイズ | 意味 |
|-------------|-----|--------|------|
| **Certificate** | グレー (#607D8B) | 50px | 手帳・受給者証 |
| **PublicAssistance** | ブラウン (#795548) | 48px | 公的支援 |

### 🔴 第4の柱：危機管理ネットワーク（Crisis Network）

| ノードタイプ | 色 | サイズ | 意味 |
|-------------|-----|--------|------|
| **KeyPerson** | ピンク (#E91E63) | 52px | 緊急連絡先 |
| **Guardian** | オレンジレッド (#FF5722) | 52px | 後見人 |
| **Lawyer** | オレンジ (#FF6F00) | 50px | 弁護士 |
| **Hospital** | シアン (#00BCD4) | 50px | 病院 |

### リレーションシップの色分け

> **命名規則**: 正式名は右側。左側は廃止済み（後方互換のため .grass に残存）。
> 詳細は `docs/NEO4J_SCHEMA_CONVENTION.md` を参照。

| リレーション | 色 | 太さ | 意味 |
|-------------|-----|------|------|
| **MUST_AVOID** (旧: PROHIBITED) | 赤 | 3px | 禁忌（最重要） |
| **REQUIRES** (旧: PREFERS) | 緑 | 2px | 推奨 |
| **LOGGED** / **ABOUT** | オレンジ | 1.5px | 記録 |
| **HAS_KEY_PERSON** (旧: EMERGENCY_CONTACT) | ピンク | 2px | 緊急連絡 |

---

## 探索用クエリの使い方

`queries/exploration_queries.cypher` には30個の事前作成クエリが含まれています。

### クイックスタート：よく使うクエリ

#### 1️⃣ クライアント全体像を見る
```cypher
// 【1】特定クライアントの全データ可視化
MATCH path = (c:Client {name: '山田健太'})-[*1..2]-(n)
RETURN path
LIMIT 100;
```

**見方**:
- 中心に **青い大きなノード（Client）** が表示
- 周囲に **赤い禁忌（NgAction）**、**緑の推奨ケア（CarePreference）** などが配置
- クリックすると詳細情報が表示されます

#### 2️⃣ 禁忌事項だけを見る（緊急時）
```cypher
// 【4】禁忌事項マップ（緊急時用）
MATCH (c:Client {name: '山田健太'})-[:MUST_AVOID|PROHIBITED]->(ng:NgAction)
RETURN c, ng;
```

**見方**:
- **赤い太い線** と **赤い大きなノード** で禁忌が強調表示
- リスクレベルが高い順に確認

#### 3️⃣ 支援記録のタイムライン
```cypher
// 【9】支援記録タイムライン
MATCH (s:Supporter)-[:LOGGED]->(log:SupportLog)-[:ABOUT]->(c:Client {name: '山田健太'})
RETURN s, log, c
ORDER BY log.date DESC
LIMIT 20;
```

**見方**:
- **オレンジのノード（SupportLog）** が時系列で表示
- **ティールのノード（Supporter）** で誰が記録したかわかる

#### 4️⃣ 効果的だったパターンを発見
```cypher
// 【10】効果的だった支援記録（頻度順）
MATCH (c:Client {name: '山田健太'})<-[:ABOUT]-(log:SupportLog)
WHERE log.effectiveness = 'Effective'
WITH c, log.situation as 状況, log.action as 対応, count(*) as 頻度
WHERE 頻度 >= 2
RETURN c.name as クライアント, 状況, 対応, 頻度
ORDER BY 頻度 DESC;
```

**見方**:
- テーブル形式で結果が表示
- 頻度が高い対応 = 確立された効果的なケアパターン

#### 5️⃣ 緊急連絡網を見る
```cypher
// 【15】緊急連絡網の可視化
MATCH (c:Client {name: '山田健太'})-[:HAS_KEY_PERSON|EMERGENCY_CONTACT]->(kp:KeyPerson)
OPTIONAL MATCH (c)-[:HAS_LEGAL_REP|HAS_GUARDIAN]->(g:Guardian)
RETURN c, kp, g;
```

**見方**:
- **ピンクのノード（KeyPerson）** = 緊急連絡先
- **オレンジレッドのノード（Guardian）** = 後見人
- 全て一画面で確認可能

---

## よくある可視化パターン

### パターン1: 新規クライアント登録後の確認

```cypher
// データが正しく登録されたか確認
MATCH (c:Client {name: 'クライアント名'})
OPTIONAL MATCH (c)-[r]->(n)
RETURN c, r, n;
```

**チェックポイント**:
- ✅ Clientノードが中心に表示される
- ✅ NgAction（赤）が存在するか
- ✅ CarePreference（緑）が存在するか
- ✅ KeyPerson（ピンク）が登録されているか

### パターン2: 支援者の活動状況を把握

```cypher
// 【13】支援者別の記録件数ランキング
MATCH (s:Supporter)-[:LOGGED]->(log:SupportLog)
WITH s, count(log) as 記録件数
RETURN s.name as 支援者名, 記録件数
ORDER BY 記録件数 DESC;
```

### パターン3: データ品質チェック

```cypher
// 【22】緊急連絡先が未登録のクライアント
MATCH (c:Client)
WHERE NOT (c)-[:HAS_KEY_PERSON]->(:KeyPerson)
RETURN c.name as クライアント名, '緊急連絡先なし' as 警告;
```

### パターン4: 手帳更新期限の確認

```cypher
// 【18】手帳・受給者証の一覧と有効期限
MATCH (c:Client)-[:HAS_CERTIFICATE|HOLDS]->(cert:Certificate)
RETURN c.name as クライアント,
       cert.type as 種類,
       cert.grade as 等級,
       cert.issueDate as 交付日,
       cert.nextRenewalDate as 次回更新日
ORDER BY cert.nextRenewalDate;
```

---

## ビジュアル探索のコツ

### 1. ズームとパン操作
- **マウスホイール**: ズームイン/アウト
- **ドラッグ**: グラフ全体を移動
- **ノードをドラッグ**: レイアウトを手動調整

### 2. ノードの展開
- ノードをダブルクリック → 関連ノードを展開
- 右クリック → "Expand / Collapse" で接続を表示/非表示

### 3. フィルタリング
- 特定のリレーションだけ見たい場合：
  ```cypher
  MATCH (c:Client)-[:MUST_AVOID|PROHIBITED]->(ng:NgAction)
  RETURN c, ng;  // 禁忌だけ表示
  ```

### 4. 大量データの扱い
- `LIMIT` を必ず使用（例: `LIMIT 50`）
- 範囲指定で段階的に探索：
  ```cypher
  MATCH path = (c:Client)-[*1]-(n)  // 1ホップ先まで
  RETURN path LIMIT 30;
  ```

---

## トラブルシューティング

### Q: スタイルが適用されない
**A**:
1. .grassファイルの内容を再度コピー&ペースト
2. Neo4jブラウザをリロード（F5）
3. クエリを再実行

### Q: ノードが多すぎて見づらい
**A**:
1. `LIMIT` を小さくする（例: `LIMIT 10`）
2. 特定のリレーションだけ表示（例: `[:MUST_AVOID|PROHIBITED]`）
3. 特定のノードタイプだけ表示（例: `MATCH (ng:NgAction)`）

### Q: クライアント名がわからない
**A**:
```cypher
// 【2】全クライアント一覧
MATCH (c:Client)
RETURN c.name as 氏名, c.dob as 生年月日
ORDER BY c.name;
```

### Q: データが登録されているか不安
**A**:
```cypher
// 【25】データベース統計（全体像）
MATCH (n)
RETURN labels(n)[0] as ノードタイプ, count(*) as 件数
ORDER BY 件数 DESC;
```

---

## 次のステップ

1. **実際のデータで試す**: Streamlit UIまたはMCPツールでデータを登録
2. **カスタムクエリ**: `exploration_queries.cypher` を参考に独自クエリを作成
3. **定期的な可視化**: 毎週末に支援記録の可視化で振り返り
4. **パターン発見**: 効果的なケアパターンを定期的に抽出

---

**関連ファイル**:
- `queries/schema_setup.cypher` - スキーマ定義
- `queries/neo4j_browser_style.grass` - スタイリング定義
- `queries/exploration_queries.cypher` - 30個の探索クエリ集
