# CLAUDE.md – COGNITUM Projektkonfiguration

> Auto-generiert aus masterplan.yaml v1.2.0 am 2026-05-03T12:00:00Z

## Verfassung
Die globale Verfassung ist in `constitution.md` definiert.

## Aktive ADRs
| ID | Titel | Status |
|----|-------|--------|
| ADR-2026-05-03-001 | Annahme des DaySensOS-Konstruktionsprotokolls | Status.ACCEPTED |
| ADR-2026-05-03-003 | Make-or-Buy COGNITUM Norm-Adapter statt G2G | Status.ACCEPTED |
| ADR-2026-05-03-004 | CNA v0.1 Architektur | Status.ACCEPTED |
| ADR-2026-05-03-005 | CNA v0.2 Morphologische Systemanalyse | Status.ACCEPTED |
| ADR-2026-05-03-006 | Lebendiger Masterplan YAML-SSoT-System | Status.ACCEPTED |
| ADR-2026-05-03-007 | Tool-Auswahl SSoT-System | Status.ACCEPTED |

## Module
| ID | Name | Layer | Version | Status |
|----|------|-------|---------|--------|
| L1 | Perception | L1 | 0.9.0 | Status.ACCEPTED |
| L2 | Situation | L2 | 0.8.0 | Status.ACCEPTED |
| L3 | Episodes | L3 | 0.8.0 | Status.ACCEPTED |
| L4 | Features | L4 | 0.8.0 | Status.ACCEPTED |
| L5 | Intelligence | L5 | 0.8.0 | Status.ACCEPTED |
| CNA | Norm-Adapter | L3-Compliance | 0.2.0 | Status.PROPOSED |

## Konstruktionsregeln
1. Morphologisches Analyse-Gate vor jeder Implementierung (VDI 2221/2222/2225).
2. Keine Implementierung ohne ADR.
3. Privacy-Invarianten (Zero-Retention, Per-Sensor-Consent) unverrückbar.
4. Alle Entscheidungen als ADR dokumentieren.