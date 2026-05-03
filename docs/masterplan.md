# COGNITUM Masterplan v1.2.0

Generated: 2026-05-03T12:00:00Z

## ADRs
### ADR-2026-05-03-001: Annahme des DaySensOS-Konstruktionsprotokolls
- **Status:** Status.ACCEPTED
- **Decision:** Protokoll als systemischer Gate-Mechanismus uebernommen
### ADR-2026-05-03-002: G2G Cert AI als externer Compliance-Pruefservice
- **Status:** Status.DEPRECATED
- **Decision:** Externer Pruefservice per API
### ADR-2026-05-03-003: Make-or-Buy COGNITUM Norm-Adapter statt G2G Cert AI
- **Status:** Status.ACCEPTED
- **Decision:** Eigenentwicklung CNA, YAML-Regelwerk plus zkVM-Proof
### ADR-2026-05-03-004: CNA v0.1 COGNITUM Norm-Adapter Architektur
- **Status:** Status.ACCEPTED
- **Decision:** MCP-Server, YAML-Regeln, zkVM-Proof
### ADR-2026-05-03-005: CNA v0.2 Integration der Morphologischen Systemanalyse
- **Status:** Status.ACCEPTED
- **Decision:** Regeln referenzieren Sensorkanaele. Per-Sensor-Consent respektiert.
### ADR-2026-05-03-006: Lebendiger Masterplan YAML-SSoT-System
- **Status:** Status.ACCEPTED
- **Decision:** masterplan.yaml als SSoT, Pydantic plus Yamale, Jinja2, Pandoc, GitLab-CI
### ADR-2026-05-03-007: Tool-Auswahl fuer das Masterplan-SSoT-System
- **Status:** Status.ACCEPTED
- **Decision:** Jinja2, Pandoc, Pydantic plus Yamale, git-cliff, pytest plus networkx

## Modules
### L1: Perception
- **Layer:** L1 | **Version:** 0.9.0 | **Status:** Status.ACCEPTED
- **Inputs:** Kamera (Opt-In), GPS, Accelerometer, Mikrofon-Frequenzspektrum, Lichtsensor, BT-Scan, Bildschirmzeit-API, System-Uhr
- **Outputs:** Frequenzspektrum, GPS-Koordinaten, Bewegungsvektor, Consent-State
### L2: Situation RuleEngine
- **Layer:** L2 | **Version:** 0.8.0 | **Status:** Status.ACCEPTED
- **Inputs:** L1 Outputs
- **Outputs:** Context-ID, Confidence-Score
### L3: Episodes SQLite
- **Layer:** L3 | **Version:** 0.8.0 | **Status:** Status.ACCEPTED
- **Inputs:** Context-IDs plus Timestamps von L2
- **Outputs:** Episodes (history.db)
### L4: Features Engineer
- **Layer:** L4 | **Version:** 0.8.0 | **Status:** Status.ACCEPTED
- **Inputs:** Episodes von L3
- **Outputs:** DayFeatures (focus, energy, social, movement)
### L5: Intelligence DayScore
- **Layer:** L5 | **Version:** 0.8.0 | **Status:** Status.ACCEPTED
- **Inputs:** DayFeatures von L4
- **Outputs:** DayScore (0-10), WellnessState, Recommendations
### CNA: COGNITUM Norm-Adapter
- **Layer:** L3-Compliance | **Version:** 0.2.0 | **Status:** Status.PROPOSED
- **Inputs:** Merkmalsvektor von L4, Consent-State von L1
- **Outputs:** Konformitaetserklaerung, Pruefbericht, zkVM-Proof
