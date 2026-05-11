import pytest
import yaml
import networkx as nx
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
GOVERNANCE = ROOT / "governance"

def load_masterplan():
    with open(GOVERNANCE / "masterplan.yaml") as f:
        return yaml.safe_load(f)

def build_graph(mp):
    G = nx.DiGraph()
    for adr in mp.get("adrs", []):
        G.add_node(adr["id"], type="adr")
        for up in adr.get("links", {}).get("upstream", []):
            G.add_edge(adr["id"], up, relation="depends_on")
    for mod in mp.get("modules", []):
        G.add_node(mod["id"], type="module")
        for up in mod.get("links", {}).get("upstream", []):
            G.add_edge(mod["id"], up, relation="depends_on")
    return G

VALID_STATUSES = {"proposed", "accepted", "deprecated", "superseded"}

class TestMasterplanConsistency:
    @pytest.fixture(scope="class")
    def masterplan(self): return load_masterplan()
    @pytest.fixture(scope="class")
    def graph(self, masterplan): return build_graph(masterplan)

    def test_no_dead_links(self, graph):
        dead = [f"{u}->{v}" for u, v, _ in graph.edges(data=True) if v not in graph.nodes]
        assert not dead, f"Tote Links: {dead}"

    def test_adr_deprecated_has_superseded_by(self, masterplan):
        for adr in masterplan.get("adrs", []):
            if adr.get("status") == "deprecated":
                assert adr.get("superseded_by"), f"ADR {adr['id']} deprecated ohne superseded_by"

    def test_no_duplicate_ids(self, masterplan):
        ids = [a["id"] for a in masterplan.get("adrs",[])] + [m["id"] for m in masterplan.get("modules",[])]
        dupes = set(x for x in ids if ids.count(x) > 1)
        assert not dupes, f"Doppelte IDs: {dupes}"

    def test_every_privacy_invariant_has_test(self, masterplan):
        missing = [f"Privacy {inv['id']}" for inv in masterplan.get("privacy_invariants",[])
                   if not inv.get("test_tool") and not inv.get("test_method")]
        assert not missing, f"Kein Test: {missing}"


class TestConstitution:
    @pytest.fixture(scope="class")
    def masterplan(self): return load_masterplan()

    def test_constitution_not_empty(self, masterplan):
        arts = masterplan.get("constitution_articles", [])
        assert len(arts) >= 10, f"Constitution braucht mindestens 10 Artikel, hat {len(arts)}"

    def test_constitution_ids_sequential(self, masterplan):
        ids = [a["id"] for a in masterplan.get("constitution_articles", [])]
        expected = list(range(1, len(ids) + 1))
        assert ids == expected, f"Artikel-IDs nicht sequentiell: {ids}"

    def test_constitution_no_duplicate_titles(self, masterplan):
        titles = [a["title"] for a in masterplan.get("constitution_articles", [])]
        dupes = set(x for x in titles if titles.count(x) > 1)
        assert not dupes, f"Doppelte Artikel-Titel: {dupes}"

    def test_constitution_has_privacy_first(self, masterplan):
        titles = [a["title"].lower() for a in masterplan.get("constitution_articles", [])]
        assert any("privacy" in t for t in titles), "Constitution muss Privacy-Artikel enthalten"

    def test_constitution_has_halluzination(self, masterplan):
        titles = [a["title"].lower() for a in masterplan.get("constitution_articles", [])]
        assert any("halluzin" in t for t in titles), "Art. 11 Halluzinations-Kennzeichnung fehlt"


class TestCNANorms:
    @pytest.fixture(scope="class")
    def masterplan(self): return load_masterplan()

    def test_cna_has_norms(self, masterplan):
        cna = next((m for m in masterplan.get("modules", []) if m["id"] == "CNA"), None)
        assert cna, "CNA-Modul fehlt"
        norms = cna.get("norms", [])
        assert len(norms) >= 10, f"CNA braucht mindestens 10 Norms, hat {len(norms)}"

    def test_cna_norm_ids_unique(self, masterplan):
        cna = next((m for m in masterplan.get("modules", []) if m["id"] == "CNA"), None)
        ids = [n["id"] for n in cna.get("norms", [])]
        dupes = set(x for x in ids if ids.count(x) > 1)
        assert not dupes, f"Doppelte Norm-IDs: {dupes}"

    def test_cna_norms_have_sensors(self, masterplan):
        cna = next((m for m in masterplan.get("modules", []) if m["id"] == "CNA"), None)
        missing = [n["id"] for n in cna.get("norms", [])
                   if not n.get("sensor_requirements")]
        assert not missing, f"Norms ohne Sensor-Requirements: {missing}"

    def test_cna_norms_have_condition(self, masterplan):
        cna = next((m for m in masterplan.get("modules", []) if m["id"] == "CNA"), None)
        missing = [n["id"] for n in cna.get("norms", [])
                   if not n.get("condition_yaml")]
        assert not missing, f"Norms ohne Condition-YAML: {missing}"

    def test_cna_norms_consent_sensors_flagged(self, masterplan):
        cna = next((m for m in masterplan.get("modules", []) if m["id"] == "CNA"), None)
        camera_norms = []
        for n in cna.get("norms", []):
            for sr in n.get("sensor_requirements", []):
                if sr["sensor"] in ("Kamera", "Infrarot-Kamera") and not sr.get("consent"):
                    camera_norms.append(f"{n['id']}/{sr['sensor']}")
        assert not camera_norms, f"Kamera-Sensoren ohne consent=true: {camera_norms}"


