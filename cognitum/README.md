# COGNITUM

**Privacy-First Wearable AI Governance System**

COGNITUM ist das Governance- und Architektur-Repository fuer DaySensOS — ein Privacy-First Wearable AI Operating System. Dieses Repo ist die **Single Source of Truth (SSoT)** fuer alle Architekturentscheidungen, Module, Qualitaetsmerkmale, Risiken und Privacy-Invarianten.

## Architektur

```
L1 Perception (8-Kanal Sensorfusion)
  → L2 Situation RuleEngine (YAML + RF-Classifier)
    → L3 Episodes SQLite (temporale Segmentierung)
      → L4 Features Engineer (14-Tage-Normalisierung)
        → L5 Intelligence DayScore (DayScore, WellnessState, Coach)
        → CNA Norm-Adapter (Compliance, zkVM-Proof)
```

## SSoT-Pipeline

Alle generierten Artefakte werden aus `governance/masterplan.yaml` erzeugt:

```
masterplan.yaml → generate.py → CLAUDE.md, AGENTS.md, crews/, ollama/, docs/
```

**Niemals generierte Dateien manuell editieren.** Aenderungen nur ueber `governance/masterplan.yaml`, dann:

```bash
python scripts/generate.py --targets all
```

## Struktur

| Pfad | Beschreibung |
|------|-------------|
| `governance/masterplan.yaml` | SSoT — alle ADRs, Module, ISO 25010, Risiken, Privacy |
| `governance/constitution.md` | 10 unveraenderliche Prinzipien |
| `governance/glossary.md` | Begriffsdefinitionen |
| `scripts/generate.py` | Jinja2-Generator (YAML → alles) |
| `scripts/append_audit_trail.py` | Audit-Trail-Eintrag hinzufuegen |
| `templates/` | Jinja2-Templates fuer alle generierten Dateien |
| `validation/` | Pydantic-Schema, Yamale-Schema, Konsistenz-Tests |
| `docs/masterplan.md` | Generierte Masterplan-Dokumentation |
| `CLAUDE.md` | Generierte Projektkonfiguration fuer Claude |
| `AGENTS.md` | Generierte Multi-Agent-Konfiguration |
| `crews/` | Generierte CrewAI-Agentenkonfiguration |
| `ollama/modelfiles/` | Generierte Ollama-Modelfiles (L1-L5, CNA) |

## Validierung

```bash
# Schema-Validierung
yamale --schema validation/schemas/masterplan_schema.yaml governance/masterplan.yaml

# Pydantic-Validierung
python scripts/generate.py --validate-only

# Konsistenz-Tests (Dead Links, Duplikate, Privacy-Tests)
pytest validation/tests/ -v
```

## CI/CD

GitLab CI prueft bei jedem Push:
1. **schema-check** — Yamale + Pydantic-Validierung
2. **consistency-test** — pytest mit NetworkX-Graph-Analyse
3. **render-configs** — Generiert alle Artefakte

## Prinzipien

1. **Privacy-First** — Zero-Retention, alle Daten lokal
2. **Per-Sensor-Consent** — Kamera/Mikrofon default OFF
3. **Local-First** — Keine Cloud-Abhaengigkeit
4. **Morphologisches Gate** — VDI 2221/2222/2225 vor jeder Entscheidung
5. **ADR-Pflicht** — Keine Implementierung ohne Architekturentscheidung

## Qualitaet

- **ISO 25010** — 8 Characteristics, 26 Sub-Characteristics bewertet
- **ISO 23894** — 7 AI-spezifische Risiken mit Mitigationen
- **Privacy** — 7 Invarianten mit definierten Test-Methoden
- **Tests** — 839 Tests, 97% Coverage (L1)

## Autor

**Fatih Dinc** — datalabel.tech

## Lizenz

Proprietaer. Alle Rechte vorbehalten.
