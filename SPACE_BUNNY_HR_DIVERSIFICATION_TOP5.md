# Workforce Astra — HR Process Diversification (Space Bunny Evaluation)

**Author:** Space Bunny (`opencode/space-bunny-free`)
**Written:** 25-Sep-2026
**Read before writing:** `README.md`, `sql/01`–`sql/07`, `MCP_TOOLS.md`, and the three sibling proposals in this folder
(`ANTIGRAVITY_HR_DIVERSIFICATION_PROPOSALS.md`, `COPILOT_HR_DIVERSIFICATION_TOP5.md`,
`OPENCODE_HR_DIVERSIFICATION_PROPOSALS.md`).

## Executive summary

All three sibling proposals converged on the **same five ideas**: org health, pay equity, promotion/leveling,
hiring funnel, skills/L&D. Two of those five are **already shipped and verified live** in this repo
(`sql/05_org_health.sql`, `sql/06_pay_equity.sql` — both dated 21-Sep-2026, both with verified golden values).
This set therefore deliberately **excludes** org health and pay equity, and also excludes hiring funnel and
promotion/leveling (triple-proposed, zero competitive differentiation).

What remains are four HR business processes that are structurally distinct from headcount/retention:
**workforce management (absence)**, **workforce planning (cost model)**, **job architecture (band health)**,
**talent mobility (internal fill)**, **talent development (onboarding ramp)**.

Scoring: `(impact × rubric fit) ÷ effort hours`.

## 1. Top 5, ranked

