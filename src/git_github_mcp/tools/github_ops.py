"""GitHub operations portmanteau via gh CLI.

Requires: gh auth login (https://cli.github.com)
"""

import json
from pathlib import Path
from typing import Any

from ..utils.gh_cli import run_gh
from ..utils.response import success_response, error_response

ACTION_TYPE = (
    # Repos
    "repo_list", "repo_view", "repo_create", "repo_fork", "repo_clone",
    "repo_delete", "repo_rename", "repo_archive",
    # Issues
    "issue_list", "issue_view", "issue_create", "issue_close", "issue_comment",
    # PRs
    "pr_list", "pr_view", "pr_create", "pr_merge", "pr_checkout",
    "pr_close", "pr_comment",
    # Releases
    "release_list", "release_view", "release_create",
    "release_delete", "release_update",
    # Workflows (Actions)
    "workflow_list", "workflow_run", "workflow_runs",
    "workflow_cancel", "workflow_disable", "workflow_enable",
    # Labels
    "label_list", "label_create", "label_delete",
    # Secrets
    "secrets_list", "secrets_set", "secrets_delete",
    # Collaborators
    "collaborator_add", "collaborator_remove",
    # Search
    "search_repos", "search_issues", "search_code",
    # Auth / misc
    "auth_status", "gist_list",
)


def _j(s: str) -> Any:
    """Parse JSON safely."""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return []


def _ok(op: str, data: dict, msg: str | None = None, next_steps: list | None = None) -> dict:
    return success_response(data, op, message=msg, next_steps=next_steps or [])


def _err(op: str, msg: str, **kw) -> dict:
    return error_response(op, msg, **kw)


def _repo_arg(owner: str | None, repo: str | None) -> str | None:
    if owner and repo:
        return f"{owner}/{repo}"
    return None


