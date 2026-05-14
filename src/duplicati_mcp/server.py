"""MCP server exposing Duplicati backup management tools."""
import json
import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

from duplicati_mcp.client import DuplicatiClient, DuplicatiError
from duplicati_mcp.db import DuplicatiBackupDB, DuplicatiServerDB

mcp = FastMCP(
    "duplicati",
    host=os.environ.get("FASTMCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("FASTMCP_PORT", "8000")),
)

_READONLY = os.environ.get("DUPLICATI_READONLY", "").lower() in ("1", "true", "yes")
_DB_PATH = os.environ.get("DUPLICATI_DB_PATH", "")
_DB_ENABLED = bool(_DB_PATH)


def _readonly_error(tool: str) -> str:
    return f"Error: read-only mode is active — '{tool}' is disabled."


def _db_disabled_error() -> str:
    return "SQLite access is disabled — set the DUPLICATI_DB_PATH environment variable to enable it."


@lru_cache(maxsize=1)
def _get_server_db() -> DuplicatiServerDB:
    return DuplicatiServerDB(_DB_PATH)


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


# ---------------------------------------------------------------------------
# SQLite-backed tools (read-only access to Duplicati databases)
# ---------------------------------------------------------------------------

@mcp.tool()
async def db_get_backup_metadata(backup_id: str) -> str:
    """Return rich metadata for a backup job from the local SQLite database.

    Includes last run date, duration, file counts, quota usage, and last error.
    More detailed than what the REST API exposes.

    Args:
        backup_id: Numeric ID of the backup job (use list_backups to find IDs).
    """
    if not _DB_ENABLED:
        return _db_disabled_error()
    try:
        meta = _get_server_db().get_metadata(int(backup_id))
        if not meta:
            return f"No metadata found for backup job {backup_id}."
        return _fmt(meta)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def db_get_backup_schedule(backup_id: str) -> str:
    """Return the schedule configuration for a backup job from the local SQLite database.

    Args:
        backup_id: Numeric ID of the backup job.
    """
    if not _DB_ENABLED:
        return _db_disabled_error()
    try:
        schedule = _get_server_db().get_schedule(int(backup_id))
        if schedule is None:
            return f"Backup job {backup_id} has no schedule configured."
        return _fmt(schedule)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def db_list_errors(backup_id: str = "", limit: int = 20) -> str:
    """List recent error log entries from the local SQLite database.

    Args:
        backup_id: Numeric ID of the backup job (leave empty for all jobs).
        limit: Maximum number of entries to return (default 20).
    """
    if not _DB_ENABLED:
        return _db_disabled_error()
    try:
        bid = int(backup_id) if backup_id.strip() else None
        errors = _get_server_db().list_errors(backup_id=bid, limit=limit)
        if not errors:
            return "No error log entries found."
        return _fmt(errors)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def db_list_notifications(limit: int = 20) -> str:
    """List recent system notifications from the local SQLite database (update alerts, etc.).

    Args:
        limit: Maximum number of entries to return (default 20).
    """
    if not _DB_ENABLED:
        return _db_disabled_error()
    try:
        notifications = _get_server_db().list_notifications(limit=limit)
        if not notifications:
            return "No notifications found."
        return _fmt(notifications)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def db_get_backup_options(backup_id: str) -> str:
    """Return the configuration options for a backup job from the local SQLite database.

    Includes compression, encryption module, retention policy, file exclusions, etc.
    Sensitive values such as passphrases are excluded.

    Args:
        backup_id: Numeric ID of the backup job.
    """
    if not _DB_ENABLED:
        return _db_disabled_error()
    try:
        options = _get_server_db().get_options(int(backup_id))
        if not options:
            return f"No options found for backup job {backup_id}."
        return _fmt(options)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def db_list_operations(backup_id: str, limit: int = 20) -> str:
    """List recent operations (Backup, Restore, List, etc.) for a backup job.

    Reads from the per-backup SQLite database for detailed operation history.

    Args:
        backup_id: Numeric ID of the backup job.
        limit: Maximum number of operations to return (default 20).
    """
    if not _DB_ENABLED:
        return _db_disabled_error()
    try:
        db_path = _get_server_db().get_backup_db_path(int(backup_id))
        if db_path is None:
            return f"Backup job {backup_id} not found."
        if not os.path.exists(db_path):
            return f"Per-backup database not found at {db_path}."
        ops = DuplicatiBackupDB(db_path).list_operations(limit=limit)
        if not ops:
            return f"No operations found for backup job {backup_id}."
        return _fmt(ops)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def db_get_operation_log(backup_id: str, operation_id: str) -> str:
    """Return the detailed log and result statistics for a specific operation.

    Use db_list_operations to find operation IDs.

    Args:
        backup_id: Numeric ID of the backup job.
        operation_id: Numeric ID of the operation (from db_list_operations).
    """
    if not _DB_ENABLED:
        return _db_disabled_error()
    try:
        db_path = _get_server_db().get_backup_db_path(int(backup_id))
        if db_path is None:
            return f"Backup job {backup_id} not found."
        if not os.path.exists(db_path):
            return f"Per-backup database not found at {db_path}."
        log = DuplicatiBackupDB(db_path).get_operation_log(int(operation_id))
        return _fmt(log)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def db_list_filesets(backup_id: str, limit: int = 20) -> str:
    """List available restore points (backup versions) for a backup job.

    Args:
        backup_id: Numeric ID of the backup job.
        limit: Maximum number of filesets to return (default 20).
    """
    if not _DB_ENABLED:
        return _db_disabled_error()
    try:
        db_path = _get_server_db().get_backup_db_path(int(backup_id))
        if db_path is None:
            return f"Backup job {backup_id} not found."
        if not os.path.exists(db_path):
            return f"Per-backup database not found at {db_path}."
        filesets = DuplicatiBackupDB(db_path).list_filesets(limit=limit)
        if not filesets:
            return f"No restore points found for backup job {backup_id}."
        return _fmt(filesets)
    except Exception as e:
        return f"Error: {e}"


def main() -> None:
    """Entry point — selects stdio or streamable-http transport based on MCP_TRANSPORT env var."""
    if os.environ.get("MCP_TRANSPORT") == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
