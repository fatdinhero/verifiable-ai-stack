#!/Users/datalabel.tech/COS/cognitum/.venv/bin/python3
"""
mcp_server.py
COGNITUM Engineering Agent — MCP-Server fuer Claude Desktop und Cursor
Transport: stdio (Standard MCP)
Python: .venv (>=3.10 wegen fastmcp)
"""
import asyncio
import contextlib
import io
import json
import sys
from pathlib import Path

# Repo-Root zum Pythonpfad hinzufuegen
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

import fastmcp
from fastmcp import FastMCP

# ─── Lazy-Imports (graceful bei fehlenden Deps) ───────────────────────────────

def _load_governance():
    from governance.registry import (
        get_ta_laerm, calculate_rpn, get_action_priority,
        GEG_PRIMAERENERGIE, BEG_STUFEN,
    )
    from governance.models import EngineeringCase
    from governance.rag_memory import RAGMemory
    from governance.evaluator import SPALTENEvaluator
    from spalten_agent import run_spalten as _run_spalten
    return {
        "get_ta_laerm": get_ta_laerm,
        "calculate_rpn": calculate_rpn,
        "get_action_priority": get_action_priority,
        "GEG_PRIMAERENERGIE": GEG_PRIMAERENERGIE,
        "BEG_STUFEN": BEG_STUFEN,
        "EngineeringCase": EngineeringCase,
        "RAGMemory": RAGMemory,
        "SPALTENEvaluator": SPALTENEvaluator,
        "run_spalten": _run_spalten,
    }


@contextlib.contextmanager
def _silent():
    """Leitet stdout auf stderr um — schuetzt MCP stdio-Stream."""
    old = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old


# ─── MCP-Server ───────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="cognitum-engineering-agent",
    instructions=(
        "COGNITUM Engineering Agent v0.2. "
        "Werkzeuge: SPALTEN-Methode (VDI 2221), VDI 2225 Bewertung, "
        "FMEA/RPN, TA-Laerm, GEG/BEG Normen, ADR-Suche via RAG."
    ),
)


@mcp.tool()
def run_spalten(
    problem: str,
    domain: str = "general",
    urgency: str = "medium",
    gitops: bool = False,
) -> str:
    """
    Fuehrt einen vollstaendigen SPALTEN-Durchlauf durch (VDI 2221).
    Gibt case_id, Phasen-Zusammenfassung, VDI 2225 Score, ADR-Referenz und MR-URL zurueck.
    gitops=True erstellt automatisch Branch + Merge Request auf GitLab.
    """
    g = _load_governance()
    case = g["EngineeringCase"](
        title=problem[:80],
        problem=problem,
        domain=domain,
        urgency=g["EngineeringCase"].model_fields["urgency"].default
        if urgency == "medium" else urgency,
    )
    with _silent():
        result = g["run_spalten"](case, human_approve=gitops)

    # Kompakte Zusammenfassung extrahieren
    node_l = next((s for s in result.steps if s.phase.name == "L"), None)
    node_e = next((s for s in result.steps if s.phase.name == "E"), None)

    vdi_score = (
        node_l.artifacts.get("vdi2225", {}).get("best_score")
        if node_l else None
    )
    adr_ref = node_e.adr_ref if node_e else None

    steps_summary = [
        {"phase": s.phase.name, "confidence": s.confidence, "summary": s.summary[:120]}
        for s in result.steps
    ]

    output = {
        "case_id": result.case_id,
        "title": result.title,
        "domain": result.domain,
        "selected_solution": result.selected_solution,
        "vdi2225_score": vdi_score,
        "adr_ref": adr_ref,
        "steps_count": len(result.steps),
        "steps_summary": steps_summary,
        "mr_url": None,
    }

    # MR-URL aus GitOps-Artefakten holen (wenn gitops=True)
    if gitops:
        for s in result.steps:
            if s.phase.name == "N" and s.artifacts.get("mr_url"):
                output["mr_url"] = s.artifacts["mr_url"]

    return json.dumps(output, ensure_ascii=False, indent=2)


@mcp.tool()
def search_adrs(query: str, n_results: int = 3) -> str:
    """
    Semantische Suche ueber alle gespeicherten ADRs und Dokumente in der RAG-Datenbank.
    Gibt die relevantesten Treffer mit ID, Typ und Textausschnitt zurueck.
    """
    g = _load_governance()
    with _silent():
        rag = g["RAGMemory"](persist_dir=str(REPO_ROOT / ".chroma_db"))
        hits = rag.search(query, n_results=n_results)

    results = [
        {
            "id": h["id"],
            "type": h["type"],
            "distance": round(h["distance"], 4),
            "metadata": h.get("metadata", {}),
            "snippet": h["content"][:300],
        }
        for h in hits
    ]
    return json.dumps({"query": query, "results": results}, ensure_ascii=False, indent=2)


