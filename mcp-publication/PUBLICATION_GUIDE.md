# MCP Server Publication Guide

This guide explains how to publish the Duplicati MCP server to the official MCP registry from the command line using the `mcp-publisher` tool.

## Prerequisites

Before publishing, ensure you have:

1. **mcp-publisher**: The official MCP publication tool
   ```bash
   curl -L "https://github.com/modelcontextprotocol/registry/releases/download/v1.4.0/mcp-publisher_linux_amd64.tar.gz" | tar xz && sudo mv mcp-publisher /usr/local/bin/
   ```

2. **GitHub Account**: You need a GitHub account for namespace authentication (e.g., `io.github.username/*`)
3. **Docker and Docker Hub**: To build and publish the Docker image
4. **Updated server.json**: The `server.json` file must be properly configured

## Step 1: Verify Your Configuration

Check that [`mcp-publication/duplicati/server.json`](./duplicati/server.json) is correctly configured:

```bash
cat mcp-publication/duplicati/server.json
```

Key fields to verify:
- `name`: Should be `io.github.kcofoni/duplicati-mcp`
- `version`: Must match your Docker image tag (e.g., `0.1.0`)
- `repository.url`: Your GitHub repository URL
- `packages[0].identifier`: Docker image with correct version tag

Authenticate with Docker Hub before building:

```bash
docker login
```

## Step 2: Build and Publish Docker Image

The MCP registry requires Docker images to support `linux/amd64`.

### Option A: Simple Build (Linux AMD64)

```bash
docker build -t kcofoni/duplicati-mcp:v0.1.0 -t kcofoni/duplicati-mcp:latest .
docker push kcofoni/duplicati-mcp:v0.1.0
docker push kcofoni/duplicati-mcp:latest
```

### Option B: Multi-Architecture Build (Mac / ARM64)

```bash
# One-time setup
docker buildx create --use --name multiarch

# Build and push for linux/amd64 and linux/arm64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t kcofoni/duplicati-mcp:v0.1.0 \
  -t kcofoni/duplicati-mcp:latest \
  --push \
  .
```

> **Note**: Building from a Mac without buildx creates ARM64-only images, which will fail MCP registry validation.

## Step 3: Authenticate with mcp-publisher

```bash
cd mcp-publication/duplicati
mcp-publisher login github
```

Follow the GitHub OAuth flow.

## Step 4: Publish

```bash
mcp-publisher publish
```

The tool will validate `server.json`, authenticate your namespace, and submit to the registry.

## Step 5: Verify

On success you'll see:
```
✓ Successfully published io.github.kcofoni/duplicati-mcp@0.1.0
```

Your server will be searchable at https://registry.modelcontextprotocol.io.

## Updating an Existing Publication

1. Update `version` in `server.json`
2. Build and push the new Docker image with the matching tag
3. Re-run `mcp-publisher publish`

## Troubleshooting

### Error "no child with platform linux/amd64"

Use Option B (buildx) when building from a Mac.

### Publication fails with validation errors

```bash
# Validate your server.json
jq . mcp-publication/duplicati/server.json
```

Ensure the Docker image exists and is public on Docker Hub.

## Resources

- **MCP Registry**: https://github.com/modelcontextprotocol/registry
- **Server Schema**: https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json
