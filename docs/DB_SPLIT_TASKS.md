# Mac の Claude Code への指示書：Neo4j を共有層と個人層に分ける

作成: 2026-10-31（クラウドのセッションから）。棚卸しの結果は `docs/DB_INVENTORY_TASKS.md` と
`~/Ai-Workspace/WAM-NET/wamnet_data/reports/inventory_*.md`。

## 目指す形

| 層 | DB | ポート | 中身 | 面倒を見るリポジトリ |
|---|---|---|---|---|
| 共有層 | support-db-neo4j | 7687 | ServiceProvider・ProviderFeedback（事業所・口コミ）。将来は行政組織・制度・法令 | neo4j-agno-agent |
| 個人層 | nest-support | **7688** | Client・家族・生育歴・禁忌・支援記録（ナラティブを Claude が構造化したもの） | nest-support |

2 つを**別のポートで同時に動かせる**ようにするのが肝心。

## 河原さんから聞いていること（2026-10-31）

- 3 つの DB に入っている利用者（Client）は、**1 件を除いてすべてダミー**。
- その 1 件は名前がイニシャルで、住所などは架空。**どの DB に入っているかは不明**。
- oya-inai-db は UI の試作で、nest-support に役目を譲った。
- Neo4j Desktop の 2 つ（disability-support・Senior-Support）は練習用で、削除してよい。

## 守ること

- nest-support には、作業 H で指示した変更（ポートと接続情報）以外は書き込まない。
- 消す前に必ず dry-run で件数を出し、河原さんの承認を得る。消す前にバックアップを取る。
- 名前・住所・記録の本文は読まない・出さない。イニシャルの 1 件を探すときも、件数だけ。
- 1 つの DB を扱い終えたら止めてから次へ。

---

## 作業 G：イニシャルの 1 件がどこにあるかを探す（読み取り専用）

3 つの DB それぞれで、名前がイニシャルの形（英字 2〜3 文字。間にピリオドや空白があってもよい）の Client を数える。

```cypher
MATCH (c:Client)
WHERE c.name =~ '(?i)^[A-Z]\\.?\\s?[A-Z]\\.?(\\s?[A-Z]\\.?)?$'
RETURN count(c) AS initials_like
```

1 つの DB だけで 1 件なら、そこにある。複数の DB で見つかったら、河原さんにイニシャルを聞き、
`MATCH (c:Client {name: $name}) RETURN count(c)` で確かめる（名前は画面に出さない）。
どの DB でも 0 件なら、形が違う可能性があるので、河原さんに聞く。

報告: DB ごとの件数と、どこにあると判断したか。

## 作業 H：nest-support を 7688 番に移し、共有層と同時に動かせるようにする

nest-support のフォルダ（コンテナを作ったほう。`~/Dev-Work` 側）で行う。

1. `docker-compose.yml` の ports を `7687:7687` → `7688:7687`、`7474:7474` → `7475:7474` に変える
   （コメントアウトされている 7688 の設定があればそれを生かす）。コンテナの中のポートは変えない。
2. 接続情報を層ごとに分ける。`~/.config/nest/neo4j.env` は共有層用のまま。個人層用に
   `~/.config/nest/neo4j-personal.env` を作り、`NEO4J_URI=bolt://localhost:7688` と nest-support の認証情報を入れる。
   nest-support 側のコードが `.env` や `~/.config/nest/neo4j.env` を読んでいるなら、`neo4j-personal.env` を読むように変える
   （どのファイルがどこを読んでいるか、`grep -rn "neo4j.env\|NEO4J_URI" --include=*.py --include=*.yml --include=*.sh --include=*.md` で確かめ、変えた箇所を報告）。
