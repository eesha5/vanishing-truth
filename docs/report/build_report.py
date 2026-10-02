"""Build the CA-3 project report as a .docx.

Content is the project's own results (docs/projective-geometry-consistency-research-plan.md
sections 7.x); figures come from results/.

Writing rules for this file: plain sentences, technical terms kept and
explained once, no em or en dashes (the build fails if one appears).
Citations are written as {c:key} or {c:key1,key2} and numbered in order of
first appearance; the build fails if a reference is never cited.
"""

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results"
OUT = Path(__file__).resolve().parent / "CA3_Report_Geometric_Consistency.docx"

# ---------------------------------------------------------------- references
REFS = {
    "sarkar": "A. Sarkar, H. Mai, A. Mahapatra, S. Lazebnik, D. A. Forsyth and A. Bhattad, “Shadows Don’t Lie and Lines Can’t Bend! Generative Models don’t know Projective Geometry…for now,” in Proc. IEEE/CVF Conf. Computer Vision and Pattern Recognition (CVPR), 2024.",
    "hz": "R. Hartley and A. Zisserman, Multiple View Geometry in Computer Vision, 2nd ed. Cambridge, U.K.: Cambridge Univ. Press, 2004.",
    "kee": "E. Kee, J. F. O’Brien and H. Farid, “Exposing photo manipulation with inconsistent shadows,” ACM Transactions on Graphics, vol. 32, no. 3, 2013.",
    "farid_persp": "H. Farid, “Perspective (in)consistency of paint by text,” arXiv preprint, 2022.",
    "farid_light": "H. Farid, “Lighting (in)consistency of paint by text,” arXiv preprint, 2022.",
    "desolneux": "A. Desolneux, L. Moisan and J.-M. Morel, From Gestalt Theory to Image Analysis: A Probabilistic Approach. New York, NY, USA: Springer, 2008.",
    "criminisi": "A. Criminisi, I. Reid and A. Zisserman, “Single view metrology,” International Journal of Computer Vision, vol. 40, no. 2, pp. 123-148, 2000.",
    "coughlan": "J. M. Coughlan and A. L. Yuille, “Manhattan world: Compass direction from a single image by Bayesian inference,” in Proc. IEEE Int. Conf. Computer Vision (ICCV), 1999.",
    "schindler": "G. Schindler and F. Dellaert, “Atlanta world: An expectation maximization framework for simultaneous low-level edge grouping and camera calibration in complex man-made environments,” in Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR), 2004.",
    "hoiem": "D. Hoiem, A. A. Efros and M. Hebert, “Putting objects in perspective,” International Journal of Computer Vision, vol. 80, no. 1, pp. 3-15, 2008.",
    "yorkurban": "P. Denis, J. H. Elder and F. J. Estrada, “Efficient edge-based methods for estimating Manhattan frames in urban imagery,” in Proc. European Conf. Computer Vision (ECCV), 2008.",
    "lsd": "R. Grompone von Gioi, J. Jakubowicz, J.-M. Morel and G. Randall, “LSD: A fast line segment detector with a false detection control,” IEEE Trans. Pattern Analysis and Machine Intelligence, vol. 32, no. 4, pp. 722-732, 2010.",
    "lezama": "J. Lezama, R. Grompone von Gioi, G. Randall and J.-M. Morel, “Finding vanishing points via point alignments in image primal and dual domains,” in Proc. CVPR, 2014.",
    "du": "X. Du et al., “Generative models: What do they know? Do they know things? Let’s find out!” in Advances in Neural Information Processing Systems (NeurIPS), 2023.",
    "chen": "Y. Chen, F. Viégas and M. Wattenberg, “Beyond surface statistics: Scene representations in a latent diffusion model,” arXiv preprint, 2023.",
    "elbanani": "M. El Banani et al., “Probing the 3D awareness of visual foundation models,” in Proc. CVPR, 2024.",
    "jin": "L. Jin et al., “Perspective fields for single image camera calibration,” in Proc. CVPR, 2023.",
    "veicht": "A. Veicht et al., “GeoCalib: Learning single-image calibration with geometric optimization,” in Proc. ECCV, 2024.",
    "ldm": "R. Rombach, A. Blattmann, D. Lorenz, P. Esser and B. Ommer, “High-resolution image synthesis with latent diffusion models,” in Proc. CVPR, 2022.",
    "sdxl": "D. Podell et al., “SDXL: Improving latent diffusion models for high-resolution image synthesis,” in Proc. Int. Conf. Learning Representations (ICLR), 2024.",
    "efron": "B. Efron and R. J. Tibshirani, An Introduction to the Bootstrap. New York, NY, USA: Chapman & Hall, 1993.",
    "mannwhitney": "H. B. Mann and D. R. Whitney, “On a test of whether one of two random variables is stochastically larger than the other,” Annals of Mathematical Statistics, vol. 18, no. 1, pp. 50-60, 1947.",
    "wilson": "E. B. Wilson, “Probable inference, the law of succession, and statistical inference,” Journal of the American Statistical Association, vol. 22, no. 158, pp. 209-212, 1927.",
    "breiman": "L. Breiman, “Random forests,” Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.",
    "sklearn": "F. Pedregosa et al., “Scikit-learn: Machine learning in Python,” Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011.",
    "robinson": "M. Robinson, “Sheaves are the canonical data structure for sensor integration,” Information Fusion, vol. 36, pp. 208-224, 2017.",
}
ORDER: list[str] = []
_CITE = re.compile(r"\{c:([a-z0-9_,]+)\}")


def cites(text: str) -> str:
    def sub(m):
        nums = []
        for k in m.group(1).split(","):
            if k not in REFS:
                raise KeyError(f"unknown reference key {k}")
            if k not in ORDER:
                ORDER.append(k)
            nums.append(ORDER.index(k) + 1)
        return "[" + ", ".join(str(n) for n in sorted(nums)) + "]"
    return _CITE.sub(sub, text)


doc = Document()

# ---------------------------------------------------------------- base style
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.line_spacing = 1.15
for sec in doc.sections:
    sec.top_margin = sec.bottom_margin = Inches(1)
    sec.left_margin = sec.right_margin = Inches(1)
for name, size in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 12)):
    s = doc.styles[name]
    s.font.name = "Times New Roman"
    s.font.size = Pt(size)
    s.font.bold = True
    s.font.color.rgb = RGBColor(0, 0, 0)


def para(text, italic=False, bold=False, align=None, size=None):
    p = doc.add_paragraph()
    r = p.add_run(cites(text))
    r.italic, r.bold = italic, bold
    if size:
        r.font.size = Pt(size)
    if align:
        p.alignment = align
    return p


def bullet(text):
    doc.add_paragraph(cites(text), style="List Bullet")


def number(text):
    doc.add_paragraph(cites(text), style="List Number")


def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(cites(text))
    r.italic = True
    r.font.size = Pt(9.5)
    p.paragraph_format.space_after = Pt(12)


def figure(fname, width_in=6.0):
    path = RES / fname
    if not path.exists():
        raise FileNotFoundError(f"results/{fname} is missing; the report must not ship with a hole")
    doc.add_picture(str(path), width=Inches(width_in))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.keep_with_next = True


def table(headers, rows, widths=None, fsize=9.5):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(cites(h))
        run.bold = True
        run.font.size = Pt(fsize)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), "D9E2F3")
        c._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(cites(str(v)))
            run.font.size = Pt(fsize)
    if widths:
        for r in t.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Inches(w)
    short = len(t.rows) <= 10
    for k, r in enumerate(t.rows):
        trPr = r._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if k == 0:
            trPr.append(OxmlElement("w:tblHeader"))
        if short and k < len(t.rows) - 1:          # a short table stays on one page
            for c in r.cells:
                for para_ in c.paragraphs:
                    para_.paragraph_format.keep_with_next = True
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


