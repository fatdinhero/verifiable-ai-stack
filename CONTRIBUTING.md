# Contributing to verifiable-ai-stack

Thank you for contributing. This monorepo is a layered system for privacy-first wearable AI, semantic validation, and compliance. Contributions should improve the system without weakening governance traceability, privacy boundaries, or component ownership.

## Engineering principles

1. **Single Source of Truth:** COGNITUM governance starts in `cognitum/governance/masterplan.yaml`.
2. **Separation of concerns:** change the layer that owns the behavior.
3. **No hidden coupling:** cross-component integration belongs in documented APIs, `mcp/`, or central `docs/`.
4. **Auditability:** governance and compliance changes should be reproducible and reviewable.
5. **Local-first validation:** tests and examples must not require private user data.
6. **Schema-first outputs:** machine-consumed LLM output should use explicit JSON contracts.

## Layer ownership

| Path | Owns |
| --- | --- |
| `cognitum/` | Governance, masterplan, ADRs, DaySensOS, generated agent context. |
| `agentsprotocol/` | Semantic validation protocol, Python SDK, Rust validator. |
| `poisv/` | Scientific foundation and reference implementations. |
| `compliance/` | EU AI Act, halal, zkHalal, and related regulatory tools. |
| `mcp/` | VeriMCP composition, routing, compatibility wrappers, integration contracts. |
| `civilization-operating-system/` | Larger COS backend and system vision. |
| `llmjson/` | Structured JSON generation utility. |
| `platform/` | Future application and developer-platform surfaces. |
| `docs/` | Cross-component architecture, quality, and integration documentation. |

## Development setup

Use the component-native tooling. A full environment usually needs:

- Python 3.10+
- Rust stable
- Node 20+
- `pytest`, `pyyaml`, `numpy`, `scipy`, `pydantic`

## Required checks before submitting

Run checks for the layers you touched. For broad changes, run:

```bash
make smoke
make test-python
make test-rust
make test-node
```

Equivalent manual commands:

```bash
git diff --check
python -m compileall -q \
  cognitum \
  agentsprotocol/src/agentsprotocol \
  agentsprotocol/detect \
  poisv/reference-impl \
  compliance/eu-ai-act/veriethiccore \
  compliance/zkhalal-mcp/server.py \
  llmjson/llmjson \
  mcp

python cognitum/scripts/export_governance_claims.py --fail-on-reject

cd cognitum
python -m pytest validation/tests tests -q

cd ../agentsprotocol
python -m pytest tests -q

cd ..
rustup run stable cargo test --manifest-path agentsprotocol/src/validator/Cargo.toml

cd llmjson
python -m pytest tests -q

cd ../civilization-operating-system
npm ci
npm run build
npm test -- --runInBand
```

## Governance audit changes

If you change `cognitum/governance/masterplan.yaml` or `cognitum/scripts/export_governance_claims.py`, regenerate and inspect:

```bash
python cognitum/scripts/export_governance_claims.py --fail-on-reject
```

Tracked audit files:

- `docs/governance-audit/latest.json`
- selected minute-versioned reports under `docs/governance-audit/`

Do not commit secrets. Signing uses the `GOVERNANCE_AUDIT_HMAC_KEY` environment variable.

## Import policy

External repositories should be imported with unsquashed `git subtree` when history preservation matters. Do not replace imported component histories with copied snapshots.

## Documentation policy

- Component-specific docs remain inside the component.
- Cross-component architecture and integration docs live under `docs/`.
- Public bridge contracts should be documented before they become runtime-critical.

## Pull request quality bar

A high-quality change should include:

- concise scope,
- tests or smoke checks,
- documentation for cross-layer behavior,
- no unrelated refactors,
- no generated noise unless explicitly required,
- clean `git diff --check`.

## Code ownership

Root CODEOWNERS live in `.github/CODEOWNERS`. Governance, audit, compliance, and protocol changes require owner review in regulated workflows.
