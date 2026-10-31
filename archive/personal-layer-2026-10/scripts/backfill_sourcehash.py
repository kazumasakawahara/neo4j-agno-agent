"""
既存ノードへの sourceHash 一括付与（バックフィル）スクリプト

SupportLog, MeetingRecord, LifeHistory, Wish の既存ノードに
sourceHash (SHA256) を付与する。

使用例:
    uv run python scripts/backfill_sourcehash.py --all
    uv run python scripts/backfill_sourcehash.py --label SupportLog
    uv run python scripts/backfill_sourcehash.py --dry-run
    uv run python scripts/backfill_sourcehash.py --stats
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase

TARGET_LABELS = ["SupportLog", "MeetingRecord", "LifeHistory", "Wish"]

# Properties to EXCLUDE from hash computation (meta-properties)
EXCLUDE_PROPS = {"sourceHash", "embedding", "embeddingUpdatedAt", "textEmbedding", "summaryEmbedding"}


def log(message, level="INFO"):
    prefix = {"INFO": "  ", "OK": "  ✅", "WARN": "  ⚠️", "ERROR": "  ❌"}
    sys.stderr.write(f"{prefix.get(level, '  ')} {message}\n")
    sys.stderr.flush()


def get_driver():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, password))


def compute_hash(props: dict) -> str:
    """Compute sourceHash from node properties, excluding meta-properties."""
    filtered = {k: v for k, v in sorted(props.items()) if k not in EXCLUDE_PROPS}
    hash_input = json.dumps(filtered, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


def get_stats(driver):
    """Show sourceHash coverage stats."""
    print("\n📊 sourceHash 統計:")
    print(f"  {'ラベル':<20} {'付与済み':>8} / {'全体':>8}  {'率':>7}")
    print(f"  {'─' * 50}")
    with driver.session() as session:
        for label in TARGET_LABELS:
            total = session.run(
                f"MATCH (n:{label}) RETURN count(n) AS c"
            ).single()["c"]
            with_hash = session.run(
                f"MATCH (n:{label}) WHERE n.sourceHash IS NOT NULL RETURN count(n) AS c"
            ).single()["c"]
            rate = f"{with_hash/total*100:.1f}%" if total > 0 else "N/A"
            print(f"  {label:<20} {with_hash:>8} / {total:>8}  {rate:>7}")


def backfill_label(driver, label: str, dry_run: bool = False, batch_size: int = 100):
    """Backfill sourceHash for a single label."""
    log(f"Processing {label}...")

    with driver.session() as session:
        # Fetch nodes without sourceHash
        result = session.run(
            f"MATCH (n:{label}) WHERE n.sourceHash IS NULL RETURN elementId(n) AS id, properties(n) AS props"
        )
        nodes = [(record["id"], record["props"]) for record in result]

    if not nodes:
        log(f"{label}: No nodes without sourceHash", "OK")
        return 0

    log(f"{label}: {len(nodes)} nodes need sourceHash")

    if dry_run:
        log(f"{label}: Dry run — would update {len(nodes)} nodes", "INFO")
        return len(nodes)

    updated = 0
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i:i + batch_size]
        with driver.session() as session:
            for node_id, props in batch:
                source_hash = compute_hash(props)
                session.run(
                    "MATCH (n) WHERE elementId(n) = $id SET n.sourceHash = $hash",
                    {"id": node_id, "hash": source_hash},
                )
                updated += 1
        log(f"{label}: {updated}/{len(nodes)} updated")

    log(f"{label}: Completed — {updated} nodes updated", "OK")
    return updated


def main():
    parser = argparse.ArgumentParser(description="既存ノードへの sourceHash バックフィル")
    parser.add_argument("--all", action="store_true", help="全対象ラベルを処理")
    parser.add_argument("--label", type=str, help="特定ラベルのみ処理")
    parser.add_argument("--dry-run", action="store_true", help="実際には更新しない")
    parser.add_argument("--batch-size", type=int, default=100, help="バッチサイズ")
    parser.add_argument("--stats", action="store_true", help="統計のみ表示")
    args = parser.parse_args()

    driver = get_driver()
    try:
        driver.verify_connectivity()
        log("Neo4j connected")
    except Exception as e:
        log(f"Neo4j connection failed: {e}", "ERROR")
        sys.exit(1)

    if args.stats:
        get_stats(driver)
        driver.close()
        return

    if not args.all and not args.label:
        parser.print_help()
        sys.exit(1)

    labels = TARGET_LABELS if args.all else [args.label]
    for label in labels:
        if label not in TARGET_LABELS:
            log(f"Unsupported label: {label}", "ERROR")
            continue
        backfill_label(driver, label, dry_run=args.dry_run, batch_size=args.batch_size)

    print()
    get_stats(driver)
    driver.close()


if __name__ == "__main__":
    main()
