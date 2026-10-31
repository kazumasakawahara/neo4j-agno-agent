# Mac の Claude Code への指示書：backup_20261031_114019 を keep_ に改名する

作成: 2026-10-31（クラウドのセッションから）。

`scripts/backup.sh` は `neo4j_backup/` の `backup_*` を 30 日で自動削除する。`keep_` で始まるものは対象外。
10/31 11:40 のバックアップ（個人ノード削除前、Client 12 を含む最後の状態）を残すので、改名する。
DB には触れない。ファイル名を変えるだけ。

## 手順

```bash
cd ~/Dev-Work/neo4j-agno-agent/neo4j_backup
ls -la backup_20261031_114019*          # 対象を確かめる（.dump と _stats.txt など、同じ時刻のもの全部）
for f in backup_20261031_114019*; do mv "$f" "keep_$f"; done
ls -la keep_*                           # keep_ が 4 時点分（10/30 20:11、10/31 07:51・08:13・11:40）あること
ls backup_* 2>/dev/null || echo "keep_ 以外の backup_ は無い"
```

## 報告

`ls -la keep_*` の結果（ファイル名とサイズ）だけ。中身は開かない。
