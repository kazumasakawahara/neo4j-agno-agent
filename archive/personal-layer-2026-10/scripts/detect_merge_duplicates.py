#!/usr/bin/env python3
"""
既存ノードの重複検出・マージツール

使用例:
    uv run python scripts/detect_merge_duplicates.py --scan
    uv run python scripts/detect_merge_duplicates.py --scan --label Client
    uv run python scripts/detect_merge_duplicates.py --scan --label NgAction
    uv run python scripts/detect_merge_duplicates.py --merge --label Condition --dry-run
"""

import argparse
import os
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase
from lib.normalize import normalize_name, normalize_text, normalize_condition, name_to_kana

def log(msg, level="INFO"):
    prefix = {"INFO": "  ", "OK": "✅", "WARN": "⚠️", "ERROR": "❌", "DUP": "🔴"}
    sys.stderr.write(f"{prefix.get(level, '  ')} {msg}\n")
    sys.stderr.flush()

def get_driver():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    pw = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, pw))


def scan_client_duplicates(driver):
    """Find Client nodes with identical or similar kana readings."""
    log("Scanning Client duplicates (kana-based)...")
    with driver.session() as session:
        rows = session.run(
            "MATCH (c:Client) RETURN c.name AS name, c.kana AS kana, elementId(c) AS id"
        ).data()

    # Group by exact kana
    kana_groups = defaultdict(list)
    for r in rows:
        kana = r.get("kana") or name_to_kana(r["name"])
        if kana:
            kana_groups[kana].append(r)

    duplicates = []
    for kana, group in kana_groups.items():
        if len(group) >= 2:
            duplicates.append({
                "kana": kana,
                "nodes": group,
                "type": "exact_kana",
            })

    # Also check near-matches (ratio >= 0.9) for remaining singletons
    singletons = [g[0] for g in kana_groups.values() if len(g) == 1]
    for i, a in enumerate(singletons):
        kana_a = a.get("kana") or ""
        for b in singletons[i+1:]:
            kana_b = b.get("kana") or ""
            if kana_a and kana_b:
                ratio = SequenceMatcher(None, kana_a, kana_b).ratio()
                if ratio >= 0.9:
                    duplicates.append({
                        "kana_a": kana_a,
                        "kana_b": kana_b,
                        "similarity": round(ratio, 3),
                        "nodes": [a, b],
                        "type": "similar_kana",
                    })

    return duplicates


def scan_condition_duplicates(driver):
    """Find Condition nodes that normalize to the same canonical name."""
    log("Scanning Condition duplicates (alias-based)...")
    with driver.session() as session:
        rows = session.run(
            "MATCH (c:Condition) RETURN c.name AS name, elementId(c) AS id"
        ).data()

    canonical_groups = defaultdict(list)
    for r in rows:
        canonical = normalize_condition(r["name"])
        canonical_groups[canonical].append({**r, "canonical": canonical})

    return [
        {"canonical": canonical, "nodes": group, "type": "alias"}
        for canonical, group in canonical_groups.items()
        if len(group) >= 2
    ]


def scan_ngaction_duplicates(driver):
    """Find NgAction nodes with identical normalized action text."""
    log("Scanning NgAction duplicates (text normalization)...")
    with driver.session() as session:
        rows = session.run(
            "MATCH (ng:NgAction) RETURN ng.action AS action, ng.riskLevel AS riskLevel, elementId(ng) AS id"
        ).data()

    normalized_groups = defaultdict(list)
    for r in rows:
        norm = normalize_text(r["action"])
        normalized_groups[norm].append(r)

    return [
        {"action": norm, "nodes": group, "type": "normalized_text"}
        for norm, group in normalized_groups.items()
        if len(group) >= 2
    ]


