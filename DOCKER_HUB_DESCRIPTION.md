# Duplicati MCP Server

A Model Context Protocol (MCP) server that gives LLMs full control over Duplicati backup jobs through a standardized interface.

## What is this?

This Docker image runs an MCP server that wraps the Duplicati REST API using the Streamable HTTP transport (MCP 2025 standard). It enables AI assistants like Claude to list, run, monitor, and configure Duplicati backup jobs.

## Features

- **Backup Management**: List jobs, trigger runs, abort active backups
- **Live Monitoring**: Real-time progress, phase, file counts and ETA
- **Config Export/Import**: Export job configurations as JSON for migration or backup
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
    restart: unless-stopped
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

1. **list_backups**: List all configured backup jobs with status and last run info
2. **get_backup**: Get detailed information about a specific job
3. **run_backup**: Trigger a backup job immediately
4. **abort_backup**: Abort the currently running backup for a job
5. **get_progress**: Get live progress of the active backup task
6. **get_server_status**: Get Duplicati server state and version
7. **export_backup_config**: Export a job configuration as JSON
8. **update_backup_config**: Update an existing job configuration in place (use with `export_backup_config` to modify sources, settings, schedule, etc.)
9. **import_backup_config**: Import a job configuration from JSON

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DUPLICATI_URL` | `http://duplicati:8200` | URL of the Duplicati instance |
| `DUPLICATI_PASSWORD` | _(empty)_ | Duplicati web interface password |
| `DUPLICATI_READONLY` | `false` | Set to `true` to disable write operations |

## Read-only Mode

Set `DUPLICATI_READONLY=true` to disable all write operations (`run_backup`, `abort_backup`, `update_backup_config`, `import_backup_config`). Read tools remain fully available — useful for safely exploring and analyzing your backup configuration.

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
