# foxtest 后续开发计划(供 AI 执行,大脑编排)

> 本文是**执行指南**,面向被指派开发的 AI 工具。每个任务单(F 系列)都给出:
> 范围 / 策略 / 交付物 / **可机械验证的 DoD** / 禁止事项。
> 角色分工:**大脑(高价模型)= 拆单 + 验收 + 打回**;**执行(低价/其他 AI)= 写代码 + 自检后交付**。
> 铁律:不信"已完成"的口头汇报,一切以 DoD 命令的客观输出(pytest / 脚本运行 / 文件存在)为准。

---

## 0. 现状(已完成,勿重做)

| 资产 | 路径 | 状态 |
|---|---|---|
| IR JSON Schema | `skills/foxtest/ir/schema.json` | ✅ |
| 双语言 codegen | `skills/foxtest/scripts/codegen.py` | ✅ Python+TS |
| IR 校验器 | `skills/foxtest/scripts/validate_ir.py` | ✅ |
| 覆盖度量(① 用例 + ② UI) | `skills/foxtest/scripts/coverage.py` | ✅ |
| Skill 编排剧本 | `skills/foxtest/SKILL.md` | ✅ 骨架 |
| 参考文档 | `skills/foxtest/reference/*.md` | ✅ |
| codegen/校验单测 | `tests/test_codegen.py` | ✅ 9 passed |
| plugin 清单(预置) | `.claude-plugin/plugin.json` | ✅ 最简 |

**约定**:仓库根记为 `$ROOT`;skill 目录 `$S = $ROOT/skills/foxtest`;脚本统一 `python $S/scripts/<name>.py`。
Python 侧确定性脚本必须有单测(放 `$ROOT/tests/`);agentic 能力(探索)用"端到端产出物可验证"来把关。

---

## 1. 协作与验收模型

**通用任务卡结构**(每个 F 任务都遵循):
1. **范围**:动哪些文件、做什么、不做什么
2. **策略**:实现要点、复用什么、避免什么反模式
3. **交付物**:新增/修改的文件清单
4. **DoD 验收**:一段可直接跑的命令 + 通过标准(勾选项)
5. **禁止事项**:不破坏现有资产、不引入未声明依赖、发现疑似 bug 停下报告

**验收门(大脑每轮固定动作)**:跑该任务 DoD → 看证据 → 通过则进下一单 / 失败则带"期望 vs 实际 + 文件行号"打回。绝不替执行方重写。

**串行依赖**:按下表 `依赖` 列推进,前一单验收通过才放下一单(并行项可同时派)。

---

## 2. 任务总览

| 单号 | 任务 | 依赖 | 优先级 | DoD 摘要 | 状态 |
|------|------|------|--------|----------|------|
| F1 | 回放工程脚手架(Python + TS 可运行) | — | 高 | 生成的示例测试能在本地 demo 站点跑绿 | ✅ 已完成 |
| F2 | M1 AI 探索循环(NL→探索→IR)落地到 SKILL.md + 助手脚本 | F1 | 高 | 对固定 demo 用例产出合法 IR,codegen+回放绿 | ✅ 已完成 |
| F3 | ③ 前端代码覆盖(TS 内置 + Python CDP)+ 统一报告 | F1 | 中 | 回放后产出 lcov/HTML 代码覆盖报告 | ✅ 已完成 (已修补) |
| F4 | 三层覆盖统一报告(①②③ 汇总 JSON+Markdown) | F2,F3 | 中 | 单命令产出含三层指标的报告 | ✅ 已完成 |
| F5 | codegen 增强(页面对象/参数化/更多 action 与断言) | F1 | 中 | 新增能力均有单测;旧用例不回归 | ✅ 已完成 |
| F6 | 失败自愈回路(回放失败 → 重定位/重规划) | F2 | 低 | 注入可控失败,验证自愈或给出明确诊断 | ✅ 已完成 |
| F7 | Claude Code plugin 正式化(components/命令/marketplace) | F1-F4 | 中 | plugin.json 合法、skill 可被发现、/命令可用 | ✅ 已完成 |
| F8 | foxtest 仓库自身 CI | F1,F5 | 中 | GitHub Actions 跑 `tests/` 绿 | ✅ 已完成 |

