r"""
Workforce Astra -- ONE-COMMAND REBUILD for a fresh Snowflake trial account.

WHY THIS EXISTS
    T&C 4.6: finalists get a new trial account if theirs expired. This project's trial is
    estimated to expire ~11-Oct-2026, which is BEFORE the 27-30 Oct live grand finale, so
    rebuilding the entire solution on a fresh account in minutes is a hard requirement, not a
    nice-to-have. The alternative is arriving at the finale with nothing running.

WHAT IT DOES, IN ORDER
    0. Regenerates and verifies all 4 synthetic CSVs (workers, bands, reviews, voice transcripts).
    1. Copies them to a staging directory whose path has NO SPACES (this workspace lives under
       "F:\AGENTIC WORLD", and a space breaks the file:// URI that PUT parses).
    2. Concatenates, in dependency order, the canonical SQL in sql/ -- with the database name
       substituted so the whole solution can be built into ANY database.
    3. Applies it with one of two backends.
    4. Runs the Snowpark scoring procedure, the band review, and the regression suite.
    5. Prints the governed numbers so you can eyeball them against README.md.

BACKENDS -- AND WHY THERE ARE TWO
    --backend snow  (default) applies the whole script in ONE `snow sql -f` process. Fast, and it
                    is the only practical way to apply ~120 statements including stored procedures
                    with $$ bodies.
    --backend coco  applies the script one statement at a time through
                    `cortex -c <conn> -p "<statement>" --bypass`. Much slower, but it keeps CoCo
                    CLI in the loop for every statement, which is the evidence the hackathon asks
                    for. Use this when the record needs to show CoCo running the build.

    Honest note: CoCo's `sql_execute` tool refuses any prompt containing more than one SQL
    statement, so a 120-statement rebuild genuinely cannot be driven through a single CoCo call.
    That is why the snow backend exists. Neither backend is a shortcut around CoCo -- the canonical
    SQL in sql/ is itself the artefact that CoCo authored and applied statement by statement
    during development.

USAGE
    # rebuild into the real database (the default)
    python scripts/rebuild_all.py

    # rebuild into a scratch database, verify, then drop it
    python scripts/rebuild_all.py --database WORKFORCE_ASTRA_REBUILD_TEST --drop --yes

    # drive it through CoCo CLI instead
    python scripts/rebuild_all.py --backend coco

    # just show the SQL, run nothing
    python scripts/rebuild_all.py --print-sql

    # tear down the scratch database when finished
    python scripts/rebuild_all.py --database WORKFORCE_ASTRA_REBUILD_TEST --drop-only --yes

DEPENDENCIES
    snow backend : `uvx --from snowflake-cli` (or snow on PATH) + faker
    coco backend : `cortex` on PATH + faker
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
DATA_DIR = ROOT / "data"

REAL_DB = "WORKFORCE_ASTRA"
DEFAULT_CONNECTION = "workforce-astra-keypair"
STAGE_NAME = "workforce_astra_csv_stage"

GENERATORS = [
    DATA_DIR / "generate_synthetic_data.py",
    DATA_DIR / "generate_voice_transcripts.py",
]

# The 4 CSVs, in load order. bands <- workers <- reviews, then transcripts.
CSVS = [
    "raw_compensation_bands.csv",
    "raw_workday_workers.csv",
    "raw_performance_reviews.csv",
    "raw_voice_transcripts.csv",
]

# Dependency order, with the CSV load spliced in after the DDL and before the first view.
#
# The load MUST come after 01 (which creates the database, schema and all four raw tables) and
# BEFORE 02/04/05/06, which all read loaded data. Getting this wrong was a real bug found while
# testing: the first version loaded first, so COPY INTO had no table to load into for the voice
# transcripts, whose DDL lived two files later.
#
# NOTE: sql/03_load_data.sql is NOT used here -- its PUT paths are machine-generated and go stale.
# The load SQL is rebuilt below from the same FILE_FORMAT constant the canonical loader uses, so
# there is exactly one definition of the CSV format in the project.
SQL_FILES = [
    "01_create_tables.sql",
    "__LOAD__",
    "02_semantic_view.sql",
    "04_cortex_search.sql",
    "05_org_health.sql",
    "06_pay_equity.sql",
    "07_metric_governance.sql",
    "08_employee_voice.sql",
    "09_band_architecture.sql",
]

FILE_FORMAT = (
    "TYPE = CSV\n"
    "                 SKIP_HEADER = 1\n"
    "                 FIELD_OPTIONALLY_ENCLOSED_BY = '\"'\n"
    "                 DATE_FORMAT = 'YYYY-MM-DD'\n"
    "                 EMPTY_FIELD_AS_NULL = TRUE\n"
    "                 NULL_IF = ('')"
)

CSV_TARGETS = [
    ("raw_compensation_bands", "raw_compensation_bands.csv"),
    ("raw_workday_workers", "raw_workday_workers.csv"),
    ("raw_performance_reviews", "raw_performance_reviews.csv"),
    ("raw_voice_transcripts", "raw_voice_transcripts.csv"),
]


# ---------------------------------------------------------------------------
# SQL text handling
# ---------------------------------------------------------------------------
def substitute_db(sql: str, database: str) -> str:
    """Rewrite every reference to the project database.

    A plain token replace of WORKFORCE_ASTRA is correct here: it also rewrites the
    `CREATE DATABASE IF NOT EXISTS` line, which is exactly what makes a scratch-database build
    possible. Occurrences inside comments change too, which is harmless.
    """
    return re.sub(r"\bWORKFORCE_ASTRA\b", database, sql)


def build_load_sql(database: str, staging_uri: str) -> str:
    """The stage + PUT + COPY block, generated fresh so the PUT path is never stale."""
    lines = [
        f"-- AUTO-GENERATED by scripts/rebuild_all.py",
        f"-- stage + load the {len(CSVS)} synthetic CSVs into {database}.RAW",
        f"USE DATABASE {database};",
        f"USE SCHEMA RAW;",
        "",
        f"CREATE OR REPLACE STAGE {database}.RAW.{STAGE_NAME}",
        "  FILE_FORMAT = (" + FILE_FORMAT + ");",
        "",
    ]
    for filename in CSVS:
        lines.append(
            f"PUT file://{staging_uri}/{filename} @{database}.RAW.{STAGE_NAME} "
            "AUTO_COMPRESS = FALSE OVERWRITE = TRUE;"
        )
    lines.append("")
    for table, filename in CSV_TARGETS:
        lines += [
            f"-- {table}: TRUNCATE then FORCE, or a re-run is a silent no-op",
            f"TRUNCATE TABLE IF EXISTS {database}.RAW.{table};",
            f"COPY INTO {database}.RAW.{table}",
            f"  FROM @{database}.RAW.{STAGE_NAME}/{filename}",
            "  FILE_FORMAT = (" + FILE_FORMAT + ")",
            "  ON_ERROR = ABORT_STATEMENT",
            "  FORCE = TRUE;",
            "",
        ]
    return "\n".join(lines)


def split_statements(sql: str) -> list[str]:
    """Split on top-level semicolons only.

    Snowflake stored procedures and JavaScript handlers use $$ ... $$ bodies that contain
    semicolons, and string literals contain them too. Naively splitting on ';' corrupts both, so
    this tracks single-quote and dollar-quote state, and strips `--` comments.
    """
    out: list[str] = []
    buf: list[str] = []
    i, n = 0, len(sql)
    in_single = False
    dollar_tag: str | None = None

    while i < n:
        ch = sql[i]

        if dollar_tag is not None:
            if sql.startswith(dollar_tag, i):
                buf.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
                continue
            buf.append(ch)
            i += 1
            continue

        if in_single:
            buf.append(ch)
            if ch == "'":
                # '' is an escaped quote, not a terminator
                if i + 1 < n and sql[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                in_single = False
            i += 1
            continue

        # not in a string
        if sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j == -1 else j
            continue
        if ch == "'":
            in_single = True
            buf.append(ch)
            i += 1
            continue
        m = re.match(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$", sql[i:])
        if m:
            dollar_tag = m.group(0)
            buf.append(dollar_tag)
            i += len(dollar_tag)
            continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                out.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out


# ---------------------------------------------------------------------------
# stages
# ---------------------------------------------------------------------------
def generate_and_verify() -> None:
    for gen in GENERATORS:
        print(f"== regenerate + verify: {gen.name} ==", flush=True)
        subprocess.run([sys.executable, str(gen)], check=True)
        subprocess.run([sys.executable, str(gen), "--verify"], check=True)


def stage_csvs() -> Path:
    staging = Path(tempfile.gettempdir()) / "wf_astra_stage"
    if " " in str(staging):
        staging = Path("C:/wf_astra_stage")
    staging.mkdir(parents=True, exist_ok=True)
    for filename in CSVS:
        src = DATA_DIR / filename
        if not src.exists():
            sys.exit(f"missing {src} -- run without --print-sql first")
        shutil.copy2(src, staging / filename)
    print(f"== staged {len(CSVS)} CSVs -> {staging.as_posix()} ==", flush=True)
    return staging


def assemble(database: str, staging: Path) -> str:
    parts: list[str] = [
        "-- " + "=" * 74,
        f"-- Workforce Astra full rebuild -> {database}",
        "-- AUTO-GENERATED by scripts/rebuild_all.py. Source of truth is sql/*.sql.",
        "-- " + "=" * 74,
        "",
    ]

    for name in SQL_FILES:
        if name == "__LOAD__":
            parts.append(build_load_sql(database, staging.as_posix()))
            parts.append("")
            continue
        path = SQL_DIR / name
        if not path.exists():
            sys.exit(f"missing {path}")
        # The per-file USE statements are KEPT, not stripped: sql/01's CREATE TABLEs are
        # unqualified and depend on the session context they set. substitute_db() has already
        # rewritten every database reference, so a file cannot retarget a different database.
        body = substitute_db(path.read_text(encoding="utf-8"), database)
        parts.append("-- " + "-" * 74)
        parts.append(f"-- {name}")
        parts.append("-- " + "-" * 74)
        parts.append(body)

    parts.append("")
    parts.append("-- " + "=" * 74)
    parts.append("-- POST-BUILD: score, audit, then run the regression suite")
    parts.append("-- " + "=" * 74)
    parts.append(f"CALL {database}.RAW.score_voice_transcripts();")
    parts.append(f"CALL {database}.RAW.run_band_review();")
    parts.append(f"CALL {database}.RAW.run_metric_tests();")
    parts.append(f"CALL {database}.RAW.run_metric_tests();")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# backends
# ---------------------------------------------------------------------------
def run_snow(sql_file: Path, connection: str) -> None:
    print("== applying with the snow backend (one process) ==", flush=True)
    subprocess.run(
        ["uvx", "--from", "snowflake-cli", "snow", "sql",
         "-c", connection, "-f", str(sql_file)],
        check=True,
    )


def cortex_exe() -> str:
    """Resolve the CoCo CLI binary.

    `cortex` is on PATH in a normal shell, but not reliably inside a subprocess launched from an
    isolated interpreter environment, where it fails with a bare FileNotFoundError. Fall back to
    the documented install location instead of dying with an opaque error.
    """
    found = shutil.which("cortex")
    if found:
        return found
    candidates = sorted(Path.home().joinpath("AppData", "Local", "cortex").glob("*/cortex.exe"),
                        reverse=True)
    if candidates:
        return str(candidates[0])
    bin_dir = Path.home() / "AppData" / "Local" / "cortex" / "bin"
    if bin_dir.exists():
        return "cortex"
    sys.exit("cannot find the cortex CLI on PATH or under ~/AppData/Local/cortex")


def run_coco(sql: str, connection: str) -> None:
    print("== applying with the CoCo backend (one CoCo call per statement) ==", flush=True)
    exe = cortex_exe()
    stmts = split_statements(sql)
    print(f"   using {exe}", flush=True)
    print(f"   {len(stmts)} statements to apply", flush=True)
    for idx, stmt in enumerate(stmts, start=1):
        head = " ".join(stmt.split())[:88]
        print(f"   [{idx}/{len(stmts)}] {head}", flush=True)
        proc = subprocess.run(
            [exe, "-c", connection, "-p", stmt, "--bypass"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0 or "error" in (proc.stdout + proc.stderr).lower():
            # Surface CoCo's own words rather than a bare exit code -- a refused prompt looks
            # identical to a SQL error otherwise.
            print(f"      CoCo returned {proc.returncode}:", flush=True)
            print("      " + (proc.stdout + proc.stderr)[-800:].replace("\n", "\n      "), flush=True)
            sys.exit(f"statement {idx} failed under the CoCo backend")
    print("   all statements applied", flush=True)


def run_sql(sql: str, connection: str, backend: str, sql_file: Path) -> None:
    if backend == "snow":
        run_snow(sql_file, connection)
    else:
        run_coco(sql, connection)


def query(connection: str, statement: str) -> str:
    """Run one read-only statement through snow and return stdout, for the final report."""
    proc = subprocess.run(
        ["uvx", "--from", "snowflake-cli", "snow", "sql", "-c", connection, "-q", statement],
        capture_output=True, text=True,
    )
    return (proc.stdout or "") + (proc.stderr or "")


def drop_database(database: str, connection: str) -> None:
    print(f"== dropping {database} ==", flush=True)
    subprocess.run(
        ["uvx", "--from", "snowflake-cli", "snow", "sql", "-c", connection,
         "-q", f"DROP DATABASE IF EXISTS {database} CASCADE"],
        check=True,
    )


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild the whole Workforce Astra solution.")
    ap.add_argument("--connection", default=DEFAULT_CONNECTION)
    ap.add_argument("--database", default=REAL_DB,
                    help="target database; use a scratch name to rehearse a fresh-account build")
    ap.add_argument("--backend", choices=["snow", "coco"], default="snow")
    ap.add_argument("--print-sql", action="store_true", help="write the SQL and run nothing")
    ap.add_argument("--skip-generate", action="store_true",
                    help="use the committed CSVs as-is instead of regenerating")
    ap.add_argument("--drop", action="store_true",
                    help="DROP the target database CASCADE first (requires --yes)")
    ap.add_argument("--drop-only", action="store_true", help="just drop the database and exit")
    ap.add_argument("--yes", action="store_true", help="required to confirm --drop / --drop-only")
    args = ap.parse_args()

    if (args.drop or args.drop_only) and not args.yes:
        sys.exit("refusing to DROP a database without --yes")

    if args.drop_only:
        drop_database(args.database, args.connection)
        return 0

    if args.drop:
        print(f"== WARNING: dropping {args.database} CASCADE ==", flush=True)
        drop_database(args.database, args.connection)

    if not args.skip_generate:
        generate_and_verify()
    staging = stage_csvs()

    sql = assemble(args.database, staging)
    sql_file = staging / f"rebuild_{args.database.lower()}.sql"
    sql_file.write_text(sql, encoding="utf-8")
    print(f"\n== rebuild SQL ({len(sql):,} chars) -> {sql_file.as_posix()} ==", flush=True)

    if args.print_sql:
        print(sql)
        return 0

    run_sql(sql, args.connection, args.backend, sql_file)

    print("\n" + "=" * 74)
    print("== GOVERNED NUMBERS (compare against README.md) ==")
    print("=" * 74)
    for label, stmt in [
        ("regression suite", f"CALL {args.database}.RAW.run_metric_tests()"),
        ("row counts", f"SELECT 'workers' t, COUNT(*) n FROM {args.database}.RAW.raw_workday_workers "
                       f"UNION ALL SELECT 'reviews', COUNT(*) FROM {args.database}.RAW.raw_performance_reviews "
                       f"UNION ALL SELECT 'transcripts', COUNT(*) FROM {args.database}.RAW.raw_voice_transcripts"),
        ("voice", f"SELECT sentiment_label, COUNT(*) n FROM {args.database}.RAW.voice_theme_results GROUP BY 1"),
        ("bands", f"SELECT below_range_count, red_circle_count FROM "
                  f"SEMANTIC_VIEW({args.database}.RAW.band_health_360 METRICS band.below_range_count, band.red_circle_count)"),
    ]:
        print(f"\n-- {label} --")
        print(query(args.connection, stmt).strip())

    print("\n== rebuild complete ==")
    print(f"   database : {args.database}")
    print(f"   backend  : {args.backend}")
    print(f"   sql file : {sql_file.as_posix()}")
    print("   the Streamlit portal is NOT deployed by this script -- deploy it separately with:")
    print(f"     snow streamlit deploy -c {args.connection} --replace   (from employee_360_portal/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
