# F6 派单:失败自愈回路(交给执行 AI)

> 目标:回放失败时,定义"取当前 snapshot + 报错 → 判断用例/脚本/真 bug → 重定位或上报"的剧本。
> `$ROOT` = foxtest 仓库根,`$S = $ROOT/skills/foxtest`。

## 前置依赖
- **F2 已完成**(探索循环 + IR 产出已成型)。
- 预检:`grep -q "探索" $S/SKILL.md && echo "F2 就绪"`

## 范围
1. 增补 `$S/SKILL.md` 的「步骤 5 回放/自愈」小节:明确失败分诊与自愈流程。
2. (可选)新增 `$S/scripts/triage.py`:把失败信息(失败步骤、报错、当前 snapshot)整理成结构化诊断,**仅整理信息,不替 agent 决策**。

## SKILL.md 自愈小节须包含
- 失败时:重新 `dp snapshot` → 比对 IR 里失败步骤的 locator 是否还能在快照中定位。
- 分诊三类:
  1. **定位漂移**(元素还在但 locator 失配)→ 用快照里新的 role/name 更新 IR 对应步骤,重跑。
  2. **脚本/用例问题**(步骤顺序、预期错)→ 修正 IR。
  3. **疑似真 bug**(元素确实不存在/行为异常)→ 停下,产出清晰缺陷报告,不强行自愈。
- 自愈以**修改 IR 后重新 codegen+回放转绿**为成功标志;超过 N 次(建议 2)仍失败则上报。

## DoD 验收
```bash
# 构造一个"故意写错 locator"的 IR(基于 demo_login,把按钮 name 改成不存在的值)
# 按 SKILL.md 自愈剧本处理后,应产出修正版 IR 且回放转绿;或明确判定为真 bug。
python $S/scripts/validate_ir.py <修正后 IR>
# (若实现 triage.py)喂入失败信息,产出结构化诊断
python $S/scripts/triage.py --ir <ir> --error "<报错>" --snapshot /tmp/snap.json
```
**通过标准:**
- [ ] SKILL.md 自愈小节含三类分诊 + 重试上限 + 成功判据
- [ ] 对"故意写错 locator"场景,剧本能产出可执行下一步(修正 IR 回放转绿,或判定真 bug)
- [ ] (若做)triage.py 仅整理信息,不臆造修复

## 交付物
1. `$S/SKILL.md`(自愈小节)
2. (可选)`$S/scripts/triage.py` + 单测
3. DoD 演示输出 + 勾选
