# Architecture

The AgentsProtocol network is composed of three independently replaceable
layers (DevDocs v1.0 Section 1).

```
  +----------------------+      Query Layer
  |  Light clients       |      verify via block header + zkproof
  +----------^-----------+
             |
  +----------+-----------+      Consensus Layer
  |  GHOSTDAG + DAG      |      k-cluster ordering
  +----------^-----------+
             |
  +----------+-----------+      Validation Layer
  |  S_con, Psi, WiseScore|     per-claim and per-block
  +----------^-----------+
             |
         Claim inflow
```

## Recommended tech stack

- **Rust** — validator client (`src/validator/`).
- **RocksDB** — local DAG / claim storage.
- **rust-libp2p** — P2P transport (TCP/QUIC + noise + yamux).
- **risc0-zkvm** or **Nexus SDK** — zero-knowledge proof generation.
- **ONNX Runtime** + **Sentence Transformers** — reproducible embeddings.
- **ed25519-dalek** + **sha2** — cryptographic primitives.

## Module boundaries

```
validator/
  main.rs
  network/      P2P (libp2p), RPC endpoints
  consensus/    GHOSTDAG, block processing
  validation/   S_con, WiseScore, Psi-test
  zk/           zkVM interface (Nexus / RISC Zero / SP1)
  storage/      DAG, claims, blocks (RocksDB)
  stake/        token-staking logic
  config/       protocol parameters, versioning
```
