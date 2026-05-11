"""
cognitum_agents/base_agent.py

BaseAgent – the foundational agent class for the Cognitum agent framework.
All domain-specific agents inherit from this base.

Dependencies: Python standard library only (including sqlite3).
"""

from __future__ import annotations

import logging
import sqlite3
import datetime
import hashlib
import json
import os
import uuid
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class BaseAgent:
    """Abstract-ish base agent that every Cognitum agent inherits from.

    Parameters
    ----------
    name : str
        A human-readable identifier for this agent (e.g. ``"ResearchAgent"``).
    policy_engine : optional
        An optional policy engine object.  When supplied the agent will consult
        it during ``run()`` to enforce constraints / guard-rails.  The engine
        is expected to expose an ``evaluate(action: dict) -> dict`` method
        returning ``{"allowed": bool, "reason": str}``.  If ``None`` no policy
        checks are performed.

    Notes
    -----
    * All heavy lifting lives in ``run()``; subclasses are encouraged to
      override ``_execute()`` instead of ``run()`` directly so that the
      built-in logging, policy-check and confidence-tagging logic is preserved.
    * An on-disk SQLite database (``cognitum_agents.db`` by default) is used
      for persistent run logs so that agent activity survives process restarts.
    """

    _DEFAULT_DB_PATH: str = "cognitum_agents.db"

    # --------------------------------------------------------------------- #
    #  Construction
    # --------------------------------------------------------------------- #

    def __init__(
        self,
        name: str,
        policy_engine: Any = None,
    ) -> None:
        if not name or not isinstance(name, str):
            raise ValueError("Agent 'name' must be a non-empty string.")

        self._name: str = name
        self._policy_engine: Any = policy_engine
        self._run_count: int = 0

        # Set up a dedicated logger for this agent instance.
        self._logger: logging.Logger = logging.getLogger(
            f"cognitum_agents.{self._name}"
        )
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.DEBUG)

        # SQLite-backed persistent log.
        self._db_path: str = os.environ.get(
            "COGNITUM_DB_PATH", self._DEFAULT_DB_PATH
        )
        self._init_db()

        self.log(f"Agent '{self._name}' initialised.")

    # --------------------------------------------------------------------- #
    #  Database helpers
    # --------------------------------------------------------------------- #

    def _get_connection(self) -> sqlite3.Connection:
        """Return a new SQLite connection (caller must close)."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        """Create the persistent log table if it does not already exist."""
        conn = self._get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id          TEXT PRIMARY KEY,
                    agent_name  TEXT NOT NULL,
                    timestamp   TEXT NOT NULL,
                    level       TEXT NOT NULL,
                    message     TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id              TEXT PRIMARY KEY,
                    agent_name      TEXT NOT NULL,
                    timestamp       TEXT NOT NULL,
                    task_fingerprint TEXT NOT NULL,
                    task_json       TEXT NOT NULL,
                    result_json     TEXT NOT NULL,
                    confidence      REAL NOT NULL
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    # --------------------------------------------------------------------- #
    #  Public API
    # --------------------------------------------------------------------- #

    @property
    def name(self) -> str:
        """Return the agent's human-readable name."""
        return self._name

    def log(self, message: str) -> None:
        """Persist *message* to both the Python logger and the SQLite store.

        Parameters
        ----------
        message : str
            Arbitrary human-readable text describing an agent event.
        """
        timestamp = datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        level = "INFO"

        # Write to Python logger.
        self._logger.info(message)

        # Persist to SQLite.
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO agent_logs (id, agent_name, timestamp, level, message)
                VALUES (?, ?, ?, ?, ?);
                """,
                (str(uuid.uuid4()), self._name, timestamp, level, message),
            )
            conn.commit()
        finally:
            conn.close()

    def run(self, task: dict) -> dict:
        """Execute a task and return a structured result.

        Parameters
        ----------
        task : dict
            An arbitrary task descriptor.  Must be JSON-serialisable.  Expected
            keys vary by agent subclass but common entries include
            ``"action"``, ``"query"``, ``"parameters"`` etc.

        Returns
        -------
        dict
            A dictionary with the following keys:

            * **summary** (``str``) – A concise one-liner describing the
              outcome.  If ``confidence < 0.8`` the prefix ``[Unverified]`` is
              prepended automatically.
            * **detail** (``str``) – A more verbose explanation of what was
              done and why.
            * **sources** (``list[str]``) – References, URLs or identifiers
              that back the result.
            * **confidence** (``float``) – A value in ``[0.0, 1.0]`` indicating
              how confident the agent is in its own output.
        """
        if not isinstance(task, dict):
            raise TypeError("task must be a dict")

        task_json: str = json.dumps(task, sort_keys=True, default=str)
        task_fingerprint: str = hashlib.sha256(task_json.encode()).hexdigest()

        self._run_count += 1
        self.log(
            f"Run #{self._run_count} started | task_fingerprint={task_fingerprint}"
        )

        # ---- Policy gate ------------------------------------------------ #
        if self._policy_engine is not None:
            try:
                policy_result: dict = self._policy_engine.evaluate(task)
                if not policy_result.get("allowed", True):
                    reason: str = policy_result.get("reason", "blocked by policy")
                    self.log(f"Run #{self._run_count} blocked by policy: {reason}")
                    result: dict = {
                        "summary": f"[Blocked] {reason}",
                        "detail": (
                            f"The policy engine refused to execute this task. "
                            f"Reason: {reason}"
                        ),
                        "sources": [],
                        "confidence": 0.0,
                    }
                    self._persist_run(task_fingerprint, task_json, result)
                    return result
            except Exception as exc:
                self.log(f"Policy engine error (continuing without policy): {exc}")

        # ---- Delegate to subclass --------------------------------------- #
        try:
            result = self._execute(task)
        except Exception as exc:
            self.log(f"Run #{self._run_count} raised an exception: {exc}")
            result = {
                "summary": f"[Error] {exc}",
                "detail": (
                    f"Agent '{self._name}' encountered an unrecoverable error "
                    f"while processing the task. Exception: {type(exc).__name__}: {exc}"
                ),
                "sources": [],
                "confidence": 0.0,
            }

        # ---- Validate & normalise result -------------------------------- #
        result = self._normalise_result(result)

        # ---- Confidence tagging ----------------------------------------- #
        confidence: float = result.get("confidence", 0.0)
        summary: str = result.get("summary", "")
        if confidence < 0.8 and not summary.startswith("[Unverified]"):
            result["summary"] = f"[Unverified] {summary}"

        # ---- Persist & return ------------------------------------------- #
        self._persist_run(task_fingerprint, task_json, result)
        self.log(
            f"Run #{self._run_count} completed | confidence={result['confidence']:.2f}"
        )
        return result

    # --------------------------------------------------------------------- #
    #  Extension points for subclasses
    # --------------------------------------------------------------------- #

    def _execute(self, task: dict) -> dict:
        """Override in subclasses to implement the actual task logic.

        Parameters
        ----------
        task : dict
            The task descriptor forwarded from :meth:`run`.

        Returns
        -------
        dict
            Must contain at least ``summary``, ``detail``, ``sources`` and
            ``confidence``.

        Notes
        -----
        The default implementation returns a placeholder result indicating
        that no execution