import { test, expect } from '@playwright/test';


test("搜索-关键词返回结果 @search", async ({ page }) => {
  await page.goto("https://app.example.com/");
  await page.getByPlaceholder("搜索商品").fill("手机");
  await page.getByPlaceholder("搜索商品").press("Enter");
  await expect(page).toHaveURL(new RegExp(".*" + "/search"));
  await expect(page.getByTestId("result-list")).toBeVisible();
  await expect(page.locator(".result-item")).toHaveCount(10);
});
