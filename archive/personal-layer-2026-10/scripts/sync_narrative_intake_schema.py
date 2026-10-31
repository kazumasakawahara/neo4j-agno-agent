#!/usr/bin/env python3
"""narrative-intake スキルの schema/*.json を Python 側 allowlist と同期するスクリプト。

目的:
    api/app/lib/db_operations.py の ALLOWED_LABELS / ALLOWED_REL_TYPES / MERGE_KEYS と
    claude-skills/narrative-intake/schema/ 配下の JSON ファイルが将来ずれないよう、
    Python を Single Source of Truth として JSON を再生成する。

使い方:
    # ドリフト検出のみ (ファイルは書き換えない)
    uv run python scripts/sync_narrative_intake_schema.py --check

    # ドリフトを修正する (ファイルを上書き)
    uv run python scripts/sync_narrative_intake_schema.py --apply

動作:
    --check モードでは Python 側と skill 側 JSON を比較し、差分があれば exit code 1
    --apply モードでは skill 側 JSON を Python 側に合わせて上書き (バックアップ作成)
"""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートから api/ を import できるようにする
PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_DIR = PROJECT_ROOT / "api"
SKILL_SCHEMA_DIR = PROJECT_ROOT / "claude-skills" / "narrative-intake" / "schema"
DB_OPERATIONS_PY = API_DIR / "app" / "lib" / "db_operations.py"


# ---------------------------------------------------------------------------
# db_operations.py から allowlist を抽出する (2段構え)
#   1. 可能なら import で取得 (Python 依存が満たされている場合)
#   2. 失敗した場合は AST で静的解析 (依存なしで動作)
# ---------------------------------------------------------------------------


def _extract_via_import() -> dict | None:
    """import 経由で allowlist を取得する。失敗時は None を返す。"""
    sys.path.insert(0, str(API_DIR))
    try:
        from app.lib.db_operations import (  # noqa: E402
            ALLOWED_CREATE_LABELS,
            ALLOWED_LABELS,
            ALLOWED_REL_TYPES,
            MERGE_KEYS,
        )
    except ImportError:
        return None
    return {
        "ALLOWED_LABELS": set(ALLOWED_LABELS),
        "ALLOWED_REL_TYPES": set(ALLOWED_REL_TYPES),
        "ALLOWED_CREATE_LABELS": set(ALLOWED_CREATE_LABELS),
        "MERGE_KEYS": {k: list(v) for k, v in MERGE_KEYS.items()},
    }


def _extract_via_ast() -> dict | None:
    """AST で静的解析して allowlist 定義を取得する (外部依存なし)。"""
    if not DB_OPERATIONS_PY.exists():
        return None
    tree = ast.parse(DB_OPERATIONS_PY.read_text(encoding="utf-8"))

    result: dict = {}
    for node in ast.iter_child_nodes(tree):
        # 対象: トップレベルの代入文のみ (例: MERGE_KEYS: dict[...] = {...} / = {...})
        targets: list[str] = []
        value_node = None

        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
            value_node = node.value
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
            value_node = node.value

        if not targets or value_node is None:
            continue

        for name in targets:
            if name == "MERGE_KEYS" and isinstance(value_node, ast.Dict):
                merge: dict[str, list[str]] = {}
                for k, v in zip(value_node.keys, value_node.values):
                    if isinstance(k, ast.Constant) and isinstance(v, (ast.List, ast.Tuple, ast.Set)):
                        merge[k.value] = [
                            e.value for e in v.elts if isinstance(e, ast.Constant)
                        ]
                result["MERGE_KEYS"] = merge
            elif name == "ALLOWED_REL_TYPES" and isinstance(value_node, ast.Set):
                result["ALLOWED_REL_TYPES"] = {
                    e.value for e in value_node.elts if isinstance(e, ast.Constant)
                }
            elif name == "ALLOWED_CREATE_LABELS" and isinstance(value_node, ast.Set):
                result["ALLOWED_CREATE_LABELS"] = {
                    e.value for e in value_node.elts if isinstance(e, ast.Constant)
                }

    # ALLOWED_LABELS は MERGE_KEYS のキー + ALLOWED_CREATE_LABELS の合成
    if "MERGE_KEYS" in result and "ALLOWED_CREATE_LABELS" in result:
        result["ALLOWED_LABELS"] = set(result["MERGE_KEYS"].keys()) | set(
            result["ALLOWED_CREATE_LABELS"]
        )

    required = {"MERGE_KEYS", "ALLOWED_REL_TYPES", "ALLOWED_CREATE_LABELS", "ALLOWED_LABELS"}
    if not required.issubset(result.keys()):
        missing = required - set(result.keys())
        print(f"✗ AST解析で必須定数が見つかりませんでした: {missing}", file=sys.stderr)
        return None

    return result


