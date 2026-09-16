# MCP tool definitions (stretch — only after the core workflow is solid)

Both are **mocked/stubbed for the demo** — no real Workday tenant or production Slack workspace.
State this explicitly in the submission: these tools draft/notify, they never apply a real HR
action directly.

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

Implement as a tiny local MCP server (stdio or SSE) returning a mocked success payload — ask
CoCo CLI to scaffold a Python MCP server with these two tool schemas as a starting point.
`manager_slack_id` is already present as a mock field on `raw_workday_workers` in the synthetic
data, so no separate org-lookup table is needed for this.
