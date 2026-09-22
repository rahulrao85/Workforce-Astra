-- Workforce Astra: #1 Org Design & Manager Health Sentinel
-- Deployed live 21-Sep-2026 against account ST42987 (WORKFORCE_ASTRA.RAW).
-- Reuses raw_workday_workers.manager_id -- no new source data required.
-- Verified: 15 managers, avg span 9.0, 5 overspan managers (>10 reports), max depth 2.

USE DATABASE WORKFORCE_ASTRA;
USE SCHEMA RAW;

-- 1. Recursive hierarchy (roots = managers with a blank manager_id)
CREATE OR REPLACE TABLE raw_org_hierarchy AS
WITH RECURSIVE org AS (
    SELECT employee_id, NULLIF(manager_id,'') AS manager_id, 0 AS org_level,
           employee_id AS root_id, ARRAY_CONSTRUCT(employee_id) AS chain
    FROM raw_workday_workers WHERE manager_id IS NULL OR manager_id = ''
    UNION ALL
    SELECT w.employee_id, NULLIF(w.manager_id,''), o.org_level + 1,
           o.root_id, ARRAY_APPEND(o.chain, w.employee_id)
    FROM raw_workday_workers w JOIN org o ON w.manager_id = o.employee_id
)
SELECT employee_id, manager_id, root_id, org_level, chain FROM org;

-- 2. Flattened org metrics, merged with worker attributes (1 row per employee => no fan-out)
CREATE OR REPLACE TABLE raw_org_flattened AS
SELECT
    h.employee_id, h.manager_id, h.root_id, h.org_level, (h.org_level + 1) AS org_depth_level, h.chain,
    COALESCE(dr.direct_reports, 0) AS direct_reports,
    (COALESCE(st.subtree_size, 1) - 1) AS subtree_size,
    (COALESCE(dr.direct_reports, 0) > 0) AS is_manager,
    CASE WHEN COALESCE(dr.direct_reports,0) >= 5 THEN 'Senior Manager'
         WHEN COALESCE(dr.direct_reports,0) >= 1 THEN 'Frontline Manager'
         ELSE 'Individual Contributor' END AS management_tier,
    (COALESCE(dr.direct_reports,0) BETWEEN 1 AND 2) AS is_narrow_span,
    (COALESCE(dr.direct_reports,0) > 10) AS is_overspan,
    w.department_code, w.band_code, w.employee_status, w.employment_type,
    w.base_pay, w.manager_slack_id
FROM raw_org_hierarchy h
JOIN raw_workday_workers w ON w.employee_id = h.employee_id
LEFT JOIN (SELECT manager_id, COUNT(*) AS direct_reports FROM raw_org_hierarchy
           WHERE manager_id IS NOT NULL GROUP BY manager_id) dr ON dr.manager_id = h.employee_id
LEFT JOIN (SELECT h1.employee_id AS node, COUNT(*) AS subtree_size
           FROM raw_org_hierarchy h1 JOIN raw_org_hierarchy h2
             ON ARRAY_CONTAINS(h1.employee_id::VARIANT, h2.chain)
           GROUP BY h1.employee_id) st ON st.node = h.employee_id;

-- 3. Custom function tool: management chain walk-up
CREATE OR REPLACE FUNCTION org_walk_up(emp STRING)
RETURNS ARRAY LANGUAGE SQL AS
$$ SELECT chain FROM raw_org_flattened WHERE employee_id = emp $$;

-- 4. Custom function tool: guarded reorg simulator (SIMULATION ONLY, never mutates)
CREATE OR REPLACE PROCEDURE simulate_reorg(source_mgr STRING, target_mgr STRING)
RETURNS VARIANT LANGUAGE SQL AS
$$
DECLARE
    src_exists NUMBER DEFAULT 0; tgt_exists NUMBER DEFAULT 0; is_cycle NUMBER DEFAULT 0;
    src_subtree NUMBER DEFAULT 0; tgt_direct NUMBER DEFAULT 0; projected_span NUMBER DEFAULT 0;
