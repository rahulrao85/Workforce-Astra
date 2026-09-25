import streamlit as st
import pandas as pd
import json
import os
from datetime import date

st.set_page_config(page_title="Workforce Astra - Employee 360", layout="wide")

try:
    conn = st.connection("snowflake")
except Exception as e:
    st.error(f"Failed to connect to Snowflake: {e}")
    st.stop()


def run_query(sql):
    try:
        return conn.query(sql)
    except Exception as e:
        st.error(f"Query failed: {e}\n\nSQL: {sql[:200]}")
        return pd.DataFrame()


# ── Section 1: Header ──────────────────────────────────────────────────────
st.title("Workforce Astra — Employee 360 Portal")
st.caption(
    "People Ops command center · Governed by four Snowflake semantic views — "
    "`employee_360`, `org_health_360`, `pay_equity_360`, `employee_voice_360`"
)
st.divider()

# ── Section 2: Ask the Governed Semantic View ──────────────────────────────
st.header("Ask the Governed Semantic View")
st.markdown(
    "Each button runs a **verified query** defined in the semantic view. "
    "The SQL and live result are shown side-by-side."
)

QUERIES = {
    "Governed Headcount (FTE only)": {
        "sql": """SELECT headcount FROM SEMANTIC_VIEW(
  employee_360
  METRICS workers.headcount
)""",
        "tag": "governed_headcount",
    },
    "Naive Headcount (all active)": {
        "sql": "SELECT COUNT(*) AS total_workers FROM WORKFORCE_ASTRA.RAW.RAW_WORKDAY_WORKERS WHERE employee_status = 'Active'",
        "tag": "naive_headcount_comparison",
    },
    "Attrition Rate (FTE, trailing 12 mo)": {
        "sql": """SELECT attrition_velocity FROM SEMANTIC_VIEW(
  employee_360
  METRICS workers.attrition_velocity
)""",
        "tag": "attrition_rate",
    },
    "Comp-Ratio by Department": {
        "sql": """SELECT department_code, comp_ratio FROM SEMANTIC_VIEW(
  employee_360
  DIMENSIONS workers.department_code
  METRICS workers.comp_ratio
) ORDER BY comp_ratio""",
        "tag": "comp_ratio_by_dept",
    },
}

col_gov, col_naive = st.columns(2)

with col_gov:
    if st.button("Governed Headcount (FTE only)", use_container_width=True):
        st.session_state["active_query"] = "Governed Headcount (FTE only)"
with col_naive:
    if st.button("Naive Headcount (all active)", use_container_width=True):
        st.session_state["active_query"] = "Naive Headcount (all active)"

col_att, col_comp = st.columns(2)
with col_att:
    if st.button("Attrition Rate (FTE, trailing 12 mo)", use_container_width=True):
        st.session_state["active_query"] = "Attrition Rate (FTE, trailing 12 mo)"
with col_comp:
    if st.button("Comp-Ratio by Department", use_container_width=True):
        st.session_state["active_query"] = "Comp-Ratio by Department"

# Side-by-side headcount comparison
if st.button("Compare: Governed vs Naive Headcount", type="primary", use_container_width=True):
    st.session_state["active_query"] = "__comparison__"

active = st.session_state.get("active_query")

if active == "__comparison__":
    c1, c2 = st.columns(2)
    gov_q = QUERIES["Governed Headcount (FTE only)"]
    naive_q = QUERIES["Naive Headcount (all active)"]
    with c1:
        st.subheader("Governed (FTE only)")
        st.code(gov_q["sql"], language="sql")
        df = run_query(gov_q["sql"])
        if not df.empty:
            st.metric("Governed Headcount", int(df.iloc[0, 0]))
    with c2:
        st.subheader("Naive (all active)")
        st.code(naive_q["sql"], language="sql")
        df = run_query(naive_q["sql"])
        if not df.empty:
            st.metric("Naive Headcount", int(df.iloc[0, 0]))
    st.info(
        "The governed metric counts only FTE employees. "
        "The naive count includes contractors and interns — this is the conflict "
        "the semantic view is designed to resolve."
    )

