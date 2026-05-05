#!/usr/bin/env python3
"""
autonomous_loop.py
COGNITUM Autonomous Engineering Loop
Laedt echte Signale, verarbeitet sie via SPALTEN, bewertet und indexiert.

Nutzung:
    .venv/bin/python3 autonomous_loop.py [--batch-size N] [--max-total N] [--sleep S]
"""
import argparse
import hashlib
import json
import os
import signal as _signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from governance.models import EngineeringCase, SPALTENPhase, Urgency
from governance.problem_generator import ProblemGenerator, _generate_llm_problem, _DOMAIN_CYCLE
from governance.signal_sources import RealSignalFetcher
from governance.wiki_formatter import WikiFormatter
from governance.gitops_handler import GitOpsHandler
import spalten_agent as agent

STATE_FILE     = REPO_ROOT / ".loop_state.json"
LOG_DIR        = REPO_ROOT / "logs"
LOG_FILE       = LOG_DIR / "autonomous_loop.log"
PID_FILE       = LOG_DIR / "autonomous_loop.pid"
BOT_QUEUE_FILE = REPO_ROOT / ".bot_queue.json"

_running = True


def _handle_stop(signum: int, frame: Any) -> None:
    global _running
    _log("Signal empfangen — beende nach aktuellem Batch.")
    _running = False


_signal.signal(_signal.SIGTERM, _handle_stop)
_signal.signal(_signal.SIGINT,  _handle_stop)


# ─── State & Logging ──────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_DIR.mkdir(exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "processed_count": 0,
        "skipped_count":   0,
        "avg_score":       0.0,
        "scores":          [],
        "processed_hashes": [],
        "signal_sources":  {},
        "batch_count":     0,
        "last_run":        "",
        "total_runtime_s": 0,
        "started_at":      datetime.now(timezone.utc).isoformat(),
    }


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _problem_hash(problem: str) -> str:
    """SHA256-Praefix der ersten 120 Zeichen — Idempotenz-Key."""
    return hashlib.sha256(problem[:120].encode("utf-8")).hexdigest()[:20]


