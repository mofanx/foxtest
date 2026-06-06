# F3 派单:③ 前端 JS 代码覆盖(交给执行 AI)

> 目标:回放时采集**被测前端**的 JS 代码覆盖,产出 lcov/HTML 报告。两端实现 + 统一转换。
> `$ROOT` = foxtest 仓库根,`$S = $ROOT/skills/foxtest`。

## 前置依赖
- **F1 已完成**(runner Python/TS 工程 + demo 站点可回放)。
- 预检:`test -d $ROOT/runner/typescript && test -d $ROOT/runner/python && echo "F1 就绪"`

## 范围
1. **TypeScript 端**:用 Playwright 内置 `page.coverage.startJSCoverage()/stopJSCoverage()`(Chromium)采集 V8 覆盖。
2. **Python 端**:Playwright Python 无内置 coverage → 用 CDP `Profiler.startPreciseCoverage` / `Profiler.takePreciseCoverage`(可经 `dp` 或直接 CDP client)采集 V8 覆盖。
3. **统一转换**:用 `monocart-coverage-reports`(推荐)或 `v8-to-istanbul` 把 V8 → lcov/Istanbul,落 `runner/coverage/`。

> 重要:覆盖必须**真实采集**,不得估算。涉及 Playwright/CDP API 时,以官方文档为准(先查再写)。

## 实施要点
- TS:在 `playwright.config.ts` 或一个 fixture 里包裹用例,测试前 `startJSCoverage`,测试后 `stopJSCoverage` 收集 entries,交给 monocart 生成报告。
- Python:用 pytest fixture 拿到底层 CDP session(`page.context.new_cdp_session(page)`),`Profiler.enable` → `startPreciseCoverage(callCount=True, detailed=True)` → 跑用例 → `takePreciseCoverage` → 转换。
- 产物统一落 `runner/coverage/`(lcov.info 和/或 html)。
- demo 站点目前是纯静态 HTML,**若内联 JS 太少导致覆盖样本不足**,可在 demo 站点加一个被点击触发的小 `app.js`(几行),保证有可观测的 JS 覆盖。

## DoD 验收
```bash
# TS 路径:回放并采集
cd $ROOT/runner/typescript && npm install && npx playwright install chromium && npx playwright test
ls $ROOT/runner/coverage/lcov.info || ls $ROOT/runner/coverage/*.info || ls $ROOT/runner/coverage/index.html

# Python 路径:回放并采集(起静态服见 F1)
# ... 跑带覆盖采集的 pytest,确认 runner/coverage 下有产物
```
**通过标准:**
- [ ] 至少一种语言回放后,`runner/coverage/` 下产出可读报告(lcov 或 HTML)
- [ ] 报告能体现 demo 站点 JS 的行覆盖(非空、非全 0)
- [ ] 文档片段说明两端如何启用覆盖采集
- [ ] 不破坏 F1 的常规回放(不带覆盖时仍能跑绿)

## 禁止事项
- 不估算覆盖;不 mock 掉真实采集。
- 不确定的 API 字段先查官方文档,不臆造。

## 交付物
1. TS 覆盖采集配置/fixture + monocart 配置
2. Python 覆盖采集 fixture/脚本
3. `runner/coverage/` 产物(示例)
4. 启用说明文档片段
5. DoD 命令输出 + 勾选
