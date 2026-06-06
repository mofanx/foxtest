import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.demo
@pytest.mark.smoke
def test_demo_登录跳转(page: Page) -> None:
    """demo-登录跳转（feature: 登录）"""
    page.goto("http://localhost:8000/index.html")
    page.get_by_label("用户名").fill("admin")
    page.get_by_label("密码").fill("secret123")
    page.get_by_role("button", name="登录").click()
    expect(page).to_have_url(re.compile(r".*/dashboard"))
    expect(page.get_by_test_id("welcome")).to_be_visible()
