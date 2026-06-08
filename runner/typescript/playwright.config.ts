import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  use: {
    headless: true,
    // 默认使用 Playwright 安装的 Chromium（稳定可靠）
    // 如需使用系统 Chrome，取消注释下一行：
    // channel: 'chrome',
  },
  // 自动起本地静态站点(指向 demo-site),TS 端无需手动起服务
  webServer: {
    command: 'npx http-server -p 8000 ../demo-site',
    url: 'http://localhost:8000/index.html',
    reuseExistingServer: true,
  },
});