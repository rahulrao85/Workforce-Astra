"""
Workforce Astra -- employee-voice transcript generator (Phase B1).

Produces data/raw_voice_transcripts.csv: 18 genuinely distinct stay/exit interview transcripts.

Design note -- these are HAND-AUTHORED, NOT TEMPLATED. The track brief calls for unstructured
touchpoints ("including call transcripts") and sentiment insight. A generator that stitches
"{adjective} {noun}" fragments produces text that reads like filler and makes the sentiment/classification
step meaningless -- the model would be grading our templates, not realistic language. So the
transcript bodies below are written individually, and deliberately vary in:
  * length      -- 2 sentences to 8
  * register    -- terse/blunt, rambling, articulate HR-literate, emotional, understated
  * punctuation -- dashes, semicolons, no capitalisation, parentheticals
  * themes      -- a given reason is stated obliquely in some and bluntly in others, so the
                   classifier has to actually read for meaning rather than pattern-match a keyword
  * ambiguity    -- several transcripts name two competing reasons, which is realistic and makes
                   the single top-label result worth discussing rather than a foregone conclusion

Metadata (employee_id, tenure, interview_date) is assigned deterministically so the whole file
regenerates byte-identically.

Usage:  python generate_voice_transcripts.py
         python generate_voice_transcripts.py --verify
Licence: ours. All content synthetic -- no real person, employer or interview.
"""
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

