# Contributing to verifiable-ai-stack

This monorepo is organized as a layered system. Contributions should preserve clear ownership boundaries and keep COGNITUM's `governance/masterplan.yaml` as the governance Single Source of Truth.

## Development principles

1. **Separation of concerns:** change the layer that owns the behavior.
2. **No hidden coupling:** cross-repo integration belongs in `mcp/`, `docs/architecture/`, or explicit public APIs.
3. **Governance first:** product, compliance, and architecture decisions that affect the stack should be represented in COGNITUM governance artifacts.
4. **Local-first validation:** tests and smoke checks should not require private user data.
5. **Structured outputs:** machine-consumed LLM output should use schemas and, where appropriate, `llmjson`.

## Layer ownership

| Path | Owns |
| --- | --- |
| `cognitum/` | Governance, masterplan, ADRs, DaySensOS, generated agent context. |
| `agentsprotocol/` | Semantic validation protocol, Python SDK, Rust validator. |
| `poisv/` | Scientific foundation and reference implementations. |
| `compliance/` | EU AI Act, halal, zkHalal, and related regulatory tools. |
| `mcp/` | VeriMCP composition, routing, bridge scripts, integration contracts. |
| `civilization-operating-system/` | Larger COS backend and vision. |
| `llmjson/` | Structured JSON generation utility. |
| `platform/` | Future application and platform surfaces. |

## Before opening a change

Run the checks relevant to the touched layers:

```bash
python -m compileall -q mcp llmjson/llmjson compliance/eu-ai-act/veriethiccore compliance/zkhalal-mcp/server.py

cd cognitum
python -m pytest validation/tests tests -q

cd ../agentsprotocol
python -m pytest tests -q
rustup run stable cargo test --manifest-path src/validator/Cargo.toml
```

For TypeScript changes:

```bash
cd civilization-operating-system
npm ci
npm run build
```

## Import policy

External repositories are imported with unsquashed `git subtree` where history preservation matters. Do not replace imported component histories with copied snapshots.

## Documentation policy

- Component-specific docs remain inside the component.
- Cross-component architecture and integration docs live under `docs/`.
- Public bridge contracts should be documented before they become runtime-critical.
