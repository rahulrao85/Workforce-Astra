-- Workforce Astra: #2 Pay Equity & Adverse-Impact Auditor
-- Deployed live 21-Sep-2026. Governance story: band-mix creates a real UNadjusted gap
-- while comp_ratio (band-normalised) keeps the ADJUSTED gap small.
-- Verified live: unadjusted -16.8% vs adjusted -2.8%.

USE DATABASE WORKFORCE_ASTRA;
USE SCHEMA RAW;

-- 1. Protected attributes (SYNTHETIC). Band-mix skew is deliberate: women over-represented
--    in junior bands, under-represented in senior bands -> creates the unadjusted gap honestly.
CREATE OR REPLACE TABLE raw_employee_demographics (
    employee_id STRING PRIMARY KEY, gender_cohort STRING, ethnicity_cohort STRING, age_band STRING,
    veteran_status BOOLEAN, disability_status BOOLEAN, location_code STRING,
    synthetic_note STRING DEFAULT 'SYNTHETIC - generated deterministically; not real PII');

INSERT OVERWRITE INTO raw_employee_demographics
    (employee_id, gender_cohort, ethnicity_cohort, age_band, veteran_status, disability_status, location_code)
WITH r AS (
    SELECT employee_id, band_code,
        UNIFORM(0,99,HASH(employee_id || '|g')) AS r_g, UNIFORM(0,99,HASH(employee_id || '|e')) AS r_e,
        UNIFORM(0,99,HASH(employee_id || '|a')) AS r_a, UNIFORM(0,99,HASH(employee_id || '|v')) AS r_v,
        UNIFORM(0,99,HASH(employee_id || '|d')) AS r_d, UNIFORM(0,99,HASH(employee_id || '|l')) AS r_l
    FROM raw_workday_workers)
SELECT employee_id,
    CASE WHEN r_g < (CASE band_code WHEN 'IC3' THEN 60 WHEN 'IC4' THEN 52 WHEN 'IC5' THEN 40
                                    WHEN 'M1' THEN 35 WHEN 'M2' THEN 30 ELSE 48 END) THEN 'Women'
         WHEN r_g < 97 THEN 'Men' ELSE 'Non-binary' END,
    CASE WHEN r_e < 25 THEN 'Asian' WHEN r_e < 70 THEN 'White' WHEN r_e < 85 THEN 'Hispanic/Latino'
         WHEN r_e < 95 THEN 'Black' ELSE 'Two or More' END,
    CASE WHEN r_a < 28 THEN 'Under 30' WHEN r_a < 62 THEN '30-39' WHEN r_a < 88 THEN '40-49' ELSE '50+' END,
    (r_v < 8), (r_d < 6),
    CASE WHEN r_l < 45 THEN 'IN-BLR' WHEN r_l < 65 THEN 'US-SFO' WHEN r_l < 82 THEN 'US-NYC'
         WHEN r_l < 93 THEN 'UK-LON' ELSE 'US-AUS' END
FROM r;

-- 2. Employee-grain base (single grain => no fan-out when joined in the semantic view)
CREATE OR REPLACE TABLE raw_pay_equity_base AS
SELECT w.employee_id, w.department_code, w.band_code, w.employee_status, w.employment_type, w.hire_date,
       d.gender_cohort, d.ethnicity_cohort, d.age_band, d.location_code, d.veteran_status, d.disability_status,
       w.base_pay, c.mid_point, ROUND(w.base_pay / NULLIF(c.mid_point, 0), 4) AS comp_ratio
FROM raw_workday_workers w
JOIN raw_employee_demographics d ON d.employee_id = w.employee_id
JOIN raw_compensation_bands  c ON c.band_code = w.band_code;

-- 3. k-anonymity guardrail: cohorts below 5 have figures withheld
CREATE OR REPLACE VIEW pay_equity_cohorts AS
SELECT department_code, band_code, gender_cohort,
    COUNT(DISTINCT employee_id) AS cohort_size,
    ROUND(AVG(base_pay),0) AS avg_base_pay, ROUND(AVG(comp_ratio),4) AS avg_comp_ratio,
    (COUNT(DISTINCT employee_id) < 5) AS is_suppressed,
    CASE WHEN COUNT(DISTINCT employee_id) < 5 THEN NULL ELSE ROUND(AVG(base_pay),0) END AS avg_base_pay_safe,
    CASE WHEN COUNT(DISTINCT employee_id) < 5 THEN NULL ELSE ROUND(AVG(comp_ratio),4) END AS avg_comp_ratio_safe,
    CASE WHEN COUNT(DISTINCT employee_id) < 5 THEN 'SUPPRESSED: cohort below k=5 minimum' ELSE 'OK' END AS privacy_note