def extract_python_allowlists() -> dict:
    """Python 側の allowlist を取得する (import → AST の順でフォールバック)。"""
    data = _extract_via_import()
    source = "import"
    if data is None:
        data = _extract_via_ast()
        source = "ast"
    if data is None:
        print("✗ Python側 allowlist の抽出に失敗しました", file=sys.stderr)
        sys.exit(2)
    print(f"  (Python側allowlist抽出方式: {source})")
    return data


_py_data = extract_python_allowlists()
ALLOWED_LABELS: set = _py_data["ALLOWED_LABELS"]
ALLOWED_REL_TYPES: set = _py_data["ALLOWED_REL_TYPES"]
ALLOWED_CREATE_LABELS: set = _py_data["ALLOWED_CREATE_LABELS"]
MERGE_KEYS: dict = _py_data["MERGE_KEYS"]


# ---------------------------------------------------------------------------
# JSON 生成ロジック
# ---------------------------------------------------------------------------


_SOURCE_TAG = "api/app/lib/db_operations.py (mirror via sync_narrative_intake_schema.py)"


def build_allowed_labels_json(existing: dict | None) -> dict:
    """allowed_labels.json の期待値を構築する (既存フォーマット互換)。

    既存のスキーマは以下のキーを持つ:
      _source, _note, merge_labels, create_only_labels, all_allowed
    このスクリプトは既存 _note を温存する。
    """
    # merge_labels と create_only_labels は Python 側の MERGE_KEYS 挿入順 / 定義順を尊重したいが、
    # ASTから取得したMERGE_KEYSは挿入順で来るため dict の順序をそのまま使う
    merge_labels = list(MERGE_KEYS.keys())
    create_only = list(ALLOWED_CREATE_LABELS)
    # create_only は sort すると不安定になるので Python の定義順に従いたいが、
    # AST 経由では set になってしまうためソート
    create_only.sort()
    all_allowed = merge_labels + create_only

    return {
        "_source": _SOURCE_TAG,
        "_note": (existing or {}).get(
            "_note",
            "このファイルはマスターではない。変更はコード側で行い sync スクリプトで反映すること。",
        ),
        "merge_labels": merge_labels,
        "create_only_labels": create_only,
        "all_allowed": all_allowed,
    }


def build_allowed_rels_json(existing: dict | None) -> dict:
    """allowed_rels.json の期待値を構築する (既存フォーマット互換)。

    directions サブフィールドは既存ファイルの手書きメタ情報なので、
    存在すればそのまま温存する (Python 側には存在しない情報)。
    """
    all_allowed = sorted(ALLOWED_REL_TYPES)
    return {
        "_source": _SOURCE_TAG,
        "_note": (existing or {}).get(
            "_note",
            "廃止名 (PROHIBITED, PREFERS, EMERGENCY_CONTACT, RELATES_TO) は絶対に使用しないこと。",
        ),
        "all_allowed": all_allowed,
        "directions": (existing or {}).get("directions", {}),
    }


def build_merge_keys_json(existing: dict | None) -> dict:
    """merge_keys.json の期待値を構築する (既存フォーマット互換)。"""
    return {
        "_source": _SOURCE_TAG,
        "_note": (existing or {}).get(
            "_note",
            "merge_keys に含まれるラベルはノードJSONに必ず mergeKey フィールドを付けること。含まれないラベルは常に CREATE される。",
        ),
        "merge_keys": {k: list(v) for k, v in MERGE_KEYS.items()},
        "create_only": sorted(ALLOWED_CREATE_LABELS),
    }


# ---------------------------------------------------------------------------
# 比較・検出ロジック
# ---------------------------------------------------------------------------


def load_existing_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"✗ {path} の JSON パースに失敗: {exc}", file=sys.stderr)
        return None


def extract_comparable(data: dict | None, kind: str) -> set | dict | None:
    """比較しやすい形に変換する。_source / _note / directions は差分対象外。"""
    if data is None:
        return None

    if kind == "allowed_labels":
        return set(data.get("all_allowed") or [])
    if kind == "allowed_rels":
        return set(data.get("all_allowed") or [])
    if kind == "merge_keys":
        merge = data.get("merge_keys") or {}
        create_only = data.get("create_only") or []
        return {
            "merge_keys": {k: sorted(v) for k, v in merge.items()},
            "create_only": sorted(create_only),
        }
    return None


