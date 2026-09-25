# Workforce Astra — Snowflake CoCo CLI Hackathon (GCC Edition)

**Challenge (form dropdown):** Customer 360 and Next Best Action Engine
**Framing:** Employee 360 — the internal-stakeholder analog of Customer 360. Stated explicitly
and up front in the submission brief, not hidden.
**Submission window:** 13-Sep-2026 – 04-Oct-2026 (MVP/prototype stage)
**Status (25-Sep-2026):** core build complete and live-verified — 3 Semantic Views, Cortex Analyst
clean on all 3, Cortex Search service ACTIVE, 7/7 regression tests, 2 scheduled Tasks, 5-tool mock
MCP server, Streamlit portal deployed. Demo video not yet recorded; submission not yet filed.

## One-line pitch
Off-the-shelf HRMS platforms are rigid and suffer the same metric-divergence problem the
Customer 360 track calls out: ask Finance the attrition rate, ask HR, ask Engineering — three
different numbers from the same underlying data, because nobody owns the definition. Workforce
Astra builds the People Engine directly on Snowflake: three governed Semantic Views (Employee 360,
Org Health, Pay Equity) unify HRIS, compensation, org-hierarchy and performance data (structured +
unstructured); Cortex Analyst answers all three with visible SQL and zero warnings; a live Cortex
Search service indexes the 127 review notes behind a flight-risk call; and a 5-tool mock MCP server
drafts the retention action for a manager -- dry-run only, nothing is ever sent to Slack or Workday.

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

## Datasets and licences
**Every row of data in this project is synthetic. No real employee, employer, Workday tenant, or
personal data is used anywhere** (T&C §5(d)). Nothing here comes from an employer's real HRIS.

