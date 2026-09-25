-- Workforce Astra: Governance spine -- Metric Definition Registry, Regression Tests, Scheduled Alerts
-- Deployed live 21-Sep-2026; extended 25-Sep-2026 with the employee-voice metrics (Tests 8-17).
-- This is the layer that stops teams disagreeing again:
-- every governed metric has an owner, a certified definition, and a golden-value test.
-- Verified live: run_metric_tests() -> 17/17 PASS.
--
-- TEST STABILITY, stated honestly. Tests 1-7 are DETERMINISTIC: they read tables, so they only
-- fail if someone changes the data or a definition. Tests 8-17 read the output of Snowflake-hosted
-- Cortex models (SNOWFLAKE.CORTEX.SENTIMENT / AI_CLASSIFY), so they pin CURRENT MODEL BEHAVIOUR:
-- if Snowflake upgrades the underlying model, these will fail. That is the intended behaviour for a
-- regression suite -- it means a silent change in the AI pipeline becomes a visible, triaged alert
-- rather than a silently different number in a board pack. They are flagged model_dependent in
-- the registry below.

USE DATABASE WORKFORCE_ASTRA;
USE SCHEMA RAW;

-- 1. Tables
CREATE OR REPLACE TABLE metric_registry (
    metric_id STRING, metric_name STRING, domain STRING, owner_role STRING, definition STRING,
    certified BOOLEAN, version STRING, model_dependent BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE metric_regression_tests (
    test_id NUMBER, metric_name STRING, sql_text STRING, expected_value FLOAT, tolerance FLOAT);
CREATE OR REPLACE TABLE metric_test_results (
    test_id NUMBER, metric_name STRING, expected_value FLOAT, actual_value FLOAT, status STRING,
    checked_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE governance_alerts (
    alert_type STRING, severity STRING, metric_name STRING, detail STRING,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP());

-- 2. Registry seed (owners + certified definitions; the naive metric is deliberately UNcertified)
INSERT OVERWRITE INTO metric_registry (metric_id, metric_name, domain, owner_role, definition, certified, version, model_dependent) VALUES
  ('M-001','governed_headcount','Headcount','PEOPLE_OPS','COUNT DISTINCT of Active FTE employees (contractors excluded)',TRUE,'v1',FALSE),
  ('M-002','naive_headcount','Headcount','UNOWNED','COUNT of all Active records incl. contractors - the UNGOVERNED comparison',FALSE,'v1',FALSE),
  ('M-003','attrition_velocity','Retention','PEOPLE_OPS','Terminated FTE in trailing 12 months divided by FTE base',TRUE,'v1',FALSE),
  ('M-004','comp_ratio','Compensation','COMP','base_pay divided by band mid-point',TRUE,'v1',FALSE),
  ('M-005','avg_span_of_control','Org Design','PEOPLE_OPS','Average direct reports per manager (managers = 1+ direct reports)',TRUE,'v1',FALSE),
  ('M-006','overspan_managers','Org Design','PEOPLE_OPS','Managers with more than 10 direct reports',TRUE,'v1',FALSE),
  ('M-007','unadjusted_gap_pct','Pay Equity','LEGAL','Women minus Men average base pay over Men average base pay (band mix exposed)',TRUE,'v1',FALSE),
  ('M-008','adjusted_gap_pct','Pay Equity','LEGAL','Women minus Men average comp-ratio (band-normalised) over Men comp-ratio',TRUE,'v1',FALSE),
  -- Employee voice (Phase B1). All model_dependent = TRUE: these come from Cortex models, so a
  -- model upgrade legitimately changes the golden value and must be triaged, not ignored.
  ('M-009','voice_transcript_count','Employee Voice','PEOPLE_OPS','Count of stay and exit interview transcripts scored by the Snowpark procedure',TRUE,'v1',TRUE),
  ('M-010','voice_negative_transcript_count','Employee Voice','PEOPLE_OPS','Transcripts whose SNOWFLAKE.CORTEX.SENTIMENT score is at or below the governed -0.20 band',TRUE,'v1',TRUE),
  ('M-011','voice_flight_risk_signal_count','Employee Voice','PEOPLE_OPS','Exit interviews scoring below -0.10 whose primary classified reason is a fixable one (pay, manager, progression)',TRUE,'v1',TRUE),
  ('M-012','voice_corroborated_flight_risk_count','Employee Voice','PEOPLE_OPS','Voice flight-risk signals that also meet the structured rule: comp_ratio below 0.85 and latest rating 4 or above',TRUE,'v1',TRUE),
  ('M-013','voice_unclassified_rows','Employee Voice','PEOPLE_OPS','Transcripts the classifier returned no primary reason for. Must be zero: a silent classification failure is a governance failure, not a shrug',TRUE,'v1',TRUE);

-- 3. Golden-value tests
INSERT OVERWRITE INTO metric_regression_tests (test_id, metric_name, sql_text, expected_value, tolerance) VALUES
 (1,'governed_headcount',$$SELECT headcount FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_360 METRICS workers.headcount)$$,109,0),
 (2,'naive_headcount',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.raw_workday_workers WHERE employee_status = 'Active'$$,127,0),
 (3,'avg_span_of_control',$$SELECT AVG(direct_reports) FROM WORKFORCE_ASTRA.RAW.raw_org_flattened WHERE direct_reports >= 1$$,9.0,0.01),
 (4,'overspan_managers',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.raw_org_flattened WHERE direct_reports > 10$$,5,0),
 (5,'manager_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.raw_org_flattened WHERE direct_reports >= 1$$,15,0),
 (6,'women_avg_comp_ratio',$$SELECT AVG(comp_ratio) FROM WORKFORCE_ASTRA.RAW.raw_pay_equity_base WHERE gender_cohort = 'Women' AND employment_type = 'FTE' AND employee_status = 'Active'$$,0.9601,0.01),
  (7,'men_avg_comp_ratio',$$SELECT AVG(comp_ratio) FROM WORKFORCE_ASTRA.RAW.raw_pay_equity_base WHERE gender_cohort = 'Men' AND employment_type = 'FTE' AND employee_status = 'Active'$$,0.9633,0.01),
  -- Employee voice (Phase B1). Tests 11 and 13 are the two that matter most: a sentiment score
  -- outside the documented [-1, +1] contract, and a transcript the classifier could not label,
  -- are both silent-failure modes that would otherwise look like normal data.
  (8, 'voice_transcript_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_theme_results$$,18,0),
  (9, 'voice_exit_transcript_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_theme_results WHERE interview_type = 'exit'$$,13,0),
  (10,'voice_stay_transcript_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_theme_results WHERE interview_type = 'stay'$$,5,0),
  (11,'voice_sentiment_out_of_range',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_theme_results WHERE sentiment_score < -1 OR sentiment_score > 1$$,0,0),
  (12,'voice_unclassified_rows',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_theme_results WHERE primary_reason IS NULL$$,0,0),
  (13,'voice_negative_transcript_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_theme_results WHERE sentiment_label = 'negative'$$,9,0),
  (14,'voice_multi_reason_transcript_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_theme_results WHERE secondary_reason IS NOT NULL$$,13,0),
  (15,'voice_flight_risk_signal_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_theme_results WHERE flight_risk_signal$$,7,0),
  (16,'voice_corroborated_flight_risk_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_risk_360 WHERE corroborated_flight_risk$$,5,0),
  -- The headline voice finding, pinned: lack of progression is the single most-cited reason.
  (17,'voice_career_growth_primary_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.voice_theme_results WHERE primary_reason = 'career_growth'$$,6,0);

-- 4. Regression runner (JavaScript SP: runs each golden query and records PASS/FAIL)
CREATE OR REPLACE PROCEDURE run_metric_tests()
RETURNS VARIANT LANGUAGE JAVASCRIPT AS
$$
  var passed = 0, failed = 0;
  snowflake.execute({sqlText: 'DELETE FROM WORKFORCE_ASTRA.RAW.metric_test_results'});
  var rs = snowflake.execute({sqlText: 'SELECT test_id, metric_name, sql_text, expected_value, tolerance FROM WORKFORCE_ASTRA.RAW.metric_regression_tests ORDER BY test_id'});
  while (rs.next()) {
    var testId = rs.getColumnValue('TEST_ID'), metric = rs.getColumnValue('METRIC_NAME'),
        sql = rs.getColumnValue('SQL_TEXT'), expected = rs.getColumnValue('EXPECTED_VALUE'),
        tol = rs.getColumnValue('TOLERANCE'), actual = null;
    try { var ar = snowflake.execute({sqlText: sql}); if (ar.next()) { actual = ar.getColumnValue(1); } } catch (e) {}
    var ok = (actual !== null && Math.abs(Number(actual) - Number(expected)) <= Number(tol));
    if (ok) { passed++; } else { failed++; }
    snowflake.execute({sqlText: 'INSERT INTO WORKFORCE_ASTRA.RAW.metric_test_results (test_id, metric_name, expected_value, actual_value, status) VALUES (?,?,?,?,?)',
      binds: [testId, metric, expected, actual, ok ? 'PASS' : 'FAIL']});
  }
  return {passed: passed, failed: failed};
$$;

-- 5. Pay-equity drift check (alerts when the ADJUSTED gap breaches 2%)
CREATE OR REPLACE PROCEDURE check_pay_equity_drift()
RETURNS VARIANT LANGUAGE SQL AS
$$
DECLARE v_adj FLOAT; v_unadj FLOAT; v_adj_rnd STRING; v_unadj_rnd STRING; v_sev STRING; v_detail STRING;
BEGIN
    SELECT adjusted_gap_pct   INTO :v_adj   FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.pay_equity_360 METRICS pe.adjusted_gap_pct);
    SELECT unadjusted_gap_pct INTO :v_unadj FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.pay_equity_360 METRICS pe.unadjusted_gap_pct);
    SELECT ROUND(:v_adj * 100, 2)::STRING   INTO :v_adj_rnd;
    SELECT ROUND(:v_unadj * 100, 2)::STRING INTO :v_unadj_rnd;
    IF (ABS(COALESCE(:v_adj,0)) > 0.02) THEN
        v_sev := 'HIGH';
        v_detail := 'Adjusted gap ' || :v_adj_rnd || '% exceeds the 2% threshold - escalate to Compensation Committee. Unadjusted ' || :v_unadj_rnd || '%.';
    ELSE
        v_sev := 'INFO';
        v_detail := 'Adjusted gap ' || :v_adj_rnd || '% within threshold. Unadjusted ' || :v_unadj_rnd || '%.';
    END IF;
    INSERT INTO governance_alerts (alert_type, severity, metric_name, detail)
    VALUES ('PAY_EQUITY_DRIFT', :v_sev, 'adjusted_gap_pct', :v_detail);
    RETURN OBJECT_CONSTRUCT('adjusted_gap_pct',:v_adj,'unadjusted_gap_pct',:v_unadj,'severity',:v_sev);
END;
$$;

-- 6. Scheduled automations
CREATE OR REPLACE TASK metric_regression_daily WAREHOUSE = COMPUTE_WH SCHEDULE = 'USING CRON 30 2 * * * UTC'
AS CALL WORKFORCE_ASTRA.RAW.run_metric_tests();
CREATE OR REPLACE TASK pay_equity_drift_weekly WAREHOUSE = COMPUTE_WH SCHEDULE = 'USING CRON 0 3 * * 1 UTC'
AS CALL WORKFORCE_ASTRA.RAW.check_pay_equity_drift();
ALTER TASK metric_regression_daily  RESUME;
ALTER TASK pay_equity_drift_weekly   RESUME;

-- Verify:
-- CALL run_metric_tests();
-- SELECT * FROM metric_test_results ORDER BY test_id;   -- expect 7/7 PASS
-- SELECT * FROM governance_alerts ORDER BY created_at DESC LIMIT 5;
