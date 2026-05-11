from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from cognitum.cna.rules import RuleResult


def _build_report(results: list[RuleResult]) -> dict[str, Any]:
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    total = len(results)

    avg_confidence = sum(r.confidence for r in results) / total if total else 0.0

    if failed:
        fail_ids = ", ".join(r.rule_id for r in failed)
        summary = f"{len(passed)}/{total} Regeln erfüllt — Verstöße: {fail_ids}"
    else:
        summary = f"{total}/{total} Regeln erfüllt — Alle Normen eingehalten"

    detail = [
        {
            "rule_id": r.rule_id,
            "norm": r.norm,
            "description": r.description,
            "passed": r.passed,
            "value": r.value,
            "threshold": r.threshold,
            "confidence": r.confidence,
        }
        for r in results
    ]

    # deduplicate while preserving order
    seen: set[str] = set()
    sources: list[str] = []
    for r in results:
        if r.source not in seen:
            seen.add(r.source)
            sources.append(r.source)

    return {
        "summary": summary,
        "detail": detail,
        "sources": sources,
        "confidence": round(avg_confidence, 4),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def report_json(results: list[RuleResult]) -> str:
    return json.dumps(_build_report(results), ensure_ascii=False, indent=2)


def report_markdown(results: list[RuleResult]) -> str:
    data = _build_report(results)
    lines = [
        "# CNA Compliance Report",
        "",
        f"**Generiert:** {data['generated_at']}",
        f"**Zusammenfassung:** {data['summary']}",
        f"**Konfidenz:** {data['confidence']}",
        "",
        "## Regelprüfungen",
        "",
        "| ID | Norm | Beschreibung | Wert | Schwelle | Ergebnis |",
        "|---|---|---|---|---|---|",
    ]
    for d in data["detail"]:
        status = "✅ OK" if d["passed"] else "❌ FAIL"
        lines.append(
            f"| {d['rule_id']} | {d['norm']} | {d['description']} "
            f"| {d['value']} | {d['threshold']} | {status} |"
        )
    lines += [
        "",
        "## Quellen",
        "",
    ]
    for src in data["sources"]:
        lines.append(f"- {src}")
    lines.append("")
    return "\n".join(lines)
