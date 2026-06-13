# -*- coding:utf-8 -*-
"""
IR → Playwright 代码生成器(双语言:Python pytest / TypeScript @playwright/test)。

设计:
  - IR 是单一事实源(见 ir/schema.json)。
  - 本模块把同一份 IR 渲染成两种语言;两端共享同一套 locator/expect 语义,
    保证行为一致,差异仅在语法模板。

用法:
  python -m aiwt.codegen ir/examples/login.ir.json --lang both --out out/
"""
import argparse
import json
import re
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# 通用工具
# ─────────────────────────────────────────────────────────────────────────────

def _lit(s: str) -> str:
    """生成字符串字面量(Python 与 TS 均接受 JSON 风格的双引号转义)。"""
    return json.dumps(s, ensure_ascii=False)


_SECRET_RE = re.compile(r"^<secret:([A-Za-z_][A-Za-z0-9_]*)>$")


def _value_expr(value: str, lang: str) -> str:
    """把 value 渲染为代码表达式;支持 <secret:ENV> 读环境变量。"""
    m = _SECRET_RE.match(value or "")
    if m:
        env = m.group(1)
        return f'os.environ[{_lit(env)}]' if lang == "py" else f'process.env[{_lit(env)}]!'
    return _lit(value)


def _slug_ident(name: str) -> str:
    """用例名 → 合法 Python 测试函数名(保留中文,清洗空格/连字符等)。"""
    ident = re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]", "_", name).strip("_")
    if not ident or ident[0].isdigit():
        ident = "case_" + ident
    return ident


def _resolve_url(ir: dict, url: str) -> str:
    base = (ir.get("baseURL") or "").rstrip("/")
    if url.startswith("/") and base:
        return base + url
    return url


# ─────────────────────────────────────────────────────────────────────────────
# locator 渲染
# ─────────────────────────────────────────────────────────────────────────────

def _locator_py(loc: dict) -> str:
    by = loc["by"]
    exact = loc.get("exact")
    nth = loc.get("nth")
    if by == "role":
        args = [_lit(loc["role"])]
        if loc.get("name") is not None:
            args.append(f'name={_lit(loc["name"])}')
        if exact:
            args.append("exact=True")
        expr = f'page.get_by_role({", ".join(args)})'
    elif by == "label":
        expr = f'page.get_by_label({_lit(loc["value"])}{", exact=True" if exact else ""})'
    elif by == "text":
        expr = f'page.get_by_text({_lit(loc["value"])}{", exact=True" if exact else ""})'
    elif by == "placeholder":
        expr = f'page.get_by_placeholder({_lit(loc["value"])})'
    elif by == "testid":
        expr = f'page.get_by_test_id({_lit(loc["value"])})'
    elif by == "alt":
        expr = f'page.get_by_alt_text({_lit(loc["value"])})'
    elif by == "title":
        expr = f'page.get_by_title({_lit(loc["value"])})'
    elif by == "css":
        expr = f'page.locator({_lit(loc["value"])})'
    elif by == "xpath":
        expr = f'page.locator({_lit("xpath=" + loc["value"])})'
    else:
        raise ValueError(f"未知 locator.by: {by}")
    if nth is not None:
        expr += f".nth({nth})"
    return expr


def _locator_ts(loc: dict) -> str:
    by = loc["by"]
    exact = loc.get("exact")
    nth = loc.get("nth")
    if by == "role":
        opts = []
        if loc.get("name") is not None:
            opts.append(f'name: {_lit(loc["name"])}')
        if exact:
            opts.append("exact: true")
        opt_str = f', {{ {", ".join(opts)} }}' if opts else ""
        expr = f'page.getByRole({_lit(loc["role"])}{opt_str})'
    elif by == "label":
        expr = f'page.getByLabel({_lit(loc["value"])}{", { exact: true }" if exact else ""})'
    elif by == "text":
        expr = f'page.getByText({_lit(loc["value"])}{", { exact: true }" if exact else ""})'
    elif by == "placeholder":
        expr = f'page.getByPlaceholder({_lit(loc["value"])})'
    elif by == "testid":
        expr = f'page.getByTestId({_lit(loc["value"])})'
    elif by == "alt":
        expr = f'page.getByAltText({_lit(loc["value"])})'
    elif by == "title":
        expr = f'page.getByTitle({_lit(loc["value"])})'
    elif by == "css":
        expr = f'page.locator({_lit(loc["value"])})'
    elif by == "xpath":
        expr = f'page.locator({_lit("xpath=" + loc["value"])})'
    else:
        raise ValueError(f"未知 locator.by: {by}")
    if nth is not None:
        expr += f".nth({nth})"
    return expr


