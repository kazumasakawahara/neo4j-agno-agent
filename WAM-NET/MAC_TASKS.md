# Mac の Claude Code への指示書：WAM NET 事業所データの後始末と半年ごとの更新

作成: 2026-10-30（クラウドのセッションから）。対象ブランチ: `claude/tender-gauss-m4ky9k`

この指示書は、Mac の中にしか無いもの（Neo4j のコンテナ、`~/Ai-Workspace/WAM-NET`、定期実行）を扱う作業をまとめたもの。
クラウドのセッションからは届かないので、Mac の Claude Code で `~/Dev-Work/neo4j-agno-agent` を開いて進める。

## 0. これまでに分かっていること

- 旧版の `wamnet_downloader.py` は、先頭列「都道府県コード又は市区町村コード」で絞り込んでいた。
  この列は**事業所を指定した自治体**（北九州市 40100、久留米市 40203、福岡県 40000 など）のコードで、所在地ではない。
- そのため、旧版で作った CSV（`~/Ai-Workspace/WAM-NET/wamnet_data/` の 2026-10-30 より前のもの、2447 行）は
  - 久留米市 694 件・八女市 1 件（計 **695 件**）の近郊外の事業所が混ざり、
  - 行橋市・中間市・遠賀郡4町・京都郡2町と、小倉北区の4件（計 **414 件**）が抜けていた。
- 直した版は「事業所住所（市区町村）」で絞り込む。対象は北九州市（7区）、行橋市、中間市、遠賀郡4町（芦屋・水巻・岡垣・遠賀）、京都郡2町（苅田・みやこ）（2026-10-30 河原さん決定）。
- 直した版で 202509 を取り直した結果は **2166 件**（北九州市 1756、行橋 113、中間 66、遠賀郡 140、京都郡 91）。
  `~/Ai-Workspace/WAM-NET/wamnet_data/kitakyushu_services_202509.csv` は、この正しい版で上書き済み。

## 守ること

- **nest-support の本番 DB には接続しない・書き込まない。** Neo4j は読み取り専用で数えるだけ。
- 件数だけを扱う。事業所の行の中身や、利用者（Client など）の情報は読まない・出力しない。
- Neo4j の ServiceProvider の取り込み直し、`~/Ai-Workspace` のファイルの置き換え、定期実行の登録は、**河原さんの承認を得てから**行う。
- Docker が起動していなければ起動してよい。作業が終わったら、起動したコンテナは止める。

## 作業 A：Neo4j の ServiceProvider に近郊外が何件混ざっているか数える

1. 7687 番で動いているコンテナを確かめる。
   ```bash
   docker ps --format '{{.Names}}\t{{.Ports}}' | grep 7687
   ```
   - 名前に `nest-support` が入っていたら、**そこで止めて河原さんに知らせる。**
   - 何も動いていなければ、`~/Dev-Work/neo4j-agno-agent` で `docker compose up -d`。
2. 数える（読み取り専用。出力は市区町村ごとの件数だけ）。
   ```bash
   cd ~/Dev-Work/neo4j-agno-agent
   git pull
   set -a; source .env; set +a
   uv run --with neo4j python WAM-NET/count_area_mismatch.py neo4j --uri bolt://localhost:7687
   ```
3. 結果の読み方
   - 「新表に無い市区町村」に 久留米市・八女市 が出れば、旧版の CSV から取り込んでいる。
   - `city` が「（空）」の件数が多い場合は、取り込みに使ったスクリプトが市区町村の列を読めていない
     （`claude-skills/wamnet-provider-sync/scripts/sync_providers.py` は `市区町村`・`住所` という列名を読むが、
     WAM NET の CSV の列名は `事業所住所（市区町村）`・`事業所住所（番地以降）`）。この場合は直さずに河原さんに報告する。
4. 件数を河原さんに報告し、取り込み直すかどうかの判断を仰ぐ。取り込み直しはこの作業に含めない。
5. 1 でコンテナを起動した場合は `docker compose stop`。

## 作業 B：`~/Ai-Workspace/WAM-NET/wamnet_downloader.py` を直した版にそろえる

