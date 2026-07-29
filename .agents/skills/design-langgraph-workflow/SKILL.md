---
name: design-langgraph-workflow
description: Design, implement, refactor, or debug Capple's LangGraph chat orchestration, including ChatState, GraphContext, graph nodes and edges, structured intent parsing, prompt routing, LangChain tools, agent invocation, streaming behavior, and focused tests. Use for agent workflows, tool contracts, routing, memory/state, guardrails, LLM fallbacks, or chat architecture changes.
---

# Design a Capple LangGraph workflow

## Read the live workflow

Read `AGENTS.md`, then:

1. `backend/src/agents/README.md`
2. `backend/src/agents/graph.py` and `state.py`
3. Every node and tool touched by the request
4. `backend/src/service/chat.py` and `backend/src/controllers/api/chat.py`
5. Corresponding tests under `backend/tests/agents/`, `backend/tests/tools/`, and `backend/tests/service/test_chat_service.py`

Confirm the desired output, integration point, latency/failure expectations, required data, and whether state must persist beyond one request. Infer these from code and the request when safe; ask only if the choice would materially change the design.

## Choose the lightest design

Prefer a static node sequence or deterministic branch when the transitions are known. Use a tool-using agent only when runtime tool selection is genuinely useful. Add parallelism, evaluator loops, or persistent memory only when requirements justify their cost and failure modes.

## Preserve contracts

- Define typed, default-initialized fields in `ChatState`.
- Return partial state updates from nodes; do not mutate hidden global state.
- Pass request-scoped `db_client`, `household_id`, and `user_id` through `GraphContext`.
- Bind authorization scope inside tool factories. Never accept a model-supplied user or household ID as authority.
- Give tools narrow typed inputs and structured outputs. Keep network/data access inside tools or repositories.
- Keep parsing, clamping, ranking, deduplication, and fallback logic deterministic where practical.
- Handle low confidence, missing requirements, parser/tool failure, empty data, and model failure explicitly.
- Keep prompts scoped to Capple and prevent raw internal identifiers or secrets from reaching model output.
- Update `backend/src/agents/README.md` if the graph shape or tool inventory changes.

For uncertain LangChain or LangGraph APIs, consult current official documentation before implementation; dependency versions are declared in `backend/pyproject.toml`.

## Test the graph as a system of contracts

- State: defaults, validation, and serialization
- Nodes: normal result, malformed model output, exception fallback, and partial update
- Routing: every branch, confidence threshold, and missing requirement
- Tools: bound context, input validation, repository calls, empty results, and failures
- Agent node: tool registration, prompt propagation, runtime context, and returned messages
- Service/streaming: final message behavior and integration with the compiled graph

Mock model and external-service boundaries. Keep deterministic transformation code real.

Run focused tests, then:

```bash
make be-lint
make be-test
```
