# Changelog

All notable changes to this project will be documented in this file.

## [v1.0.1] - 2026-05-13

### Fixed
- server.json: transport type corrected (`http` → `streamable-http`) for MCP registry validation
- server.json: description shortened to ≤100 characters
- server.py: Literal type hint fixed in `main()`, switched to absolute imports for `mcp dev` compatibility

### Added
- `/release` skill: step-by-step guided release procedure (`.claude/commands/release.md`)
- Publication guides: full PyPI section (TestPyPI + prod, token scoping notes)
- Publication guides: complete release checklist orchestrating all three registries
- pyproject.toml: TestPyPI index configuration for `uv publish --index testpypi`

### Changed
- README/README_fr: added stdio client config, fixed Claude Desktop config to use `mcp-proxy`
- README/README_fr: `update_backup_config` tool documented (9 tools total)
- DOCKER_HUB_DESCRIPTION: tools list and client configurations updated

## [v1.0.0] - 2026-05-12

### Added
- Initial production release of Duplicati MCP server
- Streamable HTTP transport support (MCP 2025 standard)
- stdio transport for local development and testing via Claude Code
- Nine tools: `list_backups`, `get_backup`, `run_backup`, `abort_backup`,
  `get_progress`, `get_server_status`, `export_backup_config`, `update_backup_config`,
  `import_backup_config`
- Read-only mode via `DUPLICATI_READONLY` environment variable
- python-dotenv support for local credentials via `.env` file
- Docker Hub support with multi-architecture build
- Complete documentation in English and French
- Pylint configuration for development
- Test scripts (shell and Python)
- MCP registry publication files

### Features
- List and inspect Duplicati backup jobs
- Trigger and abort backup runs
- Monitor live backup progress
- Export, modify and update backup configurations in place
- Dual transport: stdio (local) and Streamable HTTP (Docker/remote)
- Safe read-only mode for exploration and analysis
- Compatible with Claude Desktop via mcp-proxy

### Technical
- JWT Bearer token authentication (compatible with recent Duplicati versions)
- FastMCP host/port correctly configured for Docker deployment
- Validated with Portainer and Claude Desktop

### Docker
- Published on Docker Hub: `kcofoni/duplicati-mcp`
- Docker Compose configuration
- Connects to Duplicati via REST API (no volume mount required)
