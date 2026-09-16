# Setup — Critical Path (do this before anything else)

Identical critical path regardless of which track — no CoCo CLI, SnowSQL, or Snowflake account
exists on this machine yet (checked 16-Sep-2026).

## 1. Get the Snowflake account -- CONFIRMED BLOCKER, not a nice-to-have
Verified directly against docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli today:

> "CoCo CLI is not available on standard Snowflake trial accounts (for example, accounts
> created at trial.snowflake.com). To use CoCo CLI, you need either a paid Snowflake account
> or the dedicated CoCo CLI trial."

This means signing up at the generic trial.snowflake.com **will not work** -- CoCo CLI simply
won't run on that account, no matter what Cortex features you try to enable. You need the
dedicated CoCo CLI trial link.
- **Check the Hack2Skill participant dashboard** (Resources / Perks / Workshops tab) for that
  dedicated link tied to this hackathon -- it comes with $400 credit, no card needed. Check
  emails from `support+cococlihack@hack2skill.com` if it's not obviously in the dashboard.
- If you can't find it, the CoCo CLI docs page above links to "a free CoCo CLI trial" directly --
  that's the fallback if the hackathon-specific one doesn't surface in time.
- You need to do this step yourself -- account creation needs your email/org details, and I
  won't enter payment info even if a card is requested.

## 2. Install CoCo CLI
- Docs: `docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli`
- Verify the actual current install/auth commands against that page or `coco --help` once
  installed — don't trust a remembered command name, the CLI is new enough that syntax shifts.
- Connect it to the account from step 1.

## 3. Confirm Cortex Analyst and Cortex Search are enabled
- Run a trivial query through CoCo CLI or Snowsight before building anything on top. If either
  isn't enabled on your account/region, that's a blocker to resolve first.

## Once this is done
Move to `data/generate_synthetic_data.py` and `sql/`. Kick off the OpenCode/Antigravity prompts
in `PROMPTS_FOR_AGENTS.md` in parallel — they don't need the live account to start.
