# F3-fix 派单:代码覆盖返工(交给执行 AI)

> 背景:F3 验收**不达标**。问题:
>   (a) lcov 只输出已覆盖行、从不输出未覆盖行 → 永远 ~100%,无法发现盲区;SF 指向 HTML、范围→整段行的粗粒度转换、记录重复拼接。
>   (b) TS `startJSCoverage` 实采 0 条目。
>   (c) 覆盖采集代码被**手工写进了生成的 `demo_login.spec.ts`**,违背"IR 单源、产物来自 codegen"。
> 本单目标:让代码覆盖**真实可信(能出现 <100% 并定位未覆盖分支)**,且**不污染 codegen 生成物**。
> `$ROOT` = foxtest 仓库根,`$S = $ROOT/skills/foxtest`。

## 前置依赖
- F1 回放脚手架可用。预检:`test -f $ROOT/runner/typescript/playwright.config.ts && echo ok`

---

## 1. 核心整改要求(三条,缺一不可)

### R1 — 覆盖采集移出生成文件(去手改)
- **生成的测试脚本必须是 codegen 的纯净产物**,不得含任何 `startJSCoverage`/CDP 采集代码。
- 重新用 codegen 生成 `demo_login`,确认生成物里**没有**覆盖逻辑、断言与 IR 一致(`text_visible "欢迎"` → `getByText("欢迎")`,不要改成 testid)。
- 覆盖采集改到**框架层**:
  - **TS**:用全局 fixture / `playwright.config.ts` 的 setup,或一个 `tests/_coverage.setup.ts`,在 fixture 里 `page.coverage.startJSCoverage()` / `stopJSCoverage()`,与具体用例解耦。
  - **Python**:用 `conftest.py` 的 autouse fixture(已有 conftest,完善它),通过 CDP Profiler 采集,与用例解耦。
- 删除 `playwright.config.ts` 里非法的 `use: { coverage: 'all' }`(Playwright 无此选项)。

### R2 — V8→lcov 转换必须输出未覆盖行
- 转换器要遍历 V8 ranges,对 `count==0` 的范围输出 `DA:line,0`,对 `count>0` 输出 `DA:line,<count>`。
- 同一行有多个 range 时,取**最大命中数**(被覆盖优先),避免重复/矛盾的 DA 行。
- 行覆盖率 = 命中行 / (命中+未命中)行,**必须能 <100%**。
- `SF:` 指向真实被测脚本源(内联脚本则映射到 HTML 的准确行区间;若改用外链 `app.js` 更佳,便于精确映射)。

### R3 — 让 demo 存在"必然未覆盖"的分支(可证伪)
- demo 站点的登录脚本里保留**正常登录不会走到**的分支(如 `validateLogin` 的 `password.length<6 → return false`、`alert(...)` 失败分支)。
- demo 用例用合法账号(密码长度≥6)登录成功 → 上述失败分支**不应被覆盖**。
- 因此覆盖报告必须显示这些行 `DA:line,0`,行覆盖率 **< 100%**。

---

## 2. DoD 验收(可证伪,逐项跑并贴输出)

```bash
# 1) 生成物纯净:codegen 产物里不含覆盖代码,断言与 IR 一致
python $S/scripts/codegen.py $S/ir/examples/demo_login.ir.json --lang ts --out $ROOT/runner
grep -q "startJSCoverage\|stopJSCoverage\|Profiler" $ROOT/runner/typescript/tests/demo_login.spec.ts \
  && echo "✗ 生成物仍含覆盖代码(不合格)" || echo "✓ 生成物纯净"
grep -q 'getByText("欢迎")' $ROOT/runner/typescript/tests/demo_login.spec.ts \
  && echo "✓ 断言与 IR 一致" || echo "✗ 断言被篡改"

# 2) 回放并采集覆盖(任一语言;Python 端需起 demo 静态服)
#    TS:
cd $ROOT/runner/typescript && npx playwright test
#    生成 lcov
ls $ROOT/runner/coverage/lcov.info

# 3) ★ 关键:覆盖必须 <100% 且能定位未覆盖分支(在仓库根执行)
python - <<'PY'
data = open("runner/coverage/lcov.info", encoding="utf-8").read()
da = [l for l in data.splitlines() if l.startswith("DA:")]
miss = [l for l in da if l.split(",")[-1] == "0"]
hit = [l for l in da if l.split(",")[-1] != "0"]
print(f"DA 总行={len(da)} 命中={len(hit)} 未命中={len(miss)}")
assert da, "✗ 无 DA 行 → 未采集到覆盖"
assert miss, "✗ 没有任何未覆盖行(DA:line,0) → 覆盖度量不可信(仍是假100%)"
pct = len(hit) / len(da) * 100
print(f"行覆盖率={pct:.1f}%")
assert pct < 100.0, "✗ 行覆盖率=100% → 未体现未覆盖分支"
print("✓ 覆盖真实(存在未覆盖行且 <100%)")
PY

# 4) 三层报告纳入真实代码覆盖
python $S/scripts/coverage.py report --cases-dir <md> --ir-dir $S/ir/examples \
  --snapshot <snap.json> --code-lcov $ROOT/runner/coverage/lcov.info --out /tmp/rep
grep -i "行覆盖" /tmp/rep/coverage-summary.md

# 5) 不回归
python -m pytest $ROOT/tests -q   # 在仓库根目录执行
```

**通过标准:**
- [ ] 生成的 `demo_login.spec.ts` **不含**任何覆盖采集代码,断言与 IR 一致(`getByText("欢迎")`)
- [ ] 覆盖采集在 fixture/config 层完成,功能回放仍 **1 passed**
- [ ] `lcov.info` **同时含 `DA:line,0`(未覆盖)与 `DA:line,>0`(覆盖)**
- [ ] 行覆盖率 **严格 <100%**,且未覆盖行对应 demo 里"登录失败分支"
- [ ] 三层报告 ③ 显示真实(<100%)行覆盖
- [ ] 仓库根 `pytest tests` 全绿

---

## 3. 禁止事项
- **禁止把覆盖代码写进 codegen 生成的测试文件**(R1 红线)。
- **禁止只输出已覆盖行**造成假 100%(R2 红线)。
- 不臆造覆盖数据;不确定的 Playwright/CDP 字段先查官方文档。
- 不破坏现有 31 个单测。

## 4. 交付物
1. 纯净的 codegen 生成物(无覆盖代码)
2. TS/Python 框架层覆盖采集(fixture/config)
3. 修正后的 V8→lcov 转换(输出未覆盖行)
4. demo 站点含"必然未覆盖"分支
5. 第 2 节全部 DoD 输出 + 勾选(尤其第 3 步的断言通过)
