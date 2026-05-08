#!/usr/bin/env python3
"""
crsoc/masterplan_updater.py
Phase 6: Masterplan YAML updaten + ADR erstellen
VERBOTEN: governance/registry.py veraendern
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT  = Path(__file__).resolve().parents[1]
ADR_DIR    = REPO_ROOT / "docs" / "adr"
MASTERPLAN = REPO_ROOT / "governance" / "masterplan.yaml"


class MasterplanUpdater:
    def update(self, validated_ideas: List[Dict[str, Any]], cycle_result: Dict[str, Any]) -> Dict[str, Any]:
        ts_str  = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        trigger  = cycle_result.get("trigger", "unknown")

        # ── ADR erstellen ─────────────────────────────────────────────────────
        adr_name  = f"{date_str}-crsoc-{trigger.replace('_', '-')}.json"
        adr_path  = ADR_DIR / adr_name
        ADR_DIR.mkdir(parents=True, exist_ok=True)

        adr_content = {
            "id":          f"CRSOC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
            "type":        "crsoc_cycle",
            "trigger":     trigger,
            "timestamp":   ts_str,
            "status":      "accepted",
            "context":     cycle_result.get("phases", {}).get("1_situation", {}).get("summary", ""),
            "decision":    f"CRSOC-Zyklus abgeschlossen. {len(validated_ideas)} Ideen validiert.",
            "best_idea":   cycle_result.get("best_idea", "—"),
            "best_psi":    cycle_result.get("best_score", 0.0),
            "ideas":       validated_ideas[:5],
        }
        adr_path.write_text(json.dumps(adr_content, indent=2, ensure_ascii=False), encoding="utf-8")

        # ── Masterplan: neue CRSOC-Ergebnisse anhängen ────────────────────────
        mp_updated = False
        if MASTERPLAN.exists() and validated_ideas:
            try:
                content = MASTERPLAN.read_text(encoding="utf-8")
                best_name = cycle_result.get("best_idea", "")
                best_psi  = cycle_result.get("best_score", 0.0)
                append_block = (
                    f"\n# CRSOC {trigger} ({date_str})\n"
                    f"# Beste Idee: {best_name} (Ψ={best_psi:.2f})\n"
                    f"# ADR: {adr_name}\n"
                )
                if append_block.strip() not in content:
                    MASTERPLAN.write_text(content + append_block, encoding="utf-8")
                    mp_updated = True
            except Exception as e:
                print(f"[CRSOC] Masterplan-Update Fehler (nicht kritisch): {e}")

        return {
            "adr_path":      str(adr_path.relative_to(REPO_ROOT)),
            "adr_id":        adr_content["id"],
            "masterplan_updated": mp_updated,
            "ideas_saved":   len(validated_ideas),
        }
