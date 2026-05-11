"""
governance/synthesis_agent.py
Destilliert ADRs, Analogien und Insights zu COGNITUM Design Principles.
"""
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT   = Path(__file__).resolve().parent.parent
OLLAMA_URL  = "http://localhost:11434/api/chat"
MODEL       = "qwen2.5:7b"

BOT_QUEUE_FILE   = REPO_ROOT / ".bot_queue.json"
SYNTHETIC_ADR_DIR = REPO_ROOT / "data" / "synthetic_adrs"
PRINCIPLES_JSON  = REPO_ROOT / "docs" / "design_principles.json"
PRINCIPLES_MD    = REPO_ROOT / "docs" / "COGNITUM_DESIGN_PRINCIPLES.md"

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Du bist COGNITUM Chief Architect. "
    "Analysiere alle vorliegenden ADRs, Analogien und Insights "
    "und destilliere daraus maximal 10 Design Principles fuer "
    "COGNITUM — die fundamentalen Architektur-Entscheidungen "
    "die aus der gesammelten Erfahrung hervorgehen.\n\n"
    "Jedes Prinzip hat:\n"
    "- name: kurzer praegnanter Name (max 5 Worte)\n"
    "- description: Was bedeutet dieses Prinzip? (2-3 Saetze)\n"
    "- evidence: Aus welchen ADRs/Analogien abgeleitet? (Liste)\n"
    "- priority: critical/high/medium\n"
    "- implementation_hint: Konkreter naechster Schritt\n\n"
    'Antworte NUR mit validem JSON:\n'
    '{"principles": [...], "synthesis_date": "ISO-Date", '
    '"total_cases_analyzed": 0, "top_domains": ["eu_ai_act", "daysensos"]}'
)


