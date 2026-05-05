"""
governance/problem_generator.py
ProblemGenerator — konvertiert echte Signale in SPALTEN-Engineering-Probleme
Echte Signale priorisiert, LLM-generierte nur als Fallback.
"""
import hashlib as _hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import List, Dict, Set, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from governance.signal_sources import RealSignalFetcher, _llm_call

URGENCY_VALUES = {"low", "medium", "high", "critical"}

# 50 konkrete Fallback-Seeds (je 10 pro Domain) — werden genutzt wenn Masterplan-Signale < 3
_SEED_PROBLEMS = [
    # ── eu_ai_act ──
    {"problem": "DaySensOS muss als High-Risk KI-System nach EU AI Act Art. 6 eingestuft werden — Bewertungsverfahren noch nicht definiert", "domain": "eu_ai_act", "urgency": "high"},
    {"problem": "Technische Dokumentation nach EU AI Act Annex IV fehlt fuer alle eingesetzten ML-Modelle in L5-Intelligence", "domain": "eu_ai_act", "urgency": "high"},
    {"problem": "Post-Market Surveillance System nach EU AI Act Art. 72 nicht implementiert — keine automatische Qualitaetsueberwachung", "domain": "eu_ai_act", "urgency": "medium"},
    {"problem": "Logging-System fuer EU AI Act Art. 12 Transparenzanforderungen muss erweitert werden um Entscheidungspfade zu dokumentieren", "domain": "eu_ai_act", "urgency": "medium"},
    {"problem": "Konformitaetsbewertungsverfahren fuer DaySensOS als Wearable-KI nach EU AI Act noch nicht gestartet", "domain": "eu_ai_act", "urgency": "high"},
    {"problem": "EU AI Act Art. 13 erfordert klare Nutzerinformation ueber KI-Entscheidungslogik — Erklaerbarkeits-Modul fehlt", "domain": "eu_ai_act", "urgency": "medium"},
    {"problem": "Robustheitstests nach EU AI Act Art. 15 fuer Sensor-Fusion-Algorithmen nicht durchgefuehrt", "domain": "eu_ai_act", "urgency": "medium"},
    {"problem": "Incident-Reporting-Prozess nach EU AI Act Art. 73 fuer schwerwiegende KI-Fehler nicht vorhanden", "domain": "eu_ai_act", "urgency": "high"},
    {"problem": "Daten-Governance-Framework nach EU AI Act Art. 10 fuer Sensordaten-Trainingspipeline nicht dokumentiert", "domain": "eu_ai_act", "urgency": "medium"},
    {"problem": "EU AI Act Sandbox-Teilnahme fuer DaySensOS pruefen um regulatorische Unsicherheiten fruehzeitig zu klaeren", "domain": "eu_ai_act", "urgency": "low"},
    # ── vdi_compliance ──
    {"problem": "VDI 2221 Systemgestaltung: Anforderungsliste fuer DaySensOS L1-L5 nicht vollstaendig formal spezifiziert", "domain": "vdi_compliance", "urgency": "medium"},
    {"problem": "VDI 2225 Nutzwertanalyse fuer Sensor-Hardware-Auswahl (Accelerometer, GPS, Licht) nicht dokumentiert", "domain": "vdi_compliance", "urgency": "medium"},
    {"problem": "VDI 4500 Technische Dokumentation: Benutzerinformation fuer DaySensOS nicht DIN-EN-konform erstellt", "domain": "vdi_compliance", "urgency": "low"},
    {"problem": "VDI 2206 Entwicklungsmethodik: V-Modell-Konformitaet der SPALTEN-Phasen gegenueber VDI-Phasenmodell nicht geprueft", "domain": "vdi_compliance", "urgency": "medium"},
    {"problem": "VDI 3830 Zuverlässigkeitsnachweis fuer Sensor-Kalibrierprozess in L1 Perception ausstehend", "domain": "vdi_compliance", "urgency": "medium"},
    {"problem": "VDI 2222 Konzipieren: Morphologischer Kasten fuer Consent-Gate-Varianten unvollstaendig — nur 2 von 5 Dimensionen belegt", "domain": "vdi_compliance", "urgency": "low"},
    {"problem": "VDI 6220 Mechatronik-Systemintegration: Schnittstellen zwischen L1-Perception und L2-Situation nicht formal spezifiziert", "domain": "vdi_compliance", "urgency": "medium"},
    {"problem": "VDI 2057 Einwirkung mechanischer Schwingungen: Vibrations-Feedback-Analyse fuer Wearable-Gehaeuse fehlt", "domain": "vdi_compliance", "urgency": "low"},
    {"problem": "VDI 3694 Lastenheft fuer Wearable-Softwareanforderungen nicht nach Norm strukturiert", "domain": "vdi_compliance", "urgency": "medium"},
    {"problem": "VDI 2519 Vorgehensweise Simulation: Sensor-Kalibrier-Simulation fuer verschiedene Umgebungsbedingungen fehlt", "domain": "vdi_compliance", "urgency": "low"},
    # ── dsgvo ──
    {"problem": "Art. 25 DSGVO Privacy by Design: Datenminimierung im L4-Features-Layer nicht vollstaendig umgesetzt — rohe Biometrie-Referenzwerte gespeichert", "domain": "dsgvo", "urgency": "high"},
    {"problem": "Verzeichnis von Verarbeitungstaetigkeiten nach Art. 30 DSGVO fuer alle Sensordatenfluesse fehlt", "domain": "dsgvo", "urgency": "high"},
    {"problem": "Datenschutz-Folgenabschaetzung nach Art. 35 DSGVO fuer Gesundheitsdaten-Verarbeitung durch DayScore ausstehend", "domain": "dsgvo", "urgency": "high"},
    {"problem": "Art. 17 DSGVO Recht auf Loeschung: Cascade-Delete fuer alle Nutzerdaten inkl. SQLite-Episodes und ChromaDB nicht implementiert", "domain": "dsgvo", "urgency": "high"},
    {"problem": "Art. 7 DSGVO Einwilligung: Consent-Widerruf-Mechanismus im Consent-Gate fehlt — Nutzer kann Einwilligung nicht zurueckziehen", "domain": "dsgvo", "urgency": "high"},
    {"problem": "Art. 32 DSGVO Datensicherheit: SQLite-Datenbank mit Episoden-Daten wird unverschluesselt auf Geraet gespeichert", "domain": "dsgvo", "urgency": "medium"},
    {"problem": "Art. 20 DSGVO Datenportabilitaet: Export-Funktion fuer alle Nutzerdaten in maschinenlesbarem Format fehlt", "domain": "dsgvo", "urgency": "medium"},
    {"problem": "Pseudonymisierung der biometrischen Referenzwerte in L4-Features ungenuegend — direkte Rueckfuehrung auf Person moeglich", "domain": "dsgvo", "urgency": "medium"},
    {"problem": "Art. 33 DSGVO Meldepflicht: Incident-Response-Prozess fuer Datenpannen bei Sensordaten nicht definiert", "domain": "dsgvo", "urgency": "medium"},
    {"problem": "DSGVO Art. 13/14 Informationspflichten: Datenschutzerklaerung fuer DaySensOS nicht vollstaendig — fehlende Angaben zu Verarbeitungszwecken", "domain": "dsgvo", "urgency": "medium"},
    # ── cognitum ──
    {"problem": "SPALTEN-Durchlauf erzeugt keine persistenten ADR-Dateien im GitOps-Workflow — Entscheidungen gehen verloren", "domain": "cognitum", "urgency": "high"},
    {"problem": "ChromaDB-Index waechst unbegrenzt — Eviction-Policy und maximale Index-Groesse fuer RAG-Memory fehlen", "domain": "cognitum", "urgency": "medium"},
    {"problem": "Ollama-Fallback-Strategie bei Timeout unzureichend — Autonomous Loop blockiert bei langsamen LLM-Antworten", "domain": "cognitum", "urgency": "medium"},
    {"problem": "RAG-Memory liefert veraltete Kontexte — TTL-Mechanismus fuer Vektor-Embeddings nicht implementiert", "domain": "cognitum", "urgency": "medium"},
    {"problem": "Evaluator-Scores werden nicht persistent gespeichert — Trending-Analyse und Qualitaets-KPIs ueber Zeit unmoeglich", "domain": "cognitum", "urgency": "medium"},
    {"problem": "ProblemGenerator erzeugt Duplikate bei erschoepften Masterplan-Signalen — Hash-basiertes Dedup auf Signal-Ebene fehlt", "domain": "cognitum", "urgency": "low"},
    {"problem": "SPALTEN-Metriken werden nicht in Prometheus-kompatibles Format exportiert — kein Monitoring-Stack moeglich", "domain": "cognitum", "urgency": "low"},
    {"problem": "Autonomous Loop hat kein Backpressure-Mechanismus — bei hoher Last kein Throttling", "domain": "cognitum", "urgency": "medium"},
    {"problem": "GitOps-Handler erstellt Branches ohne automatischen Merge-Request — manuelle Nacharbeit fuer jeden ADR noetig", "domain": "cognitum", "urgency": "low"},
    {"problem": "MCP-Server-Integration mit gbrain wird nicht fuer Wissens-Persistenz genutzt — doppelte Datenhaltung", "domain": "cognitum", "urgency": "low"},
    # ── daysensos ──
    {"problem": "8-Kanal Sensorfusion in L1 hat keine Kalibrierungs-Drift-Erkennung — Messgenauigkeit degradiert unbemerkt", "domain": "daysensos", "urgency": "high"},
    {"problem": "SQLite-Episoden-Datenbank hat keinen Backup-Mechanismus bei Geraetwechsel — Nutzerdaten gehen verloren", "domain": "daysensos", "urgency": "medium"},
    {"problem": "DayScore-Berechnung ignoriert zirkadiane Rhythmen bei Nachtschicht-Nutzern — systematisch falsche Bewertungen", "domain": "daysensos", "urgency": "medium"},
    {"problem": "14-Tage-Normalisierung in L4 reagiert zu langsam auf akute Gesundheitsereignisse — Baseline verfaelscht Scoring", "domain": "daysensos", "urgency": "medium"},
    {"problem": "Consent-Gate hat kein Audit-Log ueber Zustimmungs- und Widerrufshistorie — Nachvollziehbarkeit nicht gegeben", "domain": "daysensos", "urgency": "high"},
    {"problem": "WellnessState-Empfehlungen sind nicht lokalisiert — nur Deutsch/Englisch unterstuetzt, keine Mehrsprachigkeit", "domain": "daysensos", "urgency": "low"},
    {"problem": "GPS-Tracking in L1 speichert exakte Koordinaten statt anonymisierter Geozonen — DSGVO-Konflikt", "domain": "daysensos", "urgency": "high"},
    {"problem": "Screen-Time-Sensor erkennt keine App-Kategorien — zu grobe Nutzungsklassifikation fuer praezise Focus-Bewertung", "domain": "daysensos", "urgency": "medium"},
    {"problem": "L5-Intelligence hat keine Erklaerbarkeits-Komponente fuer DayScore-Begruendungen — Black-Box fuer Nutzer", "domain": "daysensos", "urgency": "medium"},
    {"problem": "Accelerometer-basierte Bewegungserkennung unterscheidet nicht zwischen Sport und unkontrolliertem Zittern — False Positives", "domain": "daysensos", "urgency": "medium"},
]

