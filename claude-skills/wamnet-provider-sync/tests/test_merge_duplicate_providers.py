"""merge_duplicate_providers.py の試験（Neo4j には接続しない）。

    cd claude-skills/wamnet-provider-sync
    uv run --with pytest --with neo4j --with python-dotenv pytest tests
"""
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from merge_duplicate_providers import DuplicateMerger, business_number, canonical  # noqa: E402


@pytest.fixture
def m():
    return DuplicateMerger()


def test_canonical_moves_legacy_keys_without_overriding_formal():
    node = {"office_name": "旧名", "name": "新名", "service_type": "生活介護", "office_number": "1000000001"}
    c = canonical(node)
    assert c["name"] == "新名"            # 正式名があればそちら
    assert c["serviceType"] == "生活介護"  # 無ければレガシーから
    assert c["wamnetId"] == "1000000001"
    assert "office_name" not in c and "service_type" not in c


@pytest.mark.parametrize(
    "node, expected",
    [
        ({"wamnetId": "1000000001"}, "1000000001"),
        ({"office_number": "1000000002"}, "1000000002"),
        ({"providerId": "1000000003"}, "1000000003"),
        ({"providerId": "1000000004_11"}, "1000000004"),
        ({"providerId": "abc", "name": "x"}, ""),
        ({}, ""),
    ],
)
def test_business_number(node, expected):
    assert business_number(node) == expected


def test_find_groups_uses_number_and_normalized_service(m):
    nodes = {
        "a": {"providerId": "1000000001_41", "wamnetId": "1000000001", "serviceType": "自立訓練_機能訓練"},
        "b": {"office_number": "1000000001", "service_type": "自立訓練（機能訓練）"},   # レガシー名・表記ゆれ
        "c": {"providerId": "1000000001", "serviceType": "生活介護"},                    # 別サービス → 別の組
        "d": {"wamnetId": "1000000002", "serviceType": "生活介護"},                      # 1 つだけ → 組にならない
        "e": {"name": "番号なし", "serviceType": "生活介護"},                             # 対象外
        "f": {"wamnetId": "1000000003"},                                                # サービス種類なし → 対象外
    }
    groups = m.find_groups(nodes)
    assert list(groups.values()) == [["a", "b"]]
    assert m.stats["skipped_no_key"] == 2


def test_survivor_prefers_new_id_then_name_then_recent_then_rels(m):
    nodes = {
        "old": {"providerId": "1000000001", "name": "x", "updatedAt": "2026-10-30T20:00"},
        "new": {"providerId": "1000000001_11", "name": "x", "updatedAt": "2026-01-01"},
        "noname": {"providerId": "1000000001_11", "office_name": "x", "updatedAt": "2026-12-31"},
    }
    rels = {"old": Counter({"USES_SERVICE": 3})}
    assert m.order_group(list(nodes), nodes, rels)[0] == "new"
    # 新しい形が無ければ、名前あり → updatedAt → つながりの順
    del nodes["new"]; del nodes["noname"]
    nodes["b"] = {"providerId": "1000000001", "name": "x", "updatedAt": "2026-10-30T20:00"}
    nodes["c"] = {"providerId": "1000000001", "name": "x", "updatedAt": "2026-10-30T21:00"}
    assert m.order_group(["old", "b", "c"], nodes, rels)[0] == "c"
    nodes["c"]["updatedAt"] = nodes["old"]["updatedAt"]
    assert m.order_group(["old", "b", "c"], nodes, rels)[0] == "old"  # 同点ならつながりが多い方


def test_merge_properties_fills_gaps_and_keeps_human_values(m):
    merged, conflicts = m.merge_properties([
        {"providerId": "1000000001_11", "name": "新", "phone": "093-000-0000", "availability": "未確認"},
        {"office_name": "旧", "office_number": "1000000001", "address": "1-2-3", "availability": "空きあり",
         "corp_name": "法人", "phone": "093-999-9999"},
    ])
    assert merged["name"] == "新"                 # 残す側の値
    assert merged["address"] == "1-2-3"           # 空のところは埋める
    assert merged["corporateName"] == "法人"       # レガシー名から正式名へ
    assert merged["availability"] == "空きあり"    # 人が記録した値は「未確認」より優先
    assert merged["wamnetId"] == "1000000001"
    assert merged["mergedFrom"] == 2
    assert conflicts == {"phone": 1, "name": 1}   # 電話と名前が食い違っていた（残す側の値を使う）
    assert "office_name" not in merged and "corp_name" not in merged


def test_closed_and_out_of_area_kept_only_when_all_nodes_have_them(m):
    merged, conflicts = m.merge_properties([
        {"providerId": "1_11", "status": "Closed", "closedAt": "x", "outOfArea": True, "outOfAreaAt": "y"},
        {"providerId": "1_11", "name": "営業中"},
    ])
    assert "status" not in merged and "closedAt" not in merged
    assert "outOfArea" not in merged and "outOfAreaAt" not in merged
    assert conflicts["status"] == 1 and conflicts["outOfArea"] == 1

    merged, conflicts = m.merge_properties([
        {"providerId": "1_11", "status": "Closed", "closedAt": "x"},
        {"providerId": "1_11", "status": "Closed", "closedAt": "z"},
    ])
    assert merged["status"] == "Closed" and conflicts == {}