elif active and active in QUERIES:
    q = QUERIES[active]
    st.subheader(active)
    st.code(q["sql"], language="sql")
    df = run_query(q["sql"])
    if not df.empty:
        if len(df) == 1 and len(df.columns) == 1:
            val = df.iloc[0, 0]
            try:
                fval = float(val)
            except (TypeError, ValueError):
                fval = None
            if isinstance(fval, float) and fval < 1:
                st.metric(active, f"{fval:.2%}")
            else:
                st.metric(active, val)
        else:
            st.dataframe(df, use_container_width=True)

st.divider()

# ── Section 3: Employee Directory ──────────────────────────────────────────
st.header("Employee Directory")

dir_sql = """
SELECT w.employee_id, w.first_name, w.last_name,
       w.department_code AS department, w.band_code AS band,
       w.employee_status AS status, w.employment_type,
       ROUND(w.base_pay / NULLIF(c.mid_point, 0), 2) AS comp_ratio
FROM WORKFORCE_ASTRA.RAW.RAW_WORKDAY_WORKERS w
JOIN WORKFORCE_ASTRA.RAW.RAW_COMPENSATION_BANDS c ON w.band_code = c.band_code
ORDER BY w.department_code, w.last_name
"""

dir_df = run_query(dir_sql)

if not dir_df.empty:
    dept_filter = st.multiselect(
        "Filter by department",
        options=sorted(dir_df["DEPARTMENT"].unique()),
        default=[],
    )
    status_filter = st.multiselect(
        "Filter by status",
        options=sorted(dir_df["STATUS"].unique()),
        default=[],
    )

    filtered = dir_df.copy()
    if dept_filter:
        filtered = filtered[filtered["DEPARTMENT"].isin(dept_filter)]
    if status_filter:
        filtered = filtered[filtered["STATUS"].isin(status_filter)]

    st.dataframe(filtered, use_container_width=True, height=400)
    st.caption(f"{len(filtered)} employees shown")

st.divider()

# ── Section 4: Flight-Risk Browser ─────────────────────────────────────────
st.header("Flight-Risk Browser")
st.markdown(
    "Employees with **comp-ratio < 0.85** and **performance rating ≥ 4** — "
    "high performers at risk of leaving due to below-market compensation."
)

flight_sql = """
SELECT w.employee_id, w.first_name, w.last_name,
       w.department_code AS department, w.band_code AS band,
       ROUND(w.base_pay / NULLIF(c.mid_point, 0), 2) AS comp_ratio,
       r.rating_score, r.review_id, r.review_text,
       w.manager_slack_id
FROM WORKFORCE_ASTRA.RAW.RAW_WORKDAY_WORKERS w
JOIN WORKFORCE_ASTRA.RAW.RAW_COMPENSATION_BANDS c ON w.band_code = c.band_code
JOIN WORKFORCE_ASTRA.RAW.RAW_PERFORMANCE_REVIEWS r ON w.employee_id = r.employee_id
WHERE w.employee_status = 'Active'
  AND (w.base_pay / NULLIF(c.mid_point, 0)) < 0.85
  AND r.rating_score >= 4
ORDER BY comp_ratio ASC
"""

flight_df = run_query(flight_sql)

if flight_df.empty:
    st.success("No flight-risk employees found.")
