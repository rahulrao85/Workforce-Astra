# Copy-paste prompts to run OpenCode and Antigravity in parallel

Split so there's no overlap. Both can start immediately, in parallel with Snowflake account
setup in SETUP.md -- neither piece below needs the live account to begin.

---

## For Antigravity (remaining research -- CLI syntax + semantic view already verified by Claude)

Claude already confirmed against docs.snowflake.com today: (1) CoCo CLI does NOT work on a
standard trial.snowflake.com account -- you need the dedicated CoCo CLI trial or a paid account,
this is the real blocker, see SETUP.md step 1. (2) The `CREATE SEMANTIC VIEW` syntax in
sql/02_semantic_view.sql has been corrected to match the real documented syntax, including a
working `AI_VERIFIED_QUERIES` block using `SEMANTIC_VIEW()` table-function SQL. Don't redo either
of those -- pick up from here:

```
Working in F:\AGENTIC WORLD\hackathons\Snowflake-Workforce-Astra\ -- same-day MVP build
for the Snowflake CoCo CLI Hackathon (Customer 360 track, framed as Employee 360), due
04-Oct-2026, building today/tomorrow.

Already done (don't redo): CoCo CLI is confirmed to require a paid account or dedicated
CoCo CLI trial, NOT trial.snowflake.com (see SETUP.md). sql/02_semantic_view.sql's
CREATE SEMANTIC VIEW DDL is verified against the real Snowflake syntax including a
working AI_VERIFIED_QUERIES block with SEMANTIC_VIEW() table-function SQL for 3 of the
6 planned verified queries.

Status update: the dedicated CoCo CLI trial link was found and used -- account ST42987
(ap-southeast-7, AWS) was created, but it's currently blocked by a network policy on
every sign-in attempt (tried from 3 different IPs, all rejected). A Snowflake support
case has been filed. This does NOT block your tasks below -- none of them need the live
account, they're all offline research/code. Don't spend time on account access; that's
being handled separately.

Your tasks:
1. Add the 3 remaining AI_VERIFIED_QUERIES to sql/02_semantic_view.sql, following the
   exact pattern already in the file: the ungoverned/naive headcount comparison query
   (plain COUNT(*) on raw_workday_workers, deliberately NOT going through the semantic
   view -- this is the "before governance" comparison point), the flight-risk composite
   query joining comp_ratio + reviews.rating_score, and the review-notes lookup query.
3. Verify the exact syntax for: staging + COPY INTO to load the 3 CSVs from
   data/generate_synthetic_data.py into sql/01_create_tables.sql's tables, and creating
   a Cortex Search service over raw_performance_reviews.review_text for the stretch
   evidence skill. Add both as new SQL files in sql/.
4. Column-alias convention inside SEMANTIC_VIEW() query results (e.g. `workers__headcount`)
   is not yet confirmed against a live account -- verify against docs and correct if wrong.

Report back what changed and cite sources. Needed today.
```

---

## For OpenCode (surrounding code + MCP stub + stretch UI)

```
Working in F:\AGENTIC WORLD\hackathons\Snowflake-Workforce-Astra\ -- same-day MVP build
for the Snowflake CoCo CLI Hackathon (Customer 360 / Next Best Action track, framed as
Employee 360), due 04-Oct-2026 but building today/tomorrow to leave the weekend for
recording.

1. Review data/generate_synthetic_data.py (Faker-based generator for workers,
   compensation bands, performance reviews). Run it, sanity-check the CSVs -- especially
   that the FTE-vs-Contractor headcount split produces genuinely different numbers
   (governed vs. naive count), since that's the whole demo's proof point.
2. Package the data generation + Snowflake load as a CoCo CLI "skill" -- a
   Python/shell script + short instructions file CoCo CLI can invoke as a named skill.
   Coordinate with whatever Antigravity produces for exact load/COPY INTO syntax.
3. Build the two mock MCP tool stubs defined in MCP_TOOLS.md
   (workday_create_compensation_adjustment, slack_notify_manager_flight_risk) as a
   minimal local MCP server returning mocked success payloads -- no real Workday/Slack
   credentials involved, these are synthetic-demo stubs only.
4. STRETCH, only if the core workflow (data -> semantic view -> Cortex Analyst
   FTE-vs-contractor conflict resolution) is done and proven working first: wire the
   MCP tools to a CoCo agent skill, and/or scaffold a minimal Streamlit-in-Snowflake
   query box. Do not start this before the core workflow is proven end-to-end and
   recordable.

Report back with what's working, any data issues found, and whether the skill/MCP
packaging is ready for a screen-recorded demo.
```

---

## What I'm (Claude Code) holding
Coordinating the specs above, `SUBMISSION_BRIEF.md`, `DEMO_SCRIPT.md`, and the final
submission-deck content once you send the Hack2Skill PDF template. Ping me with results
from either agent and I'll fold corrections back into these files.
