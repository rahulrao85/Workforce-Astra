-- Workforce Astra: #4 Employee Voice -- stay/exit interview transcripts -> sentiment + reason
-- classification, computed by a SNOWPARK PYTHON stored procedure.
--
-- Built 25-Sep-2026. Applied through CoCo CLI.
--
-- Why this exists: the track brief asks for unstructured touchpoints "including call transcripts"
-- and sentiment insight, and the formal judging criteria (§9) list Snowpark. This is the only
-- Python that runs INSIDE Snowflake in this project, and the only place we use a Cortex model to
-- turn free text into a governed, testable metric.
--
-- The governance rule still applies: the reason label set is FIXED and versioned. Free-form
-- labels would re-create the "three teams, three answers" problem this project exists to fix.
--
-- All 18 transcripts are hand-authored synthetic text (data/generate_voice_transcripts.py).
-- No real person, employer or interview is involved.
--
-- API NOTE (learned by hitting it): in snowflake-snowpark-python the Cortex entry points are
-- `ai_sentiment()` and `ai_classify()` -- there is no `sentiment()`. `ai_classify` takes a list of
-- label STRINGS (not dicts) and returns {"labels": [...]} with NO confidence field, so this
-- procedure records primary + secondary reason instead of inventing a confidence score.

USE DATABASE WORKFORCE_ASTRA;
USE SCHEMA RAW;

-- ---------------------------------------------------------------------------
-- 1. Raw transcript table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE WORKFORCE_ASTRA.RAW.raw_voice_transcripts (
    transcript_id   STRING PRIMARY KEY,
    employee_id     STRING,
    interview_type  STRING,   -- 'stay' | 'exit'
    tenure_months   NUMBER,
    interview_date  DATE,
    channel         STRING,   -- structured_exit_interview | pulse_followup | ...
    transcript_text STRING,   -- the unstructured field
    synthetic_note  STRING
);

-- ---------------------------------------------------------------------------
-- 2. Stage + load
--    The CSV is produced by data/generate_voice_transcripts.py and PUT to the SAME internal
--    stage the other three tables use, so there is one load path for the whole project.
--    Run sql/01_create_tables.sql, then scripts/load_workforce_data.py, first.
-- ---------------------------------------------------------------------------
PUT file://C:/Users/rahul/AppData/Local/Temp/wf_astra_stage/raw_voice_transcripts.csv
  @WORKFORCE_ASTRA.RAW.workforce_astra_csv_stage AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

-- TRUNCATE + FORCE: a second COPY of the same file is otherwise a silent no-op.
TRUNCATE TABLE IF EXISTS WORKFORCE_ASTRA.RAW.raw_voice_transcripts;
COPY INTO WORKFORCE_ASTRA.RAW.raw_voice_transcripts
  FROM @WORKFORCE_ASTRA.RAW.workforce_astra_csv_stage/raw_voice_transcripts.csv
  FILE_FORMAT = (TYPE = CSV
                 SKIP_HEADER = 1
                 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                 DATE_FORMAT = 'YYYY-MM-DD'
                 EMPTY_FIELD_AS_NULL = TRUE
                 NULL_IF = (''))
  ON_ERROR = ABORT_STATEMENT
  FORCE = TRUE;

-- ---------------------------------------------------------------------------
-- 3. Results table
--    No reason_confidence column: AI_CLASSIFY does not return a score. Storing an invented
--    0..1 "confidence" would be the exact kind of ungoverned number this project is against.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE WORKFORCE_ASTRA.RAW.voice_theme_results (
    transcript_id      STRING PRIMARY KEY,
    employee_id        STRING,
    interview_type     STRING,
    sentiment_score    FLOAT,
    sentiment_label    STRING,
    primary_reason     STRING,
    secondary_reason   STRING,   -- 2nd label from multi-label mode; NULL when only one applies
    flight_risk_signal BOOLEAN,
    scored_at          TIMESTAMP_NTZ
);

