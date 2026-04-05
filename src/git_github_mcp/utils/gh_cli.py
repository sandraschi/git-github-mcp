"""Run gh CLI commands. Uses subprocess with shell=False."""

import os
import subprocess
from pathlib import Path


def run_gh(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 60,
) -> tuple[bool, str, str]:
    """Run gh CLI. Returns (success, stdout, stderr)."""
    try:
        # GH_PROMPT_DISABLED=1 and GIT_TERMINAL_PROMPT=0 prevent process hangs.
        env = os.environ.copy()
        env["GH_PROMPT_DISABLED"] = "1"
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes"

        result = subprocess.run(
            ["gh"] + args,
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
        return False, "", "gh CLI not found. Install: https://cli.github.com/"
    except Exception as e:
        return False, "", str(e)
