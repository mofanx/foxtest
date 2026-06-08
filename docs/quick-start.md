# 快速开始示例

本指南通过一个完整的示例，带你体验 foxtest 的核心功能。

## 场景：登录功能测试

我们将为一个登录页面生成自动化测试。

## 步骤 1: 创建 IR

使用脚手架生成 IR 模板：

```bash
python skills/foxtest/scripts/ir_scaffold.py \
  --name "用户登录" \
  --feature "用户认证" \
  --base http://localhost:8000 \
  --intent "填写用户名" \
  --intent "填写密码" \
  --intent "点击登录按钮" \
  --intent "验证跳转到首页" > login.ir.json
```

这会生成：

```json
{
  "name": "用户登录",
  "feature": "用户认证",
  "baseURL": "http://localhost:8000",
  "steps": [
    {"action": "goto", "url": "/", "comment": "TODO: 替换为实际页面路径"},
    {"action": "fill", "locator": {"by": "role", "role": "TODO", "name": "TODO"}, "value": "TODO", "comment": "填写用户名"},
    {"action": "fill", "locator": {"by": "role", "role": "TODO", "name": "TODO"}, "value": "TODO", "comment": "填写密码"},
    {"action": "click", "locator": {"by": "role", "role": "TODO", "name": "TODO"}, "comment": "点击登录按钮"},
    {"action": "expect", "type": "TODO", "comment": "验证跳转到首页"}
  ]
}
```

## 步骤 2: 填充 IR

根据实际页面结构，填充 locator 和具体值：

```json
{
  "name": "用户登录",
  "feature": "用户认证",
  "baseURL": "http://localhost:8000",
  "steps": [
    {"action": "goto", "url": "/index.html"},
    {"action": "fill", "locator": {"by": "label", "value": "用户名"}, "value": "testuser"},
    {"action": "fill", "locator": {"by": "label", "value": "密码"}, "value": "<secret:TEST_PASSWORD>"},
    {"action": "click", "locator": {"by": "role", "role": "button", "name": "登录"}},
    {"action": "expect", "type": "url_contains", "value": "/dashboard"}
  ]
}
```

> **注意**: 敏感值使用 `<secret:ENV_NAME>` 占位，运行时从环境变量读取

## 步骤 3: 校验 IR

```bash
python skills/foxtest/scripts/validate_ir.py login.ir.json
```

输出：`[OK] login.ir.json`

## 步骤 4: 生成测试脚本

```bash
# 生成 Python 测试
python skills/foxtest/scripts/codegen.py login.ir.json --lang py --out tests/

# 或生成 TypeScript 测试
python skills/foxtest/scripts/codegen.py login.ir.json --lang ts --out tests/

# 或同时生成双语言
python skills/foxtest/scripts/codegen.py login.ir.json --lang both --out tests/
```

## 步骤 5: 运行测试

### Python 端

```bash
# 设置环境变量
export TEST_PASSWORD=mypassword

# 运行测试
pytest tests/test_login.py
```

### TypeScript 端

```bash
# 设置环境变量
export TEST_PASSWORD=mypassword

# 运行测试
npx playwright test
```

## 完整示例

查看 `skills/foxtest/ir/examples/` 目录中的完整示例：

- `demo_login.ir.json` - demo 站点登录测试
- `login.ir.json` - 通用登录测试
- `search.ir.json` - 搜索功能测试
- `navigation.ir.json` - 页面导航测试

## 下一步

- 查看 [SKILL.md](../skills/foxtest/SKILL.md) 了解 AI 协作工作流
- 查看 [ir-schema.md](../skills/foxtest/reference/ir-schema.md) 了解 IR 完整字段
- 查看 [locator-map.md](../skills/foxtest/reference/locator-map.md) 了解定位器选择优先级
