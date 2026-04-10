# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- **`github_ops(pr_list)`:** JSON now includes **`comments`** and **`updatedAt`** for easier maintainer triage (spot stale PR threads).
- **Web:** `tailwind.config.js` defines **`fontFamily.ui`** / **`mono`** / **`heading`** so `@apply font-ui` in `index.css` builds (Vite production build fixed).

### Added
- **README:** Maintainer section — weekly PR list + `pr_comment` acknowledgment template, GitHub Watch reminder, **`/inbox`** web route + supervisor heartbeat note, link to **mcp-central-docs** `patterns/GITHUB_MAINTAINER_HEARTBEAT.md`.
- **Web (`web/`):** Route **`/inbox`** — **Pull requests & Issues** (tabs), optional **fleet** multi-repo list (persisted in `localStorage`), stale activity hints; sidebar nav **PRs & Issues**. Standalone **`/prs`** and **`/issues`** show comment/updated dates where applicable.
- **`llms.txt`:** Maintainer fleet triage blurb + fleet doc pointer.

## [0.4.0] - 2026-04-06

### Added
- **Automatic gh Discovery**: Hardened Windows path discovery for `gh.exe` in `C:\Program Files\GitHub CLI` and `scoop` shims. 
- **Environment Resilience**: Server now functions correctly even if the system `PATH` is missing key CLI tools (gh, just, winget).

### Changed
- **FastMCP 3.2.0**: Upgraded core framework to latest SOTA for improved tool registry performance and tool-calling reliability.
- **Dependency Refresh**: Updated project metadata and core dependencies.

## [0.3.0] - 2025-03-19
- Initial FastMCP 3.1 implementation.
- Support for 100+ Git and GitHub operations.
