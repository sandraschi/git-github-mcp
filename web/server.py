"""FastAPI backend for Git GitHub Hub webapp. Run from web/ with parent src on path."""

import logging
import os
import sys
from pathlib import Path

# Ensure parent src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Import tools directly (no MCP protocol needed for webapp)
import json
from git_github_mcp.tools.git_ops import git_ops
from git_github_mcp.tools.github_ops import github_ops
from git_github_mcp.utils.gh_cli import run_gh

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webapp")

app = FastAPI(title="Git GitHub Hub", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GitOpsRequest(BaseModel):
    operation: str = Field(..., description="clone, status, add, commit, push, pull, branch, tag, stash")
    repo_path: str | None = None
    message: str | None = None
    files: list[str] | None = None
    remote: str = "origin"
    branch: str | None = None
    force: bool = False
    all_files: bool = False
    target_dir: str | None = None
    repo_url: str | None = None


class GitHubOpsRequest(BaseModel):
    operation: str = Field(..., description="create_issue, list_issues, create_pr, list_prs, search")
    owner: str | None = None
    repo: str | None = None
    title: str | None = None
    body: str | None = None
    state: str = "open"
    limit: int = 10
    query: str | None = None


@app.post("/api/v1/git/ops")
async def git_ops_endpoint(req: GitOpsRequest):
    """Run git_ops tool."""
    result = git_ops(
        operation=req.operation,
        repo_path=req.repo_path,
        message=req.message,
        files=req.files,
        remote=req.remote,
        branch=req.branch,
        force=req.force,
        all_files=req.all_files,
        target_dir=req.target_dir,
        repo_url=req.repo_url,
    )
    return result


@app.post("/api/v1/github/ops")
async def github_ops_endpoint(req: GitHubOpsRequest):
    """Run github_ops tool."""
    result = github_ops(
        operation=req.operation,
        owner=req.owner,
        repo=req.repo,
        title=req.title,
        body=req.body,
        state=req.state,
        limit=req.limit,
        query=req.query,
    )
    return result


@app.get("/api/v1/github/repos")
async def list_repos():
    """List user's repos via gh repo list."""
    ok, out, err = run_gh(["repo", "list", "--limit", "50", "--json", "name,owner,nameWithOwner,url,description"])
    if not ok:
        return {"success": False, "error": err or "Failed to list repos", "repos": []}
    try:
        repos = json.loads(out)
    except json.JSONDecodeError:
        repos = []
    return {"success": True, "repos": repos}


@app.get("/api/v1/github/issues")
async def list_issues(owner: str, repo: str, state: str = "open"):
    """List issues for a repo."""
    result = github_ops(operation="list_issues", owner=owner, repo=repo, state=state)
    return result


@app.get("/api/v1/github/prs")
async def list_prs(owner: str, repo: str, state: str = "open"):
    """List PRs for a repo."""
    result = github_ops(operation="list_prs", owner=owner, repo=repo, state=state)
    return result


GLAMA_API_BASE = "https://glama.ai/api/mcp/v1/servers"


@app.get("/api/v1/glama/check")
async def glama_check(owner: str, repo: str):
    """Check if a GitHub repo is scraped by Glama.ai. Returns listing status and review metadata."""
    import urllib.request
    url = f"{GLAMA_API_BASE}/{owner}/{repo}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GitGitHubHub/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {
                "success": True,
                "exists": True,
                "owner": owner,
                "repo": repo,
                "url": data.get("url", f"https://glama.ai/mcp/servers/@{owner}/{repo}"),
                "name": data.get("name"),
                "description": data.get("description"),
                "license": data.get("spdxLicense", {}).get("name") if isinstance(data.get("spdxLicense"), dict) else None,
                "attributes": data.get("attributes", []),
                "glama_id": data.get("id"),
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {
                "success": True,
                "exists": False,
                "owner": owner,
                "repo": repo,
                "url": None,
                "message": "Not yet scraped by Glama",
            }
        return {"success": False, "error": f"Glama API error: {e.code}"}
    except Exception as e:
        logger.exception("Glama check failed")
        return {"success": False, "error": str(e)}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "git-github-hub"}


# Mount static frontend after build
_dist = Path(__file__).parent / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
    logger.info("Mounted frontend from dist/")
else:
    @app.get("/")
    async def root():
        return {"message": "Build frontend first: cd web && npm run build"}


def main():
    port = int(os.environ.get("PORT", "5180"))
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
