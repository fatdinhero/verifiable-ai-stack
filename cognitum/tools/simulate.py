"""DaySensOS — Sensor-Simulator.

Simuliert einen realistischen Tagesverlauf und sendet Sensordaten
an den DaySensOS Server auf :8111.

Tagesverlauf (Pforzheim, typischer Werktag):
  06:00-07:00  Schlaf → Aufwachen
  07:00-07:30  Morgenroutine (Rest)
  07:30-08:00  Commute (Pforzheim → Buero)
  08:00-10:00  Deep Work
  10:00-10:15  Pause (Rest)
  10:15-12:00  Deep Work
  12:00-13:00  Mittagspause (Social)
  13:00-14:00  Meeting
  14:00-16:00  Light Work
  16:00-16:30  Commute (Buero → Home)
  16:30-17:30  Exercise
  17:30-19:00  Social / Familie
  19:00-21:00  Rest / Abendprogramm
  21:00-22:00  Evening Coach Journaling
  22:00-06:00  Schlaf

Verwendung:
  # Echtzeit (1 Capture alle 30s):
  python tools/simulate.py

  # Schnelldurchlauf (ganzer Tag in ~2 Min):
  python tools/simulate.py --fast

  # Bestimmte Tageszeit simulieren:
  python tools/simulate.py --hour 14

  # Mehrere Tage fuer 14-Tage-Historie:
  python tools/simulate.py --days 14 --fast
"""
import argparse
import json
import math
import random
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

try:
    import httpx
    CLIENT = httpx
    USE_HTTPX = True
except ImportError:
    import urllib.request
    USE_HTTPX = False

# ─── Pforzheim Koordinaten ──────────────────────────────────
HOME = {"lat": 48.8922, "lon": 8.6946, "poi": "home"}
OFFICE = {"lat": 48.8855, "lon": 8.7050, "poi": "office"}
GYM = {"lat": 48.8900, "lon": 8.6980, "poi": "gym"}
PARK = {"lat": 48.8940, "lon": 8.7100, "poi": "park"}
CAFE = {"lat": 48.8870, "lon": 8.7020, "poi": "cafe"}

SERVER_URL = "http://localhost:8111"


# ─── Tagesverlauf-Szenarien ─────────────────────────────────

