# Demo video script — final (target 3:50, hard cap 5:00, screen recording)

The submission form asks for an end-to-end workflow through CoCo CLI, shown as input → processing → output, with at least one fully working workflow and **2–3 modular skills/capabilities**. This script shows **two named CoCo skills** (`$workforce-astra-data-gen`, `$workforce-astra-governance-check`), the governed proof point, the Streamlit portal and Cortex Analyst.

**Rehearsed end to end on 26-Sep-2026** through CoCo CLI v1.1.87, with the same prompts you'll type:
- data-gen loaded 150 workers, 5 bands, 127 reviews and 18 transcripts
- governance check: 25/25 PASS (15 deterministic / 10 model-dependent), 3 tasks `started`, 3 HIGH alerts
- proof point: 109 vs 127

If a live take shows different numbers, trust the screen and don't force this script to match. If 109/127 doesn't match, stop and check the data before recording on.

---

## Part 1 — Pre-flight (about 10 minutes before you hit record)

Run these in a normal PowerShell window, not the one you'll record.

1. **Wake the portal's compute pool.** It's paused to save about $8/day.
   ```powershell
   uvx --from snowflake-cli snow sql -c workforce-astra-keypair -q "ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU RESUME"
   ```
2. **Open the portal and let it fully load** (1–3 min cold start). Stay logged into Snowsight in the same browser:
   https://app.snowflake.com/MUNGIIX/si60728/#/streamlit-apps/WORKFORCE_ASTRA.RAW.EMPLOYEE_360_PORTAL
   Use this exact URL. The `ap-southeast-7.aws/si60728` form that CoCo prints shows an error page.
3. **Open a second browser tab on Cortex Analyst.** In Snowsight go to **AI & ML → Cortex Analyst**, pick the semantic view `WORKFORCE_ASTRA.RAW.BAND_HEALTH_360` (role ACCOUNTADMIN, warehouse COMPUTE_WH), and leave it ready to type (see beat 8).
4. **Open the recording terminal.** Use a fresh PowerShell window with a large font (Ctrl + scroll to about 18 pt) and a dark theme:
   ```powershell
   cd "F:\AGENTIC WORLD\hackathons\Snowflake-Workforce-Astra"
   cortex -c workforce-astra-keypair --only-explicit-mcp-servers
   ```
   - `--only-explicit-mcp-servers` hides an unrelated aws-mcp error banner.
   - If `cortex` isn't found, use `& "$env:LOCALAPPDATA\cortex\bin\cortex.cmd" -c workforce-astra-keypair --only-explicit-mcp-servers`.
   - If a browser sign-in tab opens, CoCo's agent connection was reset. See the access guide.
