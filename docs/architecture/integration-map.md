# Integration map

## Primary flow: governance claim validation

```text
cognitum/governance/masterplan.yaml
  -> mcp/semantic-layer/governance_claims.py
  -> bridge claim JSON
  -> agentsprotocol.compute_s_con / compute_psi / check_acceptance
  -> validation report
  -> future signed VeriMCP audit artifact
```

## Compliance flow

```text
COGNITUM governance decision
  -> compliance/eu-ai-act/veriethiccore
  -> compliance/halal policy
  -> compliance/zkhalal-mcp proof tooling
  -> mcp/compliance facade
  -> governance audit trail
```

## Structured-output flow

```text
local LLM prompt
  -> llmjson schema-constrained generation
  -> JSON contract
  -> governance/compliance/semantic validation
```

## Runtime boundary rules

- `mcp/` composes; it does not duplicate component logic.
- `compliance/` evaluates; it does not decide product truth.
- `agentsprotocol/` validates claims; it does not own COGNITUM governance.
- `cognitum/` owns masterplan truth; it should consume validation reports through explicit review workflows.
- `platform/` depends on stable lower-layer contracts only.

## Near-term integration contracts

| Contract | Producer | Consumer | Status |
| --- | --- | --- | --- |
| Governance bridge claim | `mcp/semantic-layer/governance_claims.py` | AgentsProtocol validation | Initial implementation |
| Semantic validation report | `mcp/semantic-layer/validate_governance_claims.py` | COGNITUM audit workflow | Initial implementation |
| MCP service registry | `mcp/server/registry.json` | Future VeriMCP server | Initial metadata |
| Compliance domain index | `compliance/README.md` | MCP compliance facade | Initial documentation |
