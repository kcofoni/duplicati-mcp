# Duplicati MCP Server

A Model Context Protocol (MCP) server that gives LLMs full control over Duplicati backup jobs through a standardized interface.

## What is this?

This Docker image runs an MCP server that wraps the Duplicati REST API using the Streamable HTTP transport (MCP 2025 standard). It enables AI assistants like Claude to list, run, monitor, and configure Duplicati backup jobs.

## Features

- **Backup Management**: List jobs, trigger runs, abort active backups
- **Live Monitoring**: Real-time progress, phase, file counts and ETA
- **Config Export/Import**: Export job configurations as JSON for migration or backup
- **History & Diagnostics**: Query operation history, error logs and restore points via SQLite (opt-in)
- **Read-only Mode**: Lock the server to read-only for safe exploration
- **Streamable HTTP**: Modern MCP transport, compatible with all current MCP clients

## Quick Start

```bash
docker run -d \
  --name duplicati-mcp-server \
  -p 3000:3000 \
  -e DUPLICATI_URL=http://your-duplicati-host:8200 \
  -e DUPLICATI_PASSWORD=your-password \
  kcofoni/duplicati-mcp:latest
```

## Docker Compose

```yaml
version: '3.8'

services:
  duplicati-mcp:
    image: kcofoni/duplicati-mcp:latest
    container_name: duplicati-mcp-server
    ports:
      - "3000:3000"
    environment:
      - DUPLICATI_URL=http://duplicati:8200
      - DUPLICATI_PASSWORD=
      - DUPLICATI_READONLY=false
      # Optional: enable SQLite history tools (share Duplicati config as read-only volume)
      # - DUPLICATI_DB_PATH=/duplicati-config/Duplicati-server.sqlite
    # volumes:
    #   - duplicati_config:/duplicati-config:ro
    restart: unless-stopped

# volumes:
#   duplicati_config:   # same named volume used by the Duplicati container
```

## Client Configuration

### Claude Code

Add to your project `.mcp.json`:

```json
{
  "mcpServers": {
    "duplicati": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

Replace `localhost` with your Docker host IP if running remotely.

### Claude Desktop

Claude Desktop requires `mcp-proxy` to connect to HTTP servers. Add to your configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "duplicati": {
      "command": "uvx",
      "args": ["mcp-proxy", "--transport", "streamablehttp", "http://your-host:3000/mcp"]
    }
  }
}
```

## Available Tools

### REST API tools
1. **list_backups**: List all configured backup jobs with status and last run info
2. **get_backup**: Get detailed information about a specific job
3. **run_backup**: Trigger a backup job immediately
4. **abort_backup**: Abort the currently running backup for a job
5. **get_progress**: Get live progress of the active backup task
6. **get_server_status**: Get Duplicati server state and version
7. **export_backup_config**: Export a job configuration as JSON
8. **update_backup_config**: Update an existing job configuration in place
9. **import_backup_config**: Import a job configuration from JSON

### SQLite tools (require `DUPLICATI_DB_PATH`)
10. **db_get_backup_metadata**: Rich metadata — last run date, duration, file counts, quota, last error
11. **db_get_backup_schedule**: Schedule configuration for a job
12. **db_list_errors**: Recent error log entries, optionally filtered by job
13. **db_list_notifications**: System notifications (update alerts, etc.)
14. **db_get_backup_options**: Configuration options for a job (passphrases excluded)
15. **db_list_operations**: Operation history (Backup, Restore, List, etc.) with timestamps
16. **db_get_operation_log**: Full result and statistics for a specific operation
17. **db_list_filesets**: Available restore points (backup versions)

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DUPLICATI_URL` | `http://duplicati:8200` | URL of the Duplicati instance |
| `DUPLICATI_PASSWORD` | _(empty)_ | Duplicati web interface password |
| `DUPLICATI_READONLY` | `false` | Set to `true` to disable write operations |
| `DUPLICATI_DB_PATH` | _(empty)_ | Path to `Duplicati-server.sqlite` — enables SQLite history tools |

## Read-only Mode

Set `DUPLICATI_READONLY=true` to disable all write operations (`run_backup`, `abort_backup`, `update_backup_config`, `import_backup_config`). Read tools remain fully available — useful for safely exploring and analyzing your backup configuration.

## SQLite Access

Setting `DUPLICATI_DB_PATH` enables the `db_*` tools, which provide backup history, error logs, and restore points from Duplicati's local SQLite databases. Access is strictly read-only: databases are opened in read-only mode and copied to memory via the SQLite Online Backup API — the live Duplicati databases are never locked or modified.

To enable, share the Duplicati config directory as a read-only volume and set the path:

```bash
docker run -d \
  --name duplicati-mcp-server \
  -p 3000:3000 \
  -e DUPLICATI_URL=http://your-duplicati-host:8200 \
  -e DUPLICATI_DB_PATH=/duplicati-config/Duplicati-server.sqlite \
  -v duplicati_config:/duplicati-config:ro \
  kcofoni/duplicati-mcp:latest
```

## Technical Stack

- **Language**: Python 3.11
- **Framework**: FastMCP
- **Protocol**: MCP Streamable HTTP (2025)
- **Port**: 3000
- **Endpoint**: `/mcp`

## Verification

```bash
# Check server logs
docker logs duplicati-mcp-server

# Test the MCP endpoint
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

## Source Code

- GitHub: https://github.com/kcofoni/duplicati-mcp
- Issues: https://github.com/kcofoni/duplicati-mcp/issues

## License

MIT License - See [LICENSE](https://github.com/kcofoni/duplicati-mcp/blob/main/LICENSE) for details
