# Changelog

All notable changes to AgentsProtocol are documented here.

## [1.3.0] — 2026-05-11

### Summary

Production-ready release. Supersedes v1.2.0 (initial draft).
Full Phase 3 + Phase 4 implementation with CI-verified test suite
(68 Python + 48 Rust = 116 tests).

### Added vs v1.2.0

- Phase 3: embedding sidecar (sentence-transformers), bootstrap peer dialing, simplified Dockerfile
- Phase 4: ZK proof abstraction (MockZkBackend + Risc0 skeleton), GET /verify_block/:hash RPC
- GitLab CI (.gitlab-ci.yml)
- CHANGELOG.md
- Trusted Publisher PyPI workflow (publish.yml)

### Changed

- Storage: rocksdb → sled (pure Rust, no libclang)
- Tagline: "makes AI-generated knowledge verifiable"
- Test count: 62 → 116 (68 Python + 48 Rust)

---

## [1.0.0] — 2026-05-11

### Summary

First stable release. Complete reference implementation of the PoISV protocol
with Python SDK, Rust validator node, ZK proof abstraction, P2P networking,
and CI-verified test suite (68 Python + 48 Rust = 116 tests).

### Added

**Protocol core (Python)**
- `compute_s_con` — semantic consistency score via cosine similarity
- `compute_psi` — non-collusion statistic (Pearson correlation of error vectors)
- `compute_wise_score_aggregate` — composite WiseScore (T × C × R × E)
- `verify_claim_signature` — Ed25519 claim signature verification
- `check_acceptance` — combined S_con + Psi acceptance gate
- JSON schemas for claims and control sets

**Rust validator node**
- `ClaimMempool` — max-heap sorted by S_con score
- `BlockProducer` — drains mempool, computes Psi, assembles blocks
- `DagStore` — sled-backed storage (claims + blocks trees)
- `Ghostdag` — GHOSTDAG parent selection
- `ProtocolConfig` — all parameters via environment variables
- P2P gossipsub over TCP/noise/yamux (libp2p 0.54)
- Bootstrap peer dialing via `AP_BOOTSTRAP_PEERS`
- axum RPC: `POST /submit_claim`, `GET /get_block/:hash`, `GET /verify_block/:hash`, `GET /status`

**ZK proof abstraction (Phase 4)**
- `ZkBackend` trait — `prove_block` / `verify_block`
- `ZkBlockInput` — deterministic canonical JSON (sorted claim_ids, fixed-precision floats)
- `ZkProof` struct — backend, proof_type, commitment, public_inputs_hash
- `MockZkBackend` — SHA-256 development commitment (not a cryptographic ZK proof)
- `Risc0ZkBackend` skeleton behind `--features zkvm-risc0`
- `GET /verify_block/:hash` RPC endpoint with explicit `warning` field for mock backend

**Infrastructure**
- Embedding sidecar (`embed/`) — sentence-transformers all-MiniLM-L6-v2, FastAPI
- HTTP embedder in Rust behind `--features http-embed`
- docker-compose 3-node testnet with embed service and bootstrap wiring
- GitHub Actions CI: Python 3.10/3.11/3.12 + Rust stable + release smoke tests
- `.gitignore`, `detect/requirements.txt`, `embed/requirements.txt`

### Changed

- Storage backend: rocksdb → sled (pure Rust, no libclang dependency)
- Dockerfile: removed clang/libclang, smaller image
- Tagline: "proves the content is true" → "makes AI-generated knowledge verifiable"
- Test count unified to 116 across all documentation

### Security

- Ed25519 signatures verified via ed25519-dalek v2
- Mock ZK backend explicitly labelled as non-cryptographic in all RPC responses
- No secrets or private keys committed to repository

### Roadmap

- **v1.1** — Real zkVM backend (RISC Zero guest program), mDNS peer discovery
- **v1.2** — Docker testnet end-to-end test, PyPI release
- **v2.0** — Security audit, tokenomics, testnet launch

---

## [0.x] — 2026-04-18

Initial research implementation. Bitcoin-timestamped at block 945622.
DOI: [10.5281/zenodo.19642292](https://doi.org/10.5281/zenodo.19642292)
