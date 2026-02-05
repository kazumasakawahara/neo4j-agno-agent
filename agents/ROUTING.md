# MCPサーバー ルーティングガイド

**目的:** 3つのMCPサーバーの使い分けを明確にし、どの状況でどのツールを呼び出すかを定義する。

---

## サーバー一覧

### 1. support-db（計画相談支援専用）

**対象業務:** 障害福祉サービスの利用調整、計画相談支援

**トリガーワード:**
- クライアント名（山田健太、佐々木真理 等）
- パニック、緊急、禁忌、支援記録
- キーパーソン、手帳、更新期限、後見人
- 配慮事項、ケアパターン、生育歴
- 事業所、空き状況、口コミ

**利用可能ツール:**

| ツール | 用途 | 優先度 |
|--------|------|--------|
| `search_emergency_info` | 緊急時情報（Safety First） | 最高 |
| `get_client_profile` | クライアント全体像 | 高 |
| `check_renewal_dates` | 更新期限チェック | 高 |
| `list_clients` | クライアント一覧 | 通常 |
| `get_database_stats` | 統計情報 | 通常 |
| `add_support_log` | 支援記録の追加 | 高 |
| `get_support_logs` | 支援記録の取得 | 高 |
| `discover_care_patterns` | ケアパターン発見 | 通常 |
| `get_audit_logs` | 監査ログ | 通常 |
| `get_client_change_history` | 変更履歴 | 通常 |
| `search_service_providers` | 事業所検索 | 高 |
| `link_client_to_provider` | クライアント-事業所紐付け | 通常 |
| `get_client_providers` | 利用事業所一覧 | 通常 |
| `find_alternative_providers` | 代替事業所検索 | 高 |
| `add_provider_feedback` | 事業所口コミ登録 | 通常 |
| `get_provider_feedbacks` | 口コミ取得 | 通常 |
| `search_providers_by_feedback` | 口コミ検索 | 通常 |
| `update_provider_availability` | 空き状況更新 | 通常 |
| `generate_report_file` | PDF/Excelレポート出力 | 通常 |
| `run_cypher_query` | カスタムCypherクエリ | 低（他で対応不可の時のみ） |

---

### 2. livelihood-support-db（生活困窮者自立支援専用）

**対象業務:** 生活保護受給者の自立支援、経済的搾取防止、金銭管理支援

**トリガーワード:**
- 受給者名
- 経済的リスク、搾取、金銭管理、お金がない
- 訪問前、ブリーフィング、引き継ぎ
- NG、避けるべき、効果的
- 多機関連携、ケース会議
- 類似ケース

**利用可能ツール:**

| ツール | 用途 | 優先度 |
|--------|------|--------|
| `search_emergency_info` | 緊急時情報 | 最高 |
| `get_visit_briefing_tool` | 訪問前ブリーフィング | 最高 |
| `detect_critical_guidance` | 指導的表現の検出 | 高 |
| `get_handover_summary_tool` | 引き継ぎサマリー | 高 |
| `get_client_profile` | クライアント全体像（7本柱） | 高 |
| `register_ng_approach_tool` | 避けるべき関わり方の登録 | 高 |
| `register_economic_risk_tool` | 経済的リスクの登録 | 高 |
| `register_money_management_tool` | 金銭管理状況の登録 | 高 |
| `register_effective_approach_tool` | 効果的な関わり方の登録 | 高 |
| `register_support_org_tool` | 連携支援機関の登録 | 通常 |
| `add_support_log` | 支援記録の追加（経済リスク自動検出付き） | 高 |
| `get_support_logs` | 支援記録の取得 | 高 |
| `discover_care_patterns` | ケアパターン発見 | 通常 |
| `find_similar_cases` | 類似ケース検索 | 通常 |
| `get_collaboration_history_tool` | 多機関連携履歴 | 通常 |
| `check_renewal_dates` | 更新期限チェック | 高 |
| `list_clients` | クライアント一覧 | 通常 |
| `get_audit_logs` | 監査ログ | 通常 |
| `get_client_change_history` | 変更履歴 | 通常 |
| `get_database_stats` | 統計情報 | 通常 |
| `run_cypher_query` | カスタムCypherクエリ（読み取り専用） | 低 |

---

### 3. neo4j（汎用Neo4jアクセス）

**対象業務:** 上記2つでカバーしきれない操作、別プロジェクトのデータベース

**利用可能ツール:**

| ツール | 用途 |
|--------|------|
| `get_neo4j_schema` | スキーマ取得 |
| `read_neo4j_cypher` | 読み取りクエリ |
| `write_neo4j_cypher` | 書き込みクエリ |

---

## ルーティング判断フロー

```
ユーザー入力
│
├─ 緊急ワード検出？（パニック、SOS、倒れた、救急）
│  ├─ YES → 対象がどちらのDBか判断
│  │       ├─ 障害福祉クライアント → support-db:search_emergency_info
│  │       └─ 生活保護受給者 → livelihood-support-db:search_emergency_info
│  └─ NO → 続行
│
├─ クライアント名が含まれる？
│  ├─ YES → どちらのDBに登録されているか確認
│  │       ├─ support-db → support-db のツールを使用
│  │       ├─ livelihood-support-db → livelihood-support-db のツールを使用
│  │       └─ 不明 → 両方の list_clients で確認
│  └─ NO → 続行
│
├─ 経済リスク・金銭管理・搾取に関する話題？
│  └─ YES → livelihood-support-db
│
├─ 事業所検索・口コミに関する話題？
│  └─ YES → support-db
│
├─ 訪問前ブリーフィング・引き継ぎ？
│  └─ YES → livelihood-support-db（専用ツールあり）
│
├─ 一般的なNeo4j操作？（スキーマ確認、別プロジェクト）
│  └─ YES → neo4j
│
└─ 判断不能
   └─ ユーザーに確認する
```

---

## 同名ツールの使い分け

両方のMCPサーバーに同名のツールが存在する場合がある。違いに注意すること。

### search_emergency_info
- **support-db版:** NgAction → CarePreference → KeyPerson → Hospital → Guardian の順
- **livelihood-support-db版:** NgApproach → EconomicRisk → EffectiveApproach → MentalHealthStatus → KeyPerson → Hospital の順（経済リスクを含む）

### get_client_profile
- **support-db版:** 4本柱（本人性、ケア、法的基盤、安全ネット）
- **livelihood-support-db版:** 7本柱（上記4本 + ケース記録 + 金銭的安全 + 多機関連携）

### add_support_log
- **support-db版:** 基本的な支援記録の抽出・登録
- **livelihood-support-db版:** 経済的リスクのサインも自動検出する拡張版

---

## 併用パターン

単一のケースで両方のMCPサーバーを使うことがある。

**例：障害福祉サービス利用者が生活保護も受給している場合**
1. 緊急時情報 → `livelihood-support-db:search_emergency_info`（経済リスクも含むため）
2. 事業所検索 → `support-db:search_service_providers`（こちらにしかない機能）
3. 引き継ぎ → `livelihood-support-db:get_handover_summary_tool`（専用ツール）
4. エコマップ → ecomap-generator スキル + support-db のデータ
