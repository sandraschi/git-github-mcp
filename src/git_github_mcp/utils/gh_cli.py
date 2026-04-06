"""Run gh CLI commands. Uses subprocess with shell=False."""

import os
import subprocess
from pathlib import Path


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


def run_gh(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 60,
) -> tuple[bool, str, str]:
    """Run gh CLI. Returns (success, stdout, stderr)."""
    try:
        gh_path = _get_gh_path()

        # GH_PROMPT_DISABLED=1 and GIT_TERMINAL_PROMPT=0 prevent process hangs.
        env = os.environ.copy()
        env["GH_PROMPT_DISABLED"] = "1"
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes"

        result = subprocess.run(
            [gh_path] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
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
