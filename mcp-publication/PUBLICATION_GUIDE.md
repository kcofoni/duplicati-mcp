# MCP Server Publication Guide

This guide covers publishing the Duplicati MCP server to all three registries: **PyPI**, **Docker Hub**, and the **official MCP registry**.

---

## Part 1 — PyPI

### Prerequisites

- A PyPI account at https://pypi.org
- A TestPyPI account at https://test.pypi.org (same account, separate registration)
- API tokens for both (created in account settings)

### Configuration

The `pyproject.toml` already contains the TestPyPI index configuration:

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
explicit = true
```

This tells `uv publish --index testpypi` where to upload.

### Step 1: Build the package

```bash
uv build
```

This generates two files in `dist/`:
- `duplicati_mcp-X.Y.Z-py3-none-any.whl` — wheel (installable binary)
- `duplicati_mcp-X.Y.Z.tar.gz` — source distribution (contains README, shown on PyPI)

> **Important**: Always rebuild before publishing if you changed `README.md` or any source file — the README inside the `.tar.gz` is what PyPI displays on the package page.

### Step 2: Dry-run (optional)

```bash
uv publish --index testpypi --dry-run
```

Lists the files that would be uploaded without actually uploading.

### Step 3: Publish to TestPyPI

```bash
UV_PUBLISH_TOKEN="your-testpypi-token" uv publish --index testpypi
```

> **Note on tokens**: PyPI uses project-scoped tokens (valid only for an existing project) and account-scoped tokens (valid for any project including new ones). For a **first publication**, you must use an account-scoped token — the project doesn't exist yet so a project-scoped token will return 403.

Verify at https://test.pypi.org/project/duplicati-mcp/

Test the installation:
```bash
pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  duplicati-mcp
```
(`--extra-index-url` is required because dependencies like `mcp` are not on TestPyPI.)

### Step 4: Publish to PyPI (production)

Once TestPyPI is validated:

```bash
UV_PUBLISH_TOKEN="your-pypi-token" uv publish
```

Verify at https://pypi.org/project/duplicati-mcp/

Test with uvx:
```bash
uvx duplicati-mcp@latest
```

### Updating an existing version

Bump `version` in `pyproject.toml`, rebuild, then republish. PyPI does not allow overwriting an existing version.

---

## Part 2 — Docker Hub

### Prerequisites

- Docker Hub account
- Logged in: `docker login`
- buildx configured (Mac / multi-arch builds)

### Step 1: One-time buildx setup (Mac only)

```bash
docker buildx create --use --name multiarch
```

### Step 2: Build and push multi-architecture image

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t kcofoni/duplicati-mcp:vX.Y.Z \
  -t kcofoni/duplicati-mcp:latest \
  --push \
  .
```

> **Note**: The MCP registry requires `linux/amd64`. Building from a Mac without buildx creates ARM64-only images and will fail registry validation.

Verify the image is public at https://hub.docker.com/r/kcofoni/duplicati-mcp

---

## Part 3 — Official MCP Registry

### Prerequisites

- Docker image already published on Docker Hub (Part 2 must be done first)
- `mcp-publisher` installed:
  ```bash
  curl -L "https://github.com/modelcontextprotocol/registry/releases/download/v1.4.0/mcp-publisher_linux_amd64.tar.gz" | tar xz && sudo mv mcp-publisher /usr/local/bin/
  ```
- `server.json` updated with correct version and Docker image tag

### Step 1: Verify server.json

```bash
cat mcp-publication/duplicati/server.json
```

Key fields to verify:
- `version`: must match the Docker image tag (e.g., `1.0.0`)
- `packages[0].identifier`: `docker.io/kcofoni/duplicati-mcp:vX.Y.Z`

Validate JSON:
```bash
jq . mcp-publication/duplicati/server.json
```

### Step 2: Authenticate

```bash
cd mcp-publication/duplicati
mcp-publisher login github
```

Follow the GitHub OAuth flow. Required once; token is cached locally.

### Step 3: Publish

```bash
mcp-publisher publish
```

On success:
```
✓ Successfully published io.github.kcofoni/duplicati-mcp@X.Y.Z
```

Verify at https://registry.modelcontextprotocol.io (search "duplicati").

### Updating an existing publication

1. Update `version` in `server.json`
2. Build and push the new Docker image (Part 2)
3. Re-run `mcp-publisher publish`

### Troubleshooting

**Error "no child with platform linux/amd64"**: use buildx (Step 2 of Part 2).

**403 on mcp-publisher**: ensure the Docker image is public on Docker Hub before publishing.

---

## Resources

- **PyPI**: https://pypi.org/project/duplicati-mcp/
- **TestPyPI**: https://test.pypi.org/project/duplicati-mcp/
- **Docker Hub**: https://hub.docker.com/r/kcofoni/duplicati-mcp
- **MCP Registry**: https://registry.modelcontextprotocol.io
- **Server Schema**: https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json
