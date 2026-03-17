"""Help tool for git-github-mcp. Returns documentation for git_ops and github_ops."""

from ..utils.response import success_response


def get_help(level: str = "basic", topic: str | None = None) -> dict:
    """Return help content for git-github-mcp tools.

    SUPPORTED OPERATIONS:
    - level: basic | intermediate | advanced
    - topic: git_ops | github_ops | None (all)
    """
    if topic and topic not in ("git_ops", "github_ops"):
        return {
            "success": False,
            "operation": "help",
            "error": f"Unknown topic: {topic}",
            "message": "Use topic: git_ops, github_ops, or omit for overview",
        }

    if level == "basic":
        content = _basic_help(topic)
    elif level == "intermediate":
        content = _intermediate_help(topic)
    elif level == "advanced":
        content = _advanced_help(topic)
    else:
        return {
            "success": False,
            "operation": "help",
            "error": f"Unknown level: {level}",
            "message": "Use level: basic, intermediate, or advanced",
        }

    return success_response(
        {"help_content": content, "level": level, "topic": topic},
        "help",
        message=f"Help at {level} level",
    )


def _basic_help(topic: str | None) -> str:
    lines = ["# git-github-mcp — Quick Reference", ""]
    if topic in (None, "git_ops"):
        lines.extend([
            "## git_ops (43 actions)",
            "CORE:      init, clone, add, commit, push, pull, fetch, status",
            "INSPECT:   log, diff, show, blame",
            "BRANCH:    branch_list/create/switch/delete/merge, rebase",
            "REMOTE:    remote_list/add/remove",
            "STASH:     stash, stash_pop, stash_list, stash_drop",
            "TAG:       tag_list/create/delete",
            "UNDO:      reset, revert, cherry_pick",
            "CLEANUP:   clean",
            "SUBMODULE: submodule_add/update/sync/status",
            "BISECT:    bisect_start/bad/good/reset",
            "WORKTREE:  worktree_add/list/remove",
            "",
        ])
    if topic in (None, "github_ops"):
        lines.extend([
            "## github_ops (43 actions)",
            "REPOS:         repo_list/view/create/fork/clone/delete/rename/archive",
            "ISSUES:        issue_list/view/create/close/comment",
            "PRs:           pr_list/view/create/merge/checkout/close/comment",
            "RELEASES:      release_list/view/create/delete/update",
            "ACTIONS:       workflow_list/run/runs/cancel/disable/enable",
            "LABELS:        label_list/create/delete",
            "SECRETS:       secrets_list/set/delete",
            "COLLABORATORS: collaborator_add/remove",
            "SEARCH:        search_repos/issues/code",
            "MISC:          auth_status, gist_list",
            "",
            "Requires: gh auth login",
            "",
        ])
    lines.append("Use get_help(level='advanced') for examples.")
    return "\n".join(lines)


def _intermediate_help(topic: str | None) -> str:
    lines = ["# git-github-mcp — Parameter Reference", ""]
    if topic in (None, "git_ops"):
        lines.extend([
            "## git_ops — Key parameters",
            "",
            "| Operation        | Required              | Notable optional              |",
            "|------------------|-----------------------|-------------------------------|",
            "| init             | —                     | repo_path, initial_branch     |",
            "| clone            | repo_url              | target_dir, branch            |",
            "| add              | files or all_files    | repo_path                     |",
            "| commit           | message               | all_files, amend              |",
            "| push             | —                     | remote, branch, force         |",
            "| pull/fetch       | —                     | remote, branch                |",
            "| log              | —                     | max_count, oneline, branch    |",
            "| diff             | —                     | commit, commit2, files        |",
            "| blame            | file_path             | commit                        |",
            "| branch_create    | branch                | source_branch                 |",
            "| reset            | —                     | commit, mode (soft/mixed/hard)|",
            "| clean            | —                     | dry_run, include_dirs         |",
            "| submodule_add    | submodule_url         | submodule_path                |",
            "| submodule_update | —                     | recursive                     |",
            "| bisect_bad/good  | —                     | commit                        |",
            "| worktree_add     | worktree_path         | branch                        |",
            "",
        ])
    if topic in (None, "github_ops"):
        lines.extend([
            "## github_ops — Key parameters",
            "",
            "| Operation         | Required                      | Notable optional       |",
            "|-------------------|-------------------------------|------------------------|",
            "| repo_create       | repo                          | description, private   |",
            "| repo_rename       | owner, repo, new_name         | —                      |",
            "| repo_delete       | owner, repo                   | —                      |",
            "| repo_archive      | owner, repo                   | —                      |",
            "| pr_close          | owner, repo, pr_number        | body (comment)         |",
            "| pr_comment        | owner, repo, pr_number, body  | —                      |",
            "| release_delete    | owner, repo, tag_name         | —                      |",
            "| release_update    | owner, repo, tag_name         | release_name, body     |",
            "| workflow_cancel   | owner, repo, run_id           | —                      |",
            "| workflow_disable  | owner, repo, workflow_id      | —                      |",
            "| label_create      | owner, repo, label_name       | label_color, label_description |",
            "| secrets_set       | owner, repo, secret_name, secret_value | —           |",
            "| collaborator_add  | owner, repo, username         | permission (push/admin/maintain) |",
            "",
        ])
    return "\n".join(lines)


