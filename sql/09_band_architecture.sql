-- Workforce Astra: #5 Comp Band Architecture Auditor
-- Built 25-Sep-2026. Applied through CoCo CLI.
--
-- WHY: bands get set once and drift for years. Nobody owns "is this band still fit for purpose?"
-- until an audit or a failed offer cycle. This is STRUCTURAL comp (where people sit inside their
-- range) and is deliberately distinct from sql/06 pay equity, which is DEMOGRAPHIC (whether the
-- gap is explained by band mix). The two answer different questions and both are needed.
--
-- No new raw data. Everything derives from raw_workday_workers + raw_compensation_bands, per the
-- single-grain rule: band_range_health is one row per band_code, so a semantic view over it can
-- never fan out.
--
-- WHAT THE DATA ACTUALLY SHOWS (measured live, not assumed):
--   red_circle_rate  = 0.0%   -- nobody is paid above their band maximum
--   below_range_rate = 24.7%  -- 37 of 150 employees are paid BELOW their band minimum
--   avg range penetration 0.24-0.38 -- the whole workforce sits in the lower third of its range
-- The interesting finding is therefore not red circles; it is that a quarter of the company is
-- priced outside its own published range. That is a compliance problem, and it is reported as
-- measured rather than as the more flattering metric we might have hoped for.

USE DATABASE WORKFORCE_ASTRA;
USE SCHEMA RAW;

-- ---------------------------------------------------------------------------
-- 1. Band-grain base table (derived, one row per band)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE WORKFORCE_ASTRA.RAW.band_range_health AS
WITH emp AS (
    SELECT w.employee_id, w.band_code, w.base_pay, w.employee_status, w.employment_type,
           c.min_base, c.mid_point, c.max_base,
           (w.base_pay - c.min_base) / NULLIF(c.max_base - c.min_base, 0) AS range_penetration,
           w.base_pay / NULLIF(c.mid_point, 0)                             AS comp_ratio
    FROM WORKFORCE_ASTRA.RAW.raw_workday_workers    w
    JOIN WORKFORCE_ASTRA.RAW.raw_compensation_bands c ON c.band_code = w.band_code
)
SELECT
    b.band_code,
    b.band_title,
    b.min_base,
    b.mid_point,
    b.max_base,
    COUNT(e.employee_id)                                                        AS headcount,
    -- Structural flags
    COUNT_IF(e.base_pay > b.max_base)                                            AS red_circle_count,
    COUNT_IF(e.base_pay < b.min_base)                                            AS below_range_count,
    COUNT_IF(e.base_pay = b.min_base)                                            AS at_floor_count,
    COUNT_IF(e.range_penetration >= 0 AND e.range_penetration < 0.10)            AS in_floor_cluster_count,
    COUNT_IF(e.comp_ratio < 0.90)                                                AS offer_reject_risk_count,
    -- Distribution
    MIN(e.base_pay)                                                              AS min_actual_pay,
    MAX(e.base_pay)                                                              AS max_actual_pay,
    AVG(e.base_pay)                                                              AS avg_actual_pay,
    AVG(e.range_penetration)                                                     AS avg_range_penetration,
    AVG(e.comp_ratio)                                                            AS avg_comp_ratio,
    -- Standard compression ratio: range width relative to range midpoint.
    -- 0 = infinitely wide, ->1 = infinitesimally narrow. Higher = more compressed = worse.
    (b.max_base - b.min_base) / NULLIF(b.max_base + b.min_base, 0)               AS compression_ratio,
    -- Rates
    COUNT_IF(e.base_pay > b.max_base) / NULLIF(COUNT(e.employee_id), 0)          AS red_circle_rate,
    COUNT_IF(e.base_pay < b.min_base) / NULLIF(COUNT(e.employee_id), 0)          AS below_range_rate,
    COUNT_IF(e.range_penetration >= 0 AND e.range_penetration < 0.10)
        / NULLIF(COUNT(e.employee_id), 0)                                        AS in_floor_cluster_pct,
    COUNT_IF(e.comp_ratio < 0.90) / NULLIF(COUNT(e.employee_id), 0)               AS offer_reject_risk_pct
FROM WORKFORCE_ASTRA.RAW.raw_compensation_bands b
LEFT JOIN emp e ON e.band_code = b.band_code
GROUP BY b.band_code, b.band_title, b.min_base, b.mid_point, b.max_base;

