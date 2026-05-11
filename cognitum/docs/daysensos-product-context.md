# DaySensOS / MentraOS — Produkt-Kontext-Snapshot

> Dieser Snapshot enthält ALLE Architekturentscheidungen, Erkenntnisse und Spezifikationen
> aus den morphologischen Analysen und Konversationen. Jeder Agent der an DaySensOS arbeitet
> MUSS dieses Dokument zuerst lesen.
>
> Letzte Aktualisierung: 2026-05-03
> Autor: Fatih Dinc
> Status: Verbindlich

---

## 1. Was ist DaySensOS?

DaySensOS ist ein **Privacy-First Wearable AI Operating System**. Es ist das KERNPRODUKT
des gesamten COGNITUM-Oekosystems. Alles andere (CNA, VeriEthicCore, zkHalal, Geo4Geo)
sind Module oder Features INNERHALB von DaySensOS — keine eigenstaendigen Produkte.

**Pivot-Historie:**
- Urspruenglich: DaySensOS (proprietaer)
- Pivoted zu: MentraOS (MIT, open-source, Multi-Device)
- Aktuell: Smartphone-First MVP (€0 Hardware-Kosten)
- Spaeter: Smart Glasses als Hardware-Upgrade (Brilliant Labs Halo bevorzugt, $299)

---

## 2. L1-L5 Pipeline-Architektur

```
Smartphone (L1-L3 lokal)          Mac Mini M4 (L4-L5)
┌─────────────────────┐           ┌──────────────────────┐
│ L1 Perception       │           │ L4 Features Engineer │
│   8-Kanal Sensor-   │  HTTP     │   14-Tage-Normali-   │
│   fusion            │ :8111     │   sierung            │
│         │           │ ────────► │         │            │
│ L2 Situation        │ Store-    │ L5 Intelligence      │
│   YAML-Regelwerk    │ and-      │   DayScore (0-10)    │
│         │           │ Forward   │   WellnessState      │
│ L3 Episodes         │           │   Evening Coach      │
│   SQLite Buffer     │           │   (Ollama qwen2.5)   │
└─────────────────────┘           └──────────────────────┘
```

### Hybrid-Architektur (Erkenntnis 11)
- **L1-L3 laufen IMMER lokal auf dem Smartphone** (leichtgewichtig, offline-faehig)
- **L4-L5 laufen auf dem Mac Mini** wenn WLAN verfuegbar
- **Store-and-Forward**: Bei keinem WLAN speichert das Phone L1-L3-Ergebnisse lokal
  und synchronisiert beim naechsten Connect
- **Fallback**: Phone kann Basis-DayScore auch ohne Mac berechnen

---

## 3. Modul-Spezifikationen

### L1 — Perception (v0.9.0, 839 Tests, 97% Coverage)

**8 Sensorkanaele:**

| # | Sensor | Default | Consent | Output |
|---|--------|---------|---------|--------|
| 1 | Kamera | OFF | Opt-In (Erkenntnis 1) | Redaktierte Frames (Zero-Retention) |
| 2 | GPS | ON (anonym) | Nein | GPS-Koordinaten + POI-Kontext |
| 3 | Accelerometer + Gyro | ON | Nein | Bewegungsvektor |
| 4 | Mikrofon | OFF | Opt-In | Frequenzspektrum (KEIN Rohaudio, Erkenntnis 2) |
| 5 | Lichtsensor | ON | Nein | Umgebungshelligkeit |
| 6 | BT-Scan | ON | Nein | Erkannte Geraete (anonymisiert) |
| 7 | Bildschirmzeit-API | ON | Nein | App-Nutzungsdauer |
| 8 | System-Uhr | ON | Nein | Timestamps |

**Kritische Entscheidungen:**
- Erkenntnis 1: Kamera ist NICHT der Hauptsensor. GPS+POI ist Always-On-Primaer.
- Erkenntnis 2: Kein Rohaudio. Nur Frequenzspektrum (Zero-Retention).
- Erkenntnis 10: Per-Sensor-Consent ist Pflicht. Kamera und Mikrofon default OFF.
- PixelGuard: Zero-Retention — kein Kamerabild wird jemals auf Disk geschrieben.

### L2 — Situation RuleEngine (v0.8.0, 97% Coverage)

