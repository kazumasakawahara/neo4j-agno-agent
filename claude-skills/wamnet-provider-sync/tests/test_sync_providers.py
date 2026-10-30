"""sync_providers.py の試験（Neo4j には接続しない）。

    cd claude-skills/wamnet-provider-sync
    uv run --with pytest --with neo4j --with python-dotenv pytest tests
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from sync_providers import ServiceProviderSync  # noqa: E402

# wamnet_downloader.py が出す CSV の列名（2026-10-30 に 202609 の CSV の見出しで確認）
WAMNET_ROW = {
    "都道府県コード又は市区町村コード": "40000",
    "NO（※システム内の固有の番号、連番）": "1",
    "指定機関名": "福岡県",
    "法人の名称": "社会福祉法人テスト会",
    "事業所の名称": "テスト事業所",
    "事業所番号": "4010000001",
    "事業所住所（市区町村）": "福岡県遠賀郡芦屋町",
    "事業所住所（番地以降）": "1-2-3",
    "事業所電話番号": "０９３－０００－００００",
    "事業所FAX番号": "093-000-0001",
    "定員": "20",
    "サービス種類コード": "15",
    "サービス種類": "同行援護",
}


@pytest.fixture
def sync():
    return ServiceProviderSync(dry_run=True)


def test_row_to_provider_reads_wamnet_columns(sync):
    p = sync._row_to_provider(WAMNET_ROW)
    assert p["providerId"] == "4010000001_15"  # CSV のサービス種類コードを使う（設定ファイルの 13 ではない）
    assert p["wamnetId"] == "4010000001"
    assert p["name"] == "テスト事業所"
    assert p["prefecture"] == "福岡県"
    assert p["city"] == "遠賀郡芦屋町"
    assert p["address"] == "1-2-3"
    assert p["phone"] == "093-000-0000"
    assert p["fax"] == "093-000-0001"
    assert p["capacity"] == 20
    assert p["corporateName"] == "社会福祉法人テスト会"


def test_row_to_provider_still_reads_legacy_columns(sync):
    p = sync._row_to_provider(
        {"事業所番号": "1", "事業所名": "旧", "市区町村": "行橋市", "都道府県": "福岡県", "住所": "x", "サービス種類": "居宅介護"}
    )
    assert (p["name"], p["prefecture"], p["city"], p["address"]) == ("旧", "福岡県", "行橋市", "x")
    assert p["providerId"] == "1_11"


def test_row_without_service_code_and_unknown_type_gets_00(sync):
    p = sync._row_to_provider({"事業所番号": "1", "サービス種類": "未知"})
    assert p["providerId"] == "1_00"


def _existing(pid, city):
    return {"providerId": pid, "name": pid, "serviceType": "居宅介護", "city": city}


def test_detect_changes_splits_closed_out_of_area_unknown(sync):
    new = [
        sync._row_to_provider({**WAMNET_ROW, "事業所番号": "A", "事業所住所（市区町村）": "福岡県北九州市小倉北区"}),
        sync._row_to_provider({**WAMNET_ROW, "事業所番号": "B", "事業所住所（市区町村）": "福岡県遠賀郡芦屋町"}),
    ]
    existing = {
        "A_15": _existing("A_15", "北九州市小倉北区"),       # 続いている
        "C_11": _existing("C_11", "福岡県北九州市八幡西区"),  # 対象地域から消えた → 廃止
        "D_11": _existing("D_11", "北九州市"),               # 区を省いた書き方 → 廃止
        "E_11": _existing("E_11", "芦屋町"),                 # 郡を省いた書き方 → 廃止
        "F_11": _existing("F_11", "久留米市"),               # 近郊外
        "G_11": _existing("G_11", "福岡県八女市"),           # 近郊外
        "H_11": _existing("H_11", ""),                       # 判定不能
    }
    to_add, to_update, closed, out = sync.detect_changes(new, existing)
    assert [p["providerId"] for p in to_add] == ["B_15"]
    assert closed == ["C_11", "D_11", "E_11"]
    assert out == ["F_11", "G_11"]
    assert sync.stats["unknown_area"] == 1


def test_report_has_counts_not_client_names(sync):
    sync.changes["affected_clients"] = {"closed": 2, "out_of_area": 3}
    report = sync.generate_report()
    assert "廃止の事業所を利用中: 2人" in report
    assert "近郊外の事業所を利用中: 3人" in report
    assert "clientName" not in report


def test_dry_run_writes_nothing(sync):
    sync.driver = object()  # 使われたら AttributeError になる
    sync.sync_to_neo4j([{"providerId": "x"}], [], ["y"], ["z"])


def test_area_names_loaded_from_downloader(sync):
    assert "北九州市八幡西区" in sync.area_names
    assert "遠賀郡芦屋町" in sync.area_names
    assert "久留米市" not in sync.area_names


def test_detect_changes_without_area_table_uses_data_only(sync):
    sync.area_names = set()
    new = [sync._row_to_provider({**WAMNET_ROW, "事業所番号": "A"})]
    _, _, closed, out = sync.detect_changes(new, {"C_11": _existing("C_11", "北九州市八幡西区")})
    assert (closed, out) == ([], ["C_11"])  # 表が無いと、データに出ない地域は近郊外に見える


# ---- 旧来の ID のノードとの突き合わせ（2026-10-30 の既存 4213 件の内訳に合わせた）----


def _row(number, service_code="11", service="居宅介護", city="福岡県北九州市小倉北区"):
    return {**WAMNET_ROW, "事業所番号": number, "サービス種類コード": service_code, "サービス種類": service,
            "事業所住所（市区町村）": city}


def test_legacy_nodes_are_adopted_not_duplicated(sync):
    new = [sync._row_to_provider(_row(n)) for n in ("1000000001", "1000000002", "1000000003", "1000000004")]
    existing = {
        "e1": {"providerId": "1000000001", "serviceType": "居宅介護", "city": "北九州市小倉北区"},  # 事業所番号だけ・wamnetId なし
        "e2": {"wamnetId": "1000000002", "serviceType": "居宅介護", "city": "北九州市小倉北区",      # providerId なし
               "availability": "空きあり"},
        "e3": {"providerId": "1000000003_00", "wamnetId": "1000000003", "serviceType": "居宅介護"},  # 旧スクリプトのコード
        "e4": {"providerId": "1000000004_11", "wamnetId": "1000000004", "serviceType": "居宅介護",
               "name": "テスト事業所", "address": "1-2-3", "city": "北九州市小倉北区", "phone": "093-000-0000",
               "capacity": 20},
    }
    to_add, to_update, closed, out = sync.detect_changes(new, existing)
    assert to_add == []
    assert sorted(u["key"] for u in to_update) == ["e1", "e2", "e3"]
    assert sync.stats["adopted"] == 3 and sync.stats["unchanged"] == 1
    props = {u["key"]: u["props"] for u in to_update}
    assert props["e1"]["providerId"] == "1000000001_11"
    assert "availability" not in props["e2"]  # 人が記録した空き状況を上書きしない
    assert (closed, out) == ([], [])


def test_service_type_spelling_differences_still_match(sync):
    new = [sync._row_to_provider(_row("1000000001", "41", "自立訓練_機能訓練"))]
    existing = {"e1": {"wamnetId": "1000000001", "serviceType": "自立訓練（機能訓練）"}}
    _, to_update, _, _ = sync.detect_changes(new, existing)
    assert [u["key"] for u in to_update] == ["e1"]


def test_duplicates_and_service_mismatch_are_held(sync):
    new = [sync._row_to_provider(_row("1000000001")), sync._row_to_provider(_row("1000000002"))]
    existing = {
        "d1": {"wamnetId": "1000000001", "serviceType": "居宅介護", "city": "北九州市"},
        "d2": {"providerId": "1000000001", "serviceType": "居宅介護", "city": "福岡県北九州市小倉北区"},
        "m1": {"wamnetId": "1000000002", "serviceType": "生活介護", "city": "北九州市小倉北区"},
    }
    to_add, to_update, closed, out = sync.detect_changes(new, existing)
    assert (to_add, to_update, closed, out) == ([], [], [], [])  # 作らない・触れない
    assert sync.stats["hold_duplicate"] == 1
    assert sync.stats["hold_service_mismatch"] == 1


def test_nodes_without_any_number_are_left_alone(sync):
    new = [sync._row_to_provider(_row("1000000001"))]
    existing = {"x": {"name": "手で登録した事業所", "city": "北九州市小倉北区"}}
    _, _, closed, out = sync.detect_changes(new, existing)
    assert (closed, out) == ([], [])
    assert sync.stats["no_number"] == 1


def test_legacy_out_of_area_nodes_are_marked(sync):
    new = [sync._row_to_provider(_row("1000000001"))]
    existing = {"k": {"wamnetId": "2000000001", "serviceType": "居宅介護", "city": "福岡県久留米市"}}
    _, _, closed, out = sync.detect_changes(new, existing)
    assert (closed, out) == ([], ["k"])


def test_csv_duplicate_rows_use_first_only(sync):
    row = sync._row_to_provider(_row("1000000001"))
    to_add, _, _, _ = sync.detect_changes([row, dict(row)], {})
    assert len(to_add) == 1 and sync.stats["csv_duplicate"] == 1


def test_duplicate_twin_of_matched_node_is_held_not_closed(sync):
    """providerId が一致した相手とは別に、同じ事業所番号・サービス種類のノードがあれば、廃止にせず保留にする
    （2026-10-30 の2回目の dry-run で、廃止 987 件のうち 765 件がこれだった）。"""
    new = [sync._row_to_provider(_row("1000000001")), sync._row_to_provider(_row("1000000002"))]
    existing = {
        "a": {"providerId": "1000000001_11", "wamnetId": "1000000001", "serviceType": "居宅介護",
              "city": "北九州市小倉北区"},
        "a_twin": {"wamnetId": "1000000001", "serviceType": "居宅介護", "city": "北九州市"},   # 片割れ
        "b": {"providerId": "1000000002", "serviceType": "居宅介護", "city": "北九州市小倉北区"},
        "b_twin": {"providerId": "1000000002_00", "wamnetId": "1000000002", "serviceType": "居宅介護",
                   "city": "北九州市小倉北区"},  # b と2つで候補になる → 重複の候補（行ごと保留）
        "gone": {"wamnetId": "1000000009", "serviceType": "居宅介護", "city": "北九州市小倉北区"},  # 本当に廃止
        "other_service": {"wamnetId": "1000000001", "serviceType": "生活介護",
                          "city": "北九州市小倉北区"},                                           # そのサービスは廃止
    }
    _, to_update, closed, out = sync.detect_changes(new, existing)
    assert sync.stats["hold_duplicate_nodes"] == 1  # a_twin
    assert sync.stats["hold_duplicate"] == 1        # b の行（b と b_twin）
    assert sorted(closed) == ["gone", "other_service"]
    assert out == []
    assert "a_twin" not in [u["key"] for u in to_update] and "b_twin" not in [u["key"] for u in to_update]


def test_legacy_office_number_nodes_are_judged(sync):
    """office_number と service_type しか持たない旧来ノードも、事業所番号で突き合わせ、残れば廃止・近郊外の判定を受ける。"""
    new = [sync._row_to_provider(_row("1000000001"))]
    existing = {
        "legacy": {"office_number": "1000000001", "office_name": "旧", "service_type": "居宅介護",
                   "city": "北九州市小倉北区"},
        "gone": {"office_number": "1000000009", "service_type": "居宅介護", "city": "北九州市小倉北区"},
    }
    _, to_update, closed, out = sync.detect_changes(new, existing)
    assert [u["key"] for u in to_update] == ["legacy"]  # ID の付け替え
    assert closed == ["gone"]
    assert sync.stats["no_number"] == 0
