# Demo video script (target 3:50, hard cap 5:00, screen recording)

Required by the submission form: end-to-end workflow via CoCo CLI, input -> processing -> output,
at least one fully working workflow, **2-3 modular skills/capabilities demonstrated**. This script
demonstrates **two named CoCo skills** (`$workforce-astra-data-gen`, `$workforce-astra-governance-check`)
plus the MCP action layer.

Confirmed working as of 25-Sep-2026, re-verified live 26-Sep-2026: CoCo CLI installed and connected,
**both project skills discoverable by CoCo**, semantic views `EMPLOYEE_360` / `ORG_HEALTH_360` /
`PAY_EQUITY_360` / `EMPLOYEE_VOICE_360` / `BAND_HEALTH_360` live with correct governed numbers (109
governed vs 127 naive; avg span 9.0; 5 overspan managers; unadjusted pay gap -16.8% vs adjusted -2.8%;
18 interviews scored, top reason career_growth 6, 5 corroborated flight risks; red circles 0 but 37 of
150 below band minimum, M1/IC5 overlap 71%), Cortex Analyst answers all five views with 0 warnings,
the Snowpark Python scoring procedure runs clean, MCP server has 6 tools (`--selftest` exits 0),
**25/25 regression tests pass**, and **3** scheduled Tasks are running. This script uses the real,
verified numbers throughout -- if a live run ever returns different numbers, trust what's on screen
over this document and don't force it to match.

The target is 3:50 so a real take can run long and still land under the 5:00 cap.

## Beat sheet

**0:00-0:15 -- Hook**
"HR, Finance, and Engineering ask 'how many employees do we have?' and get three different
numbers from the exact same data, because nobody owns the definition. Workforce Astra fixes
that with governed Semantic Views on Snowflake, built through CoCo CLI."

**0:15-0:45 -- Skill 1 of 2: data generation, in the CoCo CLI terminal**
Terminal window, CoCo CLI already running from `F:\AGENTIC WORLD\hackathons\Snowflake-Workforce-Astra`.
Type (don't paste silently -- let it show on screen): `$workforce-astra-data-gen generate and load the demo data`.
Narrate over the run: "This skill generates 150 synthetic employees plus 18 stay/exit interview
transcripts, verifies them against hard-gate invariants, and loads them into Snowflake." End on the
real output: 150 workers, 5 bands, 127 reviews, 18 transcripts. *(Speed up the waiting in the edit if
the load runs long -- keep the command and the final output on screen.)*

**0:45-1:20 -- Skill 2 of 2: the governance check, same terminal**
Type: `$workforce-astra-governance-check run the tests`.
It prints `25/25 PASS`, split **15 deterministic / 10 model-dependent**, the three scheduled tasks
`started`, and the open alerts. Narrate the two lines that matter:
- "Every governed metric has an owner, a certified definition, and a golden-value test -- and ten of
  them pin Cortex model behaviour, so a model upgrade trips them loudly instead of quietly changing a
  number in a board pack."
- "It passes *with* three HIGH alerts open. Those aren't failures -- they're the schedulers correctly
  escalating a real pay-equity breach and 37 people below their own band minimum."

**1:20-1:40 -- The proof point, still in the terminal**
Type: `How many active employees do we have?` -- expect **109**. Then: `How many people work here
including contractors?` -- expect **127**. Narrate: "Same data, same moment, two different answers.
That's the thesis, live, not staged." If the numbers don't match 109/127, stop and re-check the data
before continuing -- don't record over a mismatch.

**1:40-2:10 -- The Streamlit portal (the polished payoff)**
Switch to the browser, already logged into Snowsight, already navigated so there's no load-in dead
air: https://app.snowflake.com/MUNGIIX/si60728/#/streamlit-apps/WORKFORCE_ASTRA.RAW.EMPLOYEE_360_PORTAL
*(Use this exact URL. The `ap-southeast-7.aws/si60728` form that CoCo reports renders a generic
error page -- same account, wrong identifier format.)*
1. Click **"Compare: Governed vs Naive"** -- the same 109/127 conflict, now in the UI, with the SQL
   for both side by side.
2. Open the **Flight-Risk Browser**, expand one employee to show the cited review text, then click
   **Resolve** -- show the `slack_notify_manager_flight_risk` JSON payload. Narrate: "A simulated
   action matching our MCP schema exactly -- nothing is sent. The real version wires this to Slack
   and Workday."

**2:10-2:55 -- Pay equity and band architecture, same portal**
3. **Pay Equity**: **unadjusted -16.8% vs adjusted -2.8%**. "The board sees 16.8%; legal sees 2.8% once
   band mix is held constant." Point at a **SUPPRESSED** cohort row -- "cohorts under 5 people have
   their pay figures withheld, automatically."
4. **Comp Band Architecture Auditor**: **red circle 0**, then let the warning land -- **"37 of 150 --
   a quarter of the company -- is paid below its own band minimum."** Then **M1 and IC5 overlap 71%**:
   "pay alone can't tell a manager from a senior IC."
5. **The guardrail -- don't skip it**: "Note what's *absent*: no proposed-pay column, and the
   `audit_comp_bands` MCP tool can't be asked for one. The tool reports; a human sets the band."

**2:55-3:25 -- Employee voice: the unstructured layer (Snowpark)**
6. **Employee Voice**: 18 scored, **career_growth the top reason (6)**. "A Snowpark Python procedure
   inside Snowflake runs Cortex sentiment *and* classifies each reason against a fixed, governed
   taxonomy -- these aren't keywords."
7. **The money beat** -- the cross-signal table, **5 rows**. Expand `EMP-0031`: read two sentences of
   the exit interview, then the review quote beneath it. "Same person: underpaid against a peer,
   sentiment -0.53, comp-ratio 0.80, rated 4. The structured metric knew they were a flight risk.
   Only the transcript tells you *why*."

**3:25-3:40 -- Cortex Analyst (Worksheets)**
In a Snowsight worksheet, ask Cortex Analyst against `band_health_360` ("which band has the most people
paid below its minimum?"). Show the governed SQL it returns and **0 warnings**.

**3:40-3:50 -- Close**
State the stack, and only what is live: five Semantic Views, a Snowpark Python procedure, a Cortex
Search service over 127 review notes, **two reusable CoCo skills**, Streamlit-in-Snowflake, a 6-tool
mock MCP server (`dry_run=true`, nothing is sent anywhere), and 3 scheduled governance Tasks. Say out
loud that the Slack/Workday calls are mocked, not live.

## Recording notes

- **Warm up before hitting record.** If the compute pool was suspended to save credits, resume it
  first (`ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU RESUME;`), then open the Streamlit portal and let
  it fully load so there's no cold start on camera. Run one throwaway CoCo command to confirm the
  session works.
- **Mind the credits.** Every CoCo command costs credits. Do one silent dry run, not five.
- Record the actual CoCo CLI terminal and the actual Snowsight browser tab -- not a mockup, not
  slides.
- **Type the two skill invocations exactly as written above.** A typo in the `$skill-name` silently
  does nothing.
- Keep total runtime inside 3-5 minutes. If it runs long, cut beat 3 (pay equity) first.
- **Not in the video, but in the portal:** Org Health (avg span 9.0, 5 overspan managers, guarded
  `simulate_reorg`), the Employee Directory, and the Metric Governance registry. Mention them in the
  deck rather than spending video time on them.
