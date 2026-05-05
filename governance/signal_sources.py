#!/usr/bin/env python3
"""
governance/signal_sources.py
RealSignalFetcher — 5 echte Signal-Quellen fuer COGNITUM Engineering Loop
Nur stdlib + yaml (KEIN requests, KEIN feedparser, KEIN beautifulsoup4, kein LangGraph)
"""
import json
import re
import time
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

REPO_ROOT = Path(__file__).resolve().parents[1]
MASTERPLAN_PATH = REPO_ROOT / "governance" / "masterplan.yaml"
GITLAB_TOKEN_FILE = Path.home() / ".gitlab-token"
GITHUB_TOKEN_FILE = Path.home() / ".github-token"
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"


# ─── Interne Hilfsfunktionen ──────────────────────────────────────────────────

def _read_token(path: Path) -> Optional[str]:
    """Liest ersten nicht-leeren Wert aus Token-Datei."""
    try:
        text = path.read_text(encoding="utf-8").strip()
        token = text.splitlines()[0].strip()
        return token if token else None
    except Exception:
        return None


def _http_get(url: str, headers: dict = None, timeout: int = 15) -> Optional[str]:
    """HTTP GET via urllib — gibt Body-Text oder None zurueck."""
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _llm_call(prompt: str, system: str = None, timeout: int = 60) -> str:
    """Lokaler Ollama LLM-Aufruf via urllib — kein externes SDK."""
    sys_msg = system or (
        "Du bist ein Engineering-Analyst nach VDI 2221. "
        "Antworte praezise auf Deutsch. Max. 80 Woerter."
    )
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user",   "content": prompt},
        ],
        "options": {"temperature": 0.2},
        "stream": False,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            OLLAMA_URL, data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["message"]["content"].strip()
    except Exception as e:
        return f"[SIMULATION] Ollama nicht erreichbar: {e}"


# ─── RealSignalFetcher ────────────────────────────────────────────────────────

