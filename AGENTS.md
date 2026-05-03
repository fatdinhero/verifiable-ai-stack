# AGENTS.md – COGNITUM Multi-Agent-Konfiguration

> Auto-generiert aus masterplan.yaml v1.2.0

## WICHTIG: Single Source of Truth

Alle Agenten in diesem System MUESSEN den aktuellen Masterplan lesen bevor sie arbeiten:
https://gitlab.com/fatdinhero/cognitum/-/raw/main/governance/masterplan.yaml

## Active Modules
- **L1** (Perception): 8-Kanal multimodale Sensorfusion [Status.ACCEPTED]
- **L2** (Situation RuleEngine): YAML-Regelwerk plus optionaler RF-Classifier [Status.ACCEPTED]
- **L3** (Episodes SQLite): Temporale Segmentierung mit 3-Kontext-Sequenz-Buffer [Status.ACCEPTED]
- **L4** (Features Engineer): Feature-Extraktion mit relativer 14-Tage-Normalisierung [Status.ACCEPTED]
- **L5** (Intelligence DayScore): DayScore, WellnessState, Evening Coach Guided Journaling [Status.ACCEPTED]
- **CNA** (COGNITUM Norm-Adapter): Generischer Norm-Pruefadapter mit Consent-Gate [Status.PROPOSED]

## ADR Index
- [ADR-2026-05-03-001] Annahme des DaySensOS-Konstruktionsprotokolls (Status.ACCEPTED)
- [ADR-2026-05-03-002] G2G Cert AI als externer Compliance-Pruefservice (Status.DEPRECATED)
- [ADR-2026-05-03-003] Make-or-Buy COGNITUM Norm-Adapter statt G2G Cert AI (Status.ACCEPTED)
- [ADR-2026-05-03-004] CNA v0.1 COGNITUM Norm-Adapter Architektur (Status.ACCEPTED)
- [ADR-2026-05-03-005] CNA v0.2 Integration der Morphologischen Systemanalyse (Status.ACCEPTED)
- [ADR-2026-05-03-006] Lebendiger Masterplan YAML-SSoT-System (Status.ACCEPTED)
- [ADR-2026-05-03-007] Tool-Auswahl fuer das Masterplan-SSoT-System (Status.ACCEPTED)
