# CLAUDE.md – COGNITUM Projektkonfiguration

> Auto-generiert aus masterplan.yaml v1.4.1 am 2026-05-03T21:00:00Z
> NICHT MANUELL EDITIEREN. Aenderungen nur ueber governance/masterplan.yaml.

## WICHTIG: Immer aktuellen Masterplan laden

Vor jeder Arbeit in diesem Projekt MUSS der aktuelle Masterplan gelesen werden:
https://gitlab.com/fatdinhero/cognitum/-/raw/main/governance/masterplan.yaml
Dieser Masterplan ist die Single Source of Truth fuer alle Entscheidungen, Module und Regeln.

## Verfassung (14 Artikel)
1. **Privacy-First**: Zero-Retention ist unverueckbar. Keine Nutzerdaten verlassen das Geraet.
2. **Per-Sensor-Consent**: Jeder Sensorkanal individuell steuerbar. Kamera und Mikrofon default OFF.
3. **Local-First**: Keine Cloud-Abhaengigkeit. Alle Kernfunktionen muessen offline funktionieren.
4. **Morphologisches Gate**: Jede Funktionsentscheidung durchlaeuft VDI 2221/2222/2225 Konstruktionsprotokoll.
5. **ADR-Pflicht**: Keine Implementierung ohne dokumentierte Architekturentscheidung (ADR).
6. **Halal-Gate**: AAOIFI 6-Faktor-Screening auf alle Revenue-Streams.
7. **Zakat**: 2.5% automatische Berechnung auf alle Einnahmen.
8. **OTS-First**: OpenTimestamps-Anker vor jeder Veroeffentlichung.
9. **SAFE Mode**: Externes Backup vor jeder destruktiven Aktion.
10. **Golden ZIP**: Vollstaendige One-Shot-Deliverables.
11. **Halluzinations-Kennzeichnung**: Jede LLM-generierte Aussage MUSS mit Confidence-Score >= 0.8 ODER explizitem [Unverified]-Marker ausgegeben werden. Keine Erfindung von Normen, Zahlen, Paragrafen.
12. **Output-Format-Regeln**: Jeder Agent-Output MUSS strukturiert sein: { summary, detail, sources[], confidence }. Kein reiner Fliesstext bei sicherheitsrelevanten Ausgaben.
13. **Glossar-Verweis**: Alle fachspezifischen Begriffe MUESSEN mit Verweis auf glossary.md versehen werden. Kein Term wird ohne Definition verwendet.
14. **Morphologisches Entscheidungsprotokoll**: Jede Entscheidung (Produkt, Architektur, Priorisierung) MUSS den morphologischen Kasten (VDI 2221) und die Bewertungsmatrix (VDI 2225) durchlaufen. Agenten liefern begruendete Empfehlungen, keine Optionslisten.

## Aktive ADRs
| ID | Titel | Status |
|----|-------|--------|
| ADR-2026-05-03-001 | Annahme des DaySensOS-Konstruktionsprotokolls | accepted |
| ADR-2026-05-03-003 | Make-or-Buy COGNITUM Norm-Adapter statt G2G Cert AI | accepted |
| ADR-2026-05-03-004 | CNA v0.1 COGNITUM Norm-Adapter Architektur | accepted |
| ADR-2026-05-03-005 | CNA v0.2 Integration der Morphologischen Systemanalyse | accepted |
| ADR-2026-05-03-006 | Lebendiger Masterplan YAML-SSoT-System | accepted |
| ADR-2026-05-03-007 | Tool-Auswahl fuer das Masterplan-SSoT-System | accepted |
| ADR-2026-05-03-008 | Naechster Produktschritt: CNA CLI vor NGI0 und Smartphone MVP | accepted |

### Deprecated ADRs
- ~~ADR-2026-05-03-002: G2G Cert AI als externer Compliance-Pruefservice~~ → ersetzt durch ADR-2026-05-03-003

## Module
| ID | Name | Layer | Version | Status |
|----|------|-------|---------|--------|
| L1 | Perception | L1 | 0.9.0 | accepted |
| L2 | Situation RuleEngine | L2 | 0.8.0 | accepted |
| L3 | Episodes SQLite | L3 | 0.8.0 | accepted |
| L4 | Features Engineer | L4 | 0.8.0 | accepted |
| L5 | Intelligence DayScore | L5 | 0.8.0 | accepted |
| CNA | COGNITUM Norm-Adapter | L3-Compliance | 0.3.0 | proposed |