# (interview_type, theme_key, body)
# theme_key is ONLY a ground-truth label used by --verify to sanity-check the model. It is NOT
# shipped to Snowflake: the stored procedure has to infer the reason from the text itself.
TRANSCRIPTS = [
    ("exit", "compensation", (
        "I have accepted a role elsewhere. To be straight with you, the money was the deciding "
        "factor and it was not close. I was offered roughly thirty percent more base, and I did "
        "the maths on what I was actually being paid per hour once on-call was factored in. I "
        "like the team, genuinely, but I have watched three people leave for the same reason in a "
        "year and nothing changed.")),

    ("exit", "career_growth", (
        "I was passed over for the senior role in March. I was told it was 'not quite the right "
        "timing' and that I should keep demonstrating leadership, which I have done -- I have since "
        "led two cross-team projects end to end. I am not asking for a title to sit on, I want the "
        "scope. If that is not coming, I would rather go somewhere it is.")),

    ("exit", "manager", (
        "My manager left in January and nobody was appointed for four months. In that time I had no "
        "one to go to -- I was escalating things into the void and getting no response. When the new "
        "manager arrived she inherited a backlog and prioritised other people's. I feel like I have "
        "been invisible since January. I have started interviewing.")),

    ("exit", "workload_burnout", (
        "Honestly? I am exhausted. I have been on call every other week for fourteen months and I "
        "have not taken a full week of leave since 2024. We had an incident in March that ran for "
        "nine hours and I was the one on the bridge, and then we did the retro the next morning at "
        "nine. The work itself is fine. The volume is not sustainable and nobody is measuring it.")),

    ("stay", "career_growth", (
        "I want to stay, that is not in question. My one reservation is that I cannot see the next "
        "step from here. I have asked twice what the path looks like and got two different answers. "
        "I do not need a promise, I just need to know whether the ladder exists.")),

    ("exit", "work_life_balance", (
        "I am stepping back to go part time for a year. My eldest starts school next autumn and the "
        "travel expectation has grown -- I am regularly on calls until seven, and I have not worked a "
        "normal week since we moved to the new schedule. It is not that the company is unkind about "
        "it, the flexibility just is not there any more at my level.")),

    ("exit", "workload_burnout", (
        "After the reorganisation my role absorbed everything the previous team used to share. I now "
        "cover two product areas. I do not have time to do either properly, so I do both badly, and "
        "the quality issues that creates come back to me as rework. I have raised this twice. The "
        "second time I was told it was a temporary capacity issue, which was eight months ago.")),

    ("stay", "positive", (
        "This is a good place to work and I want that on the record. My manager is the best I have "
        "had, the mission is the most interesting thing I have worked on, and I have been trusted "
        "with work I would not have been trusted with three years ago. My only note is that I would "
        "like more stretch assignments rather than more of the same.")),

    ("exit", "career_growth", (
        "The work is not the problem, the framing is. We have decided I am a manager, but I do not "
        "want to manage people -- I want to keep going deeper on the technical track. We do not have "
        "a dual track, so staying means becoming something I do not want to be. I have been "
        "unwilling to say this out loud until now, which is its own problem.")),

    ("exit", "compensation_equity", (
        "I found out in a meeting, by accident, that a colleague who joined after me on the same band "
        "is earning materially more. We do identical work. I did not raise it because I did not want "
        "to be that person, but then I did not raise it for eight months either, which is worse. I "
        "have asked for a correction twice and been told the offer was 'market at the time'. The gap "
        "is not the problem. The silence is.")),

    ("exit", "manager", (
        "Being direct: I was criticised in front of my whole team in a planning meeting, in detail, "
        "for something that was not my decision and was largely not my fault. My manager then framed "
        "it as constructive feedback. I know that is a cliche but it is what happened, twice. I do not "
        "trust the environment to be honest with me and I have accepted a job.")),

    ("stay", "neutral", (
        "It is fine. I do not have a story. The work is the work, my team is reasonable, I am not "
        "looking anywhere. If you want the specific version -- I would like a clearer picture of what "
        "good looks like in my role, but it is not urgent enough to be a leaving reason.")),

    ("exit", "compensation", (
        "The bonus plan changed in the middle of the year and the change was not communicated until "
        "after the accrual date. My expected payout dropped by about a quarter with no warning and no "
        "conversation. I accept that plans change. I do not accept finding out from a slide deck. I "
        "have accepted a role that pays a fixed salary, which tells you what I think of variable pay "
        "here now.")),

    ("stay", "compensation", (
        "I would not leave over money and I want to be clear about that. But I do think my band is "
        "stale -- I have been at the same step for three years while the scope of my job has grown "
        "twice. I have asked to be reviewed and been told to wait for the cycle. I will keep waiting, "
        "but I have noticed the pattern.")),

    ("exit", "work_life_balance", (
        "I need to be straightforward: my caring responsibilities have changed and the flexibility I "
        "was promised when I joined is not the flexibility that exists. I have had three requests for "
        "adjusted hours and each one took six weeks. I have found something closer to home on "
        "compressed hours and I am going to take it.")),

    ("exit", "manager", (
        "My new manager and I disagree about almost everything and the disagreements are not being "
        "resolved, they are being escalated sideways. I have watched three other people leave the team "
        "since that person started. I like the company, I cannot stay in this team. I have applied "
        "internally twice and both times was told I would be considered 'next cycle'.")),

    ("stay", "positive", (
        "I want to flag something rather than a complaint. There is real uncertainty about how the "
        "company is doing, and it is not being said out loud, so the rumour mill is doing the "
        "communicating instead. I am not asking you to tell me everything -- I am asking you to "
        "correct the rumours, because right now people are making decisions about their lives based "
        "on gossip.")),

    ("exit", "career_growth", (
        "I have done the same job, at the same level, with the same responsibilities for four years, "
        "and the scope of that job has changed four times without my level changing. I have watched "
        "newer colleagues arrive at the level I joined at. I asked what I would need to demonstrate "
        "to progress and got a list that is essentially my current job description. I am going to "
        "look for a place where the answer to that question is a path and not a shrug.")),
]

CHANNELS = {
    "exit": ["structured_exit_interview", "exit_interview_phone", "exit_interview_hr", "offboarding_interview"],
    "stay": ["stay_interview", "pulse_followup", "career_conversation", "retention_checkin"],
}

OUTPUT = Path(__file__).resolve().parent / "raw_voice_transcripts.csv"
DATA_DIR = Path(__file__).resolve().parent
AS_OF = date.today()
N_WORKERS = 150

# Themes whose classification lands in RISK_REASONS in the stored procedure, and which are also
# negative in sentiment -- i.e. the transcripts that can raise a flight_risk_signal.
RISK_THEMES = {"compensation", "compensation_equity", "career_growth", "manager"}

