"""DaySensOS — L3 Episodes: SQLite Temporale Segmentierung.

Erkenntnis 6: 3-Kontext-Sequenz-Buffer statt letzter-Kontext-only.
Regelbasiert, NICHT LLM (Privacy + Latenz dominieren).
PRIV-09: SQLCipher-Verschluesselung in Produktion (hier SQLite fuer MVP).
"""
import sqlite3
from collections import deque
from datetime import datetime
from pathlib import Path
from .models import ContextID, SituationResult, Episode

DB_PATH = Path.home() / "COS" / "daysensos" / "history.db"


def _get_db() -> sqlite3.Connection:
    """Erstellt/oeffnet die SQLite-Datenbank."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context_id TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_min REAL DEFAULT 0,
            confidence_avg REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


class EpisodeTracker:
    """Verwaltet Episoden mit 3-Kontext-Sequenz-Buffer (Erkenntnis 6).

    Ein Kontextwechsel wird erst bestaetigt wenn 3 aufeinanderfolgende
    Klassifikationen den gleichen neuen Kontext melden.
    """

    def __init__(self):
        self.buffer: deque[SituationResult] = deque(maxlen=3)
        self.current_episode: Episode | None = None
        self.db = _get_db()

    def process(self, situation: SituationResult) -> Episode:
        """Verarbeitet eine neue Kontextklassifikation.

        Returns:
            Die aktuelle (ggf. neue) Episode.
        """
        self.buffer.append(situation)

        # Pruefe ob alle 3 Buffer-Eintraege den gleichen Kontext haben
        if len(self.buffer) == 3:
            contexts = [s.context_id for s in self.buffer]
            buffer_unanimous = len(set(contexts)) == 1
            new_context = contexts[0]
        else:
            buffer_unanimous = False
            new_context = situation.context_id

        # Kein aktuelles Episode — starte eins
        if self.current_episode is None:
            self.current_episode = Episode(
                context_id=situation.context_id,
                start_time=situation.timestamp,
                confidence_avg=situation.confidence,
            )
            return self.current_episode

        # Gleicher Kontext — Episode laeuft weiter
        if new_context == self.current_episode.context_id:
            self._update_duration(situation.timestamp)
            # Laufender Durchschnitt der Confidence
            n = max(1, self.current_episode.episodes_count if hasattr(self.current_episode, 'episodes_count') else 1)
            self.current_episode.confidence_avg = (
                self.current_episode.confidence_avg * (n - 1) + situation.confidence
            ) / n
            return self.current_episode

        # Kontextwechsel — nur wenn Buffer einstimmig (Erkenntnis 6)
        if buffer_unanimous and new_context != self.current_episode.context_id:
            self._close_episode(situation.timestamp)
            self.current_episode = Episode(
                context_id=new_context,
                start_time=situation.timestamp,
                confidence_avg=situation.confidence,
            )

        return self.current_episode

    def _update_duration(self, now: datetime):
        """Aktualisiert die Dauer der aktuellen Episode."""
        if self.current_episode and self.current_episode.start_time:
            delta = (now - self.current_episode.start_time).total_seconds()
            self.current_episode.duration_min = delta / 60.0

    def _close_episode(self, end_time: datetime):
        """Schliesst die aktuelle Episode und speichert sie in SQLite."""
        if not self.current_episode:
            return

        self._update_duration(end_time)
        self.current_episode.end_time = end_time

        self.db.execute(
            """INSERT INTO episodes (context_id, start_time, end_time, duration_min, confidence_avg)
               VALUES (?, ?, ?, ?, ?)""",
            (
                self.current_episode.context_id.value,
                self.current_episode.start_time.isoformat(),
                end_time.isoformat(),
                self.current_episode.duration_min,
                self.current_episode.confidence_avg,
            ),
        )
        self.db.commit()

    def get_today_episodes(self) -> list[Episode]:
        """Holt alle Episoden des heutigen Tages."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        rows = self.db.execute(
            "SELECT id, context_id, start_time, end_time, duration_min, confidence_avg "
            "FROM episodes WHERE start_time LIKE ?",
            (f"{today}%",),
        ).fetchall()

        return [
            Episode(
                id=r[0],
                context_id=ContextID(r[1]),
                start_time=datetime.fromisoformat(r[2]),
                end_time=datetime.fromisoformat(r[3]) if r[3] else None,
                duration_min=r[4],
                confidence_avg=r[5],
            )
            for r in rows
        ]
