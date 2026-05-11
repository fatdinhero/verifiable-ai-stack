"""Attacker-catchup probability — thin wrapper."""
from agentsprotocol.wise_score import attacker_success_probability

def attacker_success(q, z):
    return attacker_success_probability(q, z)
