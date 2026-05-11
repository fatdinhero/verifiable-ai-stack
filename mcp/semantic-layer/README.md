# MCP semantic layer

The semantic layer connects COGNITUM governance artifacts to AgentsProtocol validation.

## Scripts

- `governance_claims.py` exports masterplan modules, ADRs, and privacy invariants as deterministic bridge claims.
- `validate_governance_claims.py` validates those claims with AgentsProtocol `S_con`, `Psi`, and `check_acceptance`.

## Contract

Bridge claims are intentionally simple and stable:

```json
{
  "id": "sha256",
  "source": "cognitum/governance/masterplan.yaml",
  "kind": "module|adr|privacy_invariant",
  "statement": "human readable claim",
  "metadata": {}
}
```

They are not a replacement for AgentsProtocol signed claims. They are an integration contract for governance validation and can later be upgraded into fully signed protocol claims.
