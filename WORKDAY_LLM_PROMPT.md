# Workforce Astra — Workday Integration Prompt Pack (for any LLM)

**Purpose:** Hand this file to any capable LLM/agent (Claude, GPT, Gemini, Copilot, Antigravity, DeepSeek, …) so it can build or extend the **Workday action layer** of Workforce Astra in parallel, without breaking the governed analytics core.

**Owner of this contract:** the Human (Rahul). Do not change the contract; implement against it.

---

## 0. Ground truth the LLM must load first

- Repo: `F:\AGENTIC WORLD\hackathons\Snowflake-Workforce-Astra`
- Snowflake: account `ST42987.ap-southeast-7.aws`, db/schema `WORKFORCE_ASTRA.RAW`
- Runtime constraint: **no External Access Integration (EAI)** on this trial account. Anything that calls the internet from *inside Snowflake* (Tasks, Streamlit, UDFs) will fail. External tool calls happen from the **local MCP server** (stdio), which is not EAI-bound.
- Existing MCP server: `mcp_server/workforce_astra_mcp.py` (mock, audit-logged to `mcp_server/calls.jsonl`).
- Existing tools: `workday_create_compensation_adjustment`, `workday_create_promotion_nomination`, `workday_create_requisition`, `simulate_org_reorg`, `slack_notify_manager_flight_risk`.
- Register with CoCo CLI: `cortex mcp add workforce-astra python "<repo>/mcp_server/workforce_astra_mcp.py"`

---

## 1. The shared prompt (copy-paste this to the LLM)

> You are extending the **Workday action layer** of "Workforce Astra", a Snowflake workspace-analytics demo. The analytics core is already built and governed:
> - Semantic views: `employee_360` (headcount/attrition/comp_ratio), `org_health_360` (span of control, overspan managers), `pay_equity_360` (unadjusted vs adjusted pay gap).
> - A local MCP server (`mcp_server/workforce_astra_mcp.py`) exposes **mocked** Workday/Slack tools. Every tool must: (a) be a DRAFT/preview only, (b) never apply a real HR change, (c) append an audit record, (d) enforce guardrails and raise a clear error rather than silently succeed.
>
> **Hard rules**
> 1. **Never** mutate Snowflake data from a tool; tools return draft payloads only.
> 2. **Never** send a message to the *employee* — manager/committee channels only.
> 3. Every tool supports `dry_run` (default True) and an optional `idempotency_key` (dedupe repeated calls).
> 4. Every tool cites the **governed metric name + the evidence snippet** that triggered it in its `justification`.
> 5. Malformed identifiers (e.g. a non-`EMP-####` id, a non-`U…`/`W…` Slack id) must raise a `ToolError` with a human-readable reason.
> 6. Unknown/extra fields are rejected. No silent coercion.
>
> **Deliverables per tool**
> - Typed signature with `Field(...)` descriptions (the repo uses a `MCPServer` decorator style).
> - Deterministic return JSON: `{mock: true, status, <id>, ..., approval_chain, applied: false, note}`.
> - One row appended to `calls.jsonl`.
> - A self-test block in `_selftest()` proving the happy path **and** at least one guardrail rejection.
>
> **Acceptance test**
> `python mcp_server/workforce_astra_mcp.py --selftest` exits 0, prints a payload for every tool, and prints at least one `correctly rejected:` / `REJECTED` guardrail path.

---

## 2. Work request (split across LLMs — assign one row each)

| # | Task | Tool contract to implement | Guardrails to prove |
|---|---|---|---|
| W1 | Comp adjustment (exists — harden) | `workday_create_compensation_adjustment(employee_id, proposed_base_pay, justification, current_base_pay=None, effective_date=None, dry_run=True)` | `proposed_base_pay > 0`; warn if `|change| > 25%` (VP approval) |
| W2 | Promotion nomination (exists — extend) | `workday_create_promotion_nomination(employee_id, target_band, justification, cycle, dry_run=True)` | `target_band ∈ {IC3,IC4,IC5,M1,M2}`; justification ≥ 20 chars citing `promotion_readiness` |
| W3 | Requisition (exists — extend) | `workday_create_requisition(department_code, band_code, justification, hiring_manager_id, dry_run=True)` | band allow-list; justification must cite `overspan_managers` or `open_reqs` |
| W4 | **NEW** — Workday transfer / internal mobility | `workday_create_transfer_draft(employee_id, target_department, justification, dry_run=True)` | reject if target dept missing; reject if employee already in target |
| W5 | **NEW** — Workday termination offboarding checklist | `workday_create_offboarding_draft(employee_id, last_day, reason, dry_run=True)` | `last_day` must be future or today; reason ∈ {Voluntary, Involuntary, Retirement} |
| W6 | **NEW** — Workday learning assignment | `workday_assign_learning_path(employee_id, target_role, dry_run=True)` | target_role allow-list; must return a cited, constrained 90-day plan |
| W7 | **NEW** — Workday job-requisition status sync | `workday_sync_requisition_status(requisition_id, dry_run=True)` | read-only; never posts; idempotent by `requisition_id` |

---

## 3. What "real" would look like later (do NOT do this under the no-EAI constraint)

Document only, behind a clearly named `real_` module that is **not imported by default**:
- Workday REST patterns: `GET /ccx/service/<tenant>/Staffing/v1/workers`, `POST .../Compensation/v1/adjustments`, OAuth 2.0 `client_credentials` with `Workday` + `Bearer` tokens.
- Store credentials in Snowflake **Secrets** + an EAI, or in the local MCP process env — never in git, never in `opencode.json`.
- Keep the mock as the default path so the demo never depends on a live tenant.

---

## 4. Definition of done (report these back)

1. `python -m py_compile mcp_server/workforce_astra_mcp.py` passes.
2. `python mcp_server/workforce_astra_mcp.py --selftest` prints every tool + ≥ 1 guardrail rejection, exit 0.
3. `mcp_server/calls.jsonl` gains one audit line per invocation.
4. A short diff summary: files touched, new tools, guardrails added, anything NOT done and why.
5. State explicitly, in the final message: **"All Workday tools are MOCKED — no tenant was contacted."**

---

## 5. Prompt variants (pick per model)

- **Claude / GPT / Gemini (strong coders):** use the full prompt in §1 + assign 2–3 rows from §2.
- **Fast/cheap models (DeepSeek, mini-tier):** assign exactly **one** row from §2 and paste the §1 hard rules verbatim; ask for a single tool + its self-test only.
- **Reviewer model (second opinion):** "Audit the Workday tools against §1 hard rules and §4; list every rule violated, with file:line."