def get_scenario(hour: float) -> dict:
    """Gibt das Szenario fuer eine bestimmte Tageszeit zurueck.

    Jedes Szenario definiert typische Sensorwerte fuer den Kontext.
    Leichte Zufallsvariation sorgt fuer Realismus.
    """
    scenarios = [
        # (start_h, end_h, scenario_dict)
        (0, 6, {
            "name": "sleep",
            "location": HOME,
            "movement": (0.0, 0.2),        # fast keine Bewegung
            "light": (0, 5),                # dunkel
            "screen_time": 0,
            "bt_devices": (0, 1),           # nur eigenes Phone
            "noise_spectrum": [0.01, 0.02, 0.01],  # Stille
            "camera": False,
            "microphone": False,
        }),
        (6, 7, {
            "name": "waking_up",
            "location": HOME,
            "movement": (0.3, 1.0),
            "light": (20, 100),
            "screen_time": 5,
            "bt_devices": (1, 3),
            "noise_spectrum": [0.05, 0.1, 0.08],
            "camera": False,
            "microphone": False,
        }),
        (7, 7.5, {
            "name": "morning_routine",
            "location": HOME,
            "movement": (0.5, 1.5),
            "light": (100, 300),
            "screen_time": 10,
            "bt_devices": (1, 3),
            "noise_spectrum": [0.1, 0.2, 0.15],
            "camera": False,
            "microphone": False,
        }),
        (7.5, 8, {
            "name": "commute",
            "location": _interpolate_location(HOME, OFFICE),
            "movement": (1.5, 2.5),         # moderate Bewegung (Laufen/Bahn)
            "light": (200, 500),
            "screen_time": 3,
            "bt_devices": (5, 15),           # viele Geraete in Bahn/Bus
            "noise_spectrum": [0.3, 0.5, 0.4],
            "camera": False,
            "microphone": False,
        }),
        (8, 10, {
            "name": "deep_work_morning",
            "location": OFFICE,
            "movement": (0.1, 0.4),          # sitzt still
            "light": (300, 500),
            "screen_time": 55,               # fast nur Bildschirm
            "bt_devices": (1, 3),            # wenige Leute in der Naehe
            "noise_spectrum": [0.05, 0.08, 0.06],  # leise
            "camera": False,
            "microphone": False,
        }),
        (10, 10.25, {
            "name": "break",
            "location": OFFICE,
            "movement": (0.5, 1.5),
            "light": (300, 500),
            "screen_time": 5,
            "bt_devices": (2, 5),
            "noise_spectrum": [0.15, 0.25, 0.2],
            "camera": False,
            "microphone": False,
        }),
        (10.25, 12, {
            "name": "deep_work_late",
            "location": OFFICE,
            "movement": (0.1, 0.3),
            "light": (300, 500),
            "screen_time": 50,
            "bt_devices": (1, 3),
            "noise_spectrum": [0.05, 0.08, 0.06],
            "camera": False,
            "microphone": False,
        }),
        (12, 13, {
            "name": "lunch_social",
            "location": CAFE,
            "movement": (0.5, 1.5),
            "light": (400, 800),
            "screen_time": 10,
            "bt_devices": (5, 12),           # Kantine / Cafe
            "noise_spectrum": [0.3, 0.5, 0.45],
            "camera": False,
            "microphone": False,
        }),
        (13, 14, {
            "name": "meeting",
            "location": OFFICE,
            "movement": (0.1, 0.5),
            "light": (300, 500),
            "screen_time": 15,
            "bt_devices": (3, 8),            # Meeting-Teilnehmer
            "noise_spectrum": [0.2, 0.35, 0.3],
            "camera": False,
            "microphone": False,
        }),
        (14, 16, {
            "name": "light_work",
            "location": OFFICE,
            "movement": (0.2, 0.8),
            "light": (300, 500),
            "screen_time": 35,
            "bt_devices": (2, 5),
            "noise_spectrum": [0.1, 0.15, 0.12],
            "camera": False,
            "microphone": False,
        }),
        (16, 16.5, {
            "name": "commute_home",
            "location": _interpolate_location(OFFICE, HOME),
            "movement": (1.5, 2.5),
            "light": (200, 400),
            "screen_time": 5,
            "bt_devices": (5, 15),
            "noise_spectrum": [0.3, 0.5, 0.4],
            "camera": False,
            "microphone": False,
        }),
        (16.5, 17.5, {
            "name": "exercise",
            "location": random.choice([GYM, PARK]),
            "movement": (3.5, 6.0),          # hohe Bewegung
            "light": (400, 1000),
            "screen_time": 2,
            "bt_devices": (3, 10),
            "noise_spectrum": [0.2, 0.4, 0.35],
            "camera": False,
            "microphone": False,
        }),
        (17.5, 19, {
            "name": "social_evening",
            "location": HOME,
            "movement": (0.3, 1.0),
            "light": (200, 400),
            "screen_time": 15,
            "bt_devices": (2, 5),
            "noise_spectrum": [0.15, 0.3, 0.25],
            "camera": False,
            "microphone": False,
        }),
        (19, 21, {
            "name": "evening_rest",
            "location": HOME,
            "movement": (0.1, 0.5),
            "light": (50, 200),
            "screen_time": 25,
            "bt_devices": (1, 3),
            "noise_spectrum": [0.1, 0.15, 0.12],
            "camera": False,
            "microphone": False,
        }),
        (21, 22, {
            "name": "journaling",
            "location": HOME,
            "movement": (0.1, 0.3),
            "light": (30, 80),
            "screen_time": 15,
            "bt_devices": (1, 2),
            "noise_spectrum": [0.05, 0.08, 0.06],
            "camera": False,
            "microphone": False,
        }),
        (22, 24, {
            "name": "sleep_early",
            "location": HOME,
            "movement": (0.0, 0.2),
            "light": (0, 5),
            "screen_time": 0,
            "bt_devices": (0, 1),
            "noise_spectrum": [0.01, 0.02, 0.01],
            "camera": False,
            "microphone": False,
        }),
    ]

    for start, end, scenario in scenarios:
        if start <= hour < end:
            return scenario

    return scenarios[0][2]  # Fallback: Schlaf


