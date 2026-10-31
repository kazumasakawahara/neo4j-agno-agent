#!/usr/bin/env python3
"""Neo4j の中身を件数だけで棚卸しする（読み取り専用）。

ラベルごとのノード数、リレーション種別ごとの本数、制約・インデックスの数を出す。
プロパティの値（氏名・住所など）は一切読まない・出さない。

使い方:
    NEO4J_PASSWORD=... uv run --with neo4j python scripts/db_inventory.py --uri bolt://localhost:7687 --name support-db-neo4j
    出力先を指定: --output ~/Ai-Workspace/WAM-NET/wamnet_data/reports/inventory_support-db-neo4j.md
"""
import argparse
import os
import sys
from datetime import datetime

from neo4j import GraphDatabase, READ_ACCESS

# 個人情報を持つラベル（親亡き後支援 DB のスキーマ）。共有層に残っていないかを見る
PERSONAL_LABELS = [
    "Client", "KeyPerson", "Guardian", "Supporter", "SupportLog", "MeetingRecord",
    "NgAction", "CarePreference", "Condition", "Certificate", "PublicAssistance",
    "EconomicRisk", "MoneyManagement", "AuditLog", "Narrative", "Family",
]
# 共有してよいラベル（事業所・制度）
SHARED_LABELS = ["ServiceProvider", "ProviderFeedback", "Service", "Organization", "Law", "Institution"]


def run(session, query):
    return [r.data() for r in session.run(query)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--uri", required=True)
    p.add_argument("--name", required=True, help="DB の呼び名（レポートの見出しに使う）")
    p.add_argument("--output", "-o")
    args = p.parse_args()

    password = os.environ.get("NEO4J_PASSWORD", "")
    if not password:
        sys.exit("NEO4J_PASSWORD が未設定です")
    driver = GraphDatabase.driver(args.uri, auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), password))
    driver.verify_connectivity()

    with driver.session(default_access_mode=READ_ACCESS) as s:
        total_nodes = run(s, "MATCH (n) RETURN count(n) AS c")[0]["c"]
        total_rels = run(s, "MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
        labels = run(s, """
            CALL db.labels() YIELD label
            CALL { WITH label MATCH (n) WHERE label IN labels(n) RETURN count(n) AS c }
            RETURN label, c ORDER BY c DESC, label
        """)
        rels = run(s, """
            CALL db.relationshipTypes() YIELD relationshipType AS t
            CALL { WITH t MATCH ()-[r]->() WHERE type(r) = t RETURN count(r) AS c }
            RETURN t, c ORDER BY c DESC, t
        """)
        constraints = run(s, "SHOW CONSTRAINTS YIELD name RETURN count(*) AS c")[0]["c"]
        indexes = run(s, "SHOW INDEXES YIELD name, type RETURN type, count(*) AS c ORDER BY type")
        # ServiceProvider があれば、整った形かどうかの目安
        sp = {}
        if any(l["label"] == "ServiceProvider" for l in labels):
            sp = run(s, """
                MATCH (sp:ServiceProvider)
                RETURN count(sp) AS total,
                       count(CASE WHEN sp.providerId =~ '\\d{10}_\\d{2}' THEN 1 END) AS newId,
                       count(CASE WHEN sp.wamnetId IS NOT NULL THEN 1 END) AS withWamnetId,
                       count(CASE WHEN sp.office_number IS NOT NULL THEN 1 END) AS legacyKeys,
                       count(CASE WHEN sp.status = 'Closed' THEN 1 END) AS closed,
                       count(CASE WHEN sp.outOfArea = true THEN 1 END) AS outOfArea,
                       count(CASE WHEN sp.mergedAt IS NOT NULL THEN 1 END) AS merged
            """)[0]
    driver.close()

    label_map = {l["label"]: l["c"] for l in labels}
    personal = {l: label_map[l] for l in PERSONAL_LABELS if l in label_map}
    shared = {l: label_map[l] for l in SHARED_LABELS if l in label_map}
    other = {l: c for l, c in label_map.items() if l not in PERSONAL_LABELS and l not in SHARED_LABELS}

    out = [f"# DB 棚卸し: {args.name}", f"URI: {args.uri}  日時: {datetime.now():%Y-%m-%d %H:%M}", "",
           f"- ノード総数: {total_nodes}", f"- リレーション総数: {total_rels}",
           f"- 制約: {constraints}  インデックス: " + ", ".join(f"{i['type']} {i['c']}" for i in indexes), ""]
    for title, d in (("個人情報を持つラベル", personal), ("共有してよいラベル", shared), ("その他のラベル", other)):
        out += [f"## {title}", "| ラベル | 件数 |", "|---|---|"]
        out += [f"| {l} | {c} |" for l, c in d.items()] or ["| （なし） | |"]
        out.append("")
    out += ["## リレーション", "| 種別 | 本数 |", "|---|---|"]
    out += [f"| {r['t']} | {r['c']} |" for r in rels] or ["| （なし） | |"]
    if sp:
        out += ["", "## ServiceProvider の形", "| 項目 | 件数 |", "|---|---|"]
        out += [f"| {k} | {v} |" for k, v in sp.items()]
    text = "\n".join(out)
    if args.output:
        with open(os.path.expanduser(args.output), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"📄 {args.output}")
    print(text)


if __name__ == "__main__":
    main()
