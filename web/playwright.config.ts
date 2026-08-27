import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: "http://localhost:10714",
    headless: true,
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "uv run python -m git_github_mcp.server --port 10713",
    port: 10713,
    timeout: 30000,
    reuseExistingServer: false,
  },
});
