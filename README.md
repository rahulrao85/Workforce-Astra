# Workforce Astra — Snowflake CoCo CLI Hackathon (GCC Edition)

**Challenge (form dropdown):** Customer 360 and Next Best Action Engine
**Framing:** Employee 360 — the internal-stakeholder analog of Customer 360. Stated explicitly
and up front in the submission brief, not hidden.
**Submission window:** 13-Sep-2026 – 04-Oct-2026 (MVP/prototype stage)
**Status (25-Sep-2026):** core build complete and live-verified — 5 Semantic Views, Cortex Analyst
clean on all 5, Cortex Search service ACTIVE, 25/25 regression tests, 3 scheduled Tasks, 2 reusable
CoCo skills, 6-tool mock MCP server, Streamlit portal deployed, one-command rebuild tested on a
scratch database. **26-Sep-2026:** full recording flow rehearsed end to end through CoCo CLI;
landing page (https://workforce-astra.rahulrao.in) extended with dated Snowflake snapshots of all five
domains. Demo video not yet recorded; submission not yet filed.

## One-line pitch
Off-the-shelf HRMS platforms are rigid and suffer the same metric-divergence problem the
Customer 360 track calls out: ask Finance the attrition rate, ask HR, ask Engineering — three
different numbers from the same underlying data, because nobody owns the definition. Workforce
Astra builds the People Engine directly on Snowflake: five governed Semantic Views (Employee 360,
Org Health, Pay Equity, Employee Voice, Band Health) unify HRIS, compensation, org-hierarchy,
performance-review and exit-interview data (structured + unstructured); Cortex Analyst answers all
five with visible SQL and zero warnings; a live Cortex Search service indexes the 127 review notes
behind a flight-risk call; and a 6-tool mock MCP server drafts the retention action for a manager --
dry-run only, nothing is ever sent to Slack or Workday.

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

## Diversification build — Org Health, Pay Equity, Governance, Employee Voice, Band Health (LIVE)
Five additional governed domains on top of the core, all verified live and surfaced in the same portal:

| Domain | Object | Headline result | Rubric hit |
|---|---|---|---|
| Org design & manager health | `org_health_360` | 15 managers, avg span **9.0**, **5 overspan managers** (>10 reports) | custom function (`simulate_reorg`, guarded), Cortex Analyst |
| Pay equity / DEI | `pay_equity_360` | unadjusted gap **-16.8%** vs adjusted (band-normalised) **-2.8%** | guardrails: masking policy + k-anonymity (n<5 suppression) |
| Employee voice | `employee_voice_360` | 18 interviews scored; **career_growth is the top reason (6 of 18)**; **5 corroborated flight risks** | **Snowpark Python**, Cortex `SENTIMENT` + `AI_CLASSIFY` |
| Comp band architecture | `band_health_360` | **0 red circles — but 37 of 150 (24.7%) paid below their own band minimum**; M1/IC5 ranges overlap **71%** | guardrail (reports, never proposes), quarterly Task, 6th MCP tool |
| Metric governance | registry + tests | regression suite **25/25 PASS**, scheduled daily | 3 scheduled Tasks + guardrails |

### Two reusable CoCo skills
The submission form asks for 2–3 modular skills, and reusable/shareable skills are the headline
ingenuity signal — so there are two, both discoverable by CoCo in this project:

| Skill | Invoke | What it does |
|---|---|---|
| `workforce-astra-data-gen` | `$workforce-astra-data-gen` | Generate → verify → stage → load all 4 synthetic CSVs. `--verify` is a hard gate, not a report. |
| `workforce-astra-governance-check` | `$workforce-astra-governance-check` | Run the regression suite and **explain** it: PASS/FAIL, the failing metric's **owner**, and a deterministic vs model-dependent split. |

The second one is deliberately more than a test runner. It exists because of a real gap it found:
12 tested metrics had **no registry entry at all** — they were being regression-tested while nobody
owned their definition, which is precisely the hole the registry exists to close. The registry now
carries 29 entries covering every tested metric, and the script keeps checking, reporting any metric
that is tested but unregistered. Its `model_dependent` split also exists to stop a future agent
"fixing" a model-dependent failure by pasting in whatever number came back.

Porting it to another project needs three objects and two names changed: `run_metric_tests()`,
`metric_test_results`, and `metric_registry`. Nothing else is Workforce-Astra-specific.

### Comp band architecture — reporting an inconvenient truth
`sql/09_band_architecture.sql`. Structural comp, deliberately distinct from the demographic pay-equity
auditor: this asks *where people sit inside their published range*. The metric the demo was designed
around — red-circle rate — came out at **exactly 0**. Nobody is paid above their band maximum. The
real finding is its mirror image: **37 of 150 employees (24.7%) are paid below their own band
minimum**, a range-compliance exception rather than a market position, and the whole workforce
sits in the lower third of its range (weighted penetration 0.315). `band_range_overlap` adds the
architectural read: the **M1 and IC5 ranges overlap by 71%** of the M1 width, so pay alone cannot
separate a manager from a senior IC.

The quarterly `band_architecture_quarterly` Task writes findings to `band_review_findings` and
raises a HIGH governance alert. **It reports and never proposes** — there is deliberately no
`proposed_pay` column, and the matching MCP tool `audit_comp_bands` cannot be asked for one. Setting
a band is a human decision with legal weight.

### Employee voice — the unstructured layer, and the only Snowpark in the project
`sql/08_employee_voice.sql`. 18 hand-authored stay/exit interview transcripts
(`data/generate_voice_transcripts.py`) are scored by `score_voice_transcripts()`, a **Snowpark Python
stored procedure** — the only Python that runs inside Snowflake here. It calls
`SNOWFLAKE.CORTEX.SENTIMENT` for a signed score and `SNOWFLAKE.CORTEX.AI_CLASSIFY` (multi-label,
few-shot) for the reason, against a **fixed, versioned** 8-label taxonomy, then writes
`voice_theme_results`.

`voice_risk_360` is where it pays off: it joins the negative voice signal to the structured
flight-risk evidence and finds the **5 people who are simultaneously** saying something negative
*and* underpaid below 0.85 of band *and* rated 4+. The transcript explains a risk the structured
metric only hinted at.

Two design choices worth calling out, because both were forced by hitting the real API:
- **No invented confidence score.** `AI_CLASSIFY` returns `{"labels": [...]}` and nothing else, so
  the procedure records a primary *and* secondary reason instead of a fabricated 0–1 confidence.
- **A documented reason taxonomy, not free text.** Letting the model invent reason labels would
  re-create the "three teams, three answers" problem this project exists to fix.

Design rule enforced throughout: **single-grain base tables** feed each semantic view, so
one-to-many joins can never double-count a governed metric (the classic fan-out failure).

### Test stability, stated honestly
Regression tests **1–7 and 18–25 are deterministic** (they read tables). Tests **8–17 read Cortex
model output**, so they pin *current model behaviour*: a Snowflake model upgrade will fail them.
That is deliberate — it turns a silent change in the AI pipeline into a visible, triaged alert. The
registry marks these metrics `model_dependent = TRUE` so nobody mistakes them for deterministic
facts.

## Rebuilding on a fresh trial account
T&C §4.6 gives finalists a new trial if theirs expired — and this one is estimated to expire
**~11-Oct-2026, before the 27–30 Oct live finale**, so being able to rebuild fast is a hard
requirement rather than a nicety. `scripts/rebuild_all.py` is that button.

```bash
# the real thing -- on a FRESH trial account only. --live is required, so a bare
# run can never recreate the live database by accident
python scripts/rebuild_all.py --live

# rehearse it on a throwaway database first, exactly as it was tested
python scripts/rebuild_all.py --database WORKFORCE_ASTRA_REBUILD_TEST
python scripts/rebuild_all.py --database WORKFORCE_ASTRA_REBUILD_TEST --drop-only --yes

# drive the build through CoCo CLI instead of snow
python scripts/rebuild_all.py --live --backend coco
```

It regenerates and verifies all 4 CSVs, stages them to a space-free path, concatenates `sql/*.sql`
in dependency order with the database name substituted, applies it, then runs the Snowpark scoring
procedure, the band review and the regression suite, and prints the governed numbers to compare
against this README.

**Tested for real, not asserted.** Rehearsed end-to-end into `WORKFORCE_ASTRA_REBUILD_TEST` on
25-Sep-2026: **81 statements, 25/25 regression tests passing, 150/127/18 rows, all 5 semantic views
present**, then dropped. `WORKFORCE_ASTRA.RAW` was confirmed untouched throughout (25/25 before and
after). The rehearsal earned its keep immediately — see below.

**The bug it caught that the live database was hiding.** The first rehearsal failed with
`invalid identifier 'V_ALERT'`. `run_band_review` had been fixed interactively by CoCo while it was
being built, and I synced the *procedure body* back into `sql/09` but missed the one-character fix
to a `LET`-bound variable reference. The live procedure was correct, so nothing was visibly wrong —
but the **file** was wrong, which is exactly what a fresh account would have replayed. Note that
`CREATE OR REPLACE PROCEDURE` does *not* catch this class of error: the object deploys "successfully"
and only fails when the Task first calls it. A repo that is only ever tested against the database it
was written on cannot find this.

`scripts/test_rebuild_splitter.py` guards the other sharp edge: the rebuild splits ~81 statements,
and Snowflake procedures and JavaScript handlers have `$$` bodies full of semicolons. A naive split
silently truncates every procedure. The test covers dollar-quoted bodies, tagged dollar quotes,
semicolons inside string literals, doubled-quote escapes and comment stripping, and asserts that no
procedure or semantic-view statement in `sql/` comes out truncated. **Run it after touching any
`sql/` file:** `python scripts/test_rebuild_splitter.py`.

**Two backends, and an honest limitation.** `--backend snow` (the default) applies the whole script
in one process. `--backend coco` runs one `cortex -c … -p "<statement>" --bypass` call per statement,
which is the evidence the hackathon asks for, but it is slow and **CoCo's `sql_execute` tool
intermittently refuses to run a statement** ("tool restrictions in this session"), so it is not
reliable enough to be the default. The `snow` default exists because CoCo genuinely cannot apply an
81-statement rebuild in one call; the canonical `sql/` files are themselves the artefact CoCo
authored and applied statement-by-statement during development.

The Streamlit portal is deliberately **not** deployed by this script — deploy it separately from
`employee_360_portal/` — so a rebuild never silently overwrites a live app.

### Snowflake Marketplace — checked, not used

`SHOW DATABASES IN ACCOUNT` / `SHOW SHARES IN ACCOUNT` confirm **no Marketplace listing is installed**
on this trial account; the only inbound shares are Snowflake's own (`ACCOUNT_USAGE`,
`SAMPLE_DATA`). Plausible free compensation listings exist (US salary-by-occupation, O\*Net, an
explicitly "Free" Australian employment-statistics feed), but **installing one requires accepting the
provider's licence in the Snowsight UI — a human click an agent cannot perform.** So the band
auditor is built without an external benchmark, and if a listing is added later it will be listed
here with its licence and terms before use.

