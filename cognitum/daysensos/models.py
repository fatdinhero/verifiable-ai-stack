"""DaySensOS — Pydantic Data Models."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ConsentState(BaseModel):
    """Per-Sensor Consent (Art. 4, PRIV-02/03). Kamera+Mikrofon default OFF."""
    camera: bool = False
    microphone: bool = False
    gps: bool = True
    accelerometer: bool = True
    light: bool = True
    bt_scan: bool = True
    screen_time: bool = True
    clock: bool = True


class SensorData(BaseModel):
    """L1 Input: 8-Kanal Sensordaten vom Smartphone."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    consent_state: ConsentState = Field(default_factory=ConsentState)
    # Kanal 1: Kamera (nur wenn consent_state.camera == True)
    camera_context: Optional[str] = None  # Redaktierter Kontext, KEIN Bild
    # Kanal 2: GPS
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    gps_accuracy: Optional[float] = None
    poi_context: Optional[str] = None  # z.B. "office", "park", "home"
    # Kanal 3: Accelerometer
    accel_x: Optional[float] = None
    accel_y: Optional[float] = None
    accel_z: Optional[float] = None
    # Kanal 4: Mikrofon (nur Frequenzspektrum, KEIN Rohaudio — Erkenntnis 2)
    freq_spectrum: Optional[list[float]] = None
    # Kanal 5: Lichtsensor
    light_lux: Optional[float] = None
    # Kanal 6: BT-Scan
    bt_devices: list[str] = Field(default_factory=list)  # Anonymisierte Hashes
    # Kanal 7: Bildschirmzeit
    screen_time_min: Optional[float] = None
    # Kanal 8: System-Uhr (implizit via timestamp)


class ContextID(str, Enum):
    """L2 Kontextkategorien."""
    DEEP_WORK = "deep_work"
    LIGHT_WORK = "light_work"
    MEETING = "meeting"
    COMMUTE = "commute"
    EXERCISE = "exercise"
    SOCIAL = "social"
    REST = "rest"
    SLEEP = "sleep"
    UNKNOWN = "unknown"


class SituationResult(BaseModel):
    """L2 Output: Kontextklassifikation."""
    context_id: ContextID = ContextID.UNKNOWN
    confidence: float = 0.0
    rule_matched: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Episode(BaseModel):
    """L3 Output: Temporale Episode."""
    id: Optional[int] = None
    context_id: ContextID
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_min: float = 0.0
    confidence_avg: float = 0.0


class DayFeatures(BaseModel):
    """L4 Output: Normalisierte Tagesmerkmale (14-Tage-Fenster, Erkenntnis 7)."""
    date: str  # YYYY-MM-DD
    focus: float = 0.0       # 0-10, relativ zu den letzten 14 Tagen
    energy: float = 0.0      # 0-10
    social: float = 0.0      # 0-10
    movement: float = 0.0    # 0-10
    episodes_count: int = 0
    total_tracked_min: float = 0.0


class WellnessState(str, Enum):
    """L5 Wellness-Zustand."""
    THRIVING = "thriving"
    BALANCED = "balanced"
    DRIFTING = "drifting"
    STRESSED = "stressed"
    RECOVERING = "recovering"


class DayScore(BaseModel):
    """L5 Output: Tagesbewertung."""
    date: str
    score: float = 0.0  # 0-10
    wellness: WellnessState = WellnessState.BALANCED
    features: DayFeatures
    recommendations: list[str] = Field(default_factory=list)


class CaptureResponse(BaseModel):
    """API Response fuer POST /capture."""
    focus_score: float = 0.0
    episode: str = "unknown"
    nudge: Optional[str] = None
    display_ttl_ms: int = 3000
