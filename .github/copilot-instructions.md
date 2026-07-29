## Session Context (Git GitHub MCP)

You have access to a hardened Git/GitHub MCP server with 101+ operations across 11 tools.
Your local git and GitHub (gh CLI) operations persist across sessions.

**Before starting work:**
1. Check git/gh availability: git_github_status(level="basic")
2. Check current repo state: git_core(operation="status", repo_path=".")
3. For GitHub tasks, verify auth: github_ops(operation="auth_status")

**At end of work:**
- Review unstaged changes: git_core(operation="status")
- Commit and push if the user asked for it
