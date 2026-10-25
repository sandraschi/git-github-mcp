"""Tests for git_ops."""

import os
import subprocess
import tempfile
from importlib import import_module as _import_module
from pathlib import Path

# NOTE: git_github_mcp.tools.__init__ re-exports the git_ops function,
# shadowing the submodule attribute — importlib gets the real module.
git_ops_mod = _import_module("git_github_mcp.tools.git_ops")
from git_github_mcp.tools.git_ops import _check_git_dir, _git_env, git_env_hijack_present, git_ops

_GIT = git_ops_mod._GIT_EXE


def _raw(*args: str, cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run([_GIT, *args], cwd=cwd, capture_output=True, text=True, timeout=60)


async def _init_repo(path: str, *files: str) -> None:
    r = await git_ops(operation="init", repo_path=path)
    assert r["success"], r
    for f in files:
        (Path(path) / f).write_text("v1")
    r = await git_ops(operation="add", repo_path=path, all_files=True)
    assert r["success"], r
    os.environ["GITOPS_USER_NAME"] = "Test Bot"
    os.environ["GITOPS_USER_EMAIL"] = "bot@example.com"
    try:
        r = await git_ops(operation="commit", repo_path=path, message="init")
        assert r["success"], r
    finally:
        del os.environ["GITOPS_USER_NAME"]
        del os.environ["GITOPS_USER_EMAIL"]


async def test_git_ops_status_not_a_repo() -> None:
    """Status on non-repo returns error."""
    with tempfile.TemporaryDirectory() as tmp:
        result = await git_ops(operation="status", repo_path=tmp)
    assert result["success"] is False
    assert "git repository" in result["error"].lower()


async def test_git_ops_unknown_operation() -> None:
    """Unknown operation returns error."""
    result = await git_ops(operation="unknown")
    assert result["success"] is False
    assert "Unknown operation" in result["error"]


async def test_git_ops_commit_needs_message() -> None:
    """Commit without message returns error."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".git").mkdir()
        result = await git_ops(operation="commit", repo_path=tmp)
    assert result["success"] is False
    assert "message required" in result["error"]


async def test_git_ops_clone_needs_repo_url() -> None:
    """Clone without repo_url returns error."""
    result = await git_ops(operation="clone")
    assert result["success"] is False
    assert "repo_url required" in result["error"]


# ── Issue #3: add must verify the index, never echo inputs ───────────────────


async def test_add_stages_and_reports_truthfully() -> None:
    """Modified tracked file: success + actually-staged list, count matches index."""
    with tempfile.TemporaryDirectory() as tmp:
        await _init_repo(tmp, "f.txt")
        (Path(tmp) / "f.txt").write_text("v2")
        r = await git_ops(operation="add", repo_path=tmp, files=["f.txt"])
        assert r["success"] is True, r
        assert r["result"]["staged_files"] == ["f.txt"]
        assert r["result"]["count"] == 1
        st = await git_ops(operation="status", repo_path=tmp)
        assert st["result"]["staged_count"] == 1
        assert st["result"]["unstaged_count"] == 0


async def test_add_already_clean_says_so() -> None:
    """Clean file: success, count 0, explicit already-clean note — never a bare echo."""
    with tempfile.TemporaryDirectory() as tmp:
        await _init_repo(tmp, "f.txt")
        r = await git_ops(operation="add", repo_path=tmp, files=["f.txt"])
        assert r["success"] is True, r
        assert r["result"]["count"] == 0
        assert "f.txt" in r["result"]["already_clean"]
        assert "already" in (r.get("message") or "").lower()


async def test_add_missing_file_fails_loud() -> None:
    """Nonexistent path: loud failure naming the file."""
    with tempfile.TemporaryDirectory() as tmp:
        await _init_repo(tmp, "f.txt")
        r = await git_ops(operation="add", repo_path=tmp, files=["nope.txt"])
        assert r["success"] is False, r
        assert "nope.txt" in r["error"]


async def test_add_ignores_inherited_git_dir() -> None:
    """Killer e2e for #3: GIT_DIR/GIT_INDEX_FILE pointing at repo S must not
    redirect an add targeting repo R — repo_path is authoritative."""
    with tempfile.TemporaryDirectory() as tmp:
        r_dir, s_dir = str(Path(tmp) / "R"), str(Path(tmp) / "S")
        Path(r_dir).mkdir()
        Path(s_dir).mkdir()
        await _init_repo(r_dir, "f.txt")
        await _init_repo(s_dir, "other.txt")
        (Path(r_dir) / "f.txt").write_text("v2")
        saved = {k: os.environ.get(k) for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
        os.environ["GIT_DIR"] = str(Path(s_dir) / ".git")
        os.environ["GIT_INDEX_FILE"] = str(Path(tmp) / "alt-index")
        try:
            r = await git_ops(operation="add", repo_path=r_dir, files=["f.txt"])
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        assert r["success"] is True, r
        assert r["result"]["staged_files"] == ["f.txt"]
        assert _raw("diff", "--cached", "--name-only", cwd=r_dir).stdout.split() == ["f.txt"]
        assert _raw("diff", "--cached", "--name-only", cwd=s_dir).stdout.split() == []


def test_git_env_scrubs_discovery_hijackers(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """_git_env drops index-discovery vars but keeps identity + our own vars."""
    for k, v in {
        "GIT_DIR": "/elsewhere",
        "GIT_WORK_TREE": "/elsewhere",
        "GIT_INDEX_FILE": "Z:/nonexistent/alt-index",
        "GIT_COMMON_DIR": "/elsewhere",
        "GIT_PREFIX": "sub/",
        "GIT_NAMESPACE": "ns",
        "GIT_OBJECT_DIRECTORY": "/o",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": "/a",
        "GIT_CEILING_DIRECTORIES": "/",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "a.b",
        "GIT_CONFIG_VALUE_0": "c",
        "GIT_AUTHOR_NAME": "Kept",
    }.items():
        monkeypatch.setenv(k, v)
    env = _git_env()
    for k in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
        "GIT_NAMESPACE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0",
        "GIT_CONFIG_VALUE_0",
    ):
        assert k not in env, k
    assert env["GIT_AUTHOR_NAME"] == "Kept"
    assert env["GIT_TERMINAL_PROMPT"] == "0"


async def test_add_loud_when_index_differs(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Mocked runner: add exits 0 but worktree still differs → success False.

    This is the exact anti-regression for #3's silent success.
    """

    async def fake_runner(path, args, timeout=60):  # type: ignore[no-untyped-def]
        if args[:2] == ["rev-parse", "--absolute-git-dir"]:
            return True, str(Path(path) / ".git") + "\n", ""
        if args[0] == "add":
            return True, "", ""
        if args[:2] == ["diff", "--name-only"]:
            return True, "f.txt\n", ""
        if args[:2] == ["diff", "--cached"]:
            return True, "", ""
        raise AssertionError(args)

    monkeypatch.setattr(git_ops_mod, "_run_git_async", fake_runner)
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".git").mkdir()  # pass the repo-shape check; runner is mocked
        r = await git_ops(operation="add", repo_path=tmp, files=["f.txt"])
    assert r["success"] is False, r
    assert "f.txt" in r["error"]
    assert "unstaged" in r["error"].lower() or "differ" in r["error"].lower()


