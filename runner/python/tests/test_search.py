import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.search
def test_搜索_关键词返回结果(page: Page) -> None:
    """搜索-关键词返回结果（feature: 搜索）"""
    page.goto("https://app.example.com/")
    page.get_by_placeholder("搜索商品").fill("手机")
    page.get_by_placeholder("搜索商品").press("Enter")
    expect(page).to_have_url(re.compile(r".*/search"))
    expect(page.get_by_test_id("result-list")).to_be_visible()
    expect(page.locator(".result-item")).to_have_count(10)