| Dataset | Rows | Source & licence |
|---|---|---|
| `data/raw_workday_workers.csv` → `raw_workday_workers` | 150 | Generated by `data/generate_synthetic_data.py` using [Faker](https://github.com/joke2k/faker) (**MIT**), `random.seed(7)` + `Faker.seed(7)` so runs are reproducible. Ours — no third-party rights. |
| `data/raw_compensation_bands.csv` → `raw_compensation_bands` | 5 | Same generator, hand-set band midpoints. Ours. |
| `data/raw_performance_reviews.csv` → `raw_performance_reviews` | 127 | Same generator; the free-text `review_text` is the only unstructured field. Ours. |
| `raw_employee_demographics` | 150 | **Not** from a CSV — synthesised deterministically in SQL (`sql/06_pay_equity.sql`) from `HASH(employee_id)`, with a deliberate band-mix skew that creates the unadjusted pay gap honestly. Carries a `synthetic_note` column. Ours. |
| `raw_org_hierarchy` / `raw_org_flattened` | 150 | Derived in SQL from `raw_workday_workers.manager_id` (`sql/05_org_health.sql`). Ours. |
| `raw_pay_equity_base`, `pay_equity_cohorts` | derived | Derived in SQL, single employee grain. Ours. |
| `metric_registry`, `metric_regression_tests`, `metric_test_results`, `governance_alerts` | small | Authored by hand in `sql/07_metric_governance.sql`. Ours. |
| `site/data.js` | 150 + 127 | A client-side copy of the tables above, so the static landing page can compute the same numbers in a browser. Ours — regenerate from the CSVs, don't hand-edit. |

Third-party software: **Faker** (MIT) for generation and **`mcp`** (MIT) for the mock MCP server.
No third-party *dataset* is used, so no third-party data licence applies. If a Snowflake
Marketplace benchmark is added later (Phase B2), it will be listed here with its licence and terms
before use.

## How CoCo was used across the lifecycle
The hackathon asks for evidence of CoCo CLI at every stage, so here is exactly what ran where —
including the stage where CoCo was *not* the tool.

| Phase | Was CoCo used? | Evidence |
|---|---|---|
| **Planning / requirements** | **Partly — and honestly, not the original design** | The first design and the `CREATE SEMANTIC VIEW` syntax research were done with Claude Code; the HR-domain ideation came from four external LLM reviews kept in this repo (`ANTIGRAVITY_…`, `COPILOT_…`, `OPENCODE_…`, `SPACE_BUNNY_…`). What CoCo *did* do in this phase was the account-health and expiry assessment (trial end date, credit burn/day by service, task history) that produced a hard requirement — see the account-health audit below. |
| **Execution — building in Snowflake** | **Yes, all of it** | Every DDL, semantic view, stored procedure, scheduled Task and Streamlit deploy in `sql/` was applied through `cortex -c workforce-astra-keypair -p "…" --bypass`. Sessions: `3d9ecd0e` (34 msgs, "Implementing Governed Semantic View…", 16-Sep), `78c3abf1` (26 msgs, portal build), `823f7db6` (26 msgs, "Verifying Workforce Semantic Views…", 22-Sep). |
| **Development / debugging** | **Yes** | The largest session in the project is CoCo debugging the Streamlit container: `380a8290` (182 msgs, 17-Sep, "Debugging Runtime Errors in EMPLOYEE_360_PORTAL") — that session is what produced the comment-only `requirements.txt` fix and the `Decimal × float` fix. Also `965fe303` (portal errors), `72f68940` (compute pool), `4eb82d3e` (20 msgs, pre-recording dry run, 22-Sep). |
| **Testing / verification** | **Yes** | The regression suite is *run* through CoCo, not by hand: `94c5cc79` (25-Sep, "Executing Workforce Astra Raw Metric Tests" → `{"failed": 0, "passed": 7}`). Verification sessions today: `16686fe9` and `b6f7d874` (Cortex Search status + retrieval, 25-Sep). Account-health audit: `fb3e21b1` (12 msgs, 25-Sep — trial expiry, credit burn, `TASK_HISTORY` for both scheduled tasks). |

**Reproduce the evidence yourself** (20 CoCo sessions, 16-Sep → 25-Sep; 8 git commits):
```powershell
cortex conversations list
cortex conversations search "semantic view"
cortex conversations transcript 380a8290-3438-4832-a2ce-78bdbf57b1c2 -c workforce-astra-keypair
git log --oneline
```
Use the **full** session UUID — a truncated prefix returns HTTP 400.

**Operational note, learned the hard way:** CoCo's `sql_execute` tool rejects a prompt containing
more than one SQL statement, so DDL is applied one statement per `-p` call. It also declined a
multi-statement `SHOW …` + `SELECT …` pair; splitting them works. Every Snowflake-side change in
this repo was made through CoCo for exactly this reason — it is the tool of record, not an
afterthought.

## Files in this folder
| File | Purpose |
|---|---|
| `SETUP.md` | Account + CoCo CLI setup — same critical path as any track, do this first |
| `data/generate_synthetic_data.py` | Generates the 3 CSVs with the deliberate FTE/contractor conflict. `--verify` asserts the demo invariants |
| `scripts/load_workforce_data.py` | One-shot pipeline: generate → verify → stage (space-free path) → emit/run the load SQL |
| `.cortex/skills/workforce-astra-data-gen/SKILL.md` | **CoCo CLI skill 1** — invoke as `$workforce-astra-data-gen` |
| `mcp_server/workforce_astra_mcp.py` | Mock MCP action server (5 tools). `--selftest` runs without a client |
| `sql/01_create_tables.sql` | Raw table DDL |
| `sql/02_semantic_view.sql` | `employee_360` Semantic View + 5 verified queries (incl. the governed-vs-naive comparison) |
| `sql/03_load_data.sql` | Stage + `COPY INTO` for the 3 CSVs. Generated by the loader script — don't fork it |
| `sql/04_cortex_search.sql` | Cortex Search service over `review_text` — **live & ACTIVE over 127 reviews, verified 25-Sep-2026** (evidence step) |
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
