# Changelog

All notable changes to this project will be documented in this file.

## [v0.1.0] - 2026-05-10

### Added
- Initial version of Duplicati MCP server
- Streamable HTTP transport support (MCP 2025 standard)
- stdio transport for local development and testing
- Eight tools: `list_backups`, `get_backup`, `run_backup`, `abort_backup`,
  `get_progress`, `get_server_status`, `export_backup_config`, `import_backup_config`
- Read-only mode via `DUPLICATI_READONLY` environment variable
- Docker Hub support with multi-architecture build
- Complete documentation in English and French
- Pylint configuration for development
- Test scripts (shell and Python)
- MCP registry publication files

### Features
- List and inspect Duplicati backup jobs
- Trigger and abort backup runs
- Monitor live backup progress
- Export and import backup configurations
- Dual transport: stdio (local) and Streamable HTTP (Docker/remote)
- Safe read-only mode for exploration and analysis

### Docker
- Published on Docker Hub: `kcofoni/duplicati-mcp`
- Docker Compose configuration
- Connects to Duplicati via REST API (no volume mount required)
