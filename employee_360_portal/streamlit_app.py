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
st.caption("People Ops command center · Governed by the `employee_360` semantic view")
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