-- ---------------------------------------------------------------------------
-- 4. The Snowpark Python procedure
--    SNOWFLAKE.CORTEX.SENTIMENT   -> signed score in [-1, +1]
--    SNOWFLAKE.CORTEX.AI_CLASSIFY -> reasons from the fixed taxonomy below (multi-label)
--    No EAI needed: these are Snowflake-hosted models.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE WORKFORCE_ASTRA.RAW.score_voice_transcripts()
RETURNS TABLE (
  transcript_id      STRING,
  employee_id        STRING,
  interview_type     STRING,
  sentiment_score    FLOAT,
  sentiment_label    STRING,
  primary_reason     STRING,
  secondary_reason   STRING,
  flight_risk_signal BOOLEAN,
  scored_at          TIMESTAMP_NTZ
)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'score'
AS
$$
from snowflake.snowpark import functions as F
from snowflake.snowpark.functions import col, lit, when, ai_classify

# The governed reason taxonomy. Versioned with the results so a future reclassification is
# auditable rather than silent.
CATEGORIES = [
    "compensation",
    "compensation_equity",
    "career_growth",
    "manager",
    "workload_burnout",
    "work_life_balance",
    "org_change",
    "positive_no_issue",
]

# Few-shot anchors, one per category. These are DELIBERATELY NOT drawn from the 18 evaluation
# transcripts -- they are short invented lines. Using the real transcripts as examples would make
# the classification circular and the accuracy claim meaningless.
EXAMPLES = [
    {"input": "the other company offered 25 percent more and i have signed",
     "labels": ["compensation"],
     "explanation": "names a specific external offer and a higher salary as the reason for leaving"},
    {"input": "a colleague on the same band doing the same job is paid more and it was never corrected",
     "labels": ["compensation_equity"],
     "explanation": "compares own pay to an equivalent peer rather than to an outside offer"},
    {"input": "i have been at the same level for three years and was told there is no path to the next one",
     "labels": ["career_growth"],
     "explanation": "describes being stuck at a level with no promotion path"},
    {"input": "my manager left and nobody replaced him so i have had no support for six months",
     "labels": ["manager"],
     "explanation": "the blocker is the absence of managerial support, not pay or workload"},
    {"input": "i have been on call every other week for a year and i am completely exhausted",
     "labels": ["workload_burnout"],
     "explanation": "sustained on-call load and exhaustion rather than a single bad week"},
    {"input": "i need flexible hours for a new caring responsibility and the request was turned down",
     "labels": ["work_life_balance"],
     "explanation": "caring responsibilities and a refused flexibility request"},
    {"input": "after the reorganisation my role was absorbed into another team and i no longer own the project",
     "labels": ["org_change"],
     "explanation": "role and scope changed as a direct result of a reorganisation"},
    {"input": "nothing to report, i am happy here and the work is good",
     "labels": ["positive_no_issue"],
     "explanation": "explicitly raises no problem at all"},
]

TASK_DESCRIPTION = (
    "Classify the reasons given in an employee exit or stay interview transcript. "
    "Use only the supplied category labels. An interview often names more than one reason, so "
    "return every label that genuinely applies, most important first. Do not invent labels."
)

# Reasons that, combined with a negative exit interview, indicate actionable retention risk.
RISK_REASONS = ["compensation", "compensation_equity", "manager", "career_growth"]

# Sentiment band thresholds. Fixed constants, not tuned per run -- a governed band definition.
NEGATIVE_AT = -0.20
POSITIVE_AT = 0.20
RISK_SENTIMENT_AT = -0.10

RESULTS_TABLE = "WORKFORCE_ASTRA.RAW.voice_theme_results"
SOURCE_TABLE = "WORKFORCE_ASTRA.RAW.raw_voice_transcripts"


