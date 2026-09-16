-- Workforce Astra: Cortex Search Service (Unstructured Review Intelligence)
-- Powers the qualitative flight-risk evidence skill by indexing manager review notes.
-- Syntax verified against docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview (Sep-2026).

USE DATABASE WORKFORCE_ASTRA;
USE SCHEMA RAW;

-- 1. Create the Cortex Search Service over raw_performance_reviews.review_text
-- Single-index syntax:
--   ON <search_column>       : Column containing unstructured text to index (review_text)
--   ATTRIBUTES               : Columns available for metadata filtering in queries
--   WAREHOUSE                : Compute warehouse for initial indexing and lag refreshes
--   TARGET_LAG               : Refresh SLA from underlying table
CREATE OR REPLACE CORTEX SEARCH SERVICE review_search_service
  ON review_text
  ATTRIBUTES employee_id, review_period, rating_score
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  COMMENT = 'Cortex Search service over performance review notes for flight-risk and retention evidence'
AS
SELECT
    review_id,
    employee_id,
    review_period,
    rating_score,
    goals_met_pct,
    review_text
FROM WORKFORCE_ASTRA.RAW.raw_performance_reviews;

-- 2. Verify Service Creation & Status
SHOW CORTEX SEARCH SERVICES;
DESCRIBE CORTEX SEARCH SERVICE review_search_service;

-- 3. Test Cortex Search Query using SNOWFLAKE.CORTEX.SEARCH_PREVIEW
-- Example A: Search for flight-risk signals (competing offers, disengagement, workload)
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'review_search_service',
    '{
        "query": "competing offer external opportunities disengaged",
        "columns": ["employee_id", "review_period", "rating_score", "review_text"],
        "limit": 5
    }'
);

-- Example B: Search with attribute filter (e.g., high-performing employees with rating >= 4)
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'review_search_service',
    '{
        "query": "stretch assignment migration project mentorship",
        "columns": ["employee_id", "rating_score", "review_text"],
        "filter": {
            "@gte": {"rating_score": 4}
        },
        "limit": 5
    }'
);

-- Example C: Target a specific candidate (EMP-0042) for review note retrieval (Stretch Evidence Skill)
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'review_search_service',
    '{
        "query": "review notes and performance summary",
        "columns": ["employee_id", "review_period", "rating_score", "review_text"],
        "filter": {
            "@eq": {"employee_id": "EMP-0042"}
        },
        "limit": 1
    }'
);