`~/Ai-Workspace/WAM-NET` は別の git リポジトリで、そこの `wamnet_downloader.py` は旧版のまま。
そこで `uv run python wamnet_downloader.py` を実行すると、また北九州市が指定した事業所しか拾わない。

1. 違いを確かめる。
   ```bash
   diff ~/Ai-Workspace/WAM-NET/wamnet_downloader.py ~/Dev-Work/neo4j-agno-agent/WAM-NET/wamnet_downloader.py | head -50
   ```
2. 河原さんに、次のどちらにするかを確かめる。
   - 置き換える：今のファイルを `wamnet_downloader.py.bak-20261030` として残し、直した版を写す。
     試験で使う `soumu_area_codes_reference.json` と `test_area_codes.py` も一緒に写す。
   - 使わない：Ai-Workspace 側のファイルを消すか、先頭に「旧版。Dev-Work 側を使うこと」と書く。
3. 置き換えた場合は、試験が通ることを確かめる。
   ```bash
   cd ~/Ai-Workspace/WAM-NET
   uv run --with pytest --with pandas --with requests pytest test_area_codes.py
   ```

## 作業 C：半年ごとの更新に備える

WAM NET は3月末・9月末時点のデータを半年ごとに公開する。直した版のダウンローダーは、既定で公開済みの最新を探して取る。

### 手で更新するとき

```bash
cd ~/Ai-Workspace/WAM-NET
uv run --with pandas --with requests python ~/Dev-Work/neo4j-agno-agent/WAM-NET/wamnet_downloader.py --check
# 終了コード 0 = 最新を取得済み / 10 = 新しい公開がある / 1 = WAM NET に接続できない
uv run --with pandas --with requests python ~/Dev-Work/neo4j-agno-agent/WAM-NET/wamnet_downloader.py
cd ~/Dev-Work/neo4j-agno-agent
uv run --with pandas python WAM-NET/count_area_mismatch.py csv ~/Ai-Workspace/WAM-NET/wamnet_data/kitakyushu_services_<新しい公開時点>.csv
```

取り直したら、次を確かめてから Neo4j への取り込みを河原さんに相談する。

- 事業所住所（市区町村）の値に、対象の15の値（北九州市の7区と、行橋市・中間市・遠賀郡4町・京都郡2町）だけが出ていること。
- 件数が前回（202509 は 2166 件）から大きく外れていないこと。外れていれば、WAM NET の列名や表記が変わった可能性がある。
- 総務省の市区町村コードが変わっていないか（合併など）。総務省の Excel を落として
  `SOUMU_XLSX=<Excel> uv run --with pytest --with pandas --with requests --with openpyxl pytest WAM-NET/test_area_codes.py`。

### 毎月1日に新しい公開を確かめて通知する（河原さんの承認を得てから登録）

`--check` を launchd で毎月1日 9:10 に流し、新しい公開があれば macOS の通知を出す。ダウンロードや取り込みは自動ではしない。

