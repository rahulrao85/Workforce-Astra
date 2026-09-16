-- Workforce Astra: raw table DDL for the Employee 360 MVP.
-- Run after the Snowflake account + CoCo CLI are connected (see SETUP.md).

CREATE DATABASE IF NOT EXISTS WORKFORCE_ASTRA;
CREATE SCHEMA IF NOT EXISTS WORKFORCE_ASTRA.RAW;
USE SCHEMA WORKFORCE_ASTRA.RAW;

CREATE OR REPLACE TABLE raw_compensation_bands (
    band_code    STRING PRIMARY KEY,
    band_title   STRING,
    min_base     NUMBER,
    mid_point    NUMBER,
    max_base     NUMBER
);

CREATE OR REPLACE TABLE raw_workday_workers (
    employee_id         STRING PRIMARY KEY,
    first_name          STRING,
    last_name           STRING,
    department_code     STRING,
    band_code           STRING REFERENCES raw_compensation_bands(band_code),
    job_title           STRING,
    hire_date           DATE,
    employee_status     STRING,   -- 'Active' | 'Terminated'
    termination_date    DATE,
    termination_reason  STRING,
    employment_type     STRING,   -- 'FTE' | 'Contractor' -- the deliberate conflict field
    base_pay            NUMBER,
    manager_id          STRING,
    manager_slack_id    STRING
);

CREATE OR REPLACE TABLE raw_performance_reviews (
    review_id       STRING PRIMARY KEY,
    employee_id     STRING REFERENCES raw_workday_workers(employee_id),
    review_period   STRING,
    rating_score    NUMBER,
    goals_met_pct   NUMBER,
    review_text     STRING
);

-- Load: stage the 3 CSVs from data/generate_synthetic_data.py and COPY INTO each
-- table. Ask CoCo CLI to scaffold the exact PUT/COPY INTO commands if current
-- stage syntax needs checking.
