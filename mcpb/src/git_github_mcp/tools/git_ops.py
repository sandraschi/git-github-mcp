"""Git operations portmanteau — full local Git workflow via subprocess."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..utils.response import error_response, success_response

_NO_WINDOW = (
    0x08000000 if sys.platform == "win32" else 0
)  # CREATE_NO_WINDOW only — CREATE_BREAKAWAY_FROM_JOB (0x01000000) breaks under Electron job objects

# Hardcode real git.exe — bin\git.exe is the actual binary; cmd\git.exe is a shell wrapper
# that can deadlock when spawned from a consoleless process (e.g. MCP stdio).
_GIT_EXE = r"C:\Program Files\Git\bin\git.exe"

ACTION_TYPE = (
    # Core
    "init",
    "clone",
    "add",
    "commit",
    "push",
    "pull",
    "fetch",
    "status",
    # Inspect
    "log",
    "diff",
    "show",
    "blame",
    # Branch
    "branch_list",
    "branch_create",
    "branch_switch",
    "branch_delete",
    "branch_rename",
    "branch_merge",
    "rebase",
    # Remote
    "remote_list",
    "remote_add",
    "remote_remove",
    # Stash
    "stash",
    "stash_pop",
    "stash_list",
    "stash_drop",
    # Tag
    "tag_list",
    "tag_create",
    "tag_delete",
    # Undo
    "reset",
    "revert",
    "cherry_pick",
    # Cleanup
    "clean",
    # Submodule
    "submodule_add",
    "submodule_update",
    "submodule_sync",
    "submodule_status",
    # Bisect
    "bisect_start",
    "bisect_bad",
    "bisect_good",
    "bisect_reset",
    # Worktree
    "worktree_add",
    "worktree_list",
    "worktree_remove",
)


def _run_git(path: Path, args: list[str], timeout: int = 60) -> tuple[bool, str, str]:
    """Run git via list-based exec with CREATE_NO_WINDOW — no shell=True, no cmd.exe wrapper.

    shell=True spawns cmd.exe which can deadlock when the parent process has no console
    (e.g. MCP stdio transport under Claude Desktop / Electron). Using the real binary path
    directly with creationflags avoids both the scoop shim and the console hang.
    """
    import subprocess as sp

    cmd = [_GIT_EXE, "-C", str(path), *args]
    try:
        r = sp.run(  # noqa: S603 — list-based, no shell
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=_git_env(),
            creationflags=_NO_WINDOW,
        )
        out = r.stdout or ""
        err = r.stderr or ""
        return r.returncode == 0, out, err
    except subprocess.TimeoutExpired:
        return False, "", f"git timed out after {timeout}s"
    except FileNotFoundError:
        return False, "", f"git not found at {_GIT_EXE}"
    except Exception as e:
        return False, "", str(e)


def _git_env() -> dict:
    """Build env for git subprocess — identical to github_ops' _no_prompt_env."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"
    env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=no"
    env["GCM_INTERACTIVE"] = "never"
    env["GCM_CREDENTIAL_STORE"] = "wincred"
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
    return env


