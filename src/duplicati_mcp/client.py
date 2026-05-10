"""Async client for the Duplicati REST API."""
import httpx
from typing import Any


class DuplicatiError(Exception):
    """Raised when the Duplicati API returns an error or is unreachable."""


class DuplicatiClient:
    """Async HTTP client for the Duplicati REST API with JWT authentication."""

    def __init__(self, base_url: str, password: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._password = password
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=60.0,
            follow_redirects=True,
        )
        self._access_token: str | None = None

    async def _authenticate(self) -> None:
        if not self._password:
            return
        try:
            resp = await self._client.post(
                "/api/v1/auth/login",
                json={"Password": self._password},
            )
        except httpx.ConnectError as e:
            raise DuplicatiError(f"Cannot connect to Duplicati at {self._base_url}: {e}") from e
        if resp.status_code == 401:
            raise DuplicatiError("Authentication failed: incorrect password")
        resp.raise_for_status()
        self._access_token = resp.json().get("AccessToken")

    async def _req(self, method: str, path: str, **kwargs: Any) -> Any:
        if self._password and not self._access_token:
            await self._authenticate()

        headers: dict = kwargs.pop("headers", {})
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            resp = await self._client.request(method, path, headers=headers, **kwargs)
        except httpx.ConnectError as e:
            raise DuplicatiError(f"Cannot connect to Duplicati at {self._base_url}: {e}") from e

        if resp.status_code == 401:
            self._access_token = None
            await self._authenticate()
            headers["Authorization"] = f"Bearer {self._access_token}"
            resp = await self._client.request(method, path, headers=headers, **kwargs)

        if resp.status_code == 404:
            raise DuplicatiError(f"Resource not found: {path}")

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise DuplicatiError(f"Duplicati API error {resp.status_code}: {resp.text}") from e

        return resp.json() if resp.content else {}

    async def list_backups(self) -> list[dict]:
        """Return all configured backup jobs."""
        result = await self._req("GET", "/api/v1/backups")
        return result if isinstance(result, list) else []

    async def get_backup(self, backup_id: str) -> dict:
        """Return full details for a backup job."""
        return await self._req("GET", f"/api/v1/backup/{backup_id}")

    async def run_backup(self, backup_id: str) -> dict:
        """Trigger a backup job to run immediately."""
        return await self._req("POST", f"/api/v1/backup/{backup_id}/run")

    async def abort_backup(self, backup_id: str) -> dict:
        """Abort the currently running backup for a job."""
        return await self._req("POST", f"/api/v1/backup/{backup_id}/abort")

    async def get_progress(self) -> dict:
        """Return live progress of the active backup task."""
        return await self._req("GET", "/api/v1/progressstate")

    async def get_server_status(self) -> dict:
        """Return server state, version, and active task info."""
        return await self._req("GET", "/api/v1/serverstate")

    async def export_backup(self, backup_id: str) -> dict:
        """Export a backup job configuration as a dict."""
        return await self._req("GET", f"/api/v1/backup/{backup_id}/export")

    async def update_backup(self, backup_id: str, payload: dict) -> dict:
        """Update an existing backup job configuration via PUT."""
        return await self._req("PUT", f"/api/v1/backup/{backup_id}", json=payload)

    async def import_backup(self, config: dict) -> dict:
        """Import a backup job from a configuration dict."""
        return await self._req(
            "POST",
            "/api/v1/backups/import",
            json={"config": config, "cmdline": False, "import-metadata": False},
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
