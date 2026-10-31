#!/usr/bin/env python3
"""narrative-intake スキルの日本語最適化ルールを検証するスクリプト

検証項目:
  1. JSON 構文: 3 ファイルすべてが json.load() で読み込めること
  2. 必須キー: 各ファイルのトップレベル必須キーが揃っていること
  3. 正規表現: lifeStageHeadings と era_conversion.parsingRules.regex が
               re.compile() 可能であること
  4. 元号計算: era_conversion.json の examples が baseYear + N年 と一致すること
  5. 辞書整合性: kinshipTerms.*.canonical が variants に含まれていること
  6. NFC 正規化: 各 JSON ファイルの内容が NFC 正規化済みであること

使用例:
  uv run python claude-skills/narrative-intake/scripts/validate_ja_rules.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMA_DIR = SKILL_DIR / "schema"

errors: list[str] = []
checks_passed = 0


def check(condition: bool, name: str, detail: str = "") -> None:
    """検証項目を1件記録する。"""
    global checks_passed
    if condition:
        checks_passed += 1
    else:
        errors.append(f"{name} - {detail}")


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_ja_text_rules() -> None:
    """ja_text_rules.json の必須キーと正規表現を検証する。"""
    path = SCHEMA_DIR / "ja_text_rules.json"
    try:
        data = _load_json(path)
        check(True, "ja_text_rules.json parse")
    except json.JSONDecodeError as e:
        check(False, "ja_text_rules.json parse", str(e))
        return

    required_keys = [
        "version",
        "updatedAt",
        "sentenceEndMarkers",
        "quotationPairs",
        "forbiddenSplitContexts",
        "normalization",
        "chunkingHints",
        "lifeStageHeadings",
    ]
    for key in required_keys:
        check(key in data, f"ja_text_rules.{key}", "必須キーが存在しません")

    # lifeStageHeadings の正規表現コンパイル確認
    patterns = data.get("lifeStageHeadings", {}).get("regexPatterns", [])
    check(
        len(patterns) > 0,
        "ja_text_rules.lifeStageHeadings.regexPatterns",
        "正規表現パターンが空です",
    )
    for pattern in patterns:
        try:
            re.compile(pattern)
            check(True, f"regex compile: {pattern[:30]}")
        except re.error as e:
            check(False, f"regex compile: {pattern[:30]}", str(e))


def validate_era_conversion() -> None:
    """era_conversion.json の必須元号・正規表現・例の計算一致を検証する。"""
    path = SCHEMA_DIR / "era_conversion.json"
    try:
        data = _load_json(path)
        check(True, "era_conversion.json parse")
    except json.JSONDecodeError as e:
        check(False, "era_conversion.json parse", str(e))
        return

    check("eras" in data, "era_conversion.eras", "必須キーが存在しません")
    check("parsingRules" in data, "era_conversion.parsingRules", "必須キーが存在しません")
    check("examples" in data, "era_conversion.examples", "必須キーが存在しません")

    era_names = {e["name"] for e in data.get("eras", [])}
    for required in ["明治", "大正", "昭和", "平成", "令和"]:
        check(
            required in era_names,
            f"era_conversion.{required}",
            "元号が欠けています",
        )

    # parsingRules.regex コンパイル確認
    parsing_regex = data.get("parsingRules", {}).get("regex", "")
    try:
        re.compile(parsing_regex)
        check(True, "era_conversion.parsingRules.regex compile")
    except re.error as e:
        check(False, "era_conversion.parsingRules.regex compile", str(e))

    # examples の計算検証（全角数字も吸収する）
    base_years = {e["name"]: e["baseYear"] for e in data.get("eras", [])}
    full_to_half = str.maketrans("０１２３四五六七八九", "0123456789")
    era_regex = re.compile(
        r"(明治|大正|昭和|平成|令和|[MTSHR])\s*([元0-9０-９]+)"
    )
    alt_to_name = {
        "M": "明治",
        "T": "大正",
        "S": "昭和",
        "H": "平成",
        "R": "令和",
    }
    for ex in data.get("examples", []):
        inp = ex["input"]
        out = ex["output"]
        m = era_regex.search(inp)
        if not m:
            check(False, f"era_example regex: {inp}", "元号パターンが見つかりません")
            continue
        era_name_raw = m.group(1)
        era_name = alt_to_name.get(era_name_raw, era_name_raw)
        year_str = m.group(2).replace("元", "1")
        # 全角数字→半角
        year_str = year_str.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        try:
            n = int(year_str)
        except ValueError:
            check(False, f"era_example number: {inp}", f"数値変換失敗: {year_str}")
            continue
        expected_year = base_years[era_name] + n
        check(
            str(expected_year) in out,
            f"era_example: {inp}",
            f"期待年 {expected_year} が出力 '{out}' に含まれません",
        )


def validate_honorific_dict() -> None:
    """honorific_dict.json の kinshipTerms の canonical/variants 整合性を検証する。"""
    path = SCHEMA_DIR / "honorific_dict.json"
    try:
        data = _load_json(path)
        check(True, "honorific_dict.json parse")
    except json.JSONDecodeError as e:
        check(False, "honorific_dict.json parse", str(e))
        return

    required_keys = [
        "version",
        "updatedAt",
        "suffixHonorifics",
        "kinshipTerms",
        "professionalTitles",
        "normalizationRule",
    ]
    for key in required_keys:
        check(key in data, f"honorific_dict.{key}", "必須キーが存在しません")

    kinship = data.get("kinshipTerms", {})
    # _comment を除外して10種類以上の親族関係を確認
    kinship_entries = {k: v for k, v in kinship.items() if not k.startswith("_")}
    check(
        len(kinship_entries) >= 10,
        "honorific_dict.kinshipTerms.count",
        f"親族関係が10種未満です: {len(kinship_entries)}",
    )

    for key, term in kinship_entries.items():
        if not isinstance(term, dict):
            continue
        canonical = term.get("canonical", "")
        variants = term.get("variants", [])
        check(
            canonical in variants,
            f"honorific.{key}.canonical",
            f"canonical '{canonical}' が variants に含まれていません",
        )


def validate_nfc() -> None:
    """schema/ 配下の JSON ファイル全体が NFC 正規化済みであることを確認する。"""
    for json_file in sorted(SCHEMA_DIR.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            raw = f.read()
        normalized = unicodedata.normalize("NFC", raw)
        check(
            raw == normalized,
            f"nfc: {json_file.name}",
            "NFC 正規化されていない文字が含まれます",
        )


def main() -> int:
    validate_ja_text_rules()
    validate_era_conversion()
    validate_honorific_dict()
    validate_nfc()

    if errors:
        print(f"✗ FAIL: {len(errors)} errors ({checks_passed} checks passed)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"✓ All validations passed ({checks_passed} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
