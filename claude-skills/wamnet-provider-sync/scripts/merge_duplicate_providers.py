#!/usr/bin/env python3
"""
ServiceProvider の重複ノードを 1 つにまとめる

同じ事業所番号・同じサービス種類の ServiceProvider が複数あるとき（旧来の取り込みで ID の形が
揃っていなかったため）、1 つを残してほかを消し、つながり（USES_SERVICE・HAS_FEEDBACK など）と
プロパティを残す側に寄せる。

使用方法:
    # 1. 数えるだけ（読み取り専用）
    python merge_duplicate_providers.py --count
    # 2. どうまとめるかの計画を件数で出す（読み取り専用）
    python merge_duplicate_providers.py --dry-run
    # 3. 実際にまとめる（先にバックアップを取ること）
    python merge_duplicate_providers.py --execute --yes

出すのは件数だけ。事業所名や利用者の氏名は出さない。
Neo4j の APOC プラグイン（apoc.refactor.mergeNodes）を使う。
"""

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))
from sync_providers import ServiceProviderSync  # noqa: E402  サービス種類の正規化を共用する

try:
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("必要なパッケージをインストールしてください: pip install neo4j python-dotenv")
    sys.exit(1)


# レガシー名（snake_case）→ 正式名（camelCase）。docs/NEO4J_SCHEMA_CONVENTION.md §6.4
LEGACY_KEYS = {
    "office_name": "name",
    "corp_name": "corporateName",
    "service_type": "serviceType",
    "office_number": "wamnetId",
    "closed_days": "closedDays",
    "hours_weekday": "hoursWeekday",
    "updated_at": "updatedAt",
}

# 人が記録する値。「未確認」や空より、入っている値を優先する
HUMAN_KEYS = ("availability", "currentUsers", "targetDisability", "features")
HUMAN_EMPTY = {None, "", "未確認"}

NEW_ID = re.compile(r"\d{10}_\d{2}")
NUMBER_ONLY = re.compile(r"\d{10}")


