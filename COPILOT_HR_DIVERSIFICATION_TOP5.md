# Workforce Astra — Top 5 HR Process Diversification Opportunities

**Prepared:** 21-Sep-2026  
**Project:** Workforce Astra — Snowflake Employee 360  
**Ranking formula:** `(impact × rubric fit) ÷ effort`

## Context

Workforce Astra already has synthetic HRIS, compensation, and performance-review data for
150 employees; a governed `employee_360` Semantic View; Cortex Analyst metrics for
headcount, attrition, and comp-ratio; Cortex Search evidence retrieval; mocked Slack/Workday
actions; and a Streamlit-in-Snowflake portal.

The opportunities below deliberately expand into different HR business processes rather than
adding more slices of the existing headcount/retention dashboard. Estimates assume the current
schema, portal, Snowflake account, and working CoCo/MCP patterns can be reused.

## Ranked comparison

| Rank | Opportunity | Enterprise HR problem solved | Snowflake Semantic View + Cortex pattern | Rubric / ingenuity fit | Effort | Relative score |
|---:|---|---|---|---|---:|---:|
| **1** | **Org Health & Span-of-Control Sentinel**<br>**Domain:** Org design and management efficiency | Leadership needs a trusted answer to management layers, spans of control, player-coach managers, and organizational bottlenecks. Finance, HR, and Engineering often count “managers” and organizational depth differently, making restructuring decisions political rather than evidence-based. | **New tables:** None required initially; reuse `raw_workday_workers.manager_id`, department, band, and employment status. Add a dynamic table or view that calculates direct reports, hierarchy depth, manager-to-IC ratio, and orphan/cycle validation. Extend `employee_360` with `avg_span_of_control`, `org_depth`, `manager_population`, and `narrow_span_manager_ratio`. Cortex Analyst answers governed org-design questions; Cortex `COMPLETE` drafts a cited reorganization memo. | **Custom function-calling tool:** `simulate_reorg(source_manager, target_manager)` previews metric changes before mutation.<br>**Guardrails:** reject circular reporting lines, orphaned employees, inactive managers, and changes outside the permitted org scope.<br>**Multi-surface:** CLI analysis plus portal org view. | **2–3 h** | **9.6 / 10** |
| **2** | **Pay Equity & Compensation Governance Auditor**<br>**Domain:** DEI, pay equity, and compliance | The board/legal team needs unadjusted demographic pay gaps, while compensation leaders need adjusted comparisons controlling for band, department, tenure, and performance. A single “pay gap” number without cohort rules can mislead decision-makers and create privacy risk. | **New table:** Add synthetic `raw_worker_demographics` keyed by employee, or add a synthetic cohort field to workers; do not expose personally identifying attributes in the semantic layer. Add governed metrics for unadjusted base-pay gap, adjusted comp-ratio gap, cohort size, and disparity trend. Cortex Analyst produces reproducible cohort comparisons; Cortex `COMPLETE` can explain drivers only after deterministic SQL establishes the facts. | **Guardrails/graceful fallback:** suppress cohorts below a minimum-k threshold (for example, five people), avoid employee-level output, and clearly label insufficient-sample results.<br>**Scheduled automation:** Snowflake Task checks department/band drift and sends a Slack alert when a defined threshold is exceeded. | **3–4 h** | **9.2 / 10** |
| **3** | **Promotion Calibration Copilot**<br>**Domain:** Leveling, promotion equity, and talent progression | Calibration committees must distinguish evidence-backed promotion cases from inflated ratings and subjective manager narratives. They also need consistent tenure-in-band, performance, and budget rules across departments. | **New table:** `raw_promotion_nominations` with employee, current/target band, nomination date, months in band, justification, cycle, and status. Add metrics for nomination rate, promotion velocity, in-band tenure, and out-of-cycle nominations. Cortex Search indexes nomination justifications and historical review text; Cortex Analyst verifies objective eligibility. Keep both outputs separate before synthesis to prevent narrative text from overriding policy rules. | **Multi-agent orchestration:** quantitative eligibility agent + qualitative evidence agent + synthesis agent producing an evidence scorecard.<br>**MCP connector:** post a structured, cited summary to a calibration Slack channel; require human approval before any HRIS action. | **5–7 h** | **8.8 / 10** |
| **4** | **Requisition SLA & Hiring Velocity Engine**<br>**Domain:** Talent acquisition and workforce delivery | Recruiting reports time-to-fill from job posting, while business leaders experience the full vacancy clock from approved budget to accepted offer. Separating approval delay, posting delay, interview delay, and offer delay identifies the accountable bottleneck and the cost of vacancy. | **New tables:** `raw_requisitions` for approval/posting/target/closure dates and `raw_candidate_stages` or `raw_interview_feedback` for stage events and notes. A dynamic table calculates stage aging and SLA breaches. The Semantic View governs recruiter time-to-fill, enterprise vacancy duration, stage conversion, and aging requisitions. Cortex Search retrieves interview feedback to identify recurring bottlenecks; Cortex Analyst answers cross-functional pipeline questions. | **MCP connector:** create a Jira escalation or Slack notification for stalled requisitions, with deduplication and a dry-run mode.<br>**Reusable/shareable skill:** package an `audit-hiring-sla` CoCo skill that works against any similarly mapped ATS schema.<br>**Scheduled automation:** daily aging scan. | **5–7 h** | **8.5 / 10** |
| **5** | **Strategic Skills & Reskilling Navigator**<br>**Domain:** Learning & development and workforce planning | During a technology shift, leadership may authorize expensive external hiring without knowing which current employees have adjacent skills and could be reskilled faster. This connects L&D spend to internal mobility, hiring avoidance, and strategic capacity planning. | **New tables:** `raw_employee_skills` with proficiency and recency, plus `raw_learning_courses` with completion and domain; optionally a `target_role_skill_requirements` table. Govern skill coverage, recency-weighted readiness, internal mobility pool, course completion, and estimated recruiting-cost avoidance. Cortex Analyst answers skill-gap and candidate-pool questions; Cortex `COMPLETE` generates a constrained 90-day plan from explicitly identified gaps, with source courses and confidence labels. Cortex Search can index course descriptions or learning content. | **Custom function-calling tool:** `generate_reskilling_plan(target_role, employee_id)` with an allow-listed role catalog and no automatic HR action.<br>**Scheduled automation:** monthly strategic skill-gap scan.<br>**Solution completeness:** links analytics to a concrete development action and measurable cost-avoidance hypothesis. | **5–7 h** | **8.1 / 10** |

