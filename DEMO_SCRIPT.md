# Demo video script (4-5 min, screen recording)

Required by the submission form: end-to-end workflow via CoCo CLI, input -> processing -> output,
at least one fully working workflow, **2-3 modular skills/capabilities demonstrated**. This script
demonstrates **two named CoCo skills** (`$workforce-astra-data-gen`, `$workforce-astra-governance-check`)
plus the MCP action layer.

Confirmed working as of 25-Sep-2026: CoCo CLI installed and connected, **both project skills
discoverable by CoCo**, semantic views `EMPLOYEE_360` / `ORG_HEALTH_360` / `PAY_EQUITY_360` /
`EMPLOYEE_VOICE_360` / `BAND_HEALTH_360` live with correct governed numbers (109 governed vs 127
naive; avg span 9.0; 5 overspan managers; unadjusted pay gap -16.8% vs adjusted -2.8%; 18 interviews
scored, top reason career_growth 6, 5 corroborated flight risks; red circles 0 but 37 of 150 below
band minimum, M1/IC5 overlap 71%), Cortex Analyst answers all five views with 0 warnings, the
Snowpark Python scoring procedure runs clean, MCP server has 6 tools (`--selftest` exits 0), **25/25
regression tests pass**, and **3** scheduled Tasks are running. This script uses the real, verified
numbers throughout -- if a live run ever returns different numbers, trust what's on screen over this
document and don't force it to match.

## Beat sheet

**0:00-0:15 -- Hook**
"HR, Finance, and Engineering ask 'how many employees do we have?' and get three different
numbers from the exact same data, because nobody owns the definition. Workforce Astra fixes
that with governed Semantic Views on Snowflake, built through CoCo CLI."

