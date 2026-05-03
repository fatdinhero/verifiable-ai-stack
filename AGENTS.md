# AGENTS.md – COGNITUM Multi-Agent-Konfiguration

> Auto-generiert aus masterplan.yaml v1.2.0

## Constitution
See `constitution.md` for global rules.

## Modules
- **L1** (Perception): 8-Kanal multimodale Sensorfusion [Status.ACCEPTED]
- **L2** (Situation): YAML-Regelwerk + optionaler RF-Classifier [Status.ACCEPTED]
- **L3** (Episodes): Temporale Segmentierung mit 3-Kontext-Sequenz-Buffer [Status.ACCEPTED]
- **L4** (Features): Feature-Extraktion mit relativer 14-Tage-Normalisierung [Status.ACCEPTED]
- **L5** (Intelligence): DayScore, WellnessState, Evening Coach (Guided Journaling) [Status.ACCEPTED]
- **CNA** (Norm-Adapter): Generischer Norm-Pruefadapter mit Consent-Gate [Status.PROPOSED]

## ADR Index
- [ADR-2026-05-03-001] Annahme des DaySensOS-Konstruktionsprotokolls (Status.ACCEPTED)
- [ADR-2026-05-03-002] G2G Cert AI als externer Compliance-Pruefservice (Status.DEPRECATED)
- [ADR-2026-05-03-003] Make-or-Buy COGNITUM Norm-Adapter statt G2G (Status.ACCEPTED)
- [ADR-2026-05-03-004] CNA v0.1 Architektur (Status.ACCEPTED)
- [ADR-2026-05-03-005] CNA v0.2 Morphologische Systemanalyse (Status.ACCEPTED)
- [ADR-2026-05-03-006] Lebendiger Masterplan YAML-SSoT-System (Status.ACCEPTED)
- [ADR-2026-05-03-007] Tool-Auswahl SSoT-System (Status.ACCEPTED)
