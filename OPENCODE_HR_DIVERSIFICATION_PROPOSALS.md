# Workforce Astra — HR Process Diversification Proposals (OpenCode Evaluation)

**Document Date:** 21-Sep-2026
**Project:** Workforce Astra (`Snowflake-Workforce-Astra`)
**Track:** Customer 360 / Employee 360
**Author:** Ojasvi OpenCode Astra (OpenCode CLI)
**File Location:** `F:\AGENTIC WORLD\hackathons\Snowflake-Workforce-Astra\OPENCODE_HR_DIVERSIFICATION_PROPOSALS.md`

> This is an **independent second opinion**, produced in parallel with the Antigravity set
> (`ANTIGRAVITY_HR_DIVERSIFICATION_PROPOSALS.md`). It is grounded in the *actual* repo schema
> (`raw_workday_workers`, `raw_compensation_bands`, `raw_performance_reviews`, the
> `employee_360` Semantic View, `review_search_service`, and the local CoCo MCP server), and it
> deliberately differs in ranking from the Antigravity set so the comparison is meaningful.

---

## Executive Summary

Workforce Astra's thesis — a governed analytics layer on the enterprise's own warehouse instead of
a rigid HRMS (Workday / SuccessFactors) — extends naturally into every adjacent HR process once you
have one conformed employee key and one governed metric layer. The MVP already has: 150 synthetic
employees, the governed FTE-vs-naive headcount conflict, comp-ratio + flight-risk detection with
Cortex Search evidence, a mocked Slack/Workday MCP action, and a live Streamlit-in-Snowflake portal.

To maximise **Real-World Relevance, Technical Execution, Solution Completeness** and the **Ingenuity
Bonuses** (reusable skills, MCP connectors, scheduled automations, custom function-calling tools,
multi-agent orchestration, multi-surface, guardrails), below are the **Top 5 diversification
proposals into new HR *business processes*** (not more metrics on the same data), ranked strictly by:

$$\text{Priority Score} = \frac{\text{Impact} \times \text{Rubric Fit}}{\text{Effort}}$$

Impact and Rubric Fit are each scored /10; Effort is in hours given the existing schema + portal.

---

## 1. Top 5 Ranked Proposals (Comparison Table)

