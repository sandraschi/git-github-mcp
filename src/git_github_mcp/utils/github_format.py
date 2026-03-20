"""Pretty Markdown / HTML formatters for GitHub API JSON (gh --json)."""

from __future__ import annotations

import html
from typing import Any


def _topics_list(data: dict[str, Any]) -> list[str]:
    rt = data.get("repositoryTopics") or {}
    nodes = rt.get("nodes") if isinstance(rt, dict) else None
    if not nodes:
        return []
    out: list[str] = []
    for n in nodes:
        if isinstance(n, dict) and n.get("name"):
            out.append(str(n["name"]))
        elif isinstance(n, str):
            out.append(n)
    return out


def _languages_line(data: dict[str, Any]) -> str:
    lang = data.get("languages") or {}
    edges = lang.get("edges") if isinstance(lang, dict) else None
    if not edges:
        return ""
    parts: list[str] = []
    for e in edges[:8]:
        node = e.get("node") if isinstance(e, dict) else None
        if isinstance(node, dict) and node.get("name"):
            parts.append(str(node["name"]))
    return ", ".join(parts)


def _default_branch(data: dict[str, Any]) -> str:
    ref = data.get("defaultBranchRef") or {}
    if isinstance(ref, dict) and ref.get("name"):
        return str(ref["name"])
    return ""


def format_repo_card(data: dict[str, Any], fmt: str) -> str:
    """Render repo_view JSON as Markdown, HTML, or pass-through JSON string."""
    fmt_l = (fmt or "markdown").strip().lower()
    if fmt_l == "json":
        import json

        return json.dumps(data, indent=2)

    name = str(data.get("name") or "")
    desc = (data.get("description") or "").strip()
    priv = data.get("isPrivate")
    stars = data.get("stargazerCount")
    forks = data.get("forkCount")
    url = data.get("url") or ""
    ssh = data.get("sshUrl") or ""
    issues = data.get("issues") or {}
    issue_count = issues.get("totalCount") if isinstance(issues, dict) else None
    topics = _topics_list(data)
    langs = _languages_line(data)
    branch = _default_branch(data)

    if fmt_l == "html":
        lines = [
            '<article class="gh-repo-card" style="font-family:system-ui,sans-serif;max-width:48rem;">',
            f'<h1 style="margin:0 0 0.5rem;">{html.escape(name)}</h1>',
            f'<p style="color:#444;margin:0 0 1rem;">{html.escape(desc) if desc else "<em>No description</em>"}</p>',
            '<ul style="list-style:none;padding:0;margin:0 0 1rem;color:#333;">',
        ]
        if stars is not None:
            lines.append(f"<li><strong>Stars</strong>: {html.escape(str(stars))}</li>")
        if forks is not None:
            lines.append(f"<li><strong>Forks</strong>: {html.escape(str(forks))}</li>")
        if issue_count is not None:
            lines.append(
                f"<li><strong>Open issues (total)</strong>: {html.escape(str(issue_count))}</li>"
            )
        if branch:
            lines.append(f"<li><strong>Default branch</strong>: {html.escape(branch)}</li>")
        vis = "private" if priv else "public"
        lines.append(f"<li><strong>Visibility</strong>: {html.escape(vis)}</li>")
        lines.append("</ul>")
        if topics:
            safe = ", ".join(html.escape(t) for t in topics)
            lines.append(f"<p><strong>Topics</strong>: {safe}</p>")
        if langs:
            lines.append(f"<p><strong>Languages</strong>: {html.escape(langs)}</p>")
        if url:
            lines.append(f'<p><a href="{html.escape(url, quote=True)}">Open on GitHub</a></p>')
        if ssh:
            lines.append(f'<p style="font-size:0.9rem;"><code>{html.escape(ssh)}</code></p>')
        lines.append("</article>")
        return "\n".join(lines)

    # markdown (default)
    md: list[str] = [f"# {name}", ""]
    if desc:
        md.append(f"> {desc}")
        md.append("")
    stats = []
    if stars is not None:
        stats.append(f"**Stars:** {stars}")
    if forks is not None:
        stats.append(f"**Forks:** {forks}")
    if issue_count is not None:
        stats.append(f"**Issues (total):** {issue_count}")
    if branch:
        stats.append(f"**Default branch:** `{branch}`")
    stats.append(f"**Visibility:** {'private' if priv else 'public'}")
    md.append(" · ".join(stats))
    md.append("")
    if topics:
        md.append("**Topics:** " + ", ".join(f"`{t}`" for t in topics))
        md.append("")
    if langs:
        md.append(f"**Languages:** {langs}")
        md.append("")
    if url:
        md.append(f"- **URL:** {url}")
    if ssh:
        md.append(f"- **SSH:** `{ssh}`")
    md.append("")
    return "\n".join(md)


def _repo_slug_from_code_item(item: dict[str, Any]) -> str:
    r = item.get("repository")
    if isinstance(r, dict):
        return str(r.get("nameWithOwner") or r.get("fullName") or r.get("name") or "?")
    return "?"


def format_code_search_markdown(results: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """Build a Markdown table and a deduplicated list of repo slugs (owner/repo)."""
    seen: list[str] = []
    uniq: set[str] = set()
    for item in results:
        slug = _repo_slug_from_code_item(item)
        if slug not in uniq:
            uniq.add(slug)
            seen.append(slug)

    if not results:
        return "_No code search results._", seen

    lines = [
        "| Repository | Path | Preview |",
        "|------------|------|---------|",
    ]
    for item in results:
        slug = _repo_slug_from_code_item(item)
        path = str(item.get("path") or "")
        url = str(item.get("url") or "")
        preview = ""
        tm = item.get("textMatches") or []
        if isinstance(tm, list) and tm:
            frag = tm[0].get("fragment") if isinstance(tm[0], dict) else None
            if frag:
                preview = str(frag).replace("\n", " ").strip()[:120]
        link = f"[{path}]({url})" if url else f"`{path}`"
        prev_esc = preview.replace("|", "\\|")
        lines.append(f"| `{slug}` | {link} | {prev_esc} |")

    summary = f"**{len(results)} hit(s)** across **{len(seen)}** repo(s).\n\n" + "\n".join(lines)
    return summary, seen


def build_code_find_query(
    *,
    query: str | None,
    owner: str | None,
    extension: str | None,
    path_pattern: str | None,
    search_scope: str | None,
) -> str | None:
    """Compose a GitHub code search query. Returns None if nothing to search."""
    q = (query or "").strip()
    has_builder = bool(search_scope or owner or extension or path_pattern)
    if q and not has_builder:
        return q

    parts: list[str] = []
    if search_scope:
        parts.append(search_scope.strip())
    elif owner:
        o = owner.strip()
        if ":" not in o:
            parts.append(f"user:{o}")
        else:
            parts.append(o)

    if extension:
        ext = extension.lstrip(".").strip()
        if ext:
            parts.append(f"extension:{ext}")
    if path_pattern:
        parts.append(f"path:{path_pattern.strip()}")
    if q:
        parts.append(q)

    if not parts:
        return None
    return " ".join(parts)


def build_topic_repo_query(topic: str, owner: str | None, extra: str | None) -> str:
    """GitHub repository search by topic (repo tag), optional user/org scope."""
    parts = [f"topic:{topic.strip()}"]
    if owner:
        o = owner.strip()
        parts.append(f"user:{o}" if ":" not in o else o)
    if extra and extra.strip():
        parts.append(extra.strip())
    return " ".join(parts)
