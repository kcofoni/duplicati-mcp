import httpx
from typing import Any


class DuplicatiError(Exception):
    pass


class DuplicatiClient:
    def __init__(self, base_url: str, password: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._password = password
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=60.0,
            follow_redirects=True,
        )
        self._xsrf_token: str | None = None
        self._authenticated = False

    async def _fetch_xsrf_token(self) -> str:
        resp = await self._client.get("/api/v1/auth/refresh")
        resp.raise_for_status()
        data = resp.json()
        return data.get("Token") or resp.cookies.get("xsrf-token") or ""

    async def _authenticate(self) -> None:
        if not self._password:
            self._authenticated = True
            return
        token = await self._fetch_xsrf_token()
        resp = await self._client.post(
            "/api/v1/auth/login",
            json={"Password": self._password},
            headers={"X-XSRF-Token": token},
        )
        if resp.status_code == 401:
            raise DuplicatiError("Authentication failed: incorrect password")
        resp.raise_for_status()
        self._xsrf_token = token
        self._authenticated = True

    async def _req(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self._authenticated:
            await self._authenticate()

        headers: dict = kwargs.pop("headers", {})
        if self._xsrf_token:
            headers["X-XSRF-Token"] = self._xsrf_token

        try:
            resp = await self._client.request(method, path, headers=headers, **kwargs)
        except httpx.ConnectError as e:
            raise DuplicatiError(f"Cannot connect to Duplicati at {self._base_url}: {e}")

        if resp.status_code == 401:
            # Token expired — re-authenticate once
            self._authenticated = False
            self._xsrf_token = None
            await self._authenticate()
            headers["X-XSRF-Token"] = self._xsrf_token
            resp = await self._client.request(method, path, headers=headers, **kwargs)

        if resp.status_code == 404:
            raise DuplicatiError(f"Resource not found: {path}")

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise DuplicatiError(f"Duplicati API error {resp.status_code}: {resp.text}") from e

        return resp.json() if resp.content else {}

    async def list_backups(self) -> list[dict]:
        result = await self._req("GET", "/api/v1/backups")
        return result if isinstance(result, list) else []

    async def get_backup(self, backup_id: str) -> dict:
        return await self._req("GET", f"/api/v1/backup/{backup_id}")

    async def run_backup(self, backup_id: str) -> dict:
        return await self._req("POST", f"/api/v1/backup/{backup_id}/run")

    async def abort_backup(self, backup_id: str) -> dict:
        return await self._req("POST", f"/api/v1/backup/{backup_id}/abort")

    async def get_progress(self) -> dict:
        return await self._req("GET", "/api/v1/progressstate")

    async def get_server_status(self) -> dict:
        return await self._req("GET", "/api/v1/serverstate")

    async def export_backup(self, backup_id: str) -> dict:
        return await self._req("GET", f"/api/v1/backup/{backup_id}/export")

    async def import_backup(self, config: dict) -> dict:
        return await self._req(
            "POST",
            "/api/v1/backups/import",
            json={"config": config, "cmdline": False, "import-metadata": False},
        )

    async def aclose(self) -> None:
        await self._client.aclose()