| Rank | Idea (HR process) | Enterprise problem solved | Snowflake / Cortex mapping | Rubric bullets hit | Effort | Impact | Rubric | Score |
|:---:|---|---|---|---|:---:|:---:|:---:|:---:|
| **1** | **Absenteeism, PTO Liability & Burnout Sentinel** — Workforce Management | Unplanned absence and burnout are the #1 silent driver of schedule cost and attrition. PTO accrual liability is a balance-sheet line nobody reconciles; WFM teams and HR each keep their own absence codes, so "return-to-work risk" is unmeasured. Adjacent to the comp themes and *structurally different* — it's calendar/absence, not pay. | **New tables:** `raw_absence_events` (employee_id, leave_type, start_date, end_date, hours, reason_text, return_to_work note), `raw_pto_ledger` (accrual, used, balance, carryover_cap), plus a `raw_overtime` rollup. **Semantic view `workforce_availability_360`:** `absence_rate`, `repeat_absence_flag` (>=3 events / 6mo), `pto_liability_usd` (accrued hours x band midpoint, capped at carryover), `burnout_index` (absence + goals_met_pct + tenure band), `coverage_risk_by_manager`. **AI functions:** `AI_CLASSIFY(reason_text -> {medical, caregiving, burnout, work-stress, other})` — a *real* unstructured-to-structured extraction, the strongest `AI_*` demo available, plus `AI_COMPLETE` for a manager-coverage brief. **Cortex Search** over return_to_work notes for cited burnout evidence. | Custom function tool (`burnout_risk(employee_id)` + `absence_reason_classify`); scheduled automation (daily absence scan -> Slack); **guardrails** (k-anonymity n<5 on health-adjacent cohorts, MCP tool refuses single-employee health inference, dry-run default); multi-surface; AI functions | **3.0 h** | 8 | 9 | **24.0** |
| **2** | **Workforce Cost Model & Attrition What-If Planner** — Workforce Planning x Finance | This is the direct answer to the project's own thesis: Finance and HR disagree on cost-per-head, replacement cost, and headcount plan by *definition*, not by data. Today the answer is "ask the FP&A team." It converts the Semantic View from an HR tool into a planning tool the CFO will fund. | **New tables:** `raw_workforce_plan` (fiscal_period, department_code, plan_fte, plan_usd, cost_center), `raw_comp_events` (Hire/Promotion/Transfer/Adjustment with cost delta — reuse this for promotion *history* too), and a `scenario` table. **Semantic view `workforce_cost_360`:** `cost_per_fte`, `dept_cost_per_fte`, `annualized_terminated_cost` (from `termination_date`), `replacement_cost_est` (1.4 x avg band midpoint + recruiter fee), `plan_variance_fte`, `cost_of_1pct_attrition`. **Custom function:** `what_if_attrition(dept, pct, scenario_id)` stored proc returning delta-FTE / delta-cost / which backfills to cut. **AI_COMPLETE** writes the board-ready WFP narrative. | Multi-agent orchestration (planner agent proposes cuts -> challenger agent stress-tests against the org-health semantic view before anything is recommended); custom function tool; multi-surface (CLI scenario, portal panel, Snowsight); **guardrails** (scenario never mutates the plan table, every recommendation cites governed metrics); scheduled (monthly plan-variance Task) | **3.5 h** | 9 | 8 | **20.6** |
| **3** | **Comp Band Architecture Auditor** — Job Architecture / Range Design | Bands get set once and drift for years: red-circle rates (paid above band max), range penetration clustering at the floor, adjacent-band overlap, and compression. Band health is invisible until an audit or a failed offer cycle. Structural comp, not demographic — complements `sql/06` pay equity rather than duplicating it. | **New tables:** none required — reuses `raw_workday_workers` + `raw_compensation_bands` only. Cheapest idea on this list. **Semantic view `band_health_360`:** `red_circle_rate` (base_pay > max_base), `avg_range_penetration` (base-min)/(max-min), `band_overlap_index`, `compression_ratio` (max/mid of *actual* distribution), `in_floor_cluster_pct`, `offer_reject_risk_index` (band position vs comp_ratio). **Custom function:** `propose_band_review(band_code)` returning flagged outliers only — never a proposed number. **AI_COMPLETE** drafts the band-review memo. | Guardrails (MCP tool *reports* outliers, human sets the number; refuses to auto-adjust); multi-agent (band architect proposes -> compa-ratio critic rejects); scheduled automation (quarterly Task); reusable/shareable skill (works on any banded workforce) | **2.5 h** | 7 | 8 | **22.4** |
| **4** | **Internal Mobility Marketplace (Vacancy-Fill-First)** — Talent Mobility | External hiring at 1.4x replacement cost is approved without checking whether an internal candidate already exists at 80% of the band. Internal fill rate, lateral-move pay equity, and post-move performance lift are ungoverned. Vertically distinct from promotion — this is *lateral* + relocation, the process nobody measures. | **New tables:** `raw_internal_postings` (posting_id, band, dept, opened_date, filled_by), `raw_internal_applications` (employee_id -> posting_id, stage, outcome, move_date), `raw_mobility_events` (transfer / rotation / secondment with from->to dept). **Semantic view `mobility_360`:** `internal_fill_rate`, `lateral_move_velocity`, `post_move_perf_delta` (goals_met_pct before vs after, same employee), `lateral_move_pay_delta`, `postings_without_internal_candidates`. **AI functions:** `EMBED_TEXT` / `AI_SIMILARITY` matches free-text internal resumes -> postings (real vector use, not a metaphor); `AI_CLASSIFY` on posting descriptions to detect biased language. **Cortex Search** over internal applicant rationales. | Reusable/shareable skill (`audit-internal-fill-rate`, schema-agnostic); MCP connector (postings/HRIS); custom function tool (`match_internal_candidates(posting_id)`); multi-surface; guardrails (never auto-post a req, gendered-language flag is advisory) | **4.5 h** | 8 | 9 | **16.0** |
| **5** | **Onboarding Ramp & Time-to-Productivity** | New-hire ramp is 6-12 months and almost never measured outside manager anecdote. 90-day attrition is the leading indicator of a broken onboarding process, and it lands on the manager, not the recruiter. A clean, self-contained HR process with an obvious CFO-legible output. | **New tables:** `raw_onboarding_milestones` (employee_id, milestone, due_date, completed_date, owner), `raw_training_completions` (course, score, completed_date), `raw_first_review` (first post-hire `review_id`, its `goals_met_pct`). **Semantic view `ramp_360`:** `time_to_first_rating`, `ramp_pct_vs_peer_cohort`, `ninety_day_attrition`, `onboarding_completion_rate`, `manager_onboarding_effectiveness` (90-day attrition grouped by `manager_id` — reuse the org hierarchy, no new hierarchy work). **AI_EXTRACT** pulls capability signals out of `review_text` for new hires only; **Cortex Search** for the first-review evidence behind a low ramp score. | Scheduled automation (monthly cohort Task; the 90-day window is *natively* time-based); custom function tool (`ramp_status(employee_id)`); MCP connector (LMS); multi-surface; guardrails (cohorts n<5 suppressed) | **4.0 h** | 7 | 8 | **14.0** |