1. `uv` のフルパスを確かめる（`which uv`）。下の `/opt/homebrew/bin/uv` をその値に置き換える。
2. `~/Library/LaunchAgents/jp.lawnest.wamnet-check.plist` を作る。
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
     <key>Label</key><string>jp.lawnest.wamnet-check</string>
     <key>ProgramArguments</key>
     <array>
       <string>/bin/zsh</string><string>-c</string>
       <string>cd ~/Ai-Workspace/WAM-NET &amp;&amp; /opt/homebrew/bin/uv run --with pandas --with requests python ~/Dev-Work/neo4j-agno-agent/WAM-NET/wamnet_downloader.py --check &gt; /tmp/wamnet-check.log 2&gt;&amp;1; rc=$?; if [ $rc -eq 10 ]; then osascript -e 'display notification "新しい公開時点があります。/tmp/wamnet-check.log を確認" with title "WAM NET"'; elif [ $rc -ne 0 ]; then osascript -e 'display notification "確認に失敗しました。/tmp/wamnet-check.log を確認" with title "WAM NET"'; fi</string>
     </array>
     <key>StartCalendarInterval</key>
     <dict><key>Day</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>10</integer></dict>
   </dict>
   </plist>
   ```
3. 登録して、一度だけ手で動かして通知とログを確かめる。
   ```bash
   launchctl load ~/Library/LaunchAgents/jp.lawnest.wamnet-check.plist
   launchctl start jp.lawnest.wamnet-check
   cat /tmp/wamnet-check.log
   ```
   やめるときは `launchctl unload ~/Library/LaunchAgents/jp.lawnest.wamnet-check.plist`。

## 作業 E：ServiceProvider を 202609 で取り込み直す（2026-10-30 河原さん方針決定）

方針: 近郊外の事業所は**消さずに `outOfArea = true` を付けて残す**（利用者とのつながりを保つ）。
北九州市の二通りの書き方による重なりは、取り込み直した後に件数を見てから1つにまとめる。

`claude-skills/wamnet-provider-sync/scripts/sync_providers.py` は 2026-10-30 に直した。
WAM NET の列名（事業所の名称・事業所住所（市区町村）など）を読み、近郊外を廃止と分け、利用者は人数だけを出す。

1. 最新を取り込み、試験を通す。
   ```bash
   cd ~/Dev-Work/neo4j-agno-agent
   git pull
   (cd claude-skills/wamnet-provider-sync && uv run --with pytest --with neo4j --with python-dotenv pytest tests)
   ```
2. 作業 A の 1 と同じく、7687 番のコンテナが nest-support の本番でないことを確かめる。
3. 書き込む前にバックアップを取る（`scripts/backup.sh` など、このリポジトリの手順で）。
4. 書き込まずに試す（`--dry-run`）。`--prefecture` は付けない（既存ノードの prefecture が空のものを取りこぼすため）。
   ```bash
   uv run --with neo4j --with python-dotenv python claude-skills/wamnet-provider-sync/scripts/sync_providers.py \
     --mode diff --dry-run \
     --csv-file ~/Ai-Workspace/WAM-NET/wamnet_data/kitakyushu_services_202609.csv \
     --output ~/Desktop/sync_dryrun_202609.md
   grep -A12 "更新結果サマリー" ~/Desktop/sync_dryrun_202609.md
   grep -A4 "要確認" ~/Desktop/sync_dryrun_202609.md
   ```
   レポートには事業所名の一覧も入るが、河原さんへの報告は**件数の表と、利用中の利用者の人数だけ**にする。
5. 結果の読み方
   - 新規・更新・廃止・近郊外・判定不能・変更なしの件数を報告する。
   - **更新＋変更なしが 0 に近く、廃止＋近郊外が 4000 件前後**なら、既存ノードの providerId の書き方が今のスクリプトと違う。
     その場合は書き込まずに止め、既存の providerId の形（例: `MATCH (sp:ServiceProvider) RETURN sp.providerId LIMIT 5` の形だけ）を河原さんに報告する。
   - 近郊外は作業 A の 638 件前後になるはず。大きく違えば理由を確かめる。
6. 河原さんの承認を得たら、`--dry-run` を外して同じコマンドを流す。
7. 重なりを数える（件数だけ。まとめるのは別途承認を得てから）。
   ```cypher
   MATCH (sp:ServiceProvider) WHERE sp.wamnetId IS NOT NULL
   WITH sp.wamnetId AS id, sp.serviceType AS st, count(*) AS n WHERE n > 1
   RETURN count(*) AS groups, sum(n) AS nodes
   ```
8. 起動したコンテナは止める。

## 作業 D：プルリクエスト（任意）

直したコードは neo4j-agno-agent と oya-inai-db のブランチ `claude/tender-gauss-m4ky9k` にある。
main に入れるなら、河原さんの指示を受けてからプルリクエストを作る（クラウドのセッションからでも作れる）。

## 終わったら河原さんに報告すること

- 作業 A の件数（新表の市区町村 / 新表に無い市区町村 / city が空）
- 作業 B でどちらにしたか
- 作業 C の定期実行を登録したか、一度動かした結果
- 作業 E の dry-run の件数の表、利用中の利用者の人数、重なりの件数