else:
    st.warning(f"{len(flight_df)} flight-risk employees identified")

    for _, row in flight_df.iterrows():
        emp_label = f"{row['FIRST_NAME']} {row['LAST_NAME']} ({row['EMPLOYEE_ID']})"
        with st.expander(
            f"⚠ {emp_label}  —  {row['DEPARTMENT']} · {row['BAND']} · "
            f"Comp {row['COMP_RATIO']} · Rating {row['RATING_SCORE']}"
        ):
            st.markdown(f"**Review text (review {row['REVIEW_ID']}):**")
            st.info(row["REVIEW_TEXT"])

            comp_ratio = float(row["COMP_RATIO"])
            rating = float(row["RATING_SCORE"])
            risk_score = round((1 - comp_ratio) * 0.6 + (rating / 5) * 0.4, 2)

            payload = {
                "manager_slack_id": row["MANAGER_SLACK_ID"] or "UNKNOWN",
                "employee_id": row["EMPLOYEE_ID"],
                "risk_score": risk_score,
                "evidence_snippet": (
                    f"[{row['REVIEW_ID']}] comp_ratio={comp_ratio}, "
                    f"rating={rating}. "
                    f'"{(row["REVIEW_TEXT"] or "")[:120]}"'
                ),
            }

            if st.button(f"Resolve — Draft Slack Alert", key=f"resolve_{row['EMPLOYEE_ID']}"):
                st.markdown("**Simulated `slack_notify_manager_flight_risk` payload:**")
                st.caption(
                    "This is a **simulated action** — no Slack message is sent. "
                    "The payload matches the MCP tool schema from MCP_TOOLS.md."
                )
                st.json(payload)

st.divider()

# ── Section 5: Org Health & Manager Health ─────────────────────────────────
st.header("Org Health & Manager Health")
st.markdown(
    "Span-of-control and org-design metrics governed by the `org_health_360` semantic view. "
    "Everyone gets the identical answer to *\"how many managers and how deep is the org?\"*"
)

org_metrics_sql = """
SELECT avg_span_of_control, overspan_managers, narrow_span_managers, manager_count, max_org_depth
FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.org_health_360
  METRICS org.avg_span_of_control, org.overspan_managers, org.narrow_span_managers,
          org.manager_count, org.max_org_depth)
"""
org_df = run_query(org_metrics_sql)
if not org_df.empty:
    r = org_df.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Managers", int(r["MANAGER_COUNT"]))
    c2.metric("Avg span of control", f"{float(r['AVG_SPAN_OF_CONTROL']):.1f}")
    c3.metric("Overspan managers (>10)", int(r["OVERSPAN_MANAGERS"]))
    c4.metric("Max org depth", int(r["MAX_ORG_DEPTH"]))

overspan_sql = """
SELECT m.employee_id AS manager_id, m.management_tier, m.department_code,
       m.direct_reports, m.subtree_size
FROM WORKFORCE_ASTRA.RAW.raw_org_flattened m
WHERE m.direct_reports > 8
ORDER BY m.direct_reports DESC
"""
overspan_df = run_query(overspan_sql)
if not overspan_df.empty:
    st.markdown("**Managers with the widest spans** (org-design bottlenecks):")
    st.dataframe(overspan_df, use_container_width=True)

st.caption(
    "Reorg changes can be dry-run through the guarded `simulate_reorg` custom tool, which "
    "rejects circular reporting lines and orphans and never mutates org data."
)

st.divider()

# ── Section 6: Pay Equity & Adverse-Impact Auditor ─────────────────────────
st.header("Pay Equity & Adverse-Impact Auditor")
st.markdown(
    "The board's *unadjusted* gap vs Legal's *band-adjusted* gap — both governed by "
    "`pay_equity_360`. Most of the raw gap disappears once band mix is held constant."
)

pe_sql = """
SELECT unadjusted_gap_pct, adjusted_gap_pct FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.pay_equity_360
  METRICS pe.unadjusted_gap_pct, pe.adjusted_gap_pct)
"""
pe_df = run_query(pe_sql)
if not pe_df.empty:
    r = pe_df.iloc[0]
    c1, c2 = st.columns(2)
    c1.metric("Unadjusted gap (women vs men)", f"{float(r['UNADJUSTED_GAP_PCT']):.2%}")
    c2.metric("Adjusted gap (band-normalised)", f"{float(r['ADJUSTED_GAP_PCT']):.2%}")
    st.info(
        "Governance resolution: the unadjusted figure reflects **band mix**, not like-for-like pay. "
        "The adjusted metric controls for band via comp-ratio, which is the number legal can defend."
    )

