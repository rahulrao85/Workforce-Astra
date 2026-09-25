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

-- Employee voice (Phase B1). Its raw table lives HERE, with the other raw tables, not in
-- sql/08_employee_voice.sql -- because the CSV load has to happen after this file and before the
-- semantic views, and a table created two files later simply does not exist yet when COPY INTO
-- runs. One load path, one DDL home per raw table.
CREATE OR REPLACE TABLE raw_voice_transcripts (
    transcript_id   STRING PRIMARY KEY,
    employee_id     STRING,
    interview_type  STRING,   -- 'stay' | 'exit'
    tenure_months   NUMBER,
    interview_date  DATE,
    channel         STRING,
    transcript_text STRING,   -- the unstructured field
    synthetic_note  STRING
);

-- Load: stage the 4 CSVs from data/generate_synthetic_data.py and
-- data/generate_voice_transcripts.py, then COPY INTO each table. The canonical load path is
-- scripts/load_workforce_data.py (or scripts/rebuild_all.py for a full rebuild) -- it owns the
-- single FILE_FORMAT definition and the machine-correct PUT path. Do not hand-write a second one.
