# Workforce Astra — Snowflake CoCo CLI Hackathon (GCC Edition)

**Challenge (form dropdown):** Customer 360 and Next Best Action Engine
**Framing:** Employee 360 — the internal-stakeholder analog of Customer 360. Stated explicitly
and up front in the submission brief, not hidden.
**Submission window:** 13-Sep-2026 – 04-Oct-2026 (MVP/prototype stage)
**Status:** Building — target build-complete today/tomorrow, record demo over the weekend

## One-line pitch
Off-the-shelf HRMS platforms are rigid and suffer the same metric-divergence problem the
Customer 360 track calls out: ask Finance the attrition rate, ask HR, ask Engineering — three
different numbers from the same underlying data, because nobody owns the definition. Workforce
Astra builds the People Engine directly on Snowflake: a governed Semantic View unifies HRIS,
compensation, and performance data (structured + unstructured) into an Employee 360, Cortex
Analyst gives every persona the identical governed answer, Cortex Search cites the evidence
behind a flight-risk call, and a CoCo agent closes the loop with a real action.

## MVP scope (cut hard for a 1-2 day build)
- **Entities:** `raw_workday_workers`, `raw_compensation_bands`, `raw_performance_reviews`
  (3 tables — org hierarchy folded into `workers.manager_id`, sentiment pulses cut entirely)
- **Metrics:** `headcount`, `attrition_velocity`, `comp_ratio`
- **Deliberate conflict baked into the data:** `employment_type` (FTE vs Contractor) on the
  worker table — a naive headcount query includes contractors, the governed metric doesn't.
  This recreates the "same question, different answer across teams" cold open live, for real,
  not staged.
- **Workflow demonstrated:** data-gen skill → semantic-query skill (the conflict resolution) →
  *(stretch, only if core workflow is solid first)* Cortex Search evidence skill → one MCP
  action (Slack manager alert or comp-adjustment draft)
- **Delivered post-MVP (21-Sep-2026):** span-of-control / org health, pay-equity auditing, and a
  metric-governance spine (registry + regression tests + scheduled alerts). Still roadmap-only:
  sentiment pulses and full multi-agent orchestration

## Streamlit-in-Snowflake portal -- LIVE, CONFIRMED WORKING 19-Sep-2026
`employee_360_portal/streamlit_app.py`, deployed as `WORKFORCE_ASTRA.RAW.EMPLOYEE_360_PORTAL`:
https://app.snowflake.com/MUNGIIX/si60728/#/streamlit-apps/WORKFORCE_ASTRA.RAW.EMPLOYEE_360_PORTAL
(requires Snowsight login to view -- it's an internal app, not a public URL). Note: this account
is reachable under two identifier formats for the same tenant -- `ST42987.ap-southeast-7.aws`
(locator style, used for CLI/API connections) and `MUNGIIX/si60728` (org/account style, required
for this Snowsight URL specifically -- the CLI-generated URL using the region segment was wrong
and produced a generic error page).

Header, 5 governed query buttons (including a side-by-side governed-vs-naive comparison), an
employee directory, and a flight-risk browser with cited evidence and a simulated MCP resolve
action. Requires only pre-installed packages (`requirements.txt` is comment-only) since this
trial account has no External Access Integration -- a real `pyproject.toml` with dependencies
cannot resolve against PyPI and will break the container; see git history on this file for the
full failure/fix trail if this ever needs revisiting.

## Diversification build — Org Health, Pay Equity, Governance (LIVE 21-Sep-2026)
Three new governed domains on top of the core (`sql/05_org_health.sql`, `sql/06_pay_equity.sql`,
`sql/07_metric_governance.sql`), all verified live and surfaced in the same portal:

| Domain | Semantic view | Headline result | Rubric hit |
|---|---|---|---|
| Org design & manager health | `org_health_360` | 15 managers, avg span **9.0**, **5 overspan managers** (>10 reports) | custom function (`simulate_reorg`, guarded), Cortex Analyst |
| Pay equity / DEI | `pay_equity_360` | unadjusted gap **-16.8%** vs adjusted (band-normalised) **-2.8%** | guardrails: masking policy + k-anonymity (n<5 suppression) |
| Metric governance | registry + tests | regression suite **7/7 PASS**, scheduled daily | scheduled automation (2 Tasks) + guardrails |

Design rule enforced throughout: **single-grain base tables** feed each semantic view, so
one-to-many joins can never double-count a governed metric (the classic fan-out failure).

## Files in this folder
| File | Purpose |
|---|---|
| `SETUP.md` | Account + CoCo CLI setup — same critical path as any track, do this first |
| `data/generate_synthetic_data.py` | Generates the 3 CSVs with the deliberate FTE/contractor conflict. `--verify` asserts the demo invariants |
| `scripts/load_workforce_data.py` | One-shot pipeline: generate → verify → stage (space-free path) → emit/run the load SQL |
| `.cortex/skills/workforce-astra-data-gen/SKILL.md` | **CoCo CLI skill 1** — invoke as `$workforce-astra-data-gen` |
| `mcp_server/workforce_astra_mcp.py` | Mock MCP action server (5 tools). `--selftest` runs without a client |
| `sql/01_create_tables.sql` | Raw table DDL |
| `sql/02_semantic_view.sql` | Semantic view + 6 verified queries (incl. the naive-vs-governed comparison) |
| `sql/03_load_data.sql` | Stage + `COPY INTO` for the 3 CSVs. Generated by the loader script — don't fork it |
| `sql/04_cortex_search.sql` | Cortex Search service over `review_text` (evidence step) |
| `sql/05_org_health.sql` | Org hierarchy, `org_walk_up` UDF, guarded `simulate_reorg` proc, `org_health_360` view |
| `sql/06_pay_equity.sql` | Demographics, cohort k-anonymity suppression, masking policy, `pay_equity_360` view |
| `sql/07_metric_governance.sql` | Metric registry, golden-value regression tests, drift proc, 2 scheduled Tasks |
| `WORKDAY_LLM_PROMPT.md` | Reusable prompt pack so other LLMs can extend the Workday action layer in parallel |
| `MCP_TOOLS.md` | The 5 mock MCP tool definitions for the closed-loop action |
| `SUBMISSION_BRIEF.md` | Ready-to-paste MVP brief, states the Employee 360 reframe explicitly |
| `DEMO_SCRIPT.md` | 3-5 min recording script |
| `PROMPTS_FOR_AGENTS.md` | Copy-paste prompts for OpenCode and Antigravity |
| `requirements.txt` | `faker` (data gen) + `mcp` (mock MCP server — 2.x API) |

## Note on the parked alternative
`hackathons/Snowflake-Astra-OntoChain/` (Supply Chain Ontology track) is left in place untouched
as a fallback, not deleted. Same technical pattern, different entities — if Workforce Astra hits
a wall, that scaffold is still ready.
