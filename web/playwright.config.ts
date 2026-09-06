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
    // Serve the FastAPI web bridge (has /health + /api/*). NOTE: the old
    // `python -m git_github_mcp.server --port ...` runs STDIO transport and
    // never listens, so Playwright timed out waiting for the port.
    command:
      "uv run uvicorn git_github_mcp.server:web_app --host 127.0.0.1 --port 10713",
    port: 10713,
    timeout: 60000,
    reuseExistingServer: !process.env.CI,
  },
});