def _regex_py(substr: str) -> str:
    return f're.compile(r".*{re.escape(substr)}")'


def _regex_ts(substr: str) -> str:
    # 转义用于 RegExp 构造的字符串字面量
    return f'new RegExp(".*" + {_lit(re.escape(substr))})'


# ─────────────────────────────────────────────────────────────────────────────
# 单步渲染
# ─────────────────────────────────────────────────────────────────────────────

def _step_py(ir: dict, step: dict) -> list:
    a = step["action"]
    if a == "goto":
        return [f'page.goto({_lit(_resolve_url(ir, step["url"]))})']
    if a in ("click", "dblclick", "hover", "check", "uncheck"):
        method = {"click": "click", "dblclick": "dblclick", "hover": "hover",
                  "check": "check", "uncheck": "uncheck"}[a]
        return [f'{_locator_py(step["locator"])}.{method}()']
    if a in ("fill", "type"):
        method = "fill" if a == "fill" else "type"
        return [f'{_locator_py(step["locator"])}.{method}({_value_expr(step["value"], "py")})']
    if a == "select":
        return [f'{_locator_py(step["locator"])}.select_option({_value_expr(step["value"], "py")})']
    if a == "press":
        if step.get("locator"):
            return [f'{_locator_py(step["locator"])}.press({_lit(step["key"])})']
        return [f'page.keyboard.press({_lit(step["key"])})']
    if a == "wait":
        return [f'page.wait_for_timeout({int(step.get("ms", 1000))})']
    if a == "upload":
        return [f'{_locator_py(step["locator"])}.set_input_files({_value_expr(step["value"], "py")})']
    if a == "drag":
        target = step.get("target", {})
        return [f'{_locator_py(step["locator"])}.drag_to({_locator_py(target)})']
    if a == "scroll":
        return [f'{_locator_py(step["locator"])}.scroll_into_view_if_needed()']
    if a == "expect":
        return _expect_py(step)
    raise ValueError(f"未知 action: {a}")


def _expect_py(step: dict) -> list:
    t = step["type"]
    if t == "url_contains":
        return [f'expect(page).to_have_url({_regex_py(step["value"])})']
    if t == "url_eq":
        return [f'expect(page).to_have_url({_lit(step["value"])})']
    if t == "title_contains":
        return [f'expect(page).to_have_title({_regex_py(step["value"])})']
    if t == "text_visible":
        return [f'expect(page.get_by_text({_lit(step["value"])})).to_be_visible()']
    if t == "element_visible":
        return [f'expect({_locator_py(step["locator"])}).to_be_visible()']
    if t == "element_hidden":
        return [f'expect({_locator_py(step["locator"])}).to_be_hidden()']
    if t == "value_eq":
        return [f'expect({_locator_py(step["locator"])}).to_have_value({_lit(step["value"])})']
    if t == "count_eq":
        return [f'expect({_locator_py(step["locator"])}).to_have_count({int(step["count"])})']
    if t == "attr_eq":
        return [f'expect({_locator_py(step["locator"])}).to_have_attribute({_lit(step["attr"])}, {_lit(step["value"])})']
    if t == "contains_text":
        return [f'expect({_locator_py(step["locator"])}).to_contain_text({_lit(step["value"])})']
    if t == "attr_exists":
        return [f'expect({_locator_py(step["locator"])}).to_have_attribute({_lit(step["attr"])})']
    if t == "enabled":
        return [f'expect({_locator_py(step["locator"])}).to_be_enabled()']
    if t == "disabled":
        return [f'expect({_locator_py(step["locator"])}).to_be_disabled()']
    raise ValueError(f"未知 expect.type: {t}")