## Recommended build order

1. **Org Health & Span-of-Control Sentinel** — highest return because it reuses the existing
   hierarchy and requires no new source tables.
2. **Promotion Calibration Copilot** — best showcase of Analyst + Search + multi-agent
   orchestration, but budget more than a minimal demo estimate for testing and handoff logic.
3. **Pay Equity Auditor** — strongest governance and privacy story; add it if the demo needs a
   defensible enterprise guardrail.
4. **Requisition SLA Engine** — strongest external-tool/MCP story and an easy scheduled-run
   narrative.
5. **Skills & Reskilling Navigator** — strongest L&D/workforce-planning expansion and
   action-oriented close loop.

## Architecture and judging notes

- Keep canonical metrics in the Semantic View and expose them through Cortex Analyst; do not
  let an LLM calculate headcount, pay gaps, eligibility, or SLA durations from prose.
- Avoid fan-out errors when joining one-to-many reviews, nominations, skills, or candidate
  events. Use pre-aggregated dynamic tables or explicit grain declarations before adding
  metrics to the shared Semantic View.
- Synthetic data should include deliberately conflicting naive definitions so the demo shows
  governance resolving a real disagreement, not only a dashboard producing numbers.
- Every action connector should support preview/dry-run, allow-listed targets, structured
  payloads, idempotency keys, and human approval for consequential HR actions.
- Preserve citations for qualitative outputs and label generated recommendations as
  recommendations, not employment decisions. The deterministic evidence query remains the
  system of record.
