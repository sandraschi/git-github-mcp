"""Run gh CLI commands. Uses subprocess with shell=False."""

import subprocess
from pathlib import Path


def run_gh(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 60,
) -> tuple[bool, str, str]:
    """Run gh CLI. Returns (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "gh command timed out"
    except FileNotFoundError:
        return False, "", "gh CLI not found. Install: https://cli.github.com/"
    except Exception as e:
        return False, "", str(e)