def _step_ts(ir: dict, step: dict) -> list:
    a = step["action"]
    if a == "goto":
        return [f'await page.goto({_lit(_resolve_url(ir, step["url"]))});']
    if a in ("click", "dblclick", "hover", "check", "uncheck"):
        method = {"click": "click", "dblclick": "dblclick", "hover": "hover",
                  "check": "check", "uncheck": "uncheck"}[a]
        return [f'await {_locator_ts(step["locator"])}.{method}();']
    if a in ("fill", "type"):
        method = "fill" if a == "fill" else "type"
        return [f'await {_locator_ts(step["locator"])}.{method}({_value_expr(step["value"], "ts")});']
    if a == "select":
        return [f'await {_locator_ts(step["locator"])}.selectOption({_value_expr(step["value"], "ts")});']
    if a == "press":
        if step.get("locator"):
            return [f'await {_locator_ts(step["locator"])}.press({_lit(step["key"])});']
        return [f'await page.keyboard.press({_lit(step["key"])});']
    if a == "wait":
        return [f'await page.waitForTimeout({int(step.get("ms", 1000))});']
    if a == "upload":
        return [f'await {_locator_ts(step["locator"])}.setInputFiles({_value_expr(step["value"], "ts")});']
    if a == "drag":
        target = step.get("target", {})
        return [f'await {_locator_ts(step["locator"])}.dragTo({_locator_ts(target)});']
    if a == "scroll":
        return [f'await {_locator_ts(step["locator"])}.scrollIntoViewIfNeeded();']
    if a == "expect":
        return _expect_ts(step)
    raise ValueError(f"未知 action: {a}")


def _expect_ts(step: dict) -> list:
    t = step["type"]
    if t == "url_contains":
        return [f'await expect(page).toHaveURL({_regex_ts(step["value"])});']
    if t == "url_eq":
        return [f'await expect(page).toHaveURL({_lit(step["value"])});']
    if t == "title_contains":
        return [f'await expect(page).toHaveTitle({_regex_ts(step["value"])});']
    if t == "text_visible":
        return [f'await expect(page.getByText({_lit(step["value"])})).toBeVisible();']
    if t == "element_visible":
        return [f'await expect({_locator_ts(step["locator"])}).toBeVisible();']
    if t == "element_hidden":
        return [f'await expect({_locator_ts(step["locator"])}).toBeHidden();']
    if t == "value_eq":
        return [f'await expect({_locator_ts(step["locator"])}).toHaveValue({_lit(step["value"])});']
    if t == "count_eq":
        return [f'await expect({_locator_ts(step["locator"])}).toHaveCount({int(step["count"])});']
    if t == "attr_eq":
        return [f'await expect({_locator_ts(step["locator"])}).toHaveAttribute({_lit(step["attr"])}, {_lit(step["value"])});']
    if t == "contains_text":
        return [f'await expect({_locator_ts(step["locator"])}).toContainText({_lit(step["value"])});']
    if t == "attr_exists":
        return [f'await expect({_locator_ts(step["locator"])}).toHaveAttribute({_lit(step["attr"])});']
    if t == "enabled":
        return [f'await expect({_locator_ts(step["locator"])}).toBeEnabled();']
    if t == "disabled":
        return [f'await expect({_locator_ts(step["locator"])}).toBeDisabled();']
    raise ValueError(f"未知 expect.type: {t}")


# ─────────────────────────────────────────────────────────────────────────────
# 文件渲染
# ─────────────────────────────────────────────────────────────────────────────

