"""
Workforce Astra synthetic data generator.
Produces 3 referentially-consistent CSVs: workers, compensation_bands, performance_reviews.

Deliberately bakes in an FTE-vs-Contractor headcount/attrition conflict -- a naive query that
doesn't filter employment_type will disagree with the governed metric that does. That's the
live "same question, different answer across teams" cold open, for real data, not staged.

Usage: python generate_synthetic_data.py
Requires: pip install faker
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
random.seed(7)
Faker.seed(7)

N_WORKERS = 150
N_MANAGERS = 15              # first 15 employees are the manager pool
CONTRACTOR_RATE = 0.15       # fraction of workers who are contractors, not FTE
TERMINATION_RATE = 0.12      # fraction terminated in the last year
DEPARTMENTS = ["Engineering", "Sales", "Finance", "People Ops", "Customer Success"]
BANDS = ["IC3", "IC4", "IC5", "M1", "M2"]
AS_OF = date.today()         # no termination can land in the future
OUTPUT_DIR = Path(__file__).resolve().parent


def gen_compensation_bands():
    rows = []
    base = {"IC3": 900000, "IC4": 1300000, "IC5": 1900000, "M1": 1700000, "M2": 2400000}
    for band in BANDS:
        mid = base[band]
        rows.append({
            "band_code": band,
            "band_title": band,
            "min_base": int(mid * 0.85),
            "mid_point": mid,
            "max_base": int(mid * 1.20),
        })
    return rows


def gen_workers():
    rows = []
    managers = [f"EMP-{i:04d}" for i in range(1, N_MANAGERS + 1)]
    start = date(2021, 1, 1)
    for i in range(1, N_WORKERS + 1):
        employee_id = f"EMP-{i:04d}"
        is_manager = employee_id in managers
        # Managers sit in the M1/M2 people-management bands so the org hierarchy reads
        # believably on screen (an "IC3 Engineer" managing 14 reports invites questions).
        band = random.choice(["M1", "M2"]) if is_manager else random.choice(BANDS)
        mid = {"IC3": 900000, "IC4": 1300000, "IC5": 1900000, "M1": 1700000, "M2": 2400000}[band]
        # Managers are always active FTEs -- otherwise a "notify the manager" action can
        # point at a terminated employee or a contractor, which breaks the demo's credibility.
        is_contractor = False if is_manager else random.random() < CONTRACTOR_RATE
        is_terminated = False if is_manager else random.random() < TERMINATION_RATE
        hire_date = start + timedelta(days=random.randint(0, 1400))
        term_date = ""
        term_reason = ""
        status = "Active"
        if is_terminated:
            status = "Terminated"
            raw_term = hire_date + timedelta(days=random.randint(120, 1200))
            term_date = min(raw_term, AS_OF).isoformat()   # never a future termination
            term_reason = random.choices(
                ["Voluntary", "Involuntary", "Retirement"], weights=[0.6, 0.3, 0.1])[0]

        manager_id = random.choice(managers) if not is_manager else ""
        rows.append({
            "employee_id": employee_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "department_code": random.choice(DEPARTMENTS),
            "band_code": band,
            "job_title": band + " " + ("Manager" if band.startswith("M") else random.choice(["Engineer", "Analyst", "Specialist"])),
            "hire_date": hire_date.isoformat(),
            "employee_status": status,
            "termination_date": term_date,
            "termination_reason": term_reason,
            "employment_type": "Contractor" if is_contractor else "FTE",
            # Deliberate: base_pay is drawn from 0.75-1.15x the band midpoint, while the band
            # itself runs 0.85-1.20x. Pay therefore dips below band minimum on purpose -- that
            # is what makes comp_ratio < 0.85 a real (underpaid) flight-risk signal rather than
            # a number that can never fire.
            "base_pay": int(mid * random.uniform(0.75, 1.15)),
            "manager_id": manager_id,
            "manager_slack_id": f"U{manager_id[-4:]}" if manager_id else "",
        })
    return rows


def gen_performance_reviews(workers, bands):
    rows = []
    mid_points = {b["band_code"]: int(b["mid_point"]) for b in bands}
    # Three distinct pools, aligned so the demo's evidence step is coherent.
    #
    # The old version attached "competing offer / external opportunities" only to LOW
    # performers (rating 2-3). But the flight-risk query is defined as comp_ratio < 0.85
    # AND rating > 4, so those two sets could never intersect: the agent would flag an
    # underpaid high performer and then quote "Exceeded goals... no retention concerns
    # raised" as its evidence. Flight-risk language now lives on the underpaid high
    # performers themselves, which is also the more realistic retention story.
    flight_risk_texts = [
        "Exceeded goals again this cycle; in our 1:1 raised a competing offer and asked about band placement.",
        "Top performer on the platform migration; noted pay feels out of step with market and is interviewing externally.",
        "Strong delivery and mentorship; flagged compensation concerns and mentioned a competing offer in passing.",
    ]
    disengaged_texts = [
        "Missed two consecutive sprint commitments; disengaged in team meetings.",
        "Goals largely unmet this cycle; manager noted visible frustration with role scope.",
        "Inconsistent output and low meeting participation; workload concerns raised.",
    ]
    positive_texts = [
        "Exceeded goals for the second straight quarter; strong peer feedback on mentorship.",
        "Delivered the migration project ahead of schedule; recommended for stretch assignment.",
        "Consistently high-quality output; no retention concerns raised.",
    ]
    i = 1
    for w in workers:
        if w["employee_status"] != "Active":
            continue
        comp_ratio = int(w["base_pay"]) / mid_points[w["band_code"]]
        if comp_ratio < 0.85 and random.random() < 0.5:
            rating, goals, text = random.randint(4, 5), random.randint(85, 100), random.choice(flight_risk_texts)
        elif random.random() < 0.18:
            rating, goals, text = random.randint(2, 3), random.randint(40, 70), random.choice(disengaged_texts)
        else:
            rating, goals, text = random.randint(4, 5), random.randint(85, 100), random.choice(positive_texts)
        rows.append({
            "review_id": f"REV-{i:05d}",
            "employee_id": w["employee_id"],
            "review_period": "2026-Q2",
            "rating_score": rating,
            "goals_met_pct": goals,
            "review_text": text,
        })
        i += 1
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {path}")


def verify():
    """Re-read the CSVs and assert the invariants the demo depends on."""
    import csv as _csv

    def load(name):
        with open(OUTPUT_DIR / name, encoding="utf-8") as f:
            return list(_csv.DictReader(f))

    workers = load("raw_workday_workers.csv")
    bands = {b["band_code"]: b for b in load("raw_compensation_bands.csv")}
    reviews = load("raw_performance_reviews.csv")
    by_id = {w["employee_id"]: w for w in workers}
    failures = []

    active = [w for w in workers if w["employee_status"] == "Active"]
    naive = len(active)
    governed = len([w for w in active if w["employment_type"] == "FTE"])
    print(f"naive active COUNT(*)      : {naive}")
    print(f"governed active FTE count  : {governed}")
    print(f"ungoverned/naive delta     : {naive - governed} (must be > 0 -- the whole demo)")
    if naive == governed:
        failures.append("governed and naive headcount are equal -- the conflict is not in the data")

    terminated = [w for w in workers if w["employee_status"] == "Terminated"]
    future = [w for w in terminated if date.fromisoformat(w["termination_date"]) > AS_OF]
    print(f"terminated (total/FTE)     : {len(terminated)}/{len([w for w in terminated if w['employment_type'] == 'FTE'])}")
    print(f"terminations in the future : {len(future)}")
    if future:
        failures.append(f"{len(future)} termination date(s) in the future")

    bad_manager = [
        w for w in workers
        if w["manager_id"] and (
            w["manager_id"] not in by_id
            or by_id[w["manager_id"]]["employee_status"] != "Active"
            or by_id[w["manager_id"]]["employment_type"] != "FTE"
        )
    ]
    print(f"reports w/ bad manager ref : {len(bad_manager)}")
    if bad_manager:
        failures.append(f"{len(bad_manager)} report(s) point at a missing/terminated/contractor manager")

    for fk, table, col in (("band_code", workers, "band_code"), ("employee_id", reviews, "employee_id")):
        orphans = [r[col] for r in table if r[col] not in (set(bands) if fk == "band_code" else set(by_id))]
        if orphans:
            failures.append(f"{len(orphans)} orphan {col} reference(s)")

    eligible = [
        w for w in active
        if w["employment_type"] == "FTE"
        and int(w["base_pay"]) / int(bands[w["band_code"]]["mid_point"]) < 0.85
    ]
    print(f"active FTE underpaid (<0.85): {len(eligible)} (feeds the flight-risk query)")
    if not eligible:
        failures.append("no active FTE below 0.85 comp-ratio -- the flight-risk query returns nothing")

    # The evidence step needs headroom: a flagged candidate must ALSO have review text that
    # actually reads like a flight risk, and a manager to notify. Without this the agent
    # quotes a glowing review as evidence of attrition risk.
    by_review = {r["employee_id"]: r for r in reviews}
    risk_markers = ("competing offer", "out of step with market", "interviewing externally", "compensation concerns")
    risk = [
        w for w in active
        if int(w["base_pay"]) / int(bands[w["band_code"]]["mid_point"]) < 0.85
        and int(by_review[w["employee_id"]]["rating_score"]) >= 4
    ]
    notifiable = [
        w for w in risk
        if any(m in by_review[w["employee_id"]]["review_text"] for m in risk_markers)
        and w["manager_slack_id"]
    ]
    print(f"flight-risk candidates       : {len(risk)} (comp_ratio<0.85 AND rating>=4)")
    print(f"  ...with citable evidence     : {len(notifiable)} (need >= 3 for the demo)")
    if len(notifiable) < 3:
        failures.append(
            "fewer than 3 flight-risk candidates have both at-risk review text and a "
            "manager_slack_id -- the evidence + notify loop cannot be demonstrated"
        )

    if failures:
        print("\nVERIFY FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nVERIFY PASSED: all demo invariants hold.")
    return 0


def main():
    bands = gen_compensation_bands()
    workers = gen_workers()
    reviews = gen_performance_reviews(workers, bands)

    write_csv(OUTPUT_DIR / "raw_compensation_bands.csv", bands)
    write_csv(OUTPUT_DIR / "raw_workday_workers.csv", workers)
    write_csv(OUTPUT_DIR / "raw_performance_reviews.csv", reviews)


if __name__ == "__main__":
    import sys

    if "--verify" in sys.argv:
        sys.exit(verify())
    main()
