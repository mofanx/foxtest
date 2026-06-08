import os
import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.smoke
@pytest.mark.auth
def test_登录_正常登录(page: Page) -> None:
    """登录-正常登录（feature: 登录）"""
    page.goto("https://app.example.com/login")
    page.get_by_label("用户名").fill("admin")
    page.get_by_label("密码").fill(os.environ["APP_PASSWORD"])
    page.get_by_role("button", name="登录").click()
    expect(page).to_have_url(re.compile(r".*/dashboard"))
    expect(page.get_by_text("欢迎")).to_be_visible()