def emit_python(ir: dict, architecture: dict = None) -> str:
    func = "test_" + _slug_ident(ir["name"])
    needs_os = any(_SECRET_RE.match(s.get("value", "") or "") for s in ir["steps"])
    needs_re = any(s.get("action") == "expect" and s.get("type") in
                   ("url_contains", "url_eq", "title_contains") for s in ir["steps"])
    
    # 判断是否使用 POM 模式
    is_pom = architecture and architecture.get("mode") == "pom"
    
    head = []
    if needs_os:
        head.append("import os")
    if needs_re:
        head.append("import re")
    head.append("")
    head.append("import pytest")
    head.append("from playwright.sync_api import Page, expect")
    
    # POM 模式添加导入
    if is_pom:
        base_class = architecture.get("base_class", "BasePage")
        pages_path = architecture.get("pages_path", "pages")
        import_style = architecture.get("import_style", "relative")
        
        if import_style == "relative":
            head.append(f"from {pages_path}.base_page import {base_class}")
            # 根据测试名称推断页面类
            page_name = _infer_page_name(ir["name"], architecture)
            head.append(f"from {pages_path}.{page_name.lower()} import {page_name}")
        else:
            head.append(f"from {pages_path}.base_page import {base_class}")
            page_name = _infer_page_name(ir["name"], architecture)
            head.append(f"from {pages_path}.{page_name.lower()} import {page_name}")
    
    head.append("")
    head.append("")
    tags = ir.get("tags") or []
    deco = "".join(f"@pytest.mark.{re.sub(r'[^0-9A-Za-z_]', '_', t)}\n" for t in tags)
    
    if is_pom:
        # POM 模式：使用 Page Object
        page_class = architecture.get("page_class", _infer_page_name(ir["name"], architecture))
        page_obj_var = page_class.lower()
        method_mappings = architecture.get("method_mappings", {})
        
        body = [f'{deco}def {func}(page: Page) -> None:',
                f'    """{ir["name"]}（feature: {ir.get("feature", "")}）"""',
                f'    {page_obj_var} = {page_class}(page)']
        
        for step in ir["steps"]:
            if step.get("comment"):
                body.append(f'    # {step["comment"]}')
            for line in _step_py_pom(page_obj_var, step, method_mappings):
                body.append(f'    {line}')
    else:
        # 线性模式：直接使用 page
        body = [f'{deco}def {func}(page: Page) -> None:',
                f'    """{ir["name"]}（feature: {ir.get("feature", "")}）"""']
        for step in ir["steps"]:
            if step.get("comment"):
                body.append(f'    # {step["comment"]}')
            for line in _step_py(ir, step):
                body.append(f'    {line}')
    
    return "\n".join(head + body) + "\n"


def _infer_page_name(test_name: str, architecture: dict) -> str:
    """根据测试名称推断页面类名"""
    # 简单实现：从测试名称提取关键部分
    # 例如：登录测试 -> Login
    pattern = architecture.get("page_pattern", "{name}Page")
    
    # 提取测试名称中的关键词，转换为英文
    name_mapping = {
        "登录": "Login",
        "注册": "Register",
        "首页": "Home",
        "搜索": "Search",
        "导航": "Navigation"
    }
    
    # 移除"测试"、"Test"后缀
    clean_name = test_name.replace("测试", "").replace("Test", "")
    
    # 尝试映射到英文
    for cn, en in name_mapping.items():
        if cn in clean_name:
            page_name = en
            break
    else:
        # 如果没有映射，使用原始名称的首字母大写
        name_parts = clean_name.split("_")
        if name_parts:
            page_name = "".join(word.capitalize() for word in name_parts)
        else:
            page_name = "Page"
    
    return pattern.replace("{name}", page_name)


