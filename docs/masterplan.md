# COGNITUM Masterplan v1.2.0

Generated: 2026-05-03T12:00:00Z

## ADRs
### ADR-2026-05-03-001: Annahme des DaySensOS-Konstruktionsprotokolls
- **Status:** Status.ACCEPTED
- **Decision:** Protokoll als systemischer Gate-Mechanismus uebernommen
### ADR-2026-05-03-002: G2G Cert AI als externer Compliance-Pruefservice
- **Status:** Status.DEPRECATED
- **Decision:** Externer Pruefservice per API
### ADR-2026-05-03-003: Make-or-Buy COGNITUM Norm-Adapter statt G2G
- **Status:** Status.ACCEPTED
- **Decision:** CNA, YAML-Regelwerk + zkVM-Proof
### ADR-2026-05-03-004: CNA v0.1 Architektur
- **Status:** Status.ACCEPTED
- **Decision:** MCP-Server, YAML-Regeln, zkVM-Proof
### ADR-2026-05-03-005: CNA v0.2 Morphologische Systemanalyse
- **Status:** Status.ACCEPTED
- **Decision:** Regeln referenzieren Sensorkanaele
### ADR-2026-05-03-006: Lebendiger Masterplan YAML-SSoT-System
- **Status:** Status.ACCEPTED
- **Decision:** masterplan.yaml, Pydantic+Yamale, Jinja2, Pandoc, GitLab-CI
### ADR-2026-05-03-007: Tool-Auswahl SSoT-System
- **Status:** Status.ACCEPTED
- **Decision:** Jinja2, Pandoc, Pydantic+Yamale, git-cliff, pytest+networkx

## Modules
### L1: Perception (L1)
- **Version:** 0.9.0 | **Status:** Status.ACCEPTED
- **Inputs:** Kamera (Opt-In), GPS, Accelerometer, Frequenzspektrum, Lichtsensor, BT-Scan, Bildschirmzeit-API, System-Uhr
- **Outputs:** Frequenzspektrum, GPS-Koordinaten, Bewegungsvektor, Consent-State
### L2: Situation (L2)
- **Version:** 0.8.0 | **Status:** Status.ACCEPTED
- **Inputs:** L1 Outputs
- **Outputs:** Context-ID, Confidence-Score
### L3: Episodes (L3)
- **Version:** 0.8.0 | **Status:** Status.ACCEPTED
- **Inputs:** Context-IDs von L2
- **Outputs:** Episodes (history.db)
### L4: Features (L4)
- **Version:** 0.8.0 | **Status:** Status.ACCEPTED
- **Inputs:** Episodes von L3
- **Outputs:** DayFeatures
### L5: Intelligence (L5)
- **Version:** 0.8.0 | **Status:** Status.ACCEPTED
- **Inputs:** DayFeatures von L4
- **Outputs:** DayScore, WellnessState, Recommendations
### CNA: Norm-Adapter (L3-Compliance)
- **Version:** 0.2.0 | **Status:** Status.PROPOSED
- **Inputs:** Merkmalsvektor von L4, Consent-State von L1
- **Outputs:** Konformitaetserklaerung, Pruefbericht, zkVM-Proof
