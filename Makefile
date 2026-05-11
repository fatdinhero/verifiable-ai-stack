.PHONY: help audit audit-signed smoke test-python test-rust test-node test-all clean

help:
	@echo "verifiable-ai-stack tasks"
	@echo "  make audit        Run governance audit quality gate"
	@echo "  make smoke        Run syntax and governance smoke checks"
	@echo "  make test-python  Run Python component tests"
	@echo "  make test-rust    Run AgentsProtocol Rust validator tests"
	@echo "  make test-node    Run COS TypeScript build and tests"
	@echo "  make test-all     Run all main checks"
	@echo "  make clean        Remove local runtime/test artifacts"

audit:
	python3 cognitum/scripts/export_governance_claims.py --fail-on-reject

audit-signed:
	@test -n "$$GOVERNANCE_AUDIT_HMAC_KEY" || (echo "Set GOVERNANCE_AUDIT_HMAC_KEY first" && exit 1)
	python3 cognitum/scripts/export_governance_claims.py --fail-on-reject

smoke:
	git diff --check
	python3 -m compileall -q cognitum/scripts/export_governance_claims.py mcp
	python3 cognitum/scripts/export_governance_claims.py --stdout --fail-on-reject > /tmp/verifiable-ai-stack-governance-audit.json

test-python:
	cd cognitum && python3 -m pytest validation/tests tests -q
	cd agentsprotocol && python3 -m pytest tests -q
	cd llmjson && python3 -m pytest tests -q

test-rust:
	rustup run stable cargo test --manifest-path agentsprotocol/src/validator/Cargo.toml

test-node:
	cd civilization-operating-system && npm run build && npm test -- --runInBand

test-all: smoke test-python test-rust test-node

clean:
	rm -rf .pytest_cache
	rm -rf cognitum/.pytest_cache agentsprotocol/.pytest_cache llmjson/.pytest_cache
	rm -rf agentsprotocol/src/validator/target
	rm -rf civilization-operating-system/dist civilization-operating-system/coverage
