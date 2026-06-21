import { defineConfig } from '@playwright/test';
export default defineConfig({
    testDir: './e2e', timeout: 60000, retries: 1,
    use: { baseURL: 'http://localhost:10703', headless: true, screenshot: 'only-on-failure' },
    webServer: {
        command: 'uv run python -m git_github_mcp.server --port 10702',
        port: 10702, timeout: 30000, reuseExistingServer: false
    }
});
