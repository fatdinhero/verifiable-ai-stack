"""
governance/wiki_formatter.py
Formatiert Bot-Queue-Eintraege und SPALTEN-Ergebnisse als GitLab Wiki Markdown.
"""
from typing import Tuple


class WikiFormatter:

    def format_analogy(self, entry: dict) -> Tuple[str, str]:
        """Gibt (title, content) fuer einen Analogy-Queue-Eintrag zurueck."""
        domain = entry.get("domain", "general").title()
        title = f"Analogies/{domain}/{entry.get('title', 'Unbekannt')[:60]}"

        content = (
            f"# {entry.get('title', 'Unbekannt')}\n\n"
            f"**Domain:** {entry.get('domain', '')}  \n"
            f"**Urgency:** {entry.get('urgency', '')}  \n"
            f"**Quelle:** {entry.get('url', 'manuell')}  \n"
            f"**Erfasst:** {entry.get('timestamp', '')}\n\n"
            f"## Engineering Problem\n"
            f"{entry.get('problem', '')}\n\n"
            f"## Begruendung\n"
            f"{entry.get('text', '')}\n\n"
            f"## Rohtext\n"
            f"{entry.get('raw_text', '')[:500]}\n\n"
            f"---\n"
            f"*Automatisch generiert von COGNITUM AnalogyExtractor*"
        )
        return title, content

    def format_insight(self, entry: dict) -> Tuple[str, str]:
        """Gibt (title, content) fuer einen Insight-Queue-Eintrag zurueck."""
        domain = entry.get("domain", "general").title()
        title = f"Insights/{domain}/{entry.get('title', 'Unbekannt')[:60]}"

        content = (
            f"# {entry.get('title', 'Unbekannt')}\n\n"
            f"**Domain:** {entry.get('domain', '')}  \n"
            f"**Urgency:** {entry.get('urgency', '')}  \n"
            f"**Quelle:** {entry.get('url', 'manuell')}  \n"
            f"**Erfasst:** {entry.get('timestamp', '')}\n\n"
            f"## Engineering Problem\n"
            f"{entry.get('problem', '')}\n\n"
            f"## Begruendung\n"
            f"{entry.get('text', '')}\n\n"
            f"## Rohtext\n"
            f"{entry.get('raw_text', '')[:500]}\n\n"
            f"---\n"
            f"*Automatisch generiert von COGNITUM AnalogyExtractor*"
        )
        return title, content

    def format_adr(self, case_result: dict) -> Tuple[str, str]:
        """Gibt (title, content) fuer ein SPALTEN ADR-Ergebnis zurueck."""
        problem = case_result.get("problem", "ADR")
        title = f"ADRs/{problem[:60]}"

        lessons = case_result.get("lessons", [])
        lessons_md = "\n".join(f"- {l}" for l in lessons) if lessons else "- Keine"

        content = (
            f"# {problem[:80]}\n\n"
            f"**Score:** {case_result.get('overall_score', 0.0):.2f}  \n"
            f"**Erfasst:** {case_result.get('timestamp', '')}\n\n"
            f"## Problem\n"
            f"{problem}\n\n"
            f"## Loesung\n"
            f"{case_result.get('solution', '')}\n\n"
            f"## Lessons Learned\n"
            f"{lessons_md}\n\n"
            f"---\n"
            f"*Automatisch generiert von COGNITUM SPALTEN-Agent*"
        )
        return title, content
