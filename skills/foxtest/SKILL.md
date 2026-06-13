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

### 步骤 0 — 架构适配（可选）

当用户需要适配现有项目架构时，通过自然语言告知参考文件：

**用户提供参考**：
```
用户："参考 tests/test_login.py 生成注册页面测试"
用户："我的项目使用 POM 模式，BasePage 在 pages/base.py"
```

**大模型操作**：
1. 使用 `read_file` 读取用户指定的参考文件
2. **大模型直接分析代码**：
   - 识别导入语句 → 判断是否使用 POM
   - 识别类继承 → 提取基类名称
   - 识别命名模式 → 提取命名规范
   - 识别导入风格 → 判断 absolute/relative
3. **将架构信息写入 IR**：
```json
{
  "name": "注册测试",
  "architecture": {
    "mode": "pom",
    "language": "python",
    "base_class": "BasePage",
    "page_pattern": "{name}Page",
    "import_style": "relative",
    "pages_path": "pages",
    "page_class": "LoginPage",
    "method_mappings": {
      "goto": "navigate",
      "fill": {
        "用户名": "fill_username",
        "密码": "fill_password"
      },
      "click": {
        "登录": "click_login_button"
      }
    }
  },
  "steps": [...]
}
```
4. 调用 codegen：`python $SKILL/scripts/codegen.py generated/test.ir.json`

**核心原则**：
- IR 是单一事实源，所有配置信息保存在 IR 中
- 大模型负责分析和决策（利用其代码理解能力）
- codegen 负责根据 IR 生成代码（固定框架）
- 无需命令行参数传递架构配置

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
  --intent "填写用户名" --intent "点击登录" > generated/login.ir.json
```
**目录约定**:所有用户生成的 IR 文件和测试脚本统一放在 `generated/` 目录中,保持工作目录整洁。

产出:一份**真实跑通**的 IR(`<case>.ir.json`)。敏感值用 `<secret:ENV_NAME>` 占位,不要写明文密码。

IR 字段全集见 `reference/ir-schema.md`;ref→Playwright 定位器映射见 `reference/locator-map.md`。

### 步骤 3 — 校验 IR

```bash
python $SKILL/scripts/validate_ir.py generated/<case>.ir.json
```

**POM 模式额外校验**：
如果使用 POM 模式，大模型需要确保 IR 包含完整的架构配置：

- `architecture.mode`: "pom"
- `architecture.language`: "py" 或 "ts"
- `architecture.page_class`: 页面类名（如 "LoginPage"）
- `architecture.method_mappings`: 方法映射（必需）
  - `goto`: 导航方法名
  - `fill`: 填充方法映射（按 locator value → 方法名）
  - `click`: 点击方法映射（按 locator value → 方法名）

**校验流程**：
1. 大模型根据参考项目分析生成 IR
2. 运行 `validate_ir.py` 校验 IR 格式
3. 如果 POM 模式缺少 `method_mappings`，大模型根据参考项目补充
4. 确保所有必需字段完整后进入下一步

### 步骤 4 — 生成双语言脚本
```bash
python $SKILL/scripts/codegen.py generated/<case>.ir.json --lang both
# 产出 generated/python/tests/test_<case>.py 与 generated/typescript/tests/<case>.spec.ts
```
**默认输出**:如果不指定 `--out`,脚本默认生成到当前目录的 `generated/` 文件夹。
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
python $SKILL/scripts/coverage.py cases --cases-dir <md目录> --ir-dir generated/

# ② UI 元素覆盖:页面可交互元素中有多少被脚本操作过
#   先用 dp 抓全集:dp snapshot --format json > snapshot.json
python $SKILL/scripts/coverage.py ui --snapshot snapshot.json --ir generated/<case>.ir.json [...]

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

---

## 浏览器配置

### 默认配置

生成的 Playwright 脚本**默认使用 Playwright 安装的 Chromium 浏览器**。这是最稳定可靠的选择，因为：

- Chromium 随 Playwright 自动安装，版本受控
- 跨平台行为一致
- 支持所有 Playwright 特性（包括 coverage API）

### 使用系统浏览器（可选）

如需使用系统安装的 Chrome/Chromium，可修改对应配置：

**TypeScript (`playwright.config.ts`)**:
```ts
use: {
  channel: 'chrome',  // 或 'msedge' 等
}
```

**Python (`conftest.py` 或测试文件)**:
```python
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "channel": "chrome"}
```

### 安装浏览器

首次使用前需安装浏览器：
```bash
# 安装 Playwright Chromium（推荐）
npx playwright install chromium

# 安装系统浏览器支持（可选）
npx playwright install chrome
```

### 限制说明

- **代码覆盖功能**：使用系统 Chrome 时，部分 CDP/coverage API 可能不可用
- **CI 环境**：推荐使用默认 Chromium，避免依赖系统浏览器

---
