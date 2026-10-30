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
