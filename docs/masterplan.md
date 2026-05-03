# COGNITUM Masterplan v1.3.0

**Generated:** 2026-05-03T18:00:00Z
**Author:** Fatih Dinc
**Organization:** datalabel.tech
**Repository:** https://gitlab.com/fatdinhero/cognitum
**Constitution:** constitution.md
**Glossary:** glossary.md

---

## ADRs
### ADR-2026-05-03-001: Annahme des DaySensOS-Konstruktionsprotokolls
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** Verbindlicher Entwicklungsstandard nach VDI 2221/2222/2225
- **Decision:** Protokoll als systemischer Gate-Mechanismus uebernommen
- **Consequences:** Jede Implementierungsentscheidung durchlaeuft morphologisches Gate
- **Links:** | downstream → ADR-2026-05-03-003
### ADR-2026-05-03-002: G2G Cert AI als externer Compliance-Pruefservice
- **Status:** deprecated
- **Date:** 2026-05-03
- **Context:** Evaluierung der G2G-Integration
- **Decision:** Externer Pruefservice per API
- **Consequences:** Wurde durch ADR-003 revidiert
- **Superseded by:** ADR-2026-05-03-003
- **Links:** upstream → ADR-2026-05-03-001 | downstream → ADR-2026-05-03-003
### ADR-2026-05-03-003: Make-or-Buy COGNITUM Norm-Adapter statt G2G Cert AI
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** G2G verletzt Zero-Retention. COGNITUM baut eigenen Norm-Adapter.
- **Decision:** Eigenentwicklung CNA, YAML-Regelwerk plus zkVM-Proof
- **Consequences:** CNA wird als MCP-Server integriert.
- **Links:** upstream → ADR-2026-05-03-002 | downstream → ADR-2026-05-03-004
### ADR-2026-05-03-004: CNA v0.1 COGNITUM Norm-Adapter Architektur
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** Erster Bauplan fuer den Norm-Adapter
- **Decision:** MCP-Server, YAML-Regeln, zkVM-Proof
- **Consequences:** Erste Anwendung GEG/KfW fuer Waermepumpen
- **Links:** upstream → ADR-2026-05-03-003 | downstream → ADR-2026-05-03-005
### ADR-2026-05-03-005: CNA v0.2 Integration der Morphologischen Systemanalyse
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** Multimodale Bedingungen, Consent-Gate, Offline-Faehigkeit
- **Decision:** Regeln referenzieren Sensorkanaele. Per-Sensor-Consent respektiert.
- **Consequences:** CNA wird nativer COGNITUM-Buerger
- **Links:** upstream → ADR-2026-05-03-004 | downstream → ADR-2026-05-03-006
### ADR-2026-05-03-006: Lebendiger Masterplan YAML-SSoT-System
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** Architektur-Report bestaetigt YAML-zentrische Single Source of Truth
- **Decision:** masterplan.yaml als SSoT, Pydantic plus Yamale, Jinja2, Pandoc, GitLab-CI
- **Consequences:** Phase 7 Implementierung abgeschlossen.
- **Links:** upstream → ADR-2026-05-03-005 | downstream → ADR-2026-05-03-007
### ADR-2026-05-03-007: Tool-Auswahl fuer das Masterplan-SSoT-System
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** Phase 4 VDI 2221 morphologische Bewertung aller Tools
- **Decision:** Jinja2, Pandoc, Pydantic plus Yamale, git-cliff, pytest plus networkx
- **Consequences:** Alle Tools offline-first, Python-nativ, CI-freundlich.
- **Links:** upstream → ADR-2026-05-03-006
---

## Module
### L1: Perception
- **Layer:** L1 | **Version:** 0.9.0 | **Status:** accepted
- **Description:** 8-Kanal multimodale Sensorfusion
- **Inputs:** Kamera (Opt-In), GPS, Accelerometer, Mikrofon-Frequenzspektrum, Lichtsensor, BT-Scan, Bildschirmzeit-API, System-Uhr
- **Outputs:** Frequenzspektrum, GPS-Koordinaten, Bewegungsvektor, Consent-State
- **Validation:** 839 Tests, 97% Coverage
- **Coverage:** 97.0%
- **Tests:** 839
- **Links:** | downstream → L2
### L2: Situation RuleEngine
- **Layer:** L2 | **Version:** 0.8.0 | **Status:** accepted
- **Description:** YAML-Regelwerk plus optionaler RF-Classifier
- **Inputs:** L1 Outputs
- **Outputs:** Context-ID, Confidence-Score
- **Validation:** 97% Coverage
- **Links:** upstream → L1 | downstream → L3
### L3: Episodes SQLite
- **Layer:** L3 | **Version:** 0.8.0 | **Status:** accepted
- **Description:** Temporale Segmentierung mit 3-Kontext-Sequenz-Buffer
- **Inputs:** Context-IDs plus Timestamps von L2
- **Outputs:** Episodes (history.db)
- **Validation:** 839 Tests gruen
- **Links:** upstream → L2 | downstream → L4
### L4: Features Engineer
- **Layer:** L4 | **Version:** 0.8.0 | **Status:** accepted
- **Description:** Feature-Extraktion mit relativer 14-Tage-Normalisierung
- **Inputs:** Episodes von L3
- **Outputs:** DayFeatures (focus, energy, social, movement)
- **Validation:** 100% Coverage
- **Links:** upstream → L3 | downstream → L5, CNA
### L5: Intelligence DayScore
- **Layer:** L5 | **Version:** 0.8.0 | **Status:** accepted
- **Description:** DayScore, WellnessState, Evening Coach Guided Journaling
- **Inputs:** DayFeatures von L4
- **Outputs:** DayScore (0-10), WellnessState, Recommendations
- **Validation:** 100% Coverage
- **Links:** upstream → L4
### CNA: COGNITUM Norm-Adapter
- **Layer:** L3-Compliance | **Version:** 0.2.0 | **Status:** proposed
- **Description:** Generischer Norm-Pruefadapter mit Consent-Gate
- **Inputs:** Merkmalsvektor von L4, Consent-State von L1
- **Outputs:** Konformitaetserklaerung, Pruefbericht, zkVM-Proof
- **Validation:** Noch nicht implementiert
- **Links:** upstream → L4, L1
---