## Datasets and licences
**Every row of data in this project is synthetic. No real employee, employer, Workday tenant, or
personal data is used anywhere** (T&C §5(d)). Nothing here comes from an employer's real HRIS.

| Dataset | Rows | Source & licence |
|---|---|---|
| `data/raw_workday_workers.csv` → `raw_workday_workers` | 150 | Generated by `data/generate_synthetic_data.py` using [Faker](https://github.com/joke2k/faker) (**MIT**), `random.seed(7)` + `Faker.seed(7)` so runs are reproducible. Ours — no third-party rights. |
| `data/raw_compensation_bands.csv` → `raw_compensation_bands` | 5 | Same generator, hand-set band midpoints. Ours. |
| `data/raw_performance_reviews.csv` → `raw_performance_reviews` | 127 | Same generator; the free-text `review_text` is the only unstructured field. Ours. |
| `raw_employee_demographics` | 150 | **Not** from a CSV — synthesised deterministically in SQL (`sql/06_pay_equity.sql`) from `HASH(employee_id)`, with a deliberate band-mix skew that creates the unadjusted pay gap honestly. Carries a `synthetic_note` column. Ours. |
| `data/raw_voice_transcripts.csv` → `raw_voice_transcripts` | 18 | **Hand-authored** stay/exit interview transcripts (`data/generate_voice_transcripts.py`), 51–85 words each, deliberately varied in length/register/ambiguity rather than templated — a templated corpus would make the sentiment and classification results meaningless. 5 of the 18 interviews are deliberately placed on employees who already meet the structured flight-risk rule (`N_CORROBORATED` in the generator), so the cross-signal is demonstrable; the sentiment scores and reason labels are still the model's own. Ours. |
| `voice_theme_results` | 18 | Derived by the Snowpark procedure from the transcripts. Ours. |
| `voice_risk_360` (view) | 18 | Derived: voice results joined to worker, band and review evidence. Ours. |
| `band_range_health`, `band_range_overlap`, `band_review_findings` | 5 / 4 / 41 | Derived in SQL (`sql/09_band_architecture.sql`) from workers + bands. Ours. |
| `raw_org_hierarchy` / `raw_org_flattened` | 150 | Derived in SQL from `raw_workday_workers.manager_id` (`sql/05_org_health.sql`). Ours. |
| `raw_pay_equity_base`, `pay_equity_cohorts` | derived | Derived in SQL, single employee grain. Ours. |
| `metric_registry`, `metric_regression_tests`, `metric_test_results`, `governance_alerts` | small | Authored by hand in `sql/07_metric_governance.sql`. Ours. |
| `site/data.js` | 150 + 127 | A client-side copy of the tables above, so the static landing page can compute the same numbers in a browser. Ours — regenerate from the CSVs, don't hand-edit. |
| `site/snapshot.js` | — | A dated snapshot of governed numbers exported from the five semantic views (org health, pay equity with suppression applied, employee voice, band health, governance) for the landing page's later sections. Aggregates and synthetic transcripts only. Regenerate with `scripts/export_site_snapshot.py`. Ours. |

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
| `data/generate_voice_transcripts.py` | Generates the 18 hand-authored stay/exit interview transcripts. `--verify` asserts length spread, no templating, and that the cross-signal is demonstrable |
| `scripts/load_workforce_data.py` | One-shot pipeline: generate → verify → stage (space-free path) → emit/run the load SQL. **Owns the single CSV `FILE_FORMAT` and the single load path for all 4 CSVs** |
| `.cortex/skills/workforce-astra-data-gen/SKILL.md` | **CoCo CLI skill 1** — invoke as `$workforce-astra-data-gen`. Generate, verify, stage, load |
| `.cortex/skills/workforce-astra-governance-check/SKILL.md` | **CoCo CLI skill 2** — invoke as `$workforce-astra-governance-check`. Run and *explain* the regression suite, name the owner of any failing metric, and separate deterministic from model-dependent failures |
| `scripts/governance_check.py` | Backing script for skill 2. Deterministic PASS/FAIL, non-zero exit, `--json`, and an unregistered-metric check. Portable to any project with the same three tables |
| `mcp_server/workforce_astra_mcp.py` | Mock MCP action server (6 tools). `--selftest` runs without a client and exits 0 |
| `sql/01_create_tables.sql` | Raw table DDL |
| `sql/02_semantic_view.sql` | `employee_360` Semantic View + 5 verified queries (incl. the governed-vs-naive comparison) |
| `sql/03_load_data.sql` | Historical output of the loader for the first 3 CSVs. **Superseded** — the canonical load path is `scripts/load_workforce_data.py` (now all 4 CSVs) and `scripts/rebuild_all.py` |
| `sql/04_cortex_search.sql` | Cortex Search service over `review_text` — **live & ACTIVE over 127 reviews, verified 25-Sep-2026** (evidence step) |
| `sql/05_org_health.sql` | Org hierarchy, `org_walk_up` UDF, guarded `simulate_reorg` proc, `org_health_360` view |
| `sql/06_pay_equity.sql` | Demographics, cohort k-anonymity suppression, masking policy, `pay_equity_360` view |
| `sql/07_metric_governance.sql` | Metric registry, golden-value regression tests (17), drift proc, 2 scheduled Tasks |
| `sql/08_employee_voice.sql` | Employee voice: transcripts table, **Snowpark Python** `score_voice_transcripts()` (Cortex SENTIMENT + AI_CLASSIFY), `voice_risk_360` cross-signal view, `employee_voice_360` semantic view |
| `sql/09_band_architecture.sql` | Band architecture: `band_range_health`, `band_range_overlap`, `band_review_findings`, `run_band_review()` (reports, never proposes), `band_health_360` view, quarterly Task |
| `scripts/rebuild_all.py` | **One-command rebuild** for a fresh trial account — regenerates data, splices `sql/*.sql` in dependency order with the database name substituted, applies via `snow` or CoCo, then scores + audits + tests |
| `scripts/export_site_snapshot.py` | Exports the landing page snapshot (`site/snapshot.js`) from the semantic views over the key-pair connection. Re-run after any data change so the public page stays accurate |
| `scripts/test_rebuild_splitter.py` | Offline test for the rebuild's SQL statement splitter (protects `$$` procedure bodies). Run after touching any `sql/` file |
| `WORKDAY_LLM_PROMPT.md` | Reusable prompt pack so other LLMs can extend the Workday action layer in parallel |
| `MCP_TOOLS.md` | The 6 mock MCP tool definitions for the closed-loop action |
| `SUBMISSION_BRIEF.md` | Ready-to-paste MVP brief, states the Employee 360 reframe explicitly |
| `DEMO_SCRIPT.md` | Final recording script: pre-flight, verbatim narration per beat, post-recording and submission steps |
| `DECK_CONTENT.md` | Slide-by-slide deck content for the Hack2Skill template |
| `deck/Workforce_Astra_Submission_Deck.pdf` / `.pptx` | The submission deck on the official template (10 slides). Rebuilt by `scripts/build_deck.py`, which needs the template `.pptx` in this folder (not committed) |
| `PROMPTS_FOR_AGENTS.md` | Copy-paste prompts for OpenCode and Antigravity |
| `requirements.txt` | `faker` (data gen) + `mcp` (mock MCP server — 2.x API) |

## Note on the parked alternative
`hackathons/Snowflake-Astra-OntoChain/` (Supply Chain Ontology track) is left in place untouched
as a fallback, not deleted. Same technical pattern, different entities — if Workforce Astra hits
a wall, that scaffold is still ready.
