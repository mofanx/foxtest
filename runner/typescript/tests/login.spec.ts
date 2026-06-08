import { test, expect } from '@playwright/test';


test("登录-正常登录 @smoke @auth", async ({ page }) => {
  await page.goto("https://app.example.com/login");
  await page.getByLabel("用户名").fill("admin");
  await page.getByLabel("密码").fill(process.env["APP_PASSWORD"]!);
  await page.getByRole("button", { name: "登录" }).click();
  await expect(page).toHaveURL(new RegExp(".*" + "/dashboard"));
  await expect(page.getByText("欢迎")).toBeVisible();
});