| Rank (Score) | Concept & HR Domain | Real-World Problem / Enterprise Relevance | Snowflake + Cortex Mapping | Ingenuity Bullets Hit | Effort | Impact | Rubric |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **#1 (28.8)** | **Org Design & Manager Health Sentinel** — *Org Design* | Reorgs, M&A integration and "unmanageable manager" problems cost enterprises millions; span-of-control, org depth and manager-attributed attrition are owned by nobody, so HR and Finance re-litigate org cost every cycle. | Reuse `raw_workday_workers.manager_id`; one recursive-CTE **Task** materialises `raw_org_flattened` (root_id, `org_level`, `span_of_control`, `chain`). Metrics: `avg_span_of_control`, `org_depth`, `single_report_managers`, `overspan_managers`, `unexplained_attrition_by_manager`, `flight_risk_reports_per_manager`. **AI_CLASSIFY** labels manager-quality themes in `review_text`; Cortex Search over reviews grouped under a manager. | Custom function tool (recursive `org_walk_up` UDF); **multi-agent** (OrgDesignAstra proposes reorg, critic agent stress-tests); Cortex Analyst; multi-surface | **2.5 h** | 8 | 9 |
| **#2 (23.1)** | **Pay-Equity & Adverse-Impact Auditor** — *DEI / Pay Equity* | The EU Pay Transparency Directive lands 2026 and US state laws + OFCCP make *unexplained* gaps a legal and reputational risk; only **adjusted** gaps (controlling band, tenure, rating) survive board scrutiny. | Add `raw_employee_demographics` + `raw_pay_decisions`; a monthly **Task** fits `comp_ratio ~ band + tenure + rating` in Snowpark and writes `pay_equity_summary` (raw gap, adjusted gap, 4/5ths adverse-impact ratio) exposed as metrics on a `pay_equity_360` view. **AI_COMPLETE** drafts the remediation memo; **AI_CLASSIFY** normalises termination reasons; Cortex Search for bias-adjacent review language. | **Guardrails / graceful fallback** (masking policies on protected attrs, row-access policy, k-anonymity suppression n<5, MCP tool refuses sub-5 cohorts); **scheduled automation** (monthly audit + alert on drift); Cortex Analyst | **3.5 h** | 9 | 9 |
| **#3 (18.3)** | **Promotion & Leveling Equity Copilot** — *Promotion / Leveling* | Promotion is the most opaque and most litigated HR process; calibration is gut-feel, time-in-band stagnation and unequal promo rates by department/group drive attrition and claims. | Add `raw_compensation_events` (Hire/Promotion/Transfer/Adjustment, from_band→to_band, effective_date) — also gives a real **event / SCD2 history** that deepens the whole view. Metrics: `promo_rate_12m`, `avg_time_in_band_days`, `time_since_last_promo`, `level_mix`. **AI_CLASSIFY** review_text → "ready for next level"; Cortex Search pulls verbatim evidence for a promo packet. | Custom function tool (`promotion_readiness_score` UDF); Cortex Search evidence; event-history modelling; multi-surface | **3.5 h** | 8 | 8 |
| **#4 (18.0)** | **Hiring Funnel Command Center** — *Hiring Funnel* | TA is a top-3 enterprise HR cost, yet TA, Finance and hiring managers each quote a different time-to-fill / offer-accept; source-of-hire ROI is essentially ungoverned. | Add `raw_requisitions` + `raw_applications` (stage + stage_entered_date) + `raw_candidate_notes`. Metrics: `open_reqs`, `time_to_fill_days`, `stage_conversion`, `offer_accept_rate`, `source_of_hire_quality`. A daily **Task** snapshots `raw_funnel_daily` for trend + SLA-breach alerts. **AI_COMPLETE** summarises offer-decline reasons; Cortex Search over recruiter/candidate notes. | **MCP connector** (ATS — local stdio, so it can be a *real* call); scheduled automation; Cortex Search; custom function (SLA-breach detector); multi-surface | **4.0 h** | 9 | 8 |
| **#5 (16.0)** | **Skills Coverage & Reskilling Navigator** — *L&D / Workforce Planning* | Skills gaps, single-points-of-failure and certification compliance are invisible until someone leaves or an audit hits; L&D spend is rarely tied to coverage or succession risk. | Add `raw_skills`, `raw_employee_skills`, `raw_learning_records` (completions + cert expiry). Metrics: `skill_coverage_pct`, `critical_spof_count` (skill held by exactly 1 person), `cert_compliance_rate`, `ld_hours_per_employee`, `skill_concentration`. **EMBED / AI_SIMILARITY** match skills↔courses↔job titles; **AI_COMPLETE** generates a personalised learning path; Cortex Search over the course catalogue. | **Reusable / shareable skills** (`cortex skill`); **MCP connector** (LMS); custom function tool (`learning_path(employee_id, target_band)`); scheduled automation (daily SPOF recompute + cert-expiry alerts) | **4.5 h** | 8 | 9 |

---

## 2. Detailed Technical Specifications

### #1. Org Design & Manager Health Sentinel (Org Design)

* **Real-World HR Problem:** Corporate efficiency mandates demand spans of 6–10 and org depth ≤ 5, yet middle managers hire 1–2 reports to justify title inflation. Finance and HR each measure "management overhead" differently, and neither has an automated view of depth, span or bottleneck managers.
* **Snowflake & Cortex Architecture:**
  * **Data Layer:** Uses the existing `raw_workday_workers.manager_id` (no new synthetic table required).
  * **Task / Dynamic Table (`raw_org_flattened`):** Recursive CTE computing `org_level`, `span_of_control`, `root_id` and management chain; recomputed on a schedule.
  * **Semantic View (`employee_360` additions):** Dimensions `management_tier`, `org_level`; metrics `avg_span_of_control`, `org_depth`, `single_report_managers`, `overspan_managers`, `unexplained_attrition_by_manager`, `flight_risk_reports_per_manager`.
  * **Cortex Analyst:** *"Which departments have average span of control below 4?"*, *"List M2 managers with fewer than 3 direct reports."*
  * **AI / Cortex:** `AI_CLASSIFY` over `review_text` labels manager-quality signals; `AI_COMPLETE` drafts a reorg recommendation memo from structural anomalies.
* **Ingenuity Bullets:** Custom function tool (`org_walk_up` recursive UDF); multi-agent (proposer + critic); Cortex Analyst; multi-surface (CLI + Streamlit org tree).
* **Effort:** **2.5 h** (0 new tables; Task + a few Semantic View metrics + 1 UDF + 1 portal chart).

### #2. Pay-Equity & Adverse-Impact Auditor (DEI / Pay Equity)