# ---------------------------------------------------------------- title page
for _ in range(4):
    doc.add_paragraph()
para("CA-3 Vision-Based Application Task", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
para("Geometric Consistency Analysis for Detection of Synthetic Imagery",
     bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=18)
para("Vanishing-Point and Shadow-Based Cues Across Generator Generations",
     italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
doc.add_paragraph()
para("Course: Computer Vision   |   Assessment: CA-3 Project Report", align=WD_ALIGN_PARAGRAPH.CENTER)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Team members: <Name, PRN>   |   <Name, PRN>   |   <Name, PRN>")
r.font.color.rgb = RGBColor(0xC0, 0, 0)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Department of <Department>, <Institute>")
r.font.color.rgb = RGBColor(0xC0, 0, 0)
para("Academic Year 2026-27", align=WD_ALIGN_PARAGRAPH.CENTER)
doc.paragraphs[-1].add_run().add_break(WD_BREAK.PAGE)

# ================================================================ 1
doc.add_heading("1. Introduction", level=1)

doc.add_heading("1.1 Background and Rationale", level=2)
para("A real photograph is made by one camera. Light from the scene passes through one optical centre "
     "and lands on a flat sensor. This is called the pinhole camera model {c:hz}, and it puts hard rules "
     "on what a photo can look like. Lines that are parallel in the real world, like the edges of a "
     "corridor, meet at one point in the image called a vanishing point (VP). The vanishing points of "
     "a box-shaped building tell you the camera's focal length (how zoomed in it was) and its principal "
     "point (where the lens axis hits the sensor). Every shadow in a sunlit scene points away from the "
     "same sun. These rules are not habits of photographers. They come from geometry, so every real "
     "camera obeys them.")
para("Modern text-to-image generators make pictures that look real in texture and colour, but there is "
     "no camera inside them. A diffusion model learns what photos look like from data. Nothing in it "
     "stores a focal length or a principal point. So whether its images still follow the camera rules "
     "is an open question, and it is one we can actually measure, in degrees and pixels, instead of "
     "asking a black-box classifier.")
para("This project builds a tool to do that measurement. We treat every image as a claim that one "
     "pinhole camera took it, and we test that claim against a set of geometric rules. Each test gives "
     "back a residual (how badly the rule is broken) in degrees or as a ratio. So when an image fails, "
     "we can say which rule failed and by how much.")

doc.add_heading("1.2 Motivation", level=2)
para("There are three reasons for this work. Forensics: as generators get better, detectors that look "
     "at pixels or frequency patterns stop working, but a broken geometry rule stays broken no matter "
     "how good the texture is. Science: which rules a generator follows and which it breaks tells us "
     "what it has actually learned about 3D space. Applications: robot navigation, visual servoing and "
     "structure from motion all assume images obey projective geometry, so synthetic images used to "
     "train or test these systems need to be checked first.")

doc.add_heading("1.3 Recent Trends", level=2)
para("Sarkar et al. {c:sarkar} showed in 2024 that generated images break projective geometry badly "
     "enough that a classifier using only geometric features, never pixels, can spot them. Since then, "
     "work has gone two ways. Some generation methods now force vanishing points to be consistent while "
     "the image is made, which shows the field sees perspective errors as a known weakness. Other work "
     "probes generators and finds they do store depth, surface normals and similar 3D information "
     "locally {c:du,chen,elbanani}, which sits uneasily next to the forensic finding that the global "
     "geometry is wrong. In 2026, informal commentary started claiming that this geometric giveaway has "
     "disappeared in the newest models. Nobody had tested that claim properly, and this project does.")

doc.add_heading("1.4 Significance of the Study", level=2)
para("Our contribution is not just another detector. It is a measurement method plus a set of checked "
     "findings. Three things matter. First, the residuals are interpretable, so a result says which rule "
     "failed and by how many degrees. Second, everything is compared against real photographs, using "
     "both a hand-picked dataset and a set of ordinary internet photos. This turned out to be critical, "
     "because some results flip depending on which real photos you compare against. Third, we define an "
     "applicability rule that decides whether an image can be measured at all before looking at the "
     "answer. This stops a common mistake where the test is applied to images it was never meant for.")

# ================================================================ 2
doc.add_heading("2. Review of Relevant Literature", level=1)

doc.add_heading("2.1 Previous Research Work", level=2)
para("Classical single-view geometry. Criminisi, Reid and Zisserman {c:criminisi} showed how to measure "
     "real-world sizes from one image using vanishing points. Coughlan and Yuille {c:coughlan} "
     "introduced the Manhattan world assumption: city scenes are mostly built from three directions at "
     "right angles to each other. Schindler and Dellaert {c:schindler} extended this to Atlanta worlds, "
     "where there is one vertical direction but several horizontal directions that need not be at right "
     "angles, like streets meeting at an angle. Hoiem, Efros and Hebert {c:hoiem} linked the horizon line "
     "to object size. Denis, Elder and Estrada {c:yorkurban} released the York Urban Database: 102 "
     "calibrated photos with hand-labelled lines and true vanishing points, still the standard test set. "
     "Grompone von Gioi et al. {c:lsd} created the Line Segment Detector (LSD), built on the a-contrario "
     "approach of Desolneux, Moisan and Morel {c:desolneux}, which needs no tuning and controls false "
     "detections. We use LSD as our first step. Lezama et al. {c:lezama} detect vanishing points from "
     "point alignments, a different route to the same goal.")
para("Image forensics from geometry. Kee, O'Brien and Farid {c:kee} turned shadow consistency into a "
     "linear programming problem. Each shadow and the object that cast it limit where the light can be "
     "to a wedge-shaped region, and in a real scene all the wedges must overlap. Farid {c:farid_persp,"
     "farid_light} used vanishing points, shadows and reflections on early text-to-image outputs, but "
     "on small samples checked by hand.")
para("Learned geometric detection. Sarkar et al. {c:sarkar} collected generated images that fool pixel "
     "detectors, then trained classifiers on three geometric representations: line segments, "
     "perspective fields and object-shadow pairs. On their hardest subset they report AUC of about 0.88 "
     "to 0.94 for lines, 0.86 to 0.92 for perspective fields and 0.77 to 0.79 for shadows. AUC (area "
     "under the ROC curve) is 0.5 for guessing and 1.0 for perfect.")
para("3D awareness of generators and learned calibration. Du et al. {c:du}, Chen et al. {c:chen} and "
     "El Banani et al. {c:elbanani} show that depth, normals and intrinsic images can be read out of "
     "generator activations with simple linear probes. Jin et al. {c:jin} and Veicht et al. {c:veicht} "
     "estimate camera calibration from a single image with learned models.")

doc.add_heading("2.2 Key Findings from the Literature", level=2)
bullet("Generated images do break projective geometry, enough to be classified from geometric features "
       "alone (Sarkar et al., AUC 0.88 to 0.94 for line features).")
bullet("Shadow consistency can be written exactly as a linear program that allows for annotation "
       "error, so no arbitrary threshold is needed (Kee, O'Brien and Farid).")
bullet("Generators store local 3D structure such as depth and normals, which simple probes can recover.")
bullet("Perspective errors are seen as a known defect, to the point that new methods force vanishing "
       "points to agree during generation.")

doc.add_heading("2.3 Research Gaps", level=2)
para("We found four gaps. This project works on the first three.")
number("Learned classifiers say that an image is fake, but not which geometric rule failed or by how "
       "much. There is no published benchmark that breaks the failure down rule by rule with proper "
       "statistics.")
number("Past studies compare against one real dataset, usually a hand-picked one. Nobody has checked "
       "whether the conclusion changes with the choice of real photos. We found that it does.")
number("The difference between local and global consistency has been talked about but never measured. "
       "In particular, no study separates whether a generator gets scene orientation wrong or gets the "
       "camera itself wrong.")
number("The three-vanishing-point camera test has not been checked on ordinary photos. Scenes that are "
       "not Manhattan worlds give large residuals that say nothing about the camera.")

# ================================================================ 3
doc.add_heading("3. Problem Statement and Objectives", level=1)

doc.add_heading("3.1 Research Questions", level=2)
number("Do images from current diffusion models follow the rules of a single pinhole camera, when "
       "compared with real photos of similar scenes taken with similar camera settings?")
number("If they break the rules, which part fails: the right angles between the scene's main "
       "directions, or the camera's focal length and principal point agreeing across the image?")
number("Does the problem shrink as models get bigger, and do the newest closed models (Google Gemini "
       "and OpenAI's ChatGPT image model) still show it?")
number("Can simple, readable geometric residuals compete with learned classifiers at telling real from "
       "generated?")

doc.add_heading("3.2 Problem Statement", level=2)
para("Given one image, decide whether its geometry fits a single pinhole camera. Report any mismatch as "
     "a readable residual tied to a specific geometric rule. Compare that residual with what the same "
     "pipeline gives on real photos. Use the results to compare different generators.")

doc.add_heading("3.3 Objectives", level=2)
number("O1: Build and validate a pipeline for line-based camera rules, namely vanishing-point "
       "concurrency and single-camera coherence, using ground truth.")
number("O2: Measure the normal range of every residual on real photos, using both a hand-picked "
       "benchmark and a set of ordinary internet photos from many cameras.")
number("O3: Build generated image sets with matched content from several models, two run locally with "
       "every setting logged and two closed frontier models.")
number("O4: Define an applicability rule that decides whether an image can be measured, without using "
       "the residual being measured, and validate it against ground truth.")
number("O5: Compare generators with real photos under matched content and camera settings, and test "
       "standard classifiers on the residuals.")
number("O6: Implement the shadow rule as a linear program and validate it on synthetic scenes with a "
       "known light source.")
number("O7: Build an interactive application that applies the measurement to any uploaded image, "
       "explains its result, and gives a calibrated score with an honest statement of its accuracy.")

doc.add_heading("3.4 Scope and Limitations", level=2)
para("Scope. One image at a time. Two line-based rule levels are built and validated in full "
     "(vanishing-point concurrency and camera coherence), plus a regional camera analysis and the "
     "shadow rule at the geometry level. Four generators are tested: Stable Diffusion 1.5 {c:ldm} and "
     "SDXL {c:sdxl}, run locally, and two closed frontier models, Google Gemini image generation "
     "(\"nano banana\") and OpenAI's image model in ChatGPT. They are compared against two real photo "
     "sets.")
para("Limitations. The frontier models were used through their apps, so their internal settings are "
     "unknown and their sample sizes are smaller than the local models'. Rules that need several views "
     "of a scene, like epipolar geometry, do not apply to single images and are left out on purpose. "
     "The shadow rule is validated geometrically but not run at scale, because automatically matching "
     "each shadow to the object that cast it is not solved in this version. Rule levels for projective "
     "invariants, conics, reflections and agreement with depth networks are specified but not built.")

# ================================================================ 4
doc.add_heading("4. Methodology", level=1)

doc.add_heading("4.1 Overview of Methodology", level=2)
para("The pipeline turns an image into a list of readable geometric residuals in five steps: detect "
     "line segments; find vanishing points without assuming right angles; decide whether the image can "
     "be measured; compute a residual for each rule; and compare against the normal range measured on "
     "real photos. One design choice runs through everything: the vanishing-point finder is never told "
     "to look for three directions at right angles (a Manhattan prior). The camera test asks exactly "
     "whether the directions are at right angles, so building that assumption into the finder would "
     "make the test meaningless.")
figure("architecture.png", 6.4)
caption("Figure 4.1: Overall architecture of the geometric-consistency measurement pipeline.")

doc.add_heading("4.2 Objective-wise Methodology", level=2)
table(["Objective", "Method used", "How it was validated"],
      [["O1 Pipeline",
        "LSD line detection; sequential RANSAC vanishing points refined by angular least squares on the "
        "unit sphere; closed-form and least-squares focal length",
        "Synthetic scenes with known cameras; York Urban true vanishing points"],
       ["O2 Real-photo baseline",
        "Full pipeline on York Urban (102 photos) and Wikimedia Commons (358 photos, 135 camera "
        "models) with EXIF focal lengths",
        "Fitted focal length compared with the EXIF focal length"],
       ["O3 Generated sets",
        "Stable Diffusion 1.5 and SDXL run locally with logged seeds and settings; Gemini and ChatGPT "
        "images from the same prompt list, numbered by prompt",
        "Prompt sets checked image by image against metadata"],
       ["O4 Applicability rule",
        "Support, localisation, separation and spatial spread of each line family, from evidence only",
        "Agreement with York Urban ground truth; unchanged decision under injected violations"],
       ["O5 Comparison and classification",
        "Matched-content and matched field-of-view comparisons; six standard classifiers on residuals",
        "Five-fold cross-validation; bootstrap confidence intervals"],
       ["O6 Shadow rule",
        "Wedge constraints solved as a linear program that minimises the largest violation",
        "Synthetic scenes with a known sun and injected shadow rotations"],
       ["O7 Demonstration app",
        "Streamlit app on the same per-image code; calibrated random forest on ten residuals",
        "Cross-validation, calibration table, leave-one-generator-out test, held-out examples"]],
      widths=[1.4, 3.1, 2.0])
caption("Table 4.1: Each objective, the method used and the validation performed.")

doc.add_heading("4.3 Design: The Constraint Hierarchy", level=2)
para("Each level is one rule a pinhole camera cannot break, with a residual in readable units.")
table(["Level", "Rule", "Residual", "Status"],
      [["L1", "Straight edges in 3D stay straight in the image", "Curvature (px)", "Not built"],
       ["L2", "Lines parallel in 3D meet at one vanishing point", "Angle (deg)", "Built, validated"],
       ["L3", "Three directions at right angles fix one focal length and principal point",
        "Deviation from 90 deg", "Built, validated (secondary)"],
       ["L3b", "Every horizontal direction gives the same focal length when paired with the vertical "
        "(Atlanta worlds)", "Spread of log focal length", "Built; primary measure"],
       ["L4 to L6", "Horizon agreement; projective invariants; circles on planes", "Various",
        "Specified, not built"],
       ["L7", "All shadows agree with one light source", "LP violation (px)",
        "Geometry built and validated"],
       ["L8 to L9", "Reflections; agreement with depth and normal networks", "Degrees",
        "Specified, not built"]],
      widths=[0.7, 3.0, 1.6, 1.2])
caption("Table 4.2: The rule hierarchy, residual units and what was built.")

doc.add_heading("4.4 Materials and Methods", level=2)
doc.add_heading("4.4.1 Hardware and software", level=3)
table(["Component", "Specification"],
      [["Compute", "NVIDIA GeForce RTX 5060 Laptop GPU, 8 GB VRAM; Windows 11"],
       ["Language", "Python 3.14"],
       ["Vision library", "OpenCV 4.13 (Line Segment Detector, morphology, connected components)"],
       ["Maths and statistics", "NumPy, SciPy (least squares, linear programming, statistical tests), "
        "scikit-learn {c:sklearn}, statsmodels, pandas"],
       ["Generative models", "PyTorch 2.14 with CUDA 13.0; diffusers 0.40; Stable Diffusion 1.5 and "
        "SDXL-base-1.0 with CPU offload to fit in 8 GB"],
       ["Project code", "projgeo package: lines, vp, camera, selection, explain, stats, appmodel, "
        "locality, regional, shadows, distortion, prompts, datasets; 25 automated tests"],
       ["Demonstration app", "Streamlit 1.58"]],
      widths=[1.8, 4.7])
caption("Table 4.3: Hardware and software used.")

doc.add_heading("4.4.2 Core algorithms", level=3)
para("Line detection. LSD runs on the greyscale image. Segments shorter than two per cent of the image "
     "diagonal are dropped to remove texture noise. We use standard refinement, because advanced "
     "refinement took up to fifty seconds on some images with no gain in quality.")
para("Vanishing points. Segments are converted to normalised coordinates. Vanishing points are found "
     "one at a time with RANSAC: pick two segments at random (longer ones more likely), take their "
     "intersection as a candidate, and score it by the total length of segments that point at it "
     "within a small angle. The best candidate is refined by weighted least squares on the unit sphere, "
     "which also handles vanishing points at infinity (parallel lines in the image). Its segments are "
     "removed and the search repeats.")
para("Camera coherence (Manhattan test). With the principal point at the image centre, we search for "
     "the one focal length that makes the three vanishing-point directions closest to 90 degrees apart. "
     "The residual is the worst deviation from 90 degrees. For three finite vanishing points, a real "
     "camera's principal point must sit at the orthocentre of the triangle they form {c:hz}, and the "
     "distance between the two is the orthocentre offset.")
para("Atlanta focal consistency (primary measure). A real camera has one focal length f. For any two "
     "vanishing points v1 and v2 of directions at right angles, f squared equals minus the dot product "
     "(v1 minus p) times (v2 minus p), where p is the principal point. The vertical direction is at a "
     "right angle to every horizontal direction, even in an Atlanta world. So we find the vertical "
     "vanishing point (by its direction from the image centre only, never by checking right angles), "
     "pair it with each horizontal vanishing point, and get one focal length per pair. In a real photo "
     "these should all agree. Our statistic is the spread of log f across the pairs. Zero means "
     "perfect agreement. A spread of 0.14 means the largest and smallest focal lengths differ by about "
     "15 per cent. If f squared comes out negative for a pair, no camera at all could produce it, and "
     "we call that an impossible pair.")
para("Uncertainty. Each vanishing point's segments are resampled with replacement and the point is "
     "re-fitted (a bootstrap {c:efron}), giving an angular spread. This separates well-pinned vanishing "
     "points from ones that slide along a family of nearly parallel lines.")

doc.add_heading("4.4.3 The applicability rule", level=3)
para("The camera test only makes sense for images that clearly show three well-separated, "
     "well-supported directions. An image is admitted only if three line families each hold at least "
     "eight per cent of the total line length, each vanishing point is pinned to better than one "
     "degree by the bootstrap, each pair is at least ten degrees apart and at least five times their "
     "uncertainty, and each family's lines spread over at least twelve per cent of the image diagonal. "
     "Real photos must also have a standard sensor aspect ratio, since cropping moves the principal "
     "point. The rule deliberately ignores right angles, focal length and the orthocentre, because "
     "those are what we are measuring.")
para("We checked the rule two ways. On York Urban, admitted images have 90 per cent of their "
     "vanishing points within five degrees of the hand-labelled truth, against 57 per cent for rejected "
     "images. And a unit test injects a camera violation that leaves the lines' layout unchanged and "
     "confirms the admit or reject decision does not change. So the rule cannot be letting real images "
     "through just because they are consistent.")

doc.add_heading("4.5 Data Acquisition", level=2)
table(["Dataset", "Size", "Role", "Source and settings"],
      [["York Urban {c:yorkurban}", "102 photos, 640x480", "Hand-picked real reference with true "
        "vanishing points", "York University; one camera, focal length 675 px"],
       ["Wikimedia Commons", "358 photos, 135 camera models", "Ordinary real photos from many cameras",
        "Commons API; EXIF camera and focal length, landscape, at least 1024 px wide; CC licences "
        "recorded"],
       ["Stable Diffusion 1.5", "200 + 250 images, 640x480", "Older open model",
        "30 steps, guidance 6.0; seed and prompt logged per image"],
       ["SDXL", "200 + 250 + 120 + 80 images", "Newer open model",
        "30 steps, guidance 6.0, CPU offload; 1024x768 plus 1:1 and 16:9 variants"],
       ["Gemini (\"nano banana\")", "181 images (168 at 640x480, 13 larger)", "Closed frontier model",
        "Google Gemini image generation used through Antigravity, September 2026; first prompt set, "
        "numbered by prompt; internal settings not exposed"],
       ["ChatGPT image model", "51 images, 1448x1086", "Closed frontier model",
        "OpenAI image generation in ChatGPT, September 2026; first prompt set, numbered by prompt; "
        "internal settings not exposed"],
       ["Synthetic scenes", "Made on demand", "Ground truth and violation injection",
        "Known camera and rotation; controlled violations of each rule"]],
      widths=[1.3, 1.3, 1.6, 2.3])
caption("Table 4.4: Datasets, their role and how they were collected.")
para("Prompt design. The generated images copy the content of the real sets. The first prompt set "
     "covers building fronts, streets, corridors, lecture halls and offices. A second set asked for "
     "corners where two walls meet, to guarantee three visible directions. A third, line-rich set also "
     "asks for repeating straight features such as tiles, shelving, window grids and brick courses, "
     "because the second set gave scenes that were the right shape but had too few lines to measure. "
     "Every local image has a record of model, prompt, negative prompt, seed, sampler, steps, guidance, "
     "resolution and date. The frontier images were made from the first prompt set, so they are "
     "compared with the local images made from that same set. Comparing them with images from a "
     "different prompt set would mix up the effect of the model with the effect of the scene.")

doc.add_heading("4.6 Implementation", level=2)
para("The system is a Python package with 25 automated tests. Testing is layered. Synthetic scenes "
     "with known cameras check that the estimators find the truth. Violation injectors check that each "
     "residual reacts to its own rule and not to others: one bends line directions to break "
     "concurrency only, one moves a vanishing point so concurrency holds but the camera breaks, one "
     "makes a vanishing point drift across the image, and one splits the image between two cameras. "
     "Each residual must grow steadily as the injected violation grows.")
para("One detail mattered for correctness. The usual inlier RMS residual stops growing once violations "
     "pass the inlier threshold, because badly broken segments just drop out of the inlier set. So we "
     "added a length-weighted capped mean over all segments, plus the share of line length that no "
     "vanishing point explains, and checked both grow steadily over the full range of violations.")
para("The per-image output shows each line family in its own colour, with the focal length each "
     "horizontal direction implies. Figure 4.2 shows this for one real photo and one generated image. "
     "The same code drives the interactive demonstration.")
figure("explain_example.png", 6.4)
caption("Figure 4.2: Per-image output. Yellow lines belong to the vertical vanishing point; each "
        "other colour is one horizontal direction, labelled with the focal length it implies. Left: a "
        "York Urban photo whose two directions give 649 and 713 px against a calibrated 675 px. Right: a "
        "ChatGPT image whose two directions give 563 and 260 px, more than a factor of two apart.")

doc.add_heading("4.7 Demonstration Application", level=2)
para("To show the method working on any image, we built a web application called One Camera or Not? "
     "with Streamlit. A user uploads one or more images, or picks from seven built-in examples. Each "
     "image goes through exactly the same code as the results in Section 5 (projgeo.explain), so the "
     "app and the report cannot disagree.")
para("For each image the app shows the line families in colour, the focal length each horizontal "
     "direction implies, and how the disagreement compares with real photos. If the image fails the "
     "applicability rule, it says \"cannot measure\" and gives the reason in plain words instead of "
     "guessing. It also warns when a reading is unreliable: a camera held almost perfectly level, or "
     "an aspect ratio that suggests the image was cropped.")
para("The app also gives a percentage likely AI-generated. This comes from a random forest "
     "{c:breiman} trained on ten geometric residuals of 625 admitted images, calibrated with Platt "
     "scaling on out-of-fold predictions. The training data is 69 per cent AI images, so the "
     "probability is re-based to a 50/50 prior: the number answers \"if this image were equally "
     "likely to be real or AI before we looked, how likely is AI given its geometry?\" The seven "
     "built-in examples were held out of training, so their scores are honest. Its accuracy is "
     "reported in Section 5.7.")
figure("app_screenshot.png", 5.6)
caption("Figure 4.3: The demonstration application with the seven held-out examples loaded: a "
        "summary ranked by score, and the full result for one image.")

# ================================================================ 5
doc.add_heading("5. Results and Discussion", level=1)

doc.add_heading("5.1 Validation of the Instrument", level=2)
para("Before comparing anything, we checked the tool against known answers. On synthetic scenes, "
     "vanishing points come out within 0.3 degrees and focal length within one per cent. On York Urban, "
     "without being told about right angles, the finder recovers 81 per cent of the true vanishing "
     "points within two degrees and 94 per cent within five. The median ratio of fitted to true focal "
     "length is 1.02, with an interquartile range of 0.99 to 1.05. So the tool finds the real camera in "
     "real photos, which we need before trusting anything it says about generated images.")
table(["Check", "Quantity", "Result"],
      [["Synthetic scenes", "Vanishing-point direction error", "Below 0.3 deg"],
       ["Synthetic scenes", "Focal length error", "Below 1 per cent"],
       ["York Urban", "True VPs recovered within 2 deg / 5 deg", "81 per cent / 94 per cent"],
       ["York Urban", "Fitted focal over true focal, median [IQR]", "1.02 [0.99, 1.05]"],
       ["Commons (EXIF)", "Fitted focal vs EXIF focal, well-conditioned photos",
        "Median +6 per cent; 58 per cent within 20 per cent"],
       ["Violation injection", "Each residual grows with its own violation", "Confirmed for all four"]],
      widths=[1.5, 2.9, 2.1])
caption("Table 5.1: Validation of the pipeline against ground truth.")
figure("commons_focal_validation.png", 3.3)
caption("Figure 5.1: Fitted focal length against EXIF focal length for real photos from 135 camera "
        "models. Dashed lines mark a 20 per cent band.")

doc.add_heading("5.2 Real-Image Null Distributions", level=2)
para("We measured the normal range of each residual on real photos. On York Urban the concurrency "
     "residual has a median of 1.31 degrees and a 95th percentile of 2.46 degrees, and the Manhattan "
     "residual has a median of 0.69 degrees. These are not zero, and assuming they are zero is the most "
     "common mistake when using these tests. We found two causes: lens distortion (a per-image fit of "
     "one radial coefficient agrees with a fit over the whole dataset) and the fact that real buildings "
     "are only roughly box-shaped.")
figure("yorkurban_ecdf.png", 6.0)
caption("Figure 5.2: Cumulative distributions of each residual on the hand-picked real set, with the "
        "estimator-only floor for comparison.")

doc.add_heading("5.3 The Decisive Role of the Real Reference", level=2)
para("The Commons photos gave the most important method lesson of the project. With no applicability "
     "rule, ordinary real photos score a median Manhattan residual of 12.2 degrees. That is worse than "
     "Stable Diffusion 1.5 and much worse than SDXL. Taken at face value it would mean generated images "
     "are more camera-consistent than real photos, which cannot be right.")
para("Looking at the worst photos explains it. They are angled streets, neighbouring buildings at odd "
     "angles, and fronts seen almost straight on. These scenes have three clear, well-supported "
     "directions that simply are not at right angles to each other. They are Atlanta worlds "
     "{c:schindler}, not Manhattan worlds, and the three-direction right-angle test does not apply to "
     "them. The problem is with the test, not the photos. Filtering on evidence does not fix it: a "
     "stricter support threshold makes it worse, and 98 per cent of these photos already have standard "
     "aspect ratios, so cropping is not the cause. Figure 5.3 shows this. Photos (e) and (f) score 79 "
     "and 50 degrees on the Manhattan test, yet their directions agree on focal length to within 13 and "
     "5 per cent on the Atlanta test.")
figure("commons_montage_credited.png", 6.4)
caption("Figure 5.3: Real Commons photos admitted by the applicability rule, at low, moderate and very "
        "high Manhattan residual, with the Atlanta disagreement for each. Photos from Wikimedia Commons, "
        "resized: " + (RES / "commons_montage_credited.txt").read_text(encoding="utf-8") + ".")
para("We made two changes as a result, and both are used below. Images are only measured if they pass "
     "the applicability rule of Section 4.4.3; this brings the Commons median Manhattan residual down "
     "from 12.2 to 2.82 degrees. And the main measure is switched from the Manhattan test to Atlanta "
     "focal consistency, which works on both kinds of scene.")

doc.add_heading("5.4 Primary Result: Camera Coherence", level=2)
para("The main comparison uses Atlanta focal consistency on images that pass the applicability rule, "
     "with the line-rich prompt set for the generators. Medians come with bootstrap 95 per cent "
     "confidence intervals {c:efron}, proportions with Wilson intervals {c:wilson}, and differences are "
     "tested with the Mann-Whitney test {c:mannwhitney}.")
table(["Quantity", "York Urban (real)", "Commons (real)", "SD 1.5", "SDXL"],
      [["Images admitted by the rule", "72", "121", "92", "112"],
       ["With two or more horizontal directions", "72", "120", "87", "109"],
       ["Usable for log-focal spread", "65", "91", "53", "65"],
       ["Log-focal spread, median [95% CI]", "0.142 [0.106, 0.221]", "0.152 [0.093, 0.220]",
        "0.465 [0.324, 0.709]", "0.355 [0.272, 0.529]"],
       ["Images with an impossible pair", "28% [19, 39]", "44% [36, 53]", "68% [57, 77]",
        "58% [48, 66]"],
       ["Manhattan residual (secondary)", "0.65 deg", "2.82 deg", "2.93 deg", "1.94 deg"]],
      widths=[2.0, 1.15, 1.15, 1.1, 1.1], fsize=8.8)
caption("Table 5.2: Atlanta focal consistency on admitted images (line-rich prompt set for the "
        "generators). \"Usable\" counts images where at least two pairs give a real focal length.")
figure("atlanta_dots.png", 6.4)
caption("Figure 5.4: Median log-focal spread (left) and share of images with at least one pair no "
        "camera could produce (right), with 95 per cent intervals. The shaded band spans the two real "
        "sets' intervals. n is the number of images usable for the log-focal spread.")
para("The two real sets agree with each other within their confidence intervals (0.142 and 0.152). "
     "Both generators sit clearly higher (0.355 and 0.465), and the intervals do not overlap. The "
     "Mann-Whitney test gives p of about 3 × 10⁻⁵ against either real set. In plain words: in a real "
     "photo, the horizontal directions agree on one focal length to within about 15 per cent. In a "
     "generated image they disagree by 35 to 60 per cent. This holds against the hand-picked set and "
     "against ordinary internet photos, which is what makes it believable.")
para("The share of images with an impossible pair rises from 28 per cent (hand-picked real) to 44 per "
     "cent (ordinary real) to 58 and 68 per cent (generated). This is a steady rise, not a clean split, "
     "so the log-focal spread is the better statistic.")

doc.add_heading("5.4.1 Robustness checks", level=3)
para("We ran two checks on the main measure. Both came from looking closely at single images.")
para("Check 1: picking the wrong vertical. The vertical vanishing point is chosen by its direction from "
     "the image centre. A vanishing point sitting near the centre, like the far end of a corridor seen "
     "head-on, can point in any direction and get picked by mistake. A real vertical vanishing point is "
     "only that close to the centre if the camera points steeply up or down. So we repeated the analysis "
     "requiring the vertical vanishing point to be at least one image height from the centre. This uses "
     "only its position, never the focal length, so it cannot bias the test. Only 0 to 5 per cent of "
     "images in any set were affected, and every result kept its size and significance.")
para("Check 2: nearly level cameras. When a camera is held almost exactly level, vertical lines are "
     "almost parallel and their vanishing point is very far away. The focal-length formula then "
     "multiplies a tiny number by a huge one, so small errors are magnified. Generated images are level "
     "far more often than real photos: 76 to 80 per cent of SD 1.5 and SDXL images have their vertical "
     "vanishing point more than 20 image heights away, against 31 to 51 per cent of real photos. If that "
     "alone raised their scores, the main result would be an artefact. It does not. Within each set, "
     "levelness is only weakly related to the score (Spearman rho 0.0 to 0.3, mostly not significant). "
     "And keeping only clearly tilted cameras (vertical vanishing point within 50 image heights), "
     "generated images are still two to three times worse than real photos, with p of 0.008 or less.")
table(["Condition", "York Urban", "Commons", "SD 1.5", "SDXL", "Largest p vs real"],
      [["As published", "0.142 (65)", "0.152 (91)", "0.465 (53)", "0.355 (65)", "0.0001"],
       ["Vertical VP at least 1 image height from centre", "0.142 (65)", "0.149 (88)", "0.465 (53)",
        "0.355 (65)", "0.0001"],
       ["Clearly tilted cameras only (vertical VP within 50 image heights)", "0.135 (52)",
        "0.135 (74)", "0.423 (23)", "0.285 (27)", "0.008"]],
      widths=[2.3, 0.85, 0.85, 0.85, 0.85, 0.8], fsize=8.6)
caption("Table 5.3: Median log-focal spread under two robustness checks, line-rich prompt set. Usable "
        "images in brackets. The last column is the largest Mann-Whitney p of either generator against "
        "either real set.")
para("The frontier models of Section 5.5.1 stay worse than real photos under both checks. Under check "
     "1 nothing changes (p 0.014 to 0.020). On the tilted-only subset their samples shrink to 19 and 23 "
     "images and p rises to between 0.02 and 0.07, so that part needs the larger planned run.")

doc.add_heading("5.5 Comparative Analysis Across Generators", level=2)
para("Stable Diffusion 1.5 and SDXL were compared on the same 250 line-rich prompts, with matched field "
     "of view and line density. This separates two abilities that usually get lumped together.")
table(["Measure", "SD 1.5", "SDXL", "p", "Reading"],
      [["Manhattan residual", "2.93 deg", "1.94 deg", "0.0002", "Gets better with the bigger model"],
       ["Atlanta log-focal spread", "0.465", "0.355", "0.55 (not significant)", "No change"],
       ["Images with an impossible pair", "68%", "58%", "0.18 (not significant)", "No change"]],
      widths=[1.8, 0.9, 0.9, 1.3, 1.6])
caption("Table 5.4: SD 1.5 against SDXL on identical prompts. 87 and 109 images have two or more "
        "horizontal directions; 53 and 65 of them give a usable log-focal spread.")
para("Going from SD 1.5 to SDXL makes the scene's right angles clearly better, but camera coherence "
     "does not change and stays about two and a half to three times worse than real photos. So "
     "orientation improves with a bigger model, and camera coherence does not. Size alone does not "
     "look like it will fix the problem.")

doc.add_heading("5.5.1 Frontier models: Gemini and ChatGPT", level=3)
para("To test the 2026 claim that the newest models no longer have this giveaway, we ran 181 prompts "
     "through Google Gemini image generation and 51 through OpenAI's image model in ChatGPT. All came "
     "from the first prompt set, so they are compared with the SD 1.5 and SDXL images made from that "
     "same set, image for image by prompt number.")
table(["Quantity", "York Urban", "Commons", "SDXL", "SD 1.5", "Gemini", "ChatGPT"],
      [["Images admitted", "72", "121", "79", "61", "58", "36"],
       ["Usable for log-focal spread", "65", "91", "38", "44", "31", "29"],
       ["Log-focal spread, median", "0.142", "0.152", "0.593", "0.592", "0.338", "0.491"],
       ["95% CI", "[0.106, 0.221]", "[0.093, 0.220]", "[0.355, 0.933]", "[0.381, 0.841]",
        "[0.182, 0.652]", "[0.320, 0.634]"],
       ["p vs York Urban / Commons", "", "", "7×10⁻⁵ / 1×10⁻⁴", "3×10⁻⁵ / 2×10⁻⁵", "0.016 / 0.018",
        "0.014 / 0.015"],
       ["Images with an impossible pair", "28%", "44%", "67%", "55%", "61%", "39%"],
       ["Share of images admitted", "71%", "34%", "40%", "30%", "32%", "71%"]],
      widths=[1.55, 0.8, 0.8, 0.8, 0.8, 0.85, 0.85], fsize=8.2)
caption("Table 5.5: Frontier models against the real sets and against SD 1.5 and SDXL on the same "
        "prompts (first prompt set).")
figure("frontier_dots.png", 6.4)
caption("Figure 5.5: The frontier models beside both real sets and the local models on the same "
        "prompts. Same layout as Figure 5.4.")
para("The giveaway has not gone away. Both frontier models are significantly worse than both real "
     "sets (p between 0.014 and 0.018). On this measure the newest models still do not commit to one "
     "camera.")
para("We cannot say the frontier models are better than SD 1.5 and SDXL. Their medians are lower "
     "(0.338 and 0.491 against about 0.59), but none of the model-to-model differences is significant: "
     "Gemini against SDXL p = 0.26, against SD 1.5 p = 0.14; ChatGPT against SDXL p = 0.23, against "
     "SD 1.5 p = 0.15. With only 29 to 44 usable images per model the test does not have enough power. "
     "The evidence against the frontier models is also about a thousand times weaker than against the "
     "older models (p near 0.015 against p near 3 × 10⁻⁵). Part of that is real narrowing and part is "
     "the smaller sample.")
para("Two side notes. ChatGPT's impossible-pair rate (39 per cent) falls between the two real sets, so "
     "on that statistic alone it looks like a real photo, but its focal spread is still high. And "
     "ChatGPT images were admitted twice as often as Gemini images (71 against 32 per cent). ChatGPT "
     "delivers 1448 px wide images that we shrink to 640 px, while most Gemini images arrived at 640 px. "
     "Larger originals give cleaner lines after shrinking, so this gap is probably about the "
     "measurement, not the model. Within Gemini, its 12 larger images were admitted 58 per cent of the "
     "time against 30 per cent for the small ones.")

doc.add_heading("5.6 Where the Inconsistency Lives", level=2)
para("Two more analyses look at where in the image the problem is. The regional analysis fits a "
     "separate camera inside each cell of an overlapping three by three grid and measures how much the "
     "cells disagree. It reports a consistency radius, the smallest distance such that one camera lies "
     "within that distance of every local camera, an idea taken from sheaf theory {c:robinson}. On the "
     "hand-picked real set against SDXL, generated images show much more disagreement in focal length "
     "between regions, and the gap grows with window size, while real photos settle on one camera.")
para("This result comes with a caveat we found while preparing this report. Each local camera is "
     "fitted by choosing the focal length that makes all the cell's vanishing points as close to right "
     "angles as possible. That is the Manhattan assumption again. It holds for York Urban by design, "
     "but it has not been checked for generated images that may contain Atlanta-style angled "
     "directions, where it would make the local focal lengths wrong. So we report this result but do "
     "not count it as independent evidence until it is redone with an Atlanta-style local fit.")
para("A second analysis tests whether the error is a smooth drift across the image within one line "
     "family, using the spatial correlation of signed angular residuals. This statistic is the same for "
     "real and generated images in every set. So the error is not a gradual warping of the picture. It "
     "is disagreement between separate structures and regions.")
figure("scale_curve_sdxl_vs_real.png", 6.0)
caption("Figure 5.6: Disagreement in implied focal length between image regions as window size grows, "
        "York Urban against SDXL. Subject to the fitting caveat in the text.")

doc.add_heading("5.7 Classification from Geometric Residuals", level=2)
para("To compare with learned detectors, we trained six standard classifiers on the residual list "
     "alone, never on pixels, and scored them with five-fold stratified cross-validation using "
     "scikit-learn {c:sklearn}. The geometry features are grouped as line concurrency (L2), Atlanta "
     "focal consistency, Manhattan right angles (including the orthocentre offset) and locality. Camera "
     "settings and content descriptors such as field of view and segment count are kept out of the "
     "geometry-only score.")
para("We also removed every feature that turns a pair of vanishing points into a focal length without "
     "knowing the pair is at right angles (the old focal spread, its bootstrap version and the count of "
     "negative f squared), plus all regional features for the reason given in Section 5.6. Removing "
     "them lowered the best AUC by at most 0.04, so detection never depended on them.")
table(["Task", "All images", "Admitted images only"],
      [["York Urban (real) vs SDXL", "0.875", "0.903"],
       ["York Urban (real) vs SD 1.5", "0.919", "0.926"],
       ["Commons (real) vs SDXL", "0.807", "0.808"],
       ["All real vs all generated", "0.804", "0.833"],
       ["Field of view matched (40 to 60 deg)", "0.814", "0.863"]],
      widths=[2.8, 1.6, 1.9])
caption("Table 5.6: Best cross-validated AUC from geometry features only. The random forest {c:breiman} "
        "was best in every task.")
figure("classifier_roc.png", 5.6)
caption("Figure 5.7: ROC curves for detection from geometric residuals alone, valid features only.")
para("Sarkar et al. {c:sarkar} report about 0.88 to 0.94 AUC for their learned line classifier. Our "
     "readable residuals reach 0.88 to 0.93 against the hand-picked set and about 0.81 to 0.86 in the "
     "two hardest cases, ordinary real photos and matched field of view. The point is not to win on AUC "
     "but to show that readable residuals cost little in accuracy.")
para("Two cautions. On York Urban, camera and content features alone reach about 0.88 to 0.90, because "
     "every York Urban photo comes from one camera with one field of view. That is why the Commons and "
     "field-of-view matched numbers are the honest ones. And the most useful single feature is the "
     "orthocentre offset (it lowers AUC by 0.11 when shuffled; nothing else passes 0.01). That is about "
     "where the principal point sits, which fits our claim that the camera is wrong, but it points at "
     "the principal point rather than the focal length, and it is a Manhattan measure. On its own, the "
     "Atlanta measure is only a moderate per-image detector (AUC 0.61 to 0.74), even though it "
     "separates the groups very clearly. It is a strong population test and a weak single-image test.")
para("The application's calibrated score (Section 4.7) was evaluated the same way. Table 5.7 gives its "
     "accuracy. Its percentages are well calibrated: images shown at 80 to 100 per cent are AI images "
     "about 80 per cent of the time, and those shown below 20 per cent about 11 per cent of the time. "
     "ChatGPT images are the hard case, barely better than guessing per image, which matches the "
     "finding in Section 5.5.1 that their impossible-pair rate looks like a real photo's.")
table(["Measure", "Value"],
      [["Cross-validated AUC, all admitted images", "0.80"],
       ["At the 50 per cent line", "78% of AI images flagged; 71% of real photos cleared"],
       ["AUC, real photos vs SD 1.5 / SDXL / Gemini / ChatGPT", "0.84 / 0.81 / 0.76 / 0.59"],
       ["AUC on a generator never seen in training, same order", "0.82 / 0.77 / 0.77 / 0.63"]],
      widths=[3.6, 2.9])
caption("Table 5.7: Accuracy of the demonstration application's per-image score, five-fold "
        "cross-validated on 625 admitted images.")

doc.add_heading("5.8 Shadow Consistency", level=2)
para("The shadow rule follows the wedge method of Kee, O'Brien and Farid {c:kee}. A shadow point and "
     "the object area that could have cast it define a wedge of possible light positions, written as "
     "two half-planes. In a real scene all wedges must overlap. We solve it as a linear program that "
     "minimises the largest half-plane violation, so the answer is a violation in pixels rather than a "
     "yes or no. On synthetic scenes with a known sun, the light position is recovered exactly, the "
     "violation grows steadily as shadows are rotated, and allowing more annotation error always makes "
     "the test more lenient, which is what makes it safe to use with hand annotations.")
para("Shadow detection uses classic steps: a grey-value transform that uses the fact that shadows are "
     "darker and bluer, Otsu thresholding, morphological closing and opening sized to the image "
     "diagonal, and connected components with an area filter.")
figure("example_shadow_mask_works.png", 6.0)
caption("Figure 5.8: Shadow detection on a sunlit SDXL image. Cast shadows on the wall are found, but "
        "so is the dark garage interior, which shows why shadows must be matched to objects before the "
        "rule can be used.")
para("We also tried to skip manual annotation by checking whether the long axes of shadow regions "
     "meet at the sun's vanishing point. We rejected this. Real photos already score 14 degrees on it, "
     "and SD 1.5 scores better than real photos, which means it measures the detector, not the light. "
     "The mask reacts to dark glass, signs and shaded rooms as much as to cast shadows (Figure 5.8). So "
     "the shadow rule needs real shadow-to-object matching, by instance shadow detection or by hand, "
     "before it can join the comparison.")

doc.add_heading("5.9 Interpretation of Results", level=2)
para("Two lines of evidence stand up cleanly. The Atlanta focal-consistency comparison shows generated "
     "images do not agree on one focal length, against two different real sets. And the SD 1.5 to SDXL "
     "comparison shows orientation improving while focal coherence does not. Together they say the "
     "weakness of current generators is not getting the scene's directions right, but committing to one "
     "camera across the whole image. A third line, the classifier, agrees that the camera is the "
     "problem but points at the principal point. A fourth, the regional analysis, agrees in direction "
     "but rests on an assumption we have not yet checked for generated images.")
para("This is a narrower claim than a quick comparison would give, and it is the one that survives "
     "controlling for content, camera settings and choice of real photos. It also makes sense "
     "mechanically. The direction of a line family can be judged from any small patch of the image, "
     "but the focal length depends on how far apart the vanishing points are, so the whole image has to "
     "be combined into one consistent picture. A model that builds images out of locally convincing "
     "pieces would get the first right and the second wrong.")

doc.add_heading("5.10 Significance of Findings", level=2)
bullet("A measurement method that says which camera rule failed and by how much, instead of one opaque "
       "score.")
bullet("Evidence that the choice of real photos can flip the direction of a comparison, which is a "
       "warning for the field.")
bullet("An applicability rule with a non-circularity test, validated against ground truth, that makes "
       "the camera test usable on ordinary photos.")
bullet("A replicated result that generated images are two and a half to three times worse than real "
       "photos at camera coherence while matching them on orientation.")
bullet("Evidence that the newest closed models, Gemini and ChatGPT, still fail this test against both "
       "real sets.")
bullet("Evidence that a bigger model fixes orientation but not camera coherence.")
bullet("A working application that applies the method to any image and reports when it cannot.")

doc.add_heading("5.11 Limitations", level=2)
para("The frontier samples are small (29 and 31 usable images), were made from the less line-rich "
     "prompt set, came at different resolutions, and were generated with settings we cannot see. A "
     "larger run of 250 line-rich prompts per model at full resolution is the next step. The shadow "
     "rule is not run at scale. Generated images are shrunk to 640 px to match York Urban, and the "
     "effect of this on line detection has not been isolated, although the Commons comparison is "
     "resolution-matched and agrees. The regional analysis needs an Atlanta-style local fit. Several "
     "rule levels are not built.")
para("The Atlanta measure itself has two known weak spots. It treats every non-vertical direction as "
     "horizontal, so sloped structures such as staircases, ramps and pitched roofs give wrong pairs, in "
     "real photos as much as in generated ones; this probably explains part of the 28 to 44 per cent "
     "impossible-pair rate in real photos. And for a camera held almost exactly level, the focal length "
     "of a single image is poorly determined, so one image's number should be read with care even "
     "though the group comparison survives the tilt check of Section 5.4.1.")
para("Three claims made during the project were withdrawn after more testing. We record them because "
     "the lesson is part of the contribution. First, we said real photos never contain an impossible "
     "vanishing-point pair. That came from reading a median fraction per image instead of the share of "
     "images; the correct figures form a steady rise, not a split. Second, we said camera coherence gets "
     "worse with model size. That used a focal spread computed over all vanishing-point pairs, "
     "including pairs not at right angles, where the focal formula does not apply; with the Atlanta "
     "measure and four times the data, the difference disappeared. Third, we said the classifier's "
     "most important features showed a focal-length problem; that relied on one of the same invalid "
     "features, and with valid features the classifier points at the principal point instead. The rule "
     "we now follow: build a focal-length statistic only from vanishing-point pairs that are at right "
     "angles by construction.")

doc.add_heading("5.12 Summary of Results", level=2)
table(["Finding", "Evidence"],
      [["The tool recovers real cameras",
        "Focal length within 2 per cent on York Urban; vanishing points within 0.3 deg on synthetic "
        "scenes"],
       ["Real-photo residuals are not zero and must be measured",
        "Concurrency median 1.31 deg; lens distortion and non-box-shaped scenes quantified"],
       ["The choice of real photos can flip the conclusion",
        "Ordinary real photos score worse than generated images on the Manhattan test"],
       ["Generated images fail camera coherence",
        "Log-focal spread 0.355 and 0.465 against 0.142 and 0.152 for real; p about 3 × 10⁻⁵"],
       ["The main result is not an artefact",
        "Unchanged when the vertical vanishing point must be away from the centre, and when only clearly "
        "tilted cameras are kept (p 0.008 or less)"],
       ["Orientation matches, the camera does not",
        "Manhattan residual comparable after the applicability rule; focal coherence 2.5 to 3 times worse"],
       ["A bigger model improves orientation only",
        "SD 1.5 to SDXL: Manhattan p = 0.0002; focal coherence p = 0.55"],
       ["The newest models still fail",
        "Gemini 0.338 and ChatGPT 0.491 against 0.142 and 0.152 for real; p about 0.015; not "
        "significantly different from SD 1.5 or SDXL yet"],
       ["Readable residuals are competitive detectors",
        "AUC 0.88 to 0.93 against the hand-picked set and 0.81 to 0.86 in the hardest cases, against "
        "0.88 to 0.94 reported for learned geometric features"],
       ["The method works as a usable tool",
        "Demonstration app: AUC 0.80, well calibrated, says when it cannot measure an image"]],
      widths=[2.4, 4.1])
caption("Table 5.8: Summary of the main results.")

# ================================================================ 6
doc.add_heading("6. References", level=1)
missing = [k for k in REFS if k not in ORDER]
if missing:
    raise RuntimeError(f"references never cited in the text: {missing}")
for i, k in enumerate(ORDER, 1):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.add_run(f"[{i}] {REFS[k]}").font.size = Pt(10)



# ---------------------------------------------------------------- table captions go above tables
def _captions_above_tables(document):
    body = document.element.body
    kids = list(body)
    for i, el in enumerate(kids):
        if el.tag != qn("w:p"):
            continue
        text = "".join(n.text or "" for n in el.iter(qn("w:t")))
        if not re.match(r"Table \d+\.\d+:", text):
            continue
        j = i - 1
        while j >= 0 and kids[j].tag == qn("w:p") and not "".join(n.text or "" for n in kids[j].iter(qn("w:t"))).strip():
            j -= 1
        if j >= 0 and kids[j].tag == qn("w:tbl"):
            kids[j].addprevious(el)
            pPr = el.get_or_add_pPr()
            pPr.append(OxmlElement("w:keepNext"))
            sp = pPr.find(qn("w:spacing"))
            if sp is None:
                sp = OxmlElement("w:spacing")
                pPr.append(sp)
            sp.set(qn("w:after"), "60")
            sp.set(qn("w:before"), "120")


_captions_above_tables(doc)

# ---------------------------------------------------------------- checks + save
def _all_text(document):
    for p_ in document.paragraphs:
        yield p_.text
    for t_ in document.tables:
        for row in t_.rows:
            for c in row.cells:
                yield c.text


for txt in _all_text(doc):
    for bad in ("—", "–"):
        if bad in txt:
            raise ValueError(f"dash {bad!r} found in: {txt[:120]}")
    if "{c:" in txt:
        raise ValueError(f"unresolved citation in: {txt[:120]}")


def _save(document, target: Path):
    """Word holds an exclusive lock on an open .docx; fall back to a sibling name."""
    try:
        document.save(str(target))
        return target
    except PermissionError:
        alt = target.with_name(target.stem + "_v2" + target.suffix)
        document.save(str(alt))
        return alt


saved = _save(doc, OUT)
words = sum(len(t.split()) for t in _all_text(doc))
print("written:", saved, "| words:", words, "| tables:", len(doc.tables),
      "| figures:", len(doc.inline_shapes), "| references:", len(ORDER))