### Note on #3's score

#3 (22.4) scores above #2 (20.6) on the formula but is ranked below it. Ranking is impact-first as the user
specified; #2 is the stronger real-world story and the only one that makes Finance a first-class stakeholder of
the semantic layer. #3 is the effort-floor option — build it if hours are short.

## 2. Build order recommendation

| Order | Idea | Cumulative effort | Why this order |
|:---:|---|:---:|---|
| 1 | Band Architecture Auditor | 2.5 h | Zero new source data. Proves the "add a governed view" pattern in under 3 hours, which de-risks everything after it. |
| 2 | Absenteeism / Burnout Sentinel | +3.0 h | Strongest `AI_*` story, and absence data is the most obviously *synthetic-but-realistic* thing to generate alongside what already exists. |
| 3 | Workforce Cost Model | +3.5 h | Highest judge-impact. Only worth building once 1 and 2 prove the multi-view pattern. |
| 4 | Internal Mobility Marketplace | +4.5 h | Most novel, most work. Cut first if time runs out. |
| 5 | Onboarding Ramp | +4.0 h | Cleanest fallback — self-contained, no dependency on 1-4. |

Minimum viable addition for judging purposes: **#1 + #3 (5.5 h)** gets you three governed semantic views
(employee_360, org_health_360, band_health_360) plus a real `AI_CLASSIFY` demo.

## 3. Comparison with the other three proposals in this folder

### 3.1 Overlap map

| Idea | Antigravity | Copilot | OpenCode | **Space Bunny** |
|---|:---:|:---:|:---:|:---:|
| Org health / span of control | #1 | #1 | #1 | *skipped — shipped in `sql/05`* |
| Pay equity / DEI | #2 | #2 | #2 | *skipped — shipped in `sql/06`* |
| Promotion / leveling equity | #3 | #3 | #3 | *skipped — triple-proposed* |
| Hiring funnel / req SLA | #4 | #4 | #4 | *skipped — triple-proposed* |
| Skills / reskilling / L&D | #5 | #5 | #5 | *skipped — triple-proposed* |
| Absenteeism / PTO / burnout (WFM) | — | — | — | **#1** |
| Workforce cost model / what-if planning | — | — | — | **#2** |
| Comp band architecture (job architecture) | — | — | *partially* (band-mix inside pay equity) | **#3** |
| Internal mobility / vacancy-fill-first | — | — | — | **#4** |
| Onboarding ramp / time-to-productivity | — | — | — | **#5** |

**Overlapping proposals across all four sets: 0. This set is fully disjoint from the other three.**

### 3.2 Where I think the other three are strongest

- **OpenCode's set is the best-engineered technically.** It is the only one that proposes a real event/SCD2
  history table (`raw_compensation_events` with from_band -> to_band), which genuinely deepens the whole semantic
  view and is the kind of thing a Snowflake judge recognises. Its `org_walk_up` recursive UDF idea is also the
  sharpest single-function proposal in the folder. If you only read one sibling file, read that one.
- **Copilot's set is the most governance-literate.** The k<5 cohort suppression, "deterministic SQL establishes
  facts, `AI_COMPLETE` only narrates after" separation, and the explicit separation of policy-eligibility from
  narrative-evidence are exactly the guardrail posture a judge probing for failure modes wants to hear.