_DOMAIN_PROMPTS = {
    "eu_ai_act":      "EU AI Act Compliance (Art. 6, 10, 12, 13, 15, 72, 73) fuer DaySensOS als Wearable-KI",
    "vdi_compliance": "VDI-Normen (2221, 2225, 2206, 4500, 3830) im Engineering-Prozess von COGNITUM/DaySensOS",
    "dsgvo":          "DSGVO-Datenschutz-Engineering (Art. 7, 17, 20, 25, 30, 32, 33, 35) fuer Sensordaten-Verarbeitung",
    "cognitum":       "COGNITUM-Systemarchitektur: SPALTEN-Loop, RAG-Memory, ChromaDB, GitOps, Autonomous-Loop-Robustheit",
    "daysensos":      "DaySensOS Sensor-App: L1-L5 Pipeline, Consent-Gate, DayScore, Episoden, Privacy-First-Architektur",
}


def _signal_to_problem(signal: dict) -> dict:
    """Konvertiert ein Signal via LLM in ein strukturiertes Engineering-Problem."""
    title = signal.get("title", "")
    body = signal.get(
        "problem",
        signal.get("description", signal.get("body", ""))
    )
    source = signal.get("source", "unknown")
    domain = signal.get("domain", "engineering")

    prompt = (
        f"Signal aus Quelle '{source}':\n"
        f"Titel: {title}\n"
        f"Details: {str(body)[:400]}\n\n"
        "Konvertiere diesen Issue/Signal in ein praezises Engineering-Problem "
        "fuer SPALTEN-Analyse (COGNITUM/DaySensOS). "
        'Antworte NUR mit validem JSON: '
        '{"problem": "...", "domain": "...", "urgency": "medium"}'
    )

    response = _llm_call(prompt, timeout=90)

    # JSON aus LLM-Antwort extrahieren
    parsed = None
    m = re.search(r'\{[^{}]+\}', response, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group())
        except json.JSONDecodeError:
            pass

    if parsed:
        urgency = parsed.get("urgency", "medium")
        if urgency not in URGENCY_VALUES:
            urgency = "medium"
        return {
            "problem": parsed.get("problem") or title or body[:100],
            "domain":  parsed.get("domain")  or domain,
            "urgency": urgency,
            "source":  source,
            "raw_signal": signal,
            "sig_key":  (title or str(body))[:120],
        }

    # Fallback: kein gueltiges JSON
    raw_problem = f"{title}: {str(body)[:100]}" if title else str(body)[:150]
    return {
        "problem": raw_problem.strip() or "Unbekanntes Problem",
        "domain":  domain,
        "urgency": "medium",
        "source":  source,
        "raw_signal": signal,
        "sig_key":  (title or str(body))[:120],
    }