class RealSignalFetcher:
    """
    Holt Engineering-Signale aus 5 echten Quellen.
    Nur stdlib + yaml — kein requests, feedparser, bs4, LangGraph.
    """

    # ── 1. GitHub Issues ──────────────────────────────────────────────────────

    def fetch_github_issues(self, repo: str) -> List[dict]:
        """
        GitHub Issues via REST API.
        Kein Token fuer public repos noetig; Token aus ~/.github-token fuer private.
        GET https://api.github.com/repos/<repo>/issues?state=open&per_page=10
        """
        url = (
            f"https://api.github.com/repos/{repo}/issues"
            "?state=open&per_page=10"
        )
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "COGNITUM-Agent/1.0",
        }
        token = _read_token(GITHUB_TOKEN_FILE)
        if token:
            headers["Authorization"] = f"token {token}"

        body = _http_get(url, headers, timeout=15)
        if not body:
            return []
        try:
            data = json.loads(body)
            if not isinstance(data, list):
                return []
            result = []
            for issue in data:
                result.append({
                    "title":  issue.get("title", ""),
                    "body":   (issue.get("body") or "")[:500],
                    "labels": [lb["name"] for lb in issue.get("labels", [])],
                    "url":    issue.get("html_url", ""),
                    "source": "github",
                    "domain": "engineering",
                    "date":   issue.get("created_at", ""),
                })
            return result
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    # ── 2. GitLab Issues ─────────────────────────────────────────────────────

    def fetch_gitlab_issues(self, project_path: str) -> List[dict]:
        """
        GitLab Issues via REST API mit Token aus ~/.gitlab-token.
        GET https://gitlab.com/api/v4/projects/<encoded>/issues?state=opened
        project_path kann '/' oder '%2F' als Trenner enthalten.
        """
        token = _read_token(GITLAB_TOKEN_FILE)
        if not token:
            return []

        # Normalisierung: doppeltes URL-Encoding vermeiden
        normalized = urllib.parse.unquote(project_path)
        encoded = urllib.parse.quote(normalized, safe="")
        url = (
            f"https://gitlab.com/api/v4/projects/{encoded}/issues"
            "?state=opened&per_page=10&order_by=updated_at"
        )
        headers = {
            "PRIVATE-TOKEN": token,
            "User-Agent": "COGNITUM-Agent/1.0",
        }

        body = _http_get(url, headers, timeout=15)
        if not body:
            return []
        try:
            data = json.loads(body)
            if not isinstance(data, list):
                return []
            result = []
            for issue in data:
                result.append({
                    "title":       issue.get("title", ""),
                    "description": (issue.get("description") or "")[:500],
                    "labels":      issue.get("labels", []),
                    "web_url":     issue.get("web_url", ""),
                    "source":      "gitlab",
                    "domain":      "engineering",
                    "date":        issue.get("updated_at", ""),
                })
            return result
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    # ── 3. Masterplan Decisions ───────────────────────────────────────────────

    def fetch_masterplan_decisions(self) -> List[dict]:
        """
        Liest governance/masterplan.yaml.
        Findet ADRs mit status != 'accepted', proposed Module, proposed Risiken.
        Gibt {problem, domain, source: 'masterplan'} zurueck.
        """
        if not MASTERPLAN_PATH.exists():
            return []

        if not _HAS_YAML:
            return [{
                "title":   "PyYAML nicht verfuegbar",
                "problem": "masterplan.yaml vorhanden aber PyYAML fehlt",
                "domain":  "governance",
                "source":  "masterplan",
                "date":    "",
                "status":  "error",
            }]

        try:
            with open(MASTERPLAN_PATH, encoding="utf-8") as f:
                plan = _yaml.safe_load(f)
        except Exception as e:
            return [{
                "title":   "masterplan.yaml Fehler",
                "problem": f"Kann masterplan.yaml nicht lesen: {e}",
                "domain":  "governance",
                "source":  "masterplan",
                "date":    "",
                "status":  "error",
            }]

        results = []

        # ADRs mit status != accepted (deprecated, proposed, draft, ...)
        for adr in plan.get("adrs", []):
            status = adr.get("status", "unknown")
            if status != "accepted":
                adr_id  = adr.get("id", "?")
                title   = adr.get("title", "Unbekannt")
                context = (adr.get("context") or "")[:200]
                results.append({
                    "title":   f"{adr_id}: {title}",
                    "problem": (
                        f"ADR {adr_id} hat Status '{status}': {title}. "
                        f"Kontext: {context}"
                    ),
                    "domain":  "governance",
                    "source":  "masterplan",
                    "date":    str(adr.get("date", "")),
                    "status":  status,
                })

        # Module mit status == proposed (noch nicht implementiert)
        for mod in plan.get("modules", []):
            if mod.get("status") == "proposed":
                mod_id = mod.get("id", "?")
                name   = mod.get("name", "Unbekannt")
                desc   = (mod.get("description") or "")[:200]
                layer  = mod.get("layer", "?")
                results.append({
                    "title":   f"Modul {mod_id} ({name}) proposed",
                    "problem": (
                        f"Modul '{name}' (Layer {layer}) noch nicht implementiert: {desc}"
                    ),
                    "domain":  str(layer),
                    "source":  "masterplan",
                    "date":    "",
                    "status":  "proposed",
                })

        # Risiken mit status == proposed (Mitigation noch ausstehend)
        for risk in plan.get("iso_23894_risks", []):
            if risk.get("status") == "proposed":
                risk_id = risk.get("id", "?")
                desc    = (risk.get("description") or "")[:200]
                mit     = (risk.get("mitigation")  or "")[:150]
                results.append({
                    "title":   f"{risk_id}: {desc[:60]}",
                    "problem": (
                        f"Risiko {risk_id} noch nicht vollstaendig mitigiert: {desc}. "
                        f"Geplante Massnahme: {mit}"
                    ),
                    "domain":  "risk_management",
                    "source":  "masterplan",
                    "date":    "",
                    "status":  "proposed",
                })

        # ISO 25010 Sub-Charakteristika mit status == proposed
        for cat in plan.get("iso_25010", []):
            for sub in cat.get("sub_characteristics", []):
                if sub.get("status") == "proposed":
                    sub_name = sub.get("name", "?")
                    notes    = (sub.get("notes") or "")[:150]
                    results.append({
                        "title":   f"ISO 25010: {sub_name} (proposed)",
                        "problem": (
                            f"Qualitaetsmerkmal '{sub_name}' noch nicht umgesetzt: {notes}"
                        ),
                        "domain":  "quality",
                        "source":  "masterplan",
                        "date":    "",
                        "status":  "proposed",
                    })

        return results

    # ── 4. Regulatory Updates via RSS ─────────────────────────────────────────

    # Keywords die Eintraege disqualifizieren (Militaer, Waffen, Krieg)
    _BLOCKLIST = {
        "militär", "militar", "military", "waffen", "weapons", "rüstung",
        "ruestung", "defense", "defence", "krieg", "war", "bundeswehr",
        "nato", "rüstungsexport", "ruestungsexport",
    }

    # Mindestens eines dieser Keywords muss im Eintrag vorkommen (Relevanz-Filter)
    _ALLOWLIST = {
        "ki", "ai", "software", "digital", "daten", "data", "compliance",
        "engineering", "sensor", "app", "tech", "norm", "recht", "regulation",
        "datenschutz", "privacy", "algorithmus", "algorithm", "it", "cloud",
        "security", "sicherheit", "api", "system", "plattform", "platform",
    }

    def _is_relevant(self, title: str, desc: str) -> bool:
        """Gibt True zurueck wenn Eintrag relevant und nicht verboten ist.
        Nutzt Wortgrenze-Matching um False-Positives wie 'war' in 'software' zu vermeiden."""
        combined = (title + " " + desc).lower()
        # Blocklist — ganzes Wort matchen (Wortgrenzen)
        for kw in self._BLOCKLIST:
            if re.search(r'\b' + re.escape(kw) + r'\b', combined):
                return False
        # Allowlist — mindestens ein ganzes Wort matchen
        for kw in self._ALLOWLIST:
            if re.search(r'\b' + re.escape(kw) + r'\b', combined):
                return True
        return False

    def fetch_regulatory_updates(self) -> List[dict]:
        """
        RSS-Feeds fuer EU AI Act, BAFA und Heise (IT-Engineering-Kontext).
        Nutzt feedparser wenn verfuegbar, sonst xml.etree + Regex-Fallback.
        Graceful: nicht erreichbare Feeds werden geloggt und uebersprungen.
        Filtert nicht-relevante und militaerbezogene Eintraege heraus.
        """
        try:
            import feedparser as _fp
            _HAS_FEEDPARSER = True
        except ImportError:
            _fp = None
            _HAS_FEEDPARSER = False

        feeds = [
            (
                "https://eur-lex.europa.eu/search.html"
                "?qid=1&text=AI+Act&type=advanced&lang=de&format=rss",
                "eu_ai_act",
            ),
            (
                "https://www.bafa.de/SiteGlobals/Frontend/"
                "InformationService/Rss/EN/bafa_rss.xml",
                "bafa_regulatory",
            ),
            (
                "https://www.heise.de/rss/heise-atom.xml",
                "it_news_de",
            ),
        ]
        results = []

        for feed_url, domain in feeds:
            # feedparser-Pfad (bevorzugt, robuster bei Atom/RSS-Varianten)
            if _HAS_FEEDPARSER:
                try:
                    import socket
                    old_timeout = socket.getdefaulttimeout()
                    socket.setdefaulttimeout(15)
                    try:
                        parsed = _fp.parse(feed_url)
                    finally:
                        socket.setdefaulttimeout(old_timeout)

                    if not parsed.entries:
                        print(f"  ⚠️  RSS-Feed leer oder nicht erreichbar: {feed_url}")
                        continue

                    for entry in parsed.entries[:20]:
                        title = (getattr(entry, "title", "") or "").strip()
                        desc  = (getattr(entry, "summary", "") or
                                 getattr(entry, "description", "") or "").strip()
                        desc  = re.sub(r"<[^>]+>", "", desc)[:300]
                        date  = (getattr(entry, "published", "") or
                                 getattr(entry, "updated", "") or "")
                        link  = getattr(entry, "link", feed_url)

                        if not title:
                            continue
                        if not self._is_relevant(title, desc):
                            continue
                        results.append({
                            "title":   title,
                            "problem": f"Regulatorisches Update: {title}. {desc}",
                            "domain":  domain,
                            "source":  feed_url,
                            "date":    date,
                            "url":     link or feed_url,
                        })
                        if len(results) >= 5 * len(feeds):
                            break
                    continue  # feedparser hat Feed erfolgreich verarbeitet
                except Exception as e:
                    print(f"  ⚠️  feedparser Fehler fuer {feed_url}: {e} — versuche stdlib")

            # stdlib-Fallback (xml.etree + Regex)
            body = _http_get(
                feed_url,
                headers={"User-Agent": "COGNITUM-Agent/1.0"},
                timeout=15,
            )
            if not body:
                print(f"  ⚠️  RSS-Feed nicht erreichbar (Timeout/Fehler): {feed_url}")
                continue

            try:
                body_clean = re.sub(
                    r'\s+xmlns(?::[a-z0-9]+)?=["\'][^"\']*["\']', '', body
                )
                root = ET.fromstring(body_clean)
                items = root.findall(".//item") or root.findall(".//entry")

                for item in items[:20]:
                    title_el = item.find("title")
                    desc_el  = item.find("description") or item.find("summary")
                    date_el  = (item.find("pubDate") or item.find("published")
                                or item.find("updated"))
                    link_el  = item.find("link")

                    title = (title_el.text or "").strip() if title_el is not None else ""
                    desc  = (desc_el.text  or "").strip() if desc_el  is not None else ""
                    desc  = re.sub(r"<[^>]+>", "", desc)[:300]
                    date  = (date_el.text  or "").strip() if date_el  is not None else ""
                    link  = ""
                    if link_el is not None:
                        link = (link_el.text or link_el.get("href", "")).strip()

                    if not title:
                        continue
                    if not self._is_relevant(title, desc):
                        continue

                    results.append({
                        "title":   title,
                        "problem": f"Regulatorisches Update: {title}. {desc}",
                        "domain":  domain,
                        "source":  feed_url,
                        "date":    date,
                        "url":     link or feed_url,
                    })

            except ET.ParseError:
                titles = re.findall(
                    r"<title[^>]*>(.*?)</title>", body, re.DOTALL | re.IGNORECASE
                )
                for raw_t in titles[1:21]:
                    clean = re.sub(r"<[^>]+>", "", raw_t).strip()
                    if clean and self._is_relevant(clean, ""):
                        results.append({
                            "title":   clean,
                            "problem": f"Regulatorisches Update ({domain}): {clean}",
                            "domain":  domain,
                            "source":  feed_url,
                            "date":    datetime.now(timezone.utc).isoformat(),
                            "url":     feed_url,
                        })

        return results

    # ── 5. Market Signals via DuckDuckGo Lite ────────────────────────────────

    def fetch_market_signals(self, queries: List[str] = None) -> List[dict]:
        """
        DuckDuckGo Lite Search — kein API-Key noetig.
        LLM extrahiert Engineering-Probleme aus HTML-Snippets.
        """
        if queries is None:
            queries = [
                "EU AI Act compliance tools 2026",
                "VDI 2221 software engineering",
                "DSGVO AI engineering Germany",
            ]

        results = []

        for query in queries:
            encoded_q = urllib.parse.quote_plus(query)
            url = f"https://lite.duckduckgo.com/lite/?q={encoded_q}"
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0 Safari/537.36"
                ),
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml",
            }

            body = _http_get(url, headers, timeout=15)
            if not body:
                continue

            # DDG Lite: <td class="result-snippet">...</td>
            snippets = re.findall(
                r'<td[^>]*class=["\'][^"\']*result-snippet[^"\']*["\'][^>]*>(.*?)</td>',
                body, re.DOTALL | re.IGNORECASE,
            )
            if not snippets:
                # Fallback: Alle <td>-Inhalte mit signifikantem Text
                snippets = re.findall(r'<td[^>]*>(.*?)</td>', body, re.DOTALL)
                snippets = [s for s in snippets
                            if len(re.sub(r"<[^>]+>", "", s).strip()) > 30]

            clean = [
                re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s).strip())[:200]
                for s in snippets[:6]
            ]
            clean = [s for s in clean if s]

            if not clean:
                continue

            snippet_text = "\n".join(f"- {s}" for s in clean[:5])
            problem = self._extract_engineering_problem(query, snippet_text)

            results.append({
                "title":   query,
                "problem": problem,
                "domain":  "market_intelligence",
                "source":  "web",
                "date":    datetime.now(timezone.utc).isoformat(),
                "url":     url,
                "query":   query,
            })

            time.sleep(1)  # Rate-Limiting

        return results

    def _extract_engineering_problem(self, query: str, snippets: str) -> str:
        """LLM extrahiert konkretes Engineering-Problem aus Web-Snippets."""
        prompt = (
            f"Suchanfrage: {query}\n\nWeb-Snippets:\n{snippets}\n\n"
            "Formuliere daraus ein konkretes Engineering-Problem fuer "
            "COGNITUM/DaySensOS (Privacy-First Wearable AI OS). "
            "Nur den Problemsatz, max. 80 Woerter."
        )
        result = _llm_call(prompt, timeout=60)
        if result.startswith("[SIMULATION]"):
            return f"Markt-Signal '{query}': {snippets[:120]}"
        return result

    # ── 6. BSI CERT-Bund Feeds ────────────────────────────────────────────────

    def fetch_bsi_feeds(self) -> List[dict]:
        """BSI / CERT-Bund RSS-Feeds via feedparser."""
        try:
            import feedparser as _fp
        except ImportError:
            print("  ⚠️  feedparser nicht verfuegbar fuer BSI-Feeds")
            return []

        urls = [
            "https://www.bsi.bund.de/SharedDocs/Abonnements/DE/RSSFeeds/rss_node.html",
            "https://www.bsi.bund.de/DE/Service-Navi/Abonnements/RSS/rss_node.html",
        ]
        results: List[dict] = []
        for url in urls:
            try:
                import socket
                old_to = socket.getdefaulttimeout()
                socket.setdefaulttimeout(15)
                try:
                    parsed = _fp.parse(url)
                finally:
                    socket.setdefaulttimeout(old_to)

                if not parsed.entries:
                    print(f"  ⚠️  BSI Feed leer oder nicht erreichbar: {url}")
                    continue

                for entry in parsed.entries[:15]:
                    title = (getattr(entry, "title", "") or "").strip()
                    summary = re.sub(
                        r"<[^>]+>", "",
                        (getattr(entry, "summary", "") or "")
                    ).strip()[:300]
                    if not title:
                        continue
                    results.append({
                        "title":   title,
                        "problem": f"BSI Sicherheitshinweis: {title}. {summary}",
                        "domain":  "security_bsi",
                        "source":  url,
                        "date":    (getattr(entry, "published", "")
                                    or getattr(entry, "updated", "")),
                        "url":     getattr(entry, "link", url),
                    })
            except Exception as e:
                print(f"  ⚠️  BSI Feed Fehler ({url}): {e}")

        return results

    # ── 7. arXiv ─────────────────────────────────────────────────────────────

    def fetch_arxiv(
        self,
        categories: List[str] = None,
        max_results: int = 10,
    ) -> List[dict]:
        """arXiv Atom-Feed — feedparser bevorzugt, stdlib-Fallback mit Namespace-Stripping."""
        if categories is None:
            categories = ["cs.AI", "cs.SE", "cs.LG"]

        try:
            import feedparser as _fp
            _use_fp = True
        except ImportError:
            _fp = None
            _use_fp = False

        results: List[dict] = []
        for cat in categories:
            url = (
                f"http://export.arxiv.org/api/query"
                f"?search_query=cat:{cat}"
                f"&max_results={max_results}"
                f"&sortBy=submittedDate"
            )
            # ── feedparser-Pfad ───────────────────────────────────────────────
            if _use_fp:
                try:
                    import socket
                    old_to = socket.getdefaulttimeout()
                    socket.setdefaulttimeout(20)
                    try:
                        parsed = _fp.parse(url)
                    finally:
                        socket.setdefaulttimeout(old_to)
                    for entry in parsed.entries[:max_results]:
                        title = re.sub(r"\s+", " ", (getattr(entry, "title", "") or "").strip())
                        summary = re.sub(r"<[^>]+>", "", (getattr(entry, "summary", "") or "")).strip()[:400]
                        summary = re.sub(r"\s+", " ", summary)
                        link = getattr(entry, "link", "") or (getattr(entry, "id", "") or "")
                        published = getattr(entry, "published", "") or getattr(entry, "updated", "")
                        if not title:
                            continue
                        results.append({
                            "title":   title,
                            "problem": f"arXiv {cat}: {title}. {summary[:200]}",
                            "domain":  f"research_{cat.replace('.', '_').lower()}",
                            "source":  "arxiv",
                            "date":    published,
                            "url":     link,
                        })
                    continue
                except Exception as e:
                    print(f"  ⚠️  arXiv feedparser Fehler ({cat}): {e} — stdlib-Fallback")

            # ── stdlib-Fallback mit aggressivem Namespace-Stripping ───────────
            body = _http_get(url, headers={"User-Agent": "COGNITUM-Agent/1.0"}, timeout=20)
            if not body:
                print(f"  ⚠️  arXiv {cat} nicht erreichbar")
                continue
            try:
                # Entferne xmlns-Deklarationen UND geprefixte Elemente (z.B. opensearch:*)
                body_clean = re.sub(r'\s+xmlns(?::[a-zA-Z0-9]+)?=["\'][^"\']*["\']', "", body)
                body_clean = re.sub(r'</?[a-zA-Z][a-zA-Z0-9]*:[a-zA-Z][^>]*>', "", body_clean)
                root = ET.fromstring(body_clean)
                atom_ns = "{http://www.w3.org/2005/Atom}"
                entries = root.findall(f"{atom_ns}entry") or root.findall(".//entry")
                for entry in entries[:max_results]:
                    def _txt(tag: str) -> str:
                        el = entry.find(f"{atom_ns}{tag}") or entry.find(tag)
                        return (el.text or "").strip() if el is not None else ""
                    title = re.sub(r"\s+", " ", _txt("title"))
                    summary = re.sub(r"\s+", " ", _txt("summary"))[:400]
                    link = ""
                    for lel in list(entry.findall(f"{atom_ns}link")) + list(entry.findall("link")):
                        if lel.get("rel", "") == "alternate":
                            link = lel.get("href", "")
                            break
                    if not link:
                        link = _txt("id")
                    published = _txt("published")
                    if not title:
                        continue
                    results.append({
                        "title":   title,
                        "problem": f"arXiv {cat}: {title}. {summary[:200]}",
                        "domain":  f"research_{cat.replace('.', '_').lower()}",
                        "source":  "arxiv",
                        "date":    published,
                        "url":     link,
                    })
            except ET.ParseError as e:
                print(f"  ⚠️  arXiv XML-Fehler ({cat}): {e}")

        return results

    # ── 8. Heise Developer ────────────────────────────────────────────────────

    def fetch_heise(self) -> List[dict]:
        """Heise Developer Atom-Feed via feedparser."""
        try:
            import feedparser as _fp
        except ImportError:
            return []

        # Spec-URL zuerst; Fallback falls 404
        urls_to_try = [
            "https://www.heise.de/rss/heise-developer-atom.xml",
            "https://www.heise.de/rss/heise-atom.xml",
        ]
        results: List[dict] = []
        active_url = urls_to_try[0]
        parsed = None
        for candidate in urls_to_try:
            try:
                import socket
                old_to = socket.getdefaulttimeout()
                socket.setdefaulttimeout(10)
                try:
                    _parsed = _fp.parse(candidate)
                finally:
                    socket.setdefaulttimeout(old_to)
                if _parsed.entries:
                    parsed = _parsed
                    active_url = candidate
                    break
            except Exception as e:
                print(f"  ⚠️  Heise Feed Fehler ({candidate}): {e}")

        if not parsed or not parsed.entries:
            print("  ⚠️  Heise Feed leer: alle URLs erschoepft")
            return []

        for entry in parsed.entries[:20]:
            title = (getattr(entry, "title", "") or "").strip()
            summary = re.sub(
                r"<[^>]+>", "",
                (getattr(entry, "summary", "") or "")
            ).strip()[:300]
            if not title:
                continue
            results.append({
                "title":   title,
                "problem": f"Heise Developer: {title}. {summary}",
                "domain":  "it_news_de",
                "source":  active_url,
                "date":    (getattr(entry, "published", "")
                            or getattr(entry, "updated", "")),
                "url":     getattr(entry, "link", active_url),
            })

        return results

    # ── 9. EDPB ──────────────────────────────────────────────────────────────

    def fetch_edpb(self) -> List[dict]:
        """European Data Protection Board News via feedparser."""
        try:
            import feedparser as _fp
        except ImportError:
            return []

        url = "https://www.edpb.europa.eu/edpb/api/feeds/news_en"
        results: List[dict] = []
        try:
            import socket
            old_to = socket.getdefaulttimeout()
            socket.setdefaulttimeout(10)
            try:
                parsed = _fp.parse(url)
            finally:
                socket.setdefaulttimeout(old_to)

            if not parsed.entries:
                print(f"  ⚠️  EDPB Feed leer: {url}")
                return []

            for entry in parsed.entries[:15]:
                title = (getattr(entry, "title", "") or "").strip()
                summary = re.sub(
                    r"<[^>]+>", "",
                    (getattr(entry, "summary", "") or "")
                ).strip()[:300]
                if not title:
                    continue
                results.append({
                    "title":   title,
                    "problem": f"EDPB Datenschutz-News: {title}. {summary}",
                    "domain":  "regulatory_edpb",
                    "source":  url,
                    "date":    (getattr(entry, "published", "")
                                or getattr(entry, "updated", "")),
                    "url":     getattr(entry, "link", url),
                })
        except Exception as e:
            print(f"  ⚠️  EDPB Feed Fehler: {e}")

        return results

    # ── 10. Product Hunt ─────────────────────────────────────────────────────

    def fetch_product_hunt(self) -> List[dict]:
        """Product Hunt via RSS-Feed (kein API-Key noetig)."""
        try:
            import feedparser as _fp
        except ImportError:
            return []

        url = "https://www.producthunt.com/feed"
        results: List[dict] = []
        try:
            import socket
            old_to = socket.getdefaulttimeout()
            socket.setdefaulttimeout(10)
            try:
                parsed = _fp.parse(url)
            finally:
                socket.setdefaulttimeout(old_to)

            if not parsed.entries:
                return []

            for entry in parsed.entries[:15]:
                title = (getattr(entry, "title", "") or "").strip()
                summary = re.sub(
                    r"<[^>]+>", "",
                    (getattr(entry, "summary", "") or "")
                ).strip()[:300]
                if not title:
                    continue
                results.append({
                    "title":   title,
                    "problem": f"Product Hunt Launch: {title}. {summary}",
                    "domain":  "market_product_hunt",
                    "source":  url,
                    "date":    (getattr(entry, "published", "")
                                or getattr(entry, "updated", "")),
                    "url":     getattr(entry, "link", url),
                })
        except Exception as e:
            print(f"  ⚠️  Product Hunt Feed Fehler (erwartet wenn 401): {e}")

        return results

    _GENESIS_PATH = Path.home() / "Documents" / "OMNI_GENESIS" / "10-Projects" / \
                    "OMNI_REACTOR" / "Genesis-Graph" / "Genesis-Graph-Index.md"
    _GENESIS_SAFE_CATEGORIES = {"Theorem", "Constraint", "IPFragment",
                                 "MarketSignal", "MarktSignal"}
    _GENESIS_IGNORE_CATEGORIES = {"CodeModule", "Schema", "Product",
                                   "Produkt", "Prozess"}
    _GENESIS_AGENT_KW = {"halal", "islamic", "compliance", "ethic",
                          "shari", "zakat", "veri", "zkp"}

    def _fetch_genesis_graph(self) -> List[str]:
        """Liest Genesis-Graph-Index.md und extrahiert relevante [[Name]]-Eintraege.
        Alle 10 Batches refreshen (via COGNITUM_BATCH_NUM env)."""
        if not self._GENESIS_PATH.exists():
            return []
        import random as _random
        results: List[str] = []
        seen: set = set()
        try:
            text    = self._GENESIS_PATH.read_text(encoding="utf-8")
            current = ""
            for line in text.splitlines():
                header = re.match(r"^##\s+(\w+)", line)
                if header:
                    current = header.group(1)
                    continue
                if current in self._GENESIS_IGNORE_CATEGORIES:
                    continue
                m = re.search(r"\[\[([^\]]+)\]\]", line)
                if not m:
                    continue
                raw_name = m.group(1).strip()
                if raw_name in seen:
                    continue
                seen.add(raw_name)

                name = re.sub(rf"^{re.escape(current)}_", "", raw_name)

                if current in self._GENESIS_SAFE_CATEGORIES:
                    results.append(
                        f"Genesis-Graph: {current} — {name}: "
                        f"Architekturentscheidung fuer {name} in COGNITUM"
                    )
                elif current == "AgentPersona":
                    if any(kw in name.lower() for kw in self._GENESIS_AGENT_KW):
                        results.append(
                            f"Genesis-Graph: AgentPersona — {name}: "
                            f"Architekturentscheidung fuer {name} in COGNITUM"
                        )
        except Exception as e:
            print(f"  ⚠️  Genesis-Graph Fehler: {e}")
        _random.shuffle(results)
        return results[:20]

    _EU_RESEARCH_KEYWORDS = {
        "ai", "artificial intelligence", "digital", "regulation",
        "compliance", "innovation", "funding", "horizon",
    }
    _EU_RESEARCH_FEEDS = [
        "https://digital-strategy.ec.europa.eu/en/rss.xml",
        "https://ec.europa.eu/commission/presscorner/api/rss?lang=en&type=IP",
    ]

    def _fetch_eu_research(self) -> List[str]:
        """EU Digital Strategy & Commission RSS — feedparser, max 10 relevante Signale."""
        results: List[str] = []
        try:
            import feedparser as _fp
            import socket
            old_to = socket.getdefaulttimeout()
            socket.setdefaulttimeout(12)
            try:
                for feed_url in self._EU_RESEARCH_FEEDS:
                    if len(results) >= 10:
                        break
                    try:
                        parsed = _fp.parse(feed_url)
                        for entry in parsed.entries[:20]:
                            title   = (getattr(entry, "title",   "") or "").strip()
                            summary = re.sub(
                                r"<[^>]+>",
                                "",
                                (getattr(entry, "summary", "") or ""),
                            ).strip()
                            combined = (title + " " + summary).lower()
                            if any(kw in combined for kw in self._EU_RESEARCH_KEYWORDS):
                                text = f"{title}: {summary[:200]}" if summary else title
                                results.append(text)
                            if len(results) >= 10:
                                break
                    except Exception:
                        pass
            finally:
                socket.setdefaulttimeout(old_to)
        except ImportError:
            pass
        except Exception as e:
            print(f"  ⚠️  EU R&I Fetch Fehler: {e}")
        return results

    # ── fetch_all ─────────────────────────────────────────────────────────────

    def fetch_all(self, repos: List[str] = None) -> List[dict]:
        """
        Aggregiert alle Quellen, filtert via RelevanceFilter (>= 0.6),
        dedupliziert via Titel-Similarity, sortiert nach Recency.
        """
        if repos is None:
            repos = ["fatdinhero/cognitum"]

        # RelevanceFilter laden (Graceful: ohne Filter wenn Import fehlschlaegt)
        try:
            from governance.relevance_filter import RelevanceFilter
            _rf = RelevanceFilter()
        except Exception as e:
            print(f"  ⚠️  RelevanceFilter nicht verfuegbar: {e}")
            _rf = None

        all_signals: List[dict] = []
        source_counts: Dict[str, int] = {}

        # 1. GitHub
        for repo in repos:
            items = self.fetch_github_issues(repo)
            all_signals.extend(items)
            source_counts["github"] = source_counts.get("github", 0) + len(items)

        # 2. GitLab
        for repo in repos:
            gl_path = repo.replace("/", "%2F")
            items = self.fetch_gitlab_issues(gl_path)
            all_signals.extend(items)
            source_counts["gitlab"] = source_counts.get("gitlab", 0) + len(items)

        # 3. Masterplan
        items = self.fetch_masterplan_decisions()
        all_signals.extend(items)
        source_counts["masterplan"] = len(items)

        # 4. BSI / CERT-Bund (ersetzt EUR-Lex/BAFA)
        items = self.fetch_bsi_feeds()
        all_signals.extend(items)
        source_counts["bsi"] = len(items)

        # 5. arXiv
        items = self.fetch_arxiv()
        all_signals.extend(items)
        source_counts["arxiv"] = len(items)

        # 6. Heise Developer
        items = self.fetch_heise()
        all_signals.extend(items)
        source_counts["heise"] = len(items)

        # 7. EDPB
        items = self.fetch_edpb()
        all_signals.extend(items)
        source_counts["edpb"] = len(items)

        # 8. Product Hunt
        items = self.fetch_product_hunt()
        all_signals.extend(items)
        source_counts["product_hunt"] = len(items)

        import os as _os
        _batch_hint = int(_os.environ.get("COGNITUM_BATCH_NUM", "0"))

        # 9. EU Research & Innovation (alle 5 Batches)
        if _batch_hint % 5 == 0:
            eu_texts = self._fetch_eu_research()
            for t in eu_texts:
                all_signals.append({
                    "title":   t[:80],
                    "problem": t,
                    "domain":  "eu_research",
                    "source":  self._EU_RESEARCH_FEEDS[0],
                })
            source_counts["eu_research"] = len(eu_texts)

        # 10. Genesis-Graph (alle 10 Batches — 764 Objekte)
        if _batch_hint % 10 == 0:
            texts = self._fetch_genesis_graph()
            for t in texts:
                all_signals.append({
                    "title":   t[:80],
                    "problem": t,
                    "domain":  "cognitum",
                    "source":  "genesis_graph",
                })
            source_counts["genesis_graph"] = len(texts)

        # 11. Market Signals
        items = self.fetch_market_signals()
        all_signals.extend(items)
        source_counts["web"] = len(items)

        # Relevanz-Filter
        if _rf is not None:
            total = len(all_signals)
            relevant_signals: List[dict] = []
            blocked_count = 0
            for sig in all_signals:
                text = (
                    sig.get("title", "")
                    + " "
                    + sig.get("problem", sig.get("body", sig.get("description", "")))
                )
                result = _rf.score(text.strip())
                sig["relevance_score"] = result["score"]
                if result["score"] == 0.0:
                    blocked_count += 1
                elif result["score"] >= 0.6:
                    relevant_signals.append(sig)
            print(
                f"  Relevanz-Filter: {len(relevant_signals)}/{total} Signale relevant "
                f"({blocked_count} blockiert)"
            )
            all_signals = relevant_signals

        # Deduplizierung
        deduplicated = self._deduplicate(all_signals)

        # Sortierung: neueste Signale zuerst
        def _sort_key(s: dict) -> str:
            d = s.get("date", "")
            return d if isinstance(d, str) and d else "0000"

        deduplicated.sort(key=_sort_key, reverse=True)

        print(f"  Signal-Quellen: {source_counts} | Gesamt (dedupliziert): {len(deduplicated)}")
        return deduplicated

    def _deduplicate(self, signals: List[dict]) -> List[dict]:
        """Deduplizierung via normalisiertem Titel-Praefix (erste 45 Zeichen)."""
        seen: set = set()
        result: List[dict] = []
        for s in signals:
            raw = s.get("title", s.get("problem", ""))
            key = re.sub(r"\s+", " ", str(raw)[:45].lower().strip())
            if key and key not in seen:
                seen.add(key)
                result.append(s)
        return result