def _step_py_pom(page_obj: str, step: dict, method_mappings: dict = None) -> list:
    """POM 模式的 Python 步骤生成"""
    action = step["action"]
    lines = []
    
    if action == "goto":
        # 使用 IR 中的方法映射，或默认 navigate
        goto_method = method_mappings.get("goto", "navigate") if method_mappings else "navigate"
        lines.append(f"{page_obj}.{goto_method}()")
    elif action == "fill":
        locator = step["locator"]
        value = step.get("value", "")
        # 使用 IR 中的方法映射
        if method_mappings and "fill" in method_mappings:
            fill_mappings = method_mappings["fill"]
            locator_value = str(locator.get("value", ""))
            # 查找匹配的方法名
            method_name = fill_mappings.get(locator_value)
            if method_name:
                lines.append(f'{page_obj}.{method_name}("{value}")')
            else:
                lines.append(f'# TODO: 未找到 locator "{locator_value}" 的填充方法映射')
        else:
            lines.append(f'# TODO: 未配置 fill 方法映射')
    elif action == "click":
        locator = step["locator"]
        # 使用 IR 中的方法映射
        if method_mappings and "click" in method_mappings:
            click_mappings = method_mappings["click"]
            locator_value = str(locator.get("value", ""))
            method_name = click_mappings.get(locator_value)
            if method_name:
                lines.append(f"{page_obj}.{method_name}()")
            else:
                lines.append(f'# TODO: 未找到 locator "{locator_value}" 的点击方法映射')
        else:
            lines.append(f'# TODO: 未配置 click 方法映射')
    elif action == "expect":
        t = step.get("type")
        value = step.get("value", "")
        if t == "url_contains":
            lines.append(f'expect(page).to_have_url(new RegExp(".*" + "{value}"))')
        else:
            lines.append(f'# TODO: 实现断言 {t}')
    else:
        lines.append(f"# TODO: 实现动作 {action}")
    
    return lines


def emit_typescript(ir: dict, architecture: dict = None) -> str:
    title = ir["name"]
    tags = ir.get("tags") or []
    tag_str = "".join(f" @{t}" for t in tags)
    
    # 判断是否使用 POM 模式
    is_pom = architecture and architecture.get("mode") == "pom"
    
    lines = ["import { test, expect } from '@playwright/test';", "", ""]
    
    # POM 模式添加导入
    if is_pom:
        base_class = architecture.get("base_class", "BasePage")
        pages_path = architecture.get("pages_path", "pages")
        import_style = architecture.get("import_style", "relative")
        
        if import_style == "relative":
            lines.append(f"import {{ {base_class} }} from '{pages_path}/basePage';")
            page_class = architecture.get("page_class", _infer_page_name_ts(ir["name"], architecture))
            lines.append(f"import {{ {page_class} }} from '{pages_path}/{page_class}';")
        else:
            lines.append(f"import {{ {base_class} }} from '{pages_path}/basePage';")
            page_class = architecture.get("page_class", _infer_page_name_ts(ir["name"], architecture))
            lines.append(f"import {{ {page_class} }} from '{pages_path}/{page_class}';")
    
    lines.append("")
    
    if is_pom:
        # POM 模式：使用 Page Object
        page_class = architecture.get("page_class", _infer_page_name_ts(ir["name"], architecture))
        page_obj_var = page_class[0].lower() + page_class[1:]
        method_mappings = architecture.get("method_mappings", {})
        
        lines.append(f'test({_lit(title + tag_str)}, async ({{ page }}) => {{')
        lines.append(f'  const {page_obj_var} = new {page_class}(page);')
        
        for step in ir["steps"]:
            if step.get("comment"):
                lines.append(f'  // {step["comment"]}')
            for line in _step_ts_pom(page_obj_var, step, method_mappings):
                lines.append(f'  {line}')
        
        lines.append("});")
    else:
        # 线性模式：直接使用 page
        lines.append(f'test({_lit(title + tag_str)}, async ({{ page }}) => {{')
        for step in ir["steps"]:
            if step.get("comment"):
                lines.append(f'  // {step["comment"]}')
            for line in _step_ts(ir, step):
                lines.append(f'  {line}')
        lines.append("});")
    
    return "\n".join(lines) + "\n"


def _infer_page_name_ts(test_name: str, architecture: dict) -> str:
    """根据测试名称推断页面类名（TypeScript 版本）"""
    pattern = architecture.get("page_pattern", "{name}Page")
    
    # 提取测试名称中的关键词，转换为英文
    name_mapping = {
        "登录": "Login",
        "注册": "Register",
        "首页": "Home",
        "搜索": "Search",
        "导航": "Navigation"
    }
    
    # 移除"测试"、"Test"后缀
    clean_name = test_name.replace("测试", "").replace("Test", "")
    
    # 尝试映射到英文
    for cn, en in name_mapping.items():
        if cn in clean_name:
            page_name = en
            break
    else:
        # 如果没有映射，使用原始名称的首字母大写
        name_parts = clean_name.split("_")
        if name_parts:
            page_name = "".join(word.capitalize() for word in name_parts)
        else:
            page_name = "Page"
    
    return pattern.replace("{name}", page_name)


