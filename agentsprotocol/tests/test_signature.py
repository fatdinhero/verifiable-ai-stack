"""Tests for Ed25519 claim signature verification."""
import hashlib
import json

import pytest

from agentsprotocol.validator import verify_claim_signature


def _make_signed_claim(payload: dict) -> dict:
    """Generate a real Ed25519 keypair and sign a claim payload."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    pub_bytes = public_key.public_bytes_raw()
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    message = hashlib.sha256(payload_bytes).digest()
    sig_bytes = private_key.sign(message)

    return {
        "protocol": "agentsprotocol",
        "version": "1.0",
        "type": "claim",
        "id": hashlib.sha256(payload_bytes).hexdigest(),
        "timestamp": "2026-04-18T14:30:00Z",
        "submitter": pub_bytes.hex(),
        "signature": sig_bytes.hex(),
        "payload": payload,
    }


PAYLOAD = {
    "statement": "The sky is blue.",
    "entities": [],
    "predicate": "hasProperty",
    "value": {"color": "blue"},
}


def test_valid_signature_accepted():
    claim = _make_signed_claim(PAYLOAD)
    assert verify_claim_signature(claim) is True


def test_tampered_payload_rejected():
    claim = _make_signed_claim(PAYLOAD)
    # Modify payload after signing
    claim["payload"]["statement"] = "The sky is red."
    assert verify_claim_signature(claim) is False


def test_wrong_signature_rejected():
    claim = _make_signed_claim(PAYLOAD)
    # Replace signature with random bytes
    claim["signature"] = "00" * 64
    assert verify_claim_signature(claim) is False


def test_wrong_pubkey_rejected():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    claim = _make_signed_claim(PAYLOAD)
    # Replace submitter with a different public key
    other_key = Ed25519PrivateKey.generate().public_key()
    claim["submitter"] = other_key.public_bytes_raw().hex()
    assert verify_claim_signature(claim) is False


def test_missing_fields_returns_false():
    assert verify_claim_signature({}) is False
    assert verify_claim_signature({"submitter": "aa", "signature": "bb"}) is False


def test_invalid_hex_returns_false():
    claim = _make_signed_claim(PAYLOAD)
    claim["signature"] = "not-hex!"
    assert verify_claim_signature(claim) is False