## ISO 25010 Qualitaetsmerkmale
### Funktionale Eignung
- **Funktionale Vollstaendigkeit:** accepted (Test: `pytest -m functional_completeness`) — L1-L5 Pipeline vollstaendig, CNA proposed
- **Funktionale Korrektheit:** accepted (Test: `pytest -m functional_correctness`) — 839 Tests gruen, DayScore-Berechnung verifiziert
- **Funktionale Angemessenheit:** accepted — VDI-Gate stellt sicher dass nur benoetigte Funktionen implementiert werden
### Leistungseffizienz
- **Zeitverhalten:** proposed — Noch kein Benchmark. Ziel: L1-L5 Pipeline unter 200ms auf Smartphone
- **Ressourcenverbrauch:** proposed — SQLite statt Cloud-DB. Ollama-Modelle lokal. RAM-Budget TBD
- **Kapazitaet:** proposed — 14-Tage-Fenster begrenzt Speicherwachstum
### Kompatibilitaet
- **Koexistenz:** accepted — Android-App laeuft neben anderen Apps, keine exklusiven Sensor-Locks
- **Interoperabilitaet:** proposed — MCP-Server-Interface fuer CNA geplant. DayGraph-Export als JSON
### Benutzbarkeit
- **Erlernbarkeit:** proposed — Evening Coach als Guided Journaling. Onboarding-Flow TBD
- **Bedienbarkeit:** proposed — Smartphone-First. Smart Glasses spaeter
- **Barrierefreiheit:** proposed — WCAG 2.1 AA als Ziel. Noch nicht implementiert
### Zuverlaessigkeit
- **Reife:** accepted (Test: `pytest -m reliability`) — 839 Tests, 97% Coverage, keine bekannten Crashes
- **Verfuegbarkeit:** accepted — Offline-First Architektur. Kein Cloud-Dependency
- **Fehlertoleranz:** accepted — 3-Kontext-Sequenz-Buffer in L3 toleriert Sensor-Ausfaelle
- **Wiederherstellbarkeit:** proposed — SQLite-WAL-Modus. Backup-Strategie TBD
### Sicherheit
- **Vertraulichkeit:** accepted (Test: `pytest -m privacy`) — Zero-Retention. Alle Daten lokal. Kein Cloud-Upload
- **Integritaet:** accepted — zkVM-Proof fuer CNA-Konformitaetserklaerungen
- **Nichtabstreitbarkeit:** accepted — OpenTimestamps-Anker auf alle kritischen Artefakte
- **Zurechenbarkeit:** accepted — Audit-Trail in masterplan.yaml. Git-History als Nachweis
- **Authentizitaet:** proposed — Per-Sensor-Consent. Biometrische Auth TBD
### Wartbarkeit
- **Modularitaet:** accepted — 5+1 Layer-Architektur. Jedes Modul unabhaengig testbar
- **Wiederverwendbarkeit:** accepted — CNA als generischer Norm-Adapter fuer beliebige Regelwerke
- **Analysierbarkeit:** accepted (Test: `pytest -m consistency`) — NetworkX-Graph-Tests pruefen ADR/Modul-Konsistenz
- **Aenderbarkeit:** accepted — SSoT-Pipeline: YAML aendern, generate.py, CI rendert alles
- **Testbarkeit:** accepted (Test: `pytest validation/tests/ -v`) — Pydantic-Schema plus Yamale plus pytest plus networkx
### Portabilitaet
- **Anpassbarkeit:** proposed — Android-First. iOS und Smart Glasses als Roadmap
- **Installierbarkeit:** proposed — Android APK geplant. Kein App Store noetig fuer MVP
- **Austauschbarkeit:** proposed — DayGraph-Export ermoeglicht Datenmigration
---

