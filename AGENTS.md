# AGENTS.md – COGNITUM Multi-Agent-Konfiguration

> Auto-generiert aus masterplan.yaml v1.3.0

## WICHTIG: Single Source of Truth

Alle Agenten in diesem System MUESSEN den aktuellen Masterplan lesen bevor sie arbeiten:
https://gitlab.com/fatdinhero/cognitum/-/raw/main/governance/masterplan.yaml

## Active Modules
- **L1** (Perception): 8-Kanal multimodale Sensorfusion [accepted]
- **L2** (Situation RuleEngine): YAML-Regelwerk plus optionaler RF-Classifier [accepted]
- **L3** (Episodes SQLite): Temporale Segmentierung mit 3-Kontext-Sequenz-Buffer [accepted]
- **L4** (Features Engineer): Feature-Extraktion mit relativer 14-Tage-Normalisierung [accepted]
- **L5** (Intelligence DayScore): DayScore, WellnessState, Evening Coach Guided Journaling [accepted]
- **CNA** (COGNITUM Norm-Adapter): Generischer Norm-Pruefadapter mit Consent-Gate [proposed]

## ADR Index
- [ADR-2026-05-03-001] Annahme des DaySensOS-Konstruktionsprotokolls (accepted)
- [ADR-2026-05-03-002] G2G Cert AI als externer Compliance-Pruefservice (deprecated)
- [ADR-2026-05-03-003] Make-or-Buy COGNITUM Norm-Adapter statt G2G Cert AI (accepted)
- [ADR-2026-05-03-004] CNA v0.1 COGNITUM Norm-Adapter Architektur (accepted)
- [ADR-2026-05-03-005] CNA v0.2 Integration der Morphologischen Systemanalyse (accepted)
- [ADR-2026-05-03-006] Lebendiger Masterplan YAML-SSoT-System (accepted)
- [ADR-2026-05-03-007] Tool-Auswahl fuer das Masterplan-SSoT-System (accepted)