def compare_and_report(
    kind: str,
    existing: dict | None,
    expected: dict,
) -> bool:
    """差分があれば True を返す (drift あり)。"""
    existing_cmp = extract_comparable(existing, kind)
    expected_cmp = extract_comparable(expected, kind)

    if existing_cmp is None:
        print(f"  {kind}: 新規作成が必要 (ファイル未存在 または 空)")
        return True

    if kind in ("allowed_labels", "allowed_rels"):
        missing = expected_cmp - existing_cmp
        extra = existing_cmp - expected_cmp
        if not missing and not extra:
            print(f"  {kind}: OK (差分なし)")
            return False
        if missing:
            print(f"  {kind}: Python側にあるがJSON側にない: {sorted(missing)}")
        if extra:
            print(f"  {kind}: JSON側にあるがPython側にない: {sorted(extra)}")
        return True

    if kind == "merge_keys":
        if existing_cmp == expected_cmp:
            print(f"  {kind}: OK (差分なし)")
            return False
        py_merge = expected_cmp["merge_keys"]
        js_merge = existing_cmp["merge_keys"]
        missing_labels = set(py_merge.keys()) - set(js_merge.keys())
        extra_labels = set(js_merge.keys()) - set(py_merge.keys())
        if missing_labels:
            print(f"  {kind}: Python側にあるがJSON側にないラベル: {sorted(missing_labels)}")
        if extra_labels:
            print(f"  {kind}: JSON側にあるがPython側にないラベル: {sorted(extra_labels)}")
        for label in set(py_merge.keys()) & set(js_merge.keys()):
            if py_merge[label] != js_merge[label]:
                print(
                    f"  {kind}: {label} のキーが異なる: "
                    f"Python={py_merge[label]} JSON={js_merge[label]}"
                )
        if expected_cmp["create_only"] != existing_cmp["create_only"]:
            print(
                f"  {kind}: create_only が異なる: "
                f"Python={expected_cmp['create_only']} "
                f"JSON={existing_cmp['create_only']}"
            )
        return True

    return False


# ---------------------------------------------------------------------------
# 書き込みロジック
# ---------------------------------------------------------------------------


def write_json_with_backup(path: Path, content: dict) -> None:
    """既存ファイルをバックアップしてから書き込む。"""
    if path.exists():
        backup = path.with_suffix(path.suffix + f".bak-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(path, backup)
        print(f"  バックアップ作成: {backup.name}")
    path.write_text(
        json.dumps(content, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  書き込み: {path.name}")


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="差分検出のみ (ファイルは書き換えない)",
    )
    group.add_argument(
        "--apply",
        action="store_true",
        help="差分があればJSONファイルを上書きする (バックアップ作成)",
    )
    args = parser.parse_args()

    if not SKILL_SCHEMA_DIR.exists():
        print(f"✗ skill スキーマディレクトリが存在しません: {SKILL_SCHEMA_DIR}", file=sys.stderr)
        return 2

    # (kind, path, builder) — builder は existing を受けて期待 JSON を返す
    targets = [
        ("allowed_labels", SKILL_SCHEMA_DIR / "allowed_labels.json", build_allowed_labels_json),
        ("allowed_rels", SKILL_SCHEMA_DIR / "allowed_rels.json", build_allowed_rels_json),
        ("merge_keys", SKILL_SCHEMA_DIR / "merge_keys.json", build_merge_keys_json),
    ]

    mode_label = "CHECK" if args.check else "APPLY"
    print(f"=== narrative-intake schema sync [{mode_label}] ===")
    print(f"Python source : {API_DIR}/app/lib/db_operations.py")
    print(f"Skill target  : {SKILL_SCHEMA_DIR}")
    print()

    any_drift = False
    for kind, path, builder in targets:
        print(f"[{kind}] {path.name}")
        existing = load_existing_json(path)
        # 既存ファイルの _note / directions を温存したいため existing を渡す
        expected = builder(existing)
        drift = compare_and_report(kind, existing, expected)
        if drift:
            any_drift = True
            if args.apply:
                write_json_with_backup(path, expected)
        print()

    if args.check:
        if any_drift:
            print("✗ ドリフト検出: --apply で修正してください")
            return 1
        print("✓ ドリフトなし — すべての JSON は Python 側と一致しています")
        return 0

    # --apply
    if any_drift:
        print("✓ 差分を反映しました")
    else:
        print("✓ 差分なし — ファイルは変更されていません")
    return 0


if __name__ == "__main__":
    sys.exit(main())