class SynthesisAgent:

    def run(self) -> dict:
        cases, analogies = self._collect_data()
        total = len(cases) + len(analogies)
        context = self._build_context(cases, analogies)

        raw = self._call_llm(context)
        result = self._parse_response(raw, total)

        PRINCIPLES_JSON.parent.mkdir(parents=True, exist_ok=True)
        PRINCIPLES_JSON.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        md = self._generate_markdown(result, len(analogies))
        PRINCIPLES_MD.write_text(md, encoding="utf-8")
        logger.info(f"Design Principles gespeichert: {PRINCIPLES_MD}")

        self.push_to_wiki(md)
        return result

    # ── Datensammlung ─────────────────────────────────────────────────────

    def _collect_data(self):
        cases: List[dict] = []

        for path in sorted(SYNTHETIC_ADR_DIR.glob("*.json")):
            try:
                d = json.loads(path.read_text(encoding="utf-8"))
                cases.append({
                    "id":       d.get("case_id", path.stem),
                    "title":    d.get("title", ""),
                    "problem":  d.get("problem", ""),
                    "domain":   d.get("domain", ""),
                    "solution": d.get("selected_solution", ""),
                    "score":    d.get("evaluation", {}).get("overall_score", 0.0),
                })
            except Exception:
                pass

        for path in sorted(REPO_ROOT.glob("spalten_result_*.json")):
            try:
                d = json.loads(path.read_text(encoding="utf-8"))
                ev = d.get("evaluation", {})
                cases.append({
                    "id":       path.stem,
                    "title":    d.get("title", ""),
                    "problem":  d.get("problem", ""),
                    "domain":   d.get("domain", ""),
                    "solution": d.get("selected_solution", ""),
                    "score":    ev.get("overall_score", 0.0),
                })
            except Exception:
                pass

        analogies: List[dict] = []
        if BOT_QUEUE_FILE.exists():
            try:
                queue = json.loads(BOT_QUEUE_FILE.read_text(encoding="utf-8"))
                for e in queue:
                    if e.get("source_type") in ("analogy_extraction", "insight"):
                        analogies.append({
                            "title":    e.get("title", ""),
                            "problem":  e.get("problem", ""),
                            "text":     e.get("text", ""),
                            "domain":   e.get("domain", "general"),
                        })
            except Exception:
                pass

        return cases, analogies

    def _build_context(self, cases: List[dict], analogies: List[dict]) -> str:
        lines = [f"=== {len(cases)} ADR-Cases ==="]
        for c in cases[:40]:
            lines.append(
                f"[{c['domain']}] {c['title'][:60]}: {c['problem'][:80]} "
                f"→ {(c['solution'] or '')[:60]} (Score: {c['score']:.2f})"
            )
        if analogies:
            lines.append(f"\n=== {len(analogies)} Analogien/Insights ===")
            for a in analogies[:15]:
                lines.append(f"[{a['domain']}] {a['title'][:60]}: {a['text'][:80]}")
        ctx = "\n".join(lines)
        return ctx[:6000]

    # ── LLM ───────────────────────────────────────────────────────────────

    def _call_llm(self, context: str) -> str:
        payload = json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": context},
            ],
            "options": {"temperature": 0.2},
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"LLM nicht erreichbar: {e}")
            return self._fallback_principles()

    def _parse_response(self, raw: str, total: int) -> dict:
        text = raw.strip()
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        try:
            result = json.loads(text)
        except Exception:
            result = json.loads(self._fallback_principles())

        result["synthesis_date"] = datetime.now(timezone.utc).isoformat()
        result["total_cases_analyzed"] = total
        result.setdefault("top_domains", [])
        result.setdefault("principles", [])
        return result

    def _fallback_principles(self) -> str:
        return json.dumps({
            "principles": [
                {
                    "name": "Local-First Privacy",
                    "description": "Alle Daten bleiben auf dem Geraet. Keine Cloud-Abhaengigkeit.",
                    "evidence": ["PRIV-02", "PRIV-03"],
                    "priority": "critical",
                    "implementation_hint": "Consent-Gate vor jeder Sensor-Aktivierung erzwingen",
                },
                {
                    "name": "SPALTEN vor Entscheidung",
                    "description": "Jede Architektur-Entscheidung durchlaeuft den SPALTEN-Prozess.",
                    "evidence": ["VDI 2221", "VDI 2225"],
                    "priority": "critical",
                    "implementation_hint": "Morphologischen Kasten fuer alle neuen Features pflegen",
                },
            ],
            "synthesis_date": datetime.now(timezone.utc).isoformat(),
            "total_cases_analyzed": 0,
            "top_domains": ["eu_ai_act", "daysensos"],
        })

    # ── Markdown ──────────────────────────────────────────────────────────

    def _generate_markdown(self, result: dict, analogy_count: int) -> str:
        principles = result.get("principles", [])
        date       = result.get("synthesis_date", "")[:10]
        total      = result.get("total_cases_analyzed", 0)
        domains    = ", ".join(result.get("top_domains", []))

        lines = [
            "# COGNITUM Design Principles",
            f"*Automatisch destilliert aus {total} ADR-Cases und {analogy_count} Analogien*",
            f"*Stand: {date}*",
            "",
            "## Uebersicht",
            f"{len(principles)} Prinzipien | Domaenen: {domains}",
            "",
            "## Prinzipien",
            "",
        ]
        for i, p in enumerate(principles, 1):
            evidence = ", ".join(p.get("evidence", [])) or "—"
            lines += [
                f"### {i}. {p.get('name', 'Unbekannt')} [{p.get('priority', 'medium').upper()}]",
                "",
                p.get("description", ""),
                "",
                f"**Implementierungshinweis:** {p.get('implementation_hint', '—')}",
                "",
                f"**Belege:** {evidence}",
                "",
                "---",
                "",
            ]
        return "\n".join(lines)

    # ── Wiki ──────────────────────────────────────────────────────────────

    def push_to_wiki(self, content: str = "") -> bool:
        try:
            from governance.gitops_handler import GitOpsHandler
            if not content:
                if PRINCIPLES_MD.exists():
                    content = PRINCIPLES_MD.read_text(encoding="utf-8")
                else:
                    return False
            gh = GitOpsHandler()
            return gh.push_to_wiki("Design-Principles/COGNITUM-v1", content)
        except Exception as e:
            logger.warning(f"Wiki Push fehlgeschlagen: {e}")
            return False
