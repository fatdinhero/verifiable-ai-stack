# Contributing to AgentsProtocol

Contributions are organised in four phases reflecting the project roadmap.
Pick an issue labelled `good first issue` to start.

## Phase 1 — Immediate

- Implement additional language clients for the Claim parser and S_con.
- Unit tests for the JSON schema (negative cases, adversarial inputs).
- Extended control-set generation tooling.

## Phase 2 — Consensus Engine

- Synthetic Psi-test simulations with configurable attacker fractions.
- GHOSTDAG k-cluster implementation with benchmarks.

## Phase 3 — Testnet

- Local testnet without zkVM.
- RISC-V zkVM integration (Nexus / RISC Zero / SP1 backends).

## Phase 4 — Production

- Full consensus implementation.
- Security audit artefact generation.
- Testnet launch tooling.

## Workflow

1. Fork and create a feature branch.
2. Add or update tests first. `pytest tests/` must stay green.
3. Run `flake8 src/` before pushing.
4. Open a PR against `main`. CI must pass.

## Developer Certificate of Origin

By contributing you agree to the DCO: every commit must be signed off
(`git commit -s`).