## ISO 23894 Risikoregister
| ID | Beschreibung | Wahrscheinlichkeit | Impact | Mitigation | Status |
|----|-------------|-------------------|--------|------------|--------|
| RISK-01 | Sensor-Consent wird ignoriert oder umgangen | low | Datenschutzverletzung, DSGVO-Verstoss | Per-Sensor-Consent-Gate in L1 mit Default-OFF fuer Kamera und Mikrofon | accepted |
| RISK-02 | RF-Classifier in L2 produziert diskriminierende Kontextklassifikation | medium | Unfaire DayScore-Bewertung, Nutzervertrauensverlust | Primaer YAML-Regelwerk. RF nur optional. Fairness-Tests als Privacy-Invariante | accepted |
| RISK-03 | SQLite-Datenbank in L3 wird von Drittapp exfiltriert | medium | Vollstaendiger Episoden-Verlauf kompromittiert | SQLCipher-Verschluesselung. Android Scoped Storage. Kein Export ohne expliziten User-Intent | proposed |
| RISK-04 | DayScore-Algorithmus erzeugt psychischen Druck durch Gamification | medium | Nutzer-Wellbeing verschlechtert sich statt verbessert | Evening Coach als Guided Journaling statt Ranking. Keine Streaks. Kein Leaderboard | accepted |
| RISK-05 | Ollama-Modell halluziniert in Evening Coach Recommendations | high | Falsche Gesundheits- oder Verhaltensempfehlungen | LLM nur fuer Formulierung, nicht fuer medizinische Aussagen. Disclaimer. Fakten aus L4-Features | accepted |
| RISK-06 | zkVM-Proof in CNA ist zu rechenintensiv fuer Smartphone | medium | CNA-Konformitaetspruefung nur auf Desktop moeglich | Proof-Generierung optional asynchron. Fallback auf signierte YAML-Attestation | proposed |
| RISK-07 | Solo-Entwickler-Risiko: Bus-Faktor 1 | high | Projekt stirbt bei Ausfall | SSoT-Pipeline macht Repo selbstdokumentierend. CLAUDE.md und AGENTS.md als Onboarding. IP via OTS gesichert | accepted |
---

## Privacy-Invarianten
| ID | Beschreibung | Test-Tool | Test-Methode |
|----|-------------|-----------|-------------|
| PRIV-01 | Zero-Retention: Keine Nutzerdaten verlassen das Geraet | pytest | Network-Monitor-Test: Kein HTTP-Egress waehrend 24h-Betrieb |
| PRIV-02 | Per-Sensor-Consent: Jeder Sensor individuell aktivierbar/deaktivierbar | pytest | Consent-Matrix-Test: Alle 8 Sensoren einzeln togglen, Pipeline laeuft weiter |
| PRIV-03 | Kamera und Mikrofon Default-OFF | pytest | Fresh-Install-Test: Nach Erstinstallation beide Sensoren verifiziert OFF |
| PRIV-04 | DayGraph-Export nur durch expliziten User-Intent | pytest | No-Auto-Export-Test: Kein DayGraph-File ohne User-Tap |
| PRIV-05 | SQLite-DB nicht durch Drittapps lesbar | adb | Scoped-Storage-Test: adb shell versucht DB-Zugriff, wird verweigert |
| PRIV-06 | Keine biometrischen Daten in DayFeatures | pytest | Feature-Schema-Test: DayFeatures enthalten nur focus/energy/social/movement, keine biometrischen Rohdaten |
| PRIV-07 | Audit-Trail enthaelt keine personenbezogenen Daten | pytest | Audit-PII-Scan: Regex-Scan auf Email, Telefon, GPS-Koordinaten in audit_trail |
---

## Exit-Plan

| Phase | Milestones | Asset Sale | Equity Round |
|-------|-----------|------------|-------------|
| Phase 0 (heute) | v0.8.0, 839 Tests, DPMA, ISO-Docs | EUR 30k-250k | Nicht finanzierbar |
| Phase 1 | Multimodale Pipeline plus Smartphone MVP plus NGI0 | EUR 300k-1.5M | EUR 2-5M |
| Phase 2 | 500-2k Nutzer, MRR, B2B-Pilot | EUR 2-8M | EUR 8-18M |
| Phase 3 | EUR 5-50k MRR, B2B-Kunde | EUR 10-40M | EUR 30-80M |
| Exit | Retention plus Scale | EUR 30-150M | EUR 100-500M+ |
**Comps:** Limitless Meta, Bee Amazon, Humane HP, Base44 Wix

---

## Audit-Trail

| Timestamp | Commit SHA | Reason | ADR Ref | Actor |
|-----------|-----------|--------|---------|-------|
| 2026-05-03T12:00:00Z | initial | Phase 7 Bootstrap alle Artefakte deployt | ADR-2026-05-03-006 | Fatih Dinc |
| 2026-05-03T18:00:00Z | 798cee34acfab273056ead4cca2b8a19d3eada94 | v1.3.0 — ISO 25010, Risikoregister, Privacy-Invarianten, Template-Fixes | ADR-2026-05-03-006 | Fatih Dinc |
