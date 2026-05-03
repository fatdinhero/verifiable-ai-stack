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