def score(session):
    src = session.table(SOURCE_TABLE)

    # 1 + 2. Cortex sentiment and classification, evaluated in Snowflake on the raw text.
    #
    # Sentiment: call SNOWFLAKE.CORTEX.SENTIMENT directly rather than via the Snowpark helper
    # `ai_sentiment()`. The helper resolves to AI_SENTIMENT$V2, which returns an OBJECT
    # {"categories":[{"name":"overall","sentiment":"mixed"}]} -- a LABEL, not a number -- so
    # casting it to FLOAT fails with SQL compilation error 001007. The plain SENTIMENT function
    # returns the signed score in [-1, +1] that the threshold bands below need.
    scored = (
        src
        .with_column("sentiment_score",
                     F.call_function("SNOWFLAKE.CORTEX.SENTIMENT",
                                     col("transcript_text")).cast("float"))
        .with_column("_cls", ai_classify(
            col("transcript_text"),
            CATEGORIES,
            task_description=TASK_DESCRIPTION,
            output_mode="multi",
            examples=EXAMPLES,
        ))
    )

    labels = col("_cls")["labels"]

    # 3. Governed derivations.
    #    element_at() on a VARIANT array yields VARIANT and current_timestamp() is TIMESTAMP_LTZ,
    #    so both are cast explicitly -- otherwise the write succeeds but the RETURNS TABLE
    #    contract fails with "data type of returned table does not match expected returned table
    #    type" after the work is already done.
    out = (
        scored
        .with_column("primary_reason", F.element_at(labels, 0).cast("string"))
        .with_column("secondary_reason", F.element_at(labels, 1).cast("string"))
        .with_column(
            "sentiment_label",
            when(col("sentiment_score") >= F.lit(POSITIVE_AT), lit("positive"))
            .when(col("sentiment_score") <= F.lit(NEGATIVE_AT), lit("negative"))
            .otherwise(lit("neutral")),
        )
        .with_column(
            "flight_risk_signal",
            (col("interview_type") == lit("exit"))
            & (col("sentiment_score") < F.lit(RISK_SENTIMENT_AT))
            & (col("primary_reason").isin(RISK_REASONS)),
        )
        .with_column("scored_at", F.current_timestamp().cast("timestamp_ntz"))
        .select(
            "transcript_id", "employee_id", "interview_type", "sentiment_score",
            "sentiment_label", "primary_reason", "secondary_reason",
            "flight_risk_signal", "scored_at",
        )
    )

    # Idempotent: full overwrite, so a scheduled re-run can never leave stale rows behind.
    out.write.mode("overwrite").save_as_table(RESULTS_TABLE)
    return out
$$;

-- ---------------------------------------------------------------------------
-- 5. Link negative voice signal to the structured flight-risk evidence
--    The whole point: an exit interview that reads negative AND names a fixable reason
--    (pay / manager / progression), corroborated by the same person's performance-review text.
--    Grain: one row per transcript. raw_performance_reviews is one row per employee, so this
--    join cannot fan out -- same single-grain rule the other views obey.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW WORKFORCE_ASTRA.RAW.voice_risk_360 AS
SELECT v.transcript_id,
       v.employee_id,
       v.interview_type,
       v.sentiment_score,
       v.sentiment_label,
       v.primary_reason,
       v.secondary_reason,
       v.flight_risk_signal,
       t.transcript_text,
       w.department_code,
       w.band_code,
       w.employment_type,
       w.base_pay,
       c.mid_point,
       ROUND(w.base_pay / NULLIF(c.mid_point, 0), 4) AS comp_ratio,
       r.rating_score,
       r.goals_met_pct,
       r.review_text,
       -- The cross-signal: a voice complaint that lands on someone already underpaid and
       -- highly rated is the highest-value retention case in the whole dataset.
       (v.flight_risk_signal
         AND w.base_pay / NULLIF(c.mid_point, 0) < 0.85
         AND r.rating_score >= 4) AS corroborated_flight_risk
FROM WORKFORCE_ASTRA.RAW.voice_theme_results v
-- The scored result does not carry the raw text, so join it back: the whole point of this view
-- is to show the verbatim words next to the structured evidence. 1:1 on transcript_id.
JOIN WORKFORCE_ASTRA.RAW.raw_voice_transcripts   t ON t.transcript_id = v.transcript_id
JOIN WORKFORCE_ASTRA.RAW.raw_workday_workers      w ON w.employee_id   = v.employee_id
JOIN WORKFORCE_ASTRA.RAW.raw_compensation_bands   c ON c.band_code     = w.band_code
LEFT JOIN WORKFORCE_ASTRA.RAW.raw_performance_reviews r ON r.employee_id = v.employee_id;