---

## 3. 任务详情

### F1 — 回放工程脚手架(让生成的脚本真能跑)

**范围**:在 `$ROOT/runner/` 下建立 Python 与 TypeScript 两套最小可运行工程;新增一个本地 demo 站点用于自测。不改 codegen 的生成逻辑。

**策略**:
- `runner/python/`:`pytest.ini` + `requirements.txt`(`pytest`、`pytest-playwright`),约定生成脚本落到 `runner/python/tests/`。
- `runner/typescript/`:`package.json` + `playwright.config.ts`,生成脚本落到 `runner/typescript/tests/`。
- `runner/demo-site/`:一个静态 HTML(含 `登录`/`用户名`/`密码`/`注册` 等元素 + 一个跳转 `dashboard.html`),供示例 IR 真实回放,**不依赖外网**。
- 调整两个示例 IR 的 `baseURL` 指向本地 demo(或新增 demo 专用 IR),让回放可离线跑通。

**交付物**:`runner/python/*`、`runner/typescript/*`、`runner/demo-site/*`、(可选)`skills/foxtest/ir/examples/demo_login.ir.json`。

**DoD 验收**:
```bash
# 生成针对 demo 的脚本
python $S/scripts/codegen.py $S/ir/examples/demo_login.ir.json --lang both --out runner
# Python 回放(headless;demo 站点用 file:// 或本地静态服)
cd runner/python && pip install -r requirements.txt && python -m playwright install chromium && pytest -q
# TS 回放
cd runner/typescript && npm i && npx playwright install chromium && npx playwright test
```
- [ ] Python 回放:示例用例全绿
- [ ] TS 回放:示例用例全绿
- [ ] demo 站点离线可用(无外网请求)

**禁止**:不改 `codegen.py` 生成模板(如发现生成代码跑不通,报告而非私改契约);不引入重型框架。

---

### F2 — M1:AI 探索循环落地

**范围**:把 SKILL.md 的"步骤 2 探索"从描述细化为可复现剧本,并提供一个**IR 脚手架助手** `scripts/ir_scaffold.py`(从结构化用例骨架生成空 IR 模板,降低 agent 出错率)。核心智能仍由 agent + dp-cli 完成。

**策略**:
- `ir_scaffold.py`:输入用例名/feature/baseURL/步骤意图 → 输出符合 schema 的 IR 骨架(locator 待填)。
- SKILL.md 增补:dp snapshot 的 `ref:N` → 如何抉择 locator(引用 `reference/locator-map.md`)、何时插 `expect`、敏感值用 `<secret:>`。
- 提供一个固定 demo 用例(基于 F1 的 demo 站点)的"黄金 IR"作为参照样例。

**交付物**:`scripts/ir_scaffold.py`、`SKILL.md`(增补探索小节)、`ir/examples/demo_login.ir.json`(若 F1 未建)。

**DoD 验收**:
```bash
python $S/scripts/ir_scaffold.py --name "登录-正常登录" --feature 登录 --base http://localhost:8000 > /tmp/scaffold.ir.json
python $S/scripts/validate_ir.py /tmp/scaffold.ir.json        # 骨架即合法
python $S/scripts/validate_ir.py $S/ir/examples/demo_login.ir.json
python $S/scripts/codegen.py $S/ir/examples/demo_login.ir.json --lang both --out /tmp/f2out
# demo_login 走 F1 回放应全绿
```
- [ ] 脚手架输出通过 schema 校验
- [ ] demo 黄金 IR 校验 + codegen + 回放全绿
- [ ] SKILL.md 探索小节包含 locator 选择优先级与 expect 插入规则

**禁止**:不要在脚本里"假装"做 LLM 探索(探索是 agent 职责);脚手架只产模板不臆造定位器。

---

### F3 — ③ 前端 JS 代码覆盖

**范围**:回放时采集被测前端的 JS 代码覆盖,产出 lcov/HTML。两端实现 + 统一转换。