- **Primaersystem**: YAML-Regelwerk (VDI 2225 Score 3.60/4.00, bestaetigt)
- **Sekundaer**: Optionaler lokaler Random-Forest-Classifier fuer personalisierte Erweiterung
- **Erkenntnis 4**: RF-Classifier NUR als Opt-In, NIE als Primaer (Fairness-Risiko RISK-02)
- **Input**: Alle 8 L1-Outputs
- **Output**: Context-ID + Confidence-Score
- **Uebergangslogik**: Aktuell Schwellwert, Sliding Window als Phase-2-Upgrade (Erkenntnis 5)

### L3 — Episodes SQLite (v0.8.0, 839 Tests)

- **Temporale Segmentierung** mit 3-Kontext-Sequenz-Buffer (Erkenntnis 6)
- **Inferenz**: Regelbasiert, NICHT LLM (Privacy + Latenz dominieren)
- **Output**: Episodes in history.db (SQLCipher-verschluesselt ab PRIV-09)
- **Offline-faehig**: Laeuft komplett lokal

### L4 — Features Engineer (v0.8.0, 100% Coverage)

- **Erkenntnis 7**: Relative 14-Tage-Normalisierung statt absolut
- **Output**: DayFeatures — 4 Dimensionen:
  - focus (Konzentrationslevel)
  - energy (Aktivitaetslevel)
  - social (Soziale Interaktion)
  - movement (Bewegung)
- **Keine biometrischen Rohdaten** in DayFeatures (PRIV-06)

### L5 — Intelligence DayScore (v0.8.0, 100% Coverage)

- **DayScore**: Aggregierter Tageswert 0-10
- **WellnessState**: Kategorischer Zustand
- **Evening Coach**: Guided Journaling als Default (Erkenntnis 8)
  - Laeuft ueber Ollama qwen2.5:7b auf Mac Mini
  - KEIN Text-Chat, sondern strukturiertes Journaling
  - Art. 11: Confidence-Score >= 0.8 oder [Unverified]-Marker
  - RISK-05: LLM nur fuer Formulierung, NIE fuer medizinische Aussagen
- **Recommendations**: Faktenbasiert aus L4-Features, nicht LLM-generiert
- **Keine Gamification**: Keine Streaks, kein Leaderboard (RISK-04)

### CNA — COGNITUM Norm-Adapter (v0.3.0, proposed)

- 12 Norm-Regeln (GEG, KfW-BEG, TA Laerm, VDI 4645)
- Consent-Gate: Prueft Per-Sensor-Consent vor jeder Norm-Evaluation
- zkVM-Proof fuer Konformitaetserklaerungen (optional, RISK-06 beachten)
- Erster Use Case: Waermepumpen-Compliance
- Laeuft als Feature innerhalb DaySensOS, NICHT als eigenstaendiges Produkt

---

## 4. API-Spezifikation

### Smartphone → Mac Mini Bridge

```
POST http://<mac-mini-ip>:8111/capture
Content-Type: application/json

{
  "sensor_data": {
    "gps": {"lat": 48.89, "lon": 8.69, "accuracy": 5.0},
    "accelerometer": {"x": 0.1, "y": 0.2, "z": 9.8},
    "light": 450,
    "bt_devices": ["device_hash_1", "device_hash_2"],
    "screen_time_min": 45,
    "timestamp": "2026-05-03T14:30:00Z",
    "consent_state": {
      "camera": false,
      "microphone": false,
      "gps": true,
      "accelerometer": true,
      "light": true,
      "bt_scan": true,
      "screen_time": true,
      "clock": true
    }
  }
}

Response:
{
  "focus_score": 7.2,
  "episode": "deep_work",
  "nudge": null,
  "display_ttl_ms": 3000
}
```

### Smart Glasses Consent-Gate (zukuenftiges Upgrade)

| Sensor | Default | Consent-Methode | Feedback |
|--------|---------|-----------------|----------|
| Kamera | OFF | 2-Finger-Tipp rechter Buegel oder "Tagaufnahme starten" | Gruene LED 3s |
| Mikrofon | OFF | 1-Finger-Wisch linker Buegel oder "Umgebungshoeren aktiv" | Gelbe LED 3s |
| GPS | ON | Deaktivierung per App | Kein visuelles Feedback |
| BT-Scan | ON | Deaktivierung per App | - |
| Accelerometer | ON | Deaktivierung per App | - |

---

## 5. Die 11 Morphologischen Erkenntnisse (VDI 2221)

