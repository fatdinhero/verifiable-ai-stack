# MPPS Data Pipeline & ADR Management

## Ordnerstruktur

```
data/
├── synthetic_adrs/     # Automatisch generierte ADRs (JSON)
├── evaluation/         # Evaluations-Reports
├── training/           # Trainingsdaten für Fine-Tuning
└── collected_adrs.jsonl
```

## Wichtige Dateien

- `adr_generator.py` → Erzeugt synthetische ADRs
- `evaluator.py` → Bewertet ADRs (inkl. LLM-as-Judge + Adversarial)
- `gitops_handler.py` → Automatische Branch + Commit + MR
- `.gitlab-ci.yml` → CI/CD Pipeline für ADR-Validierung

## Workflow

1. Feature entwickeln → MPPS Agent läuft
2. ADR wird automatisch erzeugt + committed
3. Merge Request wird erstellt
4. CI Pipeline validiert ADR + führt Evaluation durch
5. Bei Score < 0.80 → Pipeline kann fehlschlagen (optional)

## Nächste Schritte

- `adr_generator.py` mehrfach ausführen → 500–2000 ADRs sammeln
- `evaluator.py` auf dem Datensatz laufen lassen
- Fine-Tuning mit Axolotl / Llama-Factory starten
