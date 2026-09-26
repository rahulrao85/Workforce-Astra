# Deck content: slide by slide (draft for the Hack2Skill template)

The official template hasn't arrived yet. This follows the usual Hack2Skill slide order. When the template lands, paste each block into the matching slide and drop or merge any slide the template doesn't have. Export to **PDF under 5 MB** (compress screenshots to about 1600 px wide JPG).

All numbers are live Snowflake results on synthetic data, verified 26-Sep-2026. Keep the phrase "synthetic data" visible somewhere on the deck, because the T&Cs forbid misleading claims.

---

### Slide 1: Title
- **Workforce Astra**: Employee 360 on Snowflake
- Challenge: Customer 360 and Next Best Action Engine
- Team: Rahul Rao (solo)
- Snowflake CoCo CLI Hackathon 2026, GCC Edition

### Slide 2: The problem
- HR, Finance and Engineering each re-derive headcount, attrition and pay metrics ad hoc.
- Ask "how many employees do we have?" and you get a different answer from each team, from the same data.
- The cost: board packs that disagree, pay-equity findings nobody trusts, and exit interviews that are read once and never joined to anything.
- In a GCC this is multiplied, because the parent company, the centre and the vendors each keep their own definitions.

### Slide 3: The idea
- Customer 360 unifies everything about a customer. **Employee 360 does the same for your own people.**
- Encode HRIS, comp-band, org, performance-review and interview data as **five governed Semantic Views**: Employee 360, Org Health, Pay Equity, Employee Voice, Band Health.
- Each metric has one definition, a named owner and a golden-value test.
- Next best action: the system **drafts** the manager alert or band review (dry-run) and a human decides.

### Slide 4: Proof point (the headline slide)
- Same data, same moment:
  - **109**: governed full-time-employee headcount
  - **127**: an ungoverned "active" count that silently includes 18 contractors
- The semantic view makes the governed answer the default. Every tool (CLI, portal, Cortex Analyst) resolves to the same number.
- *Visual:* the portal's "Compare: Governed vs Naive" screenshot.

### Slide 5: What it finds
Four findings on the synthetic data:
- **Pay equity:** the raw gender gap is −16.8%; adjusted for band and department it's −2.8%. Cohorts under 5 people are suppressed automatically (39 of 44).
- **Band architecture:** 0 red circles, but **37 of 150 (24.7%) are paid below their own band minimum**. The M1/IC5 ranges overlap 71%.
- **Employee voice:** 18 interviews scored by a Snowpark procedure. Career growth is the top reason. **5 corroborated flight risks**: negative sentiment, comp-ratio under 0.85, rated 4+.
- **Org health:** average span of control 9.0, 5 overspan managers.
- Footnote: we placed 5 of the 18 synthetic interviews on the risk profile deliberately, so the join has something to find.

### Slide 6: Features (MVP, all live)
| Capability | Snowflake feature |
|---|---|
| Five governed semantic views, 29 owned metrics | Semantic Views |
| Plain-English questions with visible SQL, 0 warnings | Cortex Analyst |
| Search over 127 review notes | Cortex Search |
| Interview sentiment and multi-label reason classification | Snowpark Python + Cortex AI SQL (SENTIMENT, AI_CLASSIFY) |
| Employee 360 portal: compare, flight-risk, pay equity, band auditor, voice | Streamlit in Snowflake |
| Daily regression, weekly pay-drift and quarterly band reviews | Tasks |
| 25 golden-value tests (10 pin Cortex model behaviour) | Stored procedures |
| Two reusable CoCo skills: data-gen and governance-check | CoCo CLI |
| Six-tool action layer (Slack/Workday drafts), dry-run by default | MCP server (mocked) |

### Slide 7: Process flow
```
Synthetic HRIS + bands + reviews + interviews
      │  $workforce-astra-data-gen  (CoCo skill: generate → verify invariants → stage → load)
      ▼
RAW tables in Snowflake ──► Snowpark proc scores interviews (Cortex SENTIMENT + AI_CLASSIFY)
      │
      ▼
Five governed Semantic Views  ◄── metric registry (owner, definition, golden value)
      │                                   ▲
      │                                   └── $workforce-astra-governance-check (CoCo skill) + Tasks
      ▼
Consumers: CoCo CLI · Cortex Analyst · Streamlit portal · landing page snapshot
      │
      ▼
Next best action: MCP tool drafts the Slack alert / band review (dry_run=true) → human approves
```

### Slide 8: Architecture
- **Inside Snowflake:** RAW tables → Snowpark scoring → Semantic Views → Cortex Analyst / Cortex Search → Streamlit portal. Tasks run tests and drift checks and write GOVERNANCE_ALERTS.
- **Around it:** CoCo CLI (build and operate through two skills), the MCP server (mocked actions), and the static landing page (dated snapshot exported by script).
- *Visual:* redraw the flow above as boxes, in blue and white.

### Slide 9: Governance and guardrails
- 29 metrics in the registry, **0 unowned**. 25/25 tests pass.
- Model-dependent tests: a Cortex model change trips a test instead of silently moving a number.
- Privacy: small-cohort suppression (n < 5). The data is synthetic only.
- **No automated pay decisions:** the band auditor reports and never proposes a number, and the MCP tool can't be asked for one.
- Actions are drafts only (dry-run). Nothing is sent to Slack or Workday.

### Slide 10: Screenshots of the MVP
Take these from the portal and the terminal during the recording session:
1. The CoCo terminal showing `$workforce-astra-governance-check` → 25/25 PASS
2. The portal Compare view (109 vs 127)
3. The Band Auditor ("37 of 150 below minimum")
4. The Employee Voice cross-signal table with EMP-0031 expanded
5. A Cortex Analyst answer with SQL

### Slide 11: Impact and relevance
- One number per metric across HR, Finance and Engineering: fewer reconciliation cycles and faster board reporting.
- Pay-equity and band findings are defensible, because they're adjusted, suppressed and audited.
- Exit and stay interviews become a joined signal instead of a PDF nobody reads.
- It fits GCCs directly: one governed layer across the parent company, the centre and vendors.

### Slide 12: Cost and scale
- It runs on standard Snowflake. The portal compute pool is the main standing cost and is suspended when idle.
- The build and rehearsal were done inside a trial account's credit.
- It scales with the warehouse size. The semantic views and tests don't change as headcount grows.

### Slide 13: What's next
- Replace the mocked MCP tools with real Slack and Workday connectors, behind approval.
- A Marketplace listing of the synthetic dataset and semantic views as a starter kit.
- More domains: learning, hiring funnel, internal mobility.
- Row-level security by manager hierarchy.

### Slide 14: Links
- Demo video: *(unlisted YouTube link)*
- GitHub: https://github.com/rahulrao85/Workforce-Astra
- Live page: https://workforce-astra.rahulrao.in
- Datasets: all synthetic, generated by `scripts/` in the repo. See README → Datasets and licences.
