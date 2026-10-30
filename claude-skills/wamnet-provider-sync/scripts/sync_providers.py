#!/usr/bin/env python3
"""
WAM NET事業所データ同期スクリプト

WAM NETからダウンロードした障害福祉サービス事業所CSVデータを
Neo4jのServiceProviderノードに同期します。

使用方法:
    python sync_providers.py --mode full --csv-file /path/to/data.csv
    python sync_providers.py --mode diff --csv-file /path/to/data.csv --dry-run
"""

import argparse
import ast
import csv
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Neo4j接続用
try:
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("必要なパッケージをインストールしてください: pip install neo4j python-dotenv")
    sys.exit(1)


# 対象地域の表（KITAKYUSHU_AREAS）を持つダウンローダー。skill がシンボリックリンクで置かれていても、実体のリポジトリから探す
DOWNLOADER_PATH = Path(__file__).resolve().parents[3] / "WAM-NET" / "wamnet_downloader.py"


def load_area_names(path: Path = DOWNLOADER_PATH) -> set:
    """wamnet_downloader.py の KITAKYUSHU_AREAS の市区町村名（「遠賀郡芦屋町」など）。見つからなければ空。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except OSError:
        return set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "KITAKYUSHU_AREAS" for t in node.targets
        ):
            return set(ast.literal_eval(node.value).values())
    return set()


class WAMNetSyncError(Exception):
    """WAM NET同期エラー"""
    pass


class ServiceProviderSync:
    """事業所データ同期クラス"""

    def __init__(self, dry_run: bool = False):
        """
        初期化
        
        Args:
            dry_run: Trueの場合、実際のDB更新を行わない
        """
        self.dry_run = dry_run
        self.driver = None
        self.config_dir = Path(__file__).parent.parent / "config"
        self.service_types = self._load_service_types()
        self.prefectures = self._load_prefectures()
        self.area_names = load_area_names()
        
        # 統計情報
        self.stats = {
            "new": 0,
            "modified": 0,
            "adopted": 0,
            "closed": 0,
            "out_of_area": 0,
            "unknown_area": 0,
            "no_number": 0,
            "csv_duplicate": 0,
            "hold_duplicate": 0,
            "hold_duplicate_nodes": 0,
            "hold_service_mismatch": 0,
            "unchanged": 0,
            "errors": 0
        }
        
        # 変更詳細
        self.changes = {
            "new": [],
            "modified": [],
            "closed": [],
            "out_of_area": [],
            # 利用者の氏名は持たない。廃止・近郊外の事業所に USES_SERVICE でつながる利用者の人数だけ
            "affected_clients": {"closed": 0, "out_of_area": 0},
        }

    def _load_service_types(self) -> Dict:
        """サービス種類マッピングを読み込み"""
        config_path = self.config_dir / "service_types.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"service_types": {}}

    def _load_prefectures(self) -> Dict:
        """都道府県コードを読み込み"""
        config_path = self.config_dir / "prefectures.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"prefectures": {}}

    def connect(self):
        """Neo4jに接続"""
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")
        
        if not password:
            raise WAMNetSyncError("NEO4J_PASSWORD環境変数が設定されていません")
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        # 接続テスト
        with self.driver.session() as session:
            session.run("RETURN 1")
        print(f"✅ Neo4jに接続しました: {uri}")

    def close(self):
        """接続を閉じる"""
        if self.driver:
            self.driver.close()

    def normalize_service_type(self, raw_type: str) -> str:
        """サービス種類を正規化"""
        raw_type = raw_type.strip()
        service_info = self.service_types.get("service_types", {}).get(raw_type)
        if service_info:
            return service_info.get("normalized", raw_type)
        return raw_type

    def normalize_phone(self, phone: str) -> str:
        """電話番号を正規化（ハイフン形式）"""
        if not phone:
            return ""
        # 全角→半角
        phone = phone.translate(str.maketrans("０１２３４５６７８９－", "0123456789-"))
        # 数字とハイフン以外を除去
        phone = "".join(c for c in phone if c.isdigit() or c == "-")
        return phone

    def parse_csv(self, csv_path: str, encoding: str = "cp932") -> List[Dict]:
        """
        CSVファイルを解析してServiceProviderデータに変換
        
        Args:
            csv_path: CSVファイルパス
            encoding: 文字エンコーディング（デフォルト: Shift-JIS/CP932）
        
        Returns:
            ServiceProviderデータのリスト
        """
        providers = []
        
        # エンコーディングを自動検出（cp932 → utf-8 の順で試行）
        for enc in [encoding, "utf-8", "utf-8-sig"]:
            try:
                with open(csv_path, "r", encoding=enc) as f:
                    # ヘッダー行を確認
                    first_line = f.readline()
                    f.seek(0)
                    
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        provider = self._row_to_provider(row)
                        if provider:
                            providers.append(provider)
                    
                    print(f"✅ CSVを読み込みました: {len(providers)}件 (encoding: {enc})")
                    return providers
                    
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise WAMNetSyncError(f"CSV読み込みエラー: {e}")
        
        raise WAMNetSyncError(f"CSVの文字エンコーディングを判定できません: {csv_path}")

    @staticmethod
    def _get(row: Dict, *keys: str) -> str:
        """最初に見つかった列の値。WAM NET の CSV の列名を先に、旧来の列名を後に並べる。"""
        for key in keys:
            value = row.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    def split_prefecture(self, address_city: str) -> Tuple[str, str]:
        """「福岡県北九州市小倉南区」→（福岡県, 北九州市小倉南区）。都道府県名が無ければ（"", そのまま）。"""
        for name in self.prefectures.get("prefectures", {}).values():
            if address_city.startswith(name):
                return name, address_city[len(name):]
        return "", address_city

    def _row_to_provider(self, row: Dict) -> Optional[Dict]:
        """CSV行をServiceProviderデータに変換

        WAM NET のオープンデータ（wamnet_downloader.py の出力）の列名を読む。
        「事業所住所（市区町村）」は「福岡県北九州市小倉南区」のように都道府県名から始まるので、
        prefecture と city に分ける。旧来の列名（事業所名・市区町村・住所 など）も読める。
        """
        try:
            # 事業所番号（必須）
            provider_id = self._get(row, "事業所番号", "jigyosho_no")
            if not provider_id:
                return None

            # サービス種類
            service_type_raw = self._get(row, "サービス種類", "service_type")
            service_type = self.normalize_service_type(service_type_raw)

            # 一意識別子（事業所番号_サービス種類コード）。コードは CSV の列を優先する。
            # 設定ファイルの名前と一致しないと "00" になり、同じ事業所の別サービスが同じ ID になるため。
            service_code = self._get(row, "サービス種類コード") or self.service_types.get(
                "service_types", {}
            ).get(service_type_raw, {}).get("code", "00")
            unique_id = f"{provider_id}_{service_code}"

            prefecture = self._get(row, "都道府県", "prefecture")
            city = self._get(row, "事業所住所（市区町村）", "市区町村", "city")
            pref_in_city, city = self.split_prefecture(city)
            prefecture = prefecture or pref_in_city

            return {
                "providerId": unique_id,
                "wamnetId": provider_id,
                "name": self._get(row, "事業所の名称", "事業所名", "jigyosho_name"),
                "serviceType": service_type,
                "postalCode": self._get(row, "郵便番号", "zip_code"),
                "prefecture": prefecture,
                "city": city,
                "address": self._get(row, "事業所住所（番地以降）", "住所", "address"),
                "phone": self.normalize_phone(self._get(row, "事業所電話番号", "電話番号", "tel")),
                "fax": self.normalize_phone(self._get(row, "事業所FAX番号", "FAX番号", "fax")),
                "capacity": self._parse_int(self._get(row, "定員", "capacity")),
                "corporateName": self._get(row, "法人の名称", "法人名", "corporate_name"),
                "designationDate": self._get(row, "指定年月日", "designation_date"),
                "availability": "未確認",
                "updatedAt": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"⚠️ 行変換エラー: {e}")
            return None

    def _parse_int(self, value: str) -> Optional[int]:
        """文字列を整数に変換（エラー時はNone）"""
        if not value:
            return None
        try:
            # 全角数字→半角
            value = value.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
            return int(value)
        except ValueError:
            return None

    def get_existing_providers(self, prefecture: str = "") -> Dict[str, Dict]:
        """
        既存のServiceProviderを取得
        
        Args:
            prefecture: 都道府県でフィルタ（空の場合は全件）
        
        Returns:
            ノードの elementId → プロパティのDict。providerId の無いノードも含める
            （旧来の取り込みで providerId が無く wamnetId だけのノードがあるため）
        """
        where = "WHERE sp.prefecture CONTAINS $prefecture" if prefecture else ""
        query = f"""
        MATCH (sp:ServiceProvider)
        {where}
        RETURN elementId(sp) AS eid, properties(sp) AS props
        """
        with self.driver.session() as session:
            result = session.run(query, prefecture=prefecture)
            return {record["eid"]: dict(record["props"]) for record in result}

    @staticmethod
    def legacy_number(node: Dict) -> str:
        """既存ノードの事業所番号。wamnetId を優先し、無ければ「事業所番号だけ」の形の providerId を使う。"""
        wamnet_id = str(node.get("wamnetId") or "").strip()
        if wamnet_id:
            return wamnet_id
        provider_id = str(node.get("providerId") or "").strip()
        return provider_id if re.fullmatch(r"\d{10}", provider_id) else ""

    def service_key(self, service_type: str) -> str:
        """サービス種類の比較用の形。全角半角・記号の違い（自立訓練_機能訓練 / 自立訓練（機能訓練））を吸収する。"""
        name = unicodedata.normalize("NFKC", self.normalize_service_type(str(service_type or "")))
        return re.sub(r"[\s_()（）・]", "", name)

    def detect_changes(
        self, 
        new_providers: List[Dict], 
        existing_providers: Dict[str, Dict]
    ) -> Tuple[List[Dict], List[Dict], List[str], List[str]]:
        """
        差分を検出
        
        Args:
            new_providers: 新しいデータ
            existing_providers: 既存データ（ノードのキー → プロパティ）
        
        Returns:
            (追加リスト, 更新リスト[{"key", "props"}], 廃止キーリスト, 近郊外キーリスト)

        既存ノードとの突き合わせは次の順に行う。
        1. providerId（事業所番号_サービス種類コード）が一致
        2. 事業所番号（wamnetId、または「事業所番号だけ」の providerId）とサービス種類が一致するノードが1つ
           → そのノードの providerId を新しい形に付け替える（ID の付け替え）
           2つ以上 → 重複の候補。新しい行は作らず、ノードにも触れない（保留）
        3. 事業所番号は一致するがサービス種類が一致しない → 保留（作らない・触れない）
        4. どれにも当たらない → 新規
        1〜3 の後に残ったノードのうち、事業所番号とサービス種類が CSV のどれかの行と同じものは、
        営業中の事業所の重複ノード（片割れ）として保留にし、廃止にしない。

        どの行にも当たらなかった既存ノードは、次に分ける。
        - 事業所番号が無い: 何もしない（手で登録したノードの可能性がある）
        - 廃止: 市区町村が対象地域に入る（その地域から消えた）
        - 近郊外: 市区町村が対象地域に入らない（旧版のダウンローダーが拾った近郊外の事業所など）
        - 判定不能: 市区町村が空。何もせず件数だけ数える
        対象地域は、新しいデータに出てくる市区町村と、wamnet_downloader.py の KITAKYUSHU_AREAS の市区町村を合わせたもの。
        """
        to_add = []
        to_update = []
        claimed = set()

        by_pid = {}
        by_number_service = defaultdict(list)
        by_number = defaultdict(list)
        for key, node in existing_providers.items():
            pid = str(node.get("providerId") or "").strip()
            if pid:
                by_pid.setdefault(pid, key)
            number = self.legacy_number(node)
            if number:
                by_number_service[(number, self.service_key(node.get("serviceType")))].append(key)
                by_number[number].append(key)

        def update(provider, key, adopted):
            claimed.add(key)
            existing = existing_providers[key]
            if adopted or self._is_modified(provider, existing):
                # availability（空き状況）は人が記録する値なので、既存ノードでは上書きしない
                props = {k: v for k, v in provider.items() if k != "availability"}
                to_update.append({"key": key, "props": props})
                self.stats["adopted" if adopted else "modified"] += 1
                if not adopted:
                    self.changes["modified"].append({
                        "name": provider["name"],
                        "serviceType": provider["serviceType"],
                        "changes": self._get_diff(provider, existing)
                    })
            else:
                self.stats["unchanged"] += 1

        # CSV の中で providerId が重なる行は最初の1行だけ使う（ID の付け替えで同じ providerId を2つ作らないため）
        unique = {}
        for provider in new_providers:
            unique.setdefault(provider["providerId"], provider)
        self.stats["csv_duplicate"] = len(new_providers) - len(unique)

        # 1. providerId が一致
        rest = []
        for provider in unique.values():
            key = by_pid.get(provider["providerId"])
            if key is not None and key not in claimed:
                update(provider, key, adopted=False)
            else:
                rest.append(provider)

        # 2. 事業所番号＋サービス種類が一致
        rest2 = []
        for provider in rest:
            candidates = [
                k for k in by_number_service[(provider["wamnetId"], self.service_key(provider["serviceType"]))]
                if k not in claimed
            ]
            if len(candidates) == 1:
                update(provider, candidates[0], adopted=True)
            elif len(candidates) > 1:
                claimed.update(candidates)
                self.stats["hold_duplicate"] += 1
            else:
                rest2.append(provider)

        # 3. 事業所番号だけ一致 → 保留、4. 新規
        for provider in rest2:
            others = [k for k in by_number[provider["wamnetId"]] if k not in claimed]
            if others:
                claimed.update(others)
                self.stats["hold_service_mismatch"] += 1
                continue
            to_add.append(provider)
            self.stats["new"] += 1
            self.changes["new"].append({
                "name": provider["name"],
                "serviceType": provider["serviceType"],
                "city": provider["city"]
            })

        # 重複の片割れ: 残ったノードのうち、事業所番号とサービス種類が CSV のどれかの行と同じものは、
        # 営業中の事業所の重複ノードなので、廃止に回さず保留にする（後で別途まとめる）
        csv_keys = {(p["wamnetId"], self.service_key(p["serviceType"])) for p in unique.values()}
        for key in set(existing_providers.keys()) - claimed:
            node = existing_providers[key]
            if (self.legacy_number(node), self.service_key(node.get("serviceType"))) in csv_keys:
                claimed.add(key)
                self.stats["hold_duplicate_nodes"] += 1

        # 廃止・近郊外の検出
        area_cities = {p["city"] for p in new_providers if p.get("city")} | self.area_names
        closed_ids = []
        out_of_area_ids = []
        for key in sorted(set(existing_providers.keys()) - claimed):
            existing = existing_providers[key]
            if not self.legacy_number(existing) and not existing.get("providerId"):
                self.stats["no_number"] += 1
                continue
            _, city = self.split_prefecture(str(existing.get("city") or "").strip())
            entry = {
                "providerId": existing.get("providerId", ""),
                "name": existing.get("name", ""),
                "serviceType": existing.get("serviceType", ""),
                "city": city,
            }
            if not city:
                self.stats["unknown_area"] += 1
            elif self.in_area(city, area_cities):
                closed_ids.append(key)
                self.changes["closed"].append(entry)
            else:
                out_of_area_ids.append(key)
                self.changes["out_of_area"].append(entry)
        self.stats["closed"] = len(closed_ids)
        self.stats["out_of_area"] = len(out_of_area_ids)

        return to_add, to_update, closed_ids, out_of_area_ids

    @staticmethod
    def in_area(city: str, area_cities: set) -> bool:
        """city が対象地域に入るか。区を省いた「北九州市」は前方一致で、郡や市を省いた「芦屋町」「小倉北区」は
        末尾一致で認める。"""
        return city in area_cities or any(c.startswith(city) or c.endswith(city) for c in area_cities)

    def _is_modified(self, new: Dict, existing: Dict) -> bool:
        """変更があるか判定"""
        compare_fields = ["name", "address", "city", "phone", "capacity", "serviceType"]
        for field in compare_fields:
            if str(new.get(field, "")) != str(existing.get(field, "")):
                return True
        return False

    def _get_diff(self, new: Dict, existing: Dict) -> List[str]:
        """変更点を取得"""
        diffs = []
        compare_fields = ["name", "address", "city", "phone", "capacity", "serviceType"]
        for field in compare_fields:
            new_val = str(new.get(field, ""))
            old_val = str(existing.get(field, ""))
            if new_val != old_val:
                diffs.append(f"{field}: {old_val} → {new_val}")
        return diffs

    def check_affected_clients(self, closed_ids: List[str], out_of_area_ids: List[str]):
        """廃止・近郊外の事業所を利用中のクライアントの人数を数える（氏名は読まない）"""
        query = """
        MATCH (c:Client)-[r:USES_SERVICE]->(sp:ServiceProvider)
        WHERE elementId(sp) IN $ids
          AND r.status = 'Active'
        RETURN count(DISTINCT c) AS n
        """
        with self.driver.session() as session:
            for key, ids in (("closed", closed_ids), ("out_of_area", out_of_area_ids)):
                if ids:
                    self.changes["affected_clients"][key] = session.run(query, ids=ids).single()["n"]

    def sync_to_neo4j(
        self, 
        to_add: List[Dict], 
        to_update: List[Dict], 
        closed_ids: List[str],
        out_of_area_ids: List[str] = (),
        batch_size: int = 100
    ):
        """
        Neo4jにデータを同期
        
        Args:
            to_add: 追加するデータ
            to_update: 更新するデータ
            closed_ids: 廃止としてマークするノードのキー（elementId）
            out_of_area_ids: 近郊外としてマークするノードのキー（elementId。status は変えない）
            batch_size: バッチサイズ
        """
        if self.dry_run:
            print("🔍 ドライランモード: 実際のDB更新は行いません")
            return
        
        with self.driver.session() as session:
            # 新規追加
            for i in range(0, len(to_add), batch_size):
                batch = to_add[i:i + batch_size]
                self._batch_create(session, batch)
                print(f"  追加: {i + len(batch)}/{len(to_add)}")
            
            # 更新
            for i in range(0, len(to_update), batch_size):
                batch = to_update[i:i + batch_size]
                self._batch_update(session, batch)
                print(f"  更新: {i + len(batch)}/{len(to_update)}")
            
            # 廃止マーク
            if closed_ids:
                self._mark_closed(session, closed_ids)
                print(f"  廃止マーク: {len(closed_ids)}件")

            # 近郊外マーク
            if out_of_area_ids:
                self._mark_out_of_area(session, list(out_of_area_ids))
                print(f"  近郊外マーク: {len(out_of_area_ids)}件")

    def _batch_create(self, session, providers: List[Dict]):
        """バッチで新規作成"""
        query = """
        UNWIND $providers AS p
        MERGE (sp:ServiceProvider {providerId: p.providerId})
        SET sp += p
        """
        session.run(query, providers=providers)

    def _batch_update(self, session, providers: List[Dict]):
        """バッチで更新"""
        query = """
        UNWIND $providers AS row
        MATCH (sp:ServiceProvider) WHERE elementId(sp) = row.key
        SET sp += row.props
        REMOVE sp.outOfArea, sp.outOfAreaAt
        """
        session.run(query, providers=providers)

    def _mark_closed(self, session, closed_ids: List[str]):
        """廃止としてマーク"""
        query = """
        MATCH (sp:ServiceProvider)
        WHERE elementId(sp) IN $closed_ids
        SET sp.status = 'Closed',
            sp.closedAt = datetime()
        """
        session.run(query, closed_ids=closed_ids)

    def _mark_out_of_area(self, session, ids: List[str]):
        """近郊外としてマーク。消さずに残し、利用者とのつながりも保つ。"""
        query = """
        MATCH (sp:ServiceProvider)
        WHERE elementId(sp) IN $ids
        SET sp.outOfArea = true,
            sp.outOfAreaAt = datetime()
        """
        session.run(query, ids=ids)

    def generate_report(self) -> str:
        """更新レポートを生成"""
        report = []
        report.append("# WAM NET事業所データ更新レポート\n")
        report.append(f"## 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if self.dry_run:
            report.append("**⚠️ ドライランモード（実際の更新は行っていません）**\n")
        
        report.append("## 更新結果サマリー\n")
        report.append("| カテゴリ | 件数 |")
        report.append("|---------|------|")
        report.append(f"| 🆕 新規登録 | {self.stats['new']}件 |")
        report.append(f"| 📝 更新 | {self.stats['modified']}件 |")
        report.append(f"| 🔁 ID の付け替え（旧来の ID → 事業所番号_サービス種類コード） | {self.stats['adopted']}件 |")
        report.append(f"| ⏸️ 保留: 同じ事業所番号・サービス種類のノードが複数（重複の候補） | {self.stats['hold_duplicate']}件 |")
        report.append(f"| ⏸️ 保留: 更新・付け替えの相手と同じ事業所番号・サービス種類の別ノード（重複の片割れ） | {self.stats['hold_duplicate_nodes']}件 |")
        report.append(f"| ⏸️ 保留: 事業所番号は一致、サービス種類が不一致 | {self.stats['hold_service_mismatch']}件 |")
        report.append(f"| ⚠️ 廃止 | {self.stats['closed']}件 |")
        report.append(f"| 🗺️ 近郊外（outOfArea を付ける） | {self.stats['out_of_area']}件 |")
        report.append(f"| ❔ 市区町村が空で判定不能（何もしない） | {self.stats['unknown_area']}件 |")
        report.append(f"| ➖ 事業所番号が無いノード（何もしない） | {self.stats['no_number']}件 |")
        report.append(f"| ➖ CSV の中で providerId が重なった行（2行目以降は使わない） | {self.stats['csv_duplicate']}件 |")
        report.append(f"| ✅ 変更なし | {self.stats['unchanged']}件 |")
        report.append("")
        
        # 影響を受けるクライアント（人数だけ）
        affected = self.changes["affected_clients"]
        if affected["closed"] or affected["out_of_area"]:
            report.append("## ⚠️ 要確認: 廃止・近郊外の事業所を利用中のクライアント\n")
            report.append(f"- 廃止の事業所を利用中: {affected['closed']}人")
            report.append(f"- 近郊外の事業所を利用中: {affected['out_of_area']}人")
            report.append("")
            report.append("→ **誰かは Neo4j で確かめ、代替事業所を検討してください**\n")

        # 新規登録（抜粋）
        if self.changes["new"]:
            report.append("## 新規登録事業所（抜粋・最大10件）\n")
            report.append("| 事業所名 | サービス種類 | 市区町村 |")
            report.append("|---------|-------------|---------|")
            for provider in self.changes["new"][:10]:
                report.append(
                    f"| {provider['name']} | {provider['serviceType']} | {provider['city']} |"
                )
            report.append("")
        
        # 廃止事業所
        if self.changes["closed"]:
            report.append("## 廃止事業所\n")
            report.append("| 事業所名 | サービス種類 |")
            report.append("|---------|-------------|")
            for provider in self.changes["closed"]:
                report.append(f"| {provider['name']} | {provider['serviceType']} |")
            report.append("")
        
        return "\n".join(report)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="WAM NET事業所データをNeo4jに同期"
    )
    parser.add_argument(
        "--csv-file", "-f",
        required=True,
        help="WAM NET CSVファイルのパス"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["full", "diff"],
        default="diff",
        help="同期モード: full=全件置換, diff=差分更新（デフォルト）"
    )
    parser.add_argument(
        "--prefecture", "-p",
        default="",
        help="都道府県でフィルタ（例: 福岡県）"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="ドライラン（実際のDB更新を行わない）"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=100,
        help="バッチサイズ（デフォルト: 100）"
    )
    parser.add_argument(
        "--output", "-o",
        help="レポート出力先（指定しない場合は標準出力）"
    )
    
    args = parser.parse_args()
    
    # CSVファイル存在確認
    if not os.path.exists(args.csv_file):
        print(f"❌ CSVファイルが見つかりません: {args.csv_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("WAM NET事業所データ同期")
    print("=" * 60)
    print(f"CSVファイル: {args.csv_file}")
    print(f"同期モード: {args.mode}")
    print(f"ドライラン: {args.dry_run}")
    print("=" * 60)
    
    sync = ServiceProviderSync(dry_run=args.dry_run)
    
    try:
        # Neo4j接続
        sync.connect()
        
        # CSV読み込み
        new_providers = sync.parse_csv(args.csv_file)
        
        # 都道府県フィルタ
        if args.prefecture:
            new_providers = [
                p for p in new_providers 
                if args.prefecture in p.get("prefecture", "")
            ]
            print(f"📍 都道府県フィルタ適用: {len(new_providers)}件")
        
        if args.mode == "diff":
            # 差分検出
            existing = sync.get_existing_providers(args.prefecture)
            print(f"📊 既存データ: {len(existing)}件")
            
            to_add, to_update, closed_ids, out_of_area_ids = sync.detect_changes(new_providers, existing)
            
            # 影響を受けるクライアント確認（人数だけ）
            sync.check_affected_clients(closed_ids, out_of_area_ids)
            
            # 同期実行
            sync.sync_to_neo4j(to_add, to_update, closed_ids, out_of_area_ids, args.batch_size)
            
        else:  # full mode
            print("⚠️ フルモード: 既存データを上書きします")
            # TODO: フルモードの実装
            pass
        
        # レポート生成
        report = sync.generate_report()
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n📄 レポートを保存しました: {args.output}")
        else:
            print("\n" + report)
        
        print("\n✅ 同期完了")
        
    except WAMNetSyncError as e:
        print(f"\n❌ エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sync.close()


if __name__ == "__main__":
    main()
