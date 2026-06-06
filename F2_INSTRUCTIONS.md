# F2 派单:M1 AI 探索循环落地(交给执行 AI)

> 目标:把"自然语言用例 → dp-cli 探索 → 产出 IR"从描述细化为可复现剧本,并提供 IR 脚手架助手。
> 核心智能仍由 agent + dp-cli 完成;脚本只产模板,不臆造定位器。
> `$ROOT` = foxtest 仓库根,`$S = $ROOT/skills/foxtest`。

## 前置依赖
- **F1 已完成**(runner 脚手架 + demo 站点 + `demo_login.ir.json` 可回放)。
- 预检:
```bash
test -f $S/ir/examples/demo_login.ir.json && test -d $ROOT/runner/demo-site && echo "F1 就绪" || echo "缺 F1,先做 F1"
```

## 范围
1. 新增 `$S/scripts/ir_scaffold.py`:据用例元信息产出**合法的 IR 骨架**(steps 仅含 goto + 注释占位,locator 待 agent 填)。
2. 增补 `$S/SKILL.md` 的「步骤 2 探索」小节:把 ref:N → locator 选择、expect 插入、secret 占位写成明确规则。
3. 提供/复用 demo 黄金 IR(F1 的 `demo_login.ir.json` 即可作为参照样例)。
4. 给 `ir_scaffold.py` 配单测。

> 禁止:在脚本里"假装"做 LLM 探索;脚手架不得编造 css/role/name 等真实定位器(只给占位与注释)。

## ir_scaffold.py 规格
- 参数:`--name`(必填)、`--feature`、`--base`、`--intent`(可重复,每个意图生成一条带注释的占位步骤)。
- 输出(stdout):合法 IR JSON,至少含 `name`、`steps:[{goto}]`;每个 `--intent` 追加一条形如
  `{"action":"click","locator":{"by":"role","role":"TODO","name":"TODO"},"comment":"<intent>"}` 的占位步骤。
- 产出必须能通过 `validate_ir.py`(注意:占位 locator 的 by 必须是合法枚举值,role/name 用 "TODO" 字符串)。

## SKILL.md 探索小节须包含
- 每步循环:`dp snapshot` 取 ref:N → 依用例决定动作 → `dp click/fill ref:N` → 用 JSON 结果校验 → 落 IR。
- locator 选择优先级(引用 `reference/locator-map.md`):role+name > label > placeholder > testid > text > css/xpath 兜底。
- 预期结果 → 对应 `expect` 步骤类型。
- 敏感值写 `<secret:ENV>`,严禁明文。

## DoD 验收
```bash
# 1) 脚手架产出合法 IR
python $S/scripts/ir_scaffold.py --name "登录-正常登录" --feature 登录 --base http://localhost:8000 \
  --intent "填写用户名" --intent "点击登录" > /tmp/scaffold.ir.json
python $S/scripts/validate_ir.py /tmp/scaffold.ir.json

# 2) demo 黄金 IR 端到端仍绿(复用 F1 runner)
python $S/scripts/validate_ir.py $S/ir/examples/demo_login.ir.json
python $S/scripts/codegen.py $S/ir/examples/demo_login.ir.json --lang both --out $ROOT/runner
# 按 F1 的方式回放 python + ts,应全绿

# 3) 脚手架单测
python -m pytest $ROOT/tests/ -q
```
**通过标准:**
- [ ] 脚手架输出通过 schema 校验,且含 goto + 每个 intent 一条占位步骤
- [ ] demo 黄金 IR codegen + 双语言回放全绿
- [ ] `tests/` 全绿(含新增 ir_scaffold 单测)
- [ ] SKILL.md 探索小节含 locator 优先级 + expect 规则 + secret 规则

## 交付物
1. `$S/scripts/ir_scaffold.py`
2. `$S/SKILL.md`(增补探索小节)
3. `$ROOT/tests/test_ir_scaffold.py`
4. DoD 全部命令输出 + 勾选
