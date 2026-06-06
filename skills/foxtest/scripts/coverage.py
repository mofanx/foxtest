# -*- coding:utf-8 -*-
"""
覆盖度量(本期:① 用例覆盖 + ② UI 元素覆盖 + ③ 代码覆盖)。

子命令:
  cases  —— 用例覆盖:有多少用例(Markdown 标题)已生成对应 IR
  ui     —— UI 元素覆盖:页面可交互元素中,有多少被 IR 脚本操作过
  report —— 三层覆盖统一报告:聚合 ①②③ 产出 JSON + Markdown

UI 匹配为启发式(role+name / name / locator 子串),用于回归盲区提示,不追求绝对精确。
"""
import argparse
import json
import re
from pathlib import Path


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "")).lower()


# ─────────────────────────────────────────────────────────────────────────────
# ① 用例覆盖
# ─────────────────────────────────────────────────────────────────────────────

_HEADING = re.compile(r"^#{2,3}\s+(.+?)\s*$")


def collect_cases(cases_dir: Path) -> list:
    names = []
    for md in sorted(Path(cases_dir).rglob("*.md")):
        for line in md.read_text(encoding="utf-8").splitlines():
            m = _HEADING.match(line)
            if m:
                names.append(m.group(1).strip())
    return names


def collect_ir_names(ir_dir: Path) -> list:
    names = []
    for f in sorted(Path(ir_dir).rglob("*.ir.json")):
        try:
            names.append(json.loads(f.read_text(encoding="utf-8")).get("name", ""))
        except Exception:
            pass
    return names


def cmd_cases(args) -> int:
    cases = collect_cases(Path(args.cases_dir))
    ir_names = [_norm(n) for n in collect_ir_names(Path(args.ir_dir))]
    if not cases:
        print("未在 cases-dir 找到用例(以 ## / ### 标题计)")
        return 0
    covered, missing = [], []
    for c in cases:
        nc = _norm(c)
        if any(nc == n or nc in n or n in nc for n in ir_names if n):
            covered.append(c)
        else:
            missing.append(c)
    pct = len(covered) / len(cases) * 100
    print(f"用例覆盖: {len(covered)}/{len(cases)} = {pct:.1f}%")
    if missing:
        print("未生成 IR 的用例:")
        for c in missing:
            print(f"  - {c}")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# ② UI 元素覆盖
# ─────────────────────────────────────────────────────────────────────────────

def extract_universe(snapshot: dict) -> list:
    """从 dp snapshot JSON 中提取可交互元素全集。

    兼容两种形态:
      - {'refs': {id: {role, name, locator, ...}}}
      - {'clickable_extras': [{role/tag, label/text, locator}]}
      - 顶层就是 refs dict
    返回 [{'role','name','locator'}]
    """
    universe = []
    refs = snapshot.get("refs") if isinstance(snapshot, dict) else None
    if refs is None and isinstance(snapshot, dict) and all(
            isinstance(v, dict) for v in snapshot.values()) and "steps" not in snapshot:
        refs = snapshot  # 顶层即 refs
    if isinstance(refs, dict):
        for v in refs.values():
            universe.append({
                "role": v.get("role", ""),
                "name": v.get("name", ""),
                "locator": v.get("locator", ""),
            })
    for e in (snapshot.get("clickable_extras") or []) if isinstance(snapshot, dict) else []:
        universe.append({
            "role": e.get("role") or e.get("tag", ""),
            "name": e.get("label") or e.get("text", ""),
            "locator": e.get("locator", ""),
        })
    return universe


def ir_signatures(ir: dict) -> list:
    """从 IR 的交互/断言步骤提取被操作元素签名。"""
    sigs = []
    for s in ir.get("steps", []):
        loc = s.get("locator")
        if not loc:
            continue
        by = loc.get("by")
        if by == "role":
            sigs.append(("role", _norm(loc.get("role", "")), _norm(loc.get("name", ""))))
        elif by in ("label", "text", "placeholder", "alt", "title"):
            sigs.append(("name", _norm(loc.get("value", ""))))
        elif by == "testid":
            sigs.append(("locator", _norm(loc.get("value", ""))))
        elif by in ("css", "xpath"):
            sigs.append(("locator", _norm(loc.get("value", ""))))
    return sigs


def _matches(elem: dict, sig) -> bool:
    er, en, el = _norm(elem["role"]), _norm(elem["name"]), _norm(elem["locator"])
    if sig[0] == "role":
        return er == sig[1] and (not sig[2] or sig[2] in en or en in sig[2])
    if sig[0] == "name":
        return bool(sig[1]) and (sig[1] in en or en in sig[1])
    if sig[0] == "locator":
        return bool(sig[1]) and (sig[1] in el or el in sig[1])
    return False


def cmd_ui(args) -> int:
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    universe = extract_universe(snapshot)
    if not universe:
        print("快照中未提取到可交互元素(检查 dp snapshot --format json 输出)")
        return 0
    sigs = []
    for ir_path in args.ir:
        ir = json.loads(Path(ir_path).read_text(encoding="utf-8"))
        sigs.extend(ir_signatures(ir))

    covered, uncovered = [], []
    for elem in universe:
        if any(_matches(elem, s) for s in sigs):
            covered.append(elem)
        else:
            uncovered.append(elem)
    total = len(universe)
    pct = len(covered) / total * 100
    print(f"UI 元素覆盖: {len(covered)}/{total} = {pct:.1f}%")
    if uncovered:
        print("未被任何用例操作的可交互元素(回归盲区):")
        for e in uncovered[:50]:
            label = e["name"] or e["locator"] or "(无名)"
            print(f"  - {e['role'] or 'element'} \"{label}\"")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# ③ 代码覆盖 (lcov 解析)
