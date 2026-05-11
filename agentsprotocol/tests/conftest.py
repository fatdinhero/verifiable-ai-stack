"""Shared pytest fixtures."""
import numpy as np
import pytest

from agentsprotocol.s_con import _stub_embed


@pytest.fixture
def rng():
    return np.random.default_rng(seed=20260418)


@pytest.fixture
def stub_embed():
    return _stub_embed


@pytest.fixture
def sample_corpus():
    return [
        "The capital of France is Paris.",
        "Water boils at 100 degrees Celsius at sea level.",
        "The Earth orbits the Sun once per year.",
    ]


@pytest.fixture
def sample_control_set():
    return {
        "statements": [
            "The capital of France is Paris.",
            "Water boils at 100 degrees Celsius at sea level.",
            "The Sun rises in the east.",
            "Birds can fly.",
        ],
        "expected_scores": [1.0, 0.98, 1.0, 0.9],
    }