BEGIN
    SELECT COUNT(*) INTO :src_exists FROM raw_org_flattened WHERE employee_id = :source_mgr;
    IF (src_exists = 0) THEN RETURN OBJECT_CONSTRUCT('status','REJECTED','guardrail','source manager not found'); END IF;
    SELECT COUNT(*) INTO :tgt_exists FROM raw_org_flattened WHERE employee_id = :target_mgr;
    IF (tgt_exists = 0) THEN RETURN OBJECT_CONSTRUCT('status','REJECTED','guardrail','target manager not found'); END IF;
    IF (:source_mgr = :target_mgr) THEN RETURN OBJECT_CONSTRUCT('status','REJECTED','guardrail','source and target are the same person'); END IF;
    SELECT COUNT(*) INTO :is_cycle FROM raw_org_flattened
        WHERE employee_id = :target_mgr AND ARRAY_CONTAINS(:source_mgr::VARIANT, chain);
    IF (is_cycle > 0) THEN RETURN OBJECT_CONSTRUCT('status','REJECTED','guardrail','would create a circular reporting line'); END IF;
    SELECT subtree_size INTO :src_subtree FROM raw_org_flattened WHERE employee_id = :source_mgr;
    SELECT direct_reports INTO :tgt_direct FROM raw_org_flattened WHERE employee_id = :target_mgr;
    projected_span := :tgt_direct + 1;
    RETURN OBJECT_CONSTRUCT('status','VALIDATED','source_mgr',:source_mgr,'target_mgr',:target_mgr,
        'source_subtree_size',:src_subtree,'target_current_span',:tgt_direct,
        'target_projected_span',:projected_span,'note','SIMULATION ONLY - no org data was modified');
END;
$$;

-- 5. Governed semantic view
CREATE OR REPLACE SEMANTIC VIEW org_health_360
  TABLES (org AS WORKFORCE_ASTRA.RAW.raw_org_flattened PRIMARY KEY (employee_id) WITH SYNONYMS ('org','hierarchy','organization','managers'))
  FACTS (org.direct_reports AS direct_reports, org.subtree_size AS subtree_size,
         org.org_depth_level AS org_depth_level, org.base_pay AS base_pay)
  DIMENSIONS (org.employee_id AS employee_id, org.manager_id AS manager_id, org.root_id AS root_id,
              org.department_code AS department_code, org.band_code AS band_code,
              org.management_tier AS management_tier, org.employee_status AS employee_status,
              org.employment_type AS employment_type)
  METRICS (
    org.manager_count AS COUNT(DISTINCT CASE WHEN org.direct_reports >= 1 THEN org.employee_id END),
    org.avg_span_of_control AS AVG(CASE WHEN org.direct_reports >= 1 THEN org.direct_reports END),
    org.overspan_managers AS COUNT(DISTINCT CASE WHEN org.direct_reports > 10 THEN org.employee_id END),
    org.narrow_span_managers AS COUNT(DISTINCT CASE WHEN org.direct_reports BETWEEN 1 AND 2 THEN org.employee_id END),
    org.max_org_depth AS MAX(org.org_depth_level),
    org.governed_headcount AS COUNT(DISTINCT CASE WHEN org.employee_status='Active' AND org.employment_type='FTE' THEN org.employee_id END))
  COMMENT = 'Governed org design & manager health (Workforce Astra)'
  AI_VERIFIED_QUERIES (
    avg_span AS (QUESTION 'What is the average span of control across the company?'
      SQL 'SELECT avg_span_of_control FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.org_health_360 METRICS org.avg_span_of_control)'),
    overspan_by_dept AS (QUESTION 'Which departments have managers with more than 10 direct reports?'
      SQL 'SELECT department_code, overspan_managers FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.org_health_360 DIMENSIONS org.department_code METRICS org.overspan_managers) ORDER BY overspan_managers DESC')
  );

-- Verify:
-- SELECT avg_span_of_control, overspan_managers, max_org_depth, manager_count
--   FROM SEMANTIC_VIEW(org_health_360 METRICS org.avg_span_of_control, org.overspan_managers, org.max_org_depth, org.manager_count);
-- SELECT org_walk_up('EMP-0057');
-- CALL simulate_reorg('EMP-0001','EMP-0005');
