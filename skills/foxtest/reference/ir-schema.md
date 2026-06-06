# IR 字段说明(完整 schema 见 ir/schema.json)

IR = 一条测试用例的语言无关表示。顶层:

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✓ | 用例名(→ 测试函数名/标题) |
| `feature` |  | 功能模块,用于覆盖分组 |
| `baseURL` |  | 基础 URL;`step.url` 以 `/` 开头时自动拼接 |
| `tags` |  | 标签数组(→ pytest marker / TS 标题 @tag) |
| `steps` | ✓ | 步骤数组 |

## step.action

| action | 必填字段 | 含义 |
|---|---|---|
| `goto` | `url` | 打开页面 |
| `click` / `dblclick` / `hover` / `check` / `uncheck` | `locator` | 元素操作 |
| `fill` / `type` | `locator`, `value` | 输入 |
| `select` | `locator`, `value` | 下拉选择 |
| `press` | `key`(可带 `locator`) | 按键 |
| `wait` | `ms` | 固定等待 |
| `expect` | `type`(+对应字段) | 断言 |

## expect.type

| type | 字段 | Playwright 断言 |
|---|---|---|
| `url_contains` / `url_eq` | `value` | toHaveURL |
| `title_contains` | `value` | toHaveTitle |
| `text_visible` | `value` | getByText(...).toBeVisible |
| `element_visible` / `element_hidden` | `locator` | toBeVisible / toBeHidden |
| `value_eq` | `locator`, `value` | toHaveValue |
| `count_eq` | `locator`, `count` | toHaveCount |
| `attr_eq` | `locator`, `attr`, `value` | toHaveAttribute |

## 约定
- 敏感值用 `<secret:ENV_NAME>` 占位 → codegen 生成读环境变量的代码(Python `os.environ`,TS `process.env`),不落明文。
- locator 字段见 `locator-map.md`。
