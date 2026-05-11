"""
cognitum_audit/audit_logger.py

Immutable audit logger backed by SQLite.
All entries are INSERT-only; no UPDATE or DELETE operations are supported.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any


class AuditLogger:
    """Logs agent actions to an immutable SQLite-backed audit trail.

    Every call to ``log`` appends a new row. The underlying database file
    is created on first instantiation if it does not already exist.

    Args:
        db_path: Filesystem path for the SQLite database.
                 Defaults to ``"cognitum_audit.db"``.
    """

    _CREATE_TABLE_SQL = """\
        CREATE TABLE IF NOT EXISTS audit_log (
            id          TEXT PRIMARY KEY,
            timestamp   TEXT NOT NULL,
            agent       TEXT NOT NULL,
            action      TEXT NOT NULL,
            result_json TEXT NOT NULL,
            confidence  REAL NOT NULL
        );
    """

    def __init__(self, db_path: str = "cognitum_audit.db") -> None:
        self._db_path = db_path
        self._connection = sqlite3.connect(self._db_path)
        self._connection.execute("PRAGMA journal_mode=WAL;")
        self._connection.execute(self._CREATE_TABLE_SQL)
        self._connection.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log(
        self,
        agent: str,
        action: str,
        result: dict[str, Any],
        confidence: float,
    ) -> None:
        """Append an immutable audit entry.

        Args:
            agent:      Identifier of the agent that performed the action.
            action:     Short description of the audited action.
            result:     Arbitrary result dictionary; stored as JSON text.
            confidence: Confidence score in the range [0.0, 1.0].

        Raises:
            ValueError: If *confidence* is outside the [0.0, 1.0] range.
            TypeError:  If *result* is not a dict.
        """
        if not isinstance(result, dict):
            raise TypeError(
                f"result must be a dict, got {type(result).__name__}"
            )
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {confidence}"
            )

        entry_id = uuid.uuid4().hex
        timestamp = datetime.now(timezone.utc).isoformat()
        result_json = json.dumps(result, ensure_ascii=False, default=str)

        self._connection.execute(
            """\
            INSERT INTO audit_log (id, timestamp, agent, action, result_json, confidence)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (entry_id, timestamp, agent, action, result_json, confidence),
        )
        self._connection.commit()

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying database connection."""
        self._connection.close()

    def __enter__(self) -> "AuditLogger":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"AuditLogger(db_path={self._db_path!r})"