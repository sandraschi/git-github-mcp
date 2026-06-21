"""Build [Gitingest](https://gitingest.com) URLs from GitHub coordinates.

Rule of thumb (from upstream): replace ``hub`` with ``ingest`` in ``github.com``
→ ``gitingest.com``.
"""

from __future__ import annotations

from urllib.parse import unquote, urlparse


def build_gitingest_url(
    owner: str,
    repo: str,
    ref: str | None = None,
    subpath: str | None = None,
) -> str:
    """Return https://gitingest.com/owner/repo[/tree/ref/subpath]."""
    o, r = owner.strip(), repo.strip()
    if r.endswith(".git"):
        r = r[:-4]
    base = f"https://gitingest.com/{o}/{r}"
    sp = (subpath or "").strip().strip("/")
    rf = (ref or "").strip()
    if rf and sp:
        return f"{base}/tree/{rf}/{sp}"
    if rf:
        return f"{base}/tree/{rf}"
    if sp:
        return f"{base}/tree/main/{sp}"
    return base


def github_url_to_gitingest(url: str) -> tuple[str | None, str | None]:
    """Map a github.com URL to gitingest.com, or (None, error)."""
    raw = (url or "").strip()
    if not raw:
        return None, "URL required"
    try:
        p = urlparse(raw)
    except ValueError:
        return None, "invalid URL"
    host = (p.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host != "github.com":
        return None, "expected https://github.com/... URL"
    parts = [x for x in p.path.split("/") if x]
    if len(parts) < 2:
        return None, "path must include owner and repo"
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    rest = parts[2:]
    base = f"https://gitingest.com/{owner}/{repo}"
    if not rest:
        return base, None
    kind = rest[0].lower()
    if kind == "tree" and len(rest) >= 2:
        branch = unquote(rest[1])
        tail = "/".join(unquote(x) for x in rest[2:])
        if tail:
            return f"{base}/tree/{branch}/{tail}", None
        return f"{base}/tree/{branch}", None
    if kind == "blob" and len(rest) >= 2:
        branch = unquote(rest[1])
        file_parts = [unquote(x) for x in rest[2:]]
        if len(file_parts) >= 2:
            parent = "/".join(file_parts[:-1])
            return f"{base}/tree/{branch}/{parent}", None
        if len(file_parts) == 1:
            return f"{base}/tree/{branch}", None
        return base, None
    if kind in ("pull", "issues", "actions", "releases", "compare", "commits"):
        return (
            None,
            f"URL type /{kind}/ is not a repo tree; open the repo or tree URL instead.",
        )
    return base, None


GITINGEST_HELP_MARKDOWN = """## Gitingest + fleet LLM docs

**What it is:** [Gitingest](https://gitingest.com) turns a **public GitHub repo**
(or a **subpath** on a branch) into a **single prompt-friendly text digest**:
file tree, size stats, token estimate, and concatenated sources.

**URL trick:** replace **`hub`** with **`ingest`** in **`github.com`** → **`gitingest.com`**
Example: `https://github.com/owner/repo` → `https://gitingest.com/owner/repo`

**Good for:**
- Quick **full-repo context** for an LLM when you do not have a local clone
- **Subfolder** ingestion (`/tree/branch/path`) for monorepos
- Comparing **token footprint** before pasting into a model

**vs `llms.txt` / `llms-full.txt` (fleet standard):**
| | Gitingest | `llms.txt` + `llms-full.txt` |
|--|-----------|------------------------------|
| **Source** | Live GitHub tree | **Committed** at repo root |
| **Stability** | Changes with every push | Versioned with the repo; explicit updates |
| **Shape** | Auto digest of files | **Curated** index + deep corpus for tools/ports/env |
| **Best use** | Ad-hoc ingest, exploration | **Discovery**, MCP tools, long-lived context |

Use **both**: keep **`llms.txt`** as the stable front door; use **Gitingest** when you need
the **raw codebase text** in one shot or a **path-scoped** slice.

**Private repos:** need a PAT in Gitingest / `gitingest` CLI ([upstream](https://github.com/coderamp-labs/gitingest)).

**CLI (optional):** `pipx install gitingest` then `gitingest <repo_url> --output -`
"""