# ── Issue #3 follow-up: pre-flight git-dir identity + startup probe ─────────


async def test_check_git_dir_ok_real_repo() -> None:
    """Pre-flight passes on a genuine checkout."""
    with tempfile.TemporaryDirectory() as tmp:
        await _init_repo(tmp, "f.txt")
        assert await _check_git_dir(Path(tmp)) is None


async def test_mutating_op_refuses_foreign_git_dir(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """rev-parse pointing elsewhere → add refuses BEFORE touching anything."""

    async def fake_runner(path, args, timeout=60):  # type: ignore[no-untyped-def]
        if args[:2] == ["rev-parse", "--absolute-git-dir"]:
            return True, "Z:/elsewhere/.git\n", ""
        raise AssertionError(f"must not run git beyond rev-parse: {args}")

    with tempfile.TemporaryDirectory() as tmp:
        await _init_repo(tmp, "f.txt")  # real runner still in place here
        monkeypatch.setattr(git_ops_mod, "_run_git_async", fake_runner)
        (Path(tmp) / "f.txt").write_text("v2")
        r = await git_ops(operation="add", repo_path=tmp, files=["f.txt"])
    assert r["success"] is False, r
    assert "different repository" in r["error"]
    assert "Z:/elsewhere/.git" in r["error"]


def test_git_env_hijack_present_flags_vars(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Probe helper flags hijack vars; clean env reports none."""
    monkeypatch.setenv("GIT_DIR", "/elsewhere")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "a.b")
    flagged = git_env_hijack_present()
    assert "GIT_DIR" in flagged
    assert "GIT_CONFIG_KEY_0" in flagged
    assert "GIT_AUTHOR_NAME" not in flagged
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_CONFIG_KEY_0")
    assert git_env_hijack_present() == []
