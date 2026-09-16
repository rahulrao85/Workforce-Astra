# Demo video script (3-5 min, screen recording)

Required by the submission form: end-to-end workflow via CoCo CLI, input -> processing -> output,
at least one fully working workflow, 2-3 modular skills/capabilities shown.

## Beat sheet

**0:00-0:20 -- Hook**
"HR, Finance, and Engineering all report a different headcount number from the same underlying
data, because nobody owns the definition of 'employee.' Workforce Astra builds that single
definition as a governed Semantic View on Snowflake -- this is Customer 360, applied to the
company's own workforce as its internal stakeholder."

**0:20-1:00 -- Skill 1: data generation (input -> processing -> output)**
In CoCo CLI, invoke `$workforce-astra-data-gen` on camera. Show it generate, verify (the
`--verify` gate), stage, and load the three raw tables (workers, compensation bands, performance
reviews) into Snowflake. Output: row counts -- 150 workers, 5 bands, ~127 reviews.

**1:00-2:00 -- Skill 2: semantic-view query skill -- the governance proof, live**
Ask Cortex Analyst "How many employees do we have?" -- expect **109** (governed, FTE-only). Then
ask "How many people work here including contractors?" -- expect **127**, a genuinely different
number from the SAME data (the 18-person gap is the whole thesis). Show the generated SQL for
both so it's provably not hallucinated or staged. Ask a second question (attrition rate, or
comp-ratio for Engineering) to prove it's a real live system, not a canned pair. If the numbers
on screen don't match 109/127, the account's data wasn't (re)loaded from the current generator --
stop and reload rather than record over it.

**2:00-2:45 -- (stretch, only if core workflow is proven working first) Skill 3: evidence + action**
Ask "which employees have a comp-ratio below 0.85 and a rating of 4 or above?" -- expect 30
matches, 15 with citable review evidence (e.g. `EMP-0031`, comp_ratio 0.80, rating 4). Cortex
Search surfaces the cited review text explaining why (a real competing-offer/pay-concern quote,
not a generic positive review -- that mismatch was caught and fixed in this build, worth being
sure it still holds). Click "Resolve" -- the CoCo agent calls the mocked Slack MCP tool
(`slack_notify_manager_flight_risk`) to notify `EMP-0031`'s manager (`U0006`) with the evidence
attached. State on camera that this is a mocked action, not a real Slack/Workday call.

**2:45-3:15 -- Close**
State the stack: Semantic Views, Cortex Analyst, Cortex Search, CoCo CLI skills, MCP. One line
on roadmap (comp-adjustment drafting, Streamlit command center) without overclaiming what's
built today.

## Recording notes
- Record the actual CoCo CLI terminal and Snowsight/Cortex Analyst UI, not a mockup.
- Keep total runtime inside 3-5 minutes; if time-constrained, cut the stretch skill entirely --
  the FTE-vs-contractor conflict resolution in Skill 2 is the load-bearing proof point for the
  whole pitch and must be rock solid before anything else gets screen time.
