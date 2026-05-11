# verifiable-ai-stack

[![Monorepo Smoke](https://github.com/fatdinhero/verifiable-ai-stack/actions/workflows/monorepo-smoke.yml/badge.svg)](https://github.com/fatdinhero/verifiable-ai-stack/actions/workflows/monorepo-smoke.yml)
[![Governance Audit](https://github.com/fatdinhero/verifiable-ai-stack/actions/workflows/governance-audit.yml/badge.svg)](https://github.com/fatdinhero/verifiable-ai-stack/actions/workflows/governance-audit.yml)
![License](https://img.shields.io/badge/license-mixed%20component%20licenses-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Rust](https://img.shields.io/badge/rust-stable-orange)
![Node](https://img.shields.io/badge/node-20-green)

**Privacy-First Wearable AI Operating System with strict governance, decentralized semantic validation, and regulatory compliance.**

`verifiable-ai-stack` is a professional monorepo for a local-first, auditable AI ecosystem. It combines COGNITUM governance, AgentsProtocol semantic validation, PoISV scientific foundations, compliance engines, MCP integration, structured-output utilities, and a future platform layer.

## Why this repository exists

Modern wearable AI needs more than model output. It needs traceable governance, validation, privacy boundaries, and compliance evidence. This monorepo is organized so that:

- user and sensor data stay local by default,
- `cognitum/governance/masterplan.yaml` remains the governance Single Source of Truth,
- governance statements become verifiable claims,
- AgentsProtocol scores those claims with `S_con`, `Psi`, and `check_acceptance`,
- audit reports are hash-addressable and optionally signed,
- regulatory modules stay separate from protocol and product logic,
- future platform work can grow on stable contracts.

## Architecture at a glance

```text
COGNITUM governance SSoT
  -> governance claims
  -> AgentsProtocol semantic validation
  -> governance audit report
  -> future VeriMCP facade
  -> compliance and platform workflows
```

## Repository structure

```text
verifiable-ai-stack/
├── cognitum/                         # Governance & Single Source of Truth
│   ├── governance/
│   ├── scripts/
│   ├── daysensos/
│   └── crews/
├── agentsprotocol/                   # Semantic validation & protocol
│   ├── src/
│   ├── tests/
│   └── docs/
├── poisv/                            # Scientific foundation
│   ├── whitepapers/
│   └── reference-impl/
├── compliance/                       # Regulatory layer
│   ├── eu-ai-act/
│   ├── halal/
│   └── zkhalal-mcp/
├── mcp/                              # VeriMCP integration layer
│   ├── server/
│   ├── compliance/
│   └── semantic-layer/
├── civilization-operating-system/    # Larger system vision
├── llmjson/                          # Structured-output utilities
├── platform/                         # Future product/platform surface
├── docs/                             # Central documentation
│   ├── architecture/
│   ├── governance-audit/
│   ├── vision.md
│   └── getting-started.md
├── .github/workflows/
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
├── README.md
└── .gitignore
```

## Layers and responsibilities

| Layer | Path | Responsibility |
| --- | --- | --- |
| Governance SSoT | `cognitum/` | Masterplan, ADRs, privacy invariants, DaySensOS architecture, generated agent context. |
| Semantic validation | `agentsprotocol/` | `S_con`, `Psi`, WiseScore, Python SDK, Rust validator, DAG/order layer. |
| Scientific foundation | `poisv/` | Meta-Bell Theory, Proof of WiseWork, PoISV references, notebooks, proofs. |
| Compliance | `compliance/` | EU AI Act, halal policy, zkHalal proof tooling. |
| Integration | `mcp/` | VeriMCP routing, registry metadata, compatibility wrappers. |
| System vision | `civilization-operating-system/` | Sharia-compliant backend and larger operating-system concept. |
| Utilities | `llmjson/` | Schema-constrained JSON generation for local LLM workflows. |
| Platform | `platform/` | Future UI, developer portal, orchestration, dashboards. |

## Governance audit quality gate

The first production-grade integration is already implemented:

```bash
python cognitum/scripts/export_governance_claims.py --fail-on-reject
```

It reads `cognitum/governance/masterplan.yaml`, exports governance claims for constitution articles, ADRs, modules, ISO 23894 risks, and privacy invariants, then validates them with AgentsProtocol.

Audit reports are written to:

```text
docs/governance-audit/YYYY-MM-DD_HH-MM.json
docs/governance-audit/latest.json
```

Reports include:

- report schema and version,
- report ID, Git commit/status, runtime and dependency metadata,
- SHA-256 of the masterplan source,
- SHA-256 of each original claim,
- report payload SHA-256,
- optional HMAC-SHA256 signature via `GOVERNANCE_AUDIT_HMAC_KEY`,
- VDI 2221/2225 and ISO 25010 quality-model metadata,
- multi-validator `Psi` support.

See [`docs/governance-audit/README.md`](docs/governance-audit/README.md).
For GitHub branch protection, require the `Cognitum Governance Audit / governance-audit` status check; see [`.github/required-checks.md`](.github/required-checks.md).

## Quick start

```bash
# Clone
git clone https://github.com/fatdinhero/verifiable-ai-stack.git
cd verifiable-ai-stack

# Run the governance audit quality gate
python -m pip install pyyaml numpy scipy pydantic
python cognitum/scripts/export_governance_claims.py --fail-on-reject

# Or use the root task runner
make audit

# Run core Python tests
cd cognitum
python -m pytest validation/tests tests -q

cd ../agentsprotocol
python -m pytest tests -q

# Run Rust validator tests
cd ..
rustup run stable cargo test --manifest-path agentsprotocol/src/validator/Cargo.toml

# Run COS TypeScript smoke
cd civilization-operating-system
npm ci
npm run build
npm test -- --runInBand
```

## CI/CD

Root workflows:

- `.github/workflows/monorepo-smoke.yml` checks structure, Python syntax, Rust validator tests, and TypeScript build.
- `.github/workflows/governance-audit.yml` runs the governance audit as a quality gate and uploads the generated report artifact.

## Root task runner

Common tasks are available through `make`:

```bash
make audit
make smoke
make test-python
make test-rust
make test-node
make test-all
```

## Documentation

- [Vision](docs/vision.md)
- [Getting started](docs/getting-started.md)
- [Layer architecture](docs/architecture/layers.md)
- [Integration map](docs/architecture/integration-map.md)
- [Quality standards](docs/architecture/quality-standards.md)
- [Governance audit](docs/governance-audit/README.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Import and history strategy

- `cognitum` was moved into `cognitum/` from the original repository root.
- `agentsprotocol`, `poisv`, `zkhalal-mcp`, `civilization-operating-system`, and `llmjson` were imported via unsquashed `git subtree`.
- Existing code remains prefix-isolated.
- Cross-repo glue lives in `cognitum/scripts/`, `mcp/`, `docs/`, `platform/`, and `compliance/`.

## Licensing

This monorepo aggregates components with different license terms. The root [`LICENSE`](LICENSE) is an aggregation notice. Component-level license files remain authoritative.

## Security

Do not open public issues for vulnerabilities or secret exposure. Follow [`SECURITY.md`](SECURITY.md).
