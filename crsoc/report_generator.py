#!/usr/bin/env python3
"""
crsoc/report_generator.py
Speichert CRSOC-Report + sendet Telegram-Notification
"""
from __future__ import annotations
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

REPO_ROOT    = Path(__file__).resolve().parents[1]
REPORTS_DIR  = REPO_ROOT / "reports"
TOKEN_FILE   = Path.home() / ".telegram-token"
WHITELIST_FILE = Path.home() / ".telegram-whitelist"


class ReportGenerator:
    def save(self, cycle_result: Dict[str, Any]) -> str:
        """Speichert JSON-Report, gibt Dateipfad zurueck."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts    = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        fname = f"crsoc_{ts}.json"
        path  = REPORTS_DIR / fname
        path.write_text(json.dumps(cycle_result, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def notify_telegram(self, cycle_result: Dict[str, Any], report_path: str) -> bool:
        """Sendet Telegram-Notification mit Zyklus-Zusammenfassung."""
        token    = self._read_file(TOKEN_FILE)
        chat_id  = self._read_file(WHITELIST_FILE)
        if not token or not chat_id:
            print("[CRSOC] Telegram: Token oder Chat-ID fehlt — uebersprungen")
            return False

        n        = cycle_result.get("phases", {}).get("0_intake", {}).get("processed_count", "?")
        best     = cycle_result.get("best_idea", "—")
        psi      = cycle_result.get("best_score", 0.0)
        adr      = cycle_result.get("adr_path", "n/a")
        passed   = cycle_result.get("phases", {}).get("5_metabell", {}).get("passed", 0)
        brier    = cycle_result.get("phases", {}).get("7_temporal", {}).get("brier_score", "n/a")
        brier_q  = cycle_result.get("phases", {}).get("7_temporal", {}).get("brier_quality", "n/a")

        msg = (
            f"CRSOC Zyklus abgeschlossen\n"
            f"Cases: {n}\n"
            f"Beste Idee: {best}\n"
            f"Score (Psi): {psi:.2f}\n"
            f"Ideen > 1.4: {passed}\n"
            f"Brier: {brier} ({brier_q})\n"
            f"ADR: {adr}"
        )

        return self._send(token, chat_id, msg)

    def _send(self, token: str, chat_id: str, text: str) -> bool:
        url     = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read().decode("utf-8"))
                return resp.get("ok", False)
        except Exception as e:
            print(f"[CRSOC] Telegram senden fehlgeschlagen: {e}")
            return False

    def _read_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8").splitlines()[0].strip()
        except Exception:
            return ""
