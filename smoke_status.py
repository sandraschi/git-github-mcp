"""Standalone smoke test for status.py — run this directly to find the hang point.

Usage:
    cd D:\Dev\repos\git-github-mcp
    .venv\Scripts\python.exe smoke_status.py
"""

import sys
import time

print("smoke_status: starting", flush=True)

# Step 1: shutil.which git
print("Step 1: shutil.which('git')...", flush=True)
t = time.perf_counter()
import shutil
git_path = shutil.which("git")
print(f"  -> {git_path!r}  ({time.perf_counter()-t:.3f}s)", flush=True)

# Step 2: shutil.which gh
print("Step 2: shutil.which('gh')...", flush=True)
t = time.perf_counter()
gh_path = shutil.which("gh")
print(f"  -> {gh_path!r}  ({time.perf_counter()-t:.3f}s)", flush=True)

# Step 3: git --version
print("Step 3: git --version (timeout=5)...", flush=True)
import os, subprocess
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
env = os.environ.copy()
env.update({
    "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo",
    "GCM_INTERACTIVE": "never", "GCM_CREDENTIAL_STORE": "wincred",
    "GH_PROMPT_DISABLED": "1", "NO_COLOR": "1", "TERM": "dumb",
})
t = time.perf_counter()
try:
    r = subprocess.run(["git", "--version"], capture_output=True, text=True,
                       timeout=5, env=env, creationflags=NO_WINDOW)
    print(f"  -> rc={r.returncode} stdout={r.stdout.strip()!r}  ({time.perf_counter()-t:.3f}s)", flush=True)
except subprocess.TimeoutExpired:
    print(f"  -> TIMEOUT after 5s", flush=True)
except Exception as e:
    print(f"  -> ERROR: {e}", flush=True)

# Step 4: gh --version
print("Step 4: gh --version (timeout=5)...", flush=True)
t = time.perf_counter()
try:
    r = subprocess.run(["gh", "--version"], capture_output=True, text=True,
                       timeout=5, env=env, creationflags=NO_WINDOW)
    print(f"  -> rc={r.returncode} stdout={r.stdout.strip()[:80]!r}  ({time.perf_counter()-t:.3f}s)", flush=True)
except subprocess.TimeoutExpired:
    print(f"  -> TIMEOUT after 5s", flush=True)
except Exception as e:
    print(f"  -> ERROR: {e}", flush=True)

# Step 5: gh auth token
print("Step 5: gh auth token (timeout=5)...", flush=True)
t = time.perf_counter()
try:
    r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                       timeout=5, env=env, creationflags=NO_WINDOW)
    tok = r.stdout.strip()
    print(f"  -> rc={r.returncode} token={'<present>' if tok else '<empty>'}  stderr={r.stderr.strip()[:80]!r}  ({time.perf_counter()-t:.3f}s)", flush=True)
except subprocess.TimeoutExpired:
    print(f"  -> TIMEOUT after 5s", flush=True)
except Exception as e:
    print(f"  -> ERROR: {e}", flush=True)

print("smoke_status: DONE", flush=True)