3. 両方を起動して、両方につながることを確かめる。
   ```bash
   (cd ~/Dev-Work/neo4j-agno-agent && docker compose up -d neo4j)
   (cd <nest-support> && docker compose up -d)
   docker ps --format '{{.Names}}\t{{.Ports}}'          # 7687 と 7688 が別のコンテナに付いていること
   set -a; source ~/.config/nest/neo4j.env; set +a
   uv run --with neo4j python ~/Dev-Work/neo4j-agno-agent/scripts/db_inventory.py --uri bolt://localhost:7687 --name shared | head -8
   set -a; source ~/.config/nest/neo4j-personal.env; set +a
   uv run --with neo4j python ~/Dev-Work/neo4j-agno-agent/scripts/db_inventory.py --uri bolt://localhost:7688 --name personal | head -8
   ```
   ServiceProvider 3032 が 7687 側に、Client 6 が 7688 側に出れば正しい。
4. nest-support の変更をコミットする（公開リポジトリなので、認証情報の値を含めないこと。`.env` 系のファイルが
   `.gitignore` に入っていることを `git check-ignore` で確かめる）。push は河原さんの承認を得てから。
5. `claude-skills/*/SKILL.md` と `CLAUDE.md`（neo4j-agno-agent）で「port 7688 = livelihood-support」と書いてある箇所は、
   後でクラウドのセッションが直す。ここでは触らない。

## 作業 I：support-db-neo4j を共有層にする（個人ノードを消す）

作業 G でイニシャルの 1 件が **support-db-neo4j にあった場合**は、消す前に nest-support へ移す。
移し方は、見つかった場所が分かってからクラウドのセッションが用意する（APOC の export/import を使う予定）。
nest-support か oya-inai-db にあった場合は、この作業にそのまま進む。

1. support-db-neo4j だけを起動し、バックアップを取る。取れたら `keep_` に改名する。
   ```bash
   cd ~/Dev-Work/neo4j-agno-agent
   ./scripts/backup.sh
   ```
2. dry-run。残すのは ServiceProvider と ProviderFeedback だけで、それ以外のラベルのノードは全部消す。
   ```bash
   set -a; source ~/.config/nest/neo4j.env; set +a
   uv run --with neo4j python scripts/purge_personal_nodes.py --dry-run \
     --output ~/Ai-Workspace/WAM-NET/wamnet_data/reports/purge_dryrun_$(date +%Y%m%d).md
   ```
   報告: 残すラベルと件数、消すラベルと件数、消す合計（約 166 件のはず）、口コミの作成者リンクの本数。
   「残すラベルと消すラベルを同時に持つノード」が出たら止めて報告する。
3. 河原さんの承認を得たら実行。
   ```bash
   uv run --with neo4j python scripts/purge_personal_nodes.py --execute --yes \
     --output ~/Ai-Workspace/WAM-NET/wamnet_data/reports/purge_exec_$(date +%Y%m%d).md
   ```
4. 確かめる: `db_inventory.py` を流し、個人情報を持つラベルが 0、ServiceProvider 3032 が残っていること。
   旧名のリレーション（PREFERS・PROHIBITED）も消えていること。
5. 止める。

## 作業 J：使わない Neo4j を閉じる

河原さんの承認を得てから、1 つずつ。

| 対象 | やること |
|---|---|
| oya-inai-db-neo4j | `cd <oya-inai-db> && docker compose down -v`（ボリュームごと削除）。リポジトリの README 冒頭に「2026-10-31 nest-support に統合。Neo4j は閉じた」と 1 行足す（コミットは承認後） |
| neo4j-skillgraph | `docker rm` と、使っていたボリュームの削除 |
| neo4j-support-db（エコマップ） | 同上 |
| law-graph-db | **消さない。** `db_inventory.py` で中身を数えて報告（法令なら共有層の候補） |
| Neo4j Desktop の 2 つ | 河原さんが Neo4j Desktop から削除する（Claude Code からは操作しない） |

削除の前に `docker volume ls` で、消すボリュームの名前を確かめ、報告してから消す。

## 報告してほしいこと

- 作業 G: 3 つの DB の件数と、イニシャルの 1 件の場所
- 作業 H: 変えたファイルと行、同時起動の結果（7687 に ServiceProvider、7688 に Client）
- 作業 I: dry-run の表、実行後の残りの件数
- 作業 J: 消したコンテナとボリューム、law-graph-db の棚卸し

作業 G が終わった時点で一度報告し、場所が support-db-neo4j だった場合はそこで止まる（移し方を用意するため）。
