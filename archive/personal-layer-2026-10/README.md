# 退避した個人層のコード（2026-10-31）

ここにあるのは、neo4j-agno-agent が「親亡き後支援データベース」のアプリ全体を持っていたときのコード。
2026-10-31 に Mac の Neo4j を共有層（このリポジトリ、7687）と個人層（nest-support、7688）に分け、
利用者・家族のアプリとスキルは **nest-support に一本化**した。ここのコードは動かさない。

| フォルダ・ファイル | 何だったか | 今の居場所 |
|---|---|---|
| api/・frontend/ | FastAPI（8001）＋ Next.js（3001）の業務 UI | nest-support の field-ui/ が後継 |
| lib/ | Neo4j 操作・Gemini 抽出・embedding | nest-support の lib/ |
| sos/・mobile/ | SOS 通知・モバイル入力 | nest-support の sos/ |
| skills/・tools/・agents/ | Agno エージェント、マニフェスト、プロトコル | nest-support の manifesto/ |
| claude-skills/ | neo4j-support-db・narrative-intake・ecomap-generator・emergency-protocol・html-to-pdf・inheritance-calculator・livelihood-support（断念） | nest-support の claude-skills/ |
| scripts/ | embedding のバックフィル、マイグレーション、デモデータ投入 | nest-support の scripts/ |
| CLAUDE.personal-layer.md・README.personal-layer.md | 当時の CLAUDE.md と README | — |

残したもの（リポジトリ直下）: WAM-NET/、claude-skills/{provider-search, wamnet-provider-sync}、scripts/{backup.sh, restore.sh, db_inventory.py, purge_personal_nodes.py}、docker-compose.yml、docs/。
