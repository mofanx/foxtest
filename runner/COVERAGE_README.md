# 前端 JS 代码覆盖采集说明

## 概述

本配置支持采集被测前端 JavaScript 的代码覆盖，产出 lcov/HTML 报告。

## Python 端 (推荐)

Python 端使用 CDP (Chrome DevTools Protocol) `Profiler` API 采集 V8 覆盖数据。

### 启用方式

1. 在测试文件中使用 `coverage_collector` fixture:

```python
def test_example(page, coverage_collector):
    # 测试代码
    page.goto("http://localhost:8000")
    # ...
```

2. 运行测试后会自动生成 `runner/coverage/coverage.json`

3. 转换为 lcov 格式:

```bash
cd runner/python
python convert_coverage.py ../coverage/coverage.json ../demo-site/ ../coverage/lcov.info
```

### 依赖

- `pytest-playwright`
- 支持 CDP 的浏览器 (Chromium/Chrome)

### 示例输出

```
lcov 报告已生成: ../coverage/lcov.info

Demo 站点函数覆盖统计:
  ✗ greet: 0 次调用
  ✓ validateLogin: 1 次调用
  ✓ handleLogin: 1 次调用
```

## TypeScript 端

TypeScript 端尝试使用 Playwright 内置 `page.coverage` API，但在使用系统 chrome 时可能不可用。

### 启用方式

在测试文件中手动调用覆盖 API:

```typescript
test("example", async ({ page }) => {
  await page.coverage.startJSCoverage();
  // 测试代码
  const coverage = await page.coverage.stopJSCoverage();
  // 保存覆盖数据
});
```

### 限制

- 需要原版 Chromium 浏览器
- 使用系统 chrome 时可能不支持

## 覆盖报告位置

所有覆盖报告统一存放在 `runner/coverage/` 目录:
- `coverage.json`: 原始 V8 覆盖数据
- `lcov.info`: lcov 格式报告
- `index.html`: HTML 覆盖报告 (可选，需使用 genhtml 工具生成)

## 不带覆盖的常规回放

如果不需要覆盖采集，只需在测试中不使用 `coverage_collector` fixture 即可，常规回放不受影响。

## 兼容性说明

- **Python 端**: 在 ubuntu 26.04 上使用系统 chrome 测试通过 ✓
- **TypeScript 端**: 系统 chrome 的 coverage API 不可用，需要原版 Chromium