_DOMAIN_CYCLE = list(_DOMAIN_PROMPTS.keys())


def _generate_llm_problem(index: int, domain: str = None) -> dict:
    """Generiert ein LLM-synthetisches Engineering-Problem mit Domain-Schwerpunkt als Fallback."""
    target_domain = domain or _DOMAIN_CYCLE[index % len(_DOMAIN_CYCLE)]
    domain_context = _DOMAIN_PROMPTS.get(target_domain, "COGNITUM/DaySensOS Engineering")

    prompt = (
        f"Generiere Engineering-Problem #{index} mit Schwerpunkt: {domain_context}. "
        "Sei spezifisch, technisch praezise und konkret — keine generischen Aussagen. "
        'Antworte NUR mit validem JSON: '
        f'{{"problem": "...", "domain": "{target_domain}", "urgency": "medium"}}'
    )
    response = _llm_call(prompt, timeout=90)

    m = re.search(r'\{[^{}]+\}', response, re.DOTALL)
    if m:
        try:
            p = json.loads(m.group())
            urgency = p.get("urgency", "medium")
            if urgency not in URGENCY_VALUES:
                urgency = "medium"
            return {
                "problem": p.get("problem", response[:150]),
                "domain":  p.get("domain", target_domain),
                "urgency": urgency,
                "source":  "llm_generated",
            }
        except json.JSONDecodeError:
            pass

    return {
        "problem": response[:200] if not response.startswith("[SIMULATION]") else
                   f"COGNITUM {target_domain} Problem #{index}: Sensor-Consent-Validierung",
        "domain":  target_domain,
        "urgency": "medium",
        "source":  "llm_generated",
    }