cohort_sql = """
SELECT department_code, band_code, gender_cohort, cohort_size, is_suppressed,
       privacy_note, avg_base_pay_safe, avg_comp_ratio_safe
FROM WORKFORCE_ASTRA.RAW.pay_equity_cohorts
ORDER BY department_code, band_code, gender_cohort
"""
cohort_df = run_query(cohort_sql)
if not cohort_df.empty:
    st.markdown("**Cohort view (k-anonymity enforced: cohorts below 5 are suppressed):**")
    st.dataframe(cohort_df, use_container_width=True, height=320)
    st.caption(
        "Guardrail: any cohort with fewer than 5 employees has its pay figures withheld (NULL) "
        "to prevent re-identification. Protected attributes are masked outside HR/ACCOUNTADMIN roles."
    )

st.divider()

# ── Section 7: Metric Governance & Regression Tests ────────────────────────
st.header("Metric Governance & Regression Tests")
st.markdown(
    "Every governed metric has an **owner**, a **certified definition**, and a **golden-value test** "
    "on a schedule. If a definition silently drifts, the suite fails — the layer that stops teams "
    "disagreeing again."
)

reg_sql = """
SELECT metric_name, domain, owner_role, certified, definition
FROM WORKFORCE_ASTRA.RAW.metric_registry
ORDER BY metric_id
"""
reg_df = run_query(reg_sql)
if not reg_df.empty:
    st.markdown("**Metric definition registry:**")
    st.dataframe(reg_df, use_container_width=True)

test_sql = """
SELECT test_id, metric_name, expected_value, actual_value, status, checked_at
FROM WORKFORCE_ASTRA.RAW.metric_test_results
ORDER BY test_id
"""
test_df = run_query(test_sql)
if not test_df.empty:
    passed = int((test_df["STATUS"] == "PASS").sum())
    total = len(test_df)
    if passed == total:
        st.success(f"Regression suite: {passed}/{total} PASS")
    else:
        st.error(f"Regression suite: {passed}/{total} PASS — definition drift detected")
    st.dataframe(test_df, use_container_width=True)
else:
    st.caption("No test run yet — the `metric_regression_daily` task populates this table.")

alert_sql = """
SELECT alert_type, severity, metric_name, detail, created_at
FROM WORKFORCE_ASTRA.RAW.governance_alerts
ORDER BY created_at DESC
LIMIT 10
"""
alert_df = run_query(alert_sql)
if not alert_df.empty:
    st.markdown("**Recent governance alerts:**")
    st.dataframe(alert_df, use_container_width=True)

st.caption(
    "Scheduled automations: `metric_regression_daily` (02:30 UTC) and "
    "`pay_equity_drift_weekly` (Mondays 03:00 UTC)."
)

st.divider()

# ── Section 8: Employee Voice — sentiment & reason classification ────────────
st.header("Employee Voice — Sentiment & Reason")
st.markdown(
    "Stay and exit interview transcripts, scored by a **Snowpark Python** stored procedure that "
    "runs `SNOWFLAKE.CORTEX.SENTIMENT` and `SNOWFLAKE.CORTEX.AI_CLASSIFY` inside Snowflake. "
    "The reason label set is fixed and governed — free-form labels would re-create exactly the "
    "problem this project exists to fix."
)

if st.button("Re-score all transcripts (runs the Snowpark procedure)", use_container_width=False):
    with st.spinner("Running score_voice_transcripts() …"):
        run_query("CALL WORKFORCE_ASTRA.RAW.score_voice_transcripts()")
    st.success("Re-scored. The table below is the fresh result of the procedure run.")

