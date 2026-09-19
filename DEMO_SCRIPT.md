# Demo video script (3-5 min, screen recording)

Required by the submission form: end-to-end workflow via CoCo CLI, input -> processing -> output,
at least one fully working workflow, 2-3 modular skills/capabilities demonstrated.

Confirmed working as of 19-Sep-2026: CoCo CLI installed and connected, `workforce-astra-data-gen`
skill runs end to end, semantic view `EMPLOYEE_360` live with correct governed-vs-naive numbers
(109 vs 127), Streamlit portal renders correctly with real data. This script uses the real,
verified numbers throughout -- if a live run ever returns different numbers, trust what's on
screen over this document and don't force it to match.

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

**1:45-2:45 -- The Streamlit portal (the polished payoff)**
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

**2:45-3:15 -- Close**
State the stack: Semantic Views, Cortex Analyst, Cortex Search-ready evidence, CoCo CLI skills,
Streamlit-in-Snowflake, MCP. One line on roadmap (live Slack/Workday wiring, Cortex Search over
review text) without overclaiming what's built today.

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
