# Quality standards

This monorepo follows practical software-engineering standards for a mixed Python, Rust, TypeScript, and documentation codebase.

## Baseline standards

- **Clear ownership:** every layer has a documented responsibility.
- **Small integration seams:** cross-component logic belongs in `mcp/` and should call stable APIs.
- **Repeatable checks:** CI starts with structure, syntax, Python, Rust, and TypeScript smoke checks.
- **Traceable governance:** governance-critical changes should reference COGNITUM masterplan or ADR artifacts.
- **No implicit data retention:** tests and examples must not depend on private user data.
- **Schema-first outputs:** machine-readable outputs should use stable JSON contracts.

## Python

- Prefer explicit module boundaries over path side effects.
- Keep bridge scripts deterministic and side-effect free by default.
- Use `python -m compileall` as a minimum smoke check for imported code.
- Use component-level test suites for behavioral validation.

## Rust

- Validate the AgentsProtocol validator with `cargo test`.
- Keep lockfiles reproducible where applications or binaries are involved.
- Use current stable Rust in CI and local validation.

## TypeScript

- Use `npm ci` for reproducible installs.
- Treat `npm run build` as the minimum COS smoke check.

## Documentation

- Root README explains the whole system.
- `docs/architecture/` explains cross-repo decisions.
- Component READMEs remain the source for local component usage.

## Future hardening

- Add a root task runner (`just`, `make`, or `nox`) once commands stabilize.
- Add schema validation for MCP registry and bridge reports.
- Add signed audit artifact generation after the semantic validation bridge matures.