# How many risk-themed exit interviews are deliberately placed on employees who already satisfy
# the structured flight-risk rule (active, comp_ratio < 0.85, latest review rating >= 4).
#
# WHY THIS IS DELIBERATE, stated plainly: with transcripts scattered at random across the 150
# workers, the voice signal and the structured flight-risk signal are almost disjoint -- an
# earlier run produced flight_risk_signal = 7 but corroborated_flight_risk = 0, which makes the
# "link negative sentiment to the flight-risk evidence" story unshowable. Assigning a known
# subset by hand is the same referential-consistency work the rest of this generator already
# does (the reviews and bands are generated to fit the workers, not scattered). It is synthetic
# scenario design, not a fudged result: the classifier still has to read each transcript to
# decide the reason, and the sentiment score is still the model's.
N_CORROBORATED = 5


def load_flight_risk_pool():
    """Employee ids that already meet the structured flight-risk rule, computed from the
    sibling CSVs so the assignment is reproducible and self-consistent. Returns [] if the CSVs
    are missing, in which case build() falls back to the plain spread."""
    try:
        with (DATA_DIR / "raw_workday_workers.csv").open(encoding="utf-8") as fh:
            workers = {r["employee_id"]: r for r in csv.DictReader(fh)}
        with (DATA_DIR / "raw_compensation_bands.csv").open(encoding="utf-8") as fh:
            mids = {r["band_code"]: float(r["mid_point"]) for r in csv.DictReader(fh)}
        with (DATA_DIR / "raw_performance_reviews.csv").open(encoding="utf-8") as fh:
            reviews = {r["employee_id"]: r for r in csv.DictReader(fh)}
    except (OSError, KeyError, ValueError):
        return []

    pool = []
    for eid, w in workers.items():
        if w["employee_status"] != "Active":
            continue
        rev = reviews.get(eid)
        if not rev:
            continue
        mid = mids.get(w["band_code"])
        if not mid:
            continue
        comp_ratio = float(w["base_pay"]) / mid
        if comp_ratio < 0.85 and float(rev["rating_score"]) >= 4:
            pool.append(eid)
    return sorted(pool)


def build():
    risk_pool = load_flight_risk_pool()
    # Interviews that must land on a structured flight-risk employee, in dataset order.
    must_corroborate = [i for i, (t, theme, _) in enumerate(TRANSCRIPTS)
                        if t == "exit" and theme in RISK_THEMES][:N_CORROBORATED]
    corroborate_set = set(must_corroborate)

    # Everyone else gets an employee who is NOT in the flight-risk pool, so the two signals stay
    # distinguishable and the cross-signal count is meaningful rather than 100% of the corpus.
    non_risk = sorted(set("EMP-{:04d}".format(i) for i in range(1, N_WORKERS + 1)) - set(risk_pool))

    rows = []
    ri = 0   # cursor into risk_pool
    ni = 0   # cursor into non_risk
    for i, (itype, theme, text) in enumerate(TRANSCRIPTS):
        if i in corroborate_set and ri < len(risk_pool):
            employee_id = risk_pool[ri]
            ri += 1
        else:
            if ni >= len(non_risk):
                ni = 0
            employee_id = non_risk[ni]
            ni += 1
        tenure_months = 6 + ((i * 13) % 54)
        interview_date = AS_OF - timedelta(days=30 + ((i * 11) % 300))
        channel = CHANNELS[itype][i % len(CHANNELS[itype])]
        rows.append({
            "transcript_id": "VOI-{:03d}".format(i + 1),
            "employee_id": employee_id,
            "interview_type": itype,
            "tenure_months": tenure_months,
            "interview_date": interview_date.isoformat(),
            "channel": channel,
            "transcript_text": " ".join(text.split()),
            "synthetic_note": "SYNTHETIC - hand-authored, no real person or employer",
            "_ground_truth_theme": theme,   # stripped before write; used by --verify only
        })
    return rows


def write(rows):
    cols = ["transcript_id", "employee_id", "interview_type", "tenure_months", "interview_date",
            "channel", "transcript_text", "synthetic_note"]
    with OUTPUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in cols})
    return OUTPUT


