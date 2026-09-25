# Demo video script (3-5 min, screen recording)

Required by the submission form: end-to-end workflow via CoCo CLI, input -> processing -> output,
at least one fully working workflow, 2-3 modular skills/capabilities demonstrated.

Confirmed working as of 25-Sep-2026: CoCo CLI installed and connected, `workforce-astra-data-gen`
skill runs end to end, semantic views `EMPLOYEE_360` / `ORG_HEALTH_360` / `PAY_EQUITY_360` /
`EMPLOYEE_VOICE_360` / `BAND_HEALTH_360` live with correct governed numbers (109 governed vs 127
naive; avg span 9.0; 5 overspan managers; unadjusted pay gap -16.8% vs adjusted -2.8%; 18 interviews
scored, top reason career_growth 6, 5 corroborated flight risks; red circles 0 but 37 of 150 below
band minimum, M1/IC5 overlap 71%), Cortex Analyst answers all five views with 0 warnings, the
Snowpark Python scoring procedure runs clean, MCP server has 6 tools (`--selftest` exits 0), 25/25
regression tests pass, and 3 scheduled Tasks are running. This script uses the real, verified numbers
throughout -- if a live run ever returns different numbers, trust what's on screen over this
document and don't force it to match.

## Beat sheet

**0:00-0:15 -- Hook**
"HR, Finance, and Engineering ask 'how many employees do we have?' and get three different
numbers from the exact same data, because nobody owns the definition. Workforce Astra fixes
that with a governed Semantic View on Snowflake, built entirely through CoCo CLI."