class TestISO25010:
    @pytest.fixture(scope="class")
    def masterplan(self): return load_masterplan()

    def test_iso_25010_not_empty(self, masterplan):
        chars = masterplan.get("iso_25010", [])
        assert len(chars) >= 8, f"ISO 25010 braucht mindestens 8 Characteristics, hat {len(chars)}"

    def test_iso_25010_valid_statuses(self, masterplan):
        invalid = []
        for char in masterplan.get("iso_25010", []):
            for sub in char.get("sub_characteristics", []):
                if sub.get("status") not in VALID_STATUSES:
                    invalid.append(f"{char['name']}/{sub['name']}: {sub.get('status')}")
        assert not invalid, f"Ungueltige Status: {invalid}"

    def test_iso_25010_every_char_has_subs(self, masterplan):
        empty = [c["name"] for c in masterplan.get("iso_25010", [])
                 if not c.get("sub_characteristics")]
        assert not empty, f"Characteristics ohne Sub-Characteristics: {empty}"

    def test_iso_25010_no_duplicate_char_names(self, masterplan):
        names = [c["name"] for c in masterplan.get("iso_25010", [])]
        dupes = set(x for x in names if names.count(x) > 1)
        assert not dupes, f"Doppelte Characteristic-Namen: {dupes}"


class TestRiskRegister:
    @pytest.fixture(scope="class")
    def masterplan(self): return load_masterplan()

    def test_risks_not_empty(self, masterplan):
        risks = masterplan.get("iso_23894_risks", [])
        assert len(risks) > 0, "Risikoregister ist leer"

    def test_risks_valid_probability(self, masterplan):
        valid_prob = {"low", "medium", "high"}
        invalid = [r["id"] for r in masterplan.get("iso_23894_risks", [])
                   if r.get("probability") not in valid_prob]
        assert not invalid, f"Risiken mit ungueltiger Wahrscheinlichkeit: {invalid}"

    def test_risks_have_mitigation(self, masterplan):
        missing = [r["id"] for r in masterplan.get("iso_23894_risks", [])
                   if not r.get("mitigation")]
        assert not missing, f"Risiken ohne Mitigation: {missing}"

    def test_risk_ids_unique(self, masterplan):
        ids = [r["id"] for r in masterplan.get("iso_23894_risks", [])]
        dupes = set(x for x in ids if ids.count(x) > 1)
        assert not dupes, f"Doppelte Risk-IDs: {dupes}"


class TestPrivacyInvariants:
    @pytest.fixture(scope="class")
    def masterplan(self): return load_masterplan()

    def test_privacy_not_empty(self, masterplan):
        privs = masterplan.get("privacy_invariants", [])
        assert len(privs) >= 10, f"Privacy braucht mindestens 10 Invarianten, hat {len(privs)}"

    def test_privacy_id_format(self, masterplan):
        import re
        invalid = [inv["id"] for inv in masterplan.get("privacy_invariants", [])
                   if not re.match(r"^PRIV-\d{2}$", inv.get("id", ""))]
        assert not invalid, f"Privacy-IDs mit falschem Format: {invalid}"

    def test_privacy_ids_unique(self, masterplan):
        ids = [inv["id"] for inv in masterplan.get("privacy_invariants", [])]
        dupes = set(x for x in ids if ids.count(x) > 1)
        assert not dupes, f"Doppelte Privacy-IDs: {dupes}"

    def test_zero_retention_exists(self, masterplan):
        descriptions = [inv.get("description", "").lower()
                       for inv in masterplan.get("privacy_invariants", [])]
        assert any("zero-retention" in d for d in descriptions), \
            "PRIV mit Zero-Retention fehlt — Constitution-Verstoss"

    def test_dsar_exists(self, masterplan):
        descriptions = [inv.get("description", "").lower()
                       for inv in masterplan.get("privacy_invariants", [])]
        assert any("dsar" in d or "auskunft" in d for d in descriptions), \
            "PRIV mit DSAR-Funktion fehlt"


class TestExitPlan:
    @pytest.fixture(scope="class")
    def masterplan(self): return load_masterplan()

    def test_exit_plan_not_empty(self, masterplan):
        phases = masterplan.get("exit_plan", [])
        assert len(phases) >= 3, f"Exit-Plan braucht mindestens 3 Phasen, hat {len(phases)}"

    def test_exit_plan_has_phase_0(self, masterplan):
        phases = [ep["phase"] for ep in masterplan.get("exit_plan", [])]
        assert any("0" in p or "heute" in p.lower() for p in phases), \
            "Exit-Plan braucht Phase 0 (heute)"


class TestAuditTrail:
    @pytest.fixture(scope="class")
    def masterplan(self): return load_masterplan()

    def test_audit_trail_not_empty(self, masterplan):
        trail = masterplan.get("audit_trail", [])
        assert len(trail) > 0, "Audit-Trail ist leer"

    def test_audit_entries_have_actor(self, masterplan):
        missing = [e["timestamp"] for e in masterplan.get("audit_trail", [])
                   if not e.get("actor")]
        assert not missing, f"Audit-Eintraege ohne Actor: {missing}"

    def test_audit_trail_chronological(self, masterplan):
        timestamps = [e["timestamp"] for e in masterplan.get("audit_trail", [])]
        assert timestamps == sorted(timestamps), "Audit-Trail nicht chronologisch sortiert"
