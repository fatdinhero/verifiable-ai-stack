#!/usr/bin/env python3
"""Submit a signed seed claim to a validator node.

Usage:
    python scripts/seed_claim.py [rpc_url]

Default rpc_url: http://localhost:8545

Generates a fresh Ed25519 keypair, signs a claim, and POSTs it to
POST /submit_claim. Prints the response and exits 0 on success.
"""
import hashlib
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def make_signed_claim(statement: str) -> dict:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_hex = public_key.public_bytes_raw().hex()

    payload = {
        "statement": statement,
        "entities": [],
        "predicate": "hasProperty",
        "value": {"source": "testnet-seed"},
        "evidence": [],
        "context": {"domain": "testnet"},
    }
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    message = hashlib.sha256(payload_json.encode()).digest()
    sig_hex = private_key.sign(message).hex()
    claim_id = hashlib.sha256(payload_json.encode()).hexdigest()

    return {
        "id": claim_id,
        "protocol": "agentsprotocol",
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "submitter": pub_hex,
        "signature": sig_hex,
        "statement": statement,
        "payload_json": payload_json,
    }


def wait_for_rpc(url: str, retries: int = 30, delay: float = 2.0) -> None:
    status_url = f"{url}/status"
    for i in range(retries):
        try:
            with urllib.request.urlopen(status_url, timeout=3) as r:
                if r.status == 200:
                    print(f"RPC ready at {url}")
                    return
        except Exception:
            pass
        print(f"Waiting for RPC ({i+1}/{retries})...")
        time.sleep(delay)
    raise RuntimeError(f"RPC at {url} did not become ready")


def submit_claim(url: str, claim: dict) -> dict:
    data = json.dumps(claim).encode()
    req = urllib.request.Request(
        f"{url}/submit_claim",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main() -> int:
    rpc_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8545"
    rpc_url = rpc_url.rstrip("/")

    wait_for_rpc(rpc_url)

    claim = make_signed_claim(
        "AgentsProtocol testnet genesis: semantic validation is live."
    )
    print(f"Submitting seed claim {claim['id'][:16]}...")

    try:
        response = submit_claim(rpc_url, claim)
        print(f"Response: {json.dumps(response, indent=2)}")
        if response.get("accepted"):
            print("Seed claim accepted.")
            return 0
        else:
            print("Seed claim rejected.")
            return 1
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
