"""DaySensOS — L4 Features Engineer: 14-Tage-Normalisierung.

Erkenntnis 7: Relative Normalisierung statt absolut.
PRIV-06: Keine biometrischen Rohdaten in DayFeatures.
Output: focus, energy, social, movement (jeweils 0-10).
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from .models import ContextID, DayFeatures, Episode

DB_PATH = Path.home() / "COS" / "daysensos" / "history.db"

# Kontexte die zu den 4 Feature-Dimensionen beitragen
FOCUS_CONTEXTS = {ContextID.DEEP_WORK, ContextID.LIGHT_WORK}
ENERGY_CONTEXTS = {ContextID.EXERCISE, ContextID.COMMUTE}
SOCIAL_CONTEXTS = {ContextID.SOCIAL, ContextID.MEETING}
MOVEMENT_CONTEXTS = {ContextID.EXERCISE, ContextID.COMMUTE}


def _get_episodes_range(days_back: int = 14) -> list[dict]:
    """Holt alle Episoden der letzten N Tage aus SQLite."""
    db_path = DB_PATH
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
    rows = conn.execute(
        "SELECT context_id, duration_min, start_time FROM episodes WHERE start_time > ?",
        (cutoff,),
    ).fetchall()
    conn.close()

    return [
        {"context_id": r[0], "duration_min": r[1], "date": r[2][:10]}
        for r in rows
    ]


def _compute_dimension_minutes(episodes: list[dict], contexts: set[ContextID]) -> float:
    """Summiert Minuten fuer einen bestimmten Kontext-Set."""
    context_values = {c.value for c in contexts}
    return sum(
        ep["duration_min"]
        for ep in episodes
        if ep["context_id"] in context_values
    )


def _normalize_relative(value: float, history_values: list[float]) -> float:
    """Normalisiert einen Wert relativ zum 14-Tage-Fenster (0-10).

    Erkenntnis 7: Nicht absolut, sondern relativ zu den eigenen Werten.
    """
    if not history_values:
        if value == 0:
            return 5.0  # Kein Verlauf, kein Wert — Mittelwert
        return 5.0

    max_val = max(history_values) if history_values else 1.0
    if max_val == 0:
        if value == 0:
            return 5.0
        return 5.0

    normalized = (value / max_val) * 10.0
    return min(10.0, max(0.0, normalized))


def compute_day_features(today_episodes: list[Episode]) -> DayFeatures:
    """Berechnet DayFeatures aus den heutigen Episoden mit 14-Tage-Normalisierung.

    Returns:
        DayFeatures mit normalisierten Werten (0-10) fuer focus, energy, social, movement.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Heutige Rohwerte
    today_dicts = [
        {"context_id": ep.context_id.value, "duration_min": ep.duration_min, "date": today}
        for ep in today_episodes
    ]
    focus_today = _compute_dimension_minutes(today_dicts, FOCUS_CONTEXTS)
    energy_today = _compute_dimension_minutes(today_dicts, ENERGY_CONTEXTS)
    social_today = _compute_dimension_minutes(today_dicts, SOCIAL_CONTEXTS)
    movement_today = _compute_dimension_minutes(today_dicts, MOVEMENT_CONTEXTS)

    # 14-Tage-Historie fuer Normalisierung
    history = _get_episodes_range(14)
    dates = sorted(set(ep["date"] for ep in history))

    focus_history = [_compute_dimension_minutes([e for e in history if e["date"] == d], FOCUS_CONTEXTS) for d in dates]
    energy_history = [_compute_dimension_minutes([e for e in history if e["date"] == d], ENERGY_CONTEXTS) for d in dates]
    social_history = [_compute_dimension_minutes([e for e in history if e["date"] == d], SOCIAL_CONTEXTS) for d in dates]
    movement_history = [_compute_dimension_minutes([e for e in history if e["date"] == d], MOVEMENT_CONTEXTS) for d in dates]

    total_min = sum(ep.duration_min for ep in today_episodes)

    return DayFeatures(
        date=today,
        focus=_normalize_relative(focus_today, focus_history),
        energy=_normalize_relative(energy_today, energy_history),
        social=_normalize_relative(social_today, social_history),
        movement=_normalize_relative(movement_today, movement_history),
        episodes_count=len(today_episodes),
        total_tracked_min=total_min,
    )
