import { test, expect } from '@playwright/test';


test("demo-登录跳转 @demo @smoke", async ({ page }) => {
  await page.goto("http://localhost:8000/index.html");
  await page.getByLabel("用户名").fill("admin");
  await page.getByLabel("密码").fill("secret123");
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page).toHaveURL(new RegExp(".*" + "/dashboard"));
  await expect(page.getByTestId("welcome")).toBeVisible();
});
