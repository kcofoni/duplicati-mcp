# MCP Server Publication Guide

This guide covers publishing the Duplicati MCP server to all three registries: **PyPI**, **Docker Hub**, and the **official MCP registry**.

---

## Releasing a New Version — Step by Step

Use this section as a checklist whenever you want to publish a new version.

### Step 0: Decide the version number

Follow [Semantic Versioning](https://semver.org/):
- **Patch** (`1.0.0` → `1.0.1`): bug fixes, doc corrections, minor internal changes
- **Minor** (`1.0.0` → `1.1.0`): new tools, new features, backward-compatible changes
- **Major** (`1.0.0` → `2.0.0`): breaking changes (auth, transport, tool signatures)

### Step 1: Ensure everything is committed

```bash
git status
```

If there are uncommitted changes, commit them first with a descriptive message before creating the release commit.

### Step 2: Bump the version

Update the version number in three files:

**`pyproject.toml`**
```toml
version = "X.Y.Z"
```

**`CHANGELOG.md`** — add a new section at the top:
```markdown
## [vX.Y.Z] - YYYY-MM-DD

### Added / Changed / Fixed
- ...
```

**`mcp-publication/duplicati/server.json`**
```json
"version": "X.Y.Z",
"identifier": "docker.io/kcofoni/duplicati-mcp:vX.Y.Z"
```

### Step 3: Rebuild the package

```bash
uv build
```

> Always rebuild after any source or README change — the `.tar.gz` contains the README displayed on PyPI.

### Step 4: Commit, tag and push to GitHub

```bash
git add .
git commit -m "Release vX.Y.Z — <one-line summary>"
git tag vX.Y.Z
git push origin main --tags
```

### Step 5: Publish to Docker Hub

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t kcofoni/duplicati-mcp:vX.Y.Z \
  -t kcofoni/duplicati-mcp:latest \
  --push \
  .
```

Verify the image is public at https://hub.docker.com/r/kcofoni/duplicati-mcp

### Step 6: Publish to PyPI

#### 6a — TestPyPI first

```bash
export PYPI_TEST_TOKEN=$(grep '^PYPI_TEST_TOKEN=' .env | cut -d= -f2-)
UV_PUBLISH_TOKEN=$PYPI_TEST_TOKEN uv publish --index testpypi
```

Verify at https://test.pypi.org/project/duplicati-mcp/ before proceeding.

#### 6b — PyPI production

```bash
export UV_PUBLISH_TOKEN=$(grep '^UV_PUBLISH_TOKEN=' .env | cut -d= -f2-)
uv publish
```

Verify at https://pypi.org/project/duplicati-mcp/

### Step 7: Publish to the MCP registry

> **Reminder**: authenticate before publishing if you haven't done so in this session:
> ```bash
> cd mcp-publication/duplicati
> mcp-publisher login github
> ```

```bash
cd mcp-publication/duplicati
mcp-publisher publish
```

Verify at https://registry.modelcontextprotocol.io

### Step 8: Final checks

- [ ] GitHub tag `vX.Y.Z` visible at https://github.com/kcofoni/duplicati-mcp/releases
- [ ] Docker Hub shows `vX.Y.Z` and updated `latest`
- [ ] PyPI page shows correct version and README
- [ ] MCP registry returns the server when searching "duplicati"
- [ ] `uvx duplicati-mcp@latest` installs and starts correctly

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

**422 validation error**: run the registry validator to get the exact error details:
```bash
curl -s -X POST https://registry.modelcontextprotocol.io/v0.1/validate \
  -H "Content-Type: application/json" \
  -d @server.json | python3 -m json.tool
```
Common causes: description over 100 characters, invalid transport type (use `streamable-http` not `http`).

---

## Resources

- **PyPI**: https://pypi.org/project/duplicati-mcp/
- **TestPyPI**: https://test.pypi.org/project/duplicati-mcp/
- **Docker Hub**: https://hub.docker.com/r/kcofoni/duplicati-mcp
- **MCP Registry**: https://registry.modelcontextprotocol.io
- **Server Schema**: https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json
