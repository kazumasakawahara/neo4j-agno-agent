---
name: ecomap-generator
description: 支援ネットワークをエコマップ（支援関係図）として可視化するスキル。Mermaid形式・SVG形式での出力に対応し、4種類のテンプレート（全体像、支援会議用、緊急時、引き継ぎ用）を提供。
---

# エコマップ生成スキル (ecomap-generator)

知的障害・精神障害のある方の支援ネットワークを**エコマップ（支援関係図）**として可視化するスキルです。

## 使用条件

- **neo4j-support-db**スキルが有効であること
- Neo4jデータベースにクライアント情報が登録済みであること

## 使用トリガー

ユーザーが以下のように依頼した場合にこのスキルを使用：

- 「〇〇さんのエコマップを作って」
- 「支援会議用にエコマップを表示して」
- 「緊急連絡体制を図にして」
- 「引き継ぎ用のエコマップが欲しい」

## エコマップの種類

| テンプレート | 用途 | 含まれる情報 |
|-------------|------|-------------|
| `full_view` | 全体像把握 | 全ての関係者・機関 |
| `support_meeting` | ケース会議 | 推奨ケア、キーパーソン、最近の支援記録 |
| `emergency` | 緊急時対応 | 禁忌事項（最優先）、キーパーソン、医療機関 |
| `handover` | 担当者引き継ぎ | 全情報＋支援記録履歴 |

## 実行方法

### 方法1: Mermaid形式（チャット内表示）

```bash
cd ~/AI-Workspace/claude-skills/ecomap-generator/scripts
uv run python generate_mermaid.py "クライアント名" -t テンプレート名
```

**例：**
```bash
uv run python generate_mermaid.py "山田健太" -t emergency
```

### 方法2: SVG形式（印刷用ファイル）

```bash
cd ~/AI-Workspace/claude-skills/ecomap-generator/scripts
uv run python generate_svg.py "クライアント名" -t テンプレート名
```

**例：**
```bash
uv run python generate_svg.py "山田健太" -t support_meeting
```

出力先: `~/AI-Workspace/claude-skills/ecomap-generator/outputs/`

### 方法3: Neo4jブラウザで表示

以下のCypherクエリをNeo4jブラウザ（http://localhost:7474）で実行：

**全体像:**
```cypher
MATCH path = (c:Client {name: 'クライアント名'})-[*1..2]-()
RETURN path LIMIT 100
```

**緊急時体制:**
```cypher
MATCH (c:Client {name: 'クライアント名'})
OPTIONAL MATCH (c)-[:PROHIBITED|MUST_AVOID]->(ng:NgAction)
OPTIONAL MATCH (c)-[:PREFERS|REQUIRES]->(cp:CarePreference)
WHERE cp.priority = 'High'
OPTIONAL MATCH (c)-[kp_rel:EMERGENCY_CONTACT|HAS_KEY_PERSON]->(kp:KeyPerson)
OPTIONAL MATCH (c)-[:HAS_GUARDIAN|HAS_LEGAL_REP]->(g:Guardian)
OPTIONAL MATCH (c)-[:TREATED_AT]->(h:Hospital)
RETURN c, ng, cp, kp, kp_rel, g, h
```

## neo4j-support-dbとの連携

エコマップ生成前に、以下のツールでデータを確認：

| ツール | 用途 |
|--------|------|
| `list_clients` | クライアント一覧 |
| `get_client_profile` | クライアント全体像 |
| `search_emergency_info` | 緊急時情報 |

## データモデル

### ノード

- `Client` - 本人
- `NgAction` - 禁忌事項（赤）
- `CarePreference` - 推奨ケア（緑）
- `KeyPerson` - キーパーソン（オレンジ）
- `Guardian` - 後見人（紫）
- `Hospital` - 医療機関（青）
- `Certificate` - 手帳（グレー）
- `Condition` - 特性（黄）

### リレーション

- `PROHIBITED`, `MUST_AVOID` → 禁忌事項
- `PREFERS`, `REQUIRES` → 推奨ケア
- `HAS_KEY_PERSON`, `EMERGENCY_CONTACT` → キーパーソン
- `HAS_GUARDIAN`, `HAS_LEGAL_REP` → 後見人
- `TREATED_AT` → 医療機関
- `HAS_CERTIFICATE` → 手帳
- `HAS_CONDITION` → 特性

## ファイル構成

```
~/AI-Workspace/claude-skills/ecomap-generator/
├── SKILL.md              ← このファイル
├── scripts/
│   ├── generate_mermaid.py  ← Mermaid形式出力
│   ├── generate_svg.py      ← SVG形式出力
│   └── cypher_templates.py  ← クエリテンプレート
├── templates/            ← Cypherテンプレート
└── outputs/              ← 生成ファイル
```

## バージョン

- v1.0.0 (2025-12-26) - 初版リリース
