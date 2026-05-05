"""
tests/test_signal_sources.py
Unit-Tests fuer RealSignalFetcher (stdlib-Variante: urllib + xml.etree + yaml).
Alle Netzwerkaufrufe werden via unittest.mock.patch gemockt.
"""
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]

# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _mock_urlopen(body: str):
    """Erstellt context-manager-kompatibles Mock fuer urllib.request.urlopen."""
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    cm.read = MagicMock(return_value=body.encode("utf-8"))
    return cm


RSS_BODY = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item><title>EU AI Act Article 6 Update</title>
    <description>New compliance rules for wearables.</description>
    <pubDate>Mon, 05 May 2026 00:00:00 GMT</pubDate>
    <link>https://eur-lex.europa.eu/123</link>
  </item>
</channel></rss>"""

DDG_HTML = """<html><body><table>
<tr><td class="result-snippet">Privacy-first wearable market is growing rapidly.</td></tr>
</table></body></html>"""

GITLAB_JSON = json.dumps([{
    "title": "Privacy gate regression",
    "description": "Consent gate bypassed in edge case",
    "labels": ["bug"],
    "web_url": "https://gitlab.com/issues/42",
    "updated_at": "2026-05-05T00:00:00Z",
}])

GITHUB_JSON = json.dumps([{
    "title": "Feature: BLE sensor fusion",
    "body": "Implement 8-channel BLE sensor fusion",
    "labels": [{"name": "enhancement"}],
    "html_url": "https://github.com/issues/1",
    "created_at": "2026-05-04T00:00:00Z",
}])


# ─── TestFetchGitlabIssues ────────────────────────────────────────────────────

class TestFetchGitlabIssues:
    def test_returns_list_with_token(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._read_token", return_value="test-token"), \
             patch("governance.signal_sources._http_get", return_value=GITLAB_JSON):
            result = fetcher.fetch_gitlab_issues("fatdinhero/cognitum")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["source"] == "gitlab"
        assert result[0]["title"] == "Privacy gate regression"

    def test_empty_without_token(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._read_token", return_value=None):
            result = fetcher.fetch_gitlab_issues("fatdinhero/cognitum")
        assert result == []

    def test_empty_on_http_error(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._read_token", return_value="tok"), \
             patch("governance.signal_sources._http_get", return_value=None):
            result = fetcher.fetch_gitlab_issues("fatdinhero/cognitum")
        assert result == []


# ─── TestFetchMasterplanDecisions ─────────────────────────────────────────────

class TestFetchMasterplanDecisions:
    def test_loads_real_masterplan_returns_list(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        result = fetcher.fetch_masterplan_decisions()
        assert isinstance(result, list)

    def test_each_entry_has_required_keys(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        result = fetcher.fetch_masterplan_decisions()
        for entry in result:
            assert "title" in entry
            assert "source" in entry
            assert entry["source"] == "masterplan"

    def test_missing_file_returns_empty(self, tmp_path):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        fake_path = tmp_path / "nonexistent.yaml"
        with patch("governance.signal_sources.MASTERPLAN_PATH", fake_path):
            result = fetcher.fetch_masterplan_decisions()
        assert result == []

    def test_domain_field_present(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        result = fetcher.fetch_masterplan_decisions()
        for entry in result:
            assert "domain" in entry


# ─── TestFetchRegulatoryUpdates ───────────────────────────────────────────────

class TestFetchRegulatoryUpdates:
    def test_returns_list(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._http_get", return_value=RSS_BODY):
            result = fetcher.fetch_regulatory_updates()
        assert isinstance(result, list)

    def test_parses_rss_title(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._http_get", return_value=RSS_BODY):
            result = fetcher.fetch_regulatory_updates()
        titles = [r["title"] for r in result if "title" in r]
        assert any("EU AI Act" in t for t in titles)

    def test_empty_on_network_failure(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._http_get", return_value=None):
            result = fetcher.fetch_regulatory_updates()
        assert result == []

    def test_entry_has_source_field(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._http_get", return_value=RSS_BODY):
            result = fetcher.fetch_regulatory_updates()
        for entry in result:
            assert "source" in entry


# ─── TestFetchMarketSignals ───────────────────────────────────────────────────

class TestFetchMarketSignals:
    def test_returns_list(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._http_get", return_value=DDG_HTML), \
             patch("governance.signal_sources._llm_call", return_value="[SIMULATION] test"):
            result = fetcher.fetch_market_signals(queries=["wearable AI"])
        assert isinstance(result, list)

    def test_custom_queries_respected(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._http_get", return_value=DDG_HTML), \
             patch("governance.signal_sources._llm_call", return_value="[SIMULATION] x"), \
             patch("governance.signal_sources.time.sleep"):
            result = fetcher.fetch_market_signals(queries=["q1", "q2"])
        assert len(result) == 2

    def test_empty_on_no_snippets(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._http_get", return_value="<html></html>"), \
             patch("governance.signal_sources.time.sleep"):
            result = fetcher.fetch_market_signals(queries=["wearable"])
        # Kein Snippet → kein Ergebnis
        assert result == []


# ─── TestFetchAll ─────────────────────────────────────────────────────────────

class TestFetchAll:
    def test_returns_list(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._read_token", return_value=None), \
             patch("governance.signal_sources._http_get", return_value=None), \
             patch("governance.signal_sources._llm_call", return_value="[SIMULATION]"), \
             patch("governance.signal_sources.time.sleep"):
            result = fetcher.fetch_all()
        assert isinstance(result, list)

    def test_masterplan_always_included(self):
        from governance.signal_sources import RealSignalFetcher
        fetcher = RealSignalFetcher()
        with patch("governance.signal_sources._read_token", return_value=None), \
             patch("governance.signal_sources._http_get", return_value=None), \
             patch("governance.signal_sources._llm_call", return_value="[SIMULATION]"), \
             patch("governance.signal_sources.time.sleep"):
            result = fetcher.fetch_all()
        sources = {r.get("source") for r in result}
        # Masterplan ist local — immer verfuegbar
        assert "masterplan" in sources


# ─── TestProblemGenerator ─────────────────────────────────────────────────────

class TestProblemGenerator:
    def test_generate_returns_list(self):
        from governance.problem_generator import ProblemGenerator
        gen = ProblemGenerator()
        with patch("governance.signal_sources._read_token", return_value=None), \
             patch("governance.signal_sources._http_get", return_value=None), \
             patch("governance.signal_sources._llm_call", return_value="[SIMULATION]"), \
             patch("governance.problem_generator._llm_call",
                   return_value='{"problem":"test","domain":"engineering","urgency":"medium"}'), \
             patch("governance.signal_sources.time.sleep"):
            result = gen.generate(n=2)
        assert isinstance(result, list)

    def test_each_problem_has_required_keys(self):
        from governance.problem_generator import ProblemGenerator
        gen = ProblemGenerator()
        with patch("governance.signal_sources._read_token", return_value=None), \
             patch("governance.signal_sources._http_get", return_value=None), \
             patch("governance.signal_sources._llm_call", return_value="[SIMULATION]"), \
             patch("governance.problem_generator._llm_call",
                   return_value='{"problem":"test p","domain":"engineering","urgency":"medium"}'), \
             patch("governance.signal_sources.time.sleep"):
            result = gen.generate(n=1)
        for p in result:
            assert "problem" in p
            assert "domain" in p
