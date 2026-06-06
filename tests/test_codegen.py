# -*- coding:utf-8 -*-
"""codegen / validate_ir 的单元测试,保障双语言生成的确定性与正确性。"""
import importlib.util
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "foxtest" / "scripts"
EXAMPLES = ROOT / "skills" / "foxtest" / "ir" / "examples"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


codegen = _load("codegen")
validate_ir = _load("validate_ir")

import json
LOGIN = json.loads((EXAMPLES / "login.ir.json").read_text(encoding="utf-8"))
SEARCH = json.loads((EXAMPLES / "search.ir.json").read_text(encoding="utf-8"))


# ── Python 生成 ──

def test_python_role_locator():
    out = codegen.emit_python(LOGIN)
    assert 'page.get_by_role("button", name="登录").click()' in out
    assert 'page.get_by_label("用户名").fill("admin")' in out


def test_python_secret_uses_env():
    out = codegen.emit_python(LOGIN)
    assert "import os" in out
    assert 'os.environ["APP_PASSWORD"]' in out


def test_python_expect():
    out = codegen.emit_python(LOGIN)
    assert "import re" in out
    assert "to_have_url(re.compile" in out
    assert 'expect(page.get_by_text("欢迎")).to_be_visible()' in out


def test_python_compiles(tmp_path):
    f = tmp_path / "t.py"
    f.write_text(codegen.emit_python(SEARCH), encoding="utf-8")
    py_compile.compile(str(f), doraise=True)


# ── TypeScript 生成 ──

def test_ts_role_locator():
    out = codegen.emit_typescript(LOGIN)
    assert "import { test, expect } from '@playwright/test';" in out
    assert 'await page.getByRole("button", { name: "登录" }).click();' in out


def test_ts_secret_uses_env():
    out = codegen.emit_typescript(LOGIN)
    assert 'process.env["APP_PASSWORD"]!' in out


def test_ts_count_and_testid():
    out = codegen.emit_typescript(SEARCH)
    assert 'getByTestId("result-list")' in out
    assert "toHaveCount(10)" in out


# ── 校验器 ──

def test_validate_valid_examples():
    assert validate_ir.validate_file(str(EXAMPLES / "login.ir.json")) == []
    assert validate_ir.validate_file(str(EXAMPLES / "search.ir.json")) == []


def test_validate_catches_bad_action(tmp_path):
    bad = tmp_path / "bad.ir.json"
    bad.write_text(json.dumps({"name": "x", "steps": [{"action": "frobnicate"}]}),
                   encoding="utf-8")
    assert validate_ir.validate_file(str(bad))  # 非空 = 有错误


# ── 新增 action 测试 ──

def test_python_upload_action():
    ir = {
        "name": "upload test",
        "steps": [
            {"action": "upload", "locator": {"by": "css", "value": "#file"}, "value": "/path/to/file.txt"}
        ]
    }
    out = codegen.emit_python(ir)
    assert 'set_input_files("/path/to/file.txt")' in out


def test_ts_upload_action():
    ir = {
        "name": "upload test",
        "steps": [
            {"action": "upload", "locator": {"by": "css", "value": "#file"}, "value": "/path/to/file.txt"}
        ]
    }
    out = codegen.emit_typescript(ir)
    assert 'setInputFiles("/path/to/file.txt")' in out


def test_python_drag_action():
    ir = {
        "name": "drag test",
        "steps": [
            {
                "action": "drag",
                "locator": {"by": "testid", "value": "source"},
                "target": {"by": "testid", "value": "target"}
            }
        ]
    }
    out = codegen.emit_python(ir)
    assert 'get_by_test_id("source").drag_to(' in out
    assert 'get_by_test_id("target")' in out


def test_ts_drag_action():
    ir = {
        "name": "drag test",
        "steps": [
            {
                "action": "drag",
                "locator": {"by": "testid", "value": "source"},
                "target": {"by": "testid", "value": "target"}
            }
        ]
    }
    out = codegen.emit_typescript(ir)
    assert 'getByTestId("source").dragTo(' in out
    assert 'getByTestId("target")' in out


def test_python_scroll_action():
    ir = {
        "name": "scroll test",
        "steps": [
            {"action": "scroll", "locator": {"by": "testid", "value": "footer"}}
        ]
    }
    out = codegen.emit_python(ir)
    assert 'scroll_into_view_if_needed()' in out


def test_ts_scroll_action():
    ir = {
        "name": "scroll test",
        "steps": [
            {"action": "scroll", "locator": {"by": "testid", "value": "footer"}}
        ]
    }
    out = codegen.emit_typescript(ir)
    assert 'scrollIntoViewIfNeeded()' in out


# ── 新增 expect 类型测试 ──

def test_python_contains_text():
    ir = {
        "name": "contains test",
        "steps": [
            {"action": "expect", "type": "contains_text", "locator": {"by": "css", "value": ".msg"}, "value": "Hello"}
        ]
    }
    out = codegen.emit_python(ir)
    assert 'to_contain_text("Hello")' in out


def test_ts_contains_text():
    ir = {
        "name": "contains test",
        "steps": [
            {"action": "expect", "type": "contains_text", "locator": {"by": "css", "value": ".msg"}, "value": "Hello"}
        ]
    }
    out = codegen.emit_typescript(ir)
    assert 'toContainText("Hello")' in out


def test_python_attr_exists():
    ir = {
        "name": "attr exists test",
        "steps": [
            {"action": "expect", "type": "attr_exists", "locator": {"by": "css", "value": "#btn"}, "attr": "disabled"}
        ]
    }
    out = codegen.emit_python(ir)
    assert 'to_have_attribute("disabled")' in out


def test_ts_attr_exists():
    ir = {
        "name": "attr exists test",
        "steps": [
            {"action": "expect", "type": "attr_exists", "locator": {"by": "css", "value": "#btn"}, "attr": "disabled"}
        ]
    }
    out = codegen.emit_typescript(ir)
    assert 'toHaveAttribute("disabled")' in out


def test_python_enabled():
    ir = {
        "name": "enabled test",
        "steps": [
            {"action": "expect", "type": "enabled", "locator": {"by": "css", "value": "#btn"}}
        ]
    }
    out = codegen.emit_python(ir)
    assert 'to_be_enabled()' in out


def test_ts_enabled():
    ir = {
        "name": "enabled test",
        "steps": [
            {"action": "expect", "type": "enabled", "locator": {"by": "css", "value": "#btn"}}
        ]
    }
    out = codegen.emit_typescript(ir)
    assert 'toBeEnabled()' in out


def test_python_disabled():
    ir = {
        "name": "disabled test",
        "steps": [
            {"action": "expect", "type": "disabled", "locator": {"by": "css", "value": "#btn"}}
        ]
    }
    out = codegen.emit_python(ir)
    assert 'to_be_disabled()' in out


def test_ts_disabled():
    ir = {
        "name": "disabled test",
        "steps": [
            {"action": "expect", "type": "disabled", "locator": {"by": "css", "value": "#btn"}}
        ]
    }
    out = codegen.emit_typescript(ir)
    assert 'toBeDisabled()' in out
