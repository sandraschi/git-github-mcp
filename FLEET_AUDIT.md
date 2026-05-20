# Fleet Audit — Damage Pattern Sweep

**Date**: 2026-04-30
**Scope**: 10 MCP repos (9 Python + 1 newly created)
**Patterns checked**: raw error dicts, subprocess hang risk, __init__ exports, ruff health

---

## Executive Summary

| Repo | Raw Dicts | Subprocess Risk | `main` Export | Ruff | Grade |
|------|-----------|-----------------|---------------|------|-------|
| aiwatcher-mcp | 0 ✅ | 0 ✅ | ✅ | 0 ✅ | **A+** |
| readly-mcp | 0 ✅ | 0 ✅ | ✅ | 4 | **A** |
| git-github-mcp | 0 ✅ | 0 ✅ | ✅ | 0 ✅ | **A** |
| speech-mcp | 43 | 3 | ❌ | 2 ✅ | **B** |
| dark-app-factory | 3 | 6 | ❌ | 81 | **C** |
| arxiv-mcp | 29 | 3 asyncio | ❌ | 14 | **C** |
| virtualization-mcp | 267+ | 85 | ✅ | 2 ✅ | **D** |
| plex-mcp | 194 | 3 asyncio | ✅ | 528 | **D** |
| advanced-memory-mcp | 58 | 14 | ❌ | 1827 | **F** |
| browser-mcp | n/a (new) | n/a | ✅ | 0 ✅ | **A** |

---

## Per-Repo Detail

### aiwatcher-mcp — A+
- Cleanest repo in the fleet. Zero raw dicts, no subprocess use, main exported, 0 ruff errors.
- The `response.py` utility pattern (which we fixed in git-github-mcp) is properly used everywhere.

### readly-mcp — A
- Clean structurally. 4 pre-existing ruff issues (E501 line length, S110 try-except-pass, RUF006 fire-and-forget task, S104 bind 0.0.0.0). All minor and pre-existing.

### git-github-mcp — A
- Fixed in this session. Was a D (split from 1 to 4 tools, added conversational errors, fixed subprocess hang with shell=True, 0 ruff errors).

### speech-mcp — B
- 43 raw error dicts across 5 files (heaviest in `speech.py` — 34 hits)
- 3 `subprocess.run` calls without `CREATE_NO_WINDOW` (potential console flash on Windows)
- `__init__.py` is empty (no `main` export)
- Ruff: 2 errors (minor)

### dark-app-factory — C
- 3 raw dicts (low), 6 `subprocess.run` calls, `__init__.py` empty, 81 ruff errors

### arxiv-mcp — C
- 29 raw dicts across 4 files, no response utility exists anywhere
- 3 `asyncio.create_subprocess_exec` calls for calibredb (no creationflags — console flash)
- `__init__.py` does NOT export `main`
- 14 ruff errors (2 S110 try-except-pass, 2 F401 unused imports, etc.)

### virtualization-mcp — D
- **267+ raw error dicts** (extreme, including stale .bak copies)
- **85 `subprocess.run` calls** across 12 files — mostly async-wrapped but pervasive
- 1 `CREATE_NO_WINDOW` in `windows_sandbox_helper.py` (single instance, justified for sandbox)
- Main exported ✅, ruff 2 errors ✅

### plex-mcp — D
- **194 raw dicts** across 13 files — no shared response utility despite `error_handling.py` existing
- 3 `asyncio.create_subprocess_exec` for ffmpeg/ffprobe (no creationflags)
- Main exported ✅
- **528 ruff errors** — TRY003 (187), TRY400 (121), TRY300 (87) — systemic exception-handling antipatterns

### advanced-memory-mcp — F
- **58 raw dicts** across 17 files
- **14 `subprocess.run` calls** across 4 files
- No `main` export
- **1827 ruff errors** — by far the worst in fleet. Severe technical debt.

---

## Damage Pattern Distribution

### Raw error dicts (worst offenders)
```
virtualization-mcp  ████████████████████████████████ 267
plex-mcp            ████████████████████████ 194
advanced-memory     ███████ 58
speech-mcp          ██████ 43
arxiv-mcp           ████ 29
dark-app-factory    ▌ 3
aiwatcher/readly    - 0
```

### Ruff debt (worst offenders)
```
advanced-memory     ████████████████████████████████ 1827
plex-mcp            ██████████ 528
dark-app-factory    ██ 81
arxiv-mcp           ▌ 14
readly-mcp          ▏ 4
speech/virtual      ▏ 2
aiwatcher/browser   - 0
```

### Missing `main` export
```
advanced-memory ❌
dark-app-factory ❌  
arxiv-mcp ❌
speech-mcp ❌
aiwatcher ✅
readly ✅
plex ✅
virtualization ✅
```

---

## Key Findings

1. **Only 2 repos are truly clean**: aiwatcher-mcp and browser-mcp. readly-mcp and git-github-mcp are close.

2. **The git-github-mcp damage pattern (raw dicts + subprocess hang + missing conversational errors) is NOT unique** — plex-mcp and virtualization-mcp have far worse versions of the same problem.

3. **advanced-memory-mcp needs a full rewrite or major refactoring** — 1827 ruff errors is a generation behind the fleet.

4. **virtualization-mcp's 85 subprocess calls are concerning** — each one is a potential hang point if the repo ever runs inside an Electron MCP host.

5. **No response utility exists** in arxiv-mcp, plex-mcp, speech-mcp, or virtualization-mcp — every error is a hand-rolled dict.
