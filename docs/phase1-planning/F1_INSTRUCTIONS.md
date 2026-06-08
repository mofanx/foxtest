# F1 派单:回放工程脚手架(交给执行 AI)

> 目标:让 codegen 生成的 Playwright 脚本**真能在本地离线 demo 站点上跑绿**(Python + TypeScript)。
> 角色:执行者,只按本文件创建文件,不改 `skills/foxtest/scripts/codegen.py` 的生成逻辑。
> 仓库根记为 `$ROOT`(= foxtest 仓库根),`$S = $ROOT/skills/foxtest`。
> 完成后必须通过文末「DoD 验收」。

---

## 0. 执行前提
- 先 read:`$S/scripts/codegen.py`(了解输出路径规则:`--out X` → `X/python/tests/` 与 `X/typescript/tests/`)、
  `$S/ir/schema.json`、`$S/ir/examples/login.ir.json`。
- 需要本地有 Node(npm/npx)与 Python;首次跑 Playwright 需 `playwright install chromium`。

---

## 1. 范围(只做这四块)
1. `runner/demo-site/`:离线静态站点(登录页 + dashboard),供真实回放。
2. `runner/python/`:pytest + pytest-playwright 最小工程。
3. `runner/typescript/`:@playwright/test 最小工程(用 webServer 自动起站点)。
4. `$S/ir/examples/demo_login.ir.json`:针对 demo 的可离线回放用例(**不使用 secret**,保证开箱即跑)。

> 禁止:改 `codegen.py`;引入重型框架;demo 站点请求外网。

---

## 2. 要创建的文件(按内容照建)

### 2.1 `runner/demo-site/index.html`
```html
<!doctype html>
<html lang="zh">
<head><meta charset="utf-8"><title>Demo 登录</title></head>
<body>
  <h1>登录</h1>
  <form id="login" onsubmit="location.href='dashboard.html'; return false;">
    <label for="user">用户名</label>
    <input id="user" name="user" />
    <label for="pwd">密码</label>
    <input id="pwd" name="pwd" type="password" />
    <button type="submit">登录</button>
  </form>
  <a href="register.html">注册</a>
</body>
</html>
```

### 2.2 `runner/demo-site/dashboard.html`
```html
<!doctype html>
<html lang="zh">
<head><meta charset="utf-8"><title>Dashboard</title></head>
<body><h1>欢迎</h1><p data-testid="welcome">欢迎回来,admin</p></body>
</html>
```

### 2.3 `runner/demo-site/register.html`(占位,供后续 UI 覆盖演示)
```html
<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><title>注册</title></head>
<body><h1>注册</h1></body></html>
```

### 2.4 `$S/ir/examples/demo_login.ir.json`
```json
{
  "name": "demo-登录跳转",
  "feature": "登录",
  "baseURL": "http://localhost:8000",
  "tags": ["demo", "smoke"],
  "steps": [
    {"action": "goto", "url": "/index.html"},
    {"action": "fill", "locator": {"by": "label", "value": "用户名"}, "value": "admin"},
    {"action": "fill", "locator": {"by": "label", "value": "密码"}, "value": "secret123"},
    {"action": "click", "locator": {"by": "role", "role": "button", "name": "登录"}},
    {"action": "expect", "type": "url_contains", "value": "/dashboard"},
    {"action": "expect", "type": "text_visible", "value": "欢迎"}
  ]
}
```

### 2.5 `runner/python/requirements.txt`
```
pytest>=7.4
pytest-playwright>=0.5
```

### 2.6 `runner/python/pytest.ini`
```ini
[pytest]
testpaths = tests
addopts = -v
```

### 2.7 `runner/typescript/package.json`
```json
{
  "name": "foxtest-runner-ts",
  "private": true,
  "devDependencies": { "@playwright/test": "^1.48.0" },
  "scripts": { "test": "playwright test" }
}
```

### 2.8 `runner/typescript/playwright.config.ts`
```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  use: { headless: true },
  // 自动起本地静态站点(指向 demo-site),TS 端无需手动起服务
  webServer: {
    command: 'python3 -m http.server 8000 --directory ../demo-site',
    url: 'http://localhost:8000/index.html',
    reuseExistingServer: true,
  },
});
```

---

## 3. 生成脚本到 runner
```bash
python $S/scripts/codegen.py $S/ir/examples/demo_login.ir.json --lang both --out runner
# 期望产出:
#   runner/python/tests/test_demo_login.py
#   runner/typescript/tests/demo_login.spec.ts
```

---

## 4. DoD 验收(逐项跑并贴出结果)

```bash
# 0) 校验 demo IR + 生成
python $S/scripts/validate_ir.py $S/ir/examples/demo_login.ir.json
python $S/scripts/codegen.py $S/ir/examples/demo_login.ir.json --lang both --out runner

# 1) Python 回放(需手动起静态服)
cd runner/python
pip install -r requirements.txt
python -m playwright install chromium
( python3 -m http.server 8000 --directory ../demo-site >/tmp/httpd.log 2>&1 & echo $! > /tmp/httpd.pid )
pytest -q ; kill $(cat /tmp/httpd.pid)

# 2) TypeScript 回放(webServer 自动起站点)
cd ../typescript
npm install
npx playwright install chromium
npx playwright test
```

**通过标准:**
- [ ] `validate_ir.py` 对 demo_login 通过
- [ ] codegen 产出 `runner/python/tests/test_demo_login.py` 与 `runner/typescript/tests/demo_login.spec.ts`
- [ ] **Python 回放全绿**(登录→跳转 dashboard→"欢迎" 可见)
- [ ] **TypeScript 回放全绿**
- [ ] demo 站点无任何外网请求(纯本地静态)

---

## 5. 禁止事项
- 不改 `codegen.py` 生成模板。若生成代码跑不通,**停下报告**(附失败用例 + 报错),由大脑决定是否调整契约。
- 不引入数据库/后端;demo 用纯静态 + 前端跳转。
- 不把覆盖率/自愈等后续任务塞进本单。

## 6. 交付物
1. `runner/demo-site/{index,dashboard,register}.html`
2. `runner/python/{requirements.txt,pytest.ini}` + 生成的 `tests/test_demo_login.py`
3. `runner/typescript/{package.json,playwright.config.ts}` + 生成的 `tests/demo_login.spec.ts`
4. `$S/ir/examples/demo_login.ir.json`
5. 第 4 节全部 DoD 命令的实际输出 + 勾选
