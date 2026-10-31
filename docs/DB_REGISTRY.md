# Neo4j の台帳：どの DB に何があり、どこで動き、誰が面倒を見るか

最終更新: 2026-10-31。変えたら、この日付と下の表を直す。
この台帳は neo4j-agno-agent と nest-support の両方から参照する。**新しい Neo4j を作る前に、ここに行を足す。**

## 2 層の構成

```
共有層（事業所・行政・制度）                 個人層（利用者・家族・ナラティブ）
support-db-neo4j  bolt://localhost:7687      nest-support-neo4j  bolt://localhost:7688
  ServiceProvider（WAM NET の事業所）           Client・KeyPerson・Guardian・Supporter
  ProviderFeedback（口コミ）                    LifeHistory・Wish・Condition・Certificate
  （将来）行政組織・制度・法令                  NgAction・CarePreference・SupportLog・MeetingRecord
        ↑                                           ↑ USES_SERVICE は wamnetId で共有層の事業所を指す
  wamnet_downloader.py が半年ごとに更新       Claude がナラティブを構造化して書き込む
```

- 共有層には **個人に結びつくノードを置かない**。2026-10-31 に個人ラベルのノード 166 件を消し、ServiceProvider だけにした。
- 個人層には **ServiceProvider を置かない**。事業所は `wamnetId`（WAM NET の事業所番号）で共有層を参照する。
  Neo4j Community は DB をまたぐ参照ができないので、事業所名を出すときはアプリや Claude が共有層にもう一度問い合わせる。
- 2 つは**別のポートで同時に動く**。どちらか一方だけ動いている状態で作業しない（取り違えのもと）。

## 台帳

| 呼び名 | 層 | 動かし方 | Bolt / HTTP | 接続情報 | 面倒を見るリポジトリ | 中身（2026-10-31） |
|---|---|---|---|---|---|---|
| support-db-neo4j | 共有 | Docker（neo4j-agno-agent の docker-compose） | 7687 / 7474 | `~/.config/nest/neo4j.env` | kazumasakawahara/neo4j-agno-agent | ServiceProvider 3032（Closed 126・outOfArea 601）。ほかのラベルは 0 |
| nest-support-neo4j | 個人 | Docker（nest-support の docker-compose） | 7688 / 7475 | `~/.config/nest/neo4j-personal.env` | kazumasakawahara/nest-support | Client 6（イニシャルの 1 件以外はダミー）ほか 137 ノード |
| law-graph-db | **独立した実験**（共有層には取り込まない。2026-10-31 決定） | Docker（~/Projects/legal-db） | 7692 | `~/Projects/legal-db/.env` | legal-db（ローカル、git 管理外） | 民法（明治 29 年法律第 89 号、ラベル `Statute`）総則の条文構造 282 ノード（条 98・項 62 ほか）と要件事実の関係（法概念 65・法理 13）。個人情報なし。弁護士としての研究課題で、福祉の共有層とは別に置く |

パスワードは 2026-10-31 に層ごとに別の値へ変えた。リポジトリに書かない（`.mcp.json`・`configs/*.json` は env ファイルを読む形）。

## MCP（Claude Desktop・Claude Code）

| MCP 名 | 接続先 | 使うスキル |
|---|---|---|
| `neo4j` | 個人層 7688（neo4j-personal.env） | neo4j-support-db、narrative-intake、ecomap-generator、emergency-protocol |
| `neo4j-shared` | 共有層 7687（neo4j.env） | provider-search、wamnet-provider-sync |

Claude Desktop の設定と nest-support の `.mcp.json` に両方を登録済み（2026-10-31）。

## 閉じたもの（2026-10-31）

| 名前 | 何だったか | 扱い |
|---|---|---|
| oya-inai-db-neo4j | UI の試作。nest-support に役目を譲った | コンテナ・フォルダごと削除。文書 6 つは nest-support の `docs/archive/oya-inai-db/` に写した |
| livelihood-support（7688） | 生活保護ケースワーカー向け。断念 | 7688 番を nest-support に譲った。スキルのフォルダは残っているが使わない |
| neo4j-skillgraph | 旧試作 | コンテナ・ボリューム削除 |
| neo4j-support-db（エコマップ） | 旧試作 | コンテナ・ボリューム削除 |
| Neo4j Desktop の disability-support・Senior-Support | 練習用 | 河原さんが Desktop から削除 |

## バックアップ（`neo4j_backup/`。`keep_` で始まるものは `backup.sh` の自動削除の対象外）

| ファイル | 時点 | 何の直前か |
|---|---|---|
| keep_backup_20261030_201112 | 10/30 20:11 | ServiceProvider の取り込み直し（4213 件の状態） |
| keep_backup_20261031_075158 | 10/31 07:51 | 重複ノードのまとめ（4728 件の状態） |
| keep_backup_20261031_081317 | 10/31 08:13 | まとめ後の取り込み（3020 件の状態） |
| keep_backup_20261031_114019 | 10/31 11:40 | 個人ノードの削除（3198 件。Client 12 を含む最後の状態）。2026-10-31 に keep_ に改名（`docs/BACKUP_KEEP_TASK.md`） |

半年後の更新が無事に終わったら、古いものは消してよい。

## 半年ごとの更新（WAM NET は 3 月末・9 月末のデータを公開）

`WAM-NET/MAC_TASKS.md` の作業 C。`wamnet_downloader.py --check` で新しい公開があるかを確かめ、
取り直し → `sync_providers.py --dry-run` → 承認 → 書き込み。保留の「サービス種類が不一致」23 行の扱いもそのとき決める。

## 法令を共有層に入れる方針（2026-10-31 決定）

- 共有層に要るのは**条文の層**（条・項・号・ただし書・準用・改正）だけ。要件事実の関係は入れない（人手で年単位の作業になるため）。
- 対象は支援の現場で参照する法令: 障害者総合支援法・児童福祉法・成年後見（民法第 7 条以下）・高齢者虐待防止法・個人情報保護法 など。
- 元データは e-Gov 法令 API。tsunagu-net の `docs/laws/`（高齢者虐待防止法・個人情報保護法を e-Gov API v2 から照合済み）の仕組みを使い、
  law-graph-db のデータは移さず新しく入れる。
- 時期と設計は未定。着手するときは、ラベル・リレーション名を `docs/NEO4J_SCHEMA_CONVENTION.md` に足してから取り込む。

## 個人層のコードの一本化（2026-10-31 決定・実施）

- 利用者・家族のアプリとスキルは **nest-support に一本化**。neo4j-agno-agent にあった api/・frontend/・lib/・sos/・mobile/・skills/・agents/・
  個人層のスキル（neo4j-support-db・narrative-intake・ecomap-generator ほか）は `archive/personal-layer-2026-10/` に退避した。
- Mac の `~/.claude/skills/` は narrative-intake 以外すべて nest-support を向いていた。narrative-intake のリンクは外し、
  nest-support の narrative-extractor に一本化する（`docs/CONSOLIDATION_TASKS.md` 作業 M）。
- legal-db にあった WAM NET の旧い月次書き込み処理（`com.kawahara.wamnet-supplement.plist`）は 2026-10-31 に `launchctl unload` で止めた。
  plist は残してある。共有層への書き込みは `WAM-NET/MAC_TASKS.md` の手順だけ。

## 決まっていないこと

- legal-db の README に law-graph-db のパスワードが平文で書かれている（git 管理外）。次に law-graph-db を触るときに変える。
