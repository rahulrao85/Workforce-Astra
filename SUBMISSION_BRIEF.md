# MVP Brief -- paste into the Hack2Skill "Prototype/MVP Brief" field (limit 1024 chars)

Workforce Astra applies the Customer 360 pattern to the enterprise's own workforce: Employee 360
as the internal-stakeholder analog of Customer 360. Off-the-shelf HRMS platforms suffer the exact
problem this track names -- the same question yields different answers across teams -- because
headcount, attrition, and compensation metrics are re-derived ad hoc by HR, Finance, and
Engineering. We encode HRIS, compensation-band, and performance-review data (structured +
unstructured) as a governed Snowflake Semantic View. Ask "how many employees do we have" two
ways -- governed FTE headcount vs. an ungoverned count including contractors -- and get two
different, explainable numbers from the identical underlying data, proving the governance thesis
live. Cortex Analyst answers deterministically with visible SQL; Cortex Search cites the
performance-review evidence behind a flight-risk call; a CoCo agent closes the loop with a
next-best-action (retention alert to the manager). Built entirely through Snowflake CoCo CLI as
modular, reusable skills.

<!-- char count check before pasting: keep under 1024 including spaces -->
