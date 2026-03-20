"""Git operations portmanteau. Local Git via subprocess."""

import subprocess
from pathlib import Path
from typing import Any

from ..utils.response import success_response, error_response


def _run_git(repo_path: Path, args: list[str], timeout: int = 60) -> tuple[bool, str, str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Git command timed out"
    except FileNotFoundError:
        return False, "", "Git not found"
    except Exception as e:
        return False, "", str(e)


def git_ops(
    operation: str,
    repo_path: str | None = None,
    message: str | None = None,
    files: list[str] | None = None,
    remote: str = "origin",
    branch: str | None = None,
    force: bool = False,
    all_files: bool = False,
    target_dir: str | None = None,
    repo_url: str | None = None,
) -> dict[str, Any]:
    """Git operations: clone, status, add, commit, push, pull, branch, tag, stash."""
    ops = {
        "clone", "status", "add", "commit", "push", "pull",
        "branch", "tag", "stash",
    }
    if operation not in ops:
        return error_response(
            operation,
            f"Unknown operation. Use one of: {', '.join(sorted(ops))}",
            suggested_fixes=[f"git_ops(operation='status')"],
        )

    if operation == "clone":
        if not repo_url:
            return error_response(operation, "repo_url required for clone")
        base = Path(".").resolve()
        args = ["clone", repo_url]
        if target_dir:
            args.append(str(Path(target_dir).resolve()))
        ok, out, err = _run_git(base, args)
        if not ok:
            return error_response(operation, err or "Clone failed")
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        cloned_path = Path(target_dir).resolve() if target_dir else base / repo_name
        return success_response(
            {"repo_url": repo_url, "path": str(cloned_path)},
            operation,
            message="Repository cloned",
            next_steps=[f"git_ops(operation='status', repo_path='{cloned_path}')"],
        )

    repo = Path(repo_path or ".").resolve()
    if not (repo / ".git").exists():
        return error_response(
            operation,
            f"Not a Git repository: {repo}",
            suggested_fixes=["git_ops(operation='clone', repo_url='...')"],
        )

    if operation == "status":
        ok, out, err = _run_git(repo, ["status", "--short", "-b"])
        if not ok:
            return error_response(operation, err or "Status failed")
        branch_ok, branch_out, _ = _run_git(repo, ["branch", "--show-current"])
        current_branch = branch_out.strip() if branch_ok else "?"
        return success_response(
            {"branch": current_branch, "output": out},
            operation,
            next_steps=["git_ops(operation='add', ...)", "git_ops(operation='commit', ...)"],
        )

    if operation == "add":
        args = ["add", "."] if all_files else ["add"] + (files or [])
        if not all_files and not files:
            return error_response(operation, "files or all_files=True required")
        ok, out, err = _run_git(repo, args)
        if not ok:
            return error_response(operation, err or "Add failed")
        return success_response(
            {"staged": files or "all"},
            operation,
            message="Files staged",
            next_steps=[f"git_ops(operation='commit', message='...', repo_path='{repo}')"],
        )

    if operation == "commit":
        if not message:
            return error_response(operation, "message required")
        args = ["commit", "-m", message]
        if all_files:
            args.insert(1, "-a")
        ok, out, err = _run_git(repo, args)
        if not ok:
            return error_response(operation, err or "Commit failed")
        return success_response(
            {"message": message, "output": out.strip()},
            operation,
            next_steps=[f"git_ops(operation='push', repo_path='{repo}')"],
        )

    if operation == "push":
        args = ["push", remote]
        if branch:
            args.append(branch)
        if force:
            args.insert(1, "--force")
        ok, out, err = _run_git(repo, args)
        if not ok:
            return error_response(
                operation,
                err or "Push failed",
                recovery_options=["Check remote URL", "gh auth login", "git pull first"],
            )
        return success_response(
            {"remote": remote, "branch": branch},
            operation,
            message="Pushed",
        )

    if operation == "pull":
        args = ["pull", remote]
        if branch:
            args.append(branch)
        ok, out, err = _run_git(repo, args)
        if not ok:
            return error_response(operation, err or "Pull failed")
        return success_response({"output": out.strip()}, operation, message="Pulled")

    if operation == "branch":
        ok, out, err = _run_git(repo, ["branch", "-a"])
        if not ok:
            return error_response(operation, err or "Branch list failed")
        return success_response(
            {"branches": out.strip().splitlines()},
            operation,
        )

    if operation == "tag":
        ok, out, err = _run_git(repo, ["tag", "-l"])
        if not ok:
            return error_response(operation, err or "Tag list failed")
        return success_response(
            {"tags": out.strip().splitlines() or []},
            operation,
        )

    if operation == "stash":
        ok, out, err = _run_git(repo, ["stash", "list"])
        if not ok:
            return error_response(operation, err or "Stash list failed")
        return success_response(
            {"stashes": out.strip().splitlines() or []},
            operation,
        )

    return error_response(operation, "Not implemented")