@mcp.tool()
def evaluate_adr(adr_path: str) -> str:
    """
    Prueft die Qualitaet einer ADR-Markdown-Datei nach SPALTEN/VDI-2225-Kriterien.
    Gibt quality_score (0.0-1.0) und Einzelchecks zurueck.
    adr_path: absoluter oder relativer Pfad zur .md-Datei.
    """
    g = _load_governance()
    path = Path(adr_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    if not path.exists():
        return json.dumps({"error": f"Datei nicht gefunden: {adr_path}"})

    evaluator = g["SPALTENEvaluator"]()
    result = evaluator.evaluate_adr_file(path)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_registry_value(typ: str, params: str) -> str:
    """
    Deterministischer Lookup aus der COGNITUM Compliance-Registry.
    typ: 'ta_laerm' | 'geg' | 'beg' | 'fmea'
    params fuer ta_laerm: 'zonen_typ,tageszeit'  z.B. 'reines_wohn,nacht'
    params fuer geg:      Energietraeger          z.B. 'strom'
    params fuer beg:      Effizienzstufe          z.B. '55'
    params fuer fmea:     's,o,d'                 z.B. '8,5,3'
    """
    g = _load_governance()
    typ = typ.strip().lower()

    try:
        if typ == "ta_laerm":
            parts = [p.strip() for p in params.split(",")]
            if len(parts) != 2:
                return json.dumps({"error": "ta_laerm erwartet 'zonen_typ,tageszeit'"})
            value = g["get_ta_laerm"](parts[0], parts[1])
            return json.dumps({
                "typ": "ta_laerm",
                "zonen_typ": parts[0],
                "tageszeit": parts[1],
                "wert_dba": float(value),
                "einheit": "dB(A)",
            })

        elif typ == "geg":
            key = params.strip()
            if key not in g["GEG_PRIMAERENERGIE"]:
                return json.dumps({
                    "error": f"Unbekannter Energietraeger: {key}",
                    "verfuegbar": list(g["GEG_PRIMAERENERGIE"].keys()),
                })
            return json.dumps({
                "typ": "geg",
                "energietraeger": key,
                "primaerenergiefaktor": float(g["GEG_PRIMAERENERGIE"][key]),
            })

        elif typ == "beg":
            key = params.strip()
            if key not in g["BEG_STUFEN"]:
                return json.dumps({
                    "error": f"Unbekannte BEG-Stufe: {key}",
                    "verfuegbar": list(g["BEG_STUFEN"].keys()),
                })
            stufe = g["BEG_STUFEN"][key]
            return json.dumps({
                "typ": "beg",
                "stufe": key,
                "q_p_kwh_m2a": float(stufe["q_p"]),
                "h_t_wm2k": float(stufe["h_t"]),
            })

        elif typ == "fmea":
            parts = [p.strip() for p in params.split(",")]
            if len(parts) != 3:
                return json.dumps({"error": "fmea erwartet 's,o,d' (Severity,Occurrence,Detection)"})
            s, o, d = int(parts[0]), int(parts[1]), int(parts[2])
            rpn = g["calculate_rpn"](s, o, d)
            ap = g["get_action_priority"](s, o, d)
            return json.dumps({
                "typ": "fmea",
                "severity": s, "occurrence": o, "detection": d,
                "rpn": rpn,
                "action_priority": ap,
            })

        else:
            return json.dumps({
                "error": f"Unbekannter Typ: {typ}",
                "verfuegbar": ["ta_laerm", "geg", "beg", "fmea"],
            })

    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── Test-Modus ───────────────────────────────────────────────────────────────

def test_tools():
    """Testet alle vier Tools direkt ohne MCP-Transport."""
    print("\n" + "="*60)
    print("COGNITUM MCP-Server — Tool-Test")
    print("="*60)

    tests = [
        ("get_registry_value", {"typ": "ta_laerm", "params": "reines_wohn,nacht"}),
        ("get_registry_value", {"typ": "geg",      "params": "strom"}),
        ("get_registry_value", {"typ": "beg",      "params": "55"}),
        ("get_registry_value", {"typ": "fmea",     "params": "8,5,3"}),
        ("search_adrs",        {"query": "SQLite CLI Architektur", "n_results": 2}),
        ("evaluate_adr",       {"adr_path": "docs/adr/2026-05-05-cna-cli-timeout-problem.md"}),
    ]

    async def _run():
        for tool_name, params in tests:
            print(f"\n[{tool_name}] params={params}")
            try:
                result = await mcp.call_tool(tool_name, params)
                raw = result.content[0].text if result.content else "{}"
                data = json.loads(raw)
                print(json.dumps(data, indent=2, ensure_ascii=False)[:400])
            except Exception as e:
                print(f"  FEHLER: {e}")

    asyncio.run(_run())
    print("\n" + "="*60)
    print("Test abgeschlossen.")
    print("="*60 + "\n")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--test" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "test"):
        test_tools()
    else:
        mcp.run()  # stdio-Transport fuer Claude Desktop / Cursor
