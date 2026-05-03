"""DaySensOS — L1 Perception: 8-Kanal Multimodale Sensorfusion.

Erkenntnis 1: GPS+POI ist Always-On-Primaer, Kamera ist Opt-In.
Erkenntnis 2: Kein Rohaudio — nur Frequenzspektrum.
Erkenntnis 10: Per-Sensor-Consent, Kamera+Mikrofon default OFF.
PixelGuard: Zero-Retention — kein Kamerabild wird auf Disk geschrieben.
"""
import math
from .models import SensorData, ConsentState
from .consent import apply_consent_gate


def compute_movement_magnitude(data: SensorData) -> float:
    """Berechnet Bewegungsstaerke aus Accelerometer-Daten."""
    if data.accel_x is None:
        return 0.0
    magnitude = math.sqrt(
        (data.accel_x or 0) ** 2 +
        (data.accel_y or 0) ** 2 +
        (data.accel_z or 0) ** 2
    )
    # Subtrahiere Gravitation (~9.81), Rest ist Bewegung
    return max(0.0, magnitude - 9.81)


def compute_ambient_noise_db(data: SensorData) -> float:
    """Schaetzt Umgebungslautstaerke aus Frequenzspektrum (falls consent)."""
    if not data.freq_spectrum:
        return 0.0
    # RMS des Spektrums als Proxy fuer dB
    rms = math.sqrt(sum(f ** 2 for f in data.freq_spectrum) / len(data.freq_spectrum))
    return min(120.0, max(0.0, 20 * math.log10(rms + 1e-10) + 60))


def compute_social_proximity(data: SensorData) -> int:
    """Zaehlt BT-Geraete als Social-Proximity-Signal."""
    return len(data.bt_devices)


def process_l1(raw_data: SensorData) -> dict:
    """Verarbeitet Rohdaten durch das Consent-Gate und fusioniert alle Kanaele.

    Returns:
        dict mit fusionierten Sensorsignalen fuer L2.
    """
    # Consent-Gate: Nullt nicht-konsentierte Sensoren
    data = apply_consent_gate(raw_data)

    return {
        "timestamp": data.timestamp.isoformat(),
        "consent_state": data.consent_state.model_dump(),
        # GPS + POI (Primaersensor, Erkenntnis 1/3)
        "gps_lat": data.gps_lat,
        "gps_lon": data.gps_lon,
        "poi_context": data.poi_context,
        # Bewegung
        "movement_magnitude": compute_movement_magnitude(data),
        # Audio (nur Frequenzspektrum, Erkenntnis 2)
        "ambient_noise_db": compute_ambient_noise_db(data),
        # Licht
        "light_lux": data.light_lux,
        # Social Proximity
        "bt_device_count": compute_social_proximity(data),
        # Bildschirmzeit
        "screen_time_min": data.screen_time_min,
        # Kamera-Kontext (nur wenn consent)
        "camera_context": data.camera_context,
    }
