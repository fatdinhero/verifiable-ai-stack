# Getting started

## 1. Validate the monorepo layout

```bash
test -d cognitum
test -d agentsprotocol
test -d poisv/reference-impl
test -d compliance/eu-ai-act
test -d compliance/halal
test -d compliance/zkhalal-mcp
test -d mcp/server
test -d civilization-operating-system
test -d llmjson
```

## 2. Run governance checks

```bash
cd cognitum
python scripts/generate.py --validate-only
python -m pytest validation/tests tests -q
```

## 3. Run semantic validation checks

```bash
cd agentsprotocol
python -m pip install -e ".[dev]"
python -m pytest tests -q
rustup run stable cargo test --manifest-path src/validator/Cargo.toml
```

## 4. Export and validate governance claims

From the repository root:

```bash
python mcp/semantic-layer/governance_claims.py --limit 10
python mcp/semantic-layer/validate_governance_claims.py --limit 10
```

These commands are the first bridge between COGNITUM and AgentsProtocol. They do not mutate the masterplan; they produce deterministic JSON for review and future audit signing.

The canonical quality gate is:

```bash
make audit
# or
python cognitum/scripts/export_governance_claims.py --fail-on-reject
```

## 5. Work by layer

- Governance changes start in `cognitum/governance/masterplan.yaml`.
- Protocol changes start in `agentsprotocol/`.
- Scientific reference changes start in `poisv/reference-impl/`.
- Compliance changes start in `compliance/`.
- Cross-repo integration changes start in `mcp/` and `docs/architecture/`.
- Future application/platform work starts in `platform/`.
