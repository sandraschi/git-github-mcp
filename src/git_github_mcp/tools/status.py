"""Status tool for git-github-mcp — hang-hardened with per-step logging."""

import logging
import os
import platform
import shutil
import subprocess
import sys

from ..utils.response import error_response, success_response

logger = logging.getLogger("git-github-mcp.status")

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _no_prompt_env() -> dict:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"
    env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=no"
    env["GCM_INTERACTIVE"] = "never"
    env["GCM_CREDENTIAL_STORE"] = "wincred"
    env["GH_PROMPT_DISABLED"] = "1"
    env["GH_NO_UPDATE_NOTIFIER"] = "1"
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    # Point at a minimal gitconfig to bypass any user gitconfig credential helpers
    env["GIT_CONFIG_GLOBAL"] = r"D:\Dev\repos\git-github-mcp\minimal.gitconfig"
    return env


def _run(cmd: list[str], timeout: int) -> tuple[int, str, str]:
    label = " ".join(cmd[:2])
    logger.info(f"_run start: {label} (timeout={timeout})")
    try:
        r = subprocess.run(  # noqa: S603 — list-based, no shell
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=_no_prompt_env(),
            creationflags=_NO_WINDOW,
        )
        logger.info(f"_run done: {label} rc={r.returncode}")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        logger.warning(f"_run TIMEOUT: {label}")
        return -1, "", f"timed out after {timeout}s"
    except FileNotFoundError:
        logger.warning(f"_run NOT FOUND: {label}")
        return -1, "", "not found"
    except Exception as e:
        logger.warning(f"_run ERROR: {label}: {e}")
        return -1, "", str(e)


def get_status(level: str = "basic") -> dict:
    logger.info("get_status: start")

    logger.info("get_status: _check_git start")
    git_result = _check_git()
    logger.info(f"get_status: _check_git done available={git_result.get('available')}")

    logger.info("get_status: _check_gh start")
    gh_result = _check_gh()
    logger.info(f"get_status: _check_gh done available={gh_result.get('available')} auth={gh_result.get('auth')}")

    result: dict = {
        "git": git_result,
        "gh": gh_result,
        "tools": ["git_ops", "github_ops"],
    }
    if level == "detailed":
        result["platform"] = platform.system()
        result["platform_release"] = platform.release()
        result["machine"] = platform.machine()
        result["python"] = platform.python_version()

    git_ok = result["git"].get("available", False)
    gh_ok = result["gh"].get("available", False)
    gh_auth_ok = result["gh"].get("auth") == "ok"

    if not git_ok:
        return error_response("status", "Git not found", recovery_options=["Install Git: https://git-scm.com/"])
    if not gh_ok:
        return error_response("status", "gh CLI not found", recovery_options=["Install gh: https://cli.github.com/"])
    if not gh_auth_ok:
        return success_response(
            result,
            "status",
            message="Git OK; gh installed but no token — run: gh auth login",
            next_steps=["gh auth login"],
        )
    return success_response(
        result,
        "status",
        message="git and gh available; token present",
        next_steps=["git_ops(operation='status')", "github_ops(operation='repo_list', owner='YOUR_USER')"],
    )


def _resolve_git_exe() -> str | None:
    """Return path to the real git.exe binary, avoiding the cmd wrapper.

    C:\\Program Files\\Git\\cmd\\git.EXE is a shell wrapper that can block when
    spawned from a consoleless process. The actual binary is in bin\\git.exe.
    """
    git_path = shutil.which("git")
    if git_path:
        # If we got the cmd wrapper, try the real binary next to it
        p = os.path.normpath(git_path)
        if "cmd" in p.lower():
            real = os.path.join(os.path.dirname(p), "..", "bin", "git.exe")
            real = os.path.normpath(real)
            if os.path.isfile(real):
                logger.info(f"_resolve_git_exe: using real binary {real} instead of {p}")
                return real
        return git_path
    # Fallback: common install location
    fallback = r"C:\Program Files\Git\bin\git.exe"
    if os.path.isfile(fallback):
        return fallback
    return None


def _check_git() -> dict:
    """Check git availability by path existence only — no subprocess."""
    logger.info("_check_git: resolving git exe (no subprocess)")
    git_path = _resolve_git_exe()
    logger.info(f"_check_git: resolved path={git_path}")
    if not git_path or not os.path.isfile(git_path):
        return {"available": False, "error": "not found in PATH"}
    return {"available": True, "version": "unknown (skipped --version to avoid hang)", "path": git_path}


def _check_gh() -> dict:
    """Check gh availability and auth token — minimal subprocess use."""
    logger.info("_check_gh: shutil.which")
    gh_path = shutil.which("gh")
    if not gh_path and os.path.isfile(r"C:\Program Files\GitHub CLI\gh.exe"):
        gh_path = r"C:\Program Files\GitHub CLI\gh.exe"
    logger.info(f"_check_gh: path={gh_path}")
    if not gh_path or not os.path.isfile(gh_path):
        return {"available": False, "error": "not found in PATH"}

    info: dict = {"available": True, "version": "unknown (skipped --version)", "path": gh_path}

    # GH_TOKEN in env means auth is handled without GCM — check it directly
    if os.environ.get("GH_TOKEN"):
        logger.info("_check_gh: GH_TOKEN present in env, skipping subprocess auth check")
        info["auth"] = "ok"
        info["auth_note"] = "GH_TOKEN set in environment"
        return info

    # gh auth token: reads cached token locally, no network
    logger.info("_check_gh: running gh auth token")
    token_rc, token_out, _ = _run([gh_path, "auth", "token"], 5)
    logger.info(f"_check_gh: auth token rc={token_rc}")
    if token_rc == 0 and token_out.strip():
        info["auth"] = "ok"
    else:
        info["auth"] = "not logged in"
        info["auth_hint"] = "Run: gh auth login"
    return info