* **Real-World HR Problem:** Board/ESG asks for the *unadjusted* gap (which looks alarming purely from band mix); Legal needs the *adjusted* gap (band, tenure, rating) to defend against liability. The two numbers are routinely confused, and there is no governed definition.
* **Snowflake & Cortex Architecture:**
  * **Data Layer:** `raw_employee_demographics` (protected attributes) + `raw_pay_decisions` (hires / adjustments with effective dates, to detect drift).
  * **Scheduled model:** A monthly Task fits `comp_ratio ~ band + tenure + rating` (Snowpark) and persists `pay_equity_summary` (raw gap, adjusted gap, 4/5ths adverse-impact ratio) — surfaced as metrics on `pay_equity_360`.
  * **Cortex Analyst:** *"Adjusted pay gap by gender in Engineering at IC4"* — deterministic SQL against governed metrics.
  * **Cortex Search + AI:** Search for bias-adjacent review language; `AI_COMPLETE` drafts the remediation narrative; `AI_CLASSIFY` normalises termination reasons.
* **Ingenuity Bullets:** Guardrails / graceful fallback (masking policies, row-access policy, k-anonymity suppression n<5, MCP refusal on sub-5 cohorts); scheduled automation (monthly audit + drift alert); Cortex Analyst.
* **Effort:** **3.5 h** (1–2 new tables, 1 Task, 3 metrics, 1 privacy-guardrail function).

### #3. Promotion & Leveling Equity Copilot (Promotion / Leveling)

* **Real-World HR Problem:** Calibration cycles devolve into debate because nominations are subjective and HR enforces tenure/budget rules by hand. Time-in-band stagnation and unequal promo rates by group are hidden.
* **Snowflake & Cortex Architecture:**
  * **Data Layer:** `raw_compensation_events` (`event_type`, `from_band`, `to_band`, `effective_date`, `reason`) — a real event/SCD2 fact table that materially enriches the Semantic View.
  * **Semantic View:** `promo_rate_12m`, `avg_time_in_band_days`, `time_since_last_promo`, `level_mix`.
  * **Cortex Search:** Indexes nomination / review text to verify claims against recorded milestones.
  * **AI / Cortex:** `AI_CLASSIFY` review_text → "ready for next level" signals; `AI_COMPLETE` assembles a calibration packet.
* **Ingenuity Bullets:** Custom function tool (`promotion_readiness_score`); Cortex Search evidence; event-history modelling; multi-surface.
* **Effort:** **3.5 h** (1 new event table, 3–4 metrics, 1 UDF, Search index).

### #4. Hiring Funnel Command Center (Hiring Funnel)

* **Real-World HR Problem:** Finance blames Recruiting for slow hiring; Recruiting quotes ATS time-to-fill from *job post*; the hiring manager counts from *budget approval*. Three systems, three clocks, no single governed funnel metric.
* **Snowflake & Cortex Architecture:**
  * **Data Layer:** `raw_requisitions` (`budget_approved_date`, `job_posted_date`, `filled_date`, `status`) + `raw_applications` (`stage`, `stage_entered_date`, `source`) + `raw_candidate_notes`.
  * **Semantic View:** `open_reqs`, `time_to_fill_days`, `time_to_hire_days`, `stage_conversion`, `offer_accept_rate`, `source_of_hire_quality` (joins back to `rating_score` for post-hire quality).
  * **Scheduled automation:** Daily Task snapshots `raw_funnel_daily` → trend + SLA-breach alerts.
  * **Cortex Search + AI:** Search over recruiter/candidate notes; `AI_COMPLETE` summarises offer-decline reasons; `AI_CLASSIFY` categorises decline drivers.
* **Ingenuity Bullets:** MCP connector (ATS); scheduled automation; Cortex Search; custom function (SLA-breach detector); multi-surface.
* **Effort:** **4.0 h** (2 new tables + 1 notes table, 1 daily Task, 5–6 metrics, 1 MCP tool).

### #5. Skills Coverage & Reskilling Navigator (L&D / Workforce Planning)

* **Real-World HR Problem:** On a strategic pivot (e.g. on-prem → Snowflake AI Cloud) leadership defaults to external hiring ($30k+ agency fee + ramp) while internally adjacent skills are invisible because they live in static resumes and LMS logs. Nobody knows where the single-points-of-failure are.
* **Snowflake & Cortex Architecture:**
  * **Data Layer:** `raw_skills`, `raw_employee_skills` (proficiency, last_used), `raw_learning_records` (completions + cert expiry).
  * **Semantic View:** `skill_coverage_pct`, `critical_spof_count` (skills held by exactly 1 person), `cert_compliance_rate`, `ld_hours_per_employee`, `skill_concentration`, `internal_mobility_candidate_pool`.
  * **AI / Cortex:** `EMBED` / `AI_SIMILARITY` for skill↔course↔job matching; `AI_COMPLETE` builds a 90-day reskilling plan; Cortex Search over the course catalogue.
  * **Scheduled automation:** Daily Task recomputes SPOF; cert-expiry alerts within 30 days.
