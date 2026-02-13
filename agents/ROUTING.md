# スキル＆Neo4j MCPルーティングガイド

**目的:** 5つのスキルとNeo4j MCPツールの使い分けを定義する。

**アーキテクチャ:** 各スキルはCypherテンプレートを提供し、汎用 neo4j MCP の `read_neo4j_cypher` / `write_neo4j_cypher` で実行する。

---

## スキル一覧

### 1. neo4j-support-db（計画相談支援）

**SKILL.md:** `~/.claude/skills/neo4j-support-db/SKILL.md`
**Neo4jインスタンス:** `bolt://localhost:7687`
**対象業務:** 障害福祉サービスの利用調整、計画相談支援

**トリガーワード:**
- クライアント名（山田健太、佐々木真理 等）
- パニック、緊急、禁忌、支援記録
- キーパーソン、手帳、更新期限、後見人
- 配慮事項、ケアパターン、生育歴

**Cypherテンプレート（8種）:**

| # | テンプレート | 用途 | 種別 |
|---|------------|------|------|
| 1 | クライアント一覧 | 全クライアントの基本情報と関連データ件数 | read |
| 2 | クライアントプロフィール | 4本柱の包括的情報（NgAction/CarePreference/KeyPerson/Certificate等） | read |
| 3 | 統計情報 | ノードタイプ別件数とリレーション数 | read |
| 4 | 更新期限チェック | N日以内に期限切れの手帳・受給者証 | read |
| 5 | 支援記録取得 | クライアントの支援記録履歴 | read |
| 6 | ケアパターン発見 | 効果的だった対応の自動検出 | read |
| 7 | 監査ログ | 操作履歴の確認 | read |
| 8 | 変更履歴 | クライアント情報の変更追跡 | read |

---

### 2. livelihood-support（生活困窮者自立支援）

**SKILL.md:** `~/.claude/skills/livelihood-support/SKILL.md`
**Neo4jインスタンス:** `bolt://localhost:7688`
**対象業務:** 生活保護受給者の自立支援、経済的搾取防止、金銭管理支援

**トリガーワード:**
- 受給者名
- 経済的リスク、搾取、金銭管理、お金がない
- 訪問前、ブリーフィング、引き継ぎ
- NG、避けるべき、効果的
- 多機関連携、ケース会議
- 類似ケース

**Cypherテンプレート（12種）:**

| # | テンプレート | 用途 | 種別 |
|---|------------|------|------|
| 1 | 受給者一覧 | 全受給者の基本情報 | read |
| 2a-d | プロフィール（7本柱） | 包括的情報（4分割取得） | read |
| 3 | 統計情報 | ノードタイプ別件数 | read |
| 4 | 更新期限チェック | N日以内に期限切れの証明書 | read |
| 5 | ケース記録取得 | 受給者のケース記録履歴 | read |
| 6 | 効果的パターン発見 | 効果的だった関わり方の検出 | read |
| 7 | 監査ログ | 操作履歴の確認 | read |
| 8 | 変更履歴 | 受給者情報の変更追跡 | read |
| 9 | 訪問前ブリーフィング | Safety First準拠の訪問準備情報 | read |
| 10 | 引き継ぎサマリー | 担当者交代用の包括的情報 | read |
| 11 | 類似案件検索 | 同様のリスクを持つケースの発見 | read |
| 12 | 多機関連携履歴 | ケース会議・情報共有の記録 | read |

---

### 3. provider-search（事業所検索・管理）

**SKILL.md:** `~/.claude/skills/provider-search/SKILL.md`
**Neo4jインスタンス:** `bolt://localhost:7687`（support-dbと同じ）
**対象業務:** 福祉サービス事業所の検索・利用管理・口コミ評価

**トリガーワード:**
- 事業所、空き状況、口コミ、評価
- サービス種類（生活介護、就労B型、グループホーム等）
- 代替、別の事業所、紐付け

**Cypherテンプレート（9種）:**

| # | テンプレート | 用途 | 種別 |
|---|------------|------|------|
| 1 | 事業所検索（基本） | サービス種類・地域・空きで絞り込み | read |
| 2 | クライアント利用事業所 | 利用中・調整中・終了のサービス一覧 | read |
| 3 | 代替事業所検索 | 利用中サービスの代替候補 | read |
| 4 | 口コミ取得 | 事業所の口コミ一覧 | read |
| 5 | 評価サマリー | 口コミの集計（◎○△×件数とスコア） | read |
| 6 | 口コミで事業所検索 | カテゴリ別の高評価事業所 | read |
| 7 | クライアント紐付け | クライアント↔事業所のUSES_SERVICE作成 | write |
| 8 | 口コミ登録 | ProviderFeedbackノード作成 | write |
| 9 | 空き状況更新 | availability/currentUsersの更新 | write |

