# verifiable-ai-stack

**Privacy-First Wearable AI Operating System with strict governance, decentralized semantic validation, and regulatory compliance.**

`verifiable-ai-stack` is the unified monorepo for a coherent, extensible ecosystem around local-first wearable AI. It brings together governance, protocol validation, scientific foundations, compliance engines, MCP integration, structured-output tooling, and the broader civilization operating vision.

## North Star

Build a privacy-first wearable AI stack where:

- user data stays local by default,
- governance decisions are versioned and testable,
- AI-generated claims can be semantically validated,
- compliance checks are modular and auditable,
- structured outputs are machine-verifiable,
- future platform capabilities can grow without collapsing component boundaries.

## Required structure

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
├── civilization-operating-system/    # Vision & larger system
├── llmjson/                          # Helper tools & utilities
├── platform/                         # Future platform
├── docs/                             # Central documentation
│   ├── architecture/
│   ├── vision.md
│   └── getting-started.md
├── .github/workflows/
├── README.md
└── .gitignore
```

## Layer model

| Layer | Component | Responsibility |
| --- | --- | --- |
| Governance SSoT | `cognitum/` | Masterplan, ADRs, privacy invariants, DaySensOS architecture, generation pipeline. |
| Semantic protocol | `agentsprotocol/` | `S_con`, `Psi`, WiseScore, Python SDK, Rust validator, DAG/order layer. |
| Scientific base | `poisv/` | Meta-Bell Theory, Proof of WiseWork, PoISV reference implementations, notebooks, proofs. |
| Compliance | `compliance/` | EU AI Act MCP server, halal finance logic, zkHalal proof tooling. |
| Integration | `mcp/` | VeriMCP facade, routing contracts, governance-claim export, semantic validation bridge. |
| System vision | `civilization-operating-system/` | Larger Sharia-compliant system and operating backend vision. |
| Utility | `llmjson/` | Constrained JSON generation for structured, contract-safe local LLM outputs. |
| Product platform | `platform/` | Future apps, developer portal, hosted/local orchestration, dashboards. |

## What connects the repositories

The monorepo intentionally keeps each imported project independently usable, then adds small connective tissue between them:

- `mcp/semantic-layer/governance_claims.py` exports COGNITUM masterplan entries as stable bridge claims.
- `mcp/semantic-layer/validate_governance_claims.py` scores those claims through AgentsProtocol's semantic validation primitives.
- `mcp/server/registry.json` records the current MCP and service endpoints without hard-coding runtime coupling.
- `compliance/README.md` and `mcp/compliance/README.md` define how EU AI Act, halal, zkHalal, and COS responsibilities are separated.
- `docs/architecture/` documents the layer boundaries, integration map, and evolution path.

## Local development

Work from each component folder until a unified task runner is introduced.

```bash
# Governance / DaySensOS
cd cognitum
python scripts/generate.py --validate-only
python -m pytest validation/tests tests -q

# Semantic validation
cd ../agentsprotocol
python -m pip install -e ".[dev]"
python -m pytest tests -q
cd src/validator && cargo test

# Scientific references
cd ../../../poisv
python -m compileall -q reference-impl

# Compliance
cd ../compliance/eu-ai-act
python -m compileall -q veriethiccore
cd ../zkhalal-mcp
python -m compileall -q server.py

# Bridge: governance claims -> semantic validation
cd ../..
python mcp/semantic-layer/governance_claims.py --limit 5
python mcp/semantic-layer/validate_governance_claims.py --limit 5
```

## Import and history strategy

- `cognitum` was moved into `cognitum/` from the original repository root.
- `agentsprotocol`, `poisv`, `zkhalal-mcp`, `civilization-operating-system`, and `llmjson` were imported via unsquashed `git subtree`.
- Existing code remains in prefix-isolated components; new cross-repo glue lives in `mcp/`, `docs/`, `platform/`, and `compliance/`.
- Component-specific licenses remain authoritative inside their folders.

## Strategic next step

The first production-grade integration should be:

1. Export COGNITUM masterplan and ADR statements as bridge claims.
2. Validate those claims with AgentsProtocol `S_con` and `Psi`.
3. Attach compliance findings from EU AI Act and halal modules.
4. Emit a signed audit artifact through the future VeriMCP server.
5. Use `llmjson` for schema-safe local LLM outputs in every governance/compliance flow.
