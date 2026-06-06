# a11y `ref:N` → IR locator → Playwright 定位器 映射

`dp snapshot` 为每个交互/内容节点分配 `ref:N`,并附带 `role` / `name` / `locator`。
把它落进 IR 的 `locator` 时,**优先用语义定位**(role/label/testid),css/xpath 仅兜底。

| IR locator | Python | TypeScript | 适用 |
|---|---|---|---|
| `{by:"role", role, name}` | `page.get_by_role(role, name=...)` | `page.getByRole(role, { name })` | 按钮/链接/输入框,首选 |
| `{by:"label", value}` | `page.get_by_label(...)` | `page.getByLabel(...)` | 表单项关联 label |
| `{by:"placeholder", value}` | `page.get_by_placeholder(...)` | `page.getByPlaceholder(...)` | 输入框占位符 |
| `{by:"text", value}` | `page.get_by_text(...)` | `page.getByText(...)` | 文本元素 |
| `{by:"testid", value}` | `page.get_by_test_id(...)` | `page.getByTestId(...)` | 有 data-testid |
| `{by:"alt", value}` | `page.get_by_alt_text(...)` | `page.getByAltText(...)` | 图片 |
| `{by:"title", value}` | `page.get_by_title(...)` | `page.getByTitle(...)` | title 属性 |
| `{by:"css", value}` | `page.locator(value)` | `page.locator(value)` | 兜底 |
| `{by:"xpath", value}` | `page.locator("xpath="+value)` | `page.locator("xpath="+value)` | 兜底 |

可选修饰:`exact`(精确匹配,role/label/text)、`nth`(命中多个时取第 n 个,0 基)。

## 从 snapshot 选 locator 的优先级
1. 节点有 `role` + 有意义的 `name` → `role`
2. 输入类元素有关联 label → `label`,有 placeholder → `placeholder`
3. 有 `data-testid` → `testid`
4. 纯文本元素 → `text`
5. 以上都不稳定 → 用 snapshot 给的 `locator`(css/xpath)兜底