def github_ops(
    operation: str,
    # Repo identifiers
    owner: str | None = None,
    repo: str | None = None,
    # Issue / PR fields
    title: str | None = None,
    body: str | None = None,
    issue_number: int | None = None,
    pr_number: int | None = None,
    # Lists / filters
    state: str = "open",
    limit: int = 20,
    label: str | None = None,
    assignee: str | None = None,
    # Repo create / rename
    description: str | None = None,
    private: bool = False,
    new_name: str | None = None,
    # PR
    base_branch: str | None = None,
    head_branch: str | None = None,
    draft: bool = False,
    merge_method: str = "merge",   # merge | squash | rebase
    # Release
    tag_name: str | None = None,
    release_name: str | None = None,
    prerelease: bool = False,
    # Search
    query: str | None = None,
    # Workflow
    workflow_id: str | None = None,
    run_id: str | None = None,
    ref: str | None = None,
    # Clone target
    target_dir: str | None = None,
    # Secrets
    secret_name: str | None = None,
    secret_value: str | None = None,
    # Collaborators
    username: str | None = None,
    permission: str = "push",   # pull | push | admin | maintain | triage
    # Labels
    label_name: str | None = None,
    label_color: str | None = None,
    label_description: str | None = None,
) -> dict[str, Any]:
    """GitHub operations via gh CLI — 43 actions.

    REPOS:         repo_list, repo_view, repo_create, repo_fork, repo_clone,
                   repo_delete, repo_rename, repo_archive
    ISSUES:        issue_list, issue_view, issue_create, issue_close, issue_comment
    PRs:           pr_list, pr_view, pr_create, pr_merge, pr_checkout, pr_close, pr_comment
    RELEASES:      release_list, release_view, release_create, release_delete, release_update
    ACTIONS:       workflow_list, workflow_run, workflow_runs,
                   workflow_cancel, workflow_disable, workflow_enable
    LABELS:        label_list, label_create, label_delete
    SECRETS:       secrets_list, secrets_set, secrets_delete
    COLLABORATORS: collaborator_add, collaborator_remove
    SEARCH:        search_repos, search_issues, search_code
    MISC:          auth_status, gist_list

    Requires gh CLI: https://cli.github.com — run 'gh auth login' first.
    """
    if operation not in ACTION_TYPE:
        return _err(operation, f"Unknown operation. Valid: {', '.join(sorted(ACTION_TYPE))}")

    slug = _repo_arg(owner, repo)

    # ── Auth / misc ───────────────────────────────────────────────────────────
    if operation == "auth_status":
        ok, out, err = run_gh(["auth", "status"])
        return _ok("auth_status", {"output": (out + err).strip(), "authenticated": ok})

    if operation == "gist_list":
        ok, out, err = run_gh(["gist", "list", "--limit", str(limit),
                                "--json", "id,description,public,updatedAt"])
        if not ok: return _err("gist_list", err or "gist list failed")
        return _ok("gist_list", {"gists": _j(out), "count": len(_j(out))})

    # ── Repos ─────────────────────────────────────────────────────────────────
    if operation == "repo_list":
        args = ["repo", "list", "--limit", str(limit),
                "--json", "name,description,isPrivate,stargazerCount,updatedAt,url,defaultBranchRef"]
        if owner: args.insert(2, owner)
        ok, out, err = run_gh(args)
        if not ok: return _err("repo_list", err or "repo list failed")
        data = _j(out)
        return _ok("repo_list", {"repos": data, "count": len(data)},
                   next_steps=["github_ops(operation='repo_view', owner='...', repo='...')"])

    if operation == "repo_view":
        if not slug: return _err("repo_view", "owner and repo required")
        ok, out, err = run_gh(["repo", "view", slug,
                                "--json", "name,description,isPrivate,stargazerCount,forkCount,"
                                          "issues,url,sshUrl,defaultBranchRef,languages,repositoryTopics"])
        if not ok: return _err("repo_view", err or "repo view failed")
        return _ok("repo_view", _j(out) if isinstance(_j(out), dict) else {"raw": out.strip()})

    if operation == "repo_create":
        if not repo: return _err("repo_create", "repo (name) required")
        args = ["repo", "create", repo, "--confirm"]
        if description: args += ["--description", description]
        args.append("--private" if private else "--public")
        ok, out, err = run_gh(args)
        if not ok: return _err("repo_create", err or "repo create failed",
                               recovery_options=["Check gh auth", "Name may be taken"])
        return _ok("repo_create", {"url": out.strip()}, message="Repository created")

    if operation == "repo_fork":
        if not slug: return _err("repo_fork", "owner and repo required")
        args = ["repo", "fork", slug, "--clone=false"]
        ok, out, err = run_gh(args)
        if not ok: return _err("repo_fork", err or "fork failed")
        return _ok("repo_fork", {"output": (out + err).strip()}, message="Forked")

    if operation == "repo_clone":
        if not slug: return _err("repo_clone", "owner and repo required")
        args = ["repo", "clone", slug]
        if target_dir: args.append(target_dir)
        ok, out, err = run_gh(args, timeout=120)
        if not ok: return _err("repo_clone", err or "clone failed")
        return _ok("repo_clone", {"output": (out + err).strip()})

    if operation == "repo_delete":
        if not slug: return _err("repo_delete", "owner and repo required")
        ok, out, err = run_gh(["repo", "delete", slug, "--yes"])
        if not ok: return _err("repo_delete", err or "repo delete failed",
                               recovery_options=["Check gh auth", "Requires admin access"])
        return _ok("repo_delete", {"repo": slug}, message=f"Repository {slug} deleted")

    if operation == "repo_rename":
        if not slug: return _err("repo_rename", "owner and repo required")
        if not new_name: return _err("repo_rename", "new_name required")
        ok, out, err = run_gh(["repo", "rename", new_name, "--repo", slug, "--yes"])
        if not ok: return _err("repo_rename", err or "repo rename failed")
        return _ok("repo_rename", {"old_name": repo, "new_name": new_name, "output": out.strip()},
                   message=f"Repository renamed to {new_name}")

    if operation == "repo_archive":
        if not slug: return _err("repo_archive", "owner and repo required")
        ok, out, err = run_gh(["repo", "archive", slug, "--yes"])
        if not ok: return _err("repo_archive", err or "repo archive failed")
        return _ok("repo_archive", {"repo": slug}, message=f"Repository {slug} archived")

    # ── Issues ────────────────────────────────────────────────────────────────
    if operation == "issue_list":
        if not slug: return _err("issue_list", "owner and repo required")
        args = ["issue", "list", "--repo", slug, "--state", state, "--limit", str(limit),
                "--json", "number,title,state,url,author,labels,assignees,createdAt,updatedAt"]
        if label: args += ["--label", label]
        if assignee: args += ["--assignee", assignee]
        ok, out, err = run_gh(args)
        if not ok: return _err("issue_list", err or "issue list failed")
        data = _j(out)
        return _ok("issue_list", {"issues": data, "count": len(data)})

    if operation == "issue_view":
        if not slug or not issue_number: return _err("issue_view", "owner, repo, issue_number required")
        ok, out, err = run_gh(["issue", "view", str(issue_number), "--repo", slug,
                                "--json", "number,title,body,state,url,author,labels,assignees,"
                                          "comments,createdAt,updatedAt"])
        if not ok: return _err("issue_view", err or "issue view failed")
        return _ok("issue_view", _j(out) if isinstance(_j(out), dict) else {"raw": out.strip()})

    if operation == "issue_create":
        if not slug or not title: return _err("issue_create", "owner, repo, title required")
        args = ["issue", "create", "--repo", slug, "--title", title]
        if body: args += ["--body", body]
        if label: args += ["--label", label]
        if assignee: args += ["--assignee", assignee]
        ok, out, err = run_gh(args)
        if not ok: return _err("issue_create", err or "issue create failed",
                               recovery_options=["gh auth login", "Check repo access"])
        return _ok("issue_create", {"url": out.strip(), "title": title}, message="Issue created")

    if operation == "issue_close":
        if not slug or not issue_number: return _err("issue_close", "owner, repo, issue_number required")
        args = ["issue", "close", str(issue_number), "--repo", slug]
        if body: args += ["--comment", body]
        ok, out, err = run_gh(args)
        if not ok: return _err("issue_close", err or "close failed")
        return _ok("issue_close", {"issue_number": issue_number}, message="Issue closed")

    if operation == "issue_comment":
        if not slug or not issue_number or not body:
            return _err("issue_comment", "owner, repo, issue_number, body required")
        ok, out, err = run_gh(["issue", "comment", str(issue_number), "--repo", slug, "--body", body])
        if not ok: return _err("issue_comment", err or "comment failed")
        return _ok("issue_comment", {"url": out.strip()}, message="Comment added")

    # ── PRs ───────────────────────────────────────────────────────────────────
    if operation == "pr_list":
        if not slug: return _err("pr_list", "owner and repo required")
        args = ["pr", "list", "--repo", slug, "--state", state, "--limit", str(limit),
                "--json", "number,title,state,url,author,headRefName,baseRefName,isDraft,createdAt"]
        ok, out, err = run_gh(args)
        if not ok: return _err("pr_list", err or "pr list failed")
        data = _j(out)
        return _ok("pr_list", {"prs": data, "count": len(data)})

    if operation == "pr_view":
        if not slug or not pr_number: return _err("pr_view", "owner, repo, pr_number required")
        ok, out, err = run_gh(["pr", "view", str(pr_number), "--repo", slug,
                                "--json", "number,title,body,state,url,author,headRefName,"
                                          "baseRefName,isDraft,mergeable,comments,reviews,createdAt"])
        if not ok: return _err("pr_view", err or "pr view failed")
        return _ok("pr_view", _j(out) if isinstance(_j(out), dict) else {"raw": out.strip()})

    if operation == "pr_create":
        if not slug or not title: return _err("pr_create", "owner, repo, title required")
        args = ["pr", "create", "--repo", slug, "--title", title]
        if body: args += ["--body", body]
        if base_branch: args += ["--base", base_branch]
        if head_branch: args += ["--head", head_branch]
        if draft: args.append("--draft")
        ok, out, err = run_gh(args)
        if not ok: return _err("pr_create", err or "pr create failed",
                               recovery_options=["Push branch first", "gh auth login"])
        return _ok("pr_create", {"url": out.strip(), "title": title}, message="PR created")

    if operation == "pr_merge":
        if not slug or not pr_number: return _err("pr_merge", "owner, repo, pr_number required")
        method_flag = {"merge": "--merge", "squash": "--squash", "rebase": "--rebase"}.get(merge_method, "--merge")
        ok, out, err = run_gh(["pr", "merge", str(pr_number), "--repo", slug, method_flag, "--auto"])
        if not ok: return _err("pr_merge", err or "merge failed")
        return _ok("pr_merge", {"pr_number": pr_number, "method": merge_method}, message="PR merged")

    if operation == "pr_checkout":
        if not pr_number: return _err("pr_checkout", "pr_number required")
        args = ["pr", "checkout", str(pr_number)]
        if slug: args += ["--repo", slug]
        ok, out, err = run_gh(args)
        if not ok: return _err("pr_checkout", err or "checkout failed")
        return _ok("pr_checkout", {"pr_number": pr_number, "output": (out + err).strip()})

    if operation == "pr_close":
        if not slug or not pr_number: return _err("pr_close", "owner, repo, pr_number required")
        args = ["pr", "close", str(pr_number), "--repo", slug]
        if body: args += ["--comment", body]
        ok, out, err = run_gh(args)
        if not ok: return _err("pr_close", err or "pr close failed")
        return _ok("pr_close", {"pr_number": pr_number}, message="PR closed")

    if operation == "pr_comment":
        if not slug or not pr_number or not body:
            return _err("pr_comment", "owner, repo, pr_number, body required")
        ok, out, err = run_gh(["pr", "comment", str(pr_number), "--repo", slug, "--body", body])
        if not ok: return _err("pr_comment", err or "pr comment failed")
        return _ok("pr_comment", {"url": out.strip()}, message="PR comment added")

    # ── Releases ──────────────────────────────────────────────────────────────
    if operation == "release_list":
        if not slug: return _err("release_list", "owner and repo required")
        ok, out, err = run_gh(["release", "list", "--repo", slug, "--limit", str(limit),
                                "--json", "tagName,name,isDraft,isPrerelease,publishedAt,url"])
        if not ok: return _err("release_list", err or "release list failed")
        data = _j(out)
        return _ok("release_list", {"releases": data, "count": len(data)})

    if operation == "release_view":
        if not slug or not tag_name: return _err("release_view", "owner, repo, tag_name required")
        ok, out, err = run_gh(["release", "view", tag_name, "--repo", slug,
                                "--json", "tagName,name,body,isDraft,isPrerelease,publishedAt,url,assets"])
        if not ok: return _err("release_view", err or "release view failed")
        return _ok("release_view", _j(out) if isinstance(_j(out), dict) else {"raw": out.strip()})

    if operation == "release_create":
        if not slug or not tag_name: return _err("release_create", "owner, repo, tag_name required")
        args = ["release", "create", tag_name, "--repo", slug]
        if release_name: args += ["--title", release_name]
        if body: args += ["--notes", body]
        if prerelease: args.append("--prerelease")
        ok, out, err = run_gh(args)
        if not ok: return _err("release_create", err or "release create failed")
        return _ok("release_create", {"url": out.strip(), "tag": tag_name}, message="Release created")

    if operation == "release_delete":
        if not slug or not tag_name: return _err("release_delete", "owner, repo, tag_name required")
        ok, out, err = run_gh(["release", "delete", tag_name, "--repo", slug, "--yes"])
        if not ok: return _err("release_delete", err or "release delete failed")
        return _ok("release_delete", {"tag": tag_name}, message=f"Release {tag_name} deleted")

    if operation == "release_update":
        if not slug or not tag_name: return _err("release_update", "owner, repo, tag_name required")
        args = ["release", "edit", tag_name, "--repo", slug]
        if release_name: args += ["--title", release_name]
        if body: args += ["--notes", body]
        if prerelease: args.append("--prerelease")
        ok, out, err = run_gh(args)
        if not ok: return _err("release_update", err or "release update failed")
        return _ok("release_update", {"tag": tag_name, "output": out.strip()}, message="Release updated")

    # ── Workflows ─────────────────────────────────────────────────────────────
    if operation == "workflow_list":
        if not slug: return _err("workflow_list", "owner and repo required")
        ok, out, err = run_gh(["workflow", "list", "--repo", slug,
                                "--json", "id,name,state"])
        if not ok: return _err("workflow_list", err or "workflow list failed")
        data = _j(out)
        return _ok("workflow_list", {"workflows": data, "count": len(data)})

    if operation == "workflow_run":
        if not slug or not workflow_id: return _err("workflow_run", "owner, repo, workflow_id required")
        args = ["workflow", "run", workflow_id, "--repo", slug]
        if ref: args += ["--ref", ref]
        ok, out, err = run_gh(args)
        if not ok: return _err("workflow_run", err or "workflow run failed")
        return _ok("workflow_run", {"output": (out + err).strip()}, message="Workflow triggered")

    if operation == "workflow_runs":
        if not slug: return _err("workflow_runs", "owner and repo required")
        args = ["run", "list", "--repo", slug, "--limit", str(limit),
                "--json", "databaseId,name,status,conclusion,headBranch,createdAt,url"]
        if workflow_id: args += ["--workflow", workflow_id]
        ok, out, err = run_gh(args)
        if not ok: return _err("workflow_runs", err or "run list failed")
        data = _j(out)
        return _ok("workflow_runs", {"runs": data, "count": len(data)})

    if operation == "workflow_cancel":
        if not slug or not run_id: return _err("workflow_cancel", "owner, repo, run_id required")
        ok, out, err = run_gh(["run", "cancel", run_id, "--repo", slug])
        if not ok: return _err("workflow_cancel", err or "workflow cancel failed")
        return _ok("workflow_cancel", {"run_id": run_id}, message="Workflow run cancelled")

    if operation == "workflow_disable":
        if not slug or not workflow_id: return _err("workflow_disable", "owner, repo, workflow_id required")
        ok, out, err = run_gh(["workflow", "disable", workflow_id, "--repo", slug])
        if not ok: return _err("workflow_disable", err or "workflow disable failed")
        return _ok("workflow_disable", {"workflow_id": workflow_id}, message="Workflow disabled")

    if operation == "workflow_enable":
        if not slug or not workflow_id: return _err("workflow_enable", "owner, repo, workflow_id required")
        ok, out, err = run_gh(["workflow", "enable", workflow_id, "--repo", slug])
        if not ok: return _err("workflow_enable", err or "workflow enable failed")
        return _ok("workflow_enable", {"workflow_id": workflow_id}, message="Workflow enabled")

    # ── Labels ────────────────────────────────────────────────────────────────
    if operation == "label_list":
        if not slug: return _err("label_list", "owner and repo required")
        ok, out, err = run_gh(["label", "list", "--repo", slug,
                                "--json", "name,color,description"])
        if not ok: return _err("label_list", err or "label list failed")
        data = _j(out)
        return _ok("label_list", {"labels": data, "count": len(data)})

    if operation == "label_create":
        if not slug or not label_name: return _err("label_create", "owner, repo, label_name required")
        args = ["label", "create", label_name, "--repo", slug]
        if label_color: args += ["--color", label_color.lstrip("#")]
        if label_description: args += ["--description", label_description]
        ok, out, err = run_gh(args)
        if not ok: return _err("label_create", err or "label create failed")
        return _ok("label_create", {"name": label_name}, message=f"Label '{label_name}' created")

    if operation == "label_delete":
        if not slug or not label_name: return _err("label_delete", "owner, repo, label_name required")
        ok, out, err = run_gh(["label", "delete", label_name, "--repo", slug, "--yes"])
        if not ok: return _err("label_delete", err or "label delete failed")
        return _ok("label_delete", {"name": label_name}, message=f"Label '{label_name}' deleted")

    # ── Secrets ───────────────────────────────────────────────────────────────
    if operation == "secrets_list":
        if not slug: return _err("secrets_list", "owner and repo required")
        ok, out, err = run_gh(["secret", "list", "--repo", slug,
                                "--json", "name,updatedAt"])
        if not ok: return _err("secrets_list", err or "secrets list failed")
        data = _j(out)
        return _ok("secrets_list", {"secrets": data, "count": len(data)})

    if operation == "secrets_set":
        if not slug or not secret_name or not secret_value:
            return _err("secrets_set", "owner, repo, secret_name, secret_value required")
        ok, out, err = run_gh(["secret", "set", secret_name,
                                "--repo", slug, "--body", secret_value])
        if not ok: return _err("secrets_set", err or "secret set failed")
        return _ok("secrets_set", {"name": secret_name}, message=f"Secret '{secret_name}' set")

    if operation == "secrets_delete":
        if not slug or not secret_name:
            return _err("secrets_delete", "owner, repo, secret_name required")
        ok, out, err = run_gh(["secret", "delete", secret_name, "--repo", slug])
        if not ok: return _err("secrets_delete", err or "secret delete failed")
        return _ok("secrets_delete", {"name": secret_name}, message=f"Secret '{secret_name}' deleted")

    # ── Collaborators ─────────────────────────────────────────────────────────
    if operation == "collaborator_add":
        if not slug or not username: return _err("collaborator_add", "owner, repo, username required")
        ok, out, err = run_gh(["api", f"repos/{slug}/collaborators/{username}",
                                "--method", "PUT",
                                "--field", f"permission={permission}"])
        if not ok: return _err("collaborator_add", err or "collaborator add failed",
                               recovery_options=["Check admin access", "gh auth login"])
        return _ok("collaborator_add", {"username": username, "permission": permission},
                   message=f"{username} added as collaborator ({permission})")

    if operation == "collaborator_remove":
        if not slug or not username: return _err("collaborator_remove", "owner, repo, username required")
        ok, out, err = run_gh(["api", f"repos/{slug}/collaborators/{username}",
                                "--method", "DELETE"])
        if not ok: return _err("collaborator_remove", err or "collaborator remove failed")
        return _ok("collaborator_remove", {"username": username},
                   message=f"{username} removed as collaborator")

    # ── Search ────────────────────────────────────────────────────────────────
    if operation == "search_repos":
        if not query: return _err("search_repos", "query required")
        ok, out, err = run_gh(["search", "repos", query, "--limit", str(limit),
                                "--json", "name,fullName,description,url,stargazerCount,language"])
        if not ok: return _err("search_repos", err or "search failed")
        data = _j(out)
        return _ok("search_repos", {"repos": data, "count": len(data)})

    if operation == "search_issues":
        if not query: return _err("search_issues", "query required")
        ok, out, err = run_gh(["search", "issues", query, "--limit", str(limit),
                                "--json", "number,title,state,url,repository,author,createdAt"])
        if not ok: return _err("search_issues", err or "search failed")
        data = _j(out)
        return _ok("search_issues", {"issues": data, "count": len(data)})

    if operation == "search_code":
        if not query: return _err("search_code", "query required")
        ok, out, err = run_gh(["search", "code", query, "--limit", str(limit),
                                "--json", "path,repository,url,textMatches"])
        if not ok: return _err("search_code", err or "search failed")
        data = _j(out)
        return _ok("search_code", {"results": data, "count": len(data)})

    return _err(operation, "Not implemented")
