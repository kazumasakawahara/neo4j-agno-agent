# Mac の Claude Code への指示書：2 層化の仕上げに向けた調査（作業 K・L）

作成: 2026-10-31（クラウドのセッションから）。2 層化の結果は `docs/DB_REGISTRY.md`。

ここでやるのは**調べて報告する**ことだけ。DB・ファイル・設定を変えない。
結果をもとに、クラウドのセッションが設計と整理（コードの退避・文書の書き換え）を行う。

## 守ること

- 読み取り専用。Neo4j は数えるときだけ起動し、終わったら止める。
- 個人層（nest-support、7688）には触れない。
- 出すのは件数・ラベル名・ファイル名・設定の内容。法令の名前は出してよい（個人情報ではない）。
- 出力は `~/Ai-Workspace/WAM-NET/wamnet_data/reports/` に置く。

---

## 作業 K：law-graph-db（法令の DB）を共有層に取り込めるか調べる

2026-10-31 の棚卸しで、law-graph-db（`~/Projects/legal-db`、port 7692）には 1 つの法令の条文構造（282 ノード、
条 98・項 62・ただし書 9・改正注記 12、法概念 65、法理 13）が入っていて、個人情報は無いと分かった。
共有層（事業所・行政・制度）に置く候補になる。取り込むかどうか、取り込むならどう置くかを決めるための材料を集める。

### K-1. どの法令か、どういう構造か

```bash
cd ~/Projects/legal-db
docker compose up -d && sleep 20
set -a; . ./.env; set +a
```

Neo4j Browser（http://localhost:<HTTP ポート>）か `cypher-shell` で、次を流して結果を報告する（値は法令名・ラベル名・件数だけ）。

```cypher
// 法令の名前と、持っているプロパティの名前
MATCH (l:Law) RETURN l.name AS name, keys(l) AS props LIMIT 5;
// ラベルごとのプロパティ名（値は見ない）
MATCH (n) WITH labels(n)[0] AS label, keys(n) AS ks UNWIND ks AS k
RETURN label, collect(DISTINCT k) AS props ORDER BY label;
// リレーションの種別と、両端のラベル
MATCH (a)-[r]->(b) RETURN labels(a)[0] AS from, type(r) AS rel, labels(b)[0] AS to, count(*) AS c ORDER BY c DESC;
// 制約とインデックス
SHOW CONSTRAINTS; SHOW INDEXES;
```

`:Law` というラベル名は推測。無ければ `CALL db.labels()` で確かめてから読み替える。

### K-2. どうやって作ったか

```bash
ls ~/Projects/legal-db
cat ~/Projects/legal-db/README.md 2>/dev/null | head -60
ls ~/Projects/legal-db/scripts ~/Projects/legal-db/src 2>/dev/null
grep -rln "e-Gov\|egov\|law_id\|LawId" ~/Projects/legal-db --include=*.py --include=*.md 2>/dev/null | head
```

報告するもの:
- 元データは何か（e-Gov 法令 API か、手で作ったか、別のリポジトリ tsunagu-net の `docs/laws/` と関係があるか）
- 取り込みスクリプトがあるか。あるなら、別の法令も同じ手順で入れられそうか
- 最後に更新したのはいつか（`git log -1` か、ファイルの日付）

### K-3. 共有層との関係

neo4j-agno-agent の共有層（7687）には今、ServiceProvider と ProviderFeedback しか無い。
法令を同じ DB に入れると、ラベル・リレーション名が衝突しないか、命名規則（`docs/NEO4J_SCHEMA_CONVENTION.md`：
ノード PascalCase・リレーション UPPER_SNAKE_CASE・プロパティ camelCase）に合っているかを、K-1 の結果から見て報告する。

```bash
cd ~/Projects/legal-db && docker compose stop
```

### 報告の形

| 項目 | 内容 |
|---|---|
| 法令名 | |
| ラベル一覧（件数つき） | |
| リレーション一覧（両端のラベルつき） | |
| プロパティ名の規則（camelCase か snake_case か） | |
| 元データと取り込みスクリプト | |
| 最終更新 | |
| 共有層の命名規則との衝突・ずれ | |

---

## 作業 L：neo4j-agno-agent に残る個人層のコードが、Mac で何かに使われているか調べる

neo4j-agno-agent には、利用者データを書くコード（`api/`・`frontend/`・`lib/`・`sos/`・`mobile/`・`claude-skills/neo4j-support-db` など）が
残っている。個人層は nest-support に一本化したので、これらは退避する候補。ただし、Mac で何かがまだ参照していると、退避で壊れる。
それを先に調べる。

### L-1. `~/.claude/skills/` のリンク先

```bash
ls -la ~/.claude/skills/ | awk '{print $9, $10, $11}'
```

報告: スキル名ごとに、リンク先が neo4j-agno-agent か nest-support か、それ以外か。特に次の 5 つ:
`neo4j-support-db`・`provider-search`・`wamnet-provider-sync`・`ecomap-generator`・`narrative-intake`（nest-support 側は `narrative-extractor`）。

### L-2. 自動起動・定期実行

```bash
ls ~/Library/LaunchAgents/ | grep -i "nest\|neo4j\|agno\|wamnet\|support"
grep -l "neo4j-agno-agent" ~/Library/LaunchAgents/*.plist 2>/dev/null
crontab -l 2>/dev/null | grep -i "neo4j-agno-agent\|nest-support"
```

報告: neo4j-agno-agent のパスを含む launchd / cron の項目があるか（`WAM-NET/MAC_TASKS.md` 作業 C の wamnet-check は共有層のもので、残してよい）。

### L-3. Claude Desktop・Claude Code の設定

```bash
grep -n "neo4j-agno-agent\|nest-support" ~/Library/Application\ Support/Claude/claude_desktop_config.json
grep -rn "neo4j-agno-agent" ~/.claude/settings.json ~/.claude/settings.local.json 2>/dev/null
grep -rln "neo4j-agno-agent" ~/.claude/projects 2>/dev/null | head -5
```

報告: 設定の中で neo4j-agno-agent のパスを参照している箇所（値は見せなくてよい。キー名と有無だけ）。

### L-4. neo4j-agno-agent のアプリを動かす予定があるか（河原さんに聞く）

`api/`（FastAPI 8001）・`frontend/`（Next.js 3001）・`sos/`・`mobile/` を今後も neo4j-agno-agent 側で動かす予定があるか、
それとも nest-support の `field-ui/`・`sos/` に一本化するかを、河原さんに確かめて報告に添える。

### 報告の形

| 項目 | 結果 |
|---|---|
| skills のリンク先（5 つ） | |
| launchd / cron で neo4j-agno-agent を参照するもの | |
| Claude の設定で neo4j-agno-agent を参照するもの | |
| アプリを neo4j-agno-agent 側で動かす予定 | あり / なし（河原さんの回答） |

---

## この後の流れ（クラウドのセッションが行う）

- K の結果 → 法令を共有層に置くときのラベル・リレーションの設計案と、取り込み手順を出す。取り込むかは河原さんが決める。
- L の結果 → 参照されていないコードを `archive/` に退避し、`CLAUDE.md`・`README.md` を「共有層のリポジトリ」として書き直す案をプルリクエストにする。
  skills のリンクが neo4j-agno-agent を向いていれば、nest-support 側へ張り替える手順も添える。