def merge_condition_duplicates(driver, duplicates, dry_run=True):
    """Merge Condition nodes that map to the same canonical name."""
    merged = 0
    for dup in duplicates:
        canonical = dup["canonical"]
        nodes = dup["nodes"]
        # Keep the one already named canonically, or the first one
        keeper = next((n for n in nodes if n["name"] == canonical), nodes[0])
        to_merge = [n for n in nodes if n["id"] != keeper["id"]]

        for victim in to_merge:
            log(f"  Merge: '{victim['name']}' → '{keeper['name']}' (canonical: {canonical})", "DUP")
            if not dry_run:
                with driver.session() as session:
                    # Transfer all relationships from victim to keeper
                    session.run("""
                        MATCH (victim:Condition) WHERE elementId(victim) = $victim_id
                        MATCH (keeper:Condition) WHERE elementId(keeper) = $keeper_id
                        CALL {
                            WITH victim, keeper
                            MATCH (victim)<-[r]-()
                            WITH victim, keeper, collect(r) AS rels
                            UNWIND rels AS rel
                            WITH victim, keeper, rel, startNode(rel) AS src, type(rel) AS relType
                            CALL apoc.create.relationship(src, relType, properties(rel), keeper) YIELD rel AS newRel
                            RETURN count(newRel) AS inbound
                        }
                        CALL {
                            WITH victim, keeper
                            MATCH (victim)-[r]->()
                            WITH victim, keeper, collect(r) AS rels
                            UNWIND rels AS rel
                            WITH victim, keeper, rel, endNode(rel) AS tgt, type(rel) AS relType
                            CALL apoc.create.relationship(keeper, relType, properties(rel), tgt) YIELD rel AS newRel
                            RETURN count(newRel) AS outbound
                        }
                        DETACH DELETE victim
                    """, {"victim_id": victim["id"], "keeper_id": keeper["id"]})
                merged += 1

    return merged


def print_report(label, duplicates):
    """Pretty-print duplicate report."""
    if not duplicates:
        log(f"{label}: No duplicates found", "OK")
        return

    print(f"\n{'='*60}")
    print(f"  {label}: {len(duplicates)} duplicate group(s) found")
    print(f"{'='*60}")

    for i, dup in enumerate(duplicates, 1):
        dup_type = dup.get("type", "unknown")
        print(f"\n  Group {i} ({dup_type}):")
        for node in dup["nodes"]:
            name = node.get("name") or node.get("action") or "?"
            extra = ""
            if "kana" in node:
                extra = f" (kana: {node['kana']})"
            elif "canonical" in node:
                extra = f" → {node['canonical']}"
            elif "riskLevel" in node:
                extra = f" [{node.get('riskLevel', '')}]"
            print(f"    - {name}{extra}  [id: {node['id'][:20]}...]")

        if "similarity" in dup:
            print(f"    similarity: {dup['similarity']}")


def main():
    parser = argparse.ArgumentParser(description="既存ノードの重複検出・マージツール")
    parser.add_argument("--scan", action="store_true", help="重複スキャンを実行")
    parser.add_argument("--merge", action="store_true", help="検出された重複をマージ（Conditionのみ対応）")
    parser.add_argument("--label", type=str, help="特定ラベルのみ（Client/Condition/NgAction）")
    parser.add_argument("--dry-run", action="store_true", help="マージ時、実際には変更しない")
    args = parser.parse_args()

    if not args.scan and not args.merge:
        parser.print_help()
        sys.exit(1)

    driver = get_driver()
    try:
        driver.verify_connectivity()
        log("Neo4j connected")
    except Exception as e:
        log(f"Connection failed: {e}", "ERROR")
        sys.exit(1)

    labels = [args.label] if args.label else ["Client", "Condition", "NgAction"]

    if args.scan:
        for label in labels:
            if label == "Client":
                dups = scan_client_duplicates(driver)
                print_report("Client", dups)
            elif label == "Condition":
                dups = scan_condition_duplicates(driver)
                print_report("Condition", dups)
            elif label == "NgAction":
                dups = scan_ngaction_duplicates(driver)
                print_report("NgAction", dups)

    if args.merge:
        if args.label == "Condition":
            dups = scan_condition_duplicates(driver)
            if dups:
                action = "DRY RUN" if args.dry_run else "MERGE"
                log(f"Condition: {action} — {len(dups)} groups")
                merged = merge_condition_duplicates(driver, dups, dry_run=args.dry_run)
                if not args.dry_run:
                    log(f"Merged {merged} duplicate Condition nodes", "OK")
            else:
                log("Condition: No duplicates to merge", "OK")
        else:
            log("Merge is currently only supported for Condition nodes.", "WARN")
            log("Client and NgAction require manual review due to relationship complexity.", "INFO")

    driver.close()


if __name__ == "__main__":
    main()