**0:15-0:55 -- Skill 1 of 2: data generation, in the CoCo CLI terminal**
Terminal window, CoCo CLI already running from `F:\AGENTIC WORLD\hackathons\Snowflake-Workforce-Astra`.
Type (don't paste silently -- let it show on screen): `$workforce-astra-data-gen generate and load the demo data`.
Let it run on camera: generate -> verify -> stage -> load. Narrate over it: "This skill generates 150
synthetic employees plus 18 stay/exit interview transcripts, verifies them against invariants that
are hard gates rather than reports, and loads them straight into Snowflake." End on the real output:
150 workers, 5 bands, 127 reviews, 18 transcripts in `WORKFORCE_ASTRA.RAW`.

**0:55-1:35 -- Skill 2 of 2: the governance check, same terminal**
Type: `$workforce-astra-governance-check run the tests`.
It runs `scripts/governance_check.py` and prints `25/25 PASS`, split **15 deterministic / 10
model-dependent**, the three scheduled tasks all `started`, and the open alerts. Narrate — and this
is the credibility beat, so say it plainly:
- "Every governed metric has an owner, a certified definition, and a golden-value test."
- "The suite separates tests that read tables from tests that read a *model's* output. Ten of these
  pin current Cortex model behaviour, so a Snowflake model upgrade trips them loudly instead of
  quietly changing a number in a board pack."
- "And notice it passes *with* three HIGH alerts open. Those aren't test failures — they're the
  schedulers correctly escalating a real pay-equity breach and 37 people sitting below their own
  band minimum. A green test suite and an unhappy C-suite can both be true."

**1:35-1:55 -- The proof point, still in the terminal**
Type: `How many active employees do we have?` -- expect **109**. Then: `How many people work here
including contractors?` -- expect **127**. Narrate: "Same data, same moment, two different
governed-vs-ungoverned answers. That's the thesis, live, not staged." If the numbers don't match
109/127, stop and re-check the data before continuing -- don't record over a mismatch.

**1:55-2:35 -- The Streamlit portal (the polished payoff)**
Switch to the browser, already logged into Snowsight, already navigated so there's no load-in dead
air: https://app.snowflake.com/MUNGIIX/si60728/#/streamlit-apps/WORKFORCE_ASTRA.RAW.EMPLOYEE_360_PORTAL
*(Use this exact URL. The `ap-southeast-7.aws/si60728` form that CoCo reports renders a generic
error page — same account, wrong identifier format.)*
1. Click **"Compare: Governed vs Naive"** -- the same 109/127 conflict, now in the UI, with the SQL
   for both side by side.
2. Scroll to the **Employee Directory** -- filter by department briefly to show it's live data.
3. Open the **Flight-Risk Browser**, expand one employee to show the cited review text, then click
   **Resolve** -- show the `slack_notify_manager_flight_risk` JSON payload. Narrate: "Simulated
   action matching our MCP schema exactly. The real version wires this to Slack and Workday."

**2:35-3:55 -- Four more governed domains, same portal**
5. **Org Health & Manager Health**: 15 managers, avg span **9.0**, **5 overspan managers**, depth 2.
   Narrate the guardrail: "Reorg changes are dry-run through a guarded `simulate_reorg` that rejects
   circular reporting lines -- it never mutates the org."
6. **Pay Equity & Adverse-Impact Auditor**: **unadjusted -16.8% vs adjusted -2.8%**. "The board sees
   16.8%; legal sees 2.8% once band mix is held constant." Then point at the **SUPPRESSED** cohort
   rows -- "any cohort under 5 people has its pay figures withheld, automatically."
7. **Metric Governance & Regression Tests**: the registry and **25/25 PASS**.
8. **Comp Band Architecture Auditor**: point at **red circle 0**, then let the warning land --
   **"24.7% of the company, 37 of 150, is paid below its own band minimum."** Narrate: "We designed
   this to show red circles. It found none. The real problem is the mirror image -- a quarter of the
   company is priced outside its own published range. That's a compliance exception, not a market
   position." Then the overlap table: **M1 and IC5 overlap 71%** -- "pay alone can't tell a manager
   from a senior IC. That's an architecture problem, not a promotion problem."
9. **The guardrail beat -- do not skip it**: point at the findings table, then say "note what's
   *absent*. There's no proposed-pay column, and the `audit_comp_bands` MCP tool can't be asked for
   one. The tool reports; a human sets the band. A procedure that helpfully suggests the new salary
   is exactly the failure mode this project argues against."

**3:55-4:20 -- Employee voice: the unstructured layer (Snowpark)**
10. **Employee Voice — Sentiment & Reason**: **18 scored, 13 exit / 5 stay, 9 negative, 7
    flight-risk signals, average sentiment -0.156.**
11. **"Why people leave"**: **career_growth 6**, manager 3, compensation 2. "These aren't keywords.
    A Snowpark Python procedure inside Snowflake runs Cortex sentiment *and* classifies the reason
    against a fixed, governed eight-label taxonomy -- multi-label, so 13 of the 18 honestly named
    more than one reason."
12. **The money beat** — the cross-signal table, **5 rows**. Expand `EMP-0031`: read two sentences of
    the verbatim exit interview, then the performance-review quote beneath it. "Same person: says
    she's underpaid against a peer, sentiment -0.53, comp-ratio 0.80, rated 4. The structured metric
    knew she was flight-risk. Only the transcript tells you *why* -- and the why is what your
    retention conversation actually needs."

**4:20-4:35 -- Cortex Analyst + scheduled automation (no UI)**
Ask Cortex Analyst against `employee_voice_360` ("what is the most common reason employees give?")
and `band_health_360` ("which band has the most people paid below its minimum?"). Show the
governed SQL it returns, note **0 warnings** both times. Then `SHOW TASKS IN SCHEMA
WORKFORCE_ASTRA.RAW;` — three automations, all `started`.

**4:35-4:45 -- Close**
State the stack, and only what is live: five Semantic Views (all five answer in Cortex Analyst with
0 warnings), a Snowpark Python procedure, a Cortex Search service ACTIVE over 127 review notes, **two
reusable CoCo skills**, Streamlit-in-Snowflake, a 6-tool mock MCP server (`dry_run=true`, nothing is
sent anywhere), and 3 scheduled governance Tasks. Say out loud that the Slack/Workday calls are
mocked, not live.

## Recording notes

- **Warm up both the compute pool and the CoCo CLI session before hitting record.** The compute
  pool auto-suspends after 1 hour idle; open the Streamlit portal once and let it fully load
  *before* you start recording, so there's no cold-start delay or error on camera. Similarly, run
  one throwaway CoCo CLI command first to make sure the session hasn't expired.
- Record the actual CoCo CLI terminal and the actual Snowsight browser tab -- not a mockup, not
  slides. Both are proven working; there's no reason to fake anything here.
- **Rehearse the two skill invocations by typing them exactly as written above.** They are real
  project skills and CoCo lists both, but a typo in the `$skill-name` will silently do nothing.
- Keep total runtime inside 3-5 minutes. If it's running long, cut the Employee Directory filter
  demonstration first -- it's the least load-bearing beat.
- Do a full silent dry run first (no recording) to confirm every click still works and the
  numbers still match, especially if any time has passed since the last verified run. The
  `$workforce-astra-governance-check` skill is the fastest way to confirm that in one command.
