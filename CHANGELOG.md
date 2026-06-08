# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-06-08

### Added
- IR JSON Schema 定义测试用例中间表示
- 双语言代码生成器 (Python pytest + TypeScript @playwright/test)
- IR 校验器 (validate_ir.py)
- 覆盖度量工具 (coverage.py)
  - 用例覆盖统计
  - UI 元素覆盖统计
  - 前端 JS 代码覆盖 (CDP V8 覆盖采集)
- IR 脚手架生成器 (ir_scaffold.py)
- demo 站点和示例测试用例
- 失败自愈工作流文档
- Claude Code plugin 清单

### Features
- 语义定位优先 (role/label/testid)
- 敏感值占位 `<secret:ENV>` 支持
- 双语言同步生成
- Windows 跨平台兼容

### Documentation
- SKILL.md - 完整的 AI 协作工作流
- 参考文档 (ir-schema.md, locator-map.md)
- 浏览器配置说明
- 覆盖采集说明

### Tested
- Python 回放验证通过
- TypeScript 回放验证通过
- 覆盖率采集验证通过 (62.5%)
- Windows 环境兼容性验证

---

## [Unreleased]

### Planned
- AI 探索循环实战验证
- Plugin marketplace 发布