**策略**:
- **TS**:用 Playwright 内置 `page.coverage.startJSCoverage()/stop()`(Chromium),收集 V8 覆盖。
- **Python**:Playwright Python 无内置 coverage → 用 CDP `Profiler.startPreciseCoverage`/`takePreciseCoverage`(可经 dp-cli 或直接 CDP);产出 V8 覆盖。
- **统一**:用 `monocart-coverage-reports`(或 `v8-to-istanbul`)把 V8 → lcov/Istanbul,出一份语言无关报告。
- 放在 `runner/` 的回放流程里,产物落 `runner/coverage/`。

**交付物**:`runner/coverage/*`(采集 + 转换脚本/配置)、文档片段。

**DoD 验收**:
```bash
# TS 路径:回放并采集
cd runner/typescript && npx playwright test  # 配置里启用 coverage
ls runner/coverage/*.info || ls runner/coverage/lcov.info   # 产出 lcov
# Python 路径:同样产出 V8/lcov
```
- [ ] 至少一种语言回放后产出可读的代码覆盖报告(lcov 或 HTML)
- [ ] 报告中能看到 demo 站点脚本的行覆盖
- [ ] 文档说明两端启用方式

**禁止**:不把覆盖"估算"出来——必须真实采集。

---

### F4 — 三层覆盖统一报告

**范围**:把 ① 用例(coverage.py cases)、② UI(coverage.py ui)、③ 代码(F3)汇总成一份报告。

**策略**:`scripts/coverage.py` 增加 `report` 子命令,聚合三层指标 → 输出 `coverage-summary.json` + `coverage-summary.md`。

**交付物**:`coverage.py`(新增 report 子命令)、`tests/` 对应单测。

**DoD 验收**:
```bash
python $S/scripts/coverage.py report --cases-dir <md> --ir-dir <ir> --snapshot <snap.json> [--code-lcov runner/coverage/lcov.info] --out /tmp/rep
cat /tmp/rep/coverage-summary.md
python -m pytest $ROOT/tests/ -q
```
- [ ] 产出含①②(③ 有数据则含)的 JSON + Markdown 报告
- [ ] 新增子命令有单测,`tests/` 全绿
- [ ] 现有 coverage 子命令不回归

---

### F5 — codegen 增强

**范围**:扩展生成能力:页面对象模式(Python 侧对接 pwtest 约定)、参数化/数据驱动、补齐更多 action(upload/drag/scroll)与 expect(contains_text/attr 存在性等)。

**策略**:先扩 IR schema(向后兼容,新字段可选)→ 再扩 codegen 两端 → 同步 reference 文档。每加一种能力配一条单测(Python+TS 各断言)。

**交付物**:`ir/schema.json`、`codegen.py`、`reference/*.md`、`tests/test_codegen.py`(新增用例)。

**DoD 验收**:
```bash
python -m pytest $ROOT/tests/ -q          # 含新增 + 旧用例
python $S/scripts/validate_ir.py $S/ir/examples/*.ir.json
python $S/scripts/codegen.py $S/ir/examples/*.ir.json --lang both --out /tmp/f5
python -m py_compile /tmp/f5/python/tests/*.py
```
- [ ] 新增能力 Python+TS 各有断言用例,全绿
- [ ] schema 向后兼容(旧示例仍校验通过)
- [ ] 生成的 Python 全部可编译

**禁止**:不得破坏现有 IR 的生成结果(回归)。

---

### F6 — 失败自愈回路

**范围**:回放失败时,SKILL.md 定义"取当前 snapshot + 报错 → 判断用例/脚本/真 bug → 重定位或上报"的剧本;提供一个把失败定位信息结构化的助手(可选)。

**策略**:以 SKILL.md 剧本为主;助手脚本只做信息整理,不替代 agent 决策。

**DoD 验收**:对一个"故意写错 locator"的 IR,执行剧本后能定位到失败步骤并给出修正建议(产出修正后 IR 且回放转绿),或明确判定为真 bug。
- [ ] 注入可控失败场景,剧本能产出可执行的下一步(修正/判定)
- [ ] SKILL.md 自愈小节清晰

---

### F7 — Claude Code plugin 正式化