- **Antigravity's set is the best structured as a document** — the per-proposal spec sections and the same-day
  sequencing section make it the most immediately actionable read of the three.

### 3.3 Where I think the other three are weakest

1. **All three re-propose work that is already shipped.** Org health and pay equity are deployed and verified
   (`sql/05`, `sql/06`, both 21-Sep-2026). Presenting them as proposals spends hours re-deriving a finished
   artifact and inflates the submission with things a judge can't verify are new. The correct framing is
   *"here are two governed views shipped; here are the next three"* — which is what this document does.
2. **All three converge on the identical five ideas.** For a comparative judging panel this is a wash — if
   another team submits hiring-funnel-plus-promotion, building the same thing gains you nothing on any axis.
3. **The skills/L&D idea in all three is the weakest of the common five.** It needs a new skills taxonomy, an
   employee-skills table, a course catalogue, and a learning-records table — four new synthetic sources before
   a single metric is computable. At 4.5-5 h it is the lowest impact-per-hour item any of the four sets proposes.
4. **Nobody proposed a genuinely different AI function.** Three of four sets lean on `AI_COMPLETE` (narrative
   generation) and Cortex Search. `AI_CLASSIFY` on absence/reason text and `EMBED_TEXT` on resumes are the two
   places where an AI function is doing *classification* or *retrieval* rather than *prose*, which is harder to
   fake and easier for a judge to verify correctness on.
5. **Nobody bridged HR to Finance.** All three keep every idea inside the HR silo. Your own stated thesis — HR
   and Finance get different answers to the same question — is only fully proven when the CFO is a consumer of
   the semantic layer, not just a persona in the demo. That is idea #2 here.

### 3.4 Honest risks in *my* set

- **#1 depends on synthesising absence data that nobody has reviewed.** If the reason-text is too obviously
  templated, the `AI_CLASSIFY` demo looks trivial. Write 12-15 genuinely varied free-text reason strings and it
  holds up.
- **#2 is the most likely to be judged "not Employee 360."** The track is Customer 360 / Employee 360; a cost
  planner is adjacent. Counter it by framing it as *"the Employee 360's second consumer is Finance, and here
  is the metric that proves it"* — keep `employee_id` grain visible in the view so it stays an Employee 360
  artifact, not a finance artifact.
- **#4 is the highest effort and the least certain payoff.** It is the first thing to cut. It stays on the list
  because `EMBED_TEXT` resume matching is the single most quotable technical bullet in this document, not
  because the HR problem is urgent.
- **#5 is safe but forgettable.** It is the correct answer to "what do we build if everything else is on fire",
  not a differentiator.

## 4. Cross-cutting notes

- Every proposal above follows the repo's existing pattern: new `raw_*` table at employee grain, one derived
  table at employee grain (avoids fan-out in the semantic view), one `SEMANTIC_VIEW`, one or more UDFs, one or
  more Tasks. Nothing proposed breaks the `TABLES -> RELATIONSHIPS -> FACTS -> DIMENSIONS -> METRICS -> COMMENT
  -> AI_VERIFIED_QUERIES` clause order, and every proposal fully qualifies `SEMANTIC_VIEW(DB.SCHEMA.VIEW ...)`
  and references the view logically rather than by physical table — both documented pitfalls from the 21-Sep fix
  in `sql/02_semantic_view.sql`.
- Every proposal keeps `dry_run: true` as the default on any new MCP tool, matching `MCP_TOOLS.md`. None of
  these proposals writes to Workday or Slack for real.
- Synthetic-data generation should be deterministic (`HASH(employee_id || '<field>')`) as already used in
  `sql/06_pay_equity.sql`, so judges can re-run generation and get identical values.
- Suppress any cohort under 5 people in the portal, the CLI, and the Slack output. With only 150 employees
  this matters, and a judge *will* ask.
