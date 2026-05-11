"""DaySensOS — FastAPI Server auf Port 8111.

Empfaengt Sensordaten vom Smartphone, verarbeitet L1-L5 Pipeline,
gibt CaptureResponse zurueck.

Hybrid-Architektur (Erkenntnis 11):
  - L1-L3 koennen auch auf dem Phone laufen (leichtgewichtig)
  - L4-L5 laufen hier auf dem Mac Mini (LLM-intensiv)
  - Store-and-Forward: Phone speichert lokal wenn offline
"""
import uvicorn
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import SensorData, CaptureResponse, DayFeatures
from .l1_perception import process_l1
from .l2_situation import classify_context
from .l3_episodes import EpisodeTracker
from .l4_features import compute_day_features
from .l5_intelligence import compute_day_score

app = FastAPI(
    title="DaySensOS",
    description="Privacy-First Wearable AI OS — L1-L5 Pipeline",
    version="0.9.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton EpisodeTracker (haelt 3-Kontext-Buffer im RAM)
tracker = EpisodeTracker()


@app.post("/capture", response_model=CaptureResponse)
async def capture(data: SensorData) -> CaptureResponse:
    """Hauptendpoint: Empfaengt Sensordaten, verarbeitet L1-L5, gibt Score zurueck.

    PixelGuard: Kein Kamerabild wird gespeichert. Nur der Kontext-String
    (z.B. "office", "park") passiert das System. Zero-Retention.
    """
    # L1: Perception — Consent-Gate + Sensorfusion
    signals = process_l1(data)

    # L2: Situation — YAML-Regelwerk Kontextklassifikation
    situation = classify_context(signals)

    # L3: Episodes — Temporale Segmentierung (3-Kontext-Buffer)
    episode = tracker.process(situation)

    # L4: Features — 14-Tage-Normalisierung (nur bei genuegend Daten)
    today_episodes = tracker.get_today_episodes()
    features = compute_day_features(today_episodes)

    # L5: Intelligence — DayScore + WellnessState
    day_score = compute_day_score(features)

    return CaptureResponse(
        focus_score=round(features.focus, 1),
        episode=episode.context_id.value,
        nudge=day_score.recommendations[0] if day_score.recommendations else None,
        display_ttl_ms=3000,
    )


@app.get("/status")
async def status():
    """Health-Check und aktueller Tagesstand."""
    today_episodes = tracker.get_today_episodes()
    features = compute_day_features(today_episodes)
    day_score = compute_day_score(features)

    return {
        "status": "running",
        "version": "0.9.0",
        "today": {
            "episodes": len(today_episodes),
            "tracked_min": round(features.total_tracked_min, 1),
            "score": day_score.score,
            "wellness": day_score.wellness.value,
            "features": {
                "focus": features.focus,
                "energy": features.energy,
                "social": features.social,
                "movement": features.movement,
            },
        },
        "recommendations": day_score.recommendations,
    }


@app.get("/episodes/today")
async def episodes_today():
    """Alle Episoden des heutigen Tages."""
    episodes = tracker.get_today_episodes()
    return [
        {
            "context": ep.context_id.value,
            "start": ep.start_time.isoformat(),
            "end": ep.end_time.isoformat() if ep.end_time else None,
            "duration_min": round(ep.duration_min, 1),
            "confidence": round(ep.confidence_avg, 2),
        }
        for ep in episodes
    ]


@app.get("/score")
async def score():
    """Aktueller DayScore mit Features und Empfehlungen."""
    today_episodes = tracker.get_today_episodes()
    features = compute_day_features(today_episodes)
    day_score = compute_day_score(features)
    return day_score.model_dump()


def main():
    """Startet den DaySensOS Server auf Port 8111."""
    uvicorn.run(
        "daysensos.main:app",
        host="0.0.0.0",
        port=8111,
        reload=True,
    )


if __name__ == "__main__":
    main()
