#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
IR 脚手架生成器。

根据用例元信息产出合法的 IR 骨架(steps 仅含 goto + 注释占位,locator 待 agent 填)。
核心智能仍由 agent + dp-cli 完成;本脚本只产模板,不臆造定位器。

用法:
  python ir_scaffold.py --name "登录-正常登录" --feature 登录 --base http://localhost:8000 \\
    --intent "填写用户名" --intent "点击登录"
"""
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(description="IR 脚手架生成器")
    parser.add_argument("--name", required=True, help="用例名称")
    parser.add_argument("--feature", help="所属功能模块")
    parser.add_argument("--base", help="基础 URL")
    parser.add_argument("--intent", action="append", default=[], help="步骤意图(可重复)")
    args = parser.parse_args()

    # 构建 IR 骨架
    ir = {
        "name": args.name,
    }

    if args.feature:
        ir["feature"] = args.feature
    if args.base:
        ir["baseURL"] = args.base

    # 构建步骤
    steps = []

    # 第一步总是 goto (如果有 base URL 则相对路径，否则占位)
    if args.base:
        steps.append({
            "action": "goto",
            "url": "/",
            "comment": "TODO: 替换为实际页面路径"
        })
    else:
        steps.append({
            "action": "goto",
            "url": "TODO: 替换为实际 URL",
            "comment": "TODO: 替换为实际 URL"
        })

    # 每个 intent 生成一条占位步骤
    for intent in args.intent:
        # 默认使用 role 定位器作为占位（最常用）
        placeholder_step = {
            "action": "click",  # 默认动作，agent 会根据意图修改
            "locator": {
                "by": "role",
                "role": "TODO",
                "name": "TODO"
            },
            "comment": intent
        }
        steps.append(placeholder_step)

    ir["steps"] = steps

    # 输出 JSON
    json.dump(ir, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()