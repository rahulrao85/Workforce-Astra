---
name: workforce-astra-governance-check
description: Run and explain the Workforce Astra metric regression suite, the metric-definition registry, the scheduled governance tasks and the open governance alerts. Use when asked to check metric health, run the tests, verify nothing drifted, audit which team owns a metric, confirm the demo numbers still hold, or before recording/re-submitting. Also use when a governed number looks wrong and you need to know whether the data changed or the definition did.
tools:
- bash
- read
- sql_execute
- snowflake_sql_execute
---

# When to Use

- "Run the regression suite" / "check metric health" / "did anything drift?"
- "Which team owns this metric?" / "is that number governed?"
- Before recording the demo or re-submitting — confirm the headline numbers still hold
- A governed number looks wrong and you need to know whether the **data** moved or the
  **definition** moved
- After changing anything in `sql/` — the suite is the gate, not a report

# What This Skill Provides

A deterministic PASS/FAIL with a non-zero exit code, not a vibe. Concretely:

| Output | Why it matters |
|---|---|
| `25/25 PASS`, split into deterministic vs model-dependent | A failure tells you *which kind* of problem you have, which is most of the debugging |
| The failing metric's **owner role** and definition | Stops "whose number is this?" — the exact argument this project exists to end |
| Scheduled task state | A `suspended` task means the suite is not actually protecting anything |
| Open governance alerts | Shows what the schedulers have flagged that nobody has actioned |
| A list of tested metrics with **no registry entry** | An unowned metric is a governance hole even when the test passes |

# Instructions

## 1. Run it

From the project root (`hackathons/Snowflake-Workforce-Astra/`):

```bash
uv run --no-project --with snowflake-connector-python python scripts/governance_check.py
```

`--json` for machine-readable output, `--diagnose` to add remediation guidance on failure,
`--database NAME` to point at a rebuilt copy, `--skip-tasks` to avoid the `SHOW TASKS` call.

Exit codes: **0** all pass · **1** at least one test failed · **2** the suite could not run at all
(bad connection, missing objects). Treat 2 as "not verified" and say so — never report it as a pass.

## 2. Report the result, do not editorialise

State: total passed/total, the deterministic vs model-dependent split, task state, and any open
alerts. If something failed, name the metric, the expected and actual values, and the owner role.
Do not round a failure into a pass, and do not describe 25/25 as "all metrics healthy" — say
what was checked.

## 3. If tests fail, classify before fixing

This is the part that matters. **A model-dependent failure is usually not a bug.**

- **Deterministic** (reads tables) — the data or a definition changed. Check `git log` for a
  generator or `sql/` change. If a metric was *intentionally* redefined, update
  `metric_registry.definition` **and** `metric_regression_tests.expected_value` together — never one
  without the other, or the registry starts lying about what the number means.
- **Model-dependent** (tests 8–17, reads Cortex `SENTIMENT`/`AI_CLASSIFY` output) — Snowflake may
  have upgraded the model. Confirm the new value is sane, then re-baseline deliberately and say in
  the commit message that you did. Never silently "fix" a model-dependent test by pasting in
  whatever number came back; that is how a regression suite quietly stops being one.

# Adapting this skill to another project

This is the reusable part. To point it at a different Snowflake project you need only:

1. `run_metric_tests()` — a procedure returning `{passed, failed}`
2. `metric_test_results(test_id, metric_name, expected_value, actual_value, status)`
3. `metric_registry(metric_name, owner_role, definition, model_dependent)`

Change the two table names and the `CALL` in `scripts/governance_check.py`; nothing else is
Workforce-Astra-specific. The deterministic/model-dependent split and the unregistered-metric check
are the parts worth keeping in any port — they are what turn a test runner into a governance tool.

# Best Practices

- The suite is a **gate**, not a report. After any `sql/` change, run it before claiming anything
  works. `run_metric_tests()` is also called by the `METRIC_REGRESSION_DAILY` task, so a failure
  you never ran still shows up in the registry the next morning.
- If `scripts/governance_check.py` reports unregistered metrics, **fix the registry, not the
  script.** The gap is the finding.
- The voice metrics (8–17) depend on Snowflake-hosted models. If they fail after a Snowflake
  release, re-baseline rather than hunting for a data bug that isn't there.
- Prefer `scripts/governance_check.py` over hand-writing the `SELECT`. The hand-written version
  loses the owner join and the model-dependent split, which are the two things that make a failure
  actionable.
- This account's `INFORMATION_SCHEMA.TASKS` does not resolve even as `ACCOUNTADMIN`; the script uses
  `SHOW TASKS` for that reason. Don't "fix" it back.

# Common Patterns

### Pattern 1: pre-recording gate

```bash
uv run --no-project --with snowflake-connector-python python scripts/governance_check.py
```

If exit code is 0, the demo numbers in `DEMO_SCRIPT.md` are the ones currently live. If not, do not
record over a mismatch.

### Pattern 2: who owns this number?

```sql
SELECT metric_name, owner_role, domain, definition, certified, model_dependent
FROM WORKFORCE_ASTRA.RAW.metric_registry
WHERE metric_name ILIKE '%comp_ratio%';
```

### Pattern 3: what has the schedulers been shouting about?

```sql
SELECT alert_type, severity, metric_name, detail, created_at
FROM WORKFORCE_ASTRA.RAW.governance_alerts
ORDER BY created_at DESC;
```

### Pattern 4: confirm a rebuilt copy is equivalent

```bash
uv run --no-project --with snowflake-connector-python python scripts/governance_check.py \
  --database WORKFORCE_ASTRA_REBUILD_TEST
```

Same 25/25 in a fresh database is the evidence that the rebuild is faithful.

# Known Characteristics (deliberate, not bugs)

- **The suite passes with three HIGH alerts open.** A HIGH `PAY_EQUITY_DRIFT` and a HIGH
  `BAND_ARCHITECTURE` alert are *correct*: the adjusted pay gap genuinely exceeds its 2% threshold,
  and 37 employees genuinely sit below their band minimum. Tests assert the current state is
  faithfully reported; the alerts are the schedulers correctly escalating real problems, not
  test failures.
- `last_committed_on` can be empty for a task that is `started` but has not completed a run since
  the last suspend. `started` is the state that matters for "is the schedule armed".
- `red_circle_count` is genuinely **0** and has a golden-value test asserting 0. The band auditor's
  real finding is the mirror image — 37 people *below* range minimum.

# Examples

## Example 1: routine check

User: `$workforce-astra-governance-check run the tests`

Assistant: runs the script, reports `25/25 PASS (15 deterministic, 10 model-dependent)`, three
tasks `started`, and the open alerts — noting the HIGH alerts are real findings, not failures.

## Example 2: a number looks wrong

User: `headcount says 112, the README says 109 — what happened?`

Assistant: runs the script. If the suite is green, the *data* is fine and the 112 came from an
ungoverned query, so compare it against `SELECT headcount FROM SEMANTIC_VIEW(... METRICS
workers.headcount)`. If `governed_headcount` itself is failing, the script names the expected and
actual value, marks it deterministic, and points at `git log` for what changed.
