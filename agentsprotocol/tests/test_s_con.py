"""Unit tests for S_con (DevDocs Section 3)."""
import numpy as np
import pytest

from agentsprotocol.s_con import (
    compute_s_con,
    cosine_similarity,
    _stub_embed,
    _stub_retrieve_facts,
)


def test_cosine_identical_vectors():
    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_opposite_vectors():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_zero_vector_returns_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_stub_embed_deterministic():
    assert np.allclose(_stub_embed("hello"), _stub_embed("hello"))


def test_stub_embed_different_inputs_differ():
    assert not np.allclose(_stub_embed("a"), _stub_embed("b"))


def test_stub_embed_dim():
    assert _stub_embed("x").shape == (384,)


def test_stub_retrieve_facts_list_passthrough():
    facts = ["f1", "f2"]
    assert _stub_retrieve_facts(facts, "claim") == facts


def test_stub_retrieve_facts_dict():
    out = _stub_retrieve_facts({"a": "one", "b": 2, "c": "two"}, "claim")
    assert sorted(out) == ["one", "two"]


def test_s_con_zero_below_threshold():
    # low similarity -> clipped to 0
    score = compute_s_con("unrelated claim text xyz",
                          ["totally different subject matter"], tau=0.9)
    assert score == 0.0


def test_s_con_empty_corpus():
    assert compute_s_con("anything", [], tau=0.7) == 0.0


def test_s_con_high_similarity_with_same_text():
    txt = "The sky is blue."
    # cosine(v, v) = 1; with tau=0.7 the normalised score is 1.0
    score = compute_s_con(txt, [txt], tau=0.7)
    assert score == pytest.approx(1.0)


def test_s_con_range_bounded():
    for tau in (0.0, 0.3, 0.7, 0.99):
        score = compute_s_con("claim", ["claim", "claim2"], tau=tau)
        assert 0.0 <= score <= 1.0


def test_s_con_invalid_tau_raises():
    with pytest.raises(ValueError):
        compute_s_con("x", ["y"], tau=1.0)
    with pytest.raises(ValueError):
        compute_s_con("x", ["y"], tau=-0.1)


def test_s_con_custom_embed_used():
    called = {"count": 0}

    def custom(_text):
        called["count"] += 1
        return [1.0] * 4

    compute_s_con("claim", ["fact1", "fact2"], embed=custom, tau=0.5)
    # one embed for claim, two for facts = 3 calls
    assert called["count"] == 3


def test_s_con_monotone_in_tau():
    # Higher tau => lower (or equal) normalised score for fixed cos_sim < 1
    scores = []
    for tau in (0.0, 0.3, 0.5, 0.8):
        # slightly different texts -> cos < 1
        scores.append(compute_s_con("The sky is blue.",
                                    ["The sky appears blue."], tau=tau))
    # not strictly monotone in general (can clip to 0), but once positive
    # should be non-increasing
    positive = [s for s in scores if s > 0]
    assert positive == sorted(positive, reverse=True)