-- ---------------------------------------------------------------------------
-- 6. Governed semantic view
-- ---------------------------------------------------------------------------
CREATE OR REPLACE SEMANTIC VIEW WORKFORCE_ASTRA.RAW.employee_voice_360
  TABLES (
    voice AS WORKFORCE_ASTRA.RAW.voice_theme_results PRIMARY KEY (transcript_id)
      WITH SYNONYMS ('employee voice','exit interview','stay interview','transcripts','sentiment')
  )
  FACTS (
    voice.sentiment_score AS sentiment_score
  )
  DIMENSIONS (
    voice.employee_id        AS employee_id,
    voice.interview_type     AS interview_type,
    voice.sentiment_label    AS sentiment_label,
    voice.primary_reason     AS primary_reason,
    voice.secondary_reason   AS secondary_reason,
    voice.flight_risk_signal AS flight_risk_signal
  )
  METRICS (
    voice.transcript_count AS COUNT(DISTINCT voice.transcript_id),
    voice.exit_transcript_count AS
      COUNT(DISTINCT CASE WHEN voice.interview_type = 'exit' THEN voice.transcript_id END),
    voice.stay_transcript_count AS
      COUNT(DISTINCT CASE WHEN voice.interview_type = 'stay' THEN voice.transcript_id END),
    voice.negative_transcript_count AS
      COUNT(DISTINCT CASE WHEN voice.sentiment_label = 'negative' THEN voice.transcript_id END),
    voice.multi_reason_transcript_count AS
      COUNT(DISTINCT CASE WHEN voice.secondary_reason IS NOT NULL THEN voice.transcript_id END),
    voice.flight_risk_signal_count AS
      COUNT(DISTINCT CASE WHEN voice.flight_risk_signal THEN voice.transcript_id END),
    voice.avg_sentiment AS AVG(voice.sentiment_score)
  )
  COMMENT = 'Governed employee voice: stay/exit interview sentiment and reason classification'
  AI_VERIFIED_QUERIES (
    negative_share AS (
      QUESTION 'How many exit interviews are negative in sentiment?'
      SQL 'SELECT negative_transcript_count FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_voice_360 METRICS voice.negative_transcript_count)'
    ),
    reasons AS (
      QUESTION 'What is the most common reason employees give?'
      SQL 'SELECT primary_reason, transcript_count FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_voice_360 DIMENSIONS voice.primary_reason METRICS voice.transcript_count) ORDER BY transcript_count DESC'
    ),
    reasons_with_sentiment AS (
      QUESTION 'Which reasons are associated with the most negative average sentiment?'
      SQL 'SELECT primary_reason, interview_type, avg_sentiment FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_voice_360 DIMENSIONS voice.primary_reason, voice.interview_type METRICS voice.avg_sentiment) ORDER BY avg_sentiment ASC'
    ),
    flight_risk AS (
      QUESTION 'How many interviews raise a flight-risk signal?'
      SQL 'SELECT flight_risk_signal_count FROM SEMANTIC_VIEW(WORKFORCE_ASTRA.RAW.employee_voice_360 METRICS voice.flight_risk_signal_count)'
    )
  );

-- ---------------------------------------------------------------------------
-- 7. Verify
--    CALL WORKFORCE_ASTRA.RAW.score_voice_transcripts();       -- expect 18 rows
--    SELECT interview_type, sentiment_label, primary_reason, COUNT(*) AS n
--      FROM WORKFORCE_ASTRA.RAW.voice_theme_results GROUP BY 1,2,3 ORDER BY 1,2,3;
--    SELECT * FROM WORKFORCE_ASTRA.RAW.voice_risk_360 WHERE corroborated_flight_risk;
--    CALL WORKFORCE_ASTRA.RAW.run_metric_tests();               -- expect 16/16
