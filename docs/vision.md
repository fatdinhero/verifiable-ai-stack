# Vision

`verifiable-ai-stack` is a long-term architecture for privacy-first wearable AI with governance, semantic validation, and compliance built in from the beginning.

## Core idea

Wearable AI should not become another opaque cloud data exhaust system. The stack is designed around a different premise:

1. Personal sensor data remains local by default.
2. Product and governance rules are explicit, versioned, and testable.
3. AI outputs are converted into claims that can be checked.
4. Claims are scored by semantic consistency and validator independence.
5. Compliance is modular, auditable, and routed through clear interfaces.
6. Local LLM outputs use structured schemas whenever they cross a trust boundary.

## System thesis

COGNITUM defines what the system is allowed to do. AgentsProtocol and PoISV define how claims become verifiable. Compliance modules define which regulatory and ethical constraints apply. MCP provides the integration fabric. llmjson hardens LLM output formats. The platform layer can then grow without weakening the privacy and verification core.

## Non-negotiable invariants

- COGNITUM `governance/masterplan.yaml` remains the governance Single Source of Truth.
- Component boundaries stay explicit.
- Cross-repo glue lives outside imported component internals unless a component intentionally adopts it.
- No user data is required for repository-level validation.
- Compliance results must be explainable and traceable to rules, not only to model output.
