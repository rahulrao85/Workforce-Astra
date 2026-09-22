-- Workforce Astra: governed Semantic View for Employee 360.
-- CONFIRMED LIVE 16-Sep-2026; UPDATED + RE-VERIFIED 21-Sep-2026.
-- 21-Sep fix (found via Cortex Analyst REST): verified queries must (a) reference the semantic
-- view logically, not physical tables, or Analyst silently drops them; and (b) fully qualify
-- SEMANTIC_VIEW(DB.SCHEMA.VIEW ...) or they fail with "must specify database". Also added the
-- governed `naive_headcount` metric so the headline conflict is expressible inside Analyst.
-- Verified live: governed 109 vs naive 127; Analyst returns 0 warnings.
-- Clause order is REQUIRED: TABLES -> RELATIONSHIPS -> FACTS -> DIMENSIONS -> METRICS -> COMMENT/AI_VERIFIED_QUERIES.

CREATE OR REPLACE SEMANTIC VIEW WORKFORCE_ASTRA.RAW.employee_360
  TABLES (
    workers AS WORKFORCE_ASTRA.RAW.raw_workday_workers      PRIMARY KEY (employee_id) WITH SYNONYMS ('employees','headcount'),
    comp    AS WORKFORCE_ASTRA.RAW.raw_compensation_bands   PRIMARY KEY (band_code),
    reviews AS WORKFORCE_ASTRA.RAW.raw_performance_reviews  PRIMARY KEY (review_id)
  )
  RELATIONSHIPS (
    workers_to_comp    AS workers(band_code)   REFERENCES comp(band_code),
    reviews_to_workers AS reviews(employee_id) REFERENCES workers(employee_id)
  )
  FACTS (
    workers.base_pay      AS base_pay,
    comp.mid_point        AS mid_point,
    reviews.rating_score  AS rating_score,
    reviews.goals_met_pct AS goals_met_pct
  )
  DIMENSIONS (
    workers.employee_id      AS employee_id,
    workers.department_code  AS department_code,
    workers.band_code        AS band_code,
    workers.employee_status  AS employee_status,
    workers.employment_type  AS employment_type,   -- the governance lever
    workers.hire_date        AS hire_date,
    workers.termination_date AS termination_date
  )
  METRICS (
    -- Governed headcount: FTE only. The naive metric below is the "ungoverned" number the
    -- demo's cold open shows disagreeing.
    workers.headcount AS
      COUNT(DISTINCT CASE
        WHEN workers.employee_status = 'Active' AND workers.employment_type = 'FTE'
        THEN workers.employee_id END),

    workers.naive_headcount AS
      COUNT(DISTINCT CASE
        WHEN workers.employee_status = 'Active'
        THEN workers.employee_id END),

    workers.attrition_velocity AS
      COUNT(DISTINCT CASE
        WHEN workers.employee_status = 'Terminated'
         AND workers.employment_type = 'FTE'
         AND workers.termination_date >= DATEADD('year', -1, CURRENT_DATE())
        THEN workers.employee_id END)
      / NULLIF(COUNT(DISTINCT CASE WHEN workers.employment_type = 'FTE' THEN workers.employee_id END), 0),

    workers.comp_ratio AS AVG(workers.base_pay / NULLIF(comp.mid_point, 0))
  )
  COMMENT = 'Governed Employee 360 -- Workforce Astra (governed vs naive headcount; the headline conflict)'
  AI_VERIFIED_QUERIES (
    governed_headcount AS (
      QUESTION 'How many active FTE employees do we have?'
      SQL 'SELECT headcount FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_360 METRICS workers.headcount)'
    ),
    naive_headcount AS (
      QUESTION 'How many active people work here including contractors?'
      SQL 'SELECT naive_headcount FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_360 METRICS workers.naive_headcount)'
    ),
    governed_vs_naive AS (
      QUESTION 'Compare governed headcount against the naive count including contractors'
      SQL 'SELECT headcount, naive_headcount FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_360 METRICS workers.headcount, workers.naive_headcount)'
    ),
    attrition_rate AS (
      QUESTION 'What is our attrition rate this year?'
      SQL 'SELECT attrition_velocity FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_360 METRICS workers.attrition_velocity)'
    ),
    comp_ratio_by_dept AS (
      QUESTION 'What is the comp-ratio by department?'
      SQL 'SELECT department_code, comp_ratio FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_360 DIMENSIONS workers.department_code METRICS workers.comp_ratio) ORDER BY comp_ratio'
    )
  );
