import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.navigation
@pytest.mark.smoke
def test_验证注册链接(page: Page) -> None:
    """验证注册链接（feature: 登录）"""
    page.goto("http://localhost:8000/index.html")
    expect(page.get_by_text("注册")).to_be_visible()
    page.get_by_text("注册").click()
    expect(page).to_have_url(re.compile(r".*register"))
    expect(page).to_have_title(re.compile(r".*注册"))
