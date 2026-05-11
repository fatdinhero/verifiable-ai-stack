"""MemoryStore module providing persistent key-value storage backed by SQLite."""

import sqlite3
import json
import time
from typing import Optional


class MemoryStore:
    """A persistent memory store that associates run IDs with data dictionaries.

    Uses a local SQLite database as backend. Each entry is automatically
    timestamped upon saving.

    Attributes:
        db_path: Filesystem path to the SQLite database file.
    """

    def __init__(self, db_path: str = "cognitum_memory.db") -> None:
        """Initialize the MemoryStore and ensure the database table exists.

        Args:
            db_path: Path to the SQLite database file.
                     Defaults to "cognitum_memory.db" in the current directory.
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Create the memory table if it does not already exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    run_id    TEXT PRIMARY KEY,
                    data      TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
                """
            )
            conn.commit()

    def save(self, run_id: str, data: dict) -> None:
        """Persist a data dictionary under the given run ID.

        If the run ID already exists the previous entry is overwritten.
        A Unix-epoch timestamp is recorded automatically.

        Args:
            run_id: Unique identifier for the run.
            data:   Arbitrary dictionary to store. Must be JSON-serialisable.
        """
        timestamp = time.time()
        payload = json.dumps(data)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO memory (run_id, data, timestamp)
                VALUES (?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    data      = excluded.data,
                    timestamp = excluded.timestamp
                """,
                (run_id, payload, timestamp),
            )
            conn.commit()

    def load(self, run_id: str) -> dict:
        """Retrieve the data dictionary associated with a run ID.

        Args:
            run_id: The run identifier whose data should be loaded.

        Returns:
            The stored dictionary for the given run ID.

        Raises:
            KeyError: If no entry exists for the provided run ID.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM memory WHERE run_id = ?", (run_id,)
            )
            row = cursor.fetchone()

        if row is None:
            raise KeyError(f"No memory entry found for run_id: {run_id!r}")

        return json.loads(row[0])