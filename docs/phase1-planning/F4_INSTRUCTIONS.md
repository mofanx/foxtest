# F4 派单:三层覆盖统一报告(交给执行 AI)

> 目标:把 ① 用例覆盖、② UI 元素覆盖、③ 代码覆盖(F3 的 lcov)汇总成一份报告。
> `$ROOT` = foxtest 仓库根,`$S = $ROOT/skills/foxtest`。

## 前置依赖
- **F2、F3 已完成**(② 已有数据来源;③ 能产出 lcov)。F3 缺失时,`report` 应对代码覆盖优雅缺省(标 N/A),不报错。
- 预检:`python -c "import sys; sys.path.insert(0,'$S/scripts'); import coverage; print('ok')"`

## 范围
- 给 `$S/scripts/coverage.py` 增加 `report` 子命令:聚合 ①②(③ 有 lcov 则纳入)→ 输出
  `coverage-summary.json` + `coverage-summary.md`。不改动现有 `cases` / `ui` 子命令行为。

## report 子命令规格
- 参数:`--cases-dir`、`--ir-dir`、`--snapshot`、`--code-lcov`(可选)、`--out`(目录)。
- 复用现有 `collect_cases`/`collect_ir_names`/`extract_universe`/`ir_signatures` 等函数计算 ①②。
- ③:若给了 `--code-lcov`,解析 lcov 的 LH/LF(命中行/总行)算行覆盖率;未给则记 `null`/"N/A"。
- 产物:
  - `coverage-summary.json`:`{"cases":{...}, "ui":{...}, "code":{...或null}}`
  - `coverage-summary.md`:三层指标的可读表格 + 盲区清单摘要。

## DoD 验收
```bash
# 构造最小输入跑 report(可用 F1 demo 的 IR + 一个 snapshot.json)
python $S/scripts/coverage.py report \
  --cases-dir <md目录> --ir-dir $S/ir/examples \
  --snapshot /tmp/snap.json [--code-lcov $ROOT/runner/coverage/lcov.info] --out /tmp/rep
cat /tmp/rep/coverage-summary.md
test -f /tmp/rep/coverage-summary.json && echo "JSON 产出 OK"
# 回归 + 新单测
python -m pytest $ROOT/tests/ -q
```
**通过标准:**
- [ ] 产出 `coverage-summary.json` 与 `coverage-summary.md`,含 ①②(③ 有数据则含,无则 N/A)
- [ ] `cases` / `ui` 子命令行为不回归
- [ ] `report` 有单测,`tests/` 全绿

## 禁止事项
- 不改 `cases`/`ui` 已有输出格式(只新增 `report`)。
- 代码覆盖必须来自真实 lcov,不估算。

## 交付物
1. `$S/scripts/coverage.py`(新增 report)
2. `$ROOT/tests/test_coverage_report.py`
3. 示例报告产物 + DoD 输出 + 勾选
