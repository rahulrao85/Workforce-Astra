# MVP Brief -- paste into the Hack2Skill "Prototype/MVP Brief" field (limit 1024 chars)

Workforce Astra applies Customer 360 to a company's own workforce: Employee 360, the internal
analog. HR, Finance and Engineering each re-derive headcount, attrition and comp metrics ad hoc, so
the same question gets a different answer from each. We encode HRIS, comp-band, org,
performance-review and exit-interview
data (structured + unstructured) as five governed Views: Employee 360, Org Health, Pay Equity,
Employee Voice, Band Health. Ask "how many employees do we have" two ways -- governed FTE headcount
vs. an ungoverned count including contractors -- and get two different numbers (109 vs 127) from
identical data. A Snowpark Python procedure scores those interviews with Cortex sentiment and
multi-label reason classification, surfacing the 5 who are negative, underpaid and highly rated.
A band auditor reports the 37 staff below their own range minimum but proposes no number.
Cortex Analyst answers all five with visible SQL, zero warnings; a 6-tool mock MCP server drafts
the fix (dry-run, nothing sent).

<!-- char count check before pasting: keep under 1024 including spaces -->
