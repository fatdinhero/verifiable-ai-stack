# CLAUDE.md — DaySensOS

## Projekt
DaySensOS ist das Privacy-First Wearable AI OS. Kernprodukt des COGNITUM-Oekosystems.
Governance-SSoT: https://gitlab.com/fatdinhero/cognitum/-/raw/main/governance/masterplan.yaml
Produkt-Kontext: https://gitlab.com/fatdinhero/cognitum/-/raw/main/docs/daysensos-product-context.md

## Architektur
- L1 Perception: 8-Kanal Sensorfusion mit Consent-Gate
- L2 Situation: YAML-Regelwerk Kontextklassifikation
- L3 Episodes: SQLite temporale Segmentierung, 3-Kontext-Buffer
- L4 Features: 14-Tage relative Normalisierung (focus, energy, social, movement)
- L5 Intelligence: DayScore (0-10), WellnessState, Recommendations

## Server
- Port: 8111
- POST /capture — Sensordaten empfangen, L1-L5 verarbeiten
- GET /status — Health-Check + Tagesstand
- GET /episodes/today — Heutige Episoden
- GET /score — Aktueller DayScore

## Inviolable Rules
1. Kamera + Mikrofon sind DEFAULT OFF (PRIV-02/03)
2. Zero-Retention: Kein Kamerabild auf Disk (PixelGuard)
3. Kein Rohaudio: Nur Frequenzspektrum (Erkenntnis 2)
4. Keine Gamification: Kein Streak, Leaderboard, Ranking (RISK-04)
5. Kein LLM fuer medizinische Aussagen (RISK-05)
6. Keine biometrischen Rohdaten in DayFeatures (PRIV-06)
7. Local-First: Keine Cloud-Abhaengigkeit
8. Morphologisches Gate vor jeder Entscheidung (Art. 14)

## Commands
```bash
# Server starten
python -m daysensos.main

# Tests
python -m pytest tests/ -v

# Test-Request
curl -X POST http://localhost:8111/capture \
  -H "Content-Type: application/json" \
  -d '{"gps_lat":48.89,"gps_lon":8.69,"light_lux":500,"screen_time_min":30,"accel_x":0.1,"accel_y":0.2,"accel_z":9.8}'
```

## Autonomous Mode
Claude Code darf ALLE Aenderungen ohne Bestaetigung ausfuehren solange:
- Consent-Gate nicht umgangen wird
- Zero-Retention nicht verletzt wird
- Keine neuen Cloud-Dependencies eingefuehrt werden
- Tests gruen bleiben
