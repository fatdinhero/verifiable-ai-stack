"""
tests/test_signal_sources.py
Unit-Tests fuer RealSignalFetcher + autonomous_loop._signals_to_problems.
Alle Netzwerkaufrufe werden via unittest.mock.patch gemockt.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]


def _mock_gitlab_response(issues: list) -> MagicMock:
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = issues
    return m


def _mock_ddg_response(html: str) -> MagicMock:
    m = MagicMock()
    m.text = html
    m.status_code = 200
    return m


# ---------------------------------------------------------------------------
# TestRealSignalFetcher
# ---------------------------------------------------------------------------

class TestFetchGitlabIssues:
    def test_returns_list(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        fake_issue = {
            "iid": 42,
            "title": "Privacy gate broken",
            "state": "opened",
            "labels": ["bug"],
            "updated_at": "2026-05-05T00:00:00Z",
            "web_url": "https://gitlab.com/issues/42",
        }
        with patch("governance.signal_sources.requests.get", return_value=_mock_gitlab_response([fake_issue])):
            result = fetcher.fetch_gitlab_issues()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 42
        assert result[0]["source"] == "gitlab"

    def test_handles_network_error(self):
        import requests as req_lib
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources.requests.get", side_effect=req_lib.RequestException("timeout")):
            result = fetcher.fetch_gitlab_issues()
        assert isinstance(result, list)
        assert len(result) == 1
        assert "error" in result[0]

    def test_no_token_still_works(self):
        from governance.signal_sources import RealSignalFetcher
        with patch("governance.signal_sources.GITLAB_TOKEN_PATH", Path("/nonexistent/.gitlab-token")):
            with patch("governance.signal_sources.os.environ.get", return_value=None):
                fetcher = RealSignalFetcher()
                assert fetcher._token is None


class TestFetchMasterplanDecisions:
    def test_loads_real_masterplan(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        result = fetcher.fetch_masterplan_decisions()
        assert result["source"] == "masterplan"
        assert "adrs" in result
        assert len(result["adrs"]) > 0
        assert result["adrs"][0]["id"].startswith("ADR-")

    def test_returns_version(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        result = fetcher.fetch_masterplan_decisions()
        assert result["version"] != "unknown"

    def test_missing_file_graceful(self, tmp_path):
        from governance.signal_sources import RealSignalFetcher, MASTERPLAN_PATH
        fetcher = RealSignalFetcher()
        fake_path = tmp_path / "nonexistent.yaml"
        with patch("governance.signal_sources.MASTERPLAN_PATH", fake_path):
            result = fetcher.fetch_masterplan_decisions()
        assert "error" in result

    def test_privacy_invariants_present(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        result = fetcher.fetch_masterplan_decisions()
        # masterplan.yaml hat privacy_invariants oder leere Liste — beides ok
        assert "privacy_invariants" in result


class TestFetchRegulatoryUpdates:
    def test_returns_list(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        fake_feed = MagicMock()
        fake_entry = MagicMock()
        fake_entry.title = "EU AI Act Update"
        fake_entry.link = "https://eur-lex.europa.eu/123"
        fake_entry.published = "Mon, 05 May 2026 00:00:00 GMT"
        fake_entry.summary = "Neue Anforderungen fuer Hochrisiko-KI-Systeme."
        fake_feed.entries = [fake_entry]
        with patch("governance.signal_sources.feedparser.parse", return_value=fake_feed):
            result = fetcher.fetch_regulatory_updates()
        assert isinstance(result, list)
        assert any(r.get("title") == "EU AI Act Update" for r in result)
        assert result[0]["source"] == "regulatory_rss"

    def test_feed_error_graceful(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources.feedparser.parse", side_effect=Exception("DNS fail")):
            result = fetcher.fetch_regulatory_updates()
        assert isinstance(result, list)
        # Alle Eintraege haben error-Key
        assert all("error" in r for r in result)


class TestFetchMarketSignals:
    DDG_HTML = """
    <html><body><table>
    <tr><td><a class="result-link" href="https://example.com">Wearable AI Privacy 2026</a>
        <td class="result-snippet">Privacy-first wearable market growing fast.</td></tr>
    </table></body></html>
    """

    def test_returns_list(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources.requests.post", return_value=_mock_ddg_response(self.DDG_HTML)):
            result = fetcher.fetch_market_signals(queries=["wearable AI privacy"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["query"] == "wearable AI privacy"
        assert result[0]["source"] == "duckduckgo_lite"

    def test_network_error_graceful(self):
        import requests as req_lib
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources.requests.post", side_effect=req_lib.RequestException("timeout")):
            result = fetcher.fetch_market_signals(queries=["wearable AI"])
        assert isinstance(result, list)
        assert "error" in result[0]

    def test_custom_queries(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources.requests.post", return_value=_mock_ddg_response(self.DDG_HTML)):
            result = fetcher.fetch_market_signals(queries=["q1", "q2"])
        assert len(result) == 2


# ---------------------------------------------------------------------------
# TestSignalsToProblems (autonomous_loop)
# ---------------------------------------------------------------------------

class TestSignalsToProblems:
    def _make_signals(self):
        return {
            "gitlab_issues": [
                {"id": 1, "title": "Bug: Consent Gate bypassed", "labels": ["bug"],
                 "source": "gitlab", "url": "https://gitlab.com/1"},
                {"id": 2, "title": "Feature: Dashboard", "labels": [],
                 "source": "gitlab", "url": ""},
            ],
            "masterplan": {
                "open_risks": [
                    {"id": "RISK-02", "description": "Privacy leak", "probability": "high"},
                ],
                "adrs": [],
                "privacy_invariants": [],
            },
            "regulatory": [
                {"feed": "EUR-Lex", "title": "AI Act Art. 6 Clarification",
                 "link": "https://eur-lex.eu/x", "source": "regulatory_rss"},
            ],
            "market": [
                {"query": "wearable AI", "hits": [{"title": "Wearable boom", "url": "", "snippet": ""}],
                 "source": "duckduckgo_lite"},
            ],
        }

    def test_returns_list(self):
        from autonomous_loop import _signals_to_problems
        problems = _signals_to_problems(self._make_signals())
        assert isinstance(problems, list)

    def test_bug_label_gets_high_priority(self):
        from autonomous_loop import _signals_to_problems
        problems = _signals_to_problems(self._make_signals())
        bug_probs = [p for p in problems if "Consent Gate" in p["title"]]
        assert bug_probs
        assert bug_probs[0]["priority"] == "high"

    def test_high_risk_gets_high_priority(self):
        from autonomous_loop import _signals_to_problems
        problems = _signals_to_problems(self._make_signals())
        risk_probs = [p for p in problems if p["source"] == "masterplan_risk"]
        assert risk_probs
        assert risk_probs[0]["priority"] == "high"

    def test_sorted_by_priority(self):
        from autonomous_loop import _signals_to_problems
        problems = _signals_to_problems(self._make_signals())
        prio_order = {"high": 0, "medium": 1, "low": 2}
        vals = [prio_order[p["priority"]] for p in problems]
        assert vals == sorted(vals)

    def test_errors_skipped(self):
        from autonomous_loop import _signals_to_problems
        signals = {
            "gitlab_issues": [{"error": "timeout", "source": "gitlab", "items": []}],
            "masterplan": {"open_risks": [], "adrs": [], "privacy_invariants": []},
            "regulatory": [{"feed": "X", "error": "DNS", "source": "regulatory_rss"}],
            "market": [{"query": "x", "error": "timeout", "source": "duckduckgo_lite"}],
        }
        problems = _signals_to_problems(signals)
        assert isinstance(problems, list)
        # Keine Exception, leere Liste ist ok
