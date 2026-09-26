"""
Build the submission deck on the official Hack2Skill template.

Keeps the template's title, content and thank-you backgrounds; drops its guidelines slide; fills the
content slides from verified numbers (live Snowflake, synthetic data, 26-Sep-2026). The two large
background PNGs are re-encoded as JPEG so the exported PDF stays under the 5 MB form limit.

Usage:
    uv run --no-project --with python-pptx --with pillow python scripts/build_deck.py
Writes deck/Workforce_Astra_Submission_Deck.pptx (export to PDF with PowerPoint).
"""
from __future__ import annotations

import io
from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "Prototype Submission Template _ CoCo CLI Hackathon GCC Edition.pptx"
OUT = ROOT / "deck" / "Workforce_Astra_Submission_Deck.pptx"

INK = RGBColor(0x20, 0x27, 0x29)      # template text colour
MUTED = RGBColor(0x5B, 0x65, 0x70)
ACCENT = RGBColor(0x0B, 0x5E, 0xD7)
TINT = RGBColor(0xEE, 0xF5, 0xFE)
BORDER = RGBColor(0xC7, 0xDB, 0xF7)
PANEL = RGBColor(0xF7, 0xFA, 0xFF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

BODY = "Segoe UI"
SEMI = "Segoe UI Semibold"
MONO = "Consolas"


def In(v):
    return Inches(v)


# ── text helpers ──────────────────────────────────────────────────────────────
def P(text, size=10.5, color=INK, bold=False, font=BODY, align=PP_ALIGN.LEFT, after=3,
      bullet=False, italic=False, spc=None):
    """One paragraph. `text` is a str or a list of (str, overrides) runs."""
    return dict(text=text, size=size, color=color, bold=bold, font=font, align=align,
                after=after, bullet=bullet, italic=italic, spc=spc)


def _fill_para(para, spec):
    para.alignment = spec["align"]
    para.space_after = Pt(spec["after"])
    runs = spec["text"] if isinstance(spec["text"], list) else [(spec["text"], {})]
    for txt, ov in runs:
        r = para.add_run()
        r.text = txt
        f = r.font
        f.size = Pt(ov.get("size", spec["size"]))
        f.bold = ov.get("bold", spec["bold"])
        f.italic = ov.get("italic", spec["italic"])
        f.name = ov.get("font", spec["font"])
        f.color.rgb = ov.get("color", spec["color"])
        if ov.get("link"):
            r.hyperlink.address = ov["link"]
        if spec["spc"]:
            r._r.get_or_add_rPr().set("spc", str(spec["spc"]))
    if spec["bullet"]:
        pPr = para._p.get_or_add_pPr()
        pPr.set("marL", str(In(0.15)))
        pPr.set("indent", str(-In(0.15)))
        clr = etree.SubElement(pPr, qn("a:buClr"))
        etree.SubElement(clr, qn("a:srgbClr")).set("val", str(ACCENT))
        etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
        etree.SubElement(pPr, qn("a:buChar")).set("char", "•")


def _fill_frame(tf, paras, anchor, inset):
    tf.word_wrap = True
    tf.auto_size = None
    tf.margin_left = tf.margin_right = In(inset[0])
    tf.margin_top = tf.margin_bottom = In(inset[1])
    tf.vertical_anchor = anchor
    for i, spec in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        _fill_para(para, spec)


def text(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, inset=(0, 0)):
    box = slide.shapes.add_textbox(In(x), In(y), In(w), In(h))
    _fill_frame(box.text_frame, paras, anchor, inset)
    return box


def card(slide, x, y, w, h, paras=(), fill=TINT, line=BORDER, anchor=MSO_ANCHOR.TOP,
         inset=(0.12, 0.08), radius=0.07, dash=False, line_w=0.75):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, In(x), In(y), In(w), In(h))
    s.adjustments[0] = min(0.5, radius / min(w, h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(line_w)
        if dash:
            s.line.dash_style = 7  # MSO_LINE.DASH
    s.shadow.inherit = False
    if paras:
        _fill_frame(s.text_frame, list(paras), anchor, inset)
    return s


def arrow(slide, x1, y1, x2, y2, color=ACCENT, w=1.5, dash=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, In(x1), In(y1), In(x2), In(y2))
    c.line.color.rgb = color
    c.line.width = Pt(w)
    if dash:
        c.line.dash_style = 4  # MSO_LINE.ROUND_DOT
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn("a:tailEnd"))
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("len", "med")
    return c


# ── slide scaffolding ─────────────────────────────────────────────────────────
def jpeg(blob, quality=84):
    im = Image.open(io.BytesIO(blob)).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    buf.seek(0)
    return buf


def replace_background(prs, slide, stream):
    old = next(sh for sh in slide.shapes if sh.shape_type == 13)
    pic = slide.shapes.add_picture(stream, 0, 0, prs.slide_width, prs.slide_height)
    tree = slide.shapes._spTree
    tree.remove(pic._element)
    tree.insert(2, pic._element)
    rid = old._element.blip_rId
    tree.remove(old._element)
    slide.part.drop_rel(rid)


def delete_slide(prs, slide):
    lst = prs.slides._sldIdLst
    for sid in list(lst):
        if prs.part.related_part(sid.rId) is slide.part:
            prs.part.drop_rel(sid.rId)
            lst.remove(sid)
            return


def new_content_slide(prs, layout, bg_png, kicker, title, page):
    s = prs.slides.add_slide(layout)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    s.shapes.add_picture(io.BytesIO(bg_png), 0, 0, prs.slide_width, prs.slide_height)
    text(s, 0.45, 0.66, 9.1, 0.24, [P(kicker.upper(), 9, ACCENT, bold=True, spc=120)])
    text(s, 0.45, 0.86, 9.1, 0.5, [P(title, 20, INK, bold=True, font=SEMI)])
    text(s, 0.45, 5.27, 7.0, 0.2,
         [P("Workforce Astra  ·  Employee 360 on Snowflake  ·  all data synthetic", 7.5, MUTED)])
    text(s, 8.55, 5.27, 1.0, 0.2, [P(str(page), 7.5, MUTED, align=PP_ALIGN.RIGHT)])
    return s


def label(txt, color=ACCENT, size=9, after=3):
    return P(txt, size, color, bold=True, after=after)


# ── content ───────────────────────────────────────────────────────────────────
def title_slide(slide):
    fields = {
        "Team Name :": "Workforce Astra",
        "Team Leader Name :": "Rahul Rao",
        "Team Size :": "1",
        "Problem Statement :": "Customer 360 and Next Best Action Engine (as Employee 360)",
    }
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        key = sh.text_frame.text.strip()
        if key in fields:
            tf = sh.text_frame
            size = tf.paragraphs[0].runs[0].font.size or Pt(13.4)
            for p in list(tf.paragraphs)[1:]:
                p._p.getparent().remove(p._p)
            para = tf.paragraphs[0]
            for r in list(para.runs):
                r._r.getparent().remove(r._r)
            _fill_para(para, P([(key + " ", {"font": SEMI}), (fields[key], {"color": ACCENT, "font": SEMI})],
                               size=size.pt, after=0))
            if key == "Problem Statement :":
                tf.word_wrap = True
                sh.width = In(9.2)


def problem_slide(s):
    x1, x2, w, y1, y2, h = 0.45, 5.1, 4.45, 1.5, 3.37, 1.8
    card(s, x1, y1, w, h, [
        label("THE BUSINESS PROBLEM"),
        P("HR, Finance and Engineering each re-derive headcount, attrition and pay metrics ad hoc. "
          "Nobody owns the definition, so the same question gets a different answer from each team.", size=11.5),
        P("Ask “how many employees do we have?” and get 109 from one query, 127 from another, "
          "on identical data.", color=MUTED, size=10.5),
    ])
    card(s, x2, y1, w, h, [
        label("WHO IT'S FOR"),
        P("People Analytics and HR business partners", size=11.5, bullet=True, after=3),
        P("Finance: workforce cost and board reporting", size=11.5, bullet=True, after=3),
        P("Engineering and delivery leaders: spans, retention", size=11.5, bullet=True, after=3),
        P("CHRO and compliance: pay equity, band policy", size=11.5, bullet=True, after=3),
    ])
    card(s, x1, y2, w, h, [
        label("PAIN POINT → IMPROVEMENT"),
        P([("Today: ", {"bold": True}),
           ("reconciliation before every board pack; pay-equity numbers nobody trusts; "
            "exit interviews read once and never joined to anything.", {})], size=11, after=6),
        P([("With Workforce Astra: ", {"bold": True, "color": ACCENT}),
           ("one owned, tested definition per metric; interview reasons joined to pay and "
            "performance; the next action drafted for a human to approve.", {})], size=11),
    ])
    card(s, x2, y2, w, h, [
        label("INDUSTRY CONTEXT: GCCs"),
        P("A Global Capability Centre runs people operations for a global parent. The parent, "
          "the centre and its vendors each keep their own definitions, and contractors blur what "
          "“headcount” means.", size=11.5),
        P("Customer 360 unifies the customer. Employee 360 unifies the workforce.",
          color=ACCENT, bold=True, size=11),
    ])


def solution_slide(s):
    card(s, 0.45, 1.5, 4.1, 2.3, [
        label("SAME DATA, SAME MOMENT, TWO ANSWERS"),
    ])
    text(s, 0.6, 1.9, 1.9, 0.7, [P("109", 40, ACCENT, bold=True, font=SEMI, after=0)])
    text(s, 0.6, 2.6, 1.85, 1.1, [P("Governed FTE headcount, from the Employee 360 semantic view", 9.5)])
    text(s, 2.55, 1.9, 1.9, 0.7, [P("127", 40, MUTED, bold=True, font=SEMI, after=0)])
    text(s, 2.55, 2.6, 1.85, 1.1, [P("Ungoverned “active” count: silently includes 18 contractors", 9.5)])
    text(s, 0.6, 3.3, 3.8, 0.4, [P("The semantic view makes the governed answer the default, in every tool.",
                                   9.5, ACCENT, bold=True)])
    card(s, 0.45, 3.93, 4.1, 1.27, [
        label("NEXT BEST ACTION"),
        P("An MCP tool drafts the manager alert, comp adjustment or band review. Every tool "
          "defaults to dry-run: nothing is sent, and a human approves.", size=10),
    ])
    text(s, 4.8, 1.47, 4.75, 0.3, [P("Five governed Semantic Views", 11, INK, bold=True, font=SEMI)])
    views = [
        ("Employee 360", "headcount, attrition and comp-ratio across HRIS and reviews"),
        ("Org Health 360", "span of control, overspan managers, org depth"),
        ("Pay Equity 360", "raw vs band-adjusted pay gap; small cohorts suppressed"),
        ("Employee Voice 360", "interview sentiment and reason, joined to risk"),
        ("Band Health 360", "below-minimum pay, red circles, band overlap"),
    ]
    y = 1.8
    for name, desc in views:
        card(s, 4.8, y, 4.75, 0.6, [P([(name + "   ", {"bold": True, "color": ACCENT, "font": SEMI}),
                                       (desc, {})], size=10, after=0)],
             anchor=MSO_ANCHOR.MIDDLE, fill=WHITE)
        y += 0.68


def arch_slide(s):
    def box(x, y, w, h, title, sub=None, fill=WHITE):
        paras = [P(title, 9.5, INK, bold=True, font=SEMI, after=1)]
        if sub:
            paras.append(P(sub, 8.5, MUTED, after=0))
        return card(s, x, y, w, h, paras, fill=fill, anchor=MSO_ANCHOR.MIDDLE, inset=(0.08, 0.04))

    # sources
    text(s, 0.45, 1.45, 1.6, 0.25, [label("DATA SOURCES")])
    card(s, 0.45, 1.75, 1.55, 1.2, [
        P("Structured", 9.5, INK, bold=True, font=SEMI, after=2),
        P("HRIS workers (150)", 8.5, MUTED, after=1),
        P("Comp bands (5)", 8.5, MUTED, after=1),
        P("Performance reviews (127)", 8.5, MUTED, after=0),
    ], inset=(0.08, 0.06))
    card(s, 0.45, 3.1, 1.55, 1.3, [
        P("Unstructured", 9.5, INK, bold=True, font=SEMI, after=2),
        P("Stay / exit interviews (18)", 8.5, MUTED, after=1),
        P("Review note text (127)", 8.5, MUTED, after=0),
    ], inset=(0.08, 0.06))
    text(s, 0.45, 4.43, 1.6, 0.25, [P("synthetic, generated in repo", 7.5, MUTED, italic=True)])

    # snowflake boundary
    card(s, 2.2, 1.4, 5.35, 3.15, fill=PANEL, line=ACCENT, dash=True, radius=0.1)
    text(s, 2.32, 1.45, 2.0, 0.22, [P("SNOWFLAKE", 8.5, ACCENT, bold=True, spc=120)])
    text(s, 2.35, 1.72, 1.55, 0.22, [label("Ingest & score", INK, 8.5)])
    box(2.35, 1.98, 1.55, 0.55, "RAW tables")
    box(2.35, 2.73, 1.55, 0.8, "Snowpark Python proc", "Cortex SENTIMENT + AI_CLASSIFY")
    box(2.35, 3.63, 1.55, 0.62, "Cortex Search", "over 127 review notes")
    text(s, 4.05, 1.72, 1.75, 0.22, [label("Governed layer", INK, 8.5)])
    card(s, 4.05, 1.98, 1.75, 1.0, [
        P("5 Semantic Views", 9.5, WHITE, bold=True, font=SEMI, after=1),
        P("Employee · Org Health · Pay Equity · Voice · Band Health", 8.5, WHITE, after=0),
    ], fill=ACCENT, line=None, anchor=MSO_ANCHOR.MIDDLE, inset=(0.08, 0.04))
    box(4.05, 3.08, 1.75, 0.6, "Metric registry", "29 metrics · 0 unowned")
    box(4.05, 3.78, 1.75, 0.62, "3 scheduled Tasks", "25 tests → governance alerts")
    text(s, 5.95, 1.72, 1.45, 0.22, [label("Serve", INK, 8.5)])
    box(5.95, 1.98, 1.45, 0.8, "Cortex Analyst", "plain English → governed SQL")
    box(5.95, 2.88, 1.45, 0.8, "Streamlit portal", "Employee 360 app")

    # around snowflake
    text(s, 7.75, 1.45, 1.8, 0.25, [label("AROUND SNOWFLAKE")])
    box(7.75, 1.75, 1.8, 0.8, "CoCo CLI", "builds and operates it all, via 2 skills", fill=TINT)
    box(7.75, 2.65, 1.8, 0.8, "MCP server", "6 action tools, dry-run by default")
    box(7.75, 3.55, 1.8, 0.7, "Landing page", "dated snapshot of the views")

    # flow
    arrow(s, 2.0, 2.25, 2.35, 2.25)
    arrow(s, 2.0, 3.3, 2.35, 3.3)
    arrow(s, 2.0, 3.94, 2.35, 3.94)
    arrow(s, 3.125, 2.53, 3.125, 2.73)
    arrow(s, 3.9, 2.25, 4.05, 2.25)
    arrow(s, 3.9, 2.85, 4.05, 2.85)
    arrow(s, 5.8, 2.38, 5.95, 2.38)
    arrow(s, 5.8, 2.93, 5.95, 2.93)
    arrow(s, 7.4, 3.28, 7.75, 3.28)
    arrow(s, 7.75, 2.15, 7.4, 2.15, dash=True)

    card(s, 0.45, 4.7, 9.1, 0.45, [P([
        ("CoCo skill 1  ", {"bold": True}), ("$workforce-astra-data-gen", {"font": MONO, "color": ACCENT}),
        ("  loads the data     ·     ", {}),
        ("CoCo skill 2  ", {"bold": True}), ("$workforce-astra-governance-check", {"font": MONO, "color": ACCENT}),
        ("  runs 25 tests, names owners", {}),
    ], 9, after=0, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)


def skills_slide(s):
    rows = [
        ("Skill 1", "$workforce-astra-data-gen",
         "Generator scripts with a fixed seed; specs for 4 tables",
         "Generate 4 CSVs → verify hard invariants (a gate, not a report) → PUT to stage → COPY INTO",
         "150 workers · 5 bands · 127 reviews · 18 transcripts loaded; the 109 vs 127 proof point holds"),
        ("Skill 2", "$workforce-astra-governance-check",
         "Metric registry (29 owned metrics) and certified golden values",
         "run_metric_tests() → split deterministic vs model-dependent → look up each metric's owner → read Tasks and alerts",
         "25/25 PASS (15 + 10) · owner named for any failure · 3 Tasks started · open alerts explained"),
    ]
    y = 1.45
    for tag, name, i, p, o in rows:
        text(s, 0.45, y, 9.1, 0.28, [P([(tag + "   ", {"bold": True, "color": INK, "font": SEMI}),
                                        (name, {"font": MONO, "color": ACCENT, "bold": True})], 11, after=0)])
        yy = y + 0.33
        for x, w, head, body, fill in ((0.45, 2.6, "INPUT", i, WHITE),
                                       (3.3, 3.3, "PROCESSING", p, TINT),
                                       (6.85, 2.7, "OUTPUT", o, WHITE)):
            card(s, x, yy, w, 1.0, [label(head, size=8, after=2), P(body, 9.5, after=0)], fill=fill)
        arrow(s, 3.05, yy + 0.5, 3.3, yy + 0.5)
        arrow(s, 6.6, yy + 0.5, 6.85, yy + 0.5)
        y += 1.45

    text(s, 0.45, 4.3, 9.1, 0.24, [label("HOW MODULES PLUG TOGETHER")])
    chips = [
        ("Semantic view per domain", "new domain = a view + registry rows + tests"),
        ("Snowpark scoring", "fixed, versioned 8-label reason taxonomy"),
        ("Scheduled Tasks", "daily tests · weekly pay drift · quarterly bands"),
        ("MCP tools", "mocked today; real connector goes behind approval"),
        ("Portable skills", "port by renaming 3 objects"),
    ]
    x = 0.45
    for head, body in chips:
        card(s, x, 4.55, 1.74, 0.62, [P(head, 8.5, INK, bold=True, font=SEMI, after=1),
                                     P(body, 8, MUTED, after=0)],
             fill=WHITE, inset=(0.08, 0.05), anchor=MSO_ANCHOR.MIDDLE)
        x += 1.84


def results_slide(s):
    tiles = [
        ("PAY EQUITY", "−2.8%", "band-adjusted gender pay gap (raw: −16.8%)",
         ["Board and legal read one governed number", "39 of 44 cohorts suppressed (under 5 people)"]),
        ("BAND HEALTH", "37 of 150", "paid below their own band minimum (24.7%)",
         ["0 red circles: the obvious metric misses it", "M1 and IC5 ranges overlap 71%"]),
        ("EMPLOYEE VOICE", "5", "corroborated flight risks: negative, underpaid, rated 4+",
         ["18 interviews scored in Snowpark + Cortex", "Top reason: career growth (6 of 18)"]),
        ("ORG HEALTH", "9.0", "average span of control across 15 managers",
         ["5 managers over 10 direct reports", "Reorg what-if tool is guarded"]),
    ]
    x = 0.45
    for head, big, cap, bullets in tiles:
        card(s, x, 1.5, 2.16, 2.5, [
            label(head, size=9, after=4),
            P(big, 30, ACCENT, bold=True, font=SEMI, after=2),
            P(cap, 10.5, INK, after=8),
            *[P(b, 9.5, MUTED, bullet=True, after=4) for b in bullets],
        ], fill=WHITE)
        x += 2.31
    card(s, 0.45, 4.12, 9.1, 1.08, [
        P([("EMP-0031", {"bold": True, "color": ACCENT, "font": SEMI}),
           ("   exit interview  ·  sentiment −0.53  ·  comp-ratio 0.80  ·  rated 4 of 5", {"color": MUTED})],
          9, after=3),
        P("“I found out in a meeting, by accident, that a colleague who joined after me on the same band "
          "is earning materially more.”", 10.5, INK, italic=True, after=3),
        P("The structured data already said flight risk; only the transcript says why. 5 of the 18 synthetic "
          "interviews were placed on the risk profile deliberately, so the join has something to find.",
          8, MUTED, after=0),
    ])


def governance_slide(s):
    stats = [
        ("29", "metrics in the registry", "0 unowned: every metric has a named owner and a certified definition"),
        ("25/25", "golden-value tests pass", "15 deterministic · 10 pin Cortex model output"),
        ("3", "scheduled Tasks", "daily regression · weekly pay drift · quarterly bands"),
    ]
    y = 1.5
    for big, cap, sub in stats:
        card(s, 0.45, y, 3.0, 1.1, [
            P([(big + "  ", {"size": 22, "bold": True, "color": ACCENT, "font": SEMI}),
               (cap, {"size": 9.5, "color": INK})], after=2),
            P(sub, 8.5, MUTED, after=0),
        ], anchor=MSO_ANCHOR.MIDDLE, fill=WHITE)
        y += 1.22
    rails = [
        ("Model changes can't slip through.",
         "Ten tests pin Cortex output, so a model upgrade fails loudly instead of quietly moving a board number."),
        ("Small cohorts stay private.",
         "Pay figures for cohorts under 5 people are withheld automatically; pay columns are masked."),
        ("No automated pay decisions.",
         "The band auditor only reports: no proposed-pay column, and the MCP tool can't be asked for one."),
        ("Actions are drafts.",
         "All 6 MCP tools default to dry_run = true. Nothing reaches Slack or Workday."),
        ("No real people.",
         "Every record and transcript is synthetic and labelled as such in the data."),
    ]
    y = 1.5
    for lead, body in rails:
        card(s, 3.7, y, 5.85, 0.62, [P([(lead + "  ", {"bold": True, "font": SEMI}), (body, {})], 9.5, after=0)],
             anchor=MSO_ANCHOR.MIDDLE)
        y += 0.705


def impact_slide(s):
    cols = [
        ("MEASURABLE IN THE MVP", [
            "Headcount overstatement caught: 127 vs 109 (+16.5%), resolved to one governed answer",
            "Pay gap explained: 14 points separate the raw −16.8% from the adjusted −2.8%",
            "37 below-minimum employees surfaced that the red-circle metric (0) misses",
            "5 at-risk strong performers flagged, with the reason in their own words",
            "25 automated checks replace manual metric reconciliation",
        ]),
        ("SCALABILITY", [
            "Views, registry and tests don't change as headcount grows; the warehouse scales",
            "A new domain is a view + registry rows + tests, proven five times here",
            "Portal compute suspends when idle; one-command rebuild on a fresh account",
            "The CoCo skills port to another project by renaming 3 objects",
        ]),
        ("BEYOND THE DEMO", [
            "Real Workday and Slack connectors, behind human approval",
            "More domains: learning, hiring funnel, internal mobility",
            "Row-level security by manager hierarchy",
            "A Marketplace starter kit: synthetic data + semantic views",
            "Fits any GCC reconciling parent, centre and vendor definitions",
        ]),
    ]
    x = 0.45
    for head, items in cols:
        card(s, x, 1.5, 2.95, 3.3, [label(head, after=6), *[P(t, 10, bullet=True, after=6) for t in items]],
             fill=WHITE if head != "MEASURABLE IN THE MVP" else TINT, inset=(0.14, 0.12))
        x += 3.075
    text(s, 0.45, 4.88, 9.1, 0.3, [P(
        "To measure in a pilot: time to reconcile board metrics, and time from risk signal to manager action. "
        "MVP figures above are on synthetic data.", 8.5, MUTED, italic=True)])


def stack_slide(s):
    stack = [
        ("Semantic Views", "5 governed domains"),
        ("Cortex Analyst", "plain English → SQL, 0 warnings"),
        ("Cortex Search", "127 review notes"),
        ("Cortex AI SQL", "SENTIMENT, AI_CLASSIFY"),
        ("Snowpark Python", "interview scoring procedure"),
        ("Streamlit in Snowflake", "Employee 360 portal"),
        ("Tasks", "3 scheduled governance jobs"),
        ("CoCo CLI", "2 skills; every DDL applied through it"),
        ("MCP server", "6 tools, mocked, dry-run"),
    ]
    for i, (name, sub) in enumerate(stack):
        x = 0.45 + (i % 3) * 1.9
        y = 1.5 + (i // 3) * 1.02
        card(s, x, y, 1.8, 0.9, [P(name, 10, INK, bold=True, font=SEMI, after=2), P(sub, 8.5, MUTED, after=0)],
             fill=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    card(s, 0.45, 4.6, 5.6, 0.6, [P(
        "Verified live on 26-Sep-2026: a full CoCo CLI run loaded the data, passed 25/25 tests, "
        "returned 109 vs 127 and answered through Cortex Analyst.", 8.5, INK, after=0)],
        anchor=MSO_ANCHOR.MIDDLE)
    card(s, 6.3, 1.5, 3.25, 3.7, [
        label("LINKS", after=6),
        P("Demo video", 9, MUTED, after=0),
        P("[add unlisted YouTube link]", 10, ACCENT, bold=True, after=8),
        P("Code", 9, MUTED, after=0),
        P([("github.com/rahulrao85/Workforce-Astra",
            {"link": "https://github.com/rahulrao85/Workforce-Astra", "color": ACCENT})], 10, after=8),
        P("Live page", 9, MUTED, after=0),
        P([("workforce-astra.rahulrao.in", {"link": "https://workforce-astra.rahulrao.in", "color": ACCENT})],
          10, after=12),
        label("DATASETS", after=4),
        P("All data is synthetic, generated by scripts in the repo; no real person or employer. "
          "Sources and licences: README → Datasets and licences.", 9, after=0),
    ], inset=(0.16, 0.14))


def main():
    prs = Presentation(TPL)
    title_s, guide_s, c1, c2, c3, thanks_s = list(prs.slides)
    layout = title_s.slide_layout
    content_png = next(sh for sh in c1.shapes if sh.shape_type == 13).image.blob

    for sl in (title_s, thanks_s):
        blob = next(sh for sh in sl.shapes if sh.shape_type == 13).image.blob
        replace_background(prs, sl, jpeg(blob))
    title_slide(title_s)

    builders = [
        ("1 · Problem brief", "Three teams, three headcounts, from the same data", problem_slide),
        ("Solution · Employee 360", "One governed definition, so every tool gives the same answer", solution_slide),
        ("2 · Architecture", "Data flow: sources to governed views to action", arch_slide),
        ("2 · Architecture: CoCo CLI skills", "Two reusable CoCo skills, and modules that plug in", skills_slide),
        ("MVP results · synthetic data, live Snowflake", "What the governed views find", results_slide),
        ("Governance & guardrails", "Trust is built in: owned, tested, guarded", governance_slide),
        ("3 · Impact statement", "One number per metric, and actions you can defend", impact_slide),
        ("Built with", "Snowflake-native, built and run through CoCo CLI", stack_slide),
    ]
    for page, (kicker, title, fn) in enumerate(builders, start=2):
        fn(new_content_slide(prs, layout, content_png, kicker, title, page))

    for sl in (guide_s, c1, c2, c3):
        delete_slide(prs, sl)
    lst = prs.slides._sldIdLst
    thanks_id = next(sid for sid in lst if prs.part.related_part(sid.rId) is thanks_s.part)
    lst.remove(thanks_id)
    lst.append(thanks_id)

    OUT.parent.mkdir(exist_ok=True)
    prs.save(OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.2f} MB, {len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
