"""
Export a dated snapshot of governed numbers from Snowflake for the static landing page.

The landing page is a static file and can't query Snowflake. The first sections compute their
numbers in the browser from the committed synthetic dataset; everything that depends on a
Snowflake-side computation (semantic-view metrics, Cortex sentiment/classification, the band and
pay-equity tables, the regression suite) comes from this snapshot, labelled with its export date.

Usage (key-pair connection, no browser):
    uv run --no-project --with snowflake-connector-python python scripts/export_site_snapshot.py
Writes site/snapshot.js.
"""
from __future__ import annotations

import datetime as dt
import decimal
import json
from pathlib import Path

import snowflake.connector

DB = "WORKFORCE_ASTRA.RAW"
OUT = Path(__file__).resolve().parent.parent / "site" / "snapshot.js"


def rows(cur, sql):
    cur.execute(sql)
    cols = [c[0].lower() for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def one(cur, sql):
    r = rows(cur, sql)
    return r[0] if r else {}


def to_json(o):
    if isinstance(o, decimal.Decimal):
        return float(o)
    if isinstance(o, (dt.datetime, dt.date)):
        return o.isoformat()
    raise TypeError(type(o))


def main():
    conn = snowflake.connector.connect(connection_name="workforce-astra-keypair")
    cur = conn.cursor()
    s = {}

    s["org"] = {
        "metrics": one(cur, f"""SELECT * FROM SEMANTIC_VIEW({DB}.ORG_HEALTH_360
            METRICS org.manager_count, org.avg_span_of_control, org.overspan_managers,
                    org.narrow_span_managers, org.max_org_depth)"""),
        "widest_spans": rows(cur, f"""SELECT employee_id, department_code, band_code,
                direct_reports, subtree_size, is_overspan
            FROM {DB}.RAW_ORG_FLATTENED WHERE is_manager
            ORDER BY direct_reports DESC, employee_id LIMIT 8"""),
    }

    s["pay_equity"] = {
        "metrics": one(cur, f"""SELECT * FROM SEMANTIC_VIEW({DB}.PAY_EQUITY_360
            METRICS pe.fte_headcount, pe.unadjusted_gap_pct, pe.adjusted_gap_pct)"""),
        # Aggregates only; pay figures are already NULL for suppressed cohorts (n < 5).
        "cohorts": rows(cur, f"""SELECT department_code, band_code, gender_cohort, cohort_size,
                is_suppressed, avg_comp_ratio_safe
            FROM {DB}.PAY_EQUITY_COHORTS
            ORDER BY is_suppressed, department_code, band_code, gender_cohort"""),
    }

    s["voice"] = {
        "metrics": one(cur, f"""SELECT * FROM SEMANTIC_VIEW({DB}.EMPLOYEE_VOICE_360
            METRICS voice.transcript_count, voice.exit_transcript_count,
                    voice.stay_transcript_count, voice.negative_transcript_count,
                    voice.multi_reason_transcript_count, voice.flight_risk_signal_count,
                    voice.avg_sentiment)"""),
        "reasons_primary": rows(cur, f"""SELECT primary_reason AS reason, COUNT(*) AS n
            FROM {DB}.VOICE_THEME_RESULTS GROUP BY 1 ORDER BY 2 DESC, 1"""),
        "reasons_any": rows(cur, f"""SELECT reason, COUNT(*) AS n FROM (
                SELECT primary_reason AS reason FROM {DB}.VOICE_THEME_RESULTS
                UNION ALL
                SELECT secondary_reason FROM {DB}.VOICE_THEME_RESULTS
                WHERE secondary_reason IS NOT NULL)
            GROUP BY 1 ORDER BY 2 DESC, 1"""),
        "corroborated": rows(cur, f"""SELECT employee_id, interview_type, sentiment_score,
                primary_reason, secondary_reason, comp_ratio, rating_score,
                transcript_text, review_text
            FROM {DB}.VOICE_RISK_360 WHERE corroborated_flight_risk
            ORDER BY sentiment_score, employee_id"""),
    }

    s["band"] = {
        "metrics": one(cur, f"""SELECT * FROM SEMANTIC_VIEW({DB}.BAND_HEALTH_360
            METRICS band.total_headcount, band.red_circle_count, band.below_range_count,
                    band.in_floor_cluster_count, band.below_range_rate)"""),
        "by_band": rows(cur, f"""SELECT band_code, headcount, below_range_count, red_circle_count,
                in_floor_cluster_count, avg_range_penetration, compression_ratio
            FROM {DB}.BAND_RANGE_HEALTH ORDER BY band_code"""),
        "overlap": rows(cur, f"""SELECT lower_band, upper_band, overlap_index
            FROM {DB}.BAND_RANGE_OVERLAP ORDER BY overlap_index DESC"""),
    }

    s["governance"] = {
        "tests": rows(cur, f"""SELECT r.test_id, r.metric_name, r.status, g.model_dependent
            FROM {DB}.METRIC_TEST_RESULTS r
            LEFT JOIN {DB}.METRIC_REGISTRY g ON g.metric_name = r.metric_name
            QUALIFY ROW_NUMBER() OVER (PARTITION BY r.test_id ORDER BY r.checked_at DESC) = 1
            ORDER BY r.test_id"""),
        "registry_size": one(cur, f"SELECT COUNT(*) AS n, COUNT_IF(owner_role IS NULL OR owner_role = '') AS unowned FROM {DB}.METRIC_REGISTRY"),
        "alerts": rows(cur, f"""SELECT alert_type, severity, detail, created_at
            FROM {DB}.GOVERNANCE_ALERTS ORDER BY created_at DESC LIMIT 3"""),
        "tasks": rows(cur, f"SHOW TASKS IN SCHEMA {DB}"),
    }
    s["governance"]["tasks"] = [
        {"name": t["name"], "schedule": t["schedule"], "state": t["state"]}
        for t in s["governance"]["tasks"]
    ]

    s["exported_at"] = dt.datetime.now().strftime("%d-%b-%Y")
    conn.close()

    OUT.write_text("const WORKFORCE_SNAPSHOT = " + json.dumps(s, default=to_json, indent=1) + ";\n",
                   encoding="utf-8")

    t = s["governance"]["tests"]
    print(f"wrote {OUT}")
    print("org:", s["org"]["metrics"])
    print("pay equity:", s["pay_equity"]["metrics"], "| cohorts:", len(s["pay_equity"]["cohorts"]),
          "suppressed:", sum(1 for c in s["pay_equity"]["cohorts"] if c["is_suppressed"]))
    print("voice:", s["voice"]["metrics"])
    print("  primary reasons:", [(r["reason"], r["n"]) for r in s["voice"]["reasons_primary"]])
    print("  any-label reasons:", [(r["reason"], r["n"]) for r in s["voice"]["reasons_any"]])
    print("  corroborated rows:", len(s["voice"]["corroborated"]))
    print("band:", s["band"]["metrics"])
    print("  overlap:", [(o["lower_band"], o["upper_band"], o["overlap_index"]) for o in s["band"]["overlap"]])
    print("tests:", sum(1 for x in t if x["status"] == "PASS"), "/", len(t), "pass;",
          "model-dependent:", sum(1 for x in t if x["model_dependent"]))
    print("registry:", s["governance"]["registry_size"], "| tasks:", s["governance"]["tasks"])


if __name__ == "__main__":
    main()