def test_plan_counts(m, monkeypatch):
    nodes = {
        "a": {"providerId": "1000000001_11", "wamnetId": "1000000001", "serviceType": "居宅介護", "name": "x"},
        "b": {"wamnetId": "1000000001", "serviceType": "居宅介護"},
        "c": {"wamnetId": "1000000001", "serviceType": "居宅介護"},
        "d": {"wamnetId": "1000000002", "serviceType": "居宅介護"},
        "e": {"providerId": "1000000002", "serviceType": "居宅介護"},
    }
    monkeypatch.setattr(m, "fetch_rel_counts", lambda eids: {"b": Counter({"USES_SERVICE": 2}),
                                                            "d": Counter({"HAS_FEEDBACK": 1})})
    plans = m.plan(nodes)
    assert len(plans) == 2
    assert plans[0]["survivor"] == "a" and sorted(plans[0]["others"]) == ["b", "c"]
    assert m.stats["groups"] == 2 and m.stats["nodes_to_remove"] == 3
    assert m.stats["group_size_3"] == 1 and m.stats["group_size_2"] == 1
    assert m.stats["rel_USES_SERVICE"] == 2 and m.stats["rel_HAS_FEEDBACK"] == 1
    assert m.stats["groups_moving_rels"] == 1  # d は残す側なので移す必要なし。b は消える側 → 移す
    report = m.report("試験")
    assert "| 重複の組 | 2 |" in report and "x" not in report.replace("dry-run", "")


def test_unjudged_legacy_node_does_not_reopen_closed_group(m):
    """2026-10-31 の dry-run で見つかった 10 組: Closed が付いたノードと、office_number しか持たず
    取り込みスクリプトの判定を受けていない旧来ノードの組。旧来ノードに印が無いのは営業中だからではないので、
    Closed を残す。"""
    merged, conflicts = m.merge_properties([
        {"providerId": "1000000001_11", "wamnetId": "1000000001", "status": "Closed", "closedAt": "x"},
        {"providerId": "1000000001", "status": "Closed", "closedAt": "y"},
        {"office_number": "1000000001", "office_name": "旧", "service_type": "居宅介護"},   # 判定外
    ])
    assert merged["status"] == "Closed" and merged["closedAt"] == "x"
    assert "status" not in conflicts


def test_judged_open_node_still_reopens(m):
    """判定を受けたノードの 1 つでも Closed でなければ、営業中とみなす（元の規則はそのまま）。"""
    merged, conflicts = m.merge_properties([
        {"providerId": "1000000001_11", "wamnetId": "1000000001", "status": "Closed", "closedAt": "x"},
        {"wamnetId": "1000000001", "name": "営業中"},
    ])
    assert "status" not in merged and conflicts["status"] == 1


def test_group_of_only_unjudged_nodes_uses_all(m):
    merged, _ = m.merge_properties([
        {"office_number": "1000000001", "status": "Closed"},
        {"office_number": "1000000001"},
    ])
    assert "status" not in merged


def test_merged_provider_id_prefers_new_form_in_group(m):
    """残す側に providerId が無くても、組の中の新しい形の providerId を使う。"""
    merged, _ = m.merge_properties([
        {"wamnetId": "4016400030", "name": "x", "updatedAt": "2026-10-30"},      # 残す側（providerId なし）
        {"providerId": "4016400030", "office_name": "x"},                        # 事業所番号だけ
        {"providerId": "4016400030_11", "wamnetId": "4016400030"},               # 新しい形
    ])
    assert merged["providerId"] == "4016400030_11"


def test_execute_removes_other_provider_ids_before_set(m):
    """一意制約を避けるため、消える側の providerId を外してから残す側に書く（Cypher の順序を確かめる）。"""
    import inspect
    src = inspect.getsource(m.execute)
    assert src.index("REMOVE o.providerId") < src.index("SET s = $props") < src.index("mergeNodes")


def test_execute_reports_failed_group(m):
    class Boom(Exception):
        pass

    class Session:
        def __init__(self):
            self.n = 0

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute_write(self, fn):
            self.n += 1
            if self.n == 3:
                raise Boom("constraint")

    class Driver:
        def session(self):
            return Session()

    m.driver = Driver()
    plans = [{"key": (f"100000000{i}", "s"), "survivor": f"s{i}", "others": [f"o{i}"], "props": {}} for i in range(5)]
    with pytest.raises(Boom):
        m.execute(plans)
    assert m.stats["executed_groups"] == 2 and m.stats["failed_at"] == 3
    assert "3 組目で止まった" in m.report("試験")
