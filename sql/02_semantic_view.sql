-- Workforce Astra: governed Semantic View for Employee 360.
-- CONFIRMED LIVE 16-Sep-2026 -- created for real as WORKFORCE_ASTRA.RAW.EMPLOYEE_360
-- via CoCo CLI against account ST42987 (ap-southeast-7, AWS). Governed headcount
-- returned 109, naive comparison returned 127 -- the intended conflict, verified live.
-- Clause order is REQUIRED: TABLES -> RELATIONSHIPS -> FACTS -> DIMENSIONS -> METRICS
-- -> COMMENT/AI_VERIFIED_QUERIES.

CREATE OR REPLACE SEMANTIC VIEW employee_360
  TABLES (
    workers AS raw_workday_workers      PRIMARY KEY (employee_id) WITH SYNONYMS ('employees','headcount'),
    comp    AS raw_compensation_bands   PRIMARY KEY (band_code),
    reviews AS raw_performance_reviews  PRIMARY KEY (review_id)
  )
  RELATIONSHIPS (
    workers_to_comp    AS workers(band_code)   REFERENCES comp(band_code),
    reviews_to_workers AS reviews(employee_id) REFERENCES workers(employee_id)
  )
  FACTS (
    workers.base_pay      AS base_pay,
    comp.mid_point         AS mid_point,
    reviews.rating_score   AS rating_score,
    reviews.goals_met_pct  AS goals_met_pct
  )
  DIMENSIONS (
    workers.employee_id       AS employee_id,
    workers.department_code   AS department_code,
    workers.band_code         AS band_code,
    workers.employee_status   AS employee_status,
    workers.employment_type   AS employment_type,   -- the governance lever
    workers.hire_date         AS hire_date,
    workers.termination_date  AS termination_date
  )
  METRICS (
    -- Governed headcount: FTE only. A naive COUNT(*) without the employment_type
    -- filter is the "ungoverned" number the demo's cold open shows disagreeing.
    workers.headcount AS
      COUNT(DISTINCT CASE
        WHEN workers.employee_status = 'Active' AND workers.employment_type = 'FTE'
        THEN workers.employee_id
      END),

    workers.attrition_velocity AS
      COUNT(DISTINCT CASE
        WHEN workers.employee_status = 'Terminated'
         AND workers.employment_type = 'FTE'
         AND workers.termination_date >= DATEADD('year', -1, CURRENT_DATE())
        THEN workers.employee_id
      END)
      / NULLIF(COUNT(DISTINCT CASE WHEN workers.employment_type = 'FTE' THEN workers.employee_id END), 0),

    workers.comp_ratio AS AVG(workers.base_pay / NULLIF(comp.mid_point, 0))
  )
  COMMENT = 'Governed Employee 360 -- Workforce Astra MVP'
  AI_VERIFIED_QUERIES (
    governed_headcount AS (
      QUESTION 'How many active employees do we have?'
      SQL 'SELECT headcount FROM SEMANTIC_VIEW(
             employee_360
             METRICS workers.headcount
           )'
    ),
    attrition_rate AS (
      QUESTION 'What is our attrition rate this year?'
      SQL 'SELECT attrition_velocity FROM SEMANTIC_VIEW(
             employee_360
             METRICS workers.attrition_velocity
           )'
    ),
    comp_ratio_by_dept AS (
      QUESTION 'What is the comp-ratio for Engineering?'
      SQL 'SELECT comp_ratio FROM SEMANTIC_VIEW(
             employee_360
             DIMENSIONS workers.department_code
             METRICS workers.comp_ratio
           ) WHERE department_code = ''Engineering'''
    ),
    naive_headcount_comparison AS (
      QUESTION 'How many people work here including contractors?'
      SQL 'SELECT COUNT(*) AS total_workers FROM raw_workday_workers WHERE employee_status = ''Active'''
    ),
    flight_risk_candidates AS (
      QUESTION 'Which employees have a comp-ratio below 0.85 and a rating of 4 or above?'
      SQL 'SELECT w.employee_id, w.first_name, w.last_name, w.department_code, w.band_code, ROUND(w.base_pay / NULLIF(c.mid_point, 0), 2) AS comp_ratio, r.rating_score FROM raw_workday_workers w JOIN raw_compensation_bands c ON w.band_code = c.band_code JOIN raw_performance_reviews r ON w.employee_id = r.employee_id WHERE w.employee_status = ''Active'' AND (w.base_pay / NULLIF(c.mid_point, 0)) < 0.85 AND r.rating_score >= 4 ORDER BY comp_ratio ASC'
    ),
    review_notes_lookup AS (
      QUESTION 'Show me the review notes for employee EMP-0042'
      SQL 'SELECT r.review_id, r.employee_id, r.review_period, r.rating_score, r.goals_met_pct, r.review_text FROM raw_performance_reviews r WHERE r.employee_id = ''EMP-0042'''
    )
  );

-- Note on SEMANTIC_VIEW() column naming (verified against docs.snowflake.com, Sep-2026):
-- In Snowflake's native SEMANTIC_VIEW() table function, output column headers use the
-- UNQUALIFIED name of the metric/dimension by default (e.g., `headcount`, `comp_ratio`),
-- NOT `workers__headcount`. If an alias like `workers__headcount` is desired in the output,
-- it must be explicitly defined inside the SEMANTIC_VIEW clause:
--   e.g., METRICS workers.headcount AS workers__headcount
-- Both the governed queries (using SEMANTIC_VIEW) and the naive/raw queries (using plain SQL)
-- are valid verified queries in Cortex Analyst. The demo compares `governed_headcount`
-- against `naive_headcount_comparison` to show genuine governance conflict resolution.