def _run_dataset_export() -> None:
    """Ruft dataset_exporter.py via Subprocess auf (alle 10 Batches)."""
    exporter = REPO_ROOT / "scripts" / "dataset_exporter.py"
    if not exporter.exists():
        _log("  dataset_exporter.py nicht gefunden — uebersprungen")
        return
    try:
        result = subprocess.run(
            [sys.executable, str(exporter)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            _log("  Dataset-Export erfolgreich")
        else:
            _log(f"  Dataset-Export Fehler: {result.stderr[:200]}")
    except Exception as e:
        _log(f"  Dataset-Export Exception: {e}")


# ─── Bot-Queue Helpers ────────────────────────────────────────────────────────

def _load_bot_queue() -> list:
    if BOT_QUEUE_FILE.exists():
        try:
            return json.loads(BOT_QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_bot_queue(queue: list) -> None:
    BOT_QUEUE_FILE.write_text(
        json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _pop_bot_queue_entry() -> Optional[dict]:
    """Holt und entfernt den ersten Eintrag aus der Bot-Queue (FIFO)."""
    queue = _load_bot_queue()
    if not queue:
        return None
    entry = queue.pop(0)
    _save_bot_queue(queue)
    return entry


# ─── AutonomousLoop ───────────────────────────────────────────────────────────

class AutonomousLoop:
    """
    Kontinuierlicher Engineering-Loop:
    Signal → Problem → SPALTEN → Evaluierung → RAG → State
    """

    def __init__(self):
        self.generator  = ProblemGenerator()
        self.fetcher    = RealSignalFetcher()
        self.state      = _load_state()
        self.wiki_fmt   = WikiFormatter()
        self.gitops     = GitOpsHandler()
        self._llm_domain_idx = 0
        LOG_DIR.mkdir(exist_ok=True)
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    def _refresh_regulatory(self) -> None:
        """Holt BSI-, EDPB- und arXiv-Signale und speichert sie in RAG-Memory."""
        try:
            bsi    = self.fetcher.fetch_bsi_feeds()
            edpb   = self.fetcher.fetch_edpb()
            arxiv  = self.fetcher.fetch_arxiv()
            signals = bsi + edpb + arxiv
            _log(
                f"  Regulatory-Refresh: {len(signals)} Signale "
                f"(BSI={len(bsi)} EDPB={len(edpb)} arXiv={len(arxiv)})"
            )
            if not signals:
                return
            # Optional: in RAG-Memory indexieren
            try:
                from governance.rag_memory import RAGMemory
                rag = RAGMemory()
                stored = 0
                for sig in signals:
                    title = sig.get("title", "")
                    problem = sig.get("problem", "")
                    if not title:
                        continue
                    adr_id = f"REG-{hashlib.sha256(title.encode()).hexdigest()[:8]}"
                    content = f"Title: {title}\nProblem: {problem}\nDomain: {sig.get('domain','')}"
                    metadata = {
                        "adr_id": adr_id, "title": title,
                        "domain": sig.get("domain", "regulatory"),
                        "source": sig.get("source", "rss"),
                        "score": 0.0, "case_id": adr_id,
                    }
                    ok = rag.add_adr(adr_id, content, metadata)
                    if ok:
                        stored += 1
                _log(f"  Regulatory-RAG: {stored}/{len(signals)} in ChromaDB indexiert")
            except Exception as e:
                _log(f"  Regulatory-RAG Fehler (nicht kritisch): {e}")
            # Quell-Statistik
            self.state["signal_sources"]["regulatory_refresh"] = (
                self.state["signal_sources"].get("regulatory_refresh", 0) + len(signals)
            )
        except Exception as e:
            _log(f"  Regulatory-Refresh Fehler: {e}")

    def _log_extended_status(self, max_total: int) -> None:
        """Erweiterter Status-Log alle 10 Batches mit ETA und Quellen-Breakdown."""
        processed = self.state["processed_count"]
        elapsed_s = max(self.state["total_runtime_s"], 1)
        remaining = max(max_total - processed, 0)

        rate_per_h = (processed / elapsed_s) * 3600
        if processed > 0:
            eta_s = remaining / (processed / elapsed_s)
            eta_h = eta_s / 3600
            eta_str = f"{eta_h:.1f}h"
        else:
            eta_str = "n/a"

        sources = self.state.get("signal_sources", {})
        src_breakdown = " | ".join(
            f"{k}={v}" for k, v in sorted(sources.items())
        ) or "keine"

        _log(
            f"  === EXTENDED STATUS ===\n"
            f"  Verarbeitet:   {processed}/{max_total}\n"
            f"  Rate:          {rate_per_h:.1f} Cases/h\n"
            f"  ETA bis {max_total}: {eta_str}\n"
            f"  Avg Score:     {self.state['avg_score']:.3f}\n"
            f"  Quellen:       {src_breakdown}"
        )

    def run_forever(
        self,
        batch_size:     int   = 3,
        sleep_between:  int   = 60,
        min_score:      float = 0.75,
        max_total:      int   = 500,
    ) -> None:
        _log(
            f"AutonomousLoop start | PID={os.getpid()} "
            f"batch={batch_size} sleep={sleep_between}s "
            f"min_score={min_score} max={max_total}"
        )

        try:
            while _running and self.state["processed_count"] < max_total:
                batch_start = time.time()
                self.state["batch_count"] += 1
                batch_num = self.state["batch_count"]

                _log(
                    f"=== Batch #{batch_num} | "
                    f"Verarbeitet: {self.state['processed_count']}/{max_total} ==="
                )

                # ── 0. Alle 5 Batches: Regulatory-Signale neu laden ───────────
                if batch_num % 5 == 0:
                    _log("  Regulatory-Refresh (alle 5 Batches)...")
                    self._refresh_regulatory()

                # ── 0b. Bot-Queue: max 1 Prioritaets-Eintrag pro Batch ───────
                bot_problems: List[dict] = []
                bot_entry = _pop_bot_queue_entry()
                if bot_entry:
                    bot_title = bot_entry.get("title", "Bot-Signal")[:60]
                    bot_text  = bot_entry.get("text", "")
                    _log(f"  Bot-Queue Eintrag: '{bot_title}'")
                    if bot_text:
                        domain = bot_entry.get("relevance_category") or "cognitum"
                        bot_problems.append({
                            "problem": bot_text[:500],
                            "domain": domain,
                            "urgency": "high",
                            "source": "bot_queue",
                            "sig_key": bot_title,
                            "priority": 0,
                        })
                    self.state["signal_sources"]["bot_queue"] = (
                        self.state["signal_sources"].get("bot_queue", 0) + 1
                    )

                # ── 1. Frische Probleme via ProblemGenerator ──────────────────
                normal_n = max(batch_size - len(bot_problems), 0)
                try:
                    problems = self.generator.generate(
                        n=normal_n,
                        skip_hashes=set(self.state["processed_hashes"]),
                    )
                except Exception as e:
                    _log(f"ProblemGenerator Fehler: {e}")
                    time.sleep(sleep_between)
                    continue

                # Bot-Queue Eintraege vorne einsetzen (Prioritaet 0)
                problems = bot_problems + problems

                # Direkter LLM-Fallback wenn ProblemGenerator zu wenig liefert
                if len(problems) < batch_size and normal_n > 0:
                    missing = batch_size - len(problems)
                    _log(f"  Direkt-LLM-Fallback: {missing} fehlende Probleme auffuellen")
                    for i in range(missing):
                        domain = _DOMAIN_CYCLE[self._llm_domain_idx % len(_DOMAIN_CYCLE)]
                        self._llm_domain_idx += 1
                        p = _generate_llm_problem(len(problems) + i + 1, domain=domain)
                        problems.append(p)

                batch_processed = 0
                batch_skipped   = 0
                batch_scores: List[float] = []

                for prob in problems:
                    if not _running:
                        break

                    problem_text = prob.get("problem", "").strip()
                    if not problem_text:
                        continue

                    # ── 2. Idempotenz-Check (problem-hash + signal-key-hash) ──
                    h       = _problem_hash(problem_text)
                    sig_key = prob.get("sig_key", "")
                    h_sig   = _problem_hash(sig_key) if sig_key else h
                    seen    = set(self.state["processed_hashes"])
                    if h in seen or h_sig in seen:
                        _log(f"  SKIP (bereits verarbeitet): {problem_text[:60]}")
                        batch_skipped += 1
                        self.state["skipped_count"] += 1
                        continue

                    # ── 3. SPALTEN-Run ────────────────────────────────────────
                    _log(f"  SPALTEN: {problem_text[:70]}")
                    try:
                        urgency_str = prob.get("urgency", "medium")
                        try:
                            urgency = Urgency(urgency_str)
                        except ValueError:
                            urgency = Urgency.medium

                        case = EngineeringCase(
                            title=problem_text[:80],
                            problem=problem_text,
                            domain=prob.get("domain", "engineering"),
                            urgency=urgency,
                        )
                        case = agent.run_spalten(
                            case,
                            human_approve=False,
                            skip_gitops=True,
                        )
                    except Exception as e:
                        _log(f"  SPALTEN Fehler: {e}")
                        for _h in {h, h_sig}:
                            if _h not in self.state["processed_hashes"]:
                                self.state["processed_hashes"].append(_h)
                        continue

                    # ── 4. Evaluierung ────────────────────────────────────────
                    node_l = next(
                        (s for s in case.steps if s.phase == SPALTENPhase.L), None
                    )
                    score: float = 0.0
                    if node_l:
                        score = node_l.artifacts.get("vdi2225", {}).get(
                            "best_score", 0.0
                        )

                    if score >= min_score:
                        _log(f"  PASS score={score:.3f} → RAG")
                        # ── 5. RAG indexieren ─────────────────────────────────
                        try:
                            agent._store_in_rag(case)
                        except Exception as e:
                            _log(f"  RAG Fehler: {e}")

                        # ── 5b. Wiki-Push fuer cross_domain_extraction ─────────
                        if prob.get("source") == "cross_domain_extraction":
                            try:
                                entry_type = prob.get("type", "analogy")
                                if entry_type == "insight":
                                    wiki_title, wiki_content = self.wiki_fmt.format_insight(prob)
                                else:
                                    wiki_title, wiki_content = self.wiki_fmt.format_analogy(prob)
                                ok = self.gitops.push_to_wiki(wiki_title, wiki_content)
                                if ok:
                                    _log(f"  Wiki: '{wiki_title}' veroeffentlicht")
                                else:
                                    _log(f"  Wiki: Push fehlgeschlagen fuer '{wiki_title}'")
                            except Exception as e:
                                _log(f"  Wiki Fehler: {e}")

                        # Quell-Statistik
                        src = prob.get("source", "unknown")
                        self.state["signal_sources"][src] = (
                            self.state["signal_sources"].get(src, 0) + 1
                        )
                    else:
                        _log(f"  FAIL score={score:.3f} < {min_score}")

                    # Beide Hashes speichern: Problem-Text + Signal-Key
                    for _h in {h, h_sig}:
                        if _h not in self.state["processed_hashes"]:
                            self.state["processed_hashes"].append(_h)
                    # Letzten 4000 Hashes behalten (2× wegen doppelter Eintraege)
                    if len(self.state["processed_hashes"]) > 4000:
                        self.state["processed_hashes"] = (
                            self.state["processed_hashes"][-4000:]
                        )

                    self.state["scores"].append(score)
                    batch_scores.append(score)
                    self.state["processed_count"] += 1
                    batch_processed += 1

                # ── 6. Alle 10 Batches: Dataset-Export + erweiterter Status ──
                if batch_num % 10 == 0:
                    _log("  Dataset-Export (alle 10 Batches)...")
                    _run_dataset_export()
                    self._log_extended_status(max_total)

                # ── 7. Status updaten ─────────────────────────────────────────
                all_scores = self.state["scores"]
                self.state["avg_score"] = (
                    round(sum(all_scores) / len(all_scores), 4)
                    if all_scores else 0.0
                )
                self.state["last_run"]        = datetime.now(timezone.utc).isoformat()
                self.state["total_runtime_s"] += int(time.time() - batch_start)
                _save_state(self.state)

                _log(
                    f"  Batch #{batch_num} fertig | "
                    f"processed={batch_processed} skipped={batch_skipped} "
                    f"batch_avg={round(sum(batch_scores)/len(batch_scores),3) if batch_scores else 0:.3f} "
                    f"total_avg={self.state['avg_score']:.3f}"
                )

                # ── 8. Sleep ──────────────────────────────────────────────────
                if _running and self.state["processed_count"] < max_total:
                    _log(f"  Sleep {sleep_between}s ...")
                    for _ in range(sleep_between):
                        if not _running:
                            break
                        time.sleep(1)

        finally:
            _log(
                f"AutonomousLoop beendet | "
                f"Total: {self.state['processed_count']} | "
                f"Skipped: {self.state['skipped_count']} | "
                f"Avg Score: {self.state['avg_score']:.3f}"
            )
            _save_state(self.state)
            if PID_FILE.exists():
                PID_FILE.unlink()


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="COGNITUM Autonomous Engineering Loop")
    parser.add_argument("--batch-size", type=int,   default=3,    metavar="N")
    parser.add_argument("--sleep",      type=int,   default=60,   metavar="S")
    parser.add_argument("--min-score",  type=float, default=0.75, metavar="F")
    parser.add_argument("--max-total",  type=int,   default=500,  metavar="N")
    args = parser.parse_args()

    loop = AutonomousLoop()
    loop.run_forever(
        batch_size=args.batch_size,
        sleep_between=args.sleep,
        min_score=args.min_score,
        max_total=args.max_total,
    )


if __name__ == "__main__":
    main()
