"""
governance/analogy_extractor.py
Cross-Domain Analogical Reasoning Extraktor fuer COGNITUM/DaySensOS.
"""
import json
import logging
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

OLLAMA_BASE = "http://localhost:11434"
REPO_ROOT = Path(__file__).resolve().parents[1]
BOT_QUEUE_FILE = REPO_ROOT / ".bot_queue.json"


class AnalogyExtractor:

    SYSTEM_PROMPT = """Du bist ein Experte fuer Cross-Domain Analogical
  Reasoning. Du analysierst beliebige Texte aus Biologie, Physik,
  Geschichte, Wirtschaft, Natur oder Kunst und extrahierst
  Engineering-Prinzipien die auf Software-Architektur, KI-Systeme
  oder Produktentwicklung anwendbar sind.

  Frage dich immer:
  - Was ist das zugrundeliegende abstrakte Prinzip?
  - Wie loest dieses System sein Problem?
  - Welches Engineering-Problem hat dieselbe Struktur?
  - Was koennte COGNITUM oder DaySensOS davon lernen?

  Antworte NUR mit validem JSON (keine Erklaerungen davor/danach):
  [
    {
      "prinzip": "Name des abstrakten Prinzips",
      "quelle": "Biologie/Physik/Geschichte/etc.",
      "engineering_problem": "Konkretes Problem fuer COGNITUM/DaySensOS",
      "domain": "cognitum oder daysensos oder eu_ai_act oder general",
      "urgency": "low oder medium oder high",
      "begruendung": "Warum ist diese Analogie valide? (max 2 Saetze)"
    }
  ]
  Maximal 3 Analogien. Nur valide, konkrete Analogien — keine generischen."""

    def extract(self, text: str, source_domain: str = "unknown") -> List[dict]:
        """Calls Ollama qwen2.5:7b, returns list of validated analogy dicts."""
        prompt = (
            f"Quell-Domain: {source_domain}\n\n"
            f"Text:\n{text[:2000]}\n\n"
            "Extrahiere maximal 3 Cross-Domain Analogien als Engineering-Prinzipien."
        )
        payload = json.dumps({
            "model": "qwen2.5:7b",
            "system": self.SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.4},
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                f"{OLLAMA_BASE}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw = data.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama-Fehler in AnalogyExtractor: {e}")
            return []

        return self._validate(self._parse_json(raw))

    def _parse_json(self, raw: str) -> list:
        """Extracts JSON array from raw LLM response."""
        try:
            result = json.loads(raw)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            try:
                result = json.loads(m.group())
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        logger.debug(f"Kein valides JSON-Array gefunden: {raw[:200]}")
        return []

    def _validate(self, analogies: list) -> List[dict]:
        """Keeps only dicts that have both prinzip and engineering_problem."""
        valid = []
        for item in analogies:
            if not isinstance(item, dict):
                continue
            if item.get("prinzip") and item.get("engineering_problem"):
                valid.append(item)
        return valid[:3]

    def extract_and_queue(
        self, text: str, source_url: str = "", title: str = ""
    ) -> int:
        """Extracts analogies and appends each as a problem-dict to .bot_queue.json."""
        analogies = self.extract(text)
        if not analogies:
            return 0

        queue: list = []
        if BOT_QUEUE_FILE.exists():
            try:
                queue = json.loads(BOT_QUEUE_FILE.read_text(encoding="utf-8"))
            except Exception:
                queue = []

        now = datetime.now(timezone.utc).isoformat()
        for analogy in analogies:
            prinzip = analogy.get("prinzip", "")
            eng_problem = analogy.get("engineering_problem", "")
            queue.append({
                "text": f"{prinzip}: {eng_problem}",
                "source_type": "analogy_extraction",
                "source_url": source_url,
                "title": prinzip,
                "metadata": {
                    "quelle": analogy.get("quelle", ""),
                    "domain": analogy.get("domain", "general"),
                    "urgency": analogy.get("urgency", "medium"),
                    "begruendung": analogy.get("begruendung", ""),
                    "original_title": title,
                },
                "source": "analogy_extraction",
                "problem": eng_problem,
                "domain": analogy.get("domain", "general"),
                "urgency": analogy.get("urgency", "medium"),
                "queued_at": now,
                "priority": 1,
            })

        BOT_QUEUE_FILE.write_text(
            json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info(f"AnalogyExtractor: {len(analogies)} Analogien in Queue gespeichert")
        return len(analogies)