def _step_ts_pom(page_obj: str, step: dict, method_mappings: dict = None) -> list:
    """POM 模式的 TypeScript 步骤生成"""
    action = step["action"]
    lines = []
    
    if action == "goto":
        # 使用 IR 中的方法映射，或默认 navigate
        goto_method = method_mappings.get("goto", "navigate") if method_mappings else "navigate"
        lines.append(f"await {page_obj}.{goto_method}();")
    elif action == "fill":
        locator = step["locator"]
        value = step.get("value", "")
        # 使用 IR 中的方法映射
        if method_mappings and "fill" in method_mappings:
            fill_mappings = method_mappings["fill"]
            locator_value = str(locator.get("value", ""))
            # 查找匹配的方法名
            method_name = fill_mappings.get(locator_value)
            if method_name:
                lines.append(f'await {page_obj}.{method_name}("{value}");')
            else:
                lines.append(f'// TODO: 未找到 locator "{locator_value}" 的填充方法映射')
        else:
            lines.append(f'// TODO: 未配置 fill 方法映射')
    elif action == "click":
        locator = step["locator"]
        # 使用 IR 中的方法映射
        if method_mappings and "click" in method_mappings:
            click_mappings = method_mappings["click"]
            locator_value = str(locator.get("value", ""))
            method_name = click_mappings.get(locator_value)
            if method_name:
                lines.append(f"await {page_obj}.{method_name}();")
            else:
                lines.append(f'// TODO: 未找到 locator "{locator_value}" 的点击方法映射')
        else:
            lines.append(f'// TODO: 未配置 click 方法映射')
    elif action == "expect":
        t = step.get("type")
        value = step.get("value", "")
        if t == "url_contains":
            lines.append(f'await expect(page).toHaveURL(new RegExp(".*" + "{value}"));')
        else:
            lines.append(f'// TODO: 实现断言 {t}')
    else:
        lines.append(f"// TODO: 实现动作 {action}")
    
    return lines


def generate(ir_path: Path, out_dir: Path, lang: str = "both") -> list:
    ir = json.loads(Path(ir_path).read_text(encoding="utf-8"))
    
    # 从 IR 读取架构配置
    architecture = ir.get("architecture", {})
    
    # 语言处理：如果为 auto，从 IR 推断
    if lang == "auto":
        detected_lang = architecture.get("language")
        if detected_lang in ["py", "ts"]:
            lang = detected_lang
        else:
            lang = "both"
    
    stem = Path(ir_path).stem.replace(".ir", "")
    written = []
    if lang in ("py", "both"):
        py_dir = out_dir / "python" / "tests"
        py_dir.mkdir(parents=True, exist_ok=True)
        p = py_dir / f"test_{stem}.py"
        p.write_text(emit_python(ir, architecture), encoding="utf-8")
        written.append(p)
    if lang in ("ts", "both"):
        ts_dir = out_dir / "typescript" / "tests"
        ts_dir.mkdir(parents=True, exist_ok=True)
        p = ts_dir / f"{stem}.spec.ts"
        p.write_text(emit_typescript(ir, architecture), encoding="utf-8")
        written.append(p)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description="IR → Playwright(Python/TypeScript)代码生成")
    ap.add_argument("ir", nargs="+", help="一个或多个 IR JSON 文件")
    ap.add_argument("--lang", choices=["py", "ts", "both", "auto"], default="auto", help="目标语言（auto=根据IR推断，默认auto）")
    ap.add_argument("--out", default="./generated", help="输出目录（默认当前目录下的 generated 文件夹）")
    args = ap.parse_args(argv)
    out_dir = Path(args.out)
    
    for ir_file in args.ir:
        for p in generate(Path(ir_file), out_dir, args.lang):
            print(f"  生成: {p}")


if __name__ == "__main__":
    main()
