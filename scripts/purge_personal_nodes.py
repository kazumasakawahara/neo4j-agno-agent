#!/usr/bin/env python3
"""共有層（support-db-neo4j）から、個人に関わるノードを消す。

残すのは事業所まわりのラベルだけ（KEEP_LABELS）。それ以外のラベルのノードは、つながりごと消す。
消す前に --dry-run で「どのラベルを何件消すか」を出し、河原さんの承認を得てから --execute --yes で実行する。

使い方:
    NEO4J_PASSWORD=... uv run --with neo4j python scripts/purge_personal_nodes.py --dry-run
    NEO4J_PASSWORD=... uv run --with neo4j python scripts/purge_personal_nodes.py --execute --yes

出すのは件数だけ。プロパティの値は読まない。
"""
import argparse
import os
import sys
from datetime import datetime

from neo4j import GraphDatabase, READ_ACCESS

# 共有層に残すラベル。これ以外は全部消す
KEEP_LABELS = ["ServiceProvider", "ProviderFeedback"]

# 複数ラベルを持つノードで、残すラベルと消すラベルが同居していたら止める（想定外）
QUERY_PLAN = """
MATCH (n)
WITH n, [l IN labels(n) WHERE l IN $keep] AS keep, [l IN labels(n) WHERE NOT l IN $keep] AS drop
RETURN
  CASE WHEN size(keep) > 0 AND size(drop) > 0 THEN 'mixed'
       WHEN size(keep) > 0 THEN 'keep' ELSE 'drop' END AS kind,
  labels(n) AS labels, count(n) AS c
ORDER BY kind, c DESC
"""

QUERY_FEEDBACK_AUTHORS = """
MATCH (:Supporter)-[r:WROTE]->(:ProviderFeedback) RETURN count(r) AS c
"""

QUERY_DELETE = """
MATCH (n)
WHERE none(l IN labels(n) WHERE l IN $keep)
WITH n LIMIT $batch
DETACH DELETE n
RETURN count(*) AS deleted
"""


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    p.add_argument("--yes", action="store_true", help="--execute のとき、バックアップを取ったことの確認")
    p.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    p.add_argument("--batch", type=int, default=500)
    p.add_argument("--output", "-o")
    args = p.parse_args()
    if args.execute and not args.yes:
        sys.exit("❌ --execute には --yes が要ります。先に scripts/backup.sh でバックアップを取ってください")

    password = os.environ.get("NEO4J_PASSWORD", "")
    if not password:
        sys.exit("NEO4J_PASSWORD が未設定です")
    driver = GraphDatabase.driver(args.uri, auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), password))
    driver.verify_connectivity()

    with driver.session(default_access_mode=READ_ACCESS) as s:
        plan = [r.data() for r in s.run(QUERY_PLAN, keep=KEEP_LABELS)]
        authors = s.run(QUERY_FEEDBACK_AUTHORS).single()["c"]
    mixed = [r for r in plan if r["kind"] == "mixed"]
    keep = [r for r in plan if r["kind"] == "keep"]
    drop = [r for r in plan if r["kind"] == "drop"]

    lines = [f"# 共有層の個人ノード削除 {'計画（dry-run）' if args.dry_run else '実行'}",
             f"URI: {args.uri}  日時: {datetime.now():%Y-%m-%d %H:%M}", "",
             "## 残すノード", "| ラベル | 件数 |", "|---|---|"]
    lines += [f"| {':'.join(r['labels'])} | {r['c']} |" for r in keep] or ["| （なし） | |"]
    lines += ["", "## 消すノード", "| ラベル | 件数 |", "|---|---|"]
    lines += [f"| {':'.join(r['labels'])} | {r['c']} |" for r in drop] or ["| （なし） | |"]
    lines += ["", f"消すノードの合計: {sum(r['c'] for r in drop)} 件", f"残るノードの合計: {sum(r['c'] for r in keep)} 件"]
    if authors:
        lines += ["", f"⚠️ 口コミ（ProviderFeedback）の作成者リンク WROTE が {authors} 本ある。Supporter を消すと作成者が分からなくなる"]
    if mixed:
        lines += ["", "❌ 残すラベルと消すラベルを同時に持つノードがある。想定外なので止める", "| ラベル | 件数 |", "|---|---|"]
        lines += [f"| {':'.join(r['labels'])} | {r['c']} |" for r in mixed]

    if args.execute and not mixed:
        total = 0
        with driver.session() as s:
            while True:
                n = s.execute_write(lambda tx: tx.run(QUERY_DELETE, keep=KEEP_LABELS, batch=args.batch).single()["deleted"])
                total += n
                if n == 0:
                    break
                print(f"  削除: {total}")
        with driver.session(default_access_mode=READ_ACCESS) as s:
            remaining = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rem_labels = [r.data() for r in s.run("CALL db.labels() YIELD label CALL { WITH label MATCH (n) WHERE label IN labels(n) RETURN count(n) AS c } RETURN label, c")]
        lines += ["", f"**削除した: {total} 件。残り: {remaining} 件**", "| 残ったラベル | 件数 |", "|---|---|"]
        lines += [f"| {r['label']} | {r['c']} |" for r in rem_labels if r["c"]]
    driver.close()

    text = "\n".join(lines)
    if args.output:
        with open(os.path.expanduser(args.output), "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)
    return 1 if mixed else 0


if __name__ == "__main__":
    sys.exit(main())
