"""DaySensOS — Per-Sensor Consent Gate (Art. 4, PRIV-02/03).

Filtert Sensordaten basierend auf dem Consent-State.
Kamera und Mikrofon sind default OFF.
Kein Sensor-Datenpunkt passiert das Gate ohne expliziten Consent.
"""
from .models import SensorData, ConsentState


def apply_consent_gate(data: SensorData) -> SensorData:
    """Nullt alle Sensorfelder fuer die kein Consent vorliegt."""
    c = data.consent_state

    if not c.camera:
        data.camera_context = None

    if not c.gps:
        data.gps_lat = None
        data.gps_lon = None
        data.gps_accuracy = None
        data.poi_context = None

    if not c.accelerometer:
        data.accel_x = None
        data.accel_y = None
        data.accel_z = None

    if not c.microphone:
        data.freq_spectrum = None

    if not c.light:
        data.light_lux = None

    if not c.bt_scan:
        data.bt_devices = []

    if not c.screen_time:
        data.screen_time_min = None

    return data
