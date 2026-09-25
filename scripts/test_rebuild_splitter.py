"""Offline check of rebuild_all.split_statements. No Snowflake, no network.

The splitter is the riskiest part of the rebuild script: Snowflake stored procedures and
JavaScript handlers use $$ ... $$ bodies full of semicolons, and string literals contain them too.
A naive split on ';' silently truncates every procedure, which would produce a rebuild script that
fails halfway through on a fresh account -- exactly when there is no time to debug.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rebuild_all import SQL_DIR, SQL_FILES, split_statements  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


# ---- torture cases -------------------------------------------------------
cases = [
    (
        "dollar-quoted body with semicolons",
        "SELECT 1; SELECT $$ body; with ; semis $$; SELECT 2;",
        ["SELECT 1", "SELECT $$ body; with ; semis $$", "SELECT 2"],
    ),
    (
        "tagged dollar-quote",
        "CREATE FUNCTION f() RETURNS INT AS $tag$ BEGIN RETURN 1; END $tag$; SELECT 9;",
        ["CREATE FUNCTION f() RETURNS INT AS $tag$ BEGIN RETURN 1; END $tag$", "SELECT 9"],
    ),
    (
        "semicolon inside a string literal",
        "SELECT ';' AS semi; SELECT 2;",
        ["SELECT ';' AS semi", "SELECT 2"],
    ),
    (
        "escaped single quote (doubled)",
        "SELECT 'it''s; fine' AS q; SELECT 2;",
        ["SELECT 'it''s; fine' AS q", "SELECT 2"],
    ),
    (
        "line comments stripped",
        "-- a comment with ; inside\nSELECT 1;\nSELECT 2;",
        ["SELECT 1", "SELECT 2"],
    ),
    (
        "trailing statement without a semicolon",
        "SELECT 1;\nSELECT 2",
        ["SELECT 1", "SELECT 2"],
    ),
]

for name, src, expected in cases:
    got = split_statements(src)
    if got != expected:
        failures.append(f"case {name!r}:\n  expected {expected}\n  got      {got}")
    else:
        print(f"  ok  {name}")

# ---- the real files ------------------------------------------------------
print()
total = 0
for fname in SQL_FILES:
    # SQL_FILES carries a "__LOAD__" sentinel marking where the generated CSV load is spliced in.
    # It is not a file, so skip it here -- the assembled rebuild is covered by the count below.
    if fname == "__LOAD__":
        continue
    path = SQL_DIR / fname
    if not path.exists():
        failures.append(f"missing {path}")
        continue
    sql = path.read_text(encoding="utf-8")
    stmts = split_statements(sql)
    total += len(stmts)

    for s in stmts:
        head = " ".join(s.split())[:120].upper()
        if "CREATE OR REPLACE PROCEDURE" in head or "CREATE PROCEDURE" in head:
            # A truncated procedure would not end in $$ (or contain a LANGUAGE clause).
            check(
                s.rstrip().endswith("$$") or "LANGUAGE" in s,
                f"{fname}: procedure statement looks truncated -> ...{s[-90:]!r}",
            )
        if "SEMANTIC VIEW" in head:
            check(
                "COMMENT" in s or "AI_VERIFIED_QUERIES" in s or "METRICS" in s,
                f"{fname}: semantic view statement looks truncated -> ...{s[-90:]!r}",
            )
        if s.count("'") % 2 != 0:
            failures.append(f"{fname}: odd number of single quotes in: {' '.join(s.split())[:90]}")

    print(f"  {fname:28s} {len(stmts):3d} statements")

print(f"\nTOTAL {total} statements across {len(SQL_FILES) - 1} files "
      f"(+ 1 __LOAD__ sentinel spliced in at assemble time)")

if failures:
    print("\nFAILURES:")
    for f in failures:
        print("  - " + f)
    raise SystemExit(1)
print("\nALL SPLITTER TESTS PASSED")
