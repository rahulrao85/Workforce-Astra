-- Workforce Astra: stage + load the 3 synthetic CSVs into WORKFORCE_ASTRA.RAW.
--
-- ⚠️ SUPERSEDED (25-Sep-2026) — HISTORICAL, DO NOT RUN BY HAND. This file predates the employee-voice
-- tables and covers only 3 of the 4 CSVs; the raw_voice_transcripts table added in Phase B1 is not
-- loaded here. It is kept for provenance only.
--
-- The CANONICAL load path is scripts/load_workforce_data.py (single FILE_FORMAT definition, single
-- load path, all 4 CSVs), or scripts/rebuild_all.py for a full rebuild. Both regenerate this file's
-- content with a machine-correct PUT path. A second hand-run load script is exactly how two load
-- paths drift and the demo silently shows stale data.
--
-- CANONICAL LOAD SCRIPT. Owned by the workforce-astra-data-gen skill
-- (.cortex/skills/workforce-astra-data-gen/SKILL.md).
--
--   COORDINATION NOTE: scripts/load_workforce_data.py regenerates this exact SQL with
--   a machine-correct PUT path. If you are editing this file, edit the builder in that
--   script too -- do not fork a second load script, or the two will drift.
--
-- Run sql/01_create_tables.sql first (creates db/schema/tables).
-- Then: python scripts/load_workforce_data.py    (generates CSVs + prints this SQL)
--
-- The CSV staging path below has NO SPACES on purpose: this workspace lives under
-- "F:\AGENTIC WORLD" and a space breaks the file:// URI that PUT parses. The loader
-- script copies the CSVs to the temp dir referenced here before PUTting.

USE DATABASE WORKFORCE_ASTRA;
USE SCHEMA RAW;

-- One file format for all three CSVs:
--   SKIP_HEADER=1                  -- generator writes a header row
--   EMPTY_FIELD_AS_NULL / NULL_IF  -- blank termination_date must land as NULL, not ''
--   DATE_FORMAT                    -- ISO dates from the generator
CREATE OR REPLACE STAGE workforce_astra_csv_stage
  FILE_FORMAT = (TYPE = CSV
                 SKIP_HEADER = 1
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 DATE_FORMAT = 'YYYY-MM-DD'
                 EMPTY_FIELD_AS_NULL = TRUE
                 NULL_IF = (''));

-- Path is produced by scripts/load_workforce_data.py (tempfile.gettempdir()/wf_astra_stage).
-- On Windows the form is file://C:/... ; on Linux/macOS it is file:///home/...
PUT file://C:/Users/rahul/AppData/Local/Temp/wf_astra_stage/raw_compensation_bands.csv @workforce_astra_csv_stage AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
PUT file://C:/Users/rahul/AppData/Local/Temp/wf_astra_stage/raw_workday_workers.csv @workforce_astra_csv_stage AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
PUT file://C:/Users/rahul/AppData/Local/Temp/wf_astra_stage/raw_performance_reviews.csv @workforce_astra_csv_stage AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

-- TRUNCATE + FORCE: without FORCE, a second COPY INTO of the same files is a no-op
-- (Snowflake remembers the load) and the demo quietly shows stale data.

TRUNCATE TABLE IF EXISTS raw_compensation_bands;
COPY INTO raw_compensation_bands
  FROM @workforce_astra_csv_stage/raw_compensation_bands.csv
  FILE_FORMAT = (TYPE = CSV
                 SKIP_HEADER = 1
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 DATE_FORMAT = 'YYYY-MM-DD'
                 EMPTY_FIELD_AS_NULL = TRUE
                 NULL_IF = (''))
  ON_ERROR = ABORT_STATEMENT
  FORCE = TRUE;

TRUNCATE TABLE IF EXISTS raw_workday_workers;
COPY INTO raw_workday_workers
  FROM @workforce_astra_csv_stage/raw_workday_workers.csv
  FILE_FORMAT = (TYPE = CSV
                 SKIP_HEADER = 1
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 DATE_FORMAT = 'YYYY-MM-DD'
                 EMPTY_FIELD_AS_NULL = TRUE
                 NULL_IF = (''))
  ON_ERROR = ABORT_STATEMENT
  FORCE = TRUE;

TRUNCATE TABLE IF EXISTS raw_performance_reviews;
COPY INTO raw_performance_reviews
  FROM @workforce_astra_csv_stage/raw_performance_reviews.csv
  FILE_FORMAT = (TYPE = CSV
                 SKIP_HEADER = 1
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 DATE_FORMAT = 'YYYY-MM-DD'
                 EMPTY_FIELD_AS_NULL = TRUE
                 NULL_IF = (''))
  ON_ERROR = ABORT_STATEMENT
  FORCE = TRUE;

-- Load receipt: 5 / 150 / 127
SELECT 'raw_compensation_bands' AS table_name, COUNT(*) AS row_count FROM raw_compensation_bands
UNION ALL SELECT 'raw_workday_workers',      COUNT(*) FROM raw_workday_workers
UNION ALL SELECT 'raw_performance_reviews',  COUNT(*) FROM raw_performance_reviews;

-- THE PROOF POINT for the demo's cold open. These two numbers MUST differ:
-- naive counts contractors as employees, the governed metric does not.
SELECT
  COUNT(*)                                  AS naive_active_headcount,
  COUNT_IF(employment_type = 'FTE')         AS governed_active_headcount,
  COUNT(*) - COUNT_IF(employment_type = 'FTE') AS delta
FROM raw_workday_workers
WHERE employee_status = 'Active';
