# neo4j-agno-agent — 福祉の共有層（事業所・行政・制度）の Neo4j

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

北九州市近郊の障害福祉サービス事業所（WAM NET のオープンデータ）を Neo4j に取り込み、
支援の現場と個人層（[nest-support](https://github.com/kazumasakawahara/nest-support)）から参照できるようにするリポジトリです。

> **2026-10-31 に役割を変えました。** それまでここにあった利用者・家族のアプリ（FastAPI・Next.js・SOS・mobile・個人層のスキル）は
> nest-support に一本化し、`archive/personal-layer-2026-10/` に退避しました。元の README は同フォルダの `README.personal-layer.md` です。

## 2 層の構成

| 層 | DB | ポート | 中身 | リポジトリ |
|---|---|---|---|---|
| **共有層（ここ）** | support-db-neo4j | 7687 | ServiceProvider（事業所）・ProviderFeedback（口コミ） | neo4j-agno-agent |
| 個人層 | nest-support-neo4j | 7688 | 利用者・家族・支援記録 | nest-support |

台帳: [`docs/DB_REGISTRY.md`](docs/DB_REGISTRY.md)

## できること

- **WAM NET の取得**（`WAM-NET/wamnet_downloader.py`）: 3 月末・9 月末に公開されるデータの最新を自動で探し、
  北九州市・行橋市・中間市・遠賀郡 4 町・京都郡 2 町の事業所を所在地で絞り込む。`--check` で新しい公開があるかだけを確かめる
- **Neo4j への取り込み**（`claude-skills/wamnet-provider-sync/scripts/sync_providers.py`）: 既存ノードと事業所番号＋サービス種類で照合し、
  新規・更新・廃止・近郊外を分けて書き込む。dry-run で件数を出してから実行する
- **重複のまとめ**（`merge_duplicate_providers.py`）: 同じ事業所のノードを 1 つに寄せる
- **事業所検索・口コミ**（`claude-skills/provider-search/`）: Claude Desktop / Claude Code から MCP `neo4j-shared` で引く Cypher テンプレート
- **棚卸し・バックアップ**（`scripts/`）: 件数だけの棚卸し、`neo4j_backup/` への保存と戻し

## 使い方

```bash
set -a; source ~/.config/nest/neo4j.env; set +a     # 接続情報（リポジトリには置かない）
docker compose up -d neo4j                           # 共有層を起動（7687）
uv run --with pytest --with pandas --with requests pytest WAM-NET/test_area_codes.py
```

半年ごとの更新と取り込みの手順は [`WAM-NET/MAC_TASKS.md`](WAM-NET/MAC_TASKS.md)。
Claude Code 向けの決まりは [`CLAUDE.md`](CLAUDE.md)。

## ライセンス

MIT