voice_metrics_sql = """
SELECT transcript_count, exit_transcript_count, stay_transcript_count,
       negative_transcript_count, multi_reason_transcript_count,
       flight_risk_signal_count, avg_sentiment
FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_voice_360
     METRICS voice.transcript_count, voice.exit_transcript_count,
             voice.stay_transcript_count, voice.negative_transcript_count,
             voice.multi_reason_transcript_count, voice.flight_risk_signal_count,
             voice.avg_sentiment)
"""
vm = run_query(voice_metrics_sql)
if not vm.empty:
    m = vm.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transcripts scored", int(m["TRANSCRIPT_COUNT"]))
    c2.metric("Exit / Stay", f"{int(m['EXIT_TRANSCRIPT_COUNT'])} / {int(m['STAY_TRANSCRIPT_COUNT'])}")
    c3.metric("Negative sentiment", int(m["NEGATIVE_TRANSCRIPT_COUNT"]))
    c4.metric("Flight-risk signals", int(m["FLIGHT_RISK_SIGNAL_COUNT"]))
    st.caption(
        f"Average sentiment {float(m['AVG_SENTIMENT']):+.3f} · "
        f"{int(m['MULTI_REASON_TRANSCRIPT_COUNT'])} interviews named more than one reason "
        "(multi-label classification, so the reasons are not forced into a single bucket)."
    )

reason_sql = """
SELECT primary_reason, transcript_count
FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_voice_360
     DIMENSIONS voice.primary_reason
     METRICS voice.transcript_count)
ORDER BY transcript_count DESC
"""
rdf = run_query(reason_sql)
if not rdf.empty:
    left, right = st.columns(2)
    with left:
        st.markdown("**Why people leave (classified primary reason):**")
        st.dataframe(rdf, use_container_width=True, height=300)
    with right:
        st.markdown("**Negative sentiment, by reason:**")
        neg_sql = """
        SELECT primary_reason, interview_type, avg_sentiment
        FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_voice_360
             DIMENSIONS voice.primary_reason, voice.interview_type
             METRICS voice.avg_sentiment)
        ORDER BY avg_sentiment ASC
        """
        ndf = run_query(neg_sql)
        if not ndf.empty:
            st.dataframe(ndf, use_container_width=True, height=300)

st.markdown("**The cross-signal: negative voice + structured flight risk in the same person**")
st.caption(
    "These are the rows that matter. An exit interview that reads negative *and* names a fixable "
    "reason (pay, manager, progression), landing on someone already underpaid and highly rated — "
    "the transcript explains the retention risk the structured metric only hinted at."
)
xb_sql = """
SELECT employee_id, department_code, primary_reason, secondary_reason,
       ROUND(sentiment_score, 3) AS sentiment_score, comp_ratio, rating_score,
       LEFT(review_text, 220) AS review_evidence, transcript_text
FROM WORKFORCE_ASTRA.RAW.voice_risk_360
WHERE corroborated_flight_risk
ORDER BY sentiment_score ASC
"""
xdf = run_query(xb_sql)
if not xdf.empty:
    st.dataframe(
        xdf.drop(columns=["TRANSCRIPT_TEXT"]),
        use_container_width=True,
    )
    for _, row in xdf.iterrows():
        with st.expander(f"{row['EMPLOYEE_ID']} — {row['PRIMARY_REASON']} (sentiment {row['SENTIMENT_SCORE']})"):
            st.markdown("**Exit interview, verbatim:**")
            st.write(row["TRANSCRIPT_TEXT"])
            st.markdown("**Corroborating performance review:**")
            st.write(row["REVIEW_EVIDENCE"])
            st.caption(
                f"comp-ratio {row['COMP_RATIO']} (below 0.85 = underpaid) · "
                f"rating {row['RATING_SCORE']} (4+ = strong performer) · "
                f"{row['DEPARTMENT_CODE']}"
            )
else:
    st.info("No corroborated flight-risk rows — no negative interview landed on an underpaid "
            "high performer in this dataset.")

st.divider()
