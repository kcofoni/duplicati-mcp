# Duplicati MCP Server

MCP (Model Context Protocol) server for managing Duplicati backups from an LLM.

[Version française / French version](README_fr.md)

## Architecture

The server wraps the Duplicati REST API and exposes it via the MCP protocol. Two transports are supported:

- **stdio** — for local use via Claude Code (no network, no port)
- **Streamable HTTP** — for Docker deployment, accessible over the network

## Getting Started

### Local use with Claude Code (stdio)

The simplest way to get started. The `.mcp.json` at the project root handles everything:

```bash
# Install uv if needed
brew install uv

# Claude Code will auto-detect .mcp.json and launch the server
```

Set your Duplicati URL and password in `.mcp.json`:

```json
{
  "mcpServers": {
    "duplicati": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "duplicati-mcp"],
      "env": {
        "DUPLICATI_URL": "http://localhost:8200",
        "DUPLICATI_PASSWORD": "your-password",
        "DUPLICATI_READONLY": ""
      }
    }
  }
}
```

### With Docker Compose (Docker Hub image)

```bash
# Edit DUPLICATI_URL and DUPLICATI_PASSWORD in docker-compose.yml, then:
docker compose up -d
```

### With Docker Compose (local build)

```bash
# Edit docker-compose.yml: comment out `image:` and uncomment `build: .`
docker compose up -d --build
```

### Direct Docker usage

```bash
docker run -d \
  --name duplicati-mcp-server \
  -p 3000:3000 \
  -e DUPLICATI_URL=http://your-duplicati-host:8200 \
  -e DUPLICATI_PASSWORD=your-password \
  kcofoni/duplicati-mcp:latest
```

### Verification

```bash
# Check that the server is running
docker logs duplicati-mcp-server

# Test the MCP endpoint
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

## Client Configuration (Docker/remote)

### Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "duplicati": {
      "type": "http",
      "url": "http://your-host:3000/mcp"
    }
  }
}
```

### Claude Desktop

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "duplicati": {
      "type": "http",
      "url": "http://your-host:3000/mcp"
    }
  }
}
```

## Available Tools

Once connected, the LLM has access to:

### Backup Jobs
1. **list_backups** — List all configured jobs with ID, name, last run date and result
2. **get_backup** — Get detailed information about a specific job
3. **run_backup** — Trigger a backup job immediately
4. **abort_backup** — Abort the currently running backup for a job

### Status & Progress
5. **get_progress** — Live progress of the active backup task (phase, %, file counts)
6. **get_server_status** — Duplicati server state, version and active task

### Configuration
7. **export_backup_config** — Export a job configuration as JSON
8. **import_backup_config** — Import a job configuration from JSON

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DUPLICATI_URL` | `http://localhost:8200` | URL of the Duplicati instance |
| `DUPLICATI_PASSWORD` | _(empty)_ | Duplicati web interface password (leave empty if none set) |
| `DUPLICATI_READONLY` | _(empty)_ | Set to `true`, `1` or `yes` to disable write operations |
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `3000` | Port for Streamable HTTP transport |

### Read-only Mode

`DUPLICATI_READONLY=true` disables `run_backup`, `abort_backup` and `import_backup_config`. All read tools remain active. Useful for safely exploring and analysing backup configurations without any risk of modification.

## Docker Hub

- **Repository**: [kcofoni/duplicati-mcp](https://hub.docker.com/r/kcofoni/duplicati-mcp)
- **Latest tag**: `kcofoni/duplicati-mcp:latest`

```bash
docker pull kcofoni/duplicati-mcp:latest
```

## Development

### File Structure

```
duplicati-mcp/
├── src/
│   └── duplicati_mcp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── client.py        # Duplicati REST API client
│       └── server.py        # FastMCP server and tools
├── mcp-publication/         # MCP registry publication files
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project metadata
├── Dockerfile
├── docker-compose.yml
├── .mcp.json                # Claude Code local config (stdio)
├── test_server.sh           # Docker container smoke test
├── test_mcp.py              # MCP protocol test
├── README.md                # This file (English)
└── README_fr.md             # French documentation
```

### Running Tests

```bash
# Smoke test (requires running Docker container)
./test_server.sh

# MCP protocol test (requires running server)
python test_mcp.py
python test_mcp.py localhost:3000
```

### Interactive Tool Testing (local)

```bash
uv run mcp dev src/duplicati_mcp/server.py
```

## Troubleshooting

### Cannot connect to Duplicati

Check that `DUPLICATI_URL` is reachable from the container. If both run in Docker, put them on the same network and use the service name as hostname.

### Authentication failed

Verify `DUPLICATI_PASSWORD` matches the password set in Duplicati's web interface. Leave empty if no password is configured.

### MCP endpoint not responding

```bash
docker ps | grep duplicati-mcp-server
docker logs duplicati-mcp-server
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
