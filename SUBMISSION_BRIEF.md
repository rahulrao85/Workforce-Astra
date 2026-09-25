# MVP Brief -- paste into the Hack2Skill "Prototype/MVP Brief" field (limit 1024 chars)

Workforce Astra applies the Customer 360 pattern to a company's own workforce: Employee 360, the
internal-stakeholder analog. Off-the-shelf HRMS suffer the problem this track names -- the same
question yields different answers across teams -- because headcount, attrition and comp metrics are
re-derived ad hoc by HR, Finance and Engineering. We encode HRIS, comp-band, performance-review and
org-hierarchy data (structured + unstructured) as three governed Semantic Views: Employee 360, Org
Health, Pay Equity. Ask "how many employees do we have" two ways -- governed FTE headcount vs. an
ungoverned count including contractors -- and get two different, explainable numbers (109 vs 127)
from identical data, proving the thesis live. Cortex Analyst answers all three with visible SQL and
zero warnings; a Cortex Search service indexes the 127 review notes behind a flight-risk call; a
5-tool mock MCP server drafts the retention action (dry-run, nothing sent). Built through Snowflake
CoCo CLI as modular, reusable skills.

<!-- char count check before pasting: keep under 1024 including spaces -->
