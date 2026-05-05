#!/usr/bin/env python3
"""
scripts/adr_generator.py
Generiert synthetische ADR-Cases via SPALTEN-Durchlaeufe.
Idempotent: bereits vorhandene Cases werden uebersprungen.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from governance.models import EngineeringCase, Urgency
from spalten_agent import run_spalten
from governance.evaluator import SPALTENEvaluator

_evaluator = SPALTENEvaluator()

OUTPUT_DIR = REPO_ROOT / "data" / "synthetic_adrs"

PROBLEMS = [
    ("CNA CLI: Authentifizierung — JWT vs. API-Key",                           "cna_cli"),
    ("CNA CLI: Logging-Strategie — strukturiert vs. plain text",               "cna_cli"),
    ("CNA CLI: Deployment-Strategie — Docker vs. pip-Package",                 "cna_cli"),
    ("CNA CLI: Fehlerbehandlung — Exception-Hierarchie definieren",             "cna_cli"),
    ("DaySensOS: Datenschutz-Architektur — On-Device vs. Cloud-Processing",    "daysensos"),
    ("DaySensOS: Sensor-Sampling-Rate — Echtzeit vs. Batch",                   "daysensos"),
    ("DaySensOS: Energieoptimierung — Duty-Cycle-Strategie",                   "daysensos"),
    ("DaySensOS: Datenformat fuer Sensordaten — Protobuf vs. JSON",            "daysensos"),
    ("COGNITUM: Prompt-Caching-Strategie fuer wiederholte SPALTEN-Runs",       "cognitum"),
    ("COGNITUM: Versionierung von masterplan.yaml — semver vs. datumbasiert",  "cognitum"),
    ("COGNITUM: Backup-Strategie fuer ChromaDB-Vektordatenbank",               "cognitum"),
    ("COGNITUM: Monitoring-Ansatz — Langfuse vs. eigenes Logging",             "cognitum"),
    ("Norm-Registry: GEG-Primaerenergiefaktoren aktuell halten",               "general"),
    ("Norm-Registry: TA-Laerm-Grenzwerte — Hardcode vs. YAML-Config",         "general"),
    ("API-Design: REST vs. GraphQL fuer den Engineering-Agent",                "general"),
    ("Datenpipeline: Batch vs. Stream-Processing fuer ADR-Indexierung",        "general"),
    ("Security: Secrets-Management — env-Variablen vs. Vault",                 "general"),
    ("Testing-Strategie: Unit vs. Integration Tests fuer Governance-Layer",    "general"),
    ("CI/CD: GitLab Runner vs. GitHub Actions als primaere Pipeline",          "general"),
    ("Dokumentation: Automatisch generiert vs. manuell gepflegt",              "general"),
]


def _slug(problem: str) -> str:
    import re
    s = problem.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s[:60].strip("_")


def _find_existing(problem: str) -> Optional[Path]:
    """Prueft ob ein Case fuer dieses Problem schon existiert (slug-Matching)."""
    slug = _slug(problem)
    for f in OUTPUT_DIR.glob("*.json"):
        if slug[:30] in f.stem:
            return f
    return None


def generate(limit: int = 20) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    problems = PROBLEMS[:limit]
    total = len(problems)

    print(f"\n{'='*60}")
    print(f"ADR Generator — {total} Probleme")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    done = 0
    skipped = 0

    for idx, (problem, domain) in enumerate(problems, 1):
        slug = _slug(problem)
        existing = _find_existing(problem)

        if existing:
            print(f"[{idx:02d}/{total}] SKIP  {problem[:60]}")
            skipped += 1
            done += 1
            continue

        print(f"[{idx:02d}/{total}] START {problem[:60]}")

        case = EngineeringCase(
            title=problem[:80],
            problem=problem,
            domain=domain,
            urgency=Urgency.medium,
        )

        try:
            # Vollstaendiger 7-Phasen-Lauf, kein GitOps, kein Branch
            result = run_spalten(case, human_approve=True, skip_gitops=True)

            # Evaluation aus letztem Export holen (bereits in result eingebettet)
            eval_result = None
            if hasattr(result, "_eval_result"):
                eval_result = result._eval_result

            data = json.loads(result.model_dump_json())
            data["_problem_slug"] = slug
            data["_domain"] = domain
            data["evaluation"] = _evaluator.evaluate_case(result)

            out_path = OUTPUT_DIR / f"{result.case_id}_{slug[:40]}.json"
            out_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            done += 1
            print(f"         ✅ gespeichert: {out_path.name}")

        except Exception as e:
            print(f"         ❌ Fehler: {e}")

    print(f"\n{'='*60}")
    print(f"Fertig: {done}/{total} | Neu: {done - skipped} | Uebersprungen: {skipped}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetische ADR-Cases generieren")
    parser.add_argument("--limit", type=int, default=20,
                        help="Maximale Anzahl zu generierender Cases (default: 20)")
    args = parser.parse_args()
    generate(limit=args.limit)
