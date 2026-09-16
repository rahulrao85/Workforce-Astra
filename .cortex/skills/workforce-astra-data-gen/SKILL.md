---
name: workforce-astra-data-gen
description: Generate the Workforce Astra synthetic HR dataset (workers, compensation bands, performance reviews) and load it into Snowflake WORKFORCE_ASTRA.RAW. Use when asked to generate, regenerate, seed, reset, or reload the Employee 360 demo data; to prove the governed-vs-naive headcount conflict; or to check why headcount numbers disagree.
tools:
- bash
- read
- write
- sql_execute
- snowflake_sql_execute
---

# When to Use

- "Generate the Workforce Astra data" / "seed the demo" / "reload the Employee 360 tables"
- "Show me the governed vs naive headcount difference" / "prove the FTE-vs-contractor conflict"
- Anything that needs `WORKFORCE_ASTRA.RAW` populated before a semantic-view or Cortex Analyst question

# What This Skill Provides

Three referentially-consistent tables loaded with **deliberately conflicting governance** baked in:

| Table | Rows | Role |
|---|---|---|
| `raw_compensation_bands` | 5 | band min / mid / max for IC3-IC5, M1-M2 |
| `raw_workday_workers` | 150 | employee master; carries `employment_type` (FTE vs Contractor) -- the governance lever |
| `raw_performance_reviews` | 127 | active-employee reviews; unstructured `review_text` feeds Cortex Search |

The load-bearing property: **a naive `COUNT(*)` of active workers and the governed FTE-only count must return different numbers.** That difference is the entire demo thesis -- the same question answered differently because nobody owns the definition of "employee."

# Instructions

## 1. Run the pipeline

From the project root (`hackathons/Snowflake-Workforce-Astra/`):

```bash
python scripts/load_workforce_data.py
```

This regenerates the CSVs, runs the invariant checks, stages copies in a space-free
directory (required: the workspace path contains a space, which breaks `PUT file://`),
and prints the `PUT` + `COPY INTO` SQL.

Then execute the printed SQL with the `sql_execute` tool. Alternatively, if the
Snowflake CLI is on PATH:

```bash
python scripts/load_workforce_data.py --run     # generates, verifies, and executes
```

Tables are loaded in dependency order: bands -> workers -> reviews. Each table is
`TRUNCATE`d then copied with `FORCE = TRUE` so re-running the demo actually reloads
instead of silently skipping already-loaded files.

## 2. Confirm the load

Expect these row counts:

```
raw_compensation_bands   5
raw_workday_workers      150
raw_performance_reviews  127
```

Run `sql/01_create_tables.sql` first if the database does not exist yet.

## 3. Assert the proof point -- do not skip this

```sql
SELECT COUNT(*) AS naive_active_headcount,
       COUNT_IF(employment_type = 'FTE') AS governed_active_headcount,
       COUNT(*) - COUNT_IF(employment_type = 'FTE') AS delta
FROM raw_workday_workers
WHERE employee_status = 'Active';
```

Expected: naive `127` > governed `109`, `delta = 18`.
If `delta = 0`, the dataset is wrong -- regenerate before continuing.

# Best Practices

- The generator is seeded (`random.seed(7)`, `Faker.seed(7)`), so output is byte-stable.
  Regenerating is free and safe; do it rather than hand-editing CSVs.
- `--verify` is a hard gate, not a report. It exits non-zero when the conflict
  disappears, a termination lands in the future, or a report points at a
  missing/terminated/contractor manager. Never proceed on a failed verify.
- Never edit the generated CSVs to "fix" the conflict. If the deltas look wrong,
  change the generator and regenerate.
- Do not load with `MATCH_BY_COLUMN_NAME` against `raw_performance_reviews`; the
  column order in the CSV already matches the DDL.

# Common Patterns

### Pattern 1: full reset before recording

```bash
python scripts/load_workforce_data.py --run
```

### Pattern 2: SQL only (already generated, just re-emitting)

```bash
python scripts/load_workforce_data.py --sql-only
```

### Pattern 3: diagnose an unexpected headcount

```sql
SELECT employment_type, employee_status, COUNT(*) AS n
FROM raw_workday_workers
GROUP BY 1, 2
ORDER BY 1, 2;
```

# Known Data Characteristics (deliberate, not bugs)

- `base_pay` is drawn from 0.75-1.15x the band midpoint while the band spans
  0.85-1.20x, so some employees sit **below band minimum**. That is intentional: it
  makes `comp_ratio < 0.85` a real underpaid-flight-risk signal instead of a
  condition that can never fire.
- Managers (`EMP-0001`..`EMP-0015`) are always active FTEs, so
  `manager_slack_id` never points at a departed employee or a contractor.
- Reviews exist for active employees only, so there is no "poor review -> departed"
  narrative available in this dataset.
- Flight-risk language ("raised a competing offer", "interviewing externally", "pay feels
  out of step with market") is attached to roughly half of the **underpaid high performers**
  -- i.e. employees who satisfy `comp_ratio < 0.85 AND rating >= 4`. That alignment is what
  makes the Cortex Search evidence step coherent: the cited snippet actually explains the
  flag. `--verify` fails if fewer than 3 such candidates exist, so this cannot silently
  regress. Expect ~15 notifiable candidates, of whom ~30 are flagged in total.
- `termination_date` is never in the future.

# Examples

## Example 1: basic usage

User: `$workforce-astra-data-gen load the demo data`

Assistant: runs `python scripts/load_workforce_data.py`, executes the emitted SQL with
`sql_execute`, then reports row counts and the governed-vs-naive delta.

## Example 2: prove the conflict

User: `$workforce-astra-data-gen how many active employees do we have, and why does it differ?`

Assistant: runs the proof-point query, confirms naive (127) vs governed FTE (109), delta 18,
and explains the difference is `employment_type` -- contractors are counted by an
ungoverned query but excluded from the governed metric.
