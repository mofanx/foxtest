---
name: foxtest
description: AI 驱动的 Web 端到端测试生成与覆盖度量。当用户需要把自然语言/Markdown 测试用例转成可运行的自动化脚本、为网站自动生成 Playwright 测试(Python 或 TypeScript)、验证测试覆盖(用例覆盖 / UI 元素覆盖 / 前端代码覆盖)、或基于页面探索自动产出回归测试时,使用此技能。配合 dp-cli 技能完成浏览器感知与操作。
---

# foxtest

把**自然语言测试用例**转成**可运行的 Playwright 脚本(Python + TypeScript)**,并度量覆盖。

核心理念:**单一语言无关中间表示(IR)** 作为事实源。AI 负责"理解用例 + 探索页面 + 产出 IR";确定性脚本负责"IR → 双语言代码 + 覆盖计算"。

```
NL/Markdown 用例 → (AI+dp-cli 探索) → IR(JSON) → codegen → Python/TS 脚本 → 回放 + 覆盖
```

约定:本技能目录为 `$SKILL`;脚本在 `$SKILL/scripts/`,IR schema 在 `$SKILL/ir/schema.json`。
运行脚本统一用 `python $SKILL/scripts/<name>.py ...`。

---

## 何时使用

- "把这些测试用例生成自动化脚本"
- "给这个网站生成 Playwright 测试 / 同时要 Python 和 TypeScript"
- "看看测试覆盖了多少页面元素 / 多少代码"
- "基于页面探索帮我补回归测试"

---

## 工作流

### 步骤 1 — 解析用例(AI)
读取用户的 Markdown/自然语言用例,逐条结构化为:用例名、所属功能、前置 URL、操作步骤、预期结果。
一个用例 → 一份待填充的 IR。

### 步骤 2 — 探索页面并产出 IR(AI + dp-cli)

**调用 `dp-cli` 技能**完成感知与操作。每一步循环:
1. `dp open <url>`(或 `--auto-connect` 复用已登录浏览器)
2. `dp snapshot` → 得到带 `ref:N` 的 a11y 视图(role/name/locator)
3. 依据用例决定下一步动作,执行 `dp click ref:N` / `dp fill ref:N "值"` / `dp press` 等,用返回的 JSON 校验是否成功
4. **把动作落进 IR**:优先用 snapshot 给出的 **role+name / label / testid** 作为 locator(语义定位,抗 DOM 漂移),css/xpath 仅兜底
5. 在"预期结果"处插入 `expect` 步骤(url_contains / text_visible / element_visible / count_eq 等)

#### Locator 选择优先级
从 `dp snapshot` 的 `ref:N` 选择定位器时,按以下优先级(详见 `reference/locator-map.md`):
1. **role + name**: 最优,语义强且抗 DOM 变化 (如 `{"by":"role","role":"button","name":"登录"}`)
2. **label**: 表单元素的首选 (如 `{"by":"label","value":"用户名"}`)
3. **placeholder**: 次优表单定位 (如 `{"by":"placeholder","value":"请输入邮箱"}`)
4. **testid**: 测试专用属性,稳定 (如 `{"by":"testid","value":"submit-btn"}`)
5. **text**: 文本内容,用于链接/标题 (如 `{"by":"text","value":"注册"}`)
6. **css / xpath**: 仅作为兜底,避免使用

#### Expect 步骤类型映射
根据预期结果选择对应的 `expect` 类型:
- 预期 URL 变化 → `url_contains` / `url_eq`
- 预期页面标题 → `title_contains`
- 预期某文本可见 → `text_visible`
- 预期某元素可见/隐藏 → `element_visible` / `element_hidden`
- 预期输入框值 → `value_eq`
- 预期元素数量 → `count_eq`
- 预期元素属性 → `attr_eq`

#### 敏感值处理
**严禁明文密码**:所有敏感值(密码、token、密钥等)必须用 `<secret:ENV_NAME>` 占位,运行时从环境变量读取。
- 错误示例: `"value": "mypassword123"`
- 正确示例: `"value": "<secret:APP_PASSWORD>"`

