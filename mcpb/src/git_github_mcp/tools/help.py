"""Help tool for git-github-mcp. Returns documentation for git_ops and github_ops."""

from ..utils.response import success_response


def get_help(level: str = "basic", topic: str | None = None) -> dict:
    """Return help content for git-github-mcp tools.

    SUPPORTED OPERATIONS:
    - level: basic | intermediate | advanced
    - topic: git_ops | github_ops | None (all)

    LEVELS:
    - basic: Quick reference and common workflows
    - intermediate: Full operation list with parameters
    - advanced: Error handling, recovery, and examples

    Args:
        level: Help detail level (basic, intermediate, advanced)
        topic: Focus on git_ops, github_ops, or None for overview

    Returns:
        Dialogic response with help_content in result.
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
    """Basic help - quick reference."""
    lines = ["# git-github-mcp - Quick Reference", ""]
    if topic in (None, "git_ops"):
        lines.extend([
            "## git_ops",
            "Operations: clone, status, add, commit, push, pull, branch, tag, stash",
            "- clone: repo_url required",
            "- status: repo_path optional (default: cwd)",
            "- add: files or all_files=True",
            "- commit: message required",
            "- push/pull: remote, branch optional",
            "",
        ])
    if topic in (None, "github_ops"):
        lines.extend([
            "## github_ops",
            "Operations: create_issue, list_issues, create_pr, list_prs, search",
            "- Requires gh auth login",
            "- create_issue, list_issues, create_pr, list_prs: owner and repo required",
            "- search: query required",
            "",
        ])
    lines.append("Use mcp_help(level='intermediate') for full parameter list.")
    return "\n".join(lines)


def _intermediate_help(topic: str | None) -> str:
    """Intermediate help - full operation list."""
    lines = ["# git-github-mcp - Operation Reference", ""]
    if topic in (None, "git_ops"):
        lines.extend([
            "## git_ops",
            "",
            "| Operation | Required | Optional |",
            "|-----------|----------|----------|",
            "| clone | repo_url | target_dir |",
            "| status | - | repo_path |",
            "| add | files or all_files | repo_path |",
            "| commit | message | repo_path, all_files |",
            "| push | - | repo_path, remote, branch, force |",
            "| pull | - | repo_path, remote, branch |",
            "| branch | - | repo_path |",
            "| tag | - | repo_path |",
            "| stash | - | repo_path |",
            "",
        ])
    if topic in (None, "github_ops"):
        lines.extend([
            "## github_ops",
            "",
            "| Operation | Required | Optional |",
            "|-----------|----------|----------|",
            "| create_issue | owner, repo, title | body |",
            "| list_issues | owner, repo | state, limit |",
            "| create_pr | owner, repo, title | body |",
            "| list_prs | owner, repo | state, limit |",
            "| search | query | limit |",
            "",
            "Parameters: state=open|closed|all, limit=10",
            "",
        ])
    return "\n".join(lines)


def _advanced_help(topic: str | None) -> str:
    """Advanced help - examples and recovery."""
    lines = ["# git-github-mcp - Advanced Usage", ""]
    if topic in (None, "git_ops"):
        lines.extend([
            "## git_ops - Examples",
            "",
            "```",
            "git_ops(operation='clone', repo_url='https://github.com/owner/repo.git')",
            "git_ops(operation='status', repo_path='D:/Dev/repos/my-repo')",
            "git_ops(operation='add', repo_path='.', files=['src/main.py'], all_files=False)",
            "git_ops(operation='commit', repo_path='.', message='Fix bug')",
            "git_ops(operation='push', repo_path='.', remote='origin', branch='main')",
            "```",
            "",
            "Recovery: If push fails, run gh auth login. Use force=True for force push.",
            "",
        ])
    if topic in (None, "github_ops"):
        lines.extend([
            "## github_ops - Examples",
            "",
            "```",
            "github_ops(operation='list_issues', owner='sandraschi', repo='git-github-mcp')",
            "github_ops(operation='create_issue', owner='x', repo='y', title='Bug', body='...')",
            "github_ops(operation='list_prs', owner='x', repo='y', state='open', limit=5)",
            "github_ops(operation='search', query='mcp server language:python', limit=10)",
            "```",
            "",
            "Recovery: Run gh auth login if operations fail. Set GITHUB_TOKEN if needed.",
            "",
        ])
    return "\n".join(lines)