5. **Warm-up (don't record).** Type `what is my current role?` and check you get ACCOUNTADMIN. Then exit CoCo and relaunch it with the same command, so the recorded session starts clean.
6. **Screen:** close notifications (Windows Focus / Do Not Disturb), hide the taskbar clock if you like, and close any window that shows a personal email, bank or employer name.
7. **Recorder:** OBS or Xbox Game Bar (`Win + Alt + R`), 1080p, microphone on. Do a 5-second test clip and play it back to check the audio.

**Credits:** each CoCo prompt runs an AI agent and costs real credits (the recording uses 5 prompts). Plan for **one take, two at most**. Mistakes get cut in the edit rather than re-recorded.

---

## Part 2 — The take: what to do and what to say

Anything in quotes is narration, to say roughly word for word. **Type** means type it on screen (don't paste silently). Timings are targets.

### Beat 1 — Hook · 0:00–0:15 · terminal on screen, CoCo idle

> "Ask HR, Finance and Engineering 'how many employees do we have?' and you get three different numbers from the same data, because nobody owns the definition. This is Workforce Astra: Employee 360, the Customer 360 idea applied to your own people. Governed on Snowflake, built entirely through CoCo CLI."

### Beat 2 — Skill 1: data generation · 0:15–0:45

**Type:** `$workforce-astra-data-gen generate and load the demo data`

While it runs:
> "This is the first of two reusable CoCo skills. It generates a synthetic company: a hundred and fifty workers, comp bands, performance reviews, and eighteen stay and exit interview transcripts. It checks them against hard invariants, then stages and loads them into Snowflake. Everything here is synthetic, with no real employee data."

When the table appears (150 / 5 / 127 / 18):
> "Four tables loaded, row counts verified."

*(In the edit, speed up the waiting and keep the typed command and the final table at normal speed.)*

### Beat 3 — Skill 2: governance check · 0:45–1:20

**Type:** `$workforce-astra-governance-check run the tests`

When `25/25 PASS` appears:
> "Skill two runs the governance suite. Twenty-nine governed metrics, every one with a named owner and a certified definition. Twenty-five golden-value tests, all passing. Ten of them pin Cortex model behaviour, so a model upgrade trips a test loudly instead of quietly changing a number in a board pack."

Point at the alerts:
> "And notice it passes *with* three HIGH alerts open. Those aren't test failures. They're scheduled Snowflake Tasks correctly escalating real findings: an adjusted pay gap over threshold, and thirty-seven people paid below their own band minimum."

### Beat 4 — The proof point · 1:20–1:40

**Type:** `How many active employees do we have?` → expect **109**
**Type:** `How many people work here including contractors?` → expect **127**

> "Same data, same moment, two different answers. A hundred and nine is the governed, full-time-employee headcount. A hundred and twenty-seven quietly counts eighteen contractors. The semantic view makes the governed answer the default one."

### Beat 5 — The portal · 1:40–2:10 · switch to the portal tab (already loaded)

1. Click **Compare: Governed vs Naive Headcount**.
   > "Here's the same conflict in a Streamlit app running inside Snowflake, with both SQL statements side by side so anyone can audit the difference."
2. Scroll to **Flight-Risk Browser**. Expand the first employee, then click **Resolve — Draft Slack Alert**.
   > "Underpaid, highly rated people, each with the review text as evidence. Resolve drafts the manager alert in the exact schema of our MCP tool. It's a simulated action and nothing is sent. The Slack and Workday calls in this build are mocked."

### Beat 6 — Pay equity and bands · 2:10–2:55 · keep scrolling

3. **Pay Equity & Adverse-Impact Auditor.**
   > "The raw gender pay gap is minus sixteen point eight percent. Hold band and department constant and it's minus two point eight. The board and legal are both right, and now they're reading the same governed number."
   Point at a **SUPPRESSED** row:
   > "Any cohort under five people has its pay figures withheld automatically, so nobody can be identified."
4. **Comp Band Architecture Auditor.**
   > "No red circles, nobody paid above their band. But thirty-seven of a hundred and fifty, a quarter of the company, are paid *below* their own band minimum. And the M1 and IC5 ranges overlap seventy-one percent, so pay alone can't tell a manager from a senior engineer."
5. **The guardrail (don't skip it).**
   > "What's missing matters: there's no proposed-pay column, and the MCP tool can't be asked for one. The system reports and a human sets the band."

*(If the take is running long, cut beat 6 first. Its numbers are in the deck.)*

### Beat 7 — Employee voice, the unstructured layer · 2:55–3:25 · scroll to Employee Voice

6. > "Now the unstructured data. A Snowpark Python procedure inside Snowflake scores all eighteen interviews with Cortex sentiment, then classifies each against a fixed, governed reason taxonomy, not keyword matching. Career growth is the top reason given."
7. The cross-signal table has **5 rows**. Expand **EMP-0031**, then read the first sentence of the interview on screen:
   > *"I found out in a meeting, by accident, that a colleague who joined after me on the same band is earning materially more."*

   Then say:
   > "Same person: sentiment minus point five three, comp-ratio point eight, rated four out of five. The structured data already said flight risk. Only the transcript says *why*. To be clear, we placed five of these eighteen synthetic interviews on the risk profile deliberately, so the join had something real to find."

### Beat 8 — Cortex Analyst · 3:25–3:40 · switch to the Cortex Analyst tab

**Type** into Cortex Analyst on `BAND_HEALTH_360`: `which band has the most people paid below its minimum?`
Expect **IC3, 10 people**, with the generated SQL shown.

> "Cortex Analyst answers in plain English from the same governed view and shows its SQL, with no warnings. There's one definition, whether you ask through the CLI, the portal, or a worksheet."

### Beat 9 — Close · 3:40–3:50

> "Workforce Astra: five governed semantic views, a Snowpark scoring procedure, Cortex Search over the review notes, two reusable CoCo skills, a Streamlit portal, three scheduled governance Tasks, and a six-tool MCP server that drafts actions in dry-run mode. Nothing is sent anywhere. One definition of every people metric, owned and tested. Thank you."

Stop recording.

---

## Part 3 — Straight after recording

1. **Pause the compute pool** (it will not switch itself off):
   ```powershell
   uvx --from snowflake-cli snow sql -c workforce-astra-keypair -q "ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU SUSPEND"
   uvx --from snowflake-cli snow sql -c workforce-astra-keypair -q "SHOW COMPUTE POOLS LIKE 'SYSTEM_COMPUTE_POOL_CPU'"
   ```
   The state should read `SUSPENDED` (it may show `STOPPING` for a minute first).
2. **Trim the video** to 3–5 minutes. Speed up the CoCo waiting sections, and don't cut away from the typed commands or the outputs.
3. **Watch it once end to end.** Check that no personal or employer info is visible and the audio is clear.
4. **Upload to YouTube as Unlisted** (not Private, because judges must be able to open it). Title: *Workforce Astra — Employee 360 on Snowflake (CoCo CLI Hackathon 2026)*. Open the link in a private window to check it plays.
5. **Submit on Hack2Skill:**
   - Challenge: **Customer 360 and Next Best Action Engine**
   - Prototype/MVP brief: paste from `SUBMISSION_BRIEF.md` (1019 characters, under the 1024 limit)
   - Demo video: the unlisted YouTube link
   - Deck: `deck/Workforce_Astra_Submission_Deck.pdf` (already built, 0.57 MB). First put the YouTube link on slide 9 of the `.pptx` and re-export to PDF
   - GitHub: https://github.com/rahulrao85/Workforce-Astra
   - Live page (if there's a field for it): https://workforce-astra.rahulrao.in
   - Make sure your profile is complete before you press submit.
6. **Resubmission is allowed until the lock** (04-Oct-2026, 11:59 PM IST). Only the final submission counts.

---

## Finals note (27–30 Oct)

Finals are a **live** demo, and a pre-recorded video may not be accepted. This script is also your live run order. If the trial has expired by then, finalists get a fresh trial: rebuild with `python scripts/rebuild_all.py --live` (see README), then refresh the landing snapshot with `scripts/export_site_snapshot.py`.

## Not in the video (in the portal and deck instead)

- **Org Health:** avg span 9.0, 5 overspan managers, guarded `simulate_reorg`
- The Employee Directory
- The Metric Governance registry (29 metrics, 0 unowned)
- The landing page's Org / Pay / Voice / Bands / Governance snapshot sections
