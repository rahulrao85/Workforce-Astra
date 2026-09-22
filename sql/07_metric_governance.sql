-- Workforce Astra: Governance spine -- Metric Definition Registry, Regression Tests, Scheduled Alerts
-- Deployed live 21-Sep-2026. This is the layer that stops teams disagreeing again:
-- every governed metric has an owner, a certified definition, and a golden-value test.
-- Verified live: run_metric_tests() -> 7/7 PASS.

USE DATABASE WORKFORCE_ASTRA;
USE SCHEMA RAW;

-- 1. Tables
CREATE OR REPLACE TABLE metric_registry (
    metric_id STRING, metric_name STRING, domain STRING, owner_role STRING, definition STRING,
    certified BOOLEAN, version STRING, updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE metric_regression_tests (
    test_id NUMBER, metric_name STRING, sql_text STRING, expected_value FLOAT, tolerance FLOAT);
CREATE OR REPLACE TABLE metric_test_results (
    test_id NUMBER, metric_name STRING, expected_value FLOAT, actual_value FLOAT, status STRING,
    checked_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE governance_alerts (
    alert_type STRING, severity STRING, metric_name STRING, detail STRING,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP());

-- 2. Registry seed (owners + certified definitions; the naive metric is deliberately UNcertified)
INSERT OVERWRITE INTO metric_registry (metric_id, metric_name, domain, owner_role, definition, certified, version) VALUES
 ('M-001','governed_headcount','Headcount','PEOPLE_OPS','COUNT DISTINCT of Active FTE employees (contractors excluded)',TRUE,'v1'),
 ('M-002','naive_headcount','Headcount','UNOWNED','COUNT of all Active records incl. contractors - the UNGOVERNED comparison',FALSE,'v1'),
 ('M-003','attrition_velocity','Retention','PEOPLE_OPS','Terminated FTE in trailing 12 months divided by FTE base',TRUE,'v1'),
 ('M-004','comp_ratio','Compensation','COMP','base_pay divided by band mid-point',TRUE,'v1'),
 ('M-005','avg_span_of_control','Org Design','PEOPLE_OPS','Average direct reports per manager (managers = 1+ direct reports)',TRUE,'v1'),
 ('M-006','overspan_managers','Org Design','PEOPLE_OPS','Managers with more than 10 direct reports',TRUE,'v1'),
 ('M-007','unadjusted_gap_pct','Pay Equity','LEGAL','Women minus Men average base pay over Men average base pay (band mix exposed)',TRUE,'v1'),
 ('M-008','adjusted_gap_pct','Pay Equity','LEGAL','Women minus Men average comp-ratio (band-normalised) over Men comp-ratio',TRUE,'v1');

-- 3. Golden-value tests
INSERT OVERWRITE INTO metric_regression_tests (test_id, metric_name, sql_text, expected_value, tolerance) VALUES
 (1,'governed_headcount',$$SELECT headcount FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_360 METRICS workers.headcount)$$,109,0),
 (2,'naive_headcount',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.raw_workday_workers WHERE employee_status = 'Active'$$,127,0),
 (3,'avg_span_of_control',$$SELECT AVG(direct_reports) FROM WORKFORCE_ASTRA.RAW.raw_org_flattened WHERE direct_reports >= 1$$,9.0,0.01),
 (4,'overspan_managers',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.raw_org_flattened WHERE direct_reports > 10$$,5,0),
 (5,'manager_count',$$SELECT COUNT(*) FROM WORKFORCE_ASTRA.RAW.raw_org_flattened WHERE direct_reports >= 1$$,15,0),
 (6,'women_avg_comp_ratio',$$SELECT AVG(comp_ratio) FROM WORKFORCE_ASTRA.RAW.raw_pay_equity_base WHERE gender_cohort = 'Women' AND employment_type = 'FTE' AND employee_status = 'Active'$$,0.9601,0.01),
 (7,'men_avg_comp_ratio',$$SELECT AVG(comp_ratio) FROM WORKFORCE_ASTRA.RAW.raw_pay_equity_base WHERE gender_cohort = 'Men' AND employment_type = 'FTE' AND employee_status = 'Active'$$,0.9633,0.01);

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
