import asyncio

from git_github_mcp.tools.github_ops import github_ops


async def main():
    # Verify gh version first to be sure
    import subprocess

    v = subprocess.run(["C:\\Program Files\\GitHub CLI\\gh.exe", "--version"], capture_output=True, text=True).stdout
    print(f"CLI Version: {v.splitlines()[0]}")

    print("Checking auth status...")
    # github_ops is a sync function in this implementation
    result = github_ops(operation="auth_status")
    print(f"Result: {result}")

    if result.get("success") and result.get("result", {}).get("authenticated"):
        print("✅ SUCCESS: Server is authenticated and gh CLI is accessible.")
    else:
        print("❌ FAILURE: Server could not authenticate or find gh.")


if __name__ == "__main__":
    asyncio.run(main())
