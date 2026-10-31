# Mac の Claude Code への指示書：Neo4j の棚卸し（件数だけ）

作成: 2026-10-31（クラウドのセッションから）

## 目的

Mac にある Neo4j を「共有層（事業所・行政・制度）」と「個人層（利用者・家族・ナラティブ）」の 2 層に整理する前に、
**今どこに何件入っているか**を数える。設計の判断材料にするのが目的で、ここでは何も変えない。

対象は Docker の 3 つ。どれも 7687 番を使うので、**1 つずつ起動して数え、止めてから次へ進む**。

| 呼び名 | リポジトリ（Mac のフォルダ） | 役割の見込み |
|---|---|---|
| support-db-neo4j | ~/Dev-Work/neo4j-agno-agent | 共有層にする予定。ServiceProvider は 2026-10-31 に整え済み |
| nest-support の Neo4j | nest-support のフォルダ（場所は `find ~ -maxdepth 3 -name nest-support -type d` で探す） | 個人層の本番。**今回も書き込まない** |
| oya-inai-db-neo4j | oya-inai-db のフォルダ | nest-support に役目を譲った試作。空なら閉じる候補 |

## 守ること

- **読み取り専用。** 数えるスクリプトは READ_ACCESS で接続し、プロパティの値（氏名・住所・記録の本文）は読まない・出さない。
- nest-support には、数える以外のことをしない。接続情報も表示しない。
- 1 つの DB を数え終えたら `docker compose stop` してから次を起動する。2 つ同時に 7687 番を使わない。
- 出力はデスクトップではなく `~/Ai-Workspace/WAM-NET/wamnet_data/reports/` に置く（git の対象外）。

## 手順

### 0. 準備

```bash
cd ~/Dev-Work/neo4j-agno-agent
git pull
docker ps --format '{{.Names}}\t{{.Ports}}'   # 何も動いていないことを確かめる
```

接続情報は DB ごとに違う可能性がある。各リポジトリの `docker-compose.yml` の `NEO4J_AUTH` が何を読んでいるかを見て、
それに合わせて `NEO4J_USERNAME` / `NEO4J_PASSWORD` を環境変数に入れる（値は画面に出さない）。
neo4j-agno-agent は `~/.config/nest/neo4j.env`。

### 1. support-db-neo4j

```bash
cd ~/Dev-Work/neo4j-agno-agent
docker compose up -d neo4j && sleep 20
set -a; source "${XDG_CONFIG_HOME:-$HOME/.config}/nest/neo4j.env"; set +a
uv run --with neo4j python scripts/db_inventory.py --uri bolt://localhost:7687 --name support-db-neo4j \
  --output ~/Ai-Workspace/WAM-NET/wamnet_data/reports/inventory_support-db-neo4j.md
docker compose stop
```

### 2. nest-support

```bash
cd <nest-support のフォルダ>
grep -n "container_name\|NEO4J_AUTH\|7687\|7688" docker-compose.yml     # コンテナ名・ポート・接続情報の読み先を確かめる
docker compose up -d && sleep 20
# NEO4J_USERNAME / NEO4J_PASSWORD を、上で確かめた読み先に合わせて環境変数に入れる
uv run --with neo4j python ~/Dev-Work/neo4j-agno-agent/scripts/db_inventory.py --uri bolt://localhost:<ポート> --name nest-support \
  --output ~/Ai-Workspace/WAM-NET/wamnet_data/reports/inventory_nest-support.md
docker compose stop
```

あわせて、リポジトリにデータが入っていないかを見る（公開リポジトリのため）。出すのはファイル名だけ。

```bash
git -C <nest-support のフォルダ> ls-files | grep -iE 'neo4j_data|neo4j_backup|\.dump$|\.csv$|\.tar\.gz$' || echo "データファイルは追跡されていない"
git -C <nest-support のフォルダ> remote -v | head -1
```

### 3. oya-inai-db-neo4j

```bash
cd <oya-inai-db のフォルダ>
docker compose up -d neo4j && sleep 20
# 接続情報を docker-compose.yml の読み先に合わせる
uv run --with neo4j python ~/Dev-Work/neo4j-agno-agent/scripts/db_inventory.py --uri bolt://localhost:7687 --name oya-inai-db-neo4j \
  --output ~/Ai-Workspace/WAM-NET/wamnet_data/reports/inventory_oya-inai-db-neo4j.md
docker compose stop
```

### 4. Neo4j Desktop の 2 つ（disability-support・Senior-Support）

練習用で実データは無い前提。削除の前に、念のため中身が空に近いことだけ確かめる。
Neo4j Desktop でインスタンスを起動し、Neo4j Browser で次を流す（件数だけ）。終わったら止める。

```cypher
MATCH (n) RETURN count(n) AS nodes
```

削除はこの指示書の範囲外（河原さんが Neo4j Desktop から行う）。

### 5. そのほかの Neo4j が無いか

```bash
docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Ports}}' | grep -i neo4j
ls ~/Library/Application\ Support/neo4j-desktop/Application/Data/dbmss/ 2>/dev/null
```

## 報告してほしいこと

3 つのレポートの内容を、次の形にまとめる。値は件数だけ。

| | support-db-neo4j | nest-support | oya-inai-db-neo4j |
|---|---|---|---|
| ノード総数 | | | |
| リレーション総数 | | | |
| ServiceProvider | | | |
| Client | | | |
| SupportLog / NgAction / CarePreference | | | |
| そのほか目立つラベル（上位 3 つと件数） | | | |
| 制約・インデックスの数 | | | |

加えて:
- nest-support のポート番号と、リポジトリにデータファイルが追跡されていないか
- Neo4j Desktop の 2 つのノード数
- 5 で見つかった、上の 3 つ以外の Neo4j コンテナ・インスタンス

## 読み方（判断の目安）

- **support-db-neo4j に Client などの個人ラベルが 0 件** → そのまま共有層にできる。
  1 件以上 → 試作データか本物かを河原さんに確かめ、消すか nest-support に移すかを決める。
- **oya-inai-db-neo4j がほぼ空** → 閉じる。ServiceProvider が入っていれば、support-db-neo4j のものと重なるので、こちらは捨ててよい。
  Client などが入っていれば、nest-support にあるものと同じか、河原さんに確かめる。
- **nest-support に ServiceProvider が入っている** → 共有層と二重になる。件数と形（新しい ID かどうか）を見て、どちらを正とするか決める。