# ─────────────────────────────────────────────────────────────────────────────

def parse_lcov(lcov_path: Path) -> dict:
    """解析 lcov.info 文件，返回行覆盖统计。"""
    if not lcov_path.exists():
        return None

    total_lines = 0
    covered_lines = 0

    try:
        content = lcov_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("DA:"):
                parts = line[3:].split(",")
                if len(parts) == 2:
                    total_lines += 1
                    count = int(parts[1])
                    if count > 0:
                        covered_lines += 1
    except Exception as e:
        print(f"警告：解析 lcov 文件失败: {e}")
        return None

    if total_lines == 0:
        return None

    return {
        "total_lines": total_lines,
        "covered_lines": covered_lines,
        "coverage_percent": covered_lines / total_lines * 100 if total_lines > 0 else 0
    }


# ─────────────────────────────────────────────────────────────────────────────
# report 子命令：三层覆盖统一报告
# ─────────────────────────────────────────────────────────────────────────────

def cmd_report(args) -> int:
    """生成三层覆盖统一报告。"""
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ① 用例覆盖
    cases = collect_cases(Path(args.cases_dir))
    ir_names = [_norm(n) for n in collect_ir_names(Path(args.ir_dir))]
    cases_covered, cases_missing = [], []
    for c in cases:
        nc = _norm(c)
        if any(nc == n or nc in n or n in nc for n in ir_names if n):
            cases_covered.append(c)
        else:
            cases_missing.append(c)
    cases_pct = len(cases_covered) / len(cases) * 100 if cases else 0

    # ② UI 元素覆盖
    ui_data = {"total": 0, "covered": 0, "coverage_percent": 0, "uncovered": []}
    if args.snapshot and Path(args.snapshot).exists():
        snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        universe = extract_universe(snapshot)
        if universe:
            sigs = []
            for ir_path in Path(args.ir_dir).rglob("*.ir.json"):
                ir = json.loads(ir_path.read_text(encoding="utf-8"))
                sigs.extend(ir_signatures(ir))

            for elem in universe:
                if any(_matches(elem, s) for s in sigs):
                    ui_data["covered"] += 1
                else:
                    ui_data["uncovered"].append(elem)
            ui_data["total"] = len(universe)
            ui_data["coverage_percent"] = ui_data["covered"] / ui_data["total"] * 100 if ui_data["total"] > 0 else 0

    # ③ 代码覆盖
    code_data = None
    if args.code_lcov:
        code_data = parse_lcov(Path(args.code_lcov))

    # 构建 JSON 报告
    report_json = {
        "cases": {
            "total": len(cases),
            "covered": len(cases_covered),
            "coverage_percent": round(cases_pct, 1),
            "missing": cases_missing
        },
        "ui": {
            "total": ui_data["total"],
            "covered": ui_data["covered"],
            "coverage_percent": round(ui_data["coverage_percent"], 1),
            "uncovered_count": len(ui_data["uncovered"])
        },
        "code": code_data
    }

    json_path = out_dir / "coverage-summary.json"
    json_path.write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")

    # 构建 Markdown 报告
    md_lines = [
        "# 覆盖度量汇总报告",
        "",
        "## ① 用例覆盖",
        f"- **覆盖率**: {len(cases_covered)}/{len(cases)} = {cases_pct:.1f}%",
        ""
    ]
    if cases_missing:
        md_lines.append("未生成 IR 的用例:")
        for c in cases_missing:
            md_lines.append(f"  - {c}")
        md_lines.append("")

    md_lines.extend([
        "## ② UI 元素覆盖",
        f"- **覆盖率**: {ui_data['covered']}/{ui_data['total']} = {ui_data['coverage_percent']:.1f}%",
        ""
    ])
    if ui_data["uncovered"]:
        md_lines.append("未被操作的可交互元素 (回归盲区):")
        for e in ui_data["uncovered"][:20]:
            label = e["name"] or e["locator"] or "(无名)"
            md_lines.append(f"  - {e['role'] or 'element'} \"{label}\"")
        if len(ui_data["uncovered"]) > 20:
            md_lines.append(f"  ... (还有 {len(ui_data['uncovered']) - 20} 个)")
        md_lines.append("")

    md_lines.extend([
        "## ③ 前端代码覆盖",
    ])
    if code_data:
        md_lines.extend([
            f"- **行覆盖率**: {code_data['covered_lines']}/{code_data['total_lines']} = {code_data['coverage_percent']:.1f}%",
            ""
        ])
    else:
        md_lines.extend([
            "- **状态**: N/A (未提供 lcov.info 或解析失败)",
            ""
        ])

    md_path = out_dir / "coverage-summary.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"报告已生成:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="foxtest 覆盖度量(用例 / UI 元素 / 代码)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("cases", help="用例覆盖")
    pc.add_argument("--cases-dir", required=True)
    pc.add_argument("--ir-dir", required=True)
    pc.set_defaults(func=cmd_cases)

    pu = sub.add_parser("ui", help="UI 元素覆盖")
    pu.add_argument("--snapshot", required=True, help="dp snapshot --format json 输出")
    pu.add_argument("--ir", nargs="+", required=True, help="一个或多个 IR 文件")
    pu.set_defaults(func=cmd_ui)

    pr = sub.add_parser("report", help="三层覆盖统一报告")
    pr.add_argument("--cases-dir", required=True)
    pr.add_argument("--ir-dir", required=True)
    pr.add_argument("--snapshot", help="dp snapshot --format json 输出 (可选)")
    pr.add_argument("--code-lcov", help="lcov.info 文件路径 (可选)")
    pr.add_argument("--out", required=True, help="输出目录")
    pr.set_defaults(func=cmd_report)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    import sys
    sys.exit(main())
