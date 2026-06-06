import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  use: {
    headless: true,
    channel: 'chrome', // 使用系统 chrome (ubuntu 26.04 兼容性)
  },
  // 自动起本地静态站点(指向 demo-site),TS 端无需手动起服务
  webServer: {
    command: 'python3 -m http.server 8000 --directory ../demo-site',
    url: 'http://localhost:8000/index.html',
    reuseExistingServer: true,
  },
});