# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## このリポジトリの役割（2026-10-31〜）

**福祉の共有層（事業所・行政・制度）の Neo4j を面倒見るリポジトリ。**

Mac の Neo4j は 2 層に分けた。台帳は `docs/DB_REGISTRY.md`。

| 層 | DB | ポート | 中身 | リポジトリ |
|---|---|---|---|---|
| **共有層（ここ）** | support-db-neo4j（Docker、`docker-compose.yml`） | 7687 / HTTP 7474 | ServiceProvider（WAM NET の事業所）・ProviderFeedback（口コミ）。将来は行政組織・制度・福祉関係の法令の条文 | kazumasakawahara/neo4j-agno-agent |
| 個人層 | nest-support-neo4j | 7688 / HTTP 7475 | 利用者・家族・生育歴・禁忌・支援記録 | kazumasakawahara/nest-support |

- 接続情報は `~/.config/nest/neo4j.env`（共有層）。個人層は `~/.config/nest/neo4j-personal.env`。リポジトリにパスワードを書かない。
- MCP は `neo4j-shared`（共有層 7687）と `neo4j`（個人層 7688）。
- **共有層に個人に結びつくノードを置かない。** 個人層に ServiceProvider を作らない。`USES_SERVICE` は `wamnetId` で共有層の事業所を指す。
- 利用者・家族のアプリ（FastAPI・Next.js・SOS・mobile・個人層のスキル）は **nest-support に一本化**した。
  ここにあったものは `archive/personal-layer-2026-10/` に退避してあり、動かさない（元の説明は同フォルダの `CLAUDE.personal-layer.md`）。

## 中身

```
neo4j-agno-agent/
├── docker-compose.yml          # 共有層 Neo4j（support-db-neo4j、7687）。NEO4J_AUTH は neo4j.env から
├── pyproject.toml / uv.lock    # neo4j・pandas・requests・python-dotenv だけ（dev: pytest・openpyxl）。パッケージは作らない
├── WAM-NET/                    # WAM NET 事業所データの取得（半年ごと）
│   ├── wamnet_downloader.py    #   公開済みの最新を自動で探し、北九州市近郊を所在地で絞り込む
│   ├── count_area_mismatch.py  #   近郊外の混入を件数だけ数える
│   ├── test_area_codes.py      #   市区町村コード表の照合・絞り込み・公開時点の試験
│   ├── soumu_area_codes_reference.json
│   └── MAC_TASKS.md            #   Mac で行う更新・取り込みの手順（作業 A〜F）
├── claude-skills/
│   ├── wamnet-provider-sync/   # CSV → ServiceProvider の取り込み（sync_providers.py）、重複まとめ（merge_duplicate_providers.py）
│   └── provider-search/        # 事業所検索・口コミの Cypher テンプレート（MCP neo4j-shared）
├── scripts/
│   ├── backup.sh / restore.sh  # neo4j_backup/ への保存と戻し。keep_ で始まるものは自動削除の対象外
│   ├── db_inventory.py         # 件数だけの棚卸し（読み取り専用）
│   └── purge_personal_nodes.py # 共有層から個人ノードを消す（2026-10-31 に実施済み）
├── docs/
│   ├── DB_REGISTRY.md          # どの DB に何があり、どこで動き、誰が面倒を見るかの台帳
│   ├── NEO4J_SCHEMA_CONVENTION.md
│   ├── DB_INVENTORY_TASKS.md / DB_SPLIT_TASKS.md / CONSOLIDATION_TASKS.md   # 2026-10-31 の整理の記録
│   └── …
├── configs/                    # Claude Desktop の MCP 設定のひな形
└── archive/personal-layer-2026-10/   # 退避した個人層のコード（api・frontend・lib・sos・mobile・skills・agents ほか）
```

## よくある作業

```bash
# 共有層の起動・停止（接続情報を先に読む）
set -a; source ~/.config/nest/neo4j.env; set +a
docker compose up -d neo4j
docker compose stop

# 棚卸し（件数だけ）
uv run --with neo4j python scripts/db_inventory.py --uri bolt://localhost:7687 --name support-db-neo4j

# WAM NET の更新（半年ごと。詳しくは WAM-NET/MAC_TASKS.md 作業 C）
cd ~/Ai-Workspace/WAM-NET
uv run --with pandas --with requests python ~/Dev-Work/neo4j-agno-agent/WAM-NET/wamnet_downloader.py --check
uv run --with pandas --with requests python ~/Dev-Work/neo4j-agno-agent/WAM-NET/wamnet_downloader.py
cd ~/Dev-Work/neo4j-agno-agent
uv run --with neo4j --with python-dotenv python claude-skills/wamnet-provider-sync/scripts/sync_providers.py \
  --mode diff --dry-run --csv-file ~/Ai-Workspace/WAM-NET/wamnet_data/kitakyushu_services_<YYYYMM>.csv

# 試験
uv run --with pytest --with pandas --with requests pytest WAM-NET/test_area_codes.py
(cd claude-skills/wamnet-provider-sync && uv run --with pytest --with neo4j --with python-dotenv pytest tests)
```

## 守ること

- DB に書く前に dry-run で件数を出し、承認を得て、バックアップを取る（`WAM-NET/MAC_TASKS.md` の手順どおり）。
- 出すのは件数。個人層のデータ（氏名・記録）は読まない・出さない。nest-support の DB にはこのリポジトリから書かない。
- ServiceProvider の一意キーは `providerId`（事業所番号_サービス種類コード）。`wamnetId`（事業所番号）で既存ノードと照合する。
- 命名規則: ノード PascalCase / リレーション UPPER_SNAKE_CASE / プロパティ camelCase（`docs/NEO4J_SCHEMA_CONVENTION.md`）。
  レガシー名（`office_name` など）は読むだけで、新しく書かない。
- 新しい Neo4j を作る前に `docs/DB_REGISTRY.md` に行を足す。

## 決まっていること・いないこと（2026-10-31）

- WAM NET の月次処理は、`wamnet-check`（毎月 1 日に新しい公開があるかを確かめて通知するだけ）に一本化。legal-db にあった旧い書き込み処理は止めた。
- law-graph-db（民法総則と要件事実の実験）は独立したまま。共有層には取り込まない。
- 共有層に福祉関係の法令の条文層を e-Gov から入れる設計は未着手。
- 保留の「サービス種類が不一致」23 行は、次の半年更新のときに扱いを決める。

## Development Context

This system was developed by a lawyer working with NPOs supporting families of children with intellectual disabilities.
共有層は、支援の現場が「どの事業所が、どこで、何のサービスを」を正確に引けるための土台で、個人層（nest-support）から `wamnetId` で参照される。
