"""Build the CA-3 project presentation as a .pptx (16:9, 13.333 x 7.5 in).

Palette is content-informed: deep navy / teal for REAL photographs, amber for
GENERATED images, used consistently wherever the two are contrasted.
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


def stat(s, x, y, w, value, label, color=TEAL, vsize=40):
    textbox(s, x, y, w, 0.75, value, size=vsize, bold=True, color=color,
            font=HEAD_FONT, align=PP_ALIGN.CENTER)
    textbox(s, x, y + 0.72, w, 0.7, label, size=11.5, color=GREY, align=PP_ALIGN.CENTER)


def picture(s, fname, x, y, w=None, h=None):
    p = RES / fname
    if not p.exists():
        card(s, x, y, w or 4, h or 2.5, fill=RGBColor(0xEE, 0xEE, 0xEE))
        textbox(s, x + 0.2, (y + (h or 2.5) / 2 - 0.2), (w or 4) - 0.4, 0.6,
                f"[INSERT FIGURE: {fname}]", size=11, italic=True, color=GREY,
                align=PP_ALIGN.CENTER)
        return
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    s.shapes.add_picture(str(p), Inches(x), Inches(y), **kw)


def placeholder_note(s, x, y, w, h, text):
    card(s, x, y, w, h, fill=RGBColor(0xFD, 0xF3, 0xE2), line=AMBER)
    textbox(s, x + 0.25, y + 0.22, w - 0.5, h - 0.44,
            "[TO ADD] " + text, size=12, italic=True, color=RGBColor(0x8A, 0x5A, 0x12))


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
            p = c.text_frame.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            r.font.size = Pt(fsize)
            r.font.color.rgb = INK
            r.font.name = BODY_FONT
            c.fill.solid()
            c.fill.fore_color.rgb = WHITE if i % 2 else LIGHT
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
    return t


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


# ================================================================== 1 title
s = slide(dark=True)
textbox(s, 1.0, 2.0, W - 2.0, 0.5, "CA-3 VISION-BASED APPLICATION TASK", size=15,
        bold=True, color=AMBER)
textbox(s, 1.0, 2.6, W - 2.0, 1.5,
        "Geometric Consistency Analysis for Detection of Synthetic Imagery",
        size=36, bold=True, color=WHITE, font=HEAD_FONT)
textbox(s, 1.0, 4.05, W - 2.0, 0.5,
        "Vanishing-Point and Shadow-Based Cues Across Generator Generations",
        size=17, italic=True, color=RGBColor(0xA9, 0xC4, 0xD4))
line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(4.75), Inches(1.6), Pt(3))
line.fill.solid(); line.fill.fore_color.rgb = AMBER; line.line.fill.background()
line.shadow.inherit = False
textbox(s, 1.0, 5.1, W - 2.0, 1.2,
        ["Team: <Name, PRN>   |   <Name, PRN>   |   <Name, PRN>",
         "Course: Computer Vision   |   Department of <Department>, <Institute>",
         "Academic Year 2026-27"],
        size=13, color=RGBColor(0xD6, 0xE2, 0xEA), space_after=4)
notes(s, "State the one-line thesis: a photograph is made by a camera, a generated image is not, "
         "and that difference is measurable in degrees.")

# ================================================================== 2 problem
s = slide()
title(s, "Problem Statement")
card(s, 0.7, 1.9, 7.4, 2.2, fill=LIGHT)
textbox(s, 1.0, 2.15, 6.8, 1.8,
        "Given a single image, decide whether its geometry is consistent with formation by "
        "ONE pinhole camera, express any inconsistency as a residual in interpretable units, "
        "calibrate that residual against real photographs, and use the resulting profile to "
        "compare generative models.", size=16, color=INK)
bullets(s, 0.7, 4.4, 7.4, 2.4, [
    ("Not “is this image fake?” but “which camera rule does it break, and by how much?”", True),
    "Residuals in degrees and ratios, never an opaque score",
    "Every comparison calibrated against real-photograph distributions",
], size=14)
card(s, 8.5, 1.9, 4.1, 4.9, fill=NAVY)
textbox(s, 8.85, 2.2, 3.4, 0.5, "THE CLAIM UNDER TEST", size=12, bold=True, color=AMBER)
textbox(s, 8.85, 2.8, 3.4, 3.7,
        ["Parallel 3D lines meet at one vanishing point.",
         "",
         "Three orthogonal directions fix one focal length and one principal point.",
         "",
         "All shadows point away from one light source.",
         "",
         "No real camera can break these."],
        size=13.5, color=WHITE, space_after=2)
notes(s, "Emphasise that these are consequences of projective geometry, not statistical tendencies.")

# ================================================================== 3 motivation
s = slide()
title(s, "Motivation and Background")
for i, (hd, body, col) in enumerate([
    ("Forensic", "Pixel and frequency detectors degrade as generators improve. A geometric "
                 "violation stays a violation however convincing the texture is.", TEAL),
    ("Scientific", "Which constraints a model satisfies is a probe of what it has internalised "
                   "about 3D structure.", NAVY),
    ("Applied (Robotics)", "Visual servoing, navigation and structure-from-motion assume "
                           "projective consistency. Synthetic training data must be sound.", AMBER),
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
        "Background: a generator learns the appearance statistics of photographs. Nothing in its "
        "architecture represents an optical centre, a focal length or a principal point — so "
        "whether its images obey camera geometry is an open empirical question.",
        size=14, color=WHITE)
notes(s, "The robotics link is the syllabus tie-in: active perception and autonomous vehicles "
         "depend on projective consistency.")

# ================================================================== 4 objectives
s = slide()
title(s, "Objectives")
objs = [
    ("O1", "Build and validate a measurement pipeline for vanishing-point concurrency and "
           "single-camera coherence"),
    ("O2", "Establish real-image null distributions on a curated benchmark and an uncurated "
           "internet corpus"),
    ("O3", "Generate content-matched image sets from multiple diffusion models with logged "
           "parameters"),
    ("O4", "Define an applicability rule, independent of the residual, and validate it against "
           "ground truth"),
    ("O5", "Compare generators under matched content and camera configuration; evaluate standard "
           "classifiers on the residuals"),
    ("O6", "Implement the shadow constraint as a linear program and validate on synthetic scenes"),
]
for i, (tag, txt) in enumerate(objs):
    y = 2.0 + i * 0.83
    badge = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(y),
                               Inches(0.78), Inches(0.58))
    badge.fill.solid(); badge.fill.fore_color.rgb = TEAL if i % 2 == 0 else NAVY
    badge.line.fill.background(); badge.shadow.inherit = False
    badge.adjustments[0] = 0.2
    tf = badge.text_frame
    tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = tag
    r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = HEAD_FONT
    textbox(s, 1.65, y + 0.06, 11.0, 0.7, txt, size=14.5, color=INK)
notes(s, "O4 is the one that separates this project from a naive implementation.")

# ================================================================== 5 literature
s = slide()
title(s, "Literature Review", "What is established, and by whom")
table(s, 0.7, 2.0, 11.93, 3.6,
      ["Work", "Contribution", "Relevance here"],
      [["Sarkar et al., CVPR 2024",
        "Classifiers on geometric features only (lines, perspective fields, shadows); AUC 0.88-0.94",
        "Anchor paper: proves the cue exists, but not which constraint fails"],
       ["Kee, O'Brien & Farid, TOG 2013",
        "Shadow consistency as a linear program over wedge constraints",
        "Exact formulation adopted for our L7 implementation"],
       ["Criminisi, Reid & Zisserman, 2000",
        "Single-view metrology from vanishing points and the absolute conic",
        "Mathematical basis of the camera-coherence test"],
       ["Denis, Elder & Estrada, ECCV 2008",
        "York Urban Database: 102 calibrated images, ground-truth vanishing points",
        "Our curated real reference and validation set"],
       ["Du et al. / Chen et al. / El Banani et al.",
        "Depth, normals and intrinsics are linearly decodable from generative models",
        "Motivates the local-versus-global question"]],
      col_w=[2.5, 5.0, 4.43], fsize=11)
textbox(s, 0.7, 5.85, 11.93, 0.9,
        "Consensus: generated images violate projective geometry. Open: which constraint, by how "
        "much, and measured against which real reference.", size=14, italic=True, color=TEAL)
notes(s, "Sarkar et al. is required reading; our work extends it from detection to diagnosis.")

# ================================================================== 6 gap
s = slide(dark=True)
title(s, "Identified Research Gap", dark=True)
gaps = [
    ("1", "Detection, not diagnosis", "Learned classifiers say a violation exists, not which "
                                      "constraint failed or by how much."),
    ("2", "One real reference", "Studies compare against a single curated dataset. The dependence "
                                "of the conclusion on that choice is unexamined."),
    ("3", "Local vs global unquantified", "No study separates failure of scene orientation from "
                                          "failure of camera intrinsics."),
    ("4", "Applicability ignored", "The three-VP test is undefined for non-Manhattan scenes, yet "
                                   "is applied to them regardless."),
]
for i, (n, hd, body) in enumerate(gaps):
    x = 0.7 + (i % 2) * 6.1
    y = 2.05 + (i // 2) * 2.35
    card(s, x, y, 5.8, 2.0, fill=RGBColor(0x1B, 0x33, 0x4C))
    textbox(s, x + 0.35, y + 0.22, 0.6, 0.5, n, size=26, bold=True, color=AMBER, font=HEAD_FONT)
    textbox(s, x + 1.0, y + 0.3, 4.5, 0.45, hd, size=16, bold=True, color=WHITE, font=HEAD_FONT)
    textbox(s, x + 1.0, y + 0.85, 4.5, 1.0, body, size=12.5, color=RGBColor(0xB9, 0xCD, 0xDA))
textbox(s, 0.7, 6.85, 11.93, 0.4,
        "This project addresses gaps 1-3 and resolves gap 4 as a methodological contribution.",
        size=13, italic=True, color=AMBER)
notes(s, "Gap 4 turned out to be the one that changes results the most.")

# ================================================================== 7 methodology
s = slide()
title(s, "Proposed Methodology", "Each level is one rule a pinhole camera cannot break")
table(s, 0.7, 2.0, 11.93, 3.3,
      ["Level", "Constraint", "Residual", "Status"],
      [["L2", "3D-parallel lines meet at one vanishing point", "Angular deviation (deg)",
        "Implemented"],
       ["L3", "Three orthogonal directions fix one focal length and principal point",
        "Deviation from 90 deg", "Implemented"],
       ["L3b", "Every horizontal VP implies the same focal length with the vertical",
        "Spread of log focal length", "PRIMARY statistic"],
       ["L7", "All cast shadows consistent with one light source", "LP violation (px)",
        "Geometry validated"],
       ["L1, L4-L6, L8-L9", "Straightness, horizon, cross-ratio, conics, reflections",
        "Various", "Specified, future work"]],
      col_w=[1.5, 5.2, 2.7, 2.53], fsize=11)
card(s, 0.7, 5.6, 11.93, 1.2, fill=LIGHT)
textbox(s, 1.0, 5.82, 11.3, 0.8,
        "Key design decision: the vanishing-point estimator is given NO Manhattan or orthogonality "
        "prior. The camera test asks whether the recovered directions are orthogonal — an "
        "estimator that assumed this would make the test vacuous.",
        size=14, bold=True, color=NAVY)
notes(s, "If asked why L3b is primary: it is valid in Atlanta worlds, where L3 is not.")

# ================================================================== 8 architecture
s = slide()
title(s, "System Architecture and Workflow")
steps = [("Image", TEAL), ("LSD line\ndetection", TEAL), ("RANSAC VP\nestimation", TEAL),
         ("Applicability\nrule", AMBER), ("Residuals\nL2 / L3 / L3b / L7", NAVY),
         ("Compare vs real\nnull distribution", NAVY)]
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
        "Rejected images are reported as a selection rate — “how often is a single camera "
        "even identifiable?” is itself a result about the generator.",
        size=12.5, italic=True, color=AMBER)
card(s, 0.7, 4.35, 5.8, 2.45, fill=LIGHT)
textbox(s, 1.0, 4.55, 5.2, 0.4, "APPLICABILITY RULE (evidence only)", size=12, bold=True, color=NAVY)
bullets(s, 1.0, 5.0, 5.2, 1.7, [
    "3 VP families, each ≥ 8% of line length",
    "each localised < 1° (bootstrap)",
    "VP separation ≥ 10° and ≥ 5× its uncertainty",
    "inliers span ≥ 12% of the diagonal",
], size=12.5, space_after=5)
card(s, 6.83, 4.35, 5.8, 2.45, fill=NAVY)
textbox(s, 7.13, 4.55, 5.2, 0.4, "WHY IT IS NOT CIRCULAR", size=12, bold=True, color=AMBER)
bullets(s, 7.13, 5.0, 5.2, 1.7, [
    "Orthogonality, focal length and orthocentre are EXCLUDED",
    "Validated: selected images have 90% of VPs within 5° of ground truth (vs 57% rejected)",
    "Unit test: injecting a camera violation does not change the decision",
], size=12.5, color=WHITE, space_after=5)
notes(s, "The non-circularity test is the thing to stress if a reviewer asks whether we cherry-picked.")

# ================================================================== 9 implementation
s = slide()
title(s, "Implementation")
card(s, 0.7, 1.95, 3.7, 4.85, fill=NAVY)
textbox(s, 1.0, 2.2, 3.1, 0.4, "ENVIRONMENT", size=12, bold=True, color=AMBER)
bullets(s, 1.0, 2.7, 3.1, 4.0, [
    "Python 3.14",
    "OpenCV 4.13 (LSD, morphology)",
    "NumPy / SciPy (LP, least squares)",
    "scikit-learn, statsmodels",
    "PyTorch 2.14 + CUDA 13",
    "diffusers 0.40",
    "RTX 5060 Laptop, 8 GB VRAM",
], size=12.5, color=WHITE, space_after=7)
card(s, 4.65, 1.95, 3.7, 4.85, fill=LIGHT)
textbox(s, 4.95, 2.2, 3.1, 0.4, "PACKAGE  projgeo", size=12, bold=True, color=NAVY)
bullets(s, 4.95, 2.7, 3.1, 4.0, [
    "lines — LSD detection",
    "vp — RANSAC + refinement",
    "camera — L3, Atlanta test",
    "selection — applicability rule",
    "regional — windowed cameras",
    "shadows — wedge LP",
    "synth — scenes + injectors",
], size=12.5, space_after=7)
card(s, 8.6, 1.95, 4.03, 4.85, fill=LIGHT)
textbox(s, 8.9, 2.2, 3.4, 0.4, "VALIDATION (18 TESTS)", size=12, bold=True, color=NAVY)
bullets(s, 8.9, 2.7, 3.4, 4.0, [
    "Synthetic scenes with known cameras",
    "4 violation injectors: concurrency, VP shift, drift, two-camera split",
    "Each residual must respond to ITS OWN constraint and stay flat for others",
    "Residuals must rise monotonically with injected violation",
], size=12.5, space_after=7)
notes(s, "Mention the capped-mean fix: inlier RMS saturates, so it was replaced by an uncensored "
         "statistic verified monotone.")

# ================================================================== 10 data
s = slide()
title(s, "Data Acquisition", "Content-matched by construction; every parameter logged")
table(s, 0.7, 2.0, 11.93, 2.9,
      ["Dataset", "Size", "Role"],
      [["York Urban", "102 images", "Curated real reference with ground-truth vanishing points"],
       ["Wikimedia Commons", "358 images, 135 camera models",
        "Uncurated real reference, diverse cameras, EXIF focal lengths"],
       ["Stable Diffusion 1.5", "450 images", "Older UNet diffusion baseline"],
       ["SDXL", "650 images", "Current-generation baseline, plus 1:1 and 16:9 variants"],
       ["Synthetic scenes", "on demand", "Ground truth for validation and violation injection"]],
      col_w=[2.6, 3.0, 6.33], fsize=11.5)
card(s, 0.7, 5.2, 11.93, 1.6, fill=LIGHT)
textbox(s, 1.0, 5.4, 11.3, 1.25,
        "Prompt strata evolved twice. Stratum 1: facades, streets, corridors. Stratum 2: corners, "
        "to guarantee three visible directions — but these scenes were line-SPARSE and the "
        "selection rate FELL from 40% to 30%. Stratum 3 adds repeating line-rich features (tiles, "
        "shelving, window grids, brick courses) and reaches 48%.",
        size=13.5, color=INK)
notes(s, "The stratum-2 failure is a good example of diagnosing a negative result rather than "
         "discarding it.")

# ================================================================== 11 results 1
s = slide()
title(s, "Results 1: The Instrument Is Trustworthy", "Validation before any comparison")
stat(s, 0.7, 2.1, 2.7, "0.3°", "vanishing-point error on synthetic scenes with known cameras")
stat(s, 3.6, 2.1, 2.7, "< 1%", "focal-length error on synthetic scenes")
stat(s, 6.5, 2.1, 2.7, "81 / 94%", "of York Urban ground-truth VPs recovered within 2° / 5°")
stat(s, 9.4, 2.1, 2.7, "1.02", "median ratio of fitted to TRUE focal length (IQR 0.99-1.05)",
     color=AMBER)
picture(s, "commons_focal_validation.png", 1.1, 3.9, h=3.0)
card(s, 5.6, 3.9, 7.0, 3.0, fill=LIGHT)
textbox(s, 5.9, 4.15, 6.4, 2.5,
        ["The pipeline recovers the real camera of real photographs.", "",
         "Left: fitted focal length against EXIF focal length for photographs from 135 different "
         "camera models. Dashed lines mark a ±20% band.", "",
         "This is the precondition for interpreting any residual measured on generated images."],
        size=13.5, color=INK, space_after=4)
notes(s, "Without this slide, every later number is uninterpretable.")

# ================================================================== 12 results 2 (the twist)
s = slide(dark=True)
title(s, "Results 2: The Real Reference Decides the Verdict", dark=True)
card(s, 0.7, 2.1, 5.8, 2.0, fill=RGBColor(0x1B, 0x33, 0x4C))
textbox(s, 1.0, 2.35, 5.2, 1.6,
        ["Measured naively, UNCURATED real photographs score 12.2° on the camera test — "
         "worse than SD 1.5 and far worse than SDXL.", "",
         "Taken at face value: generated images look more camera-consistent than photographs."],
        size=13.5, color=WHITE, space_after=4)
card(s, 6.83, 2.1, 5.8, 2.0, fill=RGBColor(0x1B, 0x33, 0x4C))
textbox(s, 7.13, 2.35, 5.2, 1.6,
        ["Why: curved streets and oblique facades give three well-supported, distinct VP families "
         "that are simply NOT mutually orthogonal.", "",
         "These are Atlanta worlds. The test is undefined for them — an applicability failure, "
         "not photographic geometry."],
        size=13.5, color=WHITE, space_after=4)
for i, (val, lab, col) in enumerate([
        ("12.2°", "uncurated real, no applicability rule", AMBER),
        ("2.19°", "same images, after the rule", TEAL),
        ("0.15", "log-f spread, Atlanta residual", WHITE)]):
    stat(s, 1.5 + i * 3.6, 4.5, 3.0, val, lab, color=col, vsize=36)
textbox(s, 0.7, 6.5, 11.93, 0.5,
        "Consequence: the primary statistic is changed from Manhattan orthogonality to Atlanta focal "
        "consistency, which is valid in both world models.",
        size=13.5, italic=True, color=AMBER)
notes(s, "This is the methodological heart of the project. Stress that no evidence-based filtering "
         "removes the tail: stricter support makes it worse, and 98% of those photos are uncropped.")

# ================================================================== 13 results 3 headline
s = slide()
title(s, "Results 3: Primary Finding", "Atlanta focal consistency on images that pass the applicability rule")
table(s, 0.7, 2.0, 11.93, 2.2,
      ["Quantity", "York Urban (real)", "Commons (real)", "SD 1.5", "SDXL"],
      [["Images admitted", "72", "121", "92", "112"],
       ["Log-f spread, median [95% CI]", "0.142 [0.106, 0.221]", "0.152 [0.093, 0.220]",
        "0.465 [0.324, 0.709]", "0.355 [0.272, 0.529]"],
       ["Images with an impossible pair", "28%", "44%", "68%", "58%"]],
      col_w=[3.3, 2.3, 2.3, 2.0, 2.03], fsize=11.5)
card(s, 0.7, 4.45, 11.93, 1.15, fill=NAVY)
textbox(s, 1.0, 4.62, 11.3, 0.9,
        "In a real photograph the horizontal directions agree on ONE focal length to within ~15%. "
        "In generated images they disagree by 35-60%.  (p ≈ 3×10⁻⁵ against either "
        "real reference)", size=16, bold=True, color=WHITE)
bullets(s, 0.7, 5.85, 11.93, 1.3, [
    "The two real references agree with each other within their confidence intervals — the "
    "result does not depend on which real set is used.",
    "Both generators sit clearly above both references, with non-overlapping intervals.",
], size=13.5, space_after=6)
notes(s, "This is the slide to defend. The CIs are bootstrap; the proportions use Wilson intervals.")

# ================================================================== 14 results 4 figure
s = slide()
title(s, "Results 4: Distributions and Scaling")
picture(s, "atlanta_scaling.png", 0.7, 2.0, w=7.6)
card(s, 8.6, 2.0, 4.03, 4.5, fill=LIGHT)
textbox(s, 8.9, 2.25, 3.4, 0.5, "SD 1.5 → SDXL", size=15, bold=True, color=NAVY, font=HEAD_FONT)
textbox(s, 8.9, 2.85, 3.4, 3.4,
        ["Identical prompts, matched field of view and line density, 250 images per model.", "",
         "Orientation: 2.93° → 1.94°   (p = 0.0002, improves)", "",
         "Focal coherence: 0.465 → 0.355   (p = 0.55, UNCHANGED)", "",
         "Scaling improves which way the axes point. It does not teach the model to commit to one "
         "camera."],
        size=12.5, color=INK, space_after=3)
textbox(s, 0.7, 6.65, 7.6, 0.5,
        "Left: log-f spread distributions.  Right: share of images containing a VP pair for which "
        "no camera exists.", size=11.5, italic=True, color=GREY)
notes(s, "Be explicit that the focal result is a null, not a reversal — an earlier version of "
         "this claim was withdrawn.")

# ================================================================== 15 results 5 classifiers
s = slide()
title(s, "Results 5: Detection from Residuals Alone", "Syllabus Unit 3 classifiers on the residual vector — never on pixels")
picture(s, "classifier_roc.png", 0.7, 2.05, w=6.4)
table(s, 7.5, 2.2, 5.13, 2.6,
      ["Task", "Best AUC"],
      [["Curated real vs SDXL", "0.916"],
       ["Curated real vs SD 1.5", "0.916"],
       ["Uncurated real vs SDXL", "0.824"],
       ["Field-of-view matched", "0.810"]],
      col_w=[3.5, 1.63], fsize=12)
card(s, 7.5, 5.05, 5.13, 1.8, fill=LIGHT)
textbox(s, 7.8, 5.25, 4.5, 1.45,
        ["Sarkar et al. report 0.88-0.94 with LEARNED geometric features.", "",
         "Interpretable, unit-bearing residuals reach the same band — interpretability costs "
         "little discriminative power."],
        size=12.5, color=INK, space_after=3)
notes(s, "Six algorithms were run: logistic regression, decision tree, SVM, random forest, naive "
         "Bayes, kNN. Five-fold stratified cross-validation.")

# ================================================================== 16 demonstration
s = slide()
title(s, "Demonstration", "Live: one image in, a diagnosed failure out")
card(s, 0.7, 2.0, 5.9, 4.3, fill=LIGHT)
textbox(s, 1.0, 2.25, 5.3, 0.45, "COMMAND", size=12, bold=True, color=NAVY)
textbox(s, 1.0, 2.75, 5.3, 0.5, "python scripts/analyze_image.py <image> --out outputs/",
        size=12.5, font="Courier New", color=TEAL)
textbox(s, 1.0, 3.4, 5.3, 0.45, "OUTPUT", size=12, bold=True, color=NAVY)
bullets(s, 1.0, 3.85, 5.3, 2.2, [
    "Overlay: segments coloured by VP cluster",
    "Vanishing points and the orthocentre vs image centre",
    "JSON of every residual, and a CSV summary row",
], size=12.5, space_after=7)
placeholder_note(s, 6.9, 2.0, 5.73, 2.0,
                 "Screenshot of the terminal running analyze_image.py on one generated image, "
                 "showing the printed residuals.")
picture(s, "example_sdxl_0010_three_cameras.png", 8.05, 4.2, h=1.85)
textbox(s, 6.9, 6.2, 5.73, 0.7,
        "A generated street scene whose three VP pairs imply focal lengths of 1626, 321 and 951 px "
        "— three different cameras in one image.", size=11.5, italic=True, color=GREY)
notes(s, "Have two images ready: one real photograph that passes, one generated image that fails.")

# ================================================================== 17 conclusion
s = slide(dark=True)
title(s, "Conclusion", dark=True)
concl = [
    ("Generators reproduce orientation, not the camera",
     "Manhattan orthogonality is comparable to real photographs after control; focal and principal-"
     "point coherence is 2.5-3× worse."),
    ("The result is robust to the real reference",
     "Both a curated benchmark and uncurated internet photographs give the same conclusion, with "
     "non-overlapping confidence intervals."),
    ("Scale is not closing the gap",
     "SD 1.5 → SDXL improves orientation significantly and leaves camera coherence unchanged."),
    ("Applicability must be tested, not assumed",
     "The three-VP test is undefined for non-Manhattan scenes; ignoring this reverses the verdict."),
]
for i, (hd, body) in enumerate(concl):
    y = 2.05 + i * 1.22
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.75), Inches(y + 0.12), Inches(0.3), Inches(0.3))
    dot.fill.solid(); dot.fill.fore_color.rgb = AMBER; dot.line.fill.background()
    dot.shadow.inherit = False
    textbox(s, 1.3, y, 11.3, 0.45, hd, size=17, bold=True, color=WHITE, font=HEAD_FONT)
    textbox(s, 1.3, y + 0.5, 11.3, 0.65, body, size=13, color=RGBColor(0xB9, 0xCD, 0xDA))
textbox(s, 0.75, 6.95, 11.93, 0.4,
        "Thesis: a generated image is locally photographic but has no single camera behind it.",
        size=14, italic=True, bold=True, color=AMBER)
notes(s, "If asked for one sentence, use the line at the bottom.")

# ================================================================== 18 future
s = slide()
title(s, "Future Scope")
items = [
    ("Frontier models", "Gemini, GPT-image and FLUX on the same prompt set — prompts already "
                        "exported and the analysis is model-agnostic.", TEAL),
    ("Shadow association", "SSIS or SAM 2 for object-shadow pairs; the wedge LP above it is built "
                           "and validated.", NAVY),
    ("Remaining levels", "Cross-ratio, conics, reflections and cross-modal normal agreement.", TEAL),
    ("Mechanism", "Why does scale not fix camera coherence? Aspect ratio is ruled out; resolution "
                  "and latent receptive field remain.", AMBER),
    ("Sheaf formalism", "Consistency radius over a cover of local cameras as a principled "
                        "local-to-global measure.", NAVY),
    ("Perception study", "Which violations are mathematically severe but visually unnoticed.", TEAL),
]
for i, (hd, body, col) in enumerate(items):
    x = 0.7 + (i % 3) * 4.12
    y = 2.1 + (i // 3) * 2.4
    card(s, x, y, 3.85, 2.05, fill=LIGHT)
    bar = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.3), Inches(y + 0.28),
                             Inches(0.36), Inches(0.36))
    bar.fill.solid(); bar.fill.fore_color.rgb = col; bar.line.fill.background()
    bar.shadow.inherit = False
    textbox(s, x + 0.82, y + 0.3, 2.8, 0.4, hd, size=14.5, bold=True, color=NAVY, font=HEAD_FONT)
    textbox(s, x + 0.3, y + 0.85, 3.25, 1.05, body, size=12, color=GREY)
notes(s, "Frontier models are the highest-value next step and need no new code.")

# ================================================================== 19 references
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
    "no. 2, pp. 123–148, 2000.",
    "[5] J. M. Coughlan and A. L. Yuille, “Manhattan world,” ICCV, 1999.",
    "[6] P. Denis, J. H. Elder and F. J. Estrada, “Efficient edge-based methods for estimating "
    "Manhattan frames in urban imagery,” ECCV, 2008.",
    "[7] R. Grompone von Gioi et al., “LSD: a fast line segment detector with a false detection "
    "control,” IEEE TPAMI, vol. 32, no. 4, 2010.",
    "[8] D. Hoiem, A. A. Efros and M. Hebert, “Putting objects in perspective,” IJCV, "
    "vol. 80, no. 1, 2008.",
    "[9] L. Jin et al., “Perspective fields for single image camera calibration,” CVPR, 2023.",
    "[10] D. Podell et al., “SDXL: improving latent diffusion models for high-resolution image "
    "synthesis,” ICLR, 2024.",
    "[11] R. Rombach et al., “High-resolution image synthesis with latent diffusion "
    "models,” CVPR, 2022.",
]
tb = s.shapes.add_textbox(Inches(0.7), Inches(1.95), Inches(11.93), Inches(4.9))
tf = tb.text_frame
tf.word_wrap = True
tf.margin_left = tf.margin_right = 0
for i, ref in enumerate(refs):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(7)
    r = p.add_run(); r.text = ref
    r.font.size = Pt(12); r.font.color.rgb = INK; r.font.name = BODY_FONT
textbox(s, 0.7, 6.9, 11.93, 0.4,
        "Dataset credits: York Urban Database (Elder Laboratory, York University); Wikimedia Commons "
        "photographs under CC licences, per-image attribution in the project metadata.",
        size=11, italic=True, color=GREY)
notes(s, "Verify all reference details against publisher records before submission.")

prs.save(str(OUT))
print("written:", OUT, "slides:", len(prs.slides.__iter__.__self__._sldIdLst))