-- ---------------------------------------------------------------------------
-- 2. Adjacent-band overlap: do neighbouring ranges sit on top of each other?
--    A large overlap means the architecture cannot tell IC4 from IC5 in practice.
--    Expressed as a fraction of the LOWER band's range width, so 0 = no overlap, 1 = identical.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE WORKFORCE_ASTRA.RAW.band_range_overlap AS
WITH ordered AS (
    SELECT band_code, min_base, max_base,
           ROW_NUMBER() OVER (ORDER BY mid_point) AS lvl
    FROM WORKFORCE_ASTRA.RAW.raw_compensation_bands
)
SELECT
    lower_band.band_code AS lower_band,
    upper_band.band_code AS upper_band,
    lower_band.min_base  AS lower_min,
    lower_band.max_base  AS lower_max,
    upper_band.min_base  AS upper_min,
    upper_band.max_base  AS upper_max,
    GREATEST(0, lower_band.max_base - upper_band.min_base) AS overlap_amount,
    GREATEST(0, lower_band.max_base - upper_band.min_base)
        / NULLIF(lower_band.max_base - lower_band.min_base, 0) AS overlap_index
FROM ordered lower_band
JOIN ordered upper_band ON upper_band.lvl = lower_band.lvl + 1;

-- ---------------------------------------------------------------------------
-- 3. Findings table + the review procedure.
--    GUARDRAIL, and it is the important part: this reports outliers. It NEVER proposes a number
--    and never writes to pay. Setting band architecture is a human decision with legal weight;
--    a stored procedure that "helpfully" suggests the new salary is exactly the failure mode this
--    project is arguing against. So there is deliberately no proposed_pay column.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE WORKFORCE_ASTRA.RAW.band_review_findings (
    employee_id STRING, band_code STRING, base_pay NUMBER, min_base NUMBER, max_base NUMBER,
    range_penetration FLOAT, comp_ratio FLOAT, flag STRING, flag_reason STRING,
    reviewed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE PROCEDURE WORKFORCE_ASTRA.RAW.run_band_review()
RETURNS VARIANT
LANGUAGE SQL
AS
$$
DECLARE
    v_rows NUMBER;
    v_red  NUMBER;
    v_below NUMBER;
    v_floor NUMBER;
BEGIN
    DELETE FROM WORKFORCE_ASTRA.RAW.band_review_findings;

    INSERT INTO WORKFORCE_ASTRA.RAW.band_review_findings
        (employee_id, band_code, base_pay, min_base, max_base, range_penetration, comp_ratio, flag, flag_reason)
    -- Computed as a derived subquery rather than a LATERAL join: the LATERAL form raised a
    -- Snowflake internal error (300002) on this account, so the flags are projected in an inner
    -- SELECT and filtered outside it.
    SELECT employee_id, band_code, base_pay, min_base, max_base, range_penetration, comp_ratio, flag, flag_reason
    FROM (
        SELECT w.employee_id, w.band_code, w.base_pay, c.min_base, c.max_base,
               (w.base_pay - c.min_base) / NULLIF(c.max_base - c.min_base, 0) AS range_penetration,
               w.base_pay / NULLIF(c.mid_point, 0) AS comp_ratio,
               CASE
                   WHEN w.base_pay < c.min_base THEN 'BELOW_RANGE_MIN'
                   WHEN w.base_pay > c.max_base THEN 'RED_CIRCLE'
                   WHEN (w.base_pay - c.min_base) / NULLIF(c.max_base - c.min_base, 0) < 0.10
                       THEN 'IN_FLOOR_CLUSTER'
               END AS flag,
               CASE
                   WHEN w.base_pay < c.min_base
                       THEN 'Paid below the published band minimum - a range-compliance exception, not a market position'
                   WHEN w.base_pay > c.max_base
                       THEN 'Paid above the published band maximum (red circle) - requires a documented exception or a band change'
                   WHEN (w.base_pay - c.min_base) / NULLIF(c.max_base - c.min_base, 0) < 0.10
                       THEN 'Sits in the bottom 10% of the range - long-tenure risk if the range never moves'
               END AS flag_reason
        FROM WORKFORCE_ASTRA.RAW.raw_workday_workers    w
        JOIN WORKFORCE_ASTRA.RAW.raw_compensation_bands c ON c.band_code = w.band_code
    ) flagged
    WHERE flag IS NOT NULL;

    SELECT COUNT(*) INTO :v_rows FROM WORKFORCE_ASTRA.RAW.band_review_findings;
    SELECT COUNT_IF(flag = 'RED_CIRCLE')        INTO :v_red   FROM WORKFORCE_ASTRA.RAW.band_review_findings;
    SELECT COUNT_IF(flag = 'BELOW_RANGE_MIN')   INTO :v_below FROM WORKFORCE_ASTRA.RAW.band_review_findings;
    SELECT COUNT_IF(flag = 'IN_FLOOR_CLUSTER')  INTO :v_floor FROM WORKFORCE_ASTRA.RAW.band_review_findings;

    -- A quarter of the company priced outside its own range is an escalation, not a dashboard line.
    -- LET, not DECLARE: in Snowflake SQL scripting a DECLARE after executable statements inside a
    -- BEGIN block is a compile error.
    LET v_alert STRING :=
        'Band review flagged ' || :v_rows || ' employees: ' || :v_below || ' below range minimum, '
        || :v_red || ' red circle, ' || :v_floor || ' clustered at the floor. '
        || 'REPORTS ONLY - no pay values are proposed or changed by this procedure.';

    INSERT INTO WORKFORCE_ASTRA.RAW.governance_alerts (alert_type, severity, metric_name, detail)
    SELECT 'BAND_ARCHITECTURE', v_sev, 'below_range_rate', v_alert
    FROM (SELECT CASE WHEN :v_below > 0 THEN 'HIGH' ELSE 'INFO' END AS v_sev);

    RETURN OBJECT_CONSTRUCT('findings', :v_rows, 'below_range_min', :v_below,
                            'red_circle', :v_red, 'in_floor_cluster', :v_floor,
                            'proposed_pay_values', 0);
END;
$$;

-- ---------------------------------------------------------------------------
-- 4. Governed semantic view
-- ---------------------------------------------------------------------------
CREATE OR REPLACE SEMANTIC VIEW WORKFORCE_ASTRA.RAW.band_health_360
  TABLES (
    band AS WORKFORCE_ASTRA.RAW.band_range_health PRIMARY KEY (band_code)
      WITH SYNONYMS ('comp bands','band architecture','range design','salary ranges')
  )
  FACTS (
    band.headcount            AS headcount,
    band.avg_actual_pay       AS avg_actual_pay,
    band.avg_range_penetration AS avg_range_penetration,
    band.compression_ratio    AS compression_ratio,
    band.avg_comp_ratio       AS avg_comp_ratio
  )
  DIMENSIONS (
    band.band_code   AS band_code,
    band.band_title  AS band_title
  )
  METRICS (
    band.total_headcount AS SUM(band.headcount),
    band.red_circle_count AS SUM(band.red_circle_count),
    band.below_range_count AS SUM(band.below_range_count),
    band.in_floor_cluster_count AS SUM(band.in_floor_cluster_count),
    -- NOTE: the metric alias must differ from the fact alias. Reusing
    -- AVG_RANGE_PENETRATION for both fails with "Duplicate expression name
    -- 'BAND.AVG_RANGE_PENETRATION'". The rate metrics likewise reference the other metrics
    -- directly rather than re-aggregating the underlying columns.
    band.wtd_avg_range_penetration AS SUM(band.avg_range_penetration * band.headcount)
                                    / NULLIF(SUM(band.headcount), 0),
    band.avg_compression_ratio AS AVG(band.compression_ratio),
    band.below_range_rate AS band.below_range_count / NULLIF(band.total_headcount, 0),
    band.red_circle_rate   AS band.red_circle_count  / NULLIF(band.total_headcount, 0),
    band.in_floor_cluster_pct AS band.in_floor_cluster_count / NULLIF(band.total_headcount, 0)
  )
  COMMENT = 'Governed comp band architecture: range compliance, penetration, clustering, compression'
  AI_VERIFIED_QUERIES (
    range_compliance AS (
      QUESTION 'How many employees are paid outside their published band range?'
      SQL 'SELECT below_range_count, red_circle_count FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.band_health_360 METRICS band.below_range_count, band.red_circle_count)'
    ),
    penetration_by_band AS (
      QUESTION 'What is the average range penetration by band?'
      SQL 'SELECT band_code, wtd_avg_range_penetration FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.band_health_360 DIMENSIONS band.band_code METRICS band.wtd_avg_range_penetration) ORDER BY wtd_avg_range_penetration DESC'
    ),
    worst_band AS (
      QUESTION 'Which band has the most people paid below its minimum?'
      SQL 'SELECT band_code, below_range_count FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.band_health_360 DIMENSIONS band.band_code METRICS band.below_range_count) ORDER BY below_range_count DESC'
    )
  );

-- ---------------------------------------------------------------------------
-- 5. Quarterly scheduled audit
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TASK band_architecture_quarterly WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 4 1 1,4,7,10 * UTC'
  AS CALL WORKFORCE_ASTRA.RAW.run_band_review();
ALTER TASK band_architecture_quarterly RESUME;

-- ---------------------------------------------------------------------------
-- 6. Verify
--    CALL WORKFORCE_ASTRA.RAW.run_band_review();     -- findings, below_range_min, red_circle, in_floor_cluster
--    SELECT * FROM WORKFORCE_ASTRA.RAW.band_range_health ORDER BY band_code;
--    SELECT * FROM WORKFORCE_ASTRA.RAW.band_range_overlap ORDER BY lower_band;
--    SHOW TASKS IN SCHEMA WORKFORCE_ASTRA.RAW;
--    CALL WORKFORCE_ASTRA.RAW.run_metric_tests();
