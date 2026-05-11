# Layer architecture

## 1. Governance layer: `cognitum/`

COGNITUM owns the Single Source of Truth. The masterplan, ADRs, privacy invariants, DaySensOS architecture, and generated agent context live here.

Rule: cross-repo integrations may read COGNITUM governance data, but they should not mutate it without an explicit governance workflow.

## 2. Semantic validation layer: `agentsprotocol/`

AgentsProtocol owns claim validation primitives:

- semantic consistency (`S_con`),
- validator independence (`Psi`),
- WiseScore,
- Rust validator and DAG logic.

Rule: integrations should call stable public APIs from `agentsprotocol/src/agentsprotocol/`.

## 3. Scientific foundation: `poisv/`

PoISV owns the research and reference implementation base. The code has been organized under `poisv/reference-impl/` while whitepaper placeholders and proofs remain visible at the scientific layer.

Rule: production validation should cite PoISV concepts but depend on AgentsProtocol APIs unless a research prototype explicitly needs reference code.

## 4. Compliance layer: `compliance/`

Compliance is split by domain:

- `eu-ai-act/` for EU AI Act checks,
- `halal/` for shared halal compliance documentation and policy,
- `zkhalal-mcp/` for zero-knowledge Sharia compliance tooling.

Rule: compliance modules return structured findings. They do not own product truth; COGNITUM governance decides how findings affect releases.

## 5. MCP integration layer: `mcp/`

MCP is the facade layer for tools that need to combine governance, semantic validation, and compliance. It contains routing metadata and first bridge scripts.

Rule: MCP code composes components; it should not fork their business logic.

## 6. Utilities and platform

- `llmjson/` provides schema-safe local LLM output.
- `civilization-operating-system/` contributes the wider Sharia-compliant operating-system vision.
- `platform/` is reserved for product and developer-platform surfaces.

Rule: platform work must depend on explicit interfaces from lower layers.
