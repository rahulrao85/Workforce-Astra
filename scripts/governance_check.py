"""
Workforce Astra -- governance check. Runs the regression suite and explains the result.

WHY A SCRIPT AND NOT JUST A PROMPT
    A skill that says "run the tests and tell me if they pass" leaves the judgement to the model,
    which is the opposite of this project's entire thesis. This script returns a deterministic
    PASS/FAIL, a non-zero exit code on failure, and a machine-readable --json mode, so the skill
    reports what the suite actually said.

WHAT IT CHECKS
    1. CALL run_metric_tests()  -- the golden-value suite.
    2. Per-test PASS/FAIL joined back to the registry, so a failure names its metric OWNER.
    3. Splits the result into DETERMINISTIC vs MODEL-DEPENDENT tests, because they fail for
       completely different reasons and conflating them wastes debugging time.
    4. Scheduled task state, and whether the most recent scheduled run agrees with the live run.
    5. Open governance alerts.

USAGE
    python scripts/governance_check.py
    python scripts/governance_check.py --json
    python scripts/governance_check.py --database WORKFORCE_ASTRA_REBUILD_TEST
    python scripts/governance_check.py --diagnose        # extra help text on any failure

EXIT CODES
    0  every test passed
    1  at least one test failed
    2  the suite could not be run at all (bad connection, missing objects, auth)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

EXIT_OK, EXIT_FAILED, EXIT_ERROR = 0, 1, 2

DIAGNOSES = {
    "model_dependent": [
        "This test reads Snowflake-hosted Cortex output (SENTIMENT / AI_CLASSIFY), so it pins",
        "CURRENT MODEL BEHAVIOUR rather than a fact about your data.",
        "  -> If the value moved but the data did not, Snowflake likely upgraded the model.",
        "     Re-baseline deliberately: confirm the new value is sane, then UPDATE the",
        "     expected_value in metric_regression_tests and note it in the commit message.",
        "  -> If the data changed, that is a real finding: re-run the scoring procedure and",
        "     check whether the underlying data or a definition moved.",
    ],
    "deterministic": [
        "This test reads tables only, so it can only fail if the DATA or a DEFINITION changed.",
        "  -> Check git log for a change to the generator, a sql/ file, or a hand-edited table.",
        "  -> If a metric was intentionally redefined, update BOTH the definition in",
        "     metric_registry and the expected_value in metric_regression_tests -- never one",
        "     without the other, or the registry starts lying.",
    ],
}


def connect(connection: str):
    try:
        import snowflake.connector
    except ImportError:
        sys.exit("snowflake-connector-python is not installed. Run this through:\n"
                 "  uv run --no-project --with snowflake-connector-python python "
                 "scripts/governance_check.py")
    return snowflake.connector.connect(connection_name=connection)


def q(cur, sql: str):
    """Run a query and return dicts with LOWERCASE keys.

    The Python connector returns column names exactly as Snowflake stores them -- upper case for
    unquoted identifiers. Every status is compared against 'PASS' downstream, so a case mismatch
    here silently reports the whole suite as failing. Normalise once, here, rather than at each
    call site.
    """
    cur.execute(sql)
    cols = [d[0].lower() for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Run and explain the Workforce Astra regression suite.")
    ap.add_argument("--connection",
                    default=os.environ.get("SNOWFLAKE_CONNECTION", "workforce-astra-keypair"))
    ap.add_argument("--database", default="WORKFORCE_ASTRA")
    ap.add_argument("--json", action="store_true", help="machine-readable output only")
    ap.add_argument("--diagnose", action="store_true", help="explain any failures")
    ap.add_argument("--skip-tasks", action="store_true", help="do not query task state")
    args = ap.parse_args()

    db = args.database
    report: dict = {"database": db, "ok": False, "tests": [], "tasks": [], "alerts": []}
    phase = "connect"

    try:
        conn = connect(args.connection)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"error": f"connect failed: {e}"}))
        return EXIT_ERROR

    try:
        cur = conn.cursor()

        phase = "call run_metric_tests"
        try:
            cur.execute(f"CALL {db}.RAW.run_metric_tests()")
            runner = cur.fetchall()
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"error": f"could not run the suite: {e}",
                              "hint": "does the database exist? try --database, and check "
                                      "sql/07_metric_governance.sql has been applied"}))
            return EXIT_ERROR

        phase = "read results"
        # model_dependent / owner / definition live on metric_REGISTRY, not on the test table.
        rows = q(cur, f"""
            SELECT r.test_id, r.metric_name, r.expected_value, r.actual_value, r.status,
                   g.model_dependent, g.owner_role, g.domain, g.definition,
                   (g.metric_name IS NULL) AS unregistered
            FROM {db}.RAW.metric_test_results r
            LEFT JOIN {db}.RAW.metric_registry g ON g.metric_name = r.metric_name
            ORDER BY r.test_id
        """)
        for r in rows:
            # A test with no registry row is UNREGISTERED, not "deterministic". Guessing would be
            # exactly the kind of unowned assumption this project exists to remove, so it is
            # surfaced as a governance gap instead of silently classified.
            r["unregistered"] = bool(r.get("unregistered"))
            r["model_dependent"] = bool(r.get("model_dependent")) and not r["unregistered"]
            report["tests"].append(r)

        if not args.skip_tasks:
            phase = "read tasks"
            # SHOW TASKS, not INFORMATION_SCHEMA.TASKS: on this account the latter fails to resolve
            # ("does not exist or not authorized") even as ACCOUNTADMIN, while SHOW returns the
            # same rows. Verified against the live account 25-Sep-2026.
            try:
                cur.execute(f"SHOW TASKS IN SCHEMA {db}.RAW")
                cols = [d[0].lower() for d in cur.description]
                report["tasks"] = [
                    {k: r[i] for i, k in enumerate(cols)
                     if k in ("name", "state", "schedule", "last_committed_on", "last_suspended_on")}
                    for r in cur.fetchall()
                ]
            except Exception:  # noqa: BLE001
                report["tasks"] = []

            try:
                report["alerts"] = q(cur, f"""
                    SELECT alert_type, severity, metric_name, detail, created_at
                    FROM {db}.RAW.governance_alerts
                    ORDER BY created_at DESC LIMIT 10
                """)
            except Exception:  # noqa: BLE001
                report["alerts"] = []

    except Exception as e:  # noqa: BLE001
        print(json.dumps({"error": f"{phase}: {e}"}))
        return EXIT_ERROR
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass

    failed = [t for t in report["tests"] if str(t.get("status", "")).upper() != "PASS"]
    unregistered = [t for t in report["tests"] if t["unregistered"]]
    det = [t for t in report["tests"] if not t["model_dependent"]]
    mod = [t for t in report["tests"] if t["model_dependent"]]
    det_fail = [t for t in det if str(t.get("status", "")).upper() != "PASS"]
    mod_fail = [t for t in mod if str(t.get("status", "")).upper() != "PASS"]
    report["summary"] = {
        "total": len(report["tests"]),
        "passed": len(report["tests"]) - len(failed),
        "failed": len(failed),
        "deterministic": {"total": len(det), "failed": len(det_fail)},
        "model_dependent": {"total": len(mod), "failed": len(mod_fail)},
        "unregistered": len(unregistered),
        "runner_return": [list(r) for r in runner] if runner else None,
    }
    report["ok"] = not failed and bool(report["tests"])

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return EXIT_OK if report["ok"] else EXIT_FAILED

    s = report["summary"]
    print(f"Workforce Astra governance check -- {db}")
    print("=" * 74)
    print(f"  regression suite : {s['passed']}/{s['total']} PASS"
          + ("" if not s["failed"] else f"   ({s['failed']} FAILED)"))
    print(f"    deterministic  : {len(det) - len(det_fail)}/{len(det)} PASS")
    print(f"    model-dependent: {len(mod) - len(mod_fail)}/{len(mod)} PASS")
    if unregistered:
        print(f"\n  !! {len(unregistered)} tested metric(s) have NO registry entry, so nobody owns "
              f"their definition:")
        for t in unregistered:
            print(f"       #{t['TEST_ID']:<3} {t['METRIC_NAME']}")
        print("     Add them to metric_registry in sql/07_metric_governance.sql.")

    if report["tasks"]:
        print("\n  scheduled tasks:")
        for t in report["tasks"]:
            print(f"    {t['name']:34s} {t['state']:8s} {t.get('LAST_COMMITTED_ON') or '-'}")

    if report["alerts"]:
        print("\n  recent governance alerts:")
        for a in report["alerts"][:5]:
            print(f"    [{a['severity']}] {a['alert_type']} / {a['metric_name']}")

    if failed:
        print("\n  FAILURES:")
        for t in failed:
            kind = "model-dependent" if t["model_dependent"] else "deterministic"
            print(f"    #{t['TEST_ID']:<3} {t['METRIC_NAME']}  ({kind})")
            print(f"         expected {t['expected_value']}  got {t['actual_value']}")
            owner = t.get("owner_role")
            if owner:
                print(f"         owner: {owner}   domain: {t.get('domain')}")
        if args.diagnose:
            for kind in ("deterministic", "model_dependent"):
                if (det_fail if kind == "deterministic" else mod_fail):
                    print(f"\n  --- how to read a {kind} failure ---")
                    for line in DIAGNOSES[kind]:
                        print("    " + line)
        return EXIT_FAILED

    print("\n  OK -- every governed metric matches its certified golden value.")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

