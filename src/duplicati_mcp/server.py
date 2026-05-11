"""MCP server exposing Duplicati backup management tools."""
import json
import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

from .client import DuplicatiClient, DuplicatiError

mcp = FastMCP(
    "duplicati",
    host=os.environ.get("FASTMCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("FASTMCP_PORT", "8000")),
)

_READONLY = os.environ.get("DUPLICATI_READONLY", "").lower() in ("1", "true", "yes")


def _readonly_error(tool: str) -> str:
    return f"Error: read-only mode is active — '{tool}' is disabled."


@lru_cache(maxsize=1)
def _get_client() -> DuplicatiClient:
    url = os.environ.get("DUPLICATI_URL", "http://localhost:8200")
    password = os.environ.get("DUPLICATI_PASSWORD") or None
    return DuplicatiClient(url, password)


def _fmt(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def list_backups() -> str:
    """List all configured Duplicati backup jobs with ID, name, last run date and result."""
    try:
        backups = await _get_client().list_backups()
        if not backups:
            return "No backup jobs configured."
        summary = []
        for entry in backups:
            b = entry.get("Backup", entry)
            meta = entry.get("Metadata", {}) if "Metadata" in entry else b.get("Metadata", {})
            summary.append({
                "id": b.get("ID"),
                "name": b.get("Name"),
                "last_run": meta.get("LastBackupDate"),
                "last_duration": meta.get("LastBackupDuration"),
                "last_result": meta.get("LastBackupResult"),
                "source_folders": b.get("Sources"),
                "target": b.get("TargetURL"),
            })
        return _fmt(summary)
    except DuplicatiError as e:
        return f"Error: {e}"


@mcp.tool()
async def get_backup(backup_id: str) -> str:
    """Get detailed information about a specific backup job.

    Args:
        backup_id: Numeric ID of the backup job (use list_backups to find IDs).
    """
    try:
        data = await _get_client().get_backup(backup_id)
        return _fmt(data)
    except DuplicatiError as e:
        return f"Error: {e}"


@mcp.tool()
async def run_backup(backup_id: str) -> str:
    """Trigger a backup job to run immediately.

    Args:
        backup_id: Numeric ID of the backup job to run.
    """
    if _READONLY:
        return _readonly_error("run_backup")
    try:
        result = await _get_client().run_backup(backup_id)
        return f"Backup job {backup_id} started.\n" + _fmt(result)
    except DuplicatiError as e:
        return f"Error: {e}"


@mcp.tool()
async def abort_backup(backup_id: str) -> str:
    """Abort the currently running backup task for a job.

    Args:
        backup_id: Numeric ID of the backup job to abort.
    """
    if _READONLY:
        return _readonly_error("abort_backup")
    try:
        result = await _get_client().abort_backup(backup_id)
        return f"Abort signal sent for backup job {backup_id}.\n" + _fmt(result)
    except DuplicatiError as e:
        return f"Error: {e}"


@mcp.tool()
async def get_progress() -> str:
    """Get the live progress of the currently running backup task (phase, %, file counts)."""
    try:
        progress = await _get_client().get_progress()
        if not progress or progress.get("Phase") in (None, "", "None"):
            return "No backup task is currently running."
        return _fmt(progress)
    except DuplicatiError as e:
        return f"Error: {e}"


@mcp.tool()
async def get_server_status() -> str:
    """Get Duplicati server status: version, program state, active task, and scheduler info."""
    try:
        status = await _get_client().get_server_status()
        return _fmt(status)
    except DuplicatiError as e:
        return f"Error: {e}"


@mcp.tool()
async def export_backup_config(backup_id: str) -> str:
    """Export a backup job configuration as a JSON string for backup or migration.

    Args:
        backup_id: Numeric ID of the backup job to export.
    """
    try:
        config = await _get_client().export_backup(backup_id)
        return _fmt(config)
    except DuplicatiError as e:
        return f"Error: {e}"



@mcp.tool()
async def update_backup_config(backup_id: str, config_json: str) -> str:
    """Update an existing backup job from a modified JSON configuration (as exported by export_backup_config).
    Use this to modify sources, settings, schedule, filters, etc. on an existing job.

    Args:
        backup_id: Numeric ID of the backup job to update.
        config_json: Modified JSON string of the backup configuration.
    """
    if _READONLY:
        return _readonly_error("update_backup_config")
    try:
        config = json.loads(config_json)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON — {e}"
    backup = config.get("Backup", config)
    payload = {"Backup": backup, "Schedule": config.get("Schedule")}
    try:
        await _get_client().update_backup(backup_id, payload)
        return f"Backup job {backup_id} updated successfully."
    except DuplicatiError as e:
        return f"Error: {e}"


@mcp.tool()
async def import_backup_config(config_json: str) -> str:
    """Import a backup job from a JSON configuration string (as produced by export_backup_config).

    Args:
        config_json: JSON string of the backup configuration to import.
    """
    if _READONLY:
        return _readonly_error("import_backup_config")
    try:
        config = json.loads(config_json)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON — {e}"
    try:
        result = await _get_client().import_backup(config)
        return "Backup configuration imported successfully.\n" + _fmt(result)
    except DuplicatiError as e:
        return f"Error: {e}"


def main() -> None:
    """Entry point — selects stdio or streamable-http transport based on MCP_TRANSPORT env var."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport if transport == "streamable-http" else "stdio")