import random as _random


def _prob_hash(text: str) -> str:
    return _hashlib.sha256(text[:120].encode("utf-8")).hexdigest()[:20]


class ProblemGenerator:
    def __init__(self):
        self.fetcher = RealSignalFetcher()
        self._seed_index = 0

    def generate(self, n: int = 5, skip_hashes: Optional[Set[str]] = None) -> List[dict]:
        """
        Generiert n Engineering-Probleme.
        1. fetch_all() — scannt ALLE Signale nach noch nicht gesehenen (skip_hashes-Prefilter)
        2. Seed-Fallback wenn frische Real-Signale erschoepft
        3. LLM-Fallback mit Domain-Rotation wenn Seed-Pool erschoepft
        4. Echte Signale werden priorisiert
        """
        skip_hashes = skip_hashes or set()

        # 1. Echte Signale holen
        signals = self.fetcher.fetch_all(repos=["fatdinhero/cognitum"])
        masterplan_signals = [s for s in signals if s.get("source") == "masterplan"]
        print(
            f"  ProblemGenerator: {len(signals)} Signale gesamt "
            f"({len(masterplan_signals)} Masterplan)"
        )

        problems: List[dict] = []

        # 2. Signale konvertieren — Prefilter via sig_key-Hash (LLM-Call sparen)
        for sig in signals:
            if len(problems) >= n:
                break
            # Schnell-Check via Signal-Key (kanonisch, deterministisch)
            sig_key = (sig.get("title") or sig.get("problem", ""))[:120]
            sig_h   = _prob_hash(sig_key)
            if sig_h in skip_hashes:
                continue
            p = _signal_to_problem(sig)
            if not p.get("problem"):
                continue
            # Auch LLM-konvertierten Hash pruefen (Rueckwaertskompatibilitaet)
            final_h = _prob_hash(p["problem"])
            if final_h in skip_hashes:
                continue
            problems.append(p)

        fresh_real = len(problems)

        # 3. Seed-Fallback — wenn frische Real-Signale nicht ausreichen
        remaining = n - len(problems)
        if remaining > 0:
            print(f"  Seed-Fallback: {remaining} Probleme (fresh_real={fresh_real})")
            seed_pool = list(_SEED_PROBLEMS)
            _random.shuffle(seed_pool)
            for seed in seed_pool:
                if remaining <= 0:
                    break
                seed_text = seed.get("problem", "")
                if _prob_hash(seed_text) in skip_hashes:
                    continue
                p = {**seed, "source": "seed_fallback"}
                problems.append(p)
                remaining -= 1

        # 4. LLM-Fallback — wenn Seeds auch erschoepft
        remaining = n - len(problems)
        if remaining > 0:
            print(f"  LLM-Fallback: {remaining} synthetische Probleme")
            for i in range(remaining):
                domain = _DOMAIN_CYCLE[(self._seed_index + i) % len(_DOMAIN_CYCLE)]
                p = _generate_llm_problem(len(problems) + i + 1, domain=domain)
                problems.append(p)
            self._seed_index = (self._seed_index + remaining) % len(_DOMAIN_CYCLE)

        # 5. Priorisierung: echte Signale zuerst
        def _priority(p: dict) -> int:
            src = p.get("source", "")
            if src in ("masterplan", "github", "gitlab"):
                return 0
            if src == "seed_fallback":
                return 1
            return 2

        problems.sort(key=_priority)
        return problems[:n]
