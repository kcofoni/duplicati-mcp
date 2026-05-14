"""Read-only SQLite access to Duplicati databases (server DB + per-backup DBs)."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

_SENSITIVE_OPTION_NAMES = {"passphrase"}


def _open_safe(db_path: str) -> sqlite3.Connection:
    """Return an in-memory snapshot of db_path via the SQLite Online Backup API.

    Uses immutable=1 to bypass SQLite locking entirely — required on read-only
    filesystem mounts (:ro Docker volumes) where fcntl locks are not available.
    The source connection is closed immediately after the copy.
    """
    source = sqlite3.connect(f"file:{db_path}?immutable=1", uri=True)
    dest = sqlite3.connect(":memory:")
    source.backup(dest)
    source.close()
    dest.row_factory = sqlite3.Row
    return dest


def _unix_to_iso(ts: int | None) -> str | None:
    """Convert Unix timestamp to ISO 8601 string."""
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError):
        return None


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the set of column names for a table (empty set if table does not exist)."""
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {row["name"] for row in rows}
    except Exception:
        return set()


class DuplicatiServerDB:
    """Read-only access to Duplicati-server.sqlite."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return _open_safe(self._db_path)

    def get_backup_db_path(self, backup_id: int) -> str | None:
        """Return the resolved per-backup DB path.

        Duplicati stores Docker-internal paths (e.g. /config/XXXX.sqlite).
        The directory is replaced with dirname(self._db_path) so the path
        is valid wherever this server DB is mounted.
        """
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT DBPath FROM Backup WHERE ID=?", (backup_id,)
            ).fetchone()
            if row is None:
                return None
            return os.path.join(
                os.path.dirname(self._db_path), os.path.basename(row["DBPath"])
            )
        finally:
            conn.close()

    def get_metadata(self, backup_id: int) -> dict[str, Any]:
        """Return all Metadata key/value pairs for a backup job."""
        conn = self._conn()
        try:
            if not _columns(conn, "Metadata"):
                return {}
            rows = conn.execute(
                "SELECT Name, Value FROM Metadata WHERE BackupID=?", (backup_id,)
            ).fetchall()
            return {row["Name"]: row["Value"] for row in rows}
        finally:
            conn.close()

    def get_schedule(self, backup_id: int) -> dict[str, Any] | None:
        """Return the schedule for a backup job, or None if not scheduled.

        Schedule.Tags contains the backup reference as 'ID=<backup_id>', not Schedule.ID.
        Schedule timestamps (Time, LastRun) are Unix timestamps, not .NET ticks.
        LastRun = -62135596800 means the schedule has never run (stored as DateTime.MinValue).
        """
        conn = self._conn()
        try:
            if not _columns(conn, "Schedule"):
                return None
            row = conn.execute(
                "SELECT * FROM Schedule WHERE Tags LIKE ?", (f"%ID={backup_id}%",)
            ).fetchone()
            if row is None:
                return None
            entry = dict(row)
            entry["Time"] = _unix_to_iso(entry.get("Time"))
            last_run = entry.get("LastRun")
            entry["LastRun"] = _unix_to_iso(last_run) if last_run and last_run > 0 else None
            return entry
        finally:
            conn.close()

    def list_errors(self, backup_id: int | None = None, limit: int = 20) -> list[dict]:
        """Return recent error log entries, optionally filtered by backup job."""
        conn = self._conn()
        try:
            if not _columns(conn, "ErrorLog"):
                return []
            if backup_id is not None:
                rows = conn.execute(
                    "SELECT * FROM ErrorLog WHERE BackupID=? ORDER BY Timestamp DESC LIMIT ?",
                    (backup_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM ErrorLog ORDER BY Timestamp DESC LIMIT ?", (limit,)
                ).fetchall()
            result = []
            for row in rows:
                entry = dict(row)
                entry["Timestamp"] = _unix_to_iso(entry.get("Timestamp"))
                result.append(entry)
            return result
        finally:
            conn.close()

    def list_notifications(self, limit: int = 20) -> list[dict]:
        """Return recent system notifications (update alerts, errors, etc.)."""
        conn = self._conn()
        try:
            if not _columns(conn, "Notification"):
                return []
            rows = conn.execute(
                "SELECT * FROM Notification ORDER BY Timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            result = []
            for row in rows:
                entry = dict(row)
                entry["Timestamp"] = _unix_to_iso(entry.get("Timestamp"))
                result.append(entry)
            return result
        finally:
            conn.close()

    def get_options(self, backup_id: int) -> list[dict]:
        """Return configuration options for a backup job, excluding sensitive values."""
        conn = self._conn()
        try:
            if not _columns(conn, "Option"):
                return []
            rows = conn.execute(
                "SELECT Name, Value FROM Option WHERE BackupID=?", (backup_id,)
            ).fetchall()
            return [
                {"name": row["Name"], "value": row["Value"]}
                for row in rows
                if row["Name"].lower() not in _SENSITIVE_OPTION_NAMES
            ]
        finally:
            conn.close()


class DuplicatiBackupDB:
    """Read-only access to a per-backup Duplicati database.

    The db_path should be derived via DuplicatiServerDB.get_backup_db_path(),
    which resolves Docker-internal paths to host-accessible paths.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return _open_safe(self._db_path)

    def list_operations(self, limit: int = 20) -> list[dict]:
        """Return recent operations (Backup, Restore, List, etc.) with timestamps."""
        conn = self._conn()
        try:
            if not _columns(conn, "Operation"):
                return []
            rows = conn.execute(
                "SELECT ID, Description, Timestamp FROM Operation "
                "ORDER BY Timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                {
                    "id": row["ID"],
                    "type": row["Description"],
                    "timestamp": _unix_to_iso(row["Timestamp"]),
                }
                for row in rows
            ]
        finally:
            conn.close()

    def get_operation_log(self, operation_id: int) -> dict[str, Any]:
        """Return the full log for a specific operation, including parsed result statistics."""
        conn = self._conn()
        try:
            op = conn.execute(
                "SELECT ID, Description, Timestamp FROM Operation WHERE ID=?",
                (operation_id,),
            ).fetchone()
            if op is None:
                return {"error": f"Operation {operation_id} not found."}

            log_rows = conn.execute(
                "SELECT Type, Message, Exception, Timestamp FROM LogData "
                "WHERE OperationID=? ORDER BY Timestamp",
                (operation_id,),
            ).fetchall()

            result_json = None
            warnings = []
            errors = []
            for row in log_rows:
                if row["Type"] == "Result":
                    try:
                        result_json = json.loads(row["Message"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                elif row["Type"] == "Warning":
                    warnings.append(row["Message"])
                elif row["Type"] == "Error":
                    errors.append(row["Message"])

            entry: dict[str, Any] = {
                "id": op["ID"],
                "type": op["Description"],
                "timestamp": _unix_to_iso(op["Timestamp"]),
            }

            if result_json:
                # Surface key stats directly; omit verbose Messages array
                entry["result"] = {
                    k: v
                    for k, v in result_json.items()
                    if k != "Messages"
                }
            if warnings:
                entry["warnings"] = warnings
            if errors:
                entry["errors"] = errors

            return entry
        finally:
            conn.close()

    def list_filesets(self, limit: int = 20) -> list[dict]:
        """Return available restore points (backup versions) with timestamps."""
        conn = self._conn()
        try:
            if not _columns(conn, "Fileset"):
                return []
            rows = conn.execute(
                "SELECT f.ID, f.IsFullBackup, f.Timestamp, o.Description AS OperationType "
                "FROM Fileset f JOIN Operation o ON f.OperationID = o.ID "
                "ORDER BY f.Timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                {
                    "id": row["ID"],
                    "timestamp": _unix_to_iso(row["Timestamp"]),
                    "is_full_backup": bool(row["IsFullBackup"]),
                    "operation_type": row["OperationType"],
                }
                for row in rows
            ]
        finally:
            conn.close()
