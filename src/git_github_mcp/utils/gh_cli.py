"""Run gh CLI commands. Uses subprocess with shell=False."""

import os
import subprocess
import sys
from pathlib import Path

# CREATE_NO_WINDOW + CREATE_BREAKAWAY_FROM_JOB (escapes Electron job object limits)
_NO_WINDOW = 0x08000000 | 0x01000000 if sys.platform == "win32" else 0


def _get_gh_path() -> str:
    """Find gh.exe, checking common Windows paths if not in PATH."""
    import shutil

    # 1. Try PATH
    wh = shutil.which("gh")
    if wh:
        return wh

    # 2. Try common Windows installation paths
    common_paths = [
        r"C:\Program Files\GitHub CLI\gh.exe",
        str(Path.home() / "scoop" / "shims" / "gh.exe"),
        str(Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps" / "gh.exe"),
    ]
    for p in common_paths:
        if Path(p).exists():
            return p

    return "gh"  # Fallback to string for subprocess to try PATH again


def _no_prompt_env() -> dict:
    """Build env dict that prevents all interactive prompts / credential UI / browser launches.

    Discovery guard (issue #3): gh shells out to git for repo resolution, so a
    launcher-inherited GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE would retarget
    it exactly like the git Ops hijack — scrubbed here too.
    """
    env = os.environ.copy()
    for _k in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
        "GIT_NAMESPACE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
    ):
        env.pop(_k, None)
    for _k in [
        k
        for k in env
        if k.startswith("GIT_CONFIG_COUNT") or k.startswith("GIT_CONFIG_KEY_") or k.startswith("GIT_CONFIG_VALUE_")
    ]:
        env.pop(_k, None)
    env["GH_PROMPT_DISABLED"] = "1"
    env["GH_NO_UPDATE_NOTIFIER"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"
    env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=no"
    env["GCM_INTERACTIVE"] = "never"
    env.setdefault("GCM_CREDENTIAL_STORE", "wincredman")  # Windows native store, no prompts
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
    return env


def run_gh(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 60,
) -> tuple[bool, str, str]:
    """Run gh CLI. Returns (success, stdout, stderr)."""
    gh_path = _get_gh_path()
    try:
        result = subprocess.run(
            [gh_path, *args],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=_no_prompt_env(),
            creationflags=_NO_WINDOW,
        )
        out = result.stdout or ""
        err = result.stderr or ""
        return result.returncode == 0, out, err
    except subprocess.TimeoutExpired:
        return False, "", "gh command timed out"
    except FileNotFoundError:
        return False, "", f"gh CLI not found ('{gh_path}'). Install: https://cli.github.com/"
    except Exception as e:
        return False, "", str(e)
