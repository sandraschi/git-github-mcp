"""Status tool for git-github-mcp. Reports git and gh CLI availability."""

import platform
import subprocess

from ..utils.response import error_response, success_response


def get_status(level: str = "basic") -> dict:
    """Report system status: git and gh CLI availability, versions.

    LEVELS:
    - basic: git/gh availability, versions
    - detailed: + platform, Python version

    Args:
        level: basic or detailed

    Returns:
        Dialogic response with status info in result.
    """
    result: dict = {
        "git": _check_git(),
        "gh": _check_gh(),
        "tools": ["git_ops", "github_ops"],
    }
    if level == "detailed":
        result["platform"] = platform.system()
        result["platform_release"] = platform.release()
        result["machine"] = platform.machine()
        result["python"] = platform.python_version()

    git_ok = result["git"].get("available", False)
    gh_ok = result["gh"].get("available", False)
    if not git_ok:
        return error_response(
            "status",
            "Git not found",
            recovery_options=["Install Git: https://git-scm.com/"],
        )
    if not gh_ok:
        return error_response(
            "status",
            "gh CLI not found",
            recovery_options=["Install gh: https://cli.github.com/", "Run gh auth login"],
        )

    return success_response(
        result,
        "status",
        message="git and gh available",
        next_steps=["mcp_help() for usage", "git_ops(operation='status') for repo status"],
    )


def _check_git() -> dict:
    """Check git availability and version."""
    try:
        r = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            return {"available": True, "version": r.stdout.strip()}
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        return {"available": False, "error": "timeout"}
    return {"available": False, "error": "not found"}


def _check_gh() -> dict:
    """Check gh CLI availability and auth status."""
    try:
        r = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            out = r.stdout.strip()
            info = {"available": True, "version": out.split("\n")[0] if out else "ok"}
            auth_r = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            info["auth"] = "ok" if auth_r.returncode == 0 else "not logged in"
            return info
    except FileNotFoundError:
        return {"available": False, "error": "not found"}
    except subprocess.TimeoutExpired:
        return {"available": False, "error": "timeout"}
    except Exception as e:
        return {"available": False, "error": str(e)}
