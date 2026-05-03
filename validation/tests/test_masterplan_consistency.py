import pytest, yaml, networkx as nx
from pathlib import Path
ROOT = Path(__file__).parent.parent.parent
GOVERNANCE = ROOT / "governance"

def load_masterplan():
    with open(GOVERNANCE / "masterplan.yaml") as f: return yaml.safe_load(f)

def build_graph(mp):
    G = nx.DiGraph()
    for a in mp.get("adrs", []):
        G.add_node(a["id"], type="adr")
        for u in a.get("links", {}).get("upstream", []): G.add_edge(a["id"], u)
    for m in mp.get("modules", []):
        G.add_node(m["id"], type="module")
        for u in m.get("links", {}).get("upstream", []): G.add_edge(m["id"], u)
    return G

class TestMasterplanConsistency:
    @pytest.fixture(scope="class")
    def masterplan(self): return load_masterplan()
    @pytest.fixture(scope="class")
    def graph(self, masterplan): return build_graph(masterplan)

    def test_no_dead_links(self, graph):
        dead = [f"{u}->{v}" for u,v,_ in graph.edges(data=True) if v not in graph.nodes]
        assert not dead, f"Tote Links: {dead}"

    def test_adr_deprecated_has_superseded_by(self, masterplan):
        for a in masterplan.get("adrs", []):
            if a.get("status") == "deprecated":
                assert a.get("superseded_by"), f"ADR {a['id']} deprecated ohne superseded_by"

    def test_no_duplicate_ids(self, masterplan):
        ids = [a["id"] for a in masterplan.get("adrs",[])] + [m["id"] for m in masterplan.get("modules",[])]
        dupes = set(x for x in ids if ids.count(x) > 1)
        assert not dupes, f"Doppelte IDs: {dupes}"

    def test_every_privacy_invariant_has_test(self, masterplan):
        missing = [f"PRIV {i['id']}" for i in masterplan.get("privacy_invariants",[])
                   if not i.get("test_tool") and not i.get("test_method")]
        assert not missing, f"Kein Test: {missing}"

    def test_module_pipeline_connected(self, masterplan):
        ids = {m["id"] for m in masterplan.get("modules",[])}
        for m in masterplan.get("modules",[]):
            for d in m.get("links",{}).get("downstream",[]):
                assert d in ids, f"{m['id']} verweist auf {d}, existiert nicht"
