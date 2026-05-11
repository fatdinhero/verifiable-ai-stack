"""DaySensOS — L5 Intelligence: DayScore, WellnessState, Evening Coach.

RISK-04: Keine Gamification (Streaks, Leaderboard, Rankings).
RISK-05: LLM nur fuer Formulierung, nicht fuer medizinische Aussagen.
Art. 11: Confidence-Score >= 0.8 oder [Unverified]-Marker.
Erkenntnis 8: Guided Journaling als Default (nicht Text-Chat).
"""
from .models import DayFeatures, DayScore, WellnessState


def compute_day_score(features: DayFeatures) -> DayScore:
    """Berechnet den DayScore (0-10) aus den normalisierten Features.

    Gewichtung:
      focus:    35% (Hauptindikator fuer Produktivitaet)
      energy:   25% (Aktivitaetslevel)
      social:   20% (Soziale Gesundheit)
      movement: 20% (Koerperliche Aktivitaet)

    Keine Gamification (RISK-04):
      - Kein Streak-Counter
      - Kein Leaderboard
      - Kein "Highscore"
      - Score ist ein Reflexionswerkzeug, kein Wettbewerb
    """
    score = (
        features.focus * 0.35 +
        features.energy * 0.25 +
        features.social * 0.20 +
        features.movement * 0.20
    )
    score = min(10.0, max(0.0, round(score, 1)))

    wellness = _classify_wellness(features, score)
    recommendations = _generate_recommendations(features, wellness)

    return DayScore(
        date=features.date,
        score=score,
        wellness=wellness,
        features=features,
        recommendations=recommendations,
    )


def _classify_wellness(features: DayFeatures, score: float) -> WellnessState:
    """Klassifiziert den WellnessState basierend auf Features."""
    if score >= 7.0 and features.social >= 4.0 and features.movement >= 3.0:
        return WellnessState.THRIVING
    elif score >= 5.5:
        return WellnessState.BALANCED
    elif features.focus >= 6.0 and features.social < 2.0:
        return WellnessState.STRESSED
    elif features.energy < 3.0:
        return WellnessState.RECOVERING
    else:
        return WellnessState.DRIFTING


def _generate_recommendations(features: DayFeatures, wellness: WellnessState) -> list[str]:
    """Generiert faktenbasierte Empfehlungen aus L4-Features.

    RISK-05: Keine medizinischen Aussagen. Nur Beobachtungen und Vorschlaege.
    Alle Empfehlungen sind faktenbasiert aus den Features, NICHT LLM-generiert.
    """
    recs = []

    if features.movement < 3.0:
        recs.append("Dein Bewegungslevel war heute niedrig. Ein kurzer Spaziergang koennte helfen.")

    if features.social < 2.0 and features.focus > 6.0:
        recs.append("Hoher Fokus bei wenig sozialer Interaktion. Plane morgen bewusst Zeit fuer Gespraeche ein.")

    if features.focus < 3.0 and features.total_tracked_min > 120:
        recs.append("Wenig Fokus trotz langer Bildschirmzeit. Vielleicht helfen kuerzere, intensivere Arbeitsbloecke.")

    if features.energy < 3.0:
        recs.append("Dein Energielevel war niedrig. Achte auf ausreichend Schlaf und Pausen.")

    if wellness == WellnessState.THRIVING:
        recs.append("Guter Tag — Fokus, Bewegung und soziale Balance stimmen.")

    if not recs:
        recs.append("Ausgeglichener Tag. Weiter so.")

    return recs
