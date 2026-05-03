# Changelog

Alle relevanten Aenderungen an COGNITUM und DaySensOS werden in dieser Datei dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).
Versionierung folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [0.9.0] - 2026-05-03

### Hinzugefuegt — DaySensOS Produkt
- L1 Perception: 8-Kanal Sensorfusion mit Consent-Gate (Kamera+Mikrofon default OFF)
- L2 Situation: YAML-Regelwerk mit 8 Kontextregeln (sleep, deep_work, exercise, commute, meeting, social, light_work, rest)
- L3 Episodes: SQLite temporale Segmentierung mit 3-Kontext-Buffer (Erkenntnis 6)
- L4 Features: 14-Tage relative Normalisierung fuer focus, energy, social, movement (Erkenntnis 7)
- L5 Intelligence: DayScore (0-10), WellnessState, faktenbasierte Recommendations
- FastAPI Server auf Port 8111 mit Endpoints: /capture, /status, /episodes/today, /score
- Sensor-Simulator mit 15 Tagesszenarien und Pforzheimer GPS-Koordinaten
- 31 Produkt-Tests (Consent, L1-L5, Privacy-Invarianten, Anti-Gamification)
- Claude Code Autonomie-Config (.claude/settings.json)

### Hinzugefuegt — Governance
- Constitution: 10 → 14 Artikel (inkl. Halluzinations-Kennzeichnung, Output-Format, Glossar-Verweis, Morphologisches Entscheidungsprotokoll)
- Privacy-Invarianten: 0 → 10 (PRIV-01 bis PRIV-10 mit Test-Methoden)
- ISO 25010: 8 Qualitaetsmerkmale mit 26 Sub-Characteristics
- ISO 23894: 7 Risiken mit Mitigationen
- CNA: 12 Norm-Regeln (GEG §71/72/74, KfW-BEG, TA Laerm, VDI 4645)
- ADRs: 7 → 8 (inkl. ADR-008 CNA-CLI-Priorisierung mit VDI 2225 Bewertungsmatrix)
- Glossar: 8 → 40 Eintraege
- 32 Governance-Tests (ISO, Risk, Privacy, Exit, Audit, Constitution, CNA-Norms)
- Produkt-Kontext-Snapshot (docs/daysensos-product-context.md)

### Geaendert
- generate.py: model_dump(mode="json") fixt Status.ACCEPTED Enum-Bug
- CLAUDE.md.j2: zeigt ISO/Risk/Privacy/Constitution + Produkt-Kontext-Link
- AGENTS.md.j2: Agenten kennen Privacy-Invarianten und Risiken
- masterplan-doc.md.j2: vollstaendig mit allen 8 Sektionen
- .gitlab-ci.yml: 3 → 4 Jobs (+ daysensos-test)
- pyproject.toml: v1.2.0 → v1.4.1

### Abgesichert
- OpenTimestamps: v1.4.0 Commit-Hash auf Bitcoin verankert
- OpenTimestamps: v0.9.0 Tag auf Bitcoin verankert
- Git-Tags: v0.9.0, v1.2.0
- GitLab CI: 63 Tests in 4 Jobs, alle gruen

## [1.4.1] - 2026-05-03

### Hinzugefuegt
- Constitution Art. 14: Morphologisches Entscheidungsprotokoll (VDI 2221/2225)
- ADR-008: CNA CLI vor NGI0 vor Phone MVP (Bewertungsmatrix als YAML)

## [1.4.0] - 2026-05-03

### Hinzugefuegt
- Constitution: 13 Artikel in SSoT (constitution_articles[])
- Privacy: PRIV-08 DSAR, PRIV-09 Verschluesselung, PRIV-10 Membership-Inference
- CNA: 12 Norm-Regeln mit Consent-Gate-Pruefung
- Schema: ConstitutionArticle Pydantic-Model + Yamale
- Template: constitution.md.j2 → governance/constitution.md

## [1.3.0] - 2026-05-03

### Hinzugefuegt
- ISO 25010: 8 Qualitaetsmerkmale (26 Sub-Characteristics)
- ISO 23894: 7 Risiken mit Mitigationen
- Privacy: PRIV-01 bis PRIV-07 mit Test-Methoden
- README.md
- 21 Tests

### Behoben
- Status.ACCEPTED Enum-Rendering in generierten Artefakten

## [1.2.0] - 2026-05-03

### Hinzugefuegt
- masterplan.yaml als Single Source of Truth
- 7 ADRs, 6 Module (L1-L5 + CNA)
- Exit-Plan (5 Phasen), Audit-Trail
- GitLab CI Pipeline (validate + render)
- Jinja2-Templates fuer CLAUDE.md, AGENTS.md, crews, modelfiles, docs
- Pydantic + Yamale Doppelvalidierung
