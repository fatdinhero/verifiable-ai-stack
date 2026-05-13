# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a polyglot monorepo (`verifiable-ai-stack`) with Python 3.10+, Rust (stable), and Node 20+ components. See `README.md` for the full architecture and `CONTRIBUTING.md` for pre-submit checks.

### Key commands

All core dev tasks are available via the root `Makefile`:

- `make test-python` — cognitum, agentsprotocol, llmjson, mcp Python tests
- `make test-rust` — AgentsProtocol Rust validator (cargo test)
- `make test-node` — COS TypeScript build + Jest
- `make test-all` — smoke + all of the above
- `make audit` — governance audit quality gate
- `ruff check .` — Python linting (pre-existing warnings in repo; config in `pyproject.toml`)

### Running the VeriMCP server

```
uvicorn app:app --app-dir mcp/server --host 127.0.0.1 --port 8088
```

Endpoints: `GET /health`, `POST /governance/claims`, `POST /governance/audit`, `POST /compliance/check`. See `mcp/server/app.py` and `mcp/README.md`.

### GitHub mirror pushes

The default `origin` remote in Cursor Cloud may point at GitLab. If asked to push to the GitHub mirror (`github.com/fatdinhero/verifiable-ai-stack.git`), use the `GITHUB_TOKEN` secret for that push and avoid writing the token into committed files or persistent git remote URLs.

### Gotchas discovered during setup

- `agentsprotocol` must be installed as an editable package (`pip install -e agentsprotocol/`) before Python tests can import `agentsprotocol.s_con`. Without this, `agentsprotocol/tests/` will fail with `ModuleNotFoundError`.
- `llmjson` also needs editable install (`pip install -e llmjson/`) for its tests to find `llmjson._types`.
- `networkx` is required for `cognitum/validation/tests/test_masterplan_consistency.py` but is not listed in any requirements file.
- `httpx` is required by FastAPI's `TestClient` used in `mcp/tests/`.
- 3 pre-existing test failures exist in `llmjson/tests/test_llmjson.py` (import name mismatches: `generate` vs `_generate`, missing `validate_schema`, version string mismatch). These are not environment issues.
- Ruff reports ~959 pre-existing lint errors across the repo (mostly `E702` semicolons in test files). The `pyproject.toml` config ignores `E501`.
- `$HOME/.local/bin` must be on `PATH` for `pytest`, `ruff`, `uvicorn` to be found directly (they install there via `pip install --user`).
- COS TypeScript: `npm ci` in `civilization-operating-system/` before `npm run build` and `npm test`.
- Rust toolchain: `rustup toolchain install stable` must have been run; the VM may ship with rustup but not the stable toolchain.