def is_empty(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def canonical(node: Dict) -> Dict:
    """レガシー名のプロパティを正式名に寄せる（正式名に値があればそちらを優先）。"""
    out = {k: v for k, v in node.items() if k not in LEGACY_KEYS}
    for legacy, formal in LEGACY_KEYS.items():
        if is_empty(out.get(formal)) and not is_empty(node.get(legacy)):
            out[formal] = node[legacy]
    return out


def business_number(node: Dict) -> str:
    """事業所番号（10 桁）。wamnetId → office_number → providerId（事業所番号だけ／先頭 10 桁）の順。"""
    for key in ("wamnetId", "office_number"):
        value = str(node.get(key) or "").strip()
        if NUMBER_ONLY.fullmatch(value):
            return value
    provider_id = str(node.get("providerId") or "").strip()
    if NUMBER_ONLY.fullmatch(provider_id):
        return provider_id
    head = provider_id.split("_", 1)[0]
    return head if NUMBER_ONLY.fullmatch(head) else ""


class DuplicateMerger:
    def __init__(self):
        self.sync = ServiceProviderSync(dry_run=True)  # service_key と split_prefecture を借りる
        self.driver = None
        self.stats = Counter()

    # ---- 接続 ----

    def connect(self, uri: str):
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")
        if not password:
            raise SystemExit("NEO4J_PASSWORD 環境変数が設定されていません")
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.driver.verify_connectivity()

    def close(self):
        if self.driver:
            self.driver.close()

    def apoc_available(self) -> bool:
        with self.driver.session() as session:
            try:
                session.run("RETURN apoc.version() AS v").single()
                return True
            except Exception:
                return False

    # ---- 読み取り ----

    def fetch_nodes(self) -> Dict[str, Dict]:
        """elementId → プロパティ（レガシー名も含めたまま）"""
        query = "MATCH (sp:ServiceProvider) RETURN elementId(sp) AS eid, properties(sp) AS props"
        with self.driver.session() as session:
            return {r["eid"]: dict(r["props"]) for r in session.run(query)}

    def fetch_rel_counts(self, eids: List[str]) -> Dict[str, Counter]:
        """elementId → {リレーション種別: 本数}"""
        query = """
        MATCH (sp:ServiceProvider) WHERE elementId(sp) IN $eids
        OPTIONAL MATCH (sp)-[r]-()
        RETURN elementId(sp) AS eid, type(r) AS t, count(r) AS n
        """
        out = defaultdict(Counter)
        with self.driver.session() as session:
            for rec in session.run(query, eids=eids):
                if rec["t"]:
                    out[rec["eid"]][rec["t"]] = rec["n"]
        return out

    # ---- 判定 ----

    def group_key(self, node: Dict) -> Optional[Tuple[str, str]]:
        c = canonical(node)
        number = business_number(c)
        service = self.sync.service_key(c.get("serviceType"))
        if not number or not service:
            return None
        return number, service

    def find_groups(self, nodes: Dict[str, Dict]) -> Dict[Tuple[str, str], List[str]]:
        groups = defaultdict(list)
        for eid, node in nodes.items():
            key = self.group_key(node)
            if key is None:
                self.stats["skipped_no_key"] += 1
                continue
            groups[key].append(eid)
        return {k: v for k, v in groups.items() if len(v) > 1}

    @staticmethod
    def survivor_rank(node: Dict, rels: Counter) -> tuple:
        """残す側の優先順位。大きいほど残す。
        1. providerId が新しい形  2. 正式名の name がある  3. updatedAt が新しい  4. つながりが多い"""
        c = canonical(node)
        return (
            1 if NEW_ID.fullmatch(str(c.get("providerId") or "")) else 0,
            0 if is_empty(node.get("name")) else 1,
            str(c.get("updatedAt") or ""),
            sum(rels.values()),
        )

    def order_group(self, eids: List[str], nodes: Dict[str, Dict], rels: Dict[str, Counter]) -> List[str]:
        """先頭が残す側。"""
        return sorted(eids, key=lambda e: self.survivor_rank(nodes[e], rels.get(e, Counter())), reverse=True)

    @staticmethod
    def was_judged(node: Dict) -> bool:
        """取り込みスクリプト（2026-10-30 の版）が廃止・近郊外の判定をしたノードか。
        あの版は wamnetId か providerId からしか事業所番号を読まなかったので、office_number だけのノードは判定外。"""
        return bool(str(node.get("wamnetId") or "").strip()) or bool(str(node.get("providerId") or "").strip())

    def merge_properties(self, ordered: List[Dict]) -> Tuple[Dict, Counter]:
        """残す側（ordered[0]）を土台に、空のところだけほかのノードから埋める。
        人が記録する値は「未確認」より入っている値を優先。status=Closed・outOfArea は全ノードに付いているときだけ残す。
        戻り値: (まとめたプロパティ, 衝突の件数)"""
        conflicts = Counter()
        cs = [canonical(n) for n in ordered]
        merged = dict(cs[0])
        for other in cs[1:]:
            for k, v in other.items():
                if is_empty(v):
                    continue
                if is_empty(merged.get(k)):
                    merged[k] = v
                elif str(merged[k]) != str(v) and k in ("name", "address", "phone", "city"):
                    conflicts[k] += 1  # 残す側の値を使う。件数だけ記録する
        for k in HUMAN_KEYS:
            values = [c.get(k) for c in cs if c.get(k) not in HUMAN_EMPTY]
            if values:
                merged[k] = values[0]
        # 廃止・近郊外の印は、判定を受けたノード全部に付いているときだけ残す。1 つでも付いていなければ営業中・近郊内とみなす。
        # 判定を受けていないノード（取り込みスクリプトが事業所番号を読めなかった旧来ノード。2026-10-31 の dry-run で
        # 10 組）は、印が無いのは「営業中だから」ではないので、数に入れない
        judged = [c for c, n in zip(cs, ordered) if self.was_judged(n)] or cs
        closed = [c.get("status") == "Closed" for c in judged]
        if not all(closed):
            if merged.get("status") == "Closed":
                merged.pop("status")
            merged.pop("closedAt", None)
            if any(closed):
                conflicts["status"] += 1
        out_of_area = [bool(c.get("outOfArea")) for c in judged]
        if not all(out_of_area):
            merged.pop("outOfArea", None)
            merged.pop("outOfAreaAt", None)
            if any(out_of_area):
                conflicts["outOfArea"] += 1
        number = business_number(merged)
        if number:
            merged["wamnetId"] = number
        merged["mergedAt"] = datetime.now().isoformat()
        merged["mergedFrom"] = len(ordered)
        return merged, conflicts

    # ---- 実行 ----

    def plan(self, nodes: Dict[str, Dict]) -> List[Dict]:
        groups = self.find_groups(nodes)
        all_eids = [e for eids in groups.values() for e in eids]
        rels = self.fetch_rel_counts(all_eids) if all_eids else {}
        plans = []
        for key, eids in sorted(groups.items()):
            ordered = self.order_group(eids, nodes, rels)
            merged, conflicts = self.merge_properties([nodes[e] for e in ordered])
            rel_total = Counter()
            for e in eids:
                rel_total.update(rels.get(e, Counter()))
            plans.append({
                "key": key, "survivor": ordered[0], "others": ordered[1:],
                "props": merged, "conflicts": conflicts, "rels": rel_total,
            })
            self.stats["groups"] += 1
            self.stats["nodes_in_groups"] += len(eids)
            self.stats["nodes_to_remove"] += len(eids) - 1
            self.stats[f"group_size_{len(eids)}"] += 1
            for k, n in conflicts.items():
                self.stats[f"conflict_{k}"] += n
            for t, n in rel_total.items():
                self.stats[f"rel_{t}"] += n
            if any(rels.get(e) for e in ordered[1:]):
                self.stats["groups_moving_rels"] += 1
        return plans

    def execute(self, plans: List[Dict], batch_size: int = 50):
        """グループごとに 1 トランザクション。残す側にまとめたプロパティを書き、APOC でつながりを寄せて消す。"""
        query = """
        MATCH (s:ServiceProvider) WHERE elementId(s) = $survivor
        SET s = $props
        WITH s
        MATCH (o:ServiceProvider) WHERE elementId(o) IN $others
        WITH s, collect(o) AS others
        CALL apoc.refactor.mergeNodes([s] + others, {properties: 'discard', mergeRels: true}) YIELD node
        RETURN elementId(node) AS eid
        """
        done = 0
        with self.driver.session() as session:
            for p in plans:
                session.execute_write(
                    lambda tx: tx.run(query, survivor=p["survivor"], others=p["others"], props=p["props"]).consume()
                )
                done += 1
                if done % batch_size == 0:
                    print(f"  まとめ済み: {done}/{len(plans)} 組")
        print(f"  まとめ済み: {done}/{len(plans)} 組")
        self.stats["executed_groups"] = done

    # ---- 報告 ----

    def report(self, mode: str) -> str:
        s = self.stats
        lines = [f"# ServiceProvider 重複まとめ {mode}", f"実行日時: {datetime.now():%Y-%m-%d %H:%M:%S}", ""]
        lines += [
            "| 項目 | 件数 |", "|---|---|",
            f"| 重複の組 | {s['groups']} |",
            f"| 組に含まれるノード | {s['nodes_in_groups']} |",
            f"| 消えるノード | {s['nodes_to_remove']} |",
        ]
        for k in sorted(k for k in s if k.startswith("group_size_")):
            lines.append(f"| 　うち {k.split('_')[-1]} 個の組 | {s[k]} |")
        lines += [
            f"| つながりを移す必要がある組 | {s['groups_moving_rels']} |",
            f"| 事業所番号かサービス種類が無く対象外のノード | {s['skipped_no_key']} |",
        ]
        rel_keys = sorted(k for k in s if k.startswith("rel_"))
        if rel_keys:
            lines += ["", "## 組に含まれるノードのつながり（本数）", "| 種別 | 本数 |", "|---|---|"]
            lines += [f"| {k[4:]} | {s[k]} |" for k in rel_keys]
        conf_keys = sorted(k for k in s if k.startswith("conflict_"))
        if conf_keys:
            lines += ["", "## 値が食い違っていた組（残す側の値を使う）", "| 項目 | 組数 |", "|---|---|"]
            lines += [f"| {k[9:]} | {s[k]} |" for k in conf_keys]
        if "executed_groups" in s:
            lines += ["", f"**実行済み: {s['executed_groups']} 組**"]
        return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="ServiceProvider の重複ノードをまとめる")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--count", action="store_true", help="重複の件数だけ数える（読み取り専用）")
    mode.add_argument("--dry-run", action="store_true", help="まとめる計画を件数で出す（読み取り専用）")
    mode.add_argument("--execute", action="store_true", help="実際にまとめる")
    p.add_argument("--yes", action="store_true", help="--execute のとき、バックアップを取ったことの確認")
    p.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    p.add_argument("--output", "-o", help="レポートの出力先（省略時は標準出力）")
    args = p.parse_args(argv)

    if args.execute and not args.yes:
        print("❌ --execute には --yes が要ります。先に scripts/backup.sh でバックアップを取ってください")
        return 2

    m = DuplicateMerger()
    m.connect(args.uri)
    try:
        if args.execute and not m.apoc_available():
            print("❌ APOC が使えません。docker-compose.yml の NEO4J_PLUGINS を確かめてください")
            return 1
        nodes = m.fetch_nodes()
        print(f"ServiceProvider: {len(nodes)} 件")
        plans = m.plan(nodes)
        label = "件数" if args.count else ("計画（dry-run）" if args.dry_run else "実行")
        if args.execute:
            m.execute(plans)
        report = m.report(label)
        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
            print(f"📄 レポート: {args.output}")
        print("\n" + report)
        return 0
    finally:
        m.close()


if __name__ == "__main__":
    sys.exit(main())
