# -*- coding:utf-8 -*-
"""
IR 校验器:按 ir/schema.json 校验一个或多个 IR 文件。

用法:
  python validate_ir.py case1.ir.json case2.ir.json

无 jsonschema 时降级为最小必填字段检查(仍可用,但不如完整 schema 严格)。
退出码:全部通过 0;有失败 1。
"""
import json
import sys
from pathlib import Path

_SCHEMA = Path(__file__).resolve().parent.parent / "ir" / "schema.json"

_VALID_ACTIONS = {"goto", "click", "dblclick", "fill", "type", "press",
                  "select", "check", "uncheck", "hover", "wait", "expect"}
_VALID_BY = {"role", "label", "text", "placeholder", "testid", "alt",
             "title", "css", "xpath"}


def _minimal_check(ir: dict) -> list:
    """无 jsonschema 时的兜底检查,返回错误列表。"""
    errs = []
    if not ir.get("name"):
        errs.append("缺少 name")
    steps = ir.get("steps")
    if not isinstance(steps, list) or not steps:
        errs.append("steps 必须是非空数组")
        return errs
    for i, s in enumerate(steps):
        a = s.get("action")
        if a not in _VALID_ACTIONS:
            errs.append(f"step[{i}] 非法 action: {a!r}")
        if a == "goto" and not s.get("url"):
            errs.append(f"step[{i}] goto 缺少 url")
        if a == "expect" and not s.get("type"):
            errs.append(f"step[{i}] expect 缺少 type")
        if a in ("click", "dblclick", "hover", "check", "uncheck", "fill", "type", "select"):
            loc = s.get("locator")
            if not loc:
                errs.append(f"step[{i}] {a} 缺少 locator")
            elif loc.get("by") not in _VALID_BY:
                errs.append(f"step[{i}] 非法 locator.by: {loc.get('by')!r}")
        if a in ("fill", "type", "select") and s.get("value") is None:
            errs.append(f"step[{i}] {a} 缺少 value")
    return errs


def validate_file(path: str) -> list:
    try:
        ir = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        return [f"无法解析 JSON: {e}"]

    try:
        import jsonschema
        schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft7Validator(schema)
        return [f"{'/'.join(map(str, e.path))}: {e.message}"
                for e in validator.iter_errors(ir)]
    except ImportError:
        return _minimal_check(ir)


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("用法: python validate_ir.py <ir.json> [...]")
        return 2
    failed = False
    for path in argv:
        errs = validate_file(path)
        if errs:
            failed = True
            print(f"✗ {path}")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"✓ {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
