"""Build the CA-3 project presentation as a .pptx (16:9, 13.333 x 7.5 in).

Palette is content-informed: deep navy / teal for REAL photographs, amber for
GENERATED images, used consistently wherever the two are contrasted.

Writing rules, as for the report: plain sentences, technical terms kept, no em
or en dashes (the build fails if one appears on a slide or in the notes).
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results"
OUT = Path(__file__).resolve().parent / "CA3_Presentation_Geometric_Consistency.pptx"

NAVY = RGBColor(0x12, 0x26, 0x3A)
TEAL = RGBColor(0x1C, 0x72, 0x93)
AMBER = RGBColor(0xE8, 0xA3, 0x3D)
LIGHT = RGBColor(0xF4, 0xF6, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREY = RGBColor(0x5A, 0x66, 0x72)
INK = RGBColor(0x1A, 0x1A, 0x1A)
DARK_CARD = RGBColor(0x1B, 0x33, 0x4C)
PALE = RGBColor(0xB9, 0xCD, 0xDA)

HEAD_FONT = "Cambria"
BODY_FONT = "Calibri"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5


# ------------------------------------------------------------------ helpers
def slide(dark=False):
    s = prs.slides.add_slide(BLANK)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY if dark else WHITE
    bg.line.fill.background()
    bg.shadow.inherit = False
    return s


def textbox(s, x, y, w, h, text, size=16, bold=False, color=INK, font=BODY_FONT,
            align=PP_ALIGN.LEFT, italic=False, anchor=MSO_ANCHOR.TOP, space_after=6):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        r.font.name = font
    return tb


def bullets(s, x, y, w, h, items, size=15, color=INK, space_after=10):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    for i, item in enumerate(items):
        bold = False
        txt = item
        if isinstance(item, tuple):
            txt, bold = item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = "•  " + txt
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        r.font.name = BODY_FONT
    return tb


def title(s, text, sub=None, dark=False):
    textbox(s, 0.7, 0.5, W - 1.4, 0.9, text, size=32, bold=True,
            color=WHITE if dark else NAVY, font=HEAD_FONT)
    if sub:
        textbox(s, 0.7, 1.32, W - 1.4, 0.45, sub, size=14, italic=True,
                color=AMBER if dark else GREY)


def card(s, x, y, w, h, fill=LIGHT, line=None):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line:
        sh.line.color.rgb = line
        sh.line.width = Pt(1.25)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    sh.adjustments[0] = 0.06
    return sh


def stat(s, x, y, w, value, label, color=TEAL, vsize=40, label_color=GREY):
    textbox(s, x, y, w, 0.75, value, size=vsize, bold=True, color=color,
            font=HEAD_FONT, align=PP_ALIGN.CENTER)
    textbox(s, x, y + 0.72, w, 0.7, label, size=11.5, color=label_color, align=PP_ALIGN.CENTER)


def picture(s, fname, x, y, w=None, h=None):
    p = RES / fname
    if not p.exists():
        raise FileNotFoundError(f"results/{fname} is missing; the deck must not ship with a hole")
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    s.shapes.add_picture(str(p), Inches(x), Inches(y), **kw)


def table(s, x, y, w, h, headers, rows, col_w=None, fsize=11):
    shp = s.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y),
                             Inches(w), Inches(h))
    t = shp.table
    if col_w:
        for i, cw in enumerate(col_w):
            t.columns[i].width = Inches(cw)
    for j, htxt in enumerate(headers):
        c = t.cell(0, j)
        c.text = ""
        p = c.text_frame.paragraphs[0]
        r = p.add_run()
        r.text = htxt
        r.font.size = Pt(fsize)
        r.font.bold = True
        r.font.color.rgb = WHITE
        r.font.name = BODY_FONT
        c.fill.solid()
        c.fill.fore_color.rgb = NAVY
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.text = ""
            for k, ln in enumerate(str(val).splitlines() or [""]):
                p = c.text_frame.paragraphs[0] if k == 0 else c.text_frame.add_paragraph()
                r = p.add_run()
                r.text = ln
                r.font.size = Pt(fsize)
                r.font.color.rgb = INK
                r.font.name = BODY_FONT
            c.fill.solid()
            c.fill.fore_color.rgb = WHITE if i % 2 else LIGHT
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
    return t


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


# ================================================================== title
s = slide(dark=True)
textbox(s, 1.0, 2.0, W - 2.0, 0.5, "CA-3 VISION-BASED APPLICATION TASK", size=15,
        bold=True, color=AMBER)
textbox(s, 1.0, 2.6, W - 2.0, 1.5,
        "Geometric Consistency Analysis for Detection of Synthetic Imagery",
        size=36, bold=True, color=WHITE, font=HEAD_FONT)
textbox(s, 1.0, 4.05, W - 2.0, 0.5,
        "Vanishing-Point and Shadow-Based Cues Across Generator Generations",
        size=17, italic=True, color=RGBColor(0xA9, 0xC4, 0xD4))
textbox(s, 1.0, 5.1, W - 2.0, 1.2,
        ["Team: <Name, PRN>   |   <Name, PRN>   |   <Name, PRN>",
         "Course: Computer Vision   |   Department of <Department>, <Institute>",
         "Academic Year 2026-27"],
        size=13, color=RGBColor(0xD6, 0xE2, 0xEA), space_after=4)
notes(s, "Open with the one-line idea: a real photo is made by one camera, an AI image is not, and "
         "that difference can be measured in degrees and pixels.")

# ================================================================== problem
s = slide()
title(s, "Problem Statement")
card(s, 0.7, 1.9, 7.4, 2.2, fill=LIGHT)
textbox(s, 1.0, 2.15, 6.8, 1.8,
        "Given a single image, decide whether its geometry fits ONE pinhole camera. Report any "
        "mismatch as a residual in readable units, compare it with real photographs, and use the "
        "result to compare image generators.", size=16, color=INK)
bullets(s, 0.7, 4.4, 7.4, 2.4, [
    ("Not “is this image fake?” but “which camera rule does it break, and by how much?”", True),
    "Residuals in degrees and ratios, never an opaque score",
    "Every comparison measured against real photographs",
], size=14)
card(s, 8.5, 1.9, 4.1, 4.9, fill=NAVY)
textbox(s, 8.85, 2.2, 3.4, 0.5, "THE CLAIM UNDER TEST", size=12, bold=True, color=AMBER)
textbox(s, 8.85, 2.8, 3.4, 3.7,
        ["Parallel 3D lines meet at one vanishing point.",
         "",
         "Every part of the image implies the same focal length and lens centre.",
         "",
         "All shadows point away from one light source.",
         "",
         "No real camera can break these."],
        size=13.5, color=WHITE, space_after=2)
notes(s, "These rules come from projective geometry, not from habits of photographers, so every "
         "real camera obeys them.")

# ================================================================== motivation
s = slide()
title(s, "Motivation and Background")
for i, (hd, body, col) in enumerate([
    ("Forensic", "Pixel and frequency detectors get worse as generators improve. A broken geometry "
                 "rule stays broken however good the texture is.", TEAL),
    ("Scientific", "Which rules a model follows tells us what it has learned about 3D space.", NAVY),
    ("Applied (Robotics)", "Visual servoing, navigation and structure from motion assume projective "
                           "geometry. Synthetic training data must obey it.", AMBER),
]):
    x = 0.7 + i * 4.12
    card(s, x, 2.0, 3.85, 2.9, fill=LIGHT)
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.3), Inches(2.3), Inches(0.42), Inches(0.42))
    dot.fill.solid(); dot.fill.fore_color.rgb = col; dot.line.fill.background()
    dot.shadow.inherit = False
    textbox(s, x + 0.3, 2.9, 3.25, 0.4, hd, size=17, bold=True, color=NAVY, font=HEAD_FONT)
    textbox(s, x + 0.3, 3.4, 3.25, 1.4, body, size=13, color=GREY)
card(s, 0.7, 5.2, 11.93, 1.5, fill=NAVY)
textbox(s, 1.1, 5.45, 11.1, 1.0,
        "Background: a generator learns what photographs look like from data. Nothing inside it "
        "stores an optical centre, a focal length or a principal point. So whether its images obey "
        "camera geometry is an open question we can measure.",
        size=14, color=WHITE)
notes(s, "The robotics link is the syllabus tie-in: active perception and autonomous vehicles "
         "depend on projective consistency.")

# ================================================================== objectives
s = slide()
title(s, "Objectives")
objs = [
    ("O1", "Build and validate a pipeline for vanishing-point concurrency and single-camera coherence"),
    ("O2", "Measure the normal range of every residual on a hand-picked benchmark and on ordinary "
           "internet photos"),
    ("O3", "Build generated image sets with matched content from four models, settings logged"),
    ("O4", "Define an applicability rule that never looks at the answer, and validate it"),
    ("O5", "Compare generators under matched content and camera settings; test standard classifiers"),
    ("O6", "Implement the shadow rule as a linear program and validate it on synthetic scenes"),
    ("O7", "Build an app that measures any image, explains the result and gives a calibrated score"),
]
for i, (tag, txt) in enumerate(objs):
    y = 1.95 + i * 0.74
    badge = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(y),
                               Inches(0.78), Inches(0.54))
    badge.fill.solid(); badge.fill.fore_color.rgb = TEAL if i % 2 == 0 else NAVY
    badge.line.fill.background(); badge.shadow.inherit = False
    badge.adjustments[0] = 0.2
    tf = badge.text_frame
    tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = tag
    r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = HEAD_FONT
    textbox(s, 1.65, y + 0.08, 11.0, 0.6, txt, size=14.5, color=INK)
notes(s, "O4 is what separates this project from a naive implementation. O7 is the demo.")

# ================================================================== literature
s = slide()
title(s, "Literature Review", "What is established, and by whom")
table(s, 0.7, 2.0, 11.93, 3.6,
      ["Work", "Contribution", "Relevance here"],
      [["Sarkar et al., CVPR 2024",
        "Classifiers on geometric features only (lines, perspective fields, shadows); AUC 0.88 to 0.94",
        "Anchor paper: proves the cue exists, but not which rule fails"],
       ["Kee, O'Brien and Farid, TOG 2013",
        "Shadow consistency as a linear program over wedge constraints",
        "Exact formulation used for our shadow rule"],
       ["Criminisi, Reid and Zisserman, 2000",
        "Single-view metrology from vanishing points",
        "Mathematical basis of the camera test"],
       ["Schindler and Dellaert, CVPR 2004",
        "Atlanta world: one vertical, several horizontal directions",
        "Why our main measure works on real streets"],
       ["Denis, Elder and Estrada, ECCV 2008",
        "York Urban Database: 102 calibrated images with true vanishing points",
        "Our hand-picked real reference and validation set"]],
      col_w=[2.7, 4.9, 4.33], fsize=11)
textbox(s, 0.7, 5.85, 11.93, 0.9,
        "Consensus: generated images break projective geometry. Open: which rule, by how much, and "
        "measured against which real photographs.", size=14, italic=True, color=TEAL)
notes(s, "Sarkar et al. is the paper we extend: from detection to diagnosis.")

# ================================================================== gap
s = slide(dark=True)
title(s, "Identified Research Gap", dark=True)
gaps = [
    ("1", "Detection, not diagnosis", "Learned classifiers say a violation exists, not which "
                                      "rule failed or by how much."),
    ("2", "One real reference", "Studies compare against one hand-picked dataset. Whether the "
                                "conclusion depends on that choice is unexamined."),
    ("3", "Local vs global unmeasured", "No study separates getting the scene's directions wrong "
                                        "from getting the camera wrong."),
    ("4", "Applicability ignored", "The three-vanishing-point test does not apply to non-box-shaped "
                                   "scenes, yet it is applied to them anyway."),
]
for i, (n, hd, body) in enumerate(gaps):
    x = 0.7 + (i % 2) * 6.1
    y = 2.05 + (i // 2) * 2.35
    card(s, x, y, 5.8, 2.0, fill=DARK_CARD)
    textbox(s, x + 0.35, y + 0.22, 0.6, 0.5, n, size=26, bold=True, color=AMBER, font=HEAD_FONT)
    textbox(s, x + 1.0, y + 0.3, 4.5, 0.45, hd, size=16, bold=True, color=WHITE, font=HEAD_FONT)
    textbox(s, x + 1.0, y + 0.85, 4.5, 1.0, body, size=12.5, color=PALE)
textbox(s, 0.7, 6.85, 11.93, 0.4,
        "This project addresses gaps 1 to 3, and solves gap 4 as part of the method.",
        size=13, italic=True, color=AMBER)
notes(s, "Gap 4 turned out to change the results the most.")

# ================================================================== methodology
s = slide()
title(s, "Proposed Methodology", "Each level is one rule a pinhole camera cannot break")
table(s, 0.7, 2.0, 11.93, 3.3,
      ["Level", "Rule", "Residual", "Status"],
      [["L2", "Lines parallel in 3D meet at one vanishing point", "Angle (deg)", "Built"],
       ["L3", "Three directions at right angles fix one focal length and principal point",
        "Deviation from 90 deg", "Built (secondary)"],
       ["L3b", "Every horizontal direction gives the same focal length with the vertical",
        "Spread of log focal length", "PRIMARY measure"],
       ["L7", "All cast shadows agree with one light source", "LP violation (px)",
        "Geometry validated"],
       ["L1, L4 to L6, L8, L9", "Straightness, horizon, cross-ratio, conics, reflections",
        "Various", "Future work"]],
      col_w=[1.7, 5.2, 2.6, 2.43], fsize=11)
card(s, 0.7, 5.6, 11.93, 1.2, fill=LIGHT)
textbox(s, 1.0, 5.82, 11.3, 0.8,
        "Key design decision: the vanishing-point finder is never told to look for right angles. "
        "The camera test asks whether the directions are at right angles, so building that in "
        "would make the test meaningless.",
        size=14, bold=True, color=NAVY)
notes(s, "If asked why L3b is primary: it works in Atlanta worlds (angled streets), where L3 does not.")

# ================================================================== architecture
s = slide()
title(s, "System Architecture and Workflow")
steps = [("Image", TEAL), ("LSD line\ndetection", TEAL), ("RANSAC VP\nestimation", TEAL),
         ("Applicability\nrule", AMBER), ("Residuals\nL2 / L3 / L3b / L7", NAVY),
         ("Compare with real\nphotographs", NAVY)]
bx, by, bw, bh = 0.7, 2.3, 1.78, 1.25
for i, (label, col) in enumerate(steps):
    x = bx + i * (bw + 0.27)
    sh = card(s, x, by, bw, bh, fill=col)
    tf = sh.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(45720)
    for j, ln in enumerate(label.split("\n")):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = ln
        r.font.size = Pt(12.5); r.font.bold = True; r.font.color.rgb = WHITE
        r.font.name = BODY_FONT
    if i < len(steps) - 1:
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + bw + 0.02),
                                Inches(by + bh / 2 - 0.11), Inches(0.23), Inches(0.22))
        ar.fill.solid(); ar.fill.fore_color.rgb = GREY; ar.line.fill.background()
        ar.shadow.inherit = False
textbox(s, 0.7, 3.72, 11.93, 0.55,
        "Images that fail the rule are reported as a selection rate: how often one camera can even "
        "be identified is itself a result about the generator.",
        size=12.5, italic=True, color=AMBER)
card(s, 0.7, 4.35, 5.8, 2.45, fill=LIGHT)
textbox(s, 1.0, 4.55, 5.2, 0.4, "APPLICABILITY RULE (evidence only)", size=12, bold=True, color=NAVY)
bullets(s, 1.0, 5.0, 5.2, 1.7, [
    "3 line families, each ≥ 8% of the line length",
    "each vanishing point pinned to < 1° (bootstrap)",
    "each pair ≥ 10° apart and ≥ 5× its uncertainty",
    "each family spread over ≥ 12% of the diagonal",
], size=12.5, space_after=5)
card(s, 6.83, 4.35, 5.8, 2.45, fill=NAVY)
textbox(s, 7.13, 4.55, 5.2, 0.4, "WHY IT IS NOT CIRCULAR", size=12, bold=True, color=AMBER)
bullets(s, 7.13, 5.0, 5.2, 1.7, [
    "Right angles, focal length and the orthocentre are EXCLUDED",
    "Admitted images: 90% of vanishing points within 5° of the truth (57% for rejected)",
    "Unit test: injecting a camera violation does not change the decision",
], size=12.5, color=WHITE, space_after=5)
notes(s, "The non-circularity test is the answer if anyone asks whether we cherry-picked images.")

# ================================================================== implementation
s = slide()
title(s, "Implementation")
card(s, 0.7, 1.95, 3.7, 4.85, fill=NAVY)
textbox(s, 1.0, 2.2, 3.1, 0.4, "ENVIRONMENT", size=12, bold=True, color=AMBER)
bullets(s, 1.0, 2.7, 3.1, 4.0, [
    "Python 3.14",
    "OpenCV 4.13 (LSD, morphology)",
    "NumPy, SciPy (LP, least squares)",
    "scikit-learn, statsmodels",
    "PyTorch 2.14 + CUDA 13",
    "diffusers 0.40",
    "Streamlit 1.58 (demo app)",
    "RTX 5060 Laptop, 8 GB VRAM",
], size=12.5, color=WHITE, space_after=6)
card(s, 4.65, 1.95, 3.7, 4.85, fill=LIGHT)
textbox(s, 4.95, 2.2, 3.1, 0.4, "PACKAGE  projgeo", size=12, bold=True, color=NAVY)
bullets(s, 4.95, 2.7, 3.1, 4.0, [
    "lines: LSD detection",
    "vp: RANSAC + refinement",
    "selection: applicability rule",
    "camera: focal length, Atlanta test",
    "explain: one image, end to end",
    "stats: confidence intervals",
    "appmodel: the app's score",
    "shadows, synth: L7 and tests",
], size=12.5, space_after=6)
card(s, 8.6, 1.95, 4.03, 4.85, fill=LIGHT)
textbox(s, 8.9, 2.2, 3.4, 0.4, "VALIDATION (25 TESTS)", size=12, bold=True, color=NAVY)
bullets(s, 8.9, 2.7, 3.4, 4.0, [
    "Synthetic scenes with known cameras",
    "4 violation injectors: concurrency, VP shift, drift, two-camera split",
    "Each residual must react to its OWN rule and stay flat for the others",
    "Residuals must rise steadily with the injected violation",
], size=12.5, space_after=7)
notes(s, "explain.py is the single implementation of the measurement: the report's numbers, the "
         "robustness checks and the app all call it, so they cannot disagree.")

# ================================================================== data
s = slide()
title(s, "Data Acquisition", "Matched content by construction; every setting logged")
table(s, 0.7, 1.95, 11.93, 3.3,
      ["Dataset", "Size", "Role"],
      [["York Urban", "102 images", "Hand-picked real reference with true vanishing points"],
       ["Wikimedia Commons", "358 images, 135 camera models",
        "Ordinary real photos, many cameras, EXIF focal lengths"],
       ["Stable Diffusion 1.5", "450 images", "Older open model, run on our GPU"],
       ["SDXL", "650 images", "Newer open model, plus 1:1 and 16:9 variants"],
       ["Gemini (“nano banana”)", "181 images", "Closed frontier model, September 2026"],
       ["ChatGPT image model", "51 images", "Closed frontier model, September 2026"],
       ["Synthetic scenes", "on demand", "Ground truth for testing"]],
      col_w=[2.9, 3.0, 6.03], fsize=11.5)
card(s, 0.7, 5.45, 11.93, 1.5, fill=LIGHT)
textbox(s, 1.0, 5.62, 11.3, 1.2,
        "Three prompt sets. Set 1: building fronts, streets, corridors (also used for Gemini and "
        "ChatGPT). Set 2: corners, to guarantee three directions; too few lines, so selection fell "
        "from 40% to 30%. Set 3 adds repeating straight features (tiles, shelving, window grids) and "
        "reaches 48%. Every comparison uses a single prompt set.",
        size=13, color=INK)
notes(s, "Comparing a model on one prompt set against another model on a different set would mix "
         "up the model with the scene type, so we never do it.")

# ================================================================== results 1
s = slide()
title(s, "Results 1: The Tool Is Trustworthy", "Validation before any comparison")
stat(s, 0.7, 2.1, 2.7, "0.3°", "vanishing-point error on synthetic scenes with known cameras")
stat(s, 3.6, 2.1, 2.7, "< 1%", "focal-length error on synthetic scenes")
stat(s, 6.5, 2.1, 2.7, "81 / 94%", "of York Urban's true vanishing points found within 2° / 5°")
stat(s, 9.4, 2.1, 2.7, "1.02", "median ratio of fitted to TRUE focal length (IQR 0.99 to 1.05)",
     color=AMBER)
picture(s, "commons_focal_validation.png", 1.1, 3.9, h=3.0)
card(s, 5.6, 3.9, 7.0, 3.0, fill=LIGHT)
textbox(s, 5.9, 4.15, 6.4, 2.5,
        ["The pipeline finds the real camera in real photos.", "",
         "Left: fitted focal length against EXIF focal length for photos from 135 camera models. "
         "Dashed lines mark a ±20% band.", "",
         "We need this before trusting anything the tool says about AI images."],
        size=13.5, color=INK, space_after=4)
notes(s, "Without this slide every later number would be uninterpretable.")

# ================================================================== results 2 (the twist)
s = slide(dark=True)
title(s, "Results 2: The Real Reference Decides the Verdict", dark=True)
card(s, 0.7, 2.1, 5.8, 2.0, fill=DARK_CARD)
textbox(s, 1.0, 2.35, 5.2, 1.6,
        ["Measured naively, ORDINARY real photos score 12.2° on the right-angle test: worse "
         "than SD 1.5 and far worse than SDXL.", "",
         "Taken at face value, AI images would look more camera-consistent than photos."],
        size=13.5, color=WHITE, space_after=4)
card(s, 6.83, 2.1, 5.8, 2.0, fill=DARK_CARD)
textbox(s, 7.13, 2.35, 5.2, 1.6,
        ["Why: angled streets and facades have three clear directions that are simply NOT at "
         "right angles.", "",
         "These are Atlanta worlds. The right-angle test does not apply to them. The fault is in "
         "the test, not the photos."],
        size=13.5, color=WHITE, space_after=4)
for i, (val, lab, col) in enumerate([
        ("12.2°", "ordinary real photos, no applicability rule", AMBER),
        ("2.82°", "same photos, after the rule", TEAL),
        ("0.15", "log-focal spread, Atlanta measure", WHITE)]):
    stat(s, 1.5 + i * 3.6, 4.5, 3.0, val, lab, color=col, vsize=36, label_color=PALE)
textbox(s, 0.7, 6.5, 11.93, 0.5,
        "So the main measure became Atlanta focal consistency, which works on both kinds of scene.",
        size=13.5, italic=True, color=AMBER)
notes(s, "This is the method lesson of the project. No filtering on evidence removes the tail: a "
         "stricter threshold makes it worse, and 98% of those photos are uncropped.")

# ================================================================== results 3 headline
s = slide()
title(s, "Results 3: Primary Finding", "Atlanta focal consistency on images that pass the applicability rule")
table(s, 0.7, 1.95, 11.93, 2.3,
      ["Quantity", "York Urban (real)", "Commons (real)", "SD 1.5", "SDXL"],
      [["Images admitted by the rule", "72", "121", "92", "112"],
       ["Usable for log-focal spread", "65", "91", "53", "65"],
       ["Log-focal spread, median [95% CI]", "0.142 [0.106, 0.221]", "0.152 [0.093, 0.220]",
        "0.465 [0.324, 0.709]", "0.355 [0.272, 0.529]"],
       ["Images with an impossible pair", "28%", "44%", "68%", "58%"]],
      col_w=[3.45, 2.12, 2.12, 2.12, 2.12], fsize=11)
card(s, 0.7, 4.5, 11.93, 1.15, fill=NAVY)
textbox(s, 1.0, 4.68, 11.3, 0.85,
        "In a real photo the horizontal directions agree on ONE focal length to within about 15%. "
        "In AI images they disagree by 35 to 60%.  (p ≈ 3×10⁻⁵ against either "
        "real set)", size=16, bold=True, color=WHITE)
bullets(s, 0.7, 5.9, 11.93, 1.2, [
    "The two real sets agree with each other, so the result does not depend on which real photos "
    "are used.",
    "Both generators sit clearly above both real sets, with non-overlapping intervals.",
], size=13.5, space_after=6)
notes(s, "This is the slide to defend. Intervals are bootstrap (2000 resamples); proportions use "
         "Wilson intervals; the test is Mann-Whitney. Line-rich prompt set.")

# ================================================================== results 4 figure + scaling
s = slide()
title(s, "Results 4: Distributions and Scaling")
picture(s, "atlanta_dots_slide.png", 0.7, 1.95, w=7.6)
textbox(s, 0.7, 5.85, 7.6, 0.7,
        "Dots: medians. Lines: 95% intervals. Grey band: the range of the real-photo intervals. "
        "Left: focal disagreement. Right: share of images with a pair no camera could produce.",
        size=11.5, italic=True, color=GREY)
card(s, 8.6, 2.0, 4.03, 4.5, fill=LIGHT)
textbox(s, 8.9, 2.25, 3.4, 0.5, "SD 1.5 → SDXL", size=15, bold=True, color=NAVY, font=HEAD_FONT)
textbox(s, 8.9, 2.85, 3.4, 3.4,
        ["Same prompts, matched field of view and line density, 250 images per model.", "",
         "Orientation: 2.93° → 1.94°   (p = 0.0002, improves)", "",
         "Focal coherence: 0.465 → 0.355   (p = 0.55, UNCHANGED)", "",
         "A bigger model gets the directions right. It does not learn to commit to one camera."],
        size=12.5, color=INK, space_after=3)
notes(s, "Say clearly that the focal result is a null, not a reversal. An earlier claim that "
         "scaling made it worse was withdrawn after we found it used an invalid statistic.")

# ================================================================== results 5 robustness
s = slide()
title(s, "Results 5: Is It an Artefact?", "Two checks, both suggested by looking closely at single images")
card(s, 0.7, 1.95, 5.8, 2.45, fill=LIGHT)
textbox(s, 1.0, 2.15, 5.2, 0.4, "CHECK 1: THE WRONG “VERTICAL”", size=12, bold=True, color=NAVY)
textbox(s, 1.0, 2.6, 5.2, 1.7,
        ["A corridor's far end, near the image centre, can be picked as the vertical vanishing "
         "point by mistake.", "",
         "Require the vertical point to be at least one image height away: 0 to 5% of images "
         "change, every result holds."],
        size=12.5, color=INK, space_after=2)
card(s, 6.83, 1.95, 5.8, 2.45, fill=NAVY)
textbox(s, 7.13, 2.15, 5.2, 0.4, "CHECK 2: LEVEL CAMERAS", size=12, bold=True, color=AMBER)
textbox(s, 7.13, 2.6, 5.2, 1.7,
        ["A level camera makes focal length noisy, and AI images are level far more often "
         "(76 to 80% vs 31 to 51% of real photos).", "",
         "Keep only clearly tilted cameras: AI is still 2 to 3 times worse."],
        size=12.5, color=WHITE, space_after=2)
table(s, 0.7, 4.65, 11.93, 1.6,
      ["Condition", "York Urban", "Commons", "SD 1.5", "SDXL", "Largest p vs real"],
      [["As published", "0.142", "0.152", "0.465", "0.355", "0.0001"],
       ["Vertical point ≥ 1 image height from centre", "0.142", "0.149", "0.465", "0.355", "0.0001"],
       ["Clearly tilted cameras only", "0.135", "0.135", "0.423", "0.285", "0.008"]],
      col_w=[4.4, 1.45, 1.45, 1.45, 1.45, 1.73], fsize=11)
textbox(s, 0.7, 6.5, 11.93, 0.5,
        "Verdict: the main result survives both checks.", size=14, italic=True, bold=True, color=TEAL)
notes(s, "Both checks use only the position of the vertical vanishing point, never the focal length, "
         "so they cannot bias the test. Numbers are median log-focal spread, line-rich prompts.")

# ================================================================== results 6 classifiers
s = slide()
title(s, "Results 6: Detection from Residuals Alone", "Syllabus Unit 3 classifiers on the residuals, never on pixels")
picture(s, "classifier_roc.png", 0.7, 2.05, w=6.4)
table(s, 7.5, 2.0, 5.13, 2.5,
      ["Task (best AUC)", "All", "Admitted"],
      [["York Urban vs SDXL", "0.875", "0.903"],
       ["York Urban vs SD 1.5", "0.919", "0.926"],
       ["Commons vs SDXL", "0.807", "0.808"],
       ["Field of view matched", "0.814", "0.863"]],
      col_w=[2.9, 1.1, 1.13], fsize=12)
card(s, 7.5, 4.75, 5.13, 2.1, fill=LIGHT)
textbox(s, 7.8, 4.92, 4.5, 1.8,
        ["Sarkar et al. report 0.88 to 0.94 with LEARNED features. Readable residuals reach the "
         "same band.", "",
         "Top feature: the orthocentre offset, i.e. where the lens centre sits. Invalid focal "
         "features were removed; AUC moved by at most 0.04."],
        size=12, color=INK, space_after=3)
notes(s, "Six algorithms: logistic regression, decision tree, SVM, random forest, naive Bayes, kNN. "
         "Five-fold stratified cross-validation. The random forest was best in every task.")

# ================================================================== results 7 frontier
s = slide()
title(s, "Results 7: The Newest Models", "Gemini and ChatGPT on the same prompts as SD 1.5 and SDXL")
picture(s, "frontier_dots_slide.png", 0.7, 1.9, h=4.05)
card(s, 6.85, 1.95, 5.78, 4.0, fill=LIGHT)
textbox(s, 7.15, 2.15, 5.2, 0.4, "WHAT IT SHOWS", size=12, bold=True, color=NAVY)
bullets(s, 7.15, 2.6, 5.2, 3.3, [
    ("Both still fail: p ≈ 0.015 against both real sets", True),
    "Not yet shown to be better than SD 1.5 or SDXL (p = 0.14 to 0.26)",
    "Small samples: 31 and 29 usable images",
    "ChatGPT's impossible-pair rate (39%) looks real; its focal spread does not",
], size=14, space_after=10)
card(s, 0.7, 6.1, 11.93, 0.95, fill=NAVY)
textbox(s, 1.0, 6.27, 11.3, 0.65,
        "The 2026 claim that the geometric giveaway has disappeared does not hold on this measure.",
        size=15, bold=True, color=WHITE)
notes(s, "Gemini (nano banana, via Antigravity) and ChatGPT images were made in September 2026 from "
         "the first prompt set, so they are compared with the SD and SDXL images from that same set. "
         "Next step: 250 line-rich prompts per model at full resolution.")

# ================================================================== demonstration
s = slide()
title(s, "Demonstration: One Camera or Not?", "Live app: any image in, a measured and explained answer out")
picture(s, "app_summary.png", 0.7, 1.9, w=6.3)
picture(s, "app_result_card.png", 0.7, 3.95, w=6.3)
card(s, 7.25, 1.9, 5.38, 5.15, fill=LIGHT)
textbox(s, 7.55, 2.1, 4.8, 0.4, "RUN", size=12, bold=True, color=NAVY)
textbox(s, 7.55, 2.5, 4.8, 0.6,
        ["python -m streamlit run app/streamlit_app.py",
         "localhost:8501/?examples=all"],
        size=12, font="Courier New", color=TEAL, space_after=2)
textbox(s, 7.55, 3.25, 4.8, 0.4, "DEMO ORDER (3 MINUTES)", size=12, bold=True, color=NAVY)
bullets(s, 7.55, 3.65, 4.8, 2.2, [
    "Real corridor: 649 and 713 px vs a true 675 px",
    "Gemini classroom: directions disagree by 94%",
    "ChatGPT lecture hall: “unclear”, the hard case",
    "A Gemini image that fools it: a check, not proof",
    "An image it cannot measure, and why",
    "An image from the audience",
], size=12.5, space_after=4)
textbox(s, 7.55, 6.0, 4.8, 0.9,
        "Score: AUC 0.80, well calibrated. Flags 78% of AI images, clears 71% of real photos. "
        "Built-in examples were held out of training.",
        size=12, italic=True, color=GREY)
notes(s, "The app runs the same code as the report. Bookmark the examples link before presenting. "
         "If someone uploads a landscape or a portrait, it will say it cannot measure it: that is "
         "the applicability rule working, not a bug.")

# ================================================================== conclusion
s = slide(dark=True)
title(s, "Conclusion", dark=True)
concl = [
    ("Generators reproduce orientation, not the camera",
     "Right angles are close to real photos after control; focal agreement is 2.5 to 3 times worse."),
    ("The result does not depend on the real reference",
     "A hand-picked benchmark and ordinary internet photos give the same answer."),
    ("Scale is not closing the gap",
     "SD 1.5 → SDXL improves orientation and leaves camera coherence unchanged."),
    ("The newest models still fail",
     "Gemini and ChatGPT remain worse than both real sets; whether they improved is not yet known."),
    ("Applicability must be tested, not assumed",
     "The right-angle test does not apply to angled streets; ignoring that flips the verdict."),
]
for i, (hd, body) in enumerate(concl):
    y = 1.9 + i * 0.98
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.75), Inches(y + 0.1), Inches(0.28), Inches(0.28))
    dot.fill.solid(); dot.fill.fore_color.rgb = AMBER; dot.line.fill.background()
    dot.shadow.inherit = False
    textbox(s, 1.3, y, 11.3, 0.42, hd, size=17, bold=True, color=WHITE, font=HEAD_FONT)
    textbox(s, 1.3, y + 0.45, 11.3, 0.45, body, size=13, color=PALE)
textbox(s, 0.75, 6.95, 11.93, 0.4,
        "Thesis: an AI image looks photographic locally, but there is no single camera behind it.",
        size=14, italic=True, bold=True, color=AMBER)
notes(s, "If asked for one sentence, use the line at the bottom.")

# ================================================================== future
s = slide()
title(s, "Future Scope")
items = [
    ("Powered frontier test", "250 line-rich prompts per model at full resolution, plus Midjourney. "
                              "Prompts and instructions are ready.", TEAL),
    ("Shadow association", "SSIS or SAM 2 to pair shadows with objects; the wedge LP above it is "
                           "built and validated.", NAVY),
    ("Remaining levels", "Horizon, cross-ratio, conics, reflections and agreement with depth "
                         "networks.", TEAL),
    ("Mechanism", "Why does scale not fix the camera? Aspect ratio is ruled out; resolution and "
                  "receptive field remain.", AMBER),
    ("Atlanta-style regional fit", "Redo the regional analysis without assuming every vanishing "
                                   "point pair is at right angles.", NAVY),
    ("Perception study", "Which violations are severe in the maths but unnoticed by people.", TEAL),
]
for i, (hd, body, col) in enumerate(items):
    x = 0.7 + (i % 3) * 4.12
    y = 2.1 + (i // 3) * 2.4
    card(s, x, y, 3.85, 2.05, fill=LIGHT)
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.3), Inches(y + 0.28),
                             Inches(0.36), Inches(0.36))
    dot.fill.solid(); dot.fill.fore_color.rgb = col; dot.line.fill.background()
    dot.shadow.inherit = False
    textbox(s, x + 0.82, y + 0.3, 2.8, 0.4, hd, size=14.5, bold=True, color=NAVY, font=HEAD_FONT)
    textbox(s, x + 0.3, y + 0.85, 3.25, 1.05, body, size=12, color=GREY)
notes(s, "The powered frontier test is the highest-value next step and needs no new code.")

# ================================================================== references
s = slide()
title(s, "References")
refs = [
    "[1] A. Sarkar et al., “Shadows Don’t Lie and Lines Can’t Bend! Generative Models "
    "don’t know Projective Geometry…for now,” CVPR, 2024.",
    "[2] R. Hartley and A. Zisserman, Multiple View Geometry in Computer Vision, 2nd ed., "
    "Cambridge University Press, 2004.",
    "[3] E. Kee, J. F. O’Brien and H. Farid, “Exposing photo manipulation with inconsistent "
    "shadows,” ACM TOG, vol. 32, no. 3, 2013.",
    "[4] A. Criminisi, I. Reid and A. Zisserman, “Single view metrology,” IJCV, vol. 40, "
    "no. 2, pp. 123-148, 2000.",
    "[5] J. M. Coughlan and A. L. Yuille, “Manhattan world,” ICCV, 1999.",
    "[6] G. Schindler and F. Dellaert, “Atlanta world,” CVPR, 2004.",
    "[7] P. Denis, J. H. Elder and F. J. Estrada, “Efficient edge-based methods for estimating "
    "Manhattan frames in urban imagery,” ECCV, 2008.",
    "[8] R. Grompone von Gioi et al., “LSD: a fast line segment detector with a false detection "
    "control,” IEEE TPAMI, vol. 32, no. 4, 2010.",
    "[9] B. Efron and R. J. Tibshirani, An Introduction to the Bootstrap, Chapman & Hall, 1993.",
    "[10] L. Breiman, “Random forests,” Machine Learning, vol. 45, no. 1, 2001.",
    "[11] D. Podell et al., “SDXL: improving latent diffusion models for high-resolution image "
    "synthesis,” ICLR, 2024.",
    "[12] R. Rombach et al., “High-resolution image synthesis with latent diffusion "
    "models,” CVPR, 2022.",
]
tb = s.shapes.add_textbox(Inches(0.7), Inches(1.75), Inches(11.93), Inches(5.0))
tf = tb.text_frame
tf.word_wrap = True
tf.margin_left = tf.margin_right = 0
for i, ref in enumerate(refs):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(7)
    r = p.add_run(); r.text = ref
    r.font.size = Pt(13.5); r.font.color.rgb = INK; r.font.name = BODY_FONT
textbox(s, 0.7, 6.95, 11.93, 0.4,
        "Dataset credits: York Urban Database (Elder Laboratory, York University); Wikimedia Commons "
        "photographs under CC licences, per-image attribution in the project metadata.",
        size=11, italic=True, color=GREY)
notes(s, "The full list (26 references) is in the report. Check details against publisher records "
         "before submission.")


# ------------------------------------------------------------------ checks + save
def _texts(presentation):
    for sl in presentation.slides:
        for shp in sl.shapes:
            if shp.has_text_frame:
                yield shp.text_frame.text
            if shp.has_table:
                for row in shp.table.rows:
                    for c in row.cells:
                        yield c.text
        if sl.has_notes_slide:
            yield sl.notes_slide.notes_text_frame.text


for txt in _texts(prs):
    for bad in ("—", "–"):
        if bad in txt:
            raise ValueError(f"dash {bad!r} found in: {txt[:120]}")

try:
    prs.save(str(OUT))
    saved = OUT
except PermissionError:
    saved = OUT.with_name(OUT.stem + "_v2" + OUT.suffix)
    prs.save(str(saved))
print("written:", saved, "| slides:", len(prs.slides))
