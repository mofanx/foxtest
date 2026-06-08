# -*- coding:utf-8 -*-
"""覆盖报告功能单测。"""
import json
import subprocess
import tempfile
from pathlib import Path


def test_report_basic():
    """测试基本报告生成。"""
    # 创建测试用例文件
    cases_dir = Path(tempfile.mkdtemp())
    cases_file = cases_dir / "test.md"
    cases_file.write_text(
        "# 测试\n"
        "## 用例1\n内容\n"
        "## 用例2\n内容\n",
        encoding="utf-8"
    )

    # 使用现有的 IR 目录
    ir_dir = Path("skills/foxtest/ir/examples")

    # 创建输出目录
    out_dir = Path(tempfile.mkdtemp())

    # 运行 report 命令 (不带 snapshot 和 code-lcov)
    result = subprocess.run(
        [
            "python",
            "skills/foxtest/scripts/coverage.py",
            "report",
            "--cases-dir", str(cases_dir),
            "--ir-dir", str(ir_dir),
            "--out", str(out_dir)
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # 检查输出文件
    json_file = out_dir / "coverage-summary.json"
    md_file = out_dir / "coverage-summary.md"

    assert json_file.exists(), "JSON 报告文件未生成"
    assert md_file.exists(), "Markdown 报告文件未生成"

    # 检查 JSON 内容
    report = json.loads(json_file.read_text(encoding="utf-8"))
    assert "cases" in report
    assert "ui" in report
    assert "code" in report
    assert report["code"] is None  # 未提供 lcov 时应为 None

    # 检查 Markdown 内容
    md_content = md_file.read_text(encoding="utf-8")
    assert "用例覆盖" in md_content
    assert "UI 元素覆盖" in md_content
    assert "N/A" in md_content or "前端代码覆盖" in md_content


def test_report_with_lcov():
    """测试带 lcov 的报告生成。"""
    # 创建测试用例文件
    cases_dir = Path(tempfile.mkdtemp())
    cases_file = cases_dir / "test.md"
    cases_file.write_text("# 测试\n## 用例1\n内容\n", encoding="utf-8")

    # 使用现有的 IR 目录
    ir_dir = Path("skills/foxtest/ir/examples")

    # 使用现有的 lcov 文件
    lcov_file = Path("runner/coverage/lcov.info")

    if not lcov_file.exists():
        # 如果 lcov 不存在，跳过此测试
        return

    # 创建输出目录
    out_dir = Path(tempfile.mkdtemp())

    # 运行 report 命令 (带 code-lcov)
    result = subprocess.run(
        [
            "python3",
            "skills/foxtest/scripts/coverage.py",
            "report",
            "--cases-dir", str(cases_dir),
            "--ir-dir", str(ir_dir),
            "--code-lcov", str(lcov_file),
            "--out", str(out_dir)
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # 检查 JSON 内容
    json_file = out_dir / "coverage-summary.json"
    report = json.loads(json_file.read_text(encoding="utf-8"))
    assert report["code"] is not None
    assert "total_lines" in report["code"]
    assert "coverage_percent" in report["code"]


def test_cases_ui_no_regression():
    """测试 cases 和 ui 子命令不回归。"""
    # 测试 cases 子命令
    cases_dir = Path(tempfile.mkdtemp())
    cases_file = cases_dir / "test.md"
    cases_file.write_text("# 测试\n## 用例1\n内容\n", encoding="utf-8")

    ir_dir = Path("skills/foxtest/ir/examples")

    result = subprocess.run(
        [
            "python3",
            "skills/foxtest/scripts/coverage.py",
            "cases",
            "--cases-dir", str(cases_dir),
            "--ir-dir", str(ir_dir)
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "用例覆盖" in result.stdout


def test_lcov_parsing():
    """测试 lcov 解析功能。"""
    # 创建测试 lcov 文件
    lcov_content = """SF:/path/to/file.js
DA:1,1
DA:2,0
DA:3,1
end_of_record
"""
    lcov_file = Path(tempfile.mktemp(suffix=".lcov"))
    lcov_file.write_text(lcov_content, encoding="utf-8")

    # 导入并测试 parse_lcov 函数
    import sys
    sys.path.insert(0, "skills/foxtest/scripts")
    from coverage import parse_lcov

    result = parse_lcov(lcov_file)
    assert result is not None
    assert result["total_lines"] == 3
    assert result["covered_lines"] == 2
    assert abs(result["coverage_percent"] - 66.67) < 0.1

    # 清理
    lcov_file.unlink()