# -*- coding:utf-8 -*-
"""Pytest fixtures for coverage collection using CDP."""
import json
import pytest
from pathlib import Path


@pytest.fixture(scope="function", autouse=True)
def coverage_collector(page):
    """
    使用 CDP 采集 JS 代码覆盖的 autouse fixture。

    注意：需要 chromium 浏览器支持 CDP Profiler API。
    自动为所有测试启用覆盖采集。
    """
    try:
        # 创建 CDP 会话
        cdp = page.context.new_cdp_session(page)

        # 启用 Profiler
        cdp.send("Profiler.enable")

        # 启动精确覆盖采集
        cdp.send("Profiler.startPreciseCoverage", {
            "callCount": True,
            "detailed": True
        })

        yield

        # 测试结束后获取覆盖数据
        result = cdp.send("Profiler.takePreciseCoverage")
        coverage_data = result.get("result", [])

        # 禁用 Profiler
        cdp.send("Profiler.disable")

        # 保存覆盖数据
        coverage_dir = Path(__file__).parent.parent / "coverage"
        coverage_dir.mkdir(exist_ok=True)

        coverage_file = coverage_dir / "coverage.json"
        with open(coverage_file, "w") as f:
            json.dump(coverage_data, f, indent=2)

        print(f"覆盖数据已保存: {len(coverage_data)} 个条目")

    except Exception as e:
        print(f"CDP 覆盖采集失败: {e}")
        print("这可能是由于浏览器不支持 CDP Profiler API")
        yield