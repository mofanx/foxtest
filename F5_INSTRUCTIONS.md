# F5 派单:codegen 增强(交给执行 AI)

> 目标:扩展生成能力——更多 action/expect、可选页面对象模式、参数化。
> `$ROOT` = foxtest 仓库根,`$S = $ROOT/skills/foxtest`。

## 前置依赖
- **F1 已完成**(用于回放验证新生成代码)。
- 预检:`python -m pytest $ROOT/tests/ -q`(现有 9 测试应全绿)

## 范围(分批,每批配单测)
1. **新增 action**:`upload`(set_input_files / setInputFiles)、`drag`(drag_to / dragTo)、`scroll`(mouse.wheel)。
2. **新增 expect.type**:`contains_text`(to_contain_text / toContainText)、`attr_exists`、`enabled`/`disabled`。
3. **可选页面对象模式**:codegen 增加 `--style pageobject`(Python 侧对接 pwtest 约定:每个 feature 一个 PO 类),默认仍是 `flat`。
4. 同步更新 `reference/ir-schema.md`、`reference/locator-map.md` 与 schema。

## 实施纪律(关键)
- **先改 schema(向后兼容,新字段/枚举值全部可选)→ 再改 codegen 两端 → 再补单测**。
- 每新增一种 action/expect,`tests/test_codegen.py` 必须**同时**有 Python 与 TS 的断言用例。
- 旧示例(login/search/demo_login)生成结果**不得回归**。

## DoD 验收
```bash
python -m pytest $ROOT/tests/ -q                       # 含新增 + 旧用例,全绿
python $S/scripts/validate_ir.py $S/ir/examples/*.ir.json
python $S/scripts/codegen.py $S/ir/examples/*.ir.json --lang both --out /tmp/f5
python -m py_compile /tmp/f5/python/tests/*.py          # 生成的 Python 全部可编译
# 若实现了 pageobject:
python $S/scripts/codegen.py $S/ir/examples/demo_login.ir.json --lang py --style pageobject --out /tmp/f5po
python -m py_compile /tmp/f5po/python/tests/*.py
```
**通过标准:**
- [ ] 每个新增 action/expect 都有 Python+TS 断言用例,`tests/` 全绿
- [ ] schema 向后兼容(旧 3 个示例仍校验通过)
- [ ] 生成的 Python 全部可编译
- [ ] (若做)pageobject 模式可生成且可编译;默认仍 flat 不变

## 禁止事项
- 不破坏现有 IR 的生成结果(回归即失败)。
- 新字段一律可选,不得让旧 IR 失效。

## 交付物
1. `$S/ir/schema.json`、`$S/scripts/codegen.py`、`$S/reference/*.md`
2. `$ROOT/tests/test_codegen.py`(新增用例)
3. (可选)pageobject 模板;DoD 输出 + 勾选
