# Changelog

All notable changes to this project will be documented in this file.

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
