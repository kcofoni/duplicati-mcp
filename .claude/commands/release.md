# Release a new version of duplicati-mcp

Guide the user through a full release: bump version, build, commit, tag, and publish to GitHub, Docker Hub, PyPI, and the MCP registry.

## Instructions

### Step 0 — Determine the new version

If `$ARGUMENTS` is provided, use it directly as the new version (e.g. `/release 1.1.0` or `/release patch`).

Otherwise, read the current version from `pyproject.toml` and ask the user:
- **patch** (bug fixes, docs): `X.Y.Z` → `X.Y.Z+1`
- **minor** (new features, new tools): `X.Y.Z` → `X.Y+1.0`
- **major** (breaking changes): `X.Y.Z` → `X+1.0.0`
- or an explicit version number

If a bump type (patch/minor/major) is given rather than an explicit version, compute the new version from the current one.

Confirm the new version with the user before proceeding.

### Step 1 — Ensure a clean state

Run `git status`. If there are uncommitted changes, ask the user whether to commit them first (with a message they provide) or to include them in the release commit.

### Step 2 — Bump the version in all three files

Update the version string in:
1. `pyproject.toml` — `version = "X.Y.Z"`
2. `CHANGELOG.md` — add a new `## [vX.Y.Z] - YYYY-MM-DD` section at the top; ask the user for the changelog entries
3. `mcp-publication/duplicati/server.json` — `"version"` field and `"identifier"` field (`docker.io/kcofoni/duplicati-mcp:vX.Y.Z`)

### Step 3 — Rebuild the package

```bash
uv build
```

The `.tar.gz` contains the README shown on PyPI — always rebuild.

### Step 4 — Commit, tag and push to GitHub

```bash
git add .
git commit -m "Release vX.Y.Z — <summary>"
git tag vX.Y.Z
git push origin main --tags
```

Ask the user to confirm the commit message before running.

### Step 5 — Publish to Docker Hub

Ask the user to confirm before running:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t kcofoni/duplicati-mcp:vX.Y.Z \
  -t kcofoni/duplicati-mcp:latest \
  --push \
  .
```

Verify the push succeeded.

### Step 6 — Publish to PyPI

Load the token from `.env` and publish. Ask before running:

```bash
source .env && uv publish
```

Verify at https://pypi.org/project/duplicati-mcp/

### Step 7 — Publish to the MCP registry

```bash
cd mcp-publication/duplicati
mcp-publisher publish
```

If not authenticated, run `mcp-publisher login github` first.

### Step 8 — Final checklist

Confirm each item with the user:
- [ ] GitHub tag `vX.Y.Z` visible at https://github.com/kcofoni/duplicati-mcp/releases
- [ ] Docker Hub shows `vX.Y.Z` and updated `latest`
- [ ] PyPI page shows correct version and README
- [ ] MCP registry returns the server when searching "duplicati"
- [ ] `uvx duplicati-mcp@latest` installs and starts correctly
