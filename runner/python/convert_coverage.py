#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
将 V8 CDP 覆盖数据转换为 lcov 格式。

用法:
  python convert_coverage.py coverage.json demo-site/ output/lcov.info
"""
import json
import sys
from pathlib import Path


def v8_to_lcov(v8_coverage: list, source_dir: Path) -> str:
    """
    将 V8 覆盖数据转换为 lcov 格式字符串。

    Args:
        v8_coverage: V8 CDP 返回的覆盖数据列表
        source_dir: 源代码目录，用于过滤和生成文件路径

    Returns:
        lcov 格式字符串
    """
    lcov_lines = []

    # 过滤出目标源的覆盖数据
    for script in v8_coverage:
        url = script.get("url", "")

        # 只处理我们 demo 站点的文件
        if not url or "localhost:8000" not in url:
            continue

        # 转换 URL 为文件路径
        if url.endswith(".html"):
            file_path = source_dir / url.split("/")[-1]
        else:
            continue

        if not file_path.exists():
            continue

        # 读取源代码
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_lines = f.readlines()
        except Exception as e:
            print(f"警告：无法读取源文件 {file_path}: {e}")
            continue

        lcov_lines.append(f"SF:{file_path.absolute()}")

        # 按行聚合覆盖数据
        line_coverage = {}  # line -> (is_covered, count)

        # 处理每个函数的覆盖
        for func in script.get("functions", []):
            ranges = func.get("ranges", [])

            for range_data in ranges:
                start_offset = range_data.get("startOffset", 0)
                end_offset = range_data.get("endOffset", 0)
                count = range_data.get("count", 0)

                # 将 offset 转换为行号
                line_start = offset_to_line(start_offset, source_lines)
                line_end = offset_to_line(end_offset, source_lines)

                # 对范围内的每一行
                for line_num in range(line_start, line_end + 1):
                    if 1 <= line_num <= len(source_lines):
                        if line_num not in line_coverage:
                            line_coverage[line_num] = (count > 0, count)
                        else:
                            # 如果当前 range count=0，强制标记为未覆盖
                            # 即使之前有 count>0 的 range 覆盖这一行
                            if count == 0:
                                line_coverage[line_num] = (False, 0)
                            # 如果当前 count>0 且之前未覆盖，标记为覆盖
                            elif count > 0 and not line_coverage[line_num][0]:
                                line_coverage[line_num] = (True, count)

        # 输出所有行的覆盖数据
        for line_num in sorted(line_coverage.keys()):
            is_covered, count = line_coverage[line_num]
            if is_covered:
                lcov_lines.append(f"DA:{line_num},1")
            else:
                lcov_lines.append(f"DA:{line_num},0")

        lcov_lines.append("end_of_record")

    return "\n".join(lcov_lines)


def offset_to_line(offset: int, lines: list) -> int:
    """
    将字符偏移量转换为行号（简化版）。

    Args:
        offset: 字符偏移量
        lines: 源代码行列表

    Returns:
        行号（从1开始）
    """
    current_offset = 0
    for i, line in enumerate(lines, 1):
        current_offset += len(line)
        if current_offset >= offset:
            return i
    return len(lines)


def main():
    if len(sys.argv) < 3:
        print("用法: python convert_coverage.py <coverage.json> <source_dir> [output_file]")
        sys.exit(1)

    coverage_file = Path(sys.argv[1])
    source_dir = Path(sys.argv[2])
    output_file = Path(sys.argv[3]) if len(sys.argv) > 3 else coverage_file.parent / "lcov.info"

    # 读取 V8 覆盖数据
    with open(coverage_file, "r") as f:
        v8_coverage = json.load(f)

    # 转换为 lcov
    lcov_content = v8_to_lcov(v8_coverage, source_dir)

    # 保存
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write(lcov_content)

    print(f"lcov 报告已生成: {output_file}")

    # 打印统计信息
    da_lines = [l for l in lcov_content.splitlines() if l.startswith("DA:")]
    if da_lines:
        hit_lines = [l for l in da_lines if l.split(",")[-1] != "0"]
        miss_lines = [l for l in da_lines if l.split(",")[-1] == "0"]
        total = len(da_lines)
        hit = len(hit_lines)
        miss = len(miss_lines)
        pct = hit / total * 100 if total > 0 else 0
        print(f"行覆盖统计: {hit}/{total} = {pct:.1f}% (未覆盖: {miss} 行)")

    # 打印函数覆盖统计
    demo_functions = []
    for script in v8_coverage:
        if "localhost:8000" in script.get("url", ""):
            for func in script.get("functions", []):
                func_name = func.get("functionName", "")
                if func_name and not func_name.startswith("_"):
                    total_count = sum(r.get("count", 0) for r in func.get("ranges", []))
                    demo_functions.append((func_name, total_count))

    if demo_functions:
        print("\nDemo 站点函数覆盖统计:")
        for func_name, count in demo_functions:
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {func_name}: {count} 次调用")


if __name__ == "__main__":
    # 设置 stdout 编码为 UTF-8，以兼容 Windows GBK 控制台
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()