import { test, expect } from '@playwright/test';


test("验证注册链接 @navigation @smoke", async ({ page }) => {
  await page.goto("http://localhost:8000/index.html");
  await expect(page.getByText("注册")).toBeVisible();
  await page.getByText("注册").click();
  await expect(page).toHaveURL(new RegExp(".*" + "register"));
  await expect(page).toHaveTitle(new RegExp(".*" + "注册"));
});
