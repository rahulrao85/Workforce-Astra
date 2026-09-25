# MCP tool definitions

All six are **mocked/stubbed for the demo** — no real Workday tenant or production Slack workspace.
State this explicitly in the submission: these tools draft/preview/notify, they never apply a real
HR action directly. Every tool supports `dry_run` (default true) and rejects malformed input.

`audit_comp_bands` is the one that goes furthest on the guardrail: it has **no output field that
could be mistaken for a pay recommendation**, and no way to be asked for one.

```json
{
  "name": "workday_create_compensation_adjustment",
  "description": "Drafts a compensation adjustment request for an employee, to be routed through the real Workday approval chain. DRAFTS only -- never applies pay changes directly.",
  "parameters": {
    "type": "object",
    "properties": {
      "employee_id": { "type": "string" },
      "current_base_pay": { "type": "number" },
      "proposed_base_pay": { "type": "number" },
      "justification": { "type": "string", "description": "Cites the semantic-view metric and evidence snippet that triggered this" },
      "effective_date": { "type": "string", "format": "date" }
    },
    "required": ["employee_id", "proposed_base_pay", "justification"]
  }
}
```

```json
{
  "name": "slack_notify_manager_flight_risk",
  "description": "Sends a private Slack DM to an employee's manager flagging a flight-risk finding, with cited evidence. Never sent to the employee themselves.",
  "parameters": {
    "type": "object",
    "properties": {
      "manager_slack_id": { "type": "string" },
      "employee_id": { "type": "string" },
      "risk_score": { "type": "number" },
      "evidence_snippet": { "type": "string", "description": "Verbatim excerpt from Cortex Search result, with source review_id" }
    },
    "required": ["manager_slack_id", "employee_id", "risk_score", "evidence_snippet"]
  }
}
```

```json
{
  "name": "workday_create_promotion_nomination",
  "description": "Drafts a promotion nomination for the calibration cycle, routed through the real Workday promotion workflow. DRAFTS only -- never promotes anyone.",
  "parameters": {
    "type": "object",
    "properties": {
      "employee_id": { "type": "string" },
      "target_band": { "type": "string", "enum": ["IC3", "IC4", "IC5", "M1", "M2"] },
      "justification": { "type": "string", "description": "Cites the governed metric + cited review evidence (>= 20 chars)" },
      "cycle": { "type": "string" },
      "dry_run": { "type": "boolean", "default": true }
    },
    "required": ["employee_id", "target_band", "justification"]
  }
}
```

```json
{
  "name": "workday_create_requisition",
  "description": "Drafts a job requisition in Workday from a governed hiring need (overspan manager, open reqs). DRAFTS only -- never posts a job.",
  "parameters": {
    "type": "object",
    "properties": {
      "department_code": { "type": "string" },
      "band_code": { "type": "string", "enum": ["IC3", "IC4", "IC5", "M1", "M2"] },
      "justification": { "type": "string" },
      "hiring_manager_id": { "type": "string" },
      "dry_run": { "type": "boolean", "default": true }
    },
    "required": ["department_code", "band_code", "justification"]
  }
}
```

```json
{
  "name": "simulate_org_reorg",
  "description": "Guarded reorg dry-run mirrors WORKFORCE_ASTRA.RAW.simulate_reorg. Rejects self-moves, circular reporting lines and overspan breaches. SIMULATION ONLY -- never mutates org data.",
  "parameters": {
    "type": "object",
    "properties": {
      "source_manager": { "type": "string" },
      "target_manager": { "type": "string" },
      "source_subtree_size": { "type": "integer" },
      "target_current_span": { "type": "integer" }
    },
    "required": ["source_manager", "target_manager"]
  }
}
```

```json
{
  "name": "audit_comp_bands",
  "description": "Comp band architecture auditor. Mirrors WORKFORCE_ASTRA.RAW.run_band_review. REPORTS employees paid outside their published band range or clustered at the floor. REPORTS ONLY -- never returns a proposed or adjusted pay value and never writes to any pay field, because setting band architecture is a human decision with legal weight.",
  "parameters": {
    "type": "object",
    "properties": {
      "band_code": { "type": "string", "enum": ["IC3", "IC4", "IC5", "M1", "M2"] },
      "flags": {
        "type": "array",
        "items": { "type": "string", "enum": ["BELOW_RANGE_MIN", "RED_CIRCLE", "IN_FLOOR_CLUSTER"] },
        "description": "Which structural flags to return. Any subset; at least one."
      }
    },
    "required": ["band_code"]
  }
}
```

Implement as a tiny local MCP server (stdio or SSE) returning a mocked success payload — ask
CoCo CLI to scaffold a Python MCP server with these tool schemas as a starting point.
`manager_slack_id` is already present as a mock field on `raw_workday_workers` in the synthetic
data, so no separate org-lookup table is needed for this.