def _interpolate_location(a: dict, b: dict) -> dict:
    """Erzeugt einen zufaelligen Punkt zwischen zwei Locations (Commute)."""
    t = random.uniform(0.2, 0.8)
    return {
        "lat": a["lat"] + t * (b["lat"] - a["lat"]) + random.gauss(0, 0.001),
        "lon": a["lon"] + t * (b["lon"] - a["lon"]) + random.gauss(0, 0.001),
        "poi": "commute",
    }


def generate_sensor_data(sim_time: datetime, scenario: dict) -> dict:
    """Generiert ein realistisches Sensor-Payload basierend auf dem Szenario."""
    loc = scenario["location"]
    mov = scenario["movement"]
    light = scenario["light"]
    bt = scenario["bt_devices"]

    # Accelerometer: Gravitation (9.81) + Bewegung
    movement_mag = random.uniform(*mov)
    angle = random.uniform(0, 2 * math.pi)
    accel_x = movement_mag * math.cos(angle) + random.gauss(0, 0.05)
    accel_y = movement_mag * math.sin(angle) + random.gauss(0, 0.05)
    accel_z = 9.81 + random.gauss(0, 0.1)

    # BT-Geraete: anonymisierte Hashes
    bt_count = random.randint(*bt)
    bt_devices = [f"dev_{random.randint(1000, 9999)}" for _ in range(bt_count)]

    payload = {
        "timestamp": sim_time.isoformat(),
        "consent_state": {
            "camera": scenario["camera"],
            "microphone": scenario["microphone"],
            "gps": True,
            "accelerometer": True,
            "light": True,
            "bt_scan": True,
            "screen_time": True,
            "clock": True,
        },
        "gps_lat": loc["lat"] + random.gauss(0, 0.0002),
        "gps_lon": loc["lon"] + random.gauss(0, 0.0002),
        "gps_accuracy": random.uniform(3, 15),
        "poi_context": loc["poi"],
        "accel_x": round(accel_x, 3),
        "accel_y": round(accel_y, 3),
        "accel_z": round(accel_z, 3),
        "light_lux": random.uniform(*light),
        "bt_devices": bt_devices,
        "screen_time_min": scenario["screen_time"] + random.uniform(-3, 3),
    }

    # Frequenzspektrum nur wenn Mikrofon consent (immer False im Simulator)
    if scenario["microphone"]:
        payload["freq_spectrum"] = [
            s + random.gauss(0, 0.02) for s in scenario["noise_spectrum"]
        ]

    return payload


def send_capture(payload: dict) -> Optional[dict]:
    """Sendet Sensordaten an POST /capture."""
    url = f"{SERVER_URL}/capture"
    body = json.dumps(payload).encode()

    try:
        if USE_HTTPX:
            resp = httpx.post(url, json=payload, timeout=5)
            return resp.json()
        else:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read())
    except Exception as e:
        print(f"  ✗ Server nicht erreichbar: {e}")
        return None


