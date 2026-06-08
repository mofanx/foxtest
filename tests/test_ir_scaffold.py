# -*- coding:utf-8 -*-
"""IR 脚手架生成器单测。"""
import json
import subprocess
import tempfile


def test_scaffold_basic():
    """测试基本脚手架生成。"""
    result = subprocess.run(
        [
            "python",
            "skills/foxtest/scripts/ir_scaffold.py",
            "--name", "测试用例",
            "--feature", "测试",
            "--base", "http://example.com",
            "--intent", "点击按钮",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    ir = json.loads(result.stdout)
    assert ir["name"] == "测试用例"
    assert ir["feature"] == "测试"
    assert ir["baseURL"] == "http://example.com"
    assert len(ir["steps"]) == 2  # goto + 1 intent
    assert ir["steps"][0]["action"] == "goto"
    assert ir["steps"][1]["action"] == "click"
    assert ir["steps"][1]["locator"]["by"] == "role"
    assert ir["steps"][1]["comment"] == "点击按钮"


def test_scaffold_multiple_intents():
    """测试多个意图。"""
    result = subprocess.run(
        [
            "python",
            "skills/foxtest/scripts/ir_scaffold.py",
            "--name", "多步骤测试",
            "--intent", "步骤1",
            "--intent", "步骤2",
            "--intent", "步骤3",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    ir = json.loads(result.stdout)
    assert len(ir["steps"]) == 4  # goto + 3 intents
    assert ir["steps"][1]["comment"] == "步骤1"
    assert ir["steps"][2]["comment"] == "步骤2"
    assert ir["steps"][3]["comment"] == "步骤3"


def test_scaffold_validate():
    """测试脚手架输出能通过 validate_ir.py。"""
    result = subprocess.run(
        [
            "python",
            "skills/foxtest/scripts/ir_scaffold.py",
            "--name", "验证测试",
            "--base", "http://localhost:8000",
            "--intent", "填写表单",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write(result.stdout)
        temp_path = f.name

    try:
        validate_result = subprocess.run(
            ["python", "skills/foxtest/scripts/validate_ir.py", temp_path],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "[OK]" in validate_result.stdout
    finally:
        import os
        os.unlink(temp_path)


def test_scaffold_minimal():
    """测试最小参数（只有 name）。"""
    result = subprocess.run(
        [
            "python",
            "skills/foxtest/scripts/ir_scaffold.py",
            "--name", "最小测试",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    ir = json.loads(result.stdout)
    assert ir["name"] == "最小测试"
    assert "feature" not in ir
    assert "baseURL" not in ir
    assert len(ir["steps"]) == 1  # 只有 goto 占位
    assert ir["steps"][0]["action"] == "goto"