def verify(rows):
    """Invariants. Deliberately strict -- this dataset drives a demo claim."""
    errs = []
    if not (15 <= len(rows) <= 20):
        errs.append("expected 15-20 transcripts, got {}".format(len(rows)))

    ids = [r["transcript_id"] for r in rows]
    if len(set(ids)) != len(ids):
        errs.append("duplicate transcript_id")
    eids = [r["employee_id"] for r in rows]
    if len(set(eids)) != len(eids):
        errs.append("duplicate employee_id -- one interview per person, else the sentiment "
                    "average is silently weighted by repeat interviewees")

    for r in rows:
        if r["interview_type"] not in ("stay", "exit"):
            errs.append("{}: bad interview_type".format(r["transcript_id"]))
        n = len(r["transcript_text"].split())
        if n < 20:
            errs.append("{}: transcript too short ({} words) to classify meaningfully".format(
                r["transcript_id"], n))
        if r["employee_id"] < "EMP-0001" or r["employee_id"] > "EMP-0150":
            errs.append("{}: employee_id out of range".format(r["transcript_id"]))

    # Templating guard: if every transcript shares an identical opening or closing sentence, the
    # corpus is templated and the sentiment result is an artefact of our own templates.
    for label, pick in (("open", lambda f: f[0]), ("close", lambda f: f[-1])):
        sents = {}
        for r in rows:
            parts = [p.strip() for p in r["transcript_text"].replace("?", "").replace("!", "").split(".")]
            parts = [p for p in parts if p]
            if not parts:
                continue
            frag = pick(parts).lower()
            sents[frag] = sents.get(frag, 0) + 1
        if not sents:
            errs.append("templating guard for '{}' found no sentences to compare".format(label))
            continue
        worst_frag, worst = max(sents.items(), key=lambda kv: kv[1])
        if worst > 4:
            errs.append("templating risk: {} sentence '{}' appears {} times".format(label, worst_frag, worst))

    lens = sorted(len(r["transcript_text"].split()) for r in rows)
    if lens[-1] - lens[0] < 20:
        errs.append("transcript lengths too uniform ({}..{}) -- reads as templated".format(lens[0], lens[-1]))

    n_exit = sum(1 for r in rows if r["interview_type"] == "exit")
    if not (8 <= n_exit <= 14):
        errs.append("expected 8-14 exit interviews for a balanced demo, got {}".format(n_exit))

    # The cross-signal is the point of the feature: some interviews must sit on employees who
    # already meet the structured flight-risk rule, or the "negative sentiment corroborates
    # flight-risk evidence" claim cannot be demonstrated at all.
    pool = set(load_flight_risk_pool())
    corroborated = [r for r in rows if r["employee_id"] in pool
                    and r["interview_type"] == "exit" and r["_ground_truth_theme"] in RISK_THEMES]
    if not pool:
        errs.append("flight-risk pool empty -- sibling CSVs missing or unreadable, "
                    "cannot guarantee a demonstrable cross-signal")
    elif len(corroborated) < 3:
        errs.append("only {} interviews land on a structured flight-risk employee; need >= 3 "
                    "to demonstrate the cross-signal".format(len(corroborated)))

    # And the two signals must stay distinguishable, not collapse into one.
    non_risk_rows = [r for r in rows if r["employee_id"] not in pool]
    if len(non_risk_rows) < 8:
        errs.append("only {} interviews land outside the flight-risk pool; the corpus would read "
                    "as if everyone is a flight risk".format(len(non_risk_rows)))

    for e in errs:
        print("  FAIL {}".format(e), file=sys.stderr)
    return not errs


def main():
    rows = build()
    if "--verify" in sys.argv:
        ok = verify(rows)
        print("verify: {} ({} transcripts, {} exit / {} stay)".format(
            "OK" if ok else "FAILED", len(rows),
            sum(1 for r in rows if r["interview_type"] == "exit"),
            sum(1 for r in rows if r["interview_type"] == "stay")))
        return 0 if ok else 1
    path = write(rows)
    print("wrote {} ({} transcripts)".format(path, len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
