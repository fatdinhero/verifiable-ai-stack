"""End-to-end integration test: Claim -> validators -> block acceptance."""
import numpy as np
import pytest

from agentsprotocol.psi_test import compute_error_vectors
from agentsprotocol.schemas import Claim
from agentsprotocol.validator import BlockProposal, Validator, block_weight


SAMPLE_CLAIM = {
    "protocol": "agentsprotocol",
    "version": "1.0",
    "type": "claim",
    "id": "0x7a9f3c",
    "timestamp": "2026-04-18T14:30:00Z",
    "submitter": "0x1234abcd",
    "signature": "0xef56",
    "payload": {
        "statement": "The temperature in Berlin is 20 degrees Celsius.",
        "entities": [{"name": "Berlin", "type": "location", "uri": "wikidata:Q64"}],
        "predicate": "hasTemperature",
        "value": {"amount": 20, "unit": "Celsius"},
        "evidence": [{"type": "sensor", "uri": "ipfs://QmT",
                      "timestamp": "2026-04-18T14:25:00Z"}],
        "context": {"domain": "Weather", "knowledgeCorpus": "ipfs://QmK"},
    },
}


def test_sample_claim_parses():
    claim = Claim.model_validate(SAMPLE_CLAIM)
    assert claim.payload.statement.startswith("The temperature in Berlin")


def test_sample_claim_rejects_wrong_protocol():
    bad = dict(SAMPLE_CLAIM)
    bad["protocol"] = "other"
    with pytest.raises(Exception):
        Claim.model_validate(bad)


def test_block_weight_formula():
    assert block_weight(0.9, [0.8, 0.7, 0.6]) == pytest.approx(0.9 * 2.1)
    assert block_weight(0.0, [1.0, 1.0]) == 0.0


def test_independent_validators_accept():
    # Build a scenario where each validator uses a slightly different embed
    # so error vectors on the control set are uncorrelated.
    rng = np.random.default_rng(7)

    def make_embed(bias):
        def _e(text):
            import hashlib
            h = hashlib.sha256((bias + text).encode()).digest()
            vec = np.frombuffer(h * 12, dtype=np.uint8)[:384].astype(float) - 127.5
            n = np.linalg.norm(vec)
            return vec / n if n > 0 else vec
        return _e

    validators = [Validator(pubkey=f"v{i}", stake=float(i + 1),
                            embed=make_embed(f"bias-{i}-"))
                  for i in range(4)]
    corpus = ["The temperature in Berlin is 20 degrees Celsius.",
              "Berlin weather today: mild and sunny."]

    # claims all match the corpus statements closely
    claim_texts = [
        "The temperature in Berlin is 20 degrees Celsius.",
        "Berlin is experiencing mild weather.",
    ]
    # Pearson correlation needs k >= 3 to avoid degenerate rho = +-1; use
    # the full 4-task control set from DevDocs Section 4.1.
    control = [
        "The capital of France is Paris.",
        "Water boils at 100 degrees Celsius at sea level.",
        "The Sun rises in the east.",
        "Birds can fly.",
        "Gold is a chemical element.",
    ]
    refs = [1.0, 0.98, 1.0, 0.9, 0.95]

    proposal = BlockProposal(
        claim_texts=claim_texts, corpus=corpus, validators=validators,
        control_statements=control, reference_scores=refs,
        tau=0.0, theta_min=0.3, psi_min=0.1, use_weighted_psi=True,
    )
    decision = proposal.decide()
    assert decision.accepted, decision.reason


def test_colluding_validators_rejected():
    # Two identical validators -> Psi drops below threshold even with
    # strong S_con, so acceptance must fail.
    v = Validator(pubkey="v", stake=1.0)
    validators = [v, Validator(pubkey="w", stake=1.0,
                               embed=v.embed, retrieve_facts=v.retrieve_facts)]
    corpus = ["a test fact"]
    control = ["s1", "s2", "s3", "s4"]
    refs = [0.5, 0.5, 0.5, 0.5]

    proposal = BlockProposal(
        claim_texts=["claim"], corpus=corpus, validators=validators,
        control_statements=control, reference_scores=refs,
        tau=0.0, theta_min=0.0, psi_min=0.5, use_weighted_psi=False,
    )
    decision = proposal.decide()
    # error vectors identical -> Psi = 0
    assert decision.psi == pytest.approx(0.0, abs=1e-9)
    assert not decision.accepted


def test_error_vectors_shape_roundtrip():
    scores = [[0.9, 0.8, 1.0], [0.7, 0.95, 0.88]]
    ref = [1.0, 0.9, 0.95]
    ev = compute_error_vectors(scores, ref)
    assert len(ev[0]) == 3
    assert all(x >= 0 for row in ev for x in row)