**范围**:完善 `.claude-plugin/plugin.json`(声明 skills 等 components);可选新增斜杠命令(如 `/foxtest-gen`);提供 marketplace 条目与安装文档。

**策略**:遵循 Claude Code plugin 规范;skill 路径保持 `skills/foxtest/`;不破坏 skill 的独立 symlink 能力。

**DoD 验收**:
```bash
python -c "import json,sys; json.load(open('.claude-plugin/plugin.json')); print('plugin.json OK')"
test -f skills/foxtest/SKILL.md && echo "skill 可被发现"
```
- [ ] plugin.json 合法且声明了 skill component
- [ ] 安装/启用文档可复制执行
- [ ] skill 仍可单独 symlink 到 `~/.claude/skills/` 生效

**禁止**:不臆造未验证的 plugin 字段;不确定的规范点先查官方文档再写。

---

### F8 — foxtest 仓库 CI

**范围**:`.github/workflows/ci.yml` 跑 `tests/`(Python 脚本单测);可选加生成脚本的冒烟(codegen + validate)。

**DoD 验收**:YAML 合法,本地 `pytest tests/ -q` 全绿;workflow 步骤与之一致。
- [ ] `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` 通过
- [ ] CI 步骤包含安装依赖 + `pytest tests/`

---

## 4. 里程碑

- **M-Run(F1+F2)**:✅ 已完成 - 打通"用例 → IR → 双语言脚本 → 真实回放绿"
- **M-Cov(F3+F4)**:✅ 已完成 - 三层覆盖可量化输出
- **M-Scale(F5+F6)**:✅ 已完成 - 生成能力增强 + 自愈，可上规模
- **M-Dist(F7+F8)**:✅ 已完成 - plugin 正式化 + CI，可分发可持续

---

## 5. 风险与对策

| 风险 | 对策 |
|---|---|
| 执行方私改 codegen 契约导致双语言漂移 | 契约改动必须先改 schema + 单测;DoD 强制 `py_compile` + 断言 |
| agentic 探索不稳定 | 用 `ref:N` 收敛动作;黄金 IR 作参照;产出物必须 validate+回放绿 |
| 覆盖被"估算"而非实采 | F3/F4 的 DoD 要求真实回放产出 lcov |
| plugin 规范臆测 | F7 要求不确定先查官方文档 |
| 引入未声明依赖 | 每单交付物列依赖;CI 安装即验证 |

---

## 6. 派单方式(给大脑用)

每个任务都有**独立派单文件** `F<x>_INSTRUCTIONS.md`(含范围/精确文件内容/DoD/禁止项/前置依赖预检)。
指令模板:
> 按 `F<x>_INSTRUCTIONS.md` 执行,完成后贴出「DoD 验收」全部命令的实际输出。
> 约束:不动其它任务范围、不破坏现有资产、发现疑似 bug 停下报告。

**依赖序提醒**:虽已全部派出,执行仍建议按依赖推进——
`F1 → F2 → (F3 ∥ F5) → F4 → F6 → F7 → F8`。
每个派单文件头部有「前置依赖 + 预检命令」,执行 AI 跑前自检前置是否就绪。

执行方回报后,大脑用同一组 DoD 命令**统一实测验收**,通过才更新本文件状态。

### 派单文件清单
| 任务 | 派单文件 | 状态 |
|---|---|---|
| F1 回放脚手架 | `F1_INSTRUCTIONS.md` | ✅ 已完成 |
| F2 AI 探索循环 | `F2_INSTRUCTIONS.md` | ✅ 已完成 |
| F3 代码覆盖 | `F3_INSTRUCTIONS.md` | ✅ 已完成 (已修补) |
| F4 覆盖统一报告 | `F4_INSTRUCTIONS.md` | ✅ 已完成 |
| F5 codegen 增强 | `F5_INSTRUCTIONS.md` | ✅ 已完成 |
| F6 失败自愈 | `F6_INSTRUCTIONS.md` | ✅ 已完成 |
| F7 plugin 正式化 | `F7_INSTRUCTIONS.md` | ✅ 已完成 |
| F8 仓库 CI | `F8_INSTRUCTIONS.md` | ✅ 已完成 |