def _advanced_help(topic: str | None) -> str:
    lines = ["# git-github-mcp — Advanced Examples", ""]
    if topic in (None, "git_ops"):
        lines.extend([
            "## git_ops — Examples",
            "",
            "```",
            "git_ops(operation='clone', repo_url='https://github.com/owner/repo.git')",
            "git_ops(operation='status', repo_path='D:/Dev/repos/my-repo')",
            "git_ops(operation='add', repo_path='.', files=['src/main.py'])",
            "git_ops(operation='commit', repo_path='.', message='Fix bug')",
            "git_ops(operation='push', repo_path='.', remote='origin', branch='main')",
            "git_ops(operation='blame', repo_path='.', file_path='src/server.py')",
            "git_ops(operation='clean', repo_path='.', dry_run=True)",
            "git_ops(operation='clean', repo_path='.', include_dirs=True)",
            "git_ops(operation='submodule_update', repo_path='.', recursive=True)",
            "git_ops(operation='bisect_start', repo_path='.')",
            "git_ops(operation='bisect_bad', repo_path='.')",
            "git_ops(operation='bisect_good', repo_path='.', commit='abc123')",
            "git_ops(operation='worktree_add', repo_path='.', worktree_path='../feature-x', branch='feature-x')",
            "```",
            "",
            "Recovery: push fails → gh auth login; use force=True for force-with-lease.",
            "",
        ])
    if topic in (None, "github_ops"):
        lines.extend([
            "## github_ops — Examples",
            "",
            "```",
            "github_ops(operation='repo_rename', owner='sandraschi', repo='old-name', new_name='new-name')",
            "github_ops(operation='repo_delete', owner='sandraschi', repo='test-repo')",
            "github_ops(operation='repo_archive', owner='sandraschi', repo='old-mcp')",
            "github_ops(operation='pr_close', owner='x', repo='y', pr_number=5, body='Not needed')",
            "github_ops(operation='pr_comment', owner='x', repo='y', pr_number=5, body='LGTM')",
            "github_ops(operation='release_delete', owner='sandraschi', repo='my-mcp', tag_name='v0.1.0')",
            "github_ops(operation='release_update', owner='sandraschi', repo='my-mcp', tag_name='v1.0.0', body='Fixed changelog')",
            "github_ops(operation='workflow_cancel', owner='sandraschi', repo='my-mcp', run_id='12345678')",
            "github_ops(operation='workflow_disable', owner='sandraschi', repo='my-mcp', workflow_id='ci.yml')",
            "github_ops(operation='label_create', owner='sandraschi', repo='my-mcp', label_name='glama-ready', label_color='0075ca')",
            "github_ops(operation='secrets_set', owner='sandraschi', repo='my-mcp', secret_name='PYPI_TOKEN', secret_value='...')",
            "github_ops(operation='collaborator_add', owner='sandraschi', repo='my-mcp', username='someuser', permission='push')",
            "```",
            "",
            "Recovery: Run gh auth login if operations fail. Set GITHUB_TOKEN if needed.",
            "",
        ])
    return "\n".join(lines)
