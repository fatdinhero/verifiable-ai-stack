# COGNITUM Masterplan v1.2.0

**Generated:** 2026-05-03T12:00:00Z
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
- **Links:** downstream → ADR-003

### ADR-2026-05-03-002: G2G Cert AI als externer Compliance-Pruefservice
- **Status:** deprecated
- **Date:** 2026-05-03
- **Context:** Evaluierung der G2G-Integration
- **Decision:** Externer Pruefservice per API
- **Consequences:** Wurde durch ADR-003 revidiert
- **Superseded by:** ADR-2026-05-03-003
- **Links:** upstream → ADR-001 | downstream → ADR-003

### ADR-2026-05-03-003: Make-or-Buy COGNITUM Norm-Adapter statt G2G Cert AI
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** G2G verletzt Zero-Retention. COGNITUM baut eigenen Norm-Adapter.
- **Decision:** Eigenentwicklung CNA, YAML-Regelwerk plus zkVM-Proof
- **Consequences:** CNA wird als MCP-Server integriert.
- **Links:** upstream → ADR-002 | downstream → ADR-004

### ADR-2026-05-03-004: CNA v0.1 COGNITUM Norm-Adapter Architektur
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** Erster Bauplan fuer den Norm-Adapter
- **Decision:** MCP-Server, YAML-Regeln, zkVM-Proof
- **Consequences:** Erste Anwendung GEG/KfW fuer Waermepumpen
- **Links:** upstream → ADR-003 | downstream → ADR-005

### ADR-2026-05-03-005: CNA v0.2 Integration der Morphologischen Systemanalyse
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** Multimodale Bedingungen, Consent-Gate, Offline-Faehigkeit
- **Decision:** Regeln referenzieren Sensorkanaele. Per-Sensor-Consent respektiert.
- **Consequences:** CNA wird nativer COGNITUM-Buerger
- **Links:** upstream → ADR-004 | downstream → ADR-006

### ADR-2026-05-03-006: Lebendiger Masterplan YAML-SSoT-System
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** Architektur-Report bestaetigt YAML-zentrische Single Source of Truth
- **Decision:** masterplan.yaml als SSoT, Pydantic plus Yamale, Jinja2, Pandoc, GitLab-CI
- **Consequences:** Phase 7 Implementierung abgeschlossen.
- **Links:** upstream → ADR-005 | downstream → ADR-007

### ADR-2026-05-03-007: Tool-Auswahl fuer das Masterplan-SSoT-System
- **Status:** accepted
- **Date:** 2026-05-03
- **Context:** Phase 4 VDI 2221 morphologische Bewertung aller Tools
- **Decision:** Jinja2, Pandoc, Pydantic plus Yamale, git-cliff, pytest plus networkx
- **Consequences:** Alle Tools offline-first, Python-nativ, CI-freundlich.
- **Links:** upstream → ADR-006

---

## Module

### L1: Perception
- **Layer:** L1 | **Version:** 0.9.0 | **Status:** accepted
- **Description:** 8-Kanal multimodale Sensorfusion
- **Inputs:** Kamera (Opt-In), GPS, Accelerometer, Mikrofon-Frequenzspektrum, Lichtsensor, BT-Scan, Bildschirmzeit-API, System-Uhr
- **Outputs:** Frequenzspektrum, GPS-Koordinaten, Bewegungsvektor, Consent-State
- **Validation:** 839 Tests, 97% Coverage
- **Links:** downstream → L2

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

## Exit-Plan

| Phase | Milestones | Asset Sale | Equity Round |
|---|---|---|---|
| Phase 0 (heute) | v0.8.0, 839 Tests, DPMA, ISO-Docs | EUR 30k–250k | Nicht finanzierbar |
| Phase 1 | Multimodale Pipeline + Smartphone MVP + NGI0 | EUR 300k–1.5M | EUR 2–5M |
| Phase 2 | 500–2k Nutzer, MRR, B2B-Pilot | EUR 2–8M | EUR 8–18M |
| Phase 3 | EUR 5–50k MRR, B2B-Kunde | EUR 10–40M | EUR 30–80M |
| Exit | Retention + Scale | EUR 30–150M | EUR 100–500M+ |

**Comps:** Limitless (Meta), Bee (Amazon), Humane (HP), Base44 (Wix)

---

## Audit-Trail

| Timestamp | Commit SHA | Reason | ADR Ref | Actor |
|---|---|---|---|---|
| 2026-05-03T12:00:00Z | initial | Phase 7 Bootstrap alle Artefakte deployt | ADR-2026-05-03-006 | Fatih Dinc |