**0:15-1:00 -- Skill 1: data generation, in the CoCo CLI terminal**
Terminal window, CoCo CLI already running from `F:\AGENTIC WORLD\hackathons\Snowflake-Workforce-Astra`.
Type (don't paste silently -- let it show on screen): `Run the workforce-astra-data-gen skill`.
Let it run on camera: generate -> verify -> load. Narrate over it: "This skill generates 150
synthetic employees with a deliberate governance conflict baked in, verifies the data with seven
invariants, and loads it straight into Snowflake." End on the real output: 150 workers, 5 comp
bands, 127 reviews loaded into `WORKFORCE_ASTRA.RAW`.

**1:00-1:45 -- Skill 2: the governance proof, live, still in the terminal**
Type: `How many active employees do we have?` -- CoCo CLI resolves this through the semantic
view, expect **109**. Then type: `How many people work here including contractors?` -- expect
**127**, a genuinely different number from the identical underlying data. Narrate: "Same data,
same moment, two different governed-vs-ungoverned answers -- that's the whole thesis, proven
live, not staged." If the numbers on screen don't match 109/127, stop and re-check the data
before continuing -- don't record over a mismatch.

**1:45-2:30 -- The Streamlit portal (the polished payoff)**
Switch to the browser, already logged into Snowsight, already navigated to the portal so there's
no load-in dead air: https://app.snowflake.com/MUNGIIX/si60728/#/streamlit-apps/WORKFORCE_ASTRA.RAW.EMPLOYEE_360_PORTAL
1. Click **"Compare: Governed vs Naive"** -- show the same 109/127 conflict, now in the UI, with
   the SQL for both shown side by side.
2. Scroll to the **Employee Directory** -- filter by department briefly to show it's real, live
   data, not a screenshot.
3. Open the **Flight-Risk Browser**, expand one employee (e.g. `EMP-0031`) to show the cited
   review text -- a real quote about a competing offer, not a generic positive review.
4. Click **Resolve** -- show the simulated `slack_notify_manager_flight_risk` JSON payload.
   Narrate: "This is a simulated action matching our MCP tool schema exactly -- the real version
   wires this to an actual Slack/Workday integration."

**2:30-4:00 -- Four more governed domains, same portal (the diversification)**
5. **Org Health & Manager Health**: read the four metrics on screen -- 15 managers, avg span
   **9.0**, **5 overspan managers** (>10 reports), max depth 2 -- then the widest-span table.
   Narrate the guardrail: "Reorg changes are dry-run through a guarded `simulate_reorg` tool that
   rejects circular reporting lines -- it never mutates the org."
6. **Pay Equity & Adverse-Impact Auditor**: point at **unadjusted -16.8% vs adjusted -2.8%**.
   Narrate: "The board sees 16.8%; legal sees 2.8% once band mix is held constant. Same data,
   one governed answer each." Then scroll the cohort table and point at the **SUPPRESSED** rows --
   "any cohort under 5 people has its pay figures withheld, automatically."
7. **Metric Governance & Regression Tests**: show the metric registry (owners + certified
   definitions) and the **25/25 PASS** suite, then the latest governance alert.
   Narrate: "Every metric has an owner and a golden-value test on a schedule -- if a definition
   silently drifts, the suite fails. That's what stops teams disagreeing again."
8. **Comp Band Architecture Auditor**: point at **red circle 0**, then let the warning land —
   **"24.7% of the company, 37 of 150, is paid below its own band minimum."**
   Narrate: "We designed this to show red circles. It found none. The real problem is the mirror
   image — a quarter of the company is priced outside its own published range. That's a compliance
   exception, not a market position." Then the overlap table: **M1 and IC5 overlap 71%** — "pay alone
   can't tell a manager from a senior IC. That's an architecture problem, not a promotion problem."
9. **The guardrail beat, and do not skip it**: point at the findings table, then say "note what's
   *absent*. There is no proposed-pay column, and the `audit_comp_bands` MCP tool can't be asked for
   one. The tool reports; a human sets the band. A procedure that helpfully suggests the new salary
   is exactly the failure mode this whole project argues against."

**3:20-3:50 -- Employee voice: the unstructured layer (Snowpark)**
10. Scroll to **Employee Voice — Sentiment & Reason**. The metric row: **18 transcripts scored,
   13 exit / 5 stay, 9 negative, 7 flight-risk signals, average sentiment -0.156**.
11. Point at **"Why people leave"**: **career_growth 6**, manager 3, compensation 2 — then the
   "negative sentiment by reason" table. Narrate: "These aren't keywords. A Snowpark Python
   procedure inside Snowflake runs Cortex sentiment *and* classifies the reason against a fixed,
   governed eight-label taxonomy — multi-label, so thirteen of the eighteen interviews honestly
   named more than one reason."
12. **The money beat** — the cross-signal table. **5 rows.** Expand the top one, `EMP-0031`:
   read two sentences of the verbatim exit interview, then the performance-review quote beneath it.
   Narrate: "Same person: says she's underpaid against a peer, sentiment -0.53, comp-ratio 0.80,
   rated 4. The structured metric knew she was flight-risk. Only the transcript tells you *why* —
   and the why is what your retention conversation actually needs."

**3:50-4:10 -- Cortex Analyst + scheduled automation (no UI)**
In a Snowflake worksheet (or CoCo CLI), ask Cortex Analyst against `employee_voice_360` -- "what is
the most common reason employees give?" -- and against `band_health_360` -- "which band has the most
people paid below its minimum?" Show the governed SQL it returns, and note 0 warnings both times.
Then run `SHOW TASKS IN SCHEMA WORKFORCE_ASTRA.RAW;` to show all three scheduled automations
`started` (daily regression, weekly pay-equity drift, quarterly band review).

**4:10-4:25 -- Close**
State the stack, and only what is live: five Semantic Views (all five answer in Cortex Analyst with
0 warnings), a Snowpark Python procedure, a Cortex Search service ACTIVE over 127 review notes, CoCo
CLI skills, Streamlit-in-Snowflake, a 6-tool mock MCP server (`dry_run=true`, nothing is sent
anywhere), and 3 scheduled governance Tasks. Say out loud that the Slack/Workday calls are mocked,
not live.

## Recording notes

- **Warm up both the compute pool and the CoCo CLI session before hitting record.** The compute
  pool auto-suspends after 1 hour idle; open the Streamlit portal once and let it fully load
  *before* you start recording, so there's no cold-start delay or error on camera. Similarly,
  run one throwaway CoCo CLI command first to make sure the session hasn't expired.
- Record the actual CoCo CLI terminal and the actual Snowsight browser tab -- not a mockup, not
  slides. Both are proven working; there's no reason to fake anything here.
- Keep total runtime inside 3-5 minutes. If it's running long, cut the Employee Directory filter
  demonstration first -- it's the least load-bearing beat.
- Do a full silent dry run first (no recording) to confirm every click still works and the
  numbers still match, especially if any time has passed since the last verified run.