## ISO 25010 Qualitaetsstatus
### Funktionale Eignung
- Funktionale Vollstaendigkeit: **accepted** — L1-L5 Pipeline vollstaendig, CNA proposed
- Funktionale Korrektheit: **accepted** — 839 Tests gruen, DayScore-Berechnung verifiziert
- Funktionale Angemessenheit: **accepted** — VDI-Gate stellt sicher dass nur benoetigte Funktionen implementiert werden
### Leistungseffizienz
- Zeitverhalten: **proposed** — Noch kein Benchmark. Ziel: L1-L5 Pipeline unter 200ms auf Smartphone
- Ressourcenverbrauch: **proposed** — SQLite statt Cloud-DB. Ollama-Modelle lokal. RAM-Budget TBD
- Kapazitaet: **proposed** — 14-Tage-Fenster begrenzt Speicherwachstum
### Kompatibilitaet
- Koexistenz: **accepted** — Android-App laeuft neben anderen Apps, keine exklusiven Sensor-Locks
- Interoperabilitaet: **proposed** — MCP-Server-Interface fuer CNA geplant. DayGraph-Export als JSON
### Benutzbarkeit
- Erlernbarkeit: **proposed** — Evening Coach als Guided Journaling. Onboarding-Flow TBD
- Bedienbarkeit: **proposed** — Smartphone-First. Smart Glasses spaeter
- Barrierefreiheit: **proposed** — WCAG 2.1 AA als Ziel. Noch nicht implementiert
### Zuverlaessigkeit
- Reife: **accepted** — 839 Tests, 97% Coverage, keine bekannten Crashes
- Verfuegbarkeit: **accepted** — Offline-First Architektur. Kein Cloud-Dependency
- Fehlertoleranz: **accepted** — 3-Kontext-Sequenz-Buffer in L3 toleriert Sensor-Ausfaelle
- Wiederherstellbarkeit: **proposed** — SQLite-WAL-Modus. Backup-Strategie TBD
### Sicherheit
- Vertraulichkeit: **accepted** — Zero-Retention. Alle Daten lokal. Kein Cloud-Upload
- Integritaet: **accepted** — zkVM-Proof fuer CNA-Konformitaetserklaerungen
- Nichtabstreitbarkeit: **accepted** — OpenTimestamps-Anker auf alle kritischen Artefakte
- Zurechenbarkeit: **accepted** — Audit-Trail in masterplan.yaml. Git-History als Nachweis
- Authentizitaet: **proposed** — Per-Sensor-Consent. Biometrische Auth TBD
### Wartbarkeit
- Modularitaet: **accepted** — 5+1 Layer-Architektur. Jedes Modul unabhaengig testbar
- Wiederverwendbarkeit: **accepted** — CNA als generischer Norm-Adapter fuer beliebige Regelwerke
- Analysierbarkeit: **accepted** — NetworkX-Graph-Tests pruefen ADR/Modul-Konsistenz
- Aenderbarkeit: **accepted** — SSoT-Pipeline: YAML aendern, generate.py, CI rendert alles
- Testbarkeit: **accepted** — Pydantic-Schema plus Yamale plus pytest plus networkx
### Portabilitaet
- Anpassbarkeit: **proposed** — Android-First. iOS und Smart Glasses als Roadmap
- Installierbarkeit: **proposed** — Android APK geplant. Kein App Store noetig fuer MVP
- Austauschbarkeit: **proposed** — DayGraph-Export ermoeglicht Datenmigration

## Risikoregister (ISO 23894)
| ID | Risiko | P | Mitigation | Status |
|----|--------|---|------------|--------|
| RISK-01 | Sensor-Consent wird ignoriert oder umgangen | low | Per-Sensor-Consent-Gate in L1 mit Default-OFF fuer Kamera und Mikrofon | accepted |
| RISK-02 | RF-Classifier in L2 produziert diskriminierende Kontextklassifikation | medium | Primaer YAML-Regelwerk. RF nur optional. Fairness-Tests als Privacy-Invariante | accepted |
| RISK-03 | SQLite-Datenbank in L3 wird von Drittapp exfiltriert | medium | SQLCipher-Verschluesselung. Android Scoped Storage. Kein Export ohne expliziten User-Intent | proposed |
| RISK-04 | DayScore-Algorithmus erzeugt psychischen Druck durch Gamification | medium | Evening Coach als Guided Journaling statt Ranking. Keine Streaks. Kein Leaderboard | accepted |
| RISK-05 | Ollama-Modell halluziniert in Evening Coach Recommendations | high | LLM nur fuer Formulierung, nicht fuer medizinische Aussagen. Disclaimer. Fakten aus L4-Features. Art. 11 Halluzinations-Kennzeichnung | accepted |
| RISK-06 | zkVM-Proof in CNA ist zu rechenintensiv fuer Smartphone | medium | Proof-Generierung optional asynchron. Fallback auf signierte YAML-Attestation | proposed |
| RISK-07 | Solo-Entwickler-Risiko: Bus-Faktor 1 | high | SSoT-Pipeline macht Repo selbstdokumentierend. CLAUDE.md und AGENTS.md als Onboarding. IP via OTS gesichert | accepted |

## Privacy-Invarianten
- **PRIV-01**: Zero-Retention: Keine Nutzerdaten verlassen das Geraet
- **PRIV-02**: Per-Sensor-Consent: Jeder Sensor individuell aktivierbar/deaktivierbar
- **PRIV-03**: Kamera und Mikrofon Default-OFF
- **PRIV-04**: DayGraph-Export nur durch expliziten User-Intent
- **PRIV-05**: SQLite-DB nicht durch Drittapps lesbar
- **PRIV-06**: Keine biometrischen Daten in DayFeatures
- **PRIV-07**: Audit-Trail enthaelt keine personenbezogenen Daten
- **PRIV-08**: DSAR-Funktion: Auskunft, Berichtigung, Loeschung innerhalb 30 Tage
- **PRIV-09**: Verschluesselung ruhend (SQLCipher) und im Transport (TLS 1.3)
- **PRIV-10**: Membership-Inference-Schutz: DayGraph-Export gegen MIA robust

> WARNUNG: Jede Code-Aenderung die eine Privacy-Invariante verletzt ist VERBOTEN.

## Verbindliche Konstruktionsregeln
1. Vor jeder Implementierung: Morphologisches Analyse-Gate (VDI 2221/2222/2225).
2. Keine Implementierung ohne abgeschlossenes ADR.
3. Privacy-Invarianten (Zero-Retention, Per-Sensor-Consent) sind unverrueckbar.
4. Alle Entscheidungen als ADR dokumentieren.
5. Nach jeder Entscheidung: masterplan.yaml aktualisieren und generate.py ausfuehren.
6. Kein generiertes Artefakt manuell editieren.

## WICHTIG: Produkt-Kontext lesen

DaySensOS ist das KERNPRODUKT. Vor jeder produktbezogenen Arbeit:
https://gitlab.com/fatdinhero/cognitum/-/raw/main/docs/daysensos-product-context.md