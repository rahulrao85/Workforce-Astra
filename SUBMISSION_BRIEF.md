# MVP Brief -- paste into the Hack2Skill "Prototype/MVP Brief" field (limit 1024 chars)

Workforce Astra applies Customer 360 to a company's own workforce: Employee 360, the
internal-stakeholder analog. HR, Finance and Engineering each re-derive headcount, attrition and comp
metrics ad hoc, so the same question gets a different answer from every team. We encode HRIS,
comp-band, org-hierarchy, performance-review and exit-interview
data (structured + unstructured) as four governed Semantic Views: Employee 360, Org Health, Pay
Equity, Employee Voice. Ask "how many employees do we have" two ways -- governed FTE headcount vs. an
ungoverned count including contractors -- and get two different, explainable numbers (109 vs 127)
from identical data. A Snowpark Python procedure scores those interviews with Cortex sentiment
plus multi-label reason classification against a fixed taxonomy, surfacing the 5 people who are
negative, underpaid and highly rated at once. Cortex Analyst answers all four views with visible SQL
and zero warnings; a 5-tool mock MCP server drafts the fix (dry-run, nothing sent).

<!-- char count check before pasting: keep under 1024 including spaces -->
