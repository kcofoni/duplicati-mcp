# Changelog

All notable changes to this project will be documented in this file.

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