FROM raw_pay_equity_base
WHERE employee_status='Active' AND employment_type='FTE'
GROUP BY department_code, band_code, gender_cohort;

-- 4. Column masking on protected attributes (unmasked only for ACCOUNTADMIN in this demo)
CREATE OR REPLACE MASKING POLICY mask_protected_attr AS (val STRING) RETURNS STRING ->
  CASE WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN') THEN val ELSE 'RESTRICTED' END;
ALTER TABLE raw_employee_demographics MODIFY COLUMN gender_cohort    SET MASKING POLICY mask_protected_attr;
ALTER TABLE raw_employee_demographics MODIFY COLUMN ethnicity_cohort SET MASKING POLICY mask_protected_attr;

-- 5. Governed semantic view: unadjusted vs adjusted gap
CREATE OR REPLACE SEMANTIC VIEW pay_equity_360
  TABLES (pe AS WORKFORCE_ASTRA.RAW.raw_pay_equity_base PRIMARY KEY (employee_id) WITH SYNONYMS ('pay_equity','compensation','demographics'))
  FACTS (pe.base_pay AS base_pay, pe.mid_point AS mid_point, pe.comp_ratio AS comp_ratio)
  DIMENSIONS (pe.employee_id AS employee_id, pe.department_code AS department_code, pe.band_code AS band_code,
              pe.gender_cohort AS gender_cohort, pe.ethnicity_cohort AS ethnicity_cohort, pe.age_band AS age_band,
              pe.location_code AS location_code, pe.employee_status AS employee_status, pe.employment_type AS employment_type)
  METRICS (
    pe.fte_headcount AS COUNT(DISTINCT CASE WHEN pe.employee_status='Active' AND pe.employment_type='FTE' THEN pe.employee_id END),
    pe.avg_base_pay AS AVG(pe.base_pay),
    pe.avg_comp_ratio AS AVG(pe.comp_ratio),
    pe.avg_base_pay_women AS AVG(CASE WHEN pe.gender_cohort='Women' THEN pe.base_pay END),
    pe.avg_base_pay_men   AS AVG(CASE WHEN pe.gender_cohort='Men'   THEN pe.base_pay END),
    pe.unadjusted_gap_pct AS (AVG(CASE WHEN pe.gender_cohort='Women' THEN pe.base_pay END)
                              - AVG(CASE WHEN pe.gender_cohort='Men' THEN pe.base_pay END))
                             / NULLIF(AVG(CASE WHEN pe.gender_cohort='Men' THEN pe.base_pay END), 0),
    pe.adjusted_gap_pct AS (AVG(CASE WHEN pe.gender_cohort='Women' THEN pe.comp_ratio END)
                            - AVG(CASE WHEN pe.gender_cohort='Men' THEN pe.comp_ratio END))
                           / NULLIF(AVG(CASE WHEN pe.gender_cohort='Men' THEN pe.comp_ratio END), 0))
  COMMENT = 'Governed pay-equity metrics: unadjusted (band-mix exposed) vs adjusted (band-normalised comp-ratio)'
  AI_VERIFIED_QUERIES (
    unadjusted_gap AS (QUESTION 'What is the unadjusted pay gap between women and men?'
      SQL 'SELECT unadjusted_gap_pct FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.pay_equity_360 METRICS pe.unadjusted_gap_pct)'),
    adjusted_gap AS (QUESTION 'What is the adjusted pay gap controlling for band?'
      SQL 'SELECT adjusted_gap_pct FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.pay_equity_360 METRICS pe.adjusted_gap_pct)'),
    adjusted_by_dept AS (QUESTION 'What is the adjusted pay gap by department?'
      SQL 'SELECT department_code, adjusted_gap_pct FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.pay_equity_360 DIMENSIONS pe.department_code METRICS pe.adjusted_gap_pct)')
  );

-- Verify:
-- SELECT unadjusted_gap_pct, adjusted_gap_pct FROM SEMANTIC_VIEW(pay_equity_360 METRICS pe.unadjusted_gap_pct, pe.adjusted_gap_pct);
-- SELECT cohort_size, is_suppressed, privacy_note FROM pay_equity_cohorts WHERE is_suppressed ORDER BY cohort_size;
