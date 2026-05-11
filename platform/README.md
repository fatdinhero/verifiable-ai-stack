# Platform

`platform/` is reserved for future product and developer-platform surfaces built on top of the lower layers.

## Intended scope

- local-first developer dashboard,
- governance and compliance review UI,
- validation report explorer,
- release orchestration,
- optional hosted services that preserve the privacy-first architecture.

## Boundary

Platform code should depend on stable contracts from `cognitum/`, `agentsprotocol/`, `compliance/`, and `mcp/`. It should not become the source of truth for governance, compliance rules, or semantic validation algorithms.
