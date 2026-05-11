# MCP semantic layer

The semantic layer connects COGNITUM governance artifacts to AgentsProtocol validation.

## Scripts

- `governance_claims.py` is a compatibility wrapper around the canonical COGNITUM exporter.
- `validate_governance_claims.py` is a compatibility wrapper around the canonical COGNITUM validator.

The canonical implementation lives in:

```text
cognitum/scripts/export_governance_claims.py
```

because COGNITUM owns `governance/masterplan.yaml`.

## Contract

Bridge claims are intentionally simple and stable:

```json
{
  "id": "sha256",
  "source": "cognitum/governance/masterplan.yaml",
  "kind": "module|architecture_decision|risk|privacy_invariant",
  "statement": "human readable claim",
  "metadata": {}
}
```

They are not a replacement for AgentsProtocol signed claims. They are an integration contract for governance validation and can later be upgraded into fully signed protocol claims.