async def _run_git_async(path: Path, args: list[str], timeout: int = 60) -> tuple[bool, str, str]:
    """Async git subprocess using asyncio.create_subprocess_exec — no thread pool."""
    try:
        proc = await asyncio.create_subprocess_exec(
            _GIT_EXE,
            *args,
            cwd=path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_git_env(),
            creationflags=_NO_WINDOW,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out = stdout.decode("utf-8", errors="replace") if stdout else ""
            err = stderr.decode("utf-8", errors="replace") if stderr else ""
            return proc.returncode == 0, out, err
        except TimeoutError:
            proc.kill()
            return False, "", f"git timed out after {timeout}s"
    except FileNotFoundError:
        return False, "", "git not found in PATH"
    except Exception as e:
        return False, "", str(e)


def _ok(op: str, data: dict, message: str | None = None, next_steps: list[str] | None = None) -> dict[str, Any]:
    return success_response(data, op, message=message, next_steps=next_steps or [])


def _err(op: str, msg: str, **kw) -> dict[str, Any]:
    return error_response(op, msg, **kw)


async def _simple(repo: Path, op: str, args: list[str], timeout: int = 60) -> dict[str, Any]:
    ok, out, err = await _run_git_async(repo, args, timeout)
    if not ok:
        return _err(op, (err or out).strip() or f"{op} failed")
    return _ok(op, {"output": out.strip()})


async def _simple_async(repo: Path, op: str, args: list[str], timeout: int = 60) -> dict[str, Any]:
    """Async version — uses asyncio.create_subprocess_exec directly."""
    ok, out, err = await _run_git_async(repo, args, timeout)
    if not ok:
        return _err(op, (err or out).strip() or f"{op} failed")
    return _ok(op, {"output": out.strip()})


async def git_ops(
    operation: str,
    repo_path: str | None = None,
    # add / commit
    message: str | None = None,
    files: list[str] | None = None,
    all_files: bool = False,
    amend: bool = False,
    # push / pull / fetch
    remote: str = "origin",
    branch: str | None = None,
    force: bool = False,
    set_upstream: bool = False,
    # clone / init
    repo_url: str | None = None,
    target_dir: str | None = None,
    initial_branch: str = "main",
    depth: int | None = None,  # shallow clone depth; None = full clone
    # log / diff / show / blame
    max_count: int = 20,
    commit: str | None = None,
    commit2: str | None = None,
    oneline: bool = False,
    file_path: str | None = None,
    # branch
    source_branch: str | None = None,
    # stash
    stash_message: str | None = None,
    stash_index: int = 0,
    # tag
    tag_name: str | None = None,
    tag_message: str | None = None,
    # reset
    mode: str = "mixed",
    # remote
    remote_url: str | None = None,
    remote_name: str | None = None,
    # clean
    dry_run: bool = False,
    include_dirs: bool = False,
    # submodule
    submodule_url: str | None = None,
    submodule_path: str | None = None,
    recursive: bool = False,
    # worktree
    worktree_path: str | None = None,
) -> dict[str, Any]:
    """Git local operations — 44 actions.

    CORE:      init, clone, add, commit, push, pull, fetch, status
    INSPECT:   log, diff, show, blame
    BRANCH:    branch_list, branch_create, branch_switch, branch_delete, branch_rename, branch_merge, rebase
    REMOTE:    remote_list, remote_add, remote_remove
    STASH:     stash, stash_pop, stash_list, stash_drop
    TAG:       tag_list, tag_create, tag_delete
    UNDO:      reset, revert, cherry_pick
    CLEANUP:   clean
    SUBMODULE: submodule_add, submodule_update, submodule_sync, submodule_status
    BISECT:    bisect_start, bisect_bad, bisect_good, bisect_reset
    WORKTREE:  worktree_add, worktree_list, worktree_remove
    """
    if operation not in ACTION_TYPE:
        return _err(operation, f"Unknown operation. Valid: {', '.join(sorted(ACTION_TYPE))}")

    repo = Path(repo_path or ".").resolve()

    # ── Actions that don't need an existing repo ──────────────────────────────
    if operation == "init":
        try:
            repo.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return _err("init", f"mkdir failed: {e}")
        ok, out, err = await _run_git_async(repo, ["init", "-b", initial_branch])
        if not ok:
            ok, out, err = await _run_git_async(repo, ["init"])  # fallback for older git
        if not ok:
            return _err("init", err or "git init failed")
        return _ok(
            "init",
            {"path": str(repo), "output": out.strip()},
            next_steps=[f"git_ops(operation='add', all_files=True, repo_path='{repo}')"],
        )

    if operation == "clone":
        if not repo_url:
            return _err("clone", "repo_url required")
        base = Path(target_dir).parent.resolve() if target_dir else Path.cwd()
        args = ["clone", repo_url]
        if branch:
            args = ["clone", "-b", branch, repo_url]
        if depth is not None:
            args.insert(1, "--depth")
            args.insert(2, str(depth))
        if target_dir:
            args.append(str(Path(target_dir).resolve()))
        ok, out, err = await _run_git_async(base, args, timeout=120)
        if not ok:
            raw_msg = (err or out).strip()
            if "timed out" in raw_msg:
                ps_cmd = f"& 'C:\\Program Files\\Git\\cmd\\git.exe' clone --depth 1 {repo_url}"
                return _err(
                    "clone",
                    (
                        f"Clone timed out after 120s â€” repository is likely large or connection is slow. "
                        f"Try a shallow clone to get just the current tree without full history. "
                        f"PowerShell fallback: {ps_cmd}"
                    ),
                    recovery_options=[
                        "Pass depth=1 to this tool for a shallow clone (fast, current tree only)",
                        "Clone manually: git clone --depth 1 " + repo_url,
                        "Check connection â€” large repos need stable bandwidth",
                    ],
                )
            return _err(
                "clone",
                raw_msg or "clone failed",
                recovery_options=["Check URL", "gh auth login", "Check network"],
            )
        dest = target_dir or repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        return _ok(
            "clone",
            {"url": repo_url, "path": str(dest), "output": (out + err).strip()},
            next_steps=[f"git_ops(operation='status', repo_path='{dest}')"],
        )

    # ── Validate repo for all other operations ────────────────────────────────
    if not (repo / ".git").exists():
        return _err(
            operation,
            f"Not a git repository: {repo}",
            suggested_fixes=[
                "git_ops(operation='init')",
                "git_ops(operation='clone', repo_url='...')",
            ],
        )

    # ── Core ──────────────────────────────────────────────────────────────────
    if operation == "status":
        ok, out, err = await _run_git_async(repo, ["status", "--porcelain"])
        if not ok:
            return _err("status", err or "status failed")

        staged: list[dict[str, str]] = []
        unstaged: list[dict[str, str]] = []
        untracked: list[str] = []
        unmerged: list[dict[str, str]] = []

        # High-fidelity Porcelain parsing (v1.20)
        # XY | Path
        # X = Index (Staged), Y = Worktree (Unstaged)
        for line in out.splitlines():
            if not line or len(line) < 4:
                continue

            x, y = line[0], line[1]
            path_str = line[3:].strip()

            # Untracked (??)
            if x == "?" and y == "?":
                untracked.append(path_str)
                continue

            # Unmerged (DD, AU, UD, UA, DU, AA, UU)
            if x in "ADU" and y in "ADU":
                state = "unmerged"
                unmerged.append({"file": path_str, "state": state, "code": f"{x}{y}"})
                continue

            # Staged changes (X is not space)
            if x != " ":
                state = "modified"
                if x == "A":
                    state = "added"
                if x == "D":
                    state = "deleted"
                if x == "R":
                    state = "renamed"
                if x == "C":
                    state = "copied"
                staged.append({"file": path_str, "state": state, "code": x})

            # Unstaged changes (Y is not space)
            if y != " ":
                state = "modified"
                if y == "D":
                    state = "deleted"
                if y == "A":
                    state = "added"  # Intent-to-add
                unstaged.append({"file": path_str, "state": state, "code": y})

        _, branch_out, _ = await _run_git_async(repo, ["branch", "--show-current"])
        _, remote_out, _ = await _run_git_async(repo, ["remote", "get-url", "origin"])

        return _ok(
            "status",
            {
                "branch": branch_out.strip(),
                "remote_url": remote_out.strip(),
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked,
                "unmerged": unmerged,
                "staged_count": len(staged),
                "unstaged_count": len(unstaged),
                "untracked_count": len(untracked),
                "unmerged_count": len(unmerged),
                "has_changes": bool(staged or unstaged or untracked or unmerged),
                "total_changes": len(staged) + len(unstaged) + len(untracked) + len(unmerged),
            },
        )

    if operation == "add":
        if all_files:
            ok, _, err = await _run_git_async(repo, ["add", "."])
            if not ok:
                return _err("add", err or "add . failed")
            return _ok(
                "add",
                {"staged": "all files"},
                next_steps=[f"git_ops(operation='commit', message='...', repo_path='{repo}')"],
            )
        if not files:
            return _err("add", "Provide files list or set all_files=True")
        ok, _, err = await _run_git_async(repo, ["add", *files])
        if not ok:
            return _err("add", err or "add failed")
        return _ok(
            "add",
            {"staged_files": files, "count": len(files)},
            next_steps=[f"git_ops(operation='commit', message='...', repo_path='{repo}')"],
        )

    if operation == "commit":
        if not message and not amend:
            return _err("commit", "message required (or set amend=True)")
        cmd = ["commit"]
        if amend:
            cmd.append("--amend")
            if not message:
                cmd.append("--no-edit")
        if message:
            cmd += ["-m", message]
        if all_files:
            cmd.insert(1, "-a")
        ok, out, err = await _run_git_async(repo, cmd)
        if not ok:
            return _err("commit", (err or out).strip() or "commit failed")
        return _ok(
            "commit",
            {"message": message, "output": out.strip(), "amended": amend},
            next_steps=[f"git_ops(operation='push', repo_path='{repo}')"],
        )

    if operation == "push":
        cmd = ["push"]
        if force:
            cmd.append("--force-with-lease")
        if set_upstream:
            cmd += ["-u", remote, branch or "HEAD"]
        else:
            cmd.append(remote)
            if branch:
                cmd.append(branch)
        ok, out, err = await _run_git_async(repo, cmd, timeout=60)
        if not ok:
            return _err(
                "push",
                (err or out).strip() or "push failed",
                recovery_options=["Check remote", "gh auth login", "git pull first"],
            )
        return _ok(
            "push",
            {"remote": remote, "branch": branch, "forced": force, "output": (out + err).strip()},
        )

    if operation == "pull":
        args = ["pull", remote] + ([branch] if branch else [])
        return await _simple_async(repo, "pull", args)

    if operation == "fetch":
        return await _simple_async(repo, "fetch", ["fetch", remote])

    # ── Inspect ───────────────────────────────────────────────────────────────
    if operation == "log":
        fmt = "--oneline" if oneline else "--pretty=format:%H|%an|%ae|%ad|%s"
        cmd = ["log", f"-{max_count}", fmt, "--date=short"]
        if branch:
            cmd.append(branch)
        ok, out, err = await _run_git_async(repo, cmd)
        if not ok:
            return _err("log", err or "log failed")
        if oneline:
            entries = [{"line": line_} for line_ in out.strip().splitlines() if line_]
        else:
            entries = []
            for line in out.strip().splitlines():
                parts = line.split("|", 4)
                if len(parts) == 5:
                    entries.append(
                        {
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "date": parts[3],
                            "subject": parts[4],
                        }
                    )
                else:
                    entries.append({"raw": line})
        return _ok("log", {"count": len(entries), "entries": entries})

    if operation == "diff":
        cmd = ["diff"]
        if commit and commit2:
            cmd += [commit, commit2]
        elif commit:
            cmd.append(commit)
        if files:
            cmd.extend(["--", *files])
        ok, out, err = await _run_git_async(repo, cmd)
        if not ok:
            return _err("diff", err or "diff failed")
        return _ok("diff", {"diff": out, "lines": len(out.splitlines())})

    if operation == "show":
        return await _simple_async(repo, "show", ["show", "--stat", commit or "HEAD"])

    if operation == "blame":
        if not file_path:
            return _err("blame", "file_path required")
        cmd = ["blame", "--line-porcelain", file_path]
        if commit:
            cmd.insert(1, commit)
        ok, out, err = await _run_git_async(repo, cmd)
        if not ok:
            return _err("blame", err or "blame failed")
        # Parse porcelain output into structured lines
        lines_data = []
        current: dict = {}
        for line in out.splitlines():
            if not line:
                continue
            if line.startswith("\t"):
                current["content"] = line[1:]
                lines_data.append(current)
                current = {}
            elif " " in line and not current:
                parts = line.split(" ", 3)
                if len(parts) >= 4:
                    current = {
                        "commit": parts[0],
                        "orig_line": parts[1],
                        "final_line": parts[2],
                        "group_size": parts[3],
                    }
                else:
                    current = {"commit": parts[0]}
            elif line.startswith("author "):
                current["author"] = line[7:]
            elif line.startswith("author-time "):
                current["author_time"] = line[12:]
            elif line.startswith("summary "):
                current["summary"] = line[8:]
        return _ok("blame", {"file": file_path, "lines": lines_data, "count": len(lines_data)})

    # ── Branch ────────────────────────────────────────────────────────────────
    if operation == "branch_list":
        return await _simple_async(repo, "branch_list", ["branch", "-a", "-v"])

    if operation == "branch_create":
        if not branch:
            return _err("branch_create", "branch required")
        cmd = ["checkout", "-b", branch] + ([source_branch] if source_branch else [])
        return await _simple_async(repo, "branch_create", cmd)

    if operation == "branch_switch":
        if not branch:
            return _err("branch_switch", "branch required")
        return await _simple_async(repo, "branch_switch", ["checkout", branch])

    if operation == "branch_delete":
        if not branch:
            return _err("branch_delete", "branch required")
        return await _simple_async(repo, "branch_delete", ["branch", "-D" if force else "-d", branch])

    if operation == "branch_rename":
        if not branch or not source_branch:
            return _err("branch_rename", "branch (old name) and source_branch (new name) required")
        return await _simple_async(repo, "branch_rename", ["branch", "-m", branch, source_branch])

    if operation == "branch_merge":
        if not source_branch:
            return _err("branch_merge", "source_branch required")
        cmd = ["merge", source_branch] + (["-m", message] if message else [])
        return await _simple_async(repo, "branch_merge", cmd)

    if operation == "rebase":
        if not source_branch:
            return _err("rebase", "source_branch required")
        return await _simple_async(repo, "rebase", ["rebase", source_branch])

    # ── Remote ────────────────────────────────────────────────────────────────
    if operation == "remote_list":
        return await _simple_async(repo, "remote_list", ["remote", "-v"])

    if operation == "remote_add":
        name = remote_name or "origin"
        if not remote_url:
            return _err("remote_add", "remote_url required")
        return await _simple_async(repo, "remote_add", ["remote", "add", name, remote_url])

    if operation == "remote_remove":
        name = remote_name or remote
        return await _simple_async(repo, "remote_remove", ["remote", "remove", name])

    # ── Stash ─────────────────────────────────────────────────────────────────
    if operation == "stash":
        cmd = ["stash", "push"] + (["-m", stash_message] if stash_message else [])
        return await _simple_async(repo, "stash", cmd)

    if operation == "stash_pop":
        return await _simple_async(repo, "stash_pop", ["stash", "pop", f"stash@{{{stash_index}}}"])

    if operation == "stash_list":
        return await _simple_async(repo, "stash_list", ["stash", "list"])

    if operation == "stash_drop":
        return await _simple_async(repo, "stash_drop", ["stash", "drop", f"stash@{{{stash_index}}}"])

    # ── Tag ───────────────────────────────────────────────────────────────────
    if operation == "tag_list":
        return await _simple_async(repo, "tag_list", ["tag", "-l", "-n1"])

    if operation == "tag_create":
        if not tag_name:
            return _err("tag_create", "tag_name required")
        cmd = ["tag", "-a", tag_name, "-m", tag_message or tag_name] if tag_message else ["tag", tag_name]
        if commit:
            cmd.append(commit)
        return await _simple_async(repo, "tag_create", cmd)

    if operation == "tag_delete":
        if not tag_name:
            return _err("tag_delete", "tag_name required")
        return await _simple_async(repo, "tag_delete", ["tag", "-d", tag_name])

    # ── Undo ─────────────────────────────────────────────────────────────────
    if operation == "reset":
        if mode not in ("soft", "mixed", "hard"):
            return _err("reset", "mode must be soft, mixed, or hard")
        return await _simple_async(repo, "reset", ["reset", f"--{mode}", commit or "HEAD"])

    if operation == "revert":
        if not commit:
            return _err("revert", "commit required")
        return await _simple_async(repo, "revert", ["revert", "--no-edit", commit])

    if operation == "cherry_pick":
        if not commit:
            return _err("cherry_pick", "commit required")
        return await _simple_async(repo, "cherry_pick", ["cherry-pick", commit])

    # ── Cleanup ───────────────────────────────────────────────────────────────
    if operation == "clean":
        # Remove untracked files (and optionally dirs)
        cmd = ["clean", "-f"]
        if include_dirs:
            cmd.append("-d")
        if dry_run:
            cmd_dry = [*cmd, "--dry-run"]
            ok, out, err = await _run_git_async(repo, cmd_dry)
            if not ok:
                return _err("clean", err or "clean dry-run failed")
            return _ok("clean", {"dry_run": True, "would_remove": out.strip().splitlines()})
        ok, out, err = await _run_git_async(repo, cmd)
        if not ok:
            return _err("clean", err or "clean failed")
        return _ok(
            "clean",
            {"output": out.strip(), "include_dirs": include_dirs},
            message="Untracked files removed",
        )

    # ── Submodule ─────────────────────────────────────────────────────────────
    if operation == "submodule_add":
        if not submodule_url:
            return _err("submodule_add", "submodule_url required")
        cmd = ["submodule", "add", submodule_url]
        if submodule_path:
            cmd.append(submodule_path)
        return await _simple_async(repo, "submodule_add", cmd)

    if operation == "submodule_update":
        cmd = ["submodule", "update", "--init"]
        if recursive:
            cmd.append("--recursive")
        return await _simple_async(repo, "submodule_update", cmd)

    if operation == "submodule_sync":
        cmd = ["submodule", "sync"]
        if recursive:
            cmd.append("--recursive")
        return await _simple_async(repo, "submodule_sync", cmd)

    if operation == "submodule_status":
        return await _simple_async(repo, "submodule_status", ["submodule", "status"])

    # ── Bisect ────────────────────────────────────────────────────────────────
    if operation == "bisect_start":
        return await _simple_async(repo, "bisect_start", ["bisect", "start"])

    if operation == "bisect_bad":
        cmd = ["bisect", "bad"] + ([commit] if commit else [])
        return await _simple_async(repo, "bisect_bad", cmd)

    if operation == "bisect_good":
        cmd = ["bisect", "good"] + ([commit] if commit else [])
        return await _simple_async(repo, "bisect_good", cmd)

    if operation == "bisect_reset":
        return await _simple_async(repo, "bisect_reset", ["bisect", "reset"])

    # ── Worktree ──────────────────────────────────────────────────────────────
    if operation == "worktree_add":
        if not worktree_path:
            return _err("worktree_add", "worktree_path required")
        cmd = ["worktree", "add", worktree_path]
        if branch:
            cmd.append(branch)
        return await _simple_async(repo, "worktree_add", cmd)

    if operation == "worktree_list":
        return await _simple_async(repo, "worktree_list", ["worktree", "list"])

    if operation == "worktree_remove":
        if not worktree_path:
            return _err("worktree_remove", "worktree_path required")
        cmd = ["worktree", "remove"] + (["--force"] if force else []) + [worktree_path]
        return await _simple_async(repo, "worktree_remove", cmd)

    return _err(operation, "Not implemented")