def simulate_day(base_date: datetime, fast: bool = False, interval_sec: int = 30):
    """Simuliert einen kompletten Tag."""
    print(f"\n{'='*60}")
    print(f"  DaySensOS Sensor-Simulator")
    print(f"  Datum: {base_date.strftime('%Y-%m-%d')}")
    print(f"  Modus: {'Schnelldurchlauf' if fast else 'Echtzeit (30s Intervall)'}")
    print(f"  Server: {SERVER_URL}")
    print(f"{'='*60}\n")

    # 24 Stunden in 30s-Schritten = 2880 Captures pro Tag
    # Im Fast-Modus: alle 5 Minuten = 288 Captures
    step_minutes = 5 if fast else 0.5
    captures = 0
    errors = 0

    current = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = current + timedelta(days=1)

    while current < end:
        hour = current.hour + current.minute / 60.0
        scenario = get_scenario(hour)
        payload = generate_sensor_data(current, scenario)

        result = send_capture(payload)

        if result:
            captures += 1
            episode = result.get("episode", "?")
            score = result.get("focus_score", 0)
            nudge = result.get("nudge", "")

            # Kompakte Ausgabe
            time_str = current.strftime("%H:%M")
            bar = "█" * int(score) + "░" * (10 - int(score))
            print(f"  {time_str}  {scenario['name']:20s}  → {episode:12s}  [{bar}] {score:.1f}  {nudge[:40] if nudge else ''}")
        else:
            errors += 1

        current += timedelta(minutes=step_minutes)

        if not fast:
            time.sleep(interval_sec)
        else:
            time.sleep(0.05)  # Minimaler Delay fuer Server

    return captures, errors


def main():
    parser = argparse.ArgumentParser(description="DaySensOS Sensor-Simulator")
    parser.add_argument("--fast", action="store_true", help="Schnelldurchlauf (ganzer Tag in ~2 Min)")
    parser.add_argument("--hour", type=float, help="Nur eine bestimmte Stunde simulieren")
    parser.add_argument("--days", type=int, default=1, help="Anzahl Tage simulieren (fuer 14-Tage-Historie)")
    parser.add_argument("--server", type=str, default="http://localhost:8111", help="Server-URL")
    args = parser.parse_args()

    global SERVER_URL
    SERVER_URL = args.server

    # Health-Check
    try:
        if USE_HTTPX:
            resp = httpx.get(f"{SERVER_URL}/status", timeout=3)
            status = resp.json()
        else:
            with urllib.request.urlopen(f"{SERVER_URL}/status", timeout=3) as resp:
                status = json.loads(resp.read())
        print(f"✓ Server erreichbar: DaySensOS v{status.get('version', '?')}")
    except Exception:
        print(f"✗ Server nicht erreichbar auf {SERVER_URL}")
        print(f"  Starte den Server mit: python -m daysensos.main")
        sys.exit(1)

    if args.hour is not None:
        # Einzelne Stunde simulieren
        now = datetime.utcnow().replace(hour=int(args.hour), minute=0)
        scenario = get_scenario(args.hour)
        payload = generate_sensor_data(now, scenario)
        result = send_capture(payload)
        print(f"\nSzenario: {scenario['name']}")
        print(f"Result: {json.dumps(result, indent=2)}")
        return

    total_captures = 0
    total_errors = 0

    for day_offset in range(args.days):
        base = datetime.utcnow() - timedelta(days=args.days - 1 - day_offset)
        captures, errors = simulate_day(base, fast=args.fast)
        total_captures += captures
        total_errors += errors

    print(f"\n{'='*60}")
    print(f"  Simulation abgeschlossen")
    print(f"  Tage: {args.days}")
    print(f"  Captures: {total_captures}")
    print(f"  Fehler: {total_errors}")
    print(f"{'='*60}")

    # Finaler Status
    try:
        if USE_HTTPX:
            resp = httpx.get(f"{SERVER_URL}/score", timeout=3)
            score = resp.json()
        else:
            with urllib.request.urlopen(f"{SERVER_URL}/score", timeout=3) as resp:
                score = json.loads(resp.read())
        print(f"\n  DayScore: {score.get('score', '?')}/10")
        print(f"  Wellness: {score.get('wellness', '?')}")
        print(f"  Features: {json.dumps(score.get('features', {}), indent=4)}")
        recs = score.get("recommendations", [])
        if recs:
            print(f"  Empfehlungen:")
            for r in recs:
                print(f"    → {r}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