**データ特記:** WAM NETインポートにより新形式(camelCase)と旧形式(snake_case)が混在。テンプレートはCOALESCEで統一処理。

---

### 4. emergency-protocol（緊急時プロトコル）

**SKILL.md:** `~/.claude/skills/emergency-protocol/SKILL.md`
**対象業務:** 緊急時の対応手順ガイド（データベース非依存）

**トリガーワード:**
- 緊急、SOS、倒れた、救急、パニック
- 親亡き後、急変

**内容:**
- 緊急対応フローチャート
- Safety Firstプロトコル
- Parent Downプロトコル（主介護者不在時）
- 関係機関への連絡手順

---

### 5. ecomap-generator（エコマップ生成）

**SKILL.md:** `~/.claude/skills/ecomap-generator/SKILL.md`
**対象業務:** 支援ネットワークの可視化

**トリガーワード:**
- エコマップ、ネットワーク図、支援関係図

**出力形式:** Mermaid / SVG

---

### 6. neo4j MCP（汎用データベースアクセス）

**接続先:** `bolt://localhost:7687`（デフォルト）

**ツール:**

| ツール | 用途 |
|--------|------|
| `get_neo4j_schema` | スキーマ取得 |
| `read_neo4j_cypher` | 読み取りクエリ実行 |
| `write_neo4j_cypher` | 書き込みクエリ実行 |

**重要:** スキルのCypherテンプレートはこのMCPツールで実行する。

---

## ルーティング判断フロー

```
ユーザー入力
│
├─ 緊急ワード検出？（パニック、SOS、倒れた、救急）
│  ├─ YES → emergency-protocol スキルで手順確認
│  │       └─ データ取得が必要な場合：
│  │           ├─ 障害福祉クライアント → neo4j-support-db テンプレート2
│  │           └─ 生活保護受給者 → livelihood-support テンプレート9（訪問前ブリーフィング）
│  └─ NO → 続行
│
├─ クライアント/受給者名が含まれる？
│  ├─ YES → どちらのDBに登録されているか確認
│  │       ├─ support-db（port 7687）→ neo4j-support-db スキル
│  │       ├─ livelihood-support（port 7688）→ livelihood-support スキル
│  │       └─ 不明 → 両方のテンプレート1（一覧）で確認
│  └─ NO → 続行
│
├─ 経済リスク・金銭管理・搾取に関する話題？
│  └─ YES → livelihood-support スキル
│
├─ 事業所検索・口コミに関する話題？
│  └─ YES → provider-search スキル
│
├─ 訪問前ブリーフィング・引き継ぎ？
│  └─ YES → livelihood-support スキル（テンプレート9, 10）
│
├─ エコマップ・ネットワーク図？
│  └─ YES → ecomap-generator スキル
│
├─ 一般的なNeo4j操作？（スキーマ確認、カスタムクエリ）
│  └─ YES → neo4j MCP を直接使用
│
└─ 判断不能
   └─ ユーザーに確認する
```

---

## Neo4jインスタンスの使い分け

2つの別インスタンスが稼働している。クエリ実行時は接続先に注意すること。

| インスタンス | Bolt | HTTP | 対象スキル |
|------------|------|------|-----------|
| support-db | localhost:7687 | localhost:7474 | neo4j-support-db, provider-search |
| livelihood-support | localhost:7688 | localhost:7475 | livelihood-support |

**`neo4j` MCP のデフォルト接続先は port 7687（support-db）。** livelihood-support のクエリは `neo4j-livelihood` MCP（port 7688）を使用すること。claude_desktop_config.json に両方のMCPが設定済み。

---

## データモデルの違い

### support-db（障害福祉）
- 中心ノード: `:Client`
- 禁忌: `:NgAction`（riskLevel付き）
- ケア指示: `:CarePreference`
- 支援記録: `:SupportLog`
- 事業所: `:ServiceProvider`, `:ProviderFeedback`

### livelihood-support（生活困窮者）
- 中心ノード: `:Recipient`
- 禁忌: `:NgApproach`（riskLevel付き）
- 効果的対応: `:EffectiveApproach`
- ケース記録: `:CaseRecord`
- 経済リスク: `:EconomicRisk`
- 金銭管理: `:MoneyManagementStatus`
- 多機関連携: `:CollaborationRecord`, `:SupportOrganization`

---

## 併用パターン

単一のケースで複数のスキルを使うことがある。

**例：障害福祉サービス利用者が生活保護も受給している場合**
1. 緊急手順 → emergency-protocol スキル
2. 障害福祉情報 → neo4j-support-db テンプレート2（プロフィール）
3. 経済リスク確認 → livelihood-support テンプレート2b（第7柱）
4. 事業所検索 → provider-search テンプレート1
5. エコマップ → ecomap-generator スキル