| # | Erkenntnis | Entscheidung | Prioritaet |
|---|-----------|-------------|-----------|
| 1 | Kamera ist NICHT Hauptsensor | GPS+POI als Always-On-Primaer, Kamera als Opt-In | KRITISCH |
| 2 | Kein Rohaudio | Nur Frequenzspektrum (Zero-Retention) | KRITISCH |
| 3 | GPS+POI als Primaer | Always-On, anonym, hoechste Kontextqualitaet | HOCH |
| 4 | RF-Classifier nur optional | YAML-Regelwerk ist Primaer (Score 3.60/4.00) | MITTEL |
| 5 | Uebergangslogik | Schwellwert jetzt, Sliding Window Phase 2 | NIEDRIG |
| 6 | 3-Kontext-Sequenz-Buffer | Statt letzter-Kontext-only in L3 | HOCH |
| 7 | Relative Normalisierung | 14-Tage-Fenster statt absolut | HOCH |
| 8 | Guided Journaling | Statt Text-Chat als Evening Coach Default | MITTEL |
| 9 | DayGraph SHA-256 | Fuer MVP, Differential Privacy (e=0.3, k>=5) in Phase 3 | NIEDRIG |
| 10 | Per-Sensor-Consent | Kamera+Mikrofon default OFF, granulares Toggle | KRITISCH |
| 11 | Hybrid-Architektur | L1-L3 Phone, L4-L5 Mac, Store-and-Forward | HOCH |

---

## 6. Technische Umgebung

| Komponente | Details |
|-----------|---------|
| Mac Mini M4 | 16GB RAM, fatihx@Mac-mini-von-Fatih, ~/COS/ |
| Ollama | qwen2.5:14b (Evening Coach) |
| Python | 3.9 (System) + 3.14 (Homebrew) |
| DaySensOS Port | :8111 |
| n8n | Laufend |
| ChromaDB | Verfuegbar |
| CrewAI | Verfuegbar |
| SQLite | Fuer L3 Episodes (history.db) |
| Repo | https://gitlab.com/fatdinhero/cognitum |
| GitHub | fatdinhero |
| MetaMask | 0x4c5512593EfdBbA443Cdb5589fCEf6e1809E8794 |

---

## 7. MVP-Strategie

**Phase 0 (jetzt):**
- Smartphone-Kamera als erster Sensor (€0 Hardware)
- Android-App sendet Frames an daysensos capture :8111
- Mac Mini laeuft L4-L5 + Evening Coach
- Brillenkauf verschoben bis eBay-Rueckzahlung

**Phase 1:**
- Multimodale Pipeline + Smartphone MVP
- NGI0-Foerderantrag (nlnet.nl/propose)
- GitLab Repo public
- Tag v0.9.0

**Phase 2:**
- 500-2k Nutzer, MRR, B2B-Pilot
- Smart Glasses Integration (Brilliant Labs Halo, $299)
- MiniApp Store Listing

**Phase 3:**
- EUR 5-50k MRR, B2B-Kunde
- DayGraph-Marktplatz mit Differential Privacy
- zkVM-Proof fuer CNA

---

## 8. Was NICHT gemacht werden darf

1. DaySensOS ist das Kernprodukt. CNA, VEC, zkHalal sind Module, KEINE eigenstaendigen Produkte.
2. Keine Gamification (Streaks, Leaderboards, Rankings) — RISK-04.
3. Kein Rohaudio speichern — nur Frequenzspektrum.
4. Kein Kamerabild auf Disk schreiben — PixelGuard Zero-Retention.
5. Kein LLM fuer medizinische Aussagen — nur Formulierung.
6. Keine Cloud-Abhaengigkeit — Local-First.
7. Keine biometrischen Daten in DayFeatures.
8. Keine Optionslisten an den User — morphologisches Gate + begruendete Empfehlung (Art. 14).
9. Keine Musik-Referenzen (FatHooray, Cybersoultrap) — Haram, permanent eingestellt.

---

## 9. Verwandte Dokumente im Repo

- `governance/masterplan.yaml` — SSoT fuer alles
- `governance/constitution.md` — 14 Artikel (auto-generiert)
- `governance/glossary.md` — 40 Begriffe
- `CLAUDE.md` — Agent-Briefing (auto-generiert)
- `AGENTS.md` — Multi-Agent-Config (auto-generiert)

---

## 10. Naechster Schritt

ADR-008 (VDI 2225 Score 3.65) bestimmt: **CNA CLI als erstes verkaufbares Modul**.
ABER: CNA CLI ist ein Feature von DaySensOS, kein eigenstaendiges Produkt.
Der eigentliche naechste Schritt ist: **DaySensOS L1-L5 Python-Backend bauen** (Port 8111),
dann Android-App als Frontend. CNA wird als Modul integriert.