* **Ingenuity Bullets:** Reusable / shareable CoCo skill; MCP connector (LMS); custom function tool (`learning_path(employee_id, target_band)`); scheduled automation.
* **Effort:** **4.5 h** (3 new tables, 4–5 metrics, 1 UDF wrapped as a tool, 1 CoCo skill).

---

## 3. Recommended Sequencing

1. **Sprint 1 — #1 Org Design Sentinel (~2.5 h):** zero new tables; one Task, a few metrics, one recursive UDF, one portal view. Highest ratio, fastest win.
2. **Sprint 2 — #2 Pay-Equity Auditor (~3.5 h):** maximum "enterprise-grade" credibility, and the guardrail story (k-anonymity + masking + MCP refusal) is a direct rubric hit.
3. **Sprint 3 — #3 Promotion Copilot (~3.5 h):** the one new event table that makes the Semantic View genuinely richer; enables clean multi-agent (quant + qual) orchestration.
4. **Sprint 4/5 — #4 Hiring Funnel (~4.0 h) / #5 Skills Navigator (~4.5 h):** pick by remaining time; #4 for the MCP + scheduled-automation story, #5 for the reusable-skill + AI-similarity story.

---

## 4. Cross-Cutting Build Notes

* **Trial-account constraint (important):** this account has **no External Access Integration (EAI)**, so keep all Snowflake-side work in-warehouse — Tasks, Cortex AI functions, Cortex Search/Analyst and Snowpark UDFs all work without it. Do external tool calls from the **local CoCo MCP server (stdio)**, which is *not* EAI-bound; you can promote one mock tool to a **real** HTTP call (e.g. a Slack incoming webhook) to make the "MCP connector" claim literal.
* **One conformed key, many domains:** keep `employee_id` as the shared dimension, build one Semantic View per process plus an umbrella `workforce_360` view — this preserves the "identical governed answer" thesis while diversifying process coverage.
* **Keep the deliberate-conflict pattern:** the headcount FTE-vs-naive conflict is what makes the governance point land; replicate it per domain (e.g. recruiter pipeline count vs governed `time_to_fill_days`; raw avg comp by cohort vs adjusted gap).
* **Skill + agent packaging:** one CoCo subagent per domain (OrgDesignAstra, PayEquityAstra, TalentAstra, SkillsAstra), each bundling its `SKILL.md` + MCP tools, under an orchestrator that routes by question — the strongest reusable-skills + multi-agent story.
* **Guardrails everywhere:** masking policies on PII, row-access policies, k-anonymity (n<5) suppression, and MCP tool refusal guards (extend the existing `slack_notify_manager_flight_risk` pattern).

---

## 5. Notable Differences vs the Antigravity Proposal Set

For the parent review — stated neutrally, not as corrections:

* **Ranking emphasis:** this set ranks **Pay-Equity #2** (legal/compliance urgency, EU directive) and keeps **Promotion & Leveling as a distinct #3**, whereas the Antigravity set ranks Promotion #3 and Pay-Equity #2 with a slightly different score scale; both agree Org Design is #1.
* **Metric mechanism:** here, adjusted pay equity is fitted with a **scheduled Snowpark model persisted to a table** and exposed as governed metrics (so Cortex Analyst returns deterministic SQL); the Antigravity set expresses the adjusted gap as same-band/same-department Semantic View metrics. Both are valid; the persisted-model route also yields an auditable artifact.
* **MCP realism:** both sets use MCP connectors; here we note explicitly that the **local stdio MCP server is not EAI-bound**, so at least one connector can be made a real external call — worth doing for the bonus.
* **Runners-up not in the top 5 (both sets scored them out):** a **Workforce Planning Scenario Simulator** (`SNOWFLAKE.ML.FORECAST` + what-if UDF + planner/critic agents, ≈14.0) and a **Voice-of-Employee / eNPS** add-on (AI_SUMMARIZE_AGG over survey verbatims + k-anonymity, scores high but overlaps the existing retention thesis).
