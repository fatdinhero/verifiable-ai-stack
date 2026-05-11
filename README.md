# AgentsProtocol

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19642292.svg)](https://doi.org/10.5281/zenodo.19642292)
[![Radicle](https://img.shields.io/badge/Radicle-rad:z2rcpKt6WkzXsdyPs9shwnrtpcPmS-blue)](https://app.radicle.xyz/nodes/iris.radicle.xyz/rad:z2rcpKt6WkzXsdyPs9shwnrtpcPmS)
![Bitcoin Block](https://img.shields.io/badge/Bitcoin_Block-945622-orange)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)
![CI](https://github.com/fatdinhero/agentsprotocol/actions/workflows/ci.yml/badge.svg)

> **AgentsProtocol makes AI-generated knowledge verifiable.**

An open protocol and reference implementation for decentralised **semantic**
validation. Every claim is scored against a public knowledge corpus (S_con),
every block is gated by a statistical non-collusion test (Psi), and only
blocks that clear both thresholds enter the canonical DAG.

## Research Pillars

| Layer | Contribution | Reference |
|---|---|---|
| MBT | Statistical certificate of validator independence (Psi) | Meta-Bell Theory (Dinc, 2026) |
| PoWW | Composite truth score T × C × R × E | Proof of WiseWork v2 (Dinc, 2026) |
| PoISV | Operational protocol: S_con + Psi + GHOSTDAG ordering | PoISV Whitepaper v1.0 (Dinc, 2026) |
| Bell-SPVU | Formal proof: Ψ ≈ 1 − \|Ŝ\|/(2√2) | [Bell-SPVU Paper](https://doi.org/10.5281/zenodo.19656679) |

## Quick Start

```bash
pip install agentsprotocol==1.3.0
```

```python
from agentsprotocol import compute_s_con, compute_psi, check_acceptance

s   = compute_s_con("The sky is blue.", ["The sky is blue."], tau=0.7)
psi = compute_psi([[0.1, 0.2, 0.3, 0.4], [0.3, 0.2, 0.1, 0.4]])
print(check_acceptance([s], psi, theta_min=0.6, psi_min=0.3))
```

Full demo: `examples/demo.py`

## Repository Structure

```
agentsprotocol/
├── src/agentsprotocol/     Python reference implementation (S_con, Psi, WiseScore, schemas)
├── src/validator/          Rust validator node (tokio, libp2p gossipsub, sled, axum RPC)
├── detect/                 FastAPI demo backend (POST /validate, GET /health)
├── tests/                  pytest suite — 105 tests, all green (68 Python + 37 Rust)
├── examples/               Runnable demos
├── scripts/                seed_claim.py — generates signed genesis claim
├── docker-compose.yml      3-node local testnet
└── .github/workflows/      CI: Python 3.10/3.11/3.12 + Rust stable
```

## Architecture

```
  Claim (JSON + Ed25519 sig)
        │
        ▼
  RPC /submit_claim  (axum, port 8545)
        │
        ▼
  verify_claim_signature()   ← ed25519-dalek
        │
        ▼
  ClaimMempool  (max-heap, sorted by S_con score)
        │
        ▼
  BlockProducer  (drains mempool every N secs or M claims)
        │  computes Psi, GHOSTDAG parent selection
        ▼
  DagStore  (sled, two trees: claims / blocks)
        │
        ▼
  P2P gossipsub  (libp2p 0.54, TCP/noise/yamux)
```

## Running Locally

**Python library:**
```bash
pip install -e ".[dev]"
pytest tests/ -v
```

**Rust validator:**
```bash
cd src/validator
cargo test
cargo run
```

**3-node testnet:**
```bash
docker compose up --build
curl http://localhost:8545/status
```

**detect/ API:**
```bash
pip install -r detect/requirements.txt
uvicorn detect.api:app --reload --port 8000
```

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | S_con, Psi, WiseScore, JSON-schema, Ed25519 signatures | ✅ Done |
| 2 | GHOSTDAG consensus, sled storage, gossipsub P2P, axum RPC | ✅ Done |
| 3 | Real embeddings (ONNX/fastembed), mDNS peer discovery, docker testnet | 🔧 In progress |
| 4 | ZK-proof integration (RISC Zero / Nexus), security audit, testnet launch | Planned |

## Citation

```bibtex
@software{dinc_agentsprotocol_2026,
  author    = {Fatih Dinc},
  title     = {AgentsProtocol: Reference Implementation},
  year      = 2026,
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.19642292},
  url       = {https://github.com/fatdinhero/agentsprotocol}
}
```

## License

Code: Apache-2.0 (`LICENSE-CODE`). Documentation: CC BY 4.0 (`LICENSE-DOCS`).

## Timestamp

All contents are included in the SHA-256 hash attested on
**Bitcoin block 945622 (2026-04-18)**.

---

**Author:** Fatih Dinc — `fatdinhero@gmail.com` — Pforzheim, Germany.