#### IR 脚手架助手
为降低 agent 出错率,可先用脚手架生成 IR 骨架:
```bash
python $SKILL/scripts/ir_scaffold.py --name "登录-正常登录" --feature 登录 --base http://localhost:8000 \\
  --intent "填写用户名" --intent "点击登录" > login.ir.json
```
脚手架产出合法的 IR 结构(steps 含 goto + 占位步骤),locator 待 agent 根据实际探索填充。

产出:一份**真实跑通**的 IR(`<case>.ir.json`)。敏感值用 `<secret:ENV_NAME>` 占位,不要写明文密码。

IR 字段全集见 `reference/ir-schema.md`;ref→Playwright 定位器映射见 `reference/locator-map.md`。

### 步骤 3 — 校验 IR
```bash
python $SKILL/scripts/validate_ir.py <case>.ir.json
```
不通过则回到步骤 2 修正,不要带着非法 IR 往下走。

### 步骤 4 — 生成双语言脚本
```bash
python $SKILL/scripts/codegen.py <case>.ir.json --lang both --out out/
# 产出 out/python/tests/test_<case>.py 与 out/typescript/tests/<case>.spec.ts
```
- Python:`pytest + playwright`(页面对象/Allure 规范可对接 pwtest 技能)
- TypeScript:`@playwright/test`

### 步骤 5 — 回放并度量覆盖

#### 回放失败自愈流程
当回放失败时,执行以下自愈剧本:

1. **捕获失败信息**:
   - 记录失败的步骤序号和 locator
   - 捕获完整错误信息
   - 重新执行 `dp snapshot` 获取当前页面状态

2. **失败分诊** (三类):
   - **定位漂移**: 元素仍在页面中,但 locator 的 role/name/值发生变化
     - 从新 snapshot 中查找语义相似的元素 (role+name 匹配)
     - 更新 IR 中对应步骤的 locator
     - 重新 codegen + 回放
   - **脚本/用例问题**: 步骤顺序错误、预期值错误、逻辑错误
     - 修正 IR 的步骤顺序或 expect 值
     - 重新 codegen + 回放
   - **疑似真 bug**: 元素确实不存在、页面行为异常、功能缺陷
     - 停止自愈,产出缺陷报告
     - 包含:失败步骤、错误信息、snapshot、IR

3. **重试机制**:
   - 最多重试 2 次
   - 每次重试前必须重新获取 snapshot
   - 超过重试上限仍失败 → 判定为真 bug

4. **成功判据**:
   - 修正 IR 后 codegen + 回放全绿
   - 或者明确判定为真 bug 并产出报告

#### 覆盖度量
```bash
# ① 用例覆盖:有多少用例生成了 IR / 通过
python $SKILL/scripts/coverage.py cases --cases-dir <md目录> --ir-dir <ir目录>

# ② UI 元素覆盖:页面可交互元素中有多少被脚本操作过
#   先用 dp 抓全集:dp snapshot --format json > snapshot.json
python $SKILL/scripts/coverage.py ui --snapshot snapshot.json --ir <case>.ir.json [...]

# ③ 前端代码覆盖(需启用 CDP 覆盖采集)
#   Python 端:使用 coverage_collector fixture 采集后转换
#   见 runner/COVERAGE_README.md
```

---

## 关键原则

1. **IR 是唯一事实源**:不要让模型直接手写 Python/TS——一律走 `codegen.py`,保证双语言一致、可复现。
2. **语义定位优先**:locator 用 role/label/testid;css/xpath 仅兜底。
3. **黄金轨迹必须真跑通**:IR 来自真实探索成功的步骤序列,而非凭空臆测。
4. **不落明文密钥**:敏感值用 `<secret:ENV>`,运行时读环境变量。
5. **浏览器能力复用 dp-cli**:本技能不直接驱动浏览器,统一通过 dp-cli。

---

## 依赖
- `dp-cli` 技能(浏览器感知/操作)
- Python:`pytest`、`playwright`(回放);`jsonschema`(可选,IR 校验)
- TypeScript:`@playwright/test`
