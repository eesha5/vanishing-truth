"""Build the CA-3 project report as a .docx.

Content is the project's own results (docs/projective-geometry-consistency-research-plan.md
sections 7.x); figures come from results/.
"""

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
    r = p.add_run(text)
    r.italic, r.bold = italic, bold
    if size:
        r.font.size = Pt(size)
    if align:
        p.alignment = align
    return p


def bullet(text):
    doc.add_paragraph(text, style="List Bullet")


def number(text):
    doc.add_paragraph(text, style="List Number")


def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.italic = True
    r.font.size = Pt(9.5)
    p.paragraph_format.space_after = Pt(12)


def figure(fname, width_in=6.0):
    """Insert a figure from results/, or a visible placeholder if missing."""
    path = RES / fname
    if not path.exists():
        placeholder(f"Missing file: results/{fname}")
        return
    doc.add_picture(str(path), width=Inches(width_in))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


def placeholder(text):
    p = doc.add_paragraph()
    r = p.add_run("[FIGURE TO INSERT] " + text)
    r.italic = True
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x88, 0x44, 0x00)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "F2F2F2")
    pPr.append(shd)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)


def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(9.5)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), "D9E2F3")
        c._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(v))
            run.font.size = Pt(9.5)
    if widths:
        for r in t.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Inches(w)
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
para("Course: Computer Vision   |   Assessment: CA-3 Project Report",
     align=WD_ALIGN_PARAGRAPH.CENTER)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Team members: <Name, PRN>   |   <Name, PRN>   |   <Name, PRN>")
r.font.color.rgb = RGBColor(0xC0, 0, 0)
para("Department of <Department>, <Institute>", align=WD_ALIGN_PARAGRAPH.CENTER)
para("Academic Year 2026-27", align=WD_ALIGN_PARAGRAPH.CENTER)
doc.paragraphs[-1].add_run().add_break(WD_BREAK.PAGE)

# ---------------------------------------------------------------- 1
doc.add_heading("1. Introduction", level=1)

doc.add_heading("1.1 Background and Rationale", level=2)
para("A photograph is the record of a physical process: light from a three-dimensional scene passes "
     "through a single optical centre and is recorded on a planar sensor. That process, the pinhole "
     "camera model, imposes constraints that no real photograph can violate. Lines that are parallel "
     "in three dimensions converge to a single vanishing point in the image; the three mutually "
     "perpendicular directions of a rectilinear building fix the camera's focal length and principal "
     "point; every cast shadow in a sunlit scene points away from one light source. These are not "
     "statistical regularities but consequences of projective geometry, and they hold for every camera "
     "ever built.")
para("Modern text-to-image generators produce images that are photorealistic at the level of texture "
     "and colour, yet they possess no camera. A diffusion model learns the appearance statistics of "
     "photographs from data; nothing in its architecture represents an optical centre, a focal length "
     "or a principal point. Whether the resulting images nevertheless obey projective constraints is "
     "therefore an empirical question with a precise answer, and one that can be measured in "
     "interpretable physical units rather than in the abstract feature space of a learned classifier.")
para("This project builds an instrument for that measurement. Every image is treated as an implicit "
     "claim that a single pinhole camera photographed the scene, and that claim is tested against a "
     "hierarchy of projective constraints. Each test returns a residual in degrees or in dimensionless "
     "ratios, so a failure is not merely detected but localised to a specific geometric rule.")

doc.add_heading("1.2 Motivation", level=2)
para("Three motivations drive the work. First, forensic: as generators improve, pixel-level and "
     "frequency-domain detectors degrade, whereas a geometric violation remains a violation regardless "
     "of how convincing the texture is. Second, scientific: the pattern of which constraints a "
     "generator satisfies and which it breaks is a probe of what the model has internalised about "
     "three-dimensional structure. Third, applied: monocular visual servoing, autonomous navigation "
     "and structure-from-motion all assume projective consistency, so synthetic imagery used to train "
     "or benchmark robot perception must be geometrically sound, and measuring that soundness is a "
     "prerequisite for using such data safely.")

doc.add_heading("1.3 Recent Trends", level=2)
para("Sarkar et al. (CVPR 2024) established that generated images violate projective geometry strongly "
     "enough for classifiers operating on geometric features alone, never on pixels, to distinguish "
     "them from photographs. Subsequent work has moved in two directions. On the generation side, "
     "systems that enforce consistent vanishing points during synthesis confirm that the community "
     "regards perspective inconsistency as a known weakness. On the analysis side, multi-view work "
     "reports that diffusion models violate epipolar constraints across generated viewpoints. In "
     "parallel, probing studies show that generative models encode depth, normals and intrinsic images "
     "locally, which sits in tension with the forensic finding of global geometric failure. Informal "
     "commentary in 2026 has begun to claim that the geometric tell has disappeared in current models; "
     "that claim is untested in the peer-reviewed literature and is precisely the kind of question this "
     "project is built to answer.")

doc.add_heading("1.4 Significance of the Study", level=2)
para("The contribution of this work is not another detector. It is a measurement methodology and a set "
     "of calibrated findings. Three aspects are significant. The residuals are interpretable, so a "
     "result states which constraint failed and by how many degrees. The comparison is calibrated "
     "against real photographs, including both a hand-curated dataset and an uncurated internet "
     "corpus, which turns out to be decisive: several apparently strong results reverse depending on "
     "which real reference is used. And the study defines an applicability criterion that decides, "
     "independently of the measurement itself, whether a given image can support the test at all, "
     "which prevents the systematic error that dominates naive applications of these constraints.")

# ---------------------------------------------------------------- 2
doc.add_heading("2. Review of Relevant Literature", level=1)

doc.add_heading("2.1 Previous Research Work", level=2)
para("Classical single-view geometry. Criminisi, Reid and Zisserman [7] established single-view "
     "metrology, recovering metric scene structure from vanishing points and the image of the absolute "
     "conic. Coughlan and Yuille [8] introduced the Manhattan-world assumption, that urban scenes are "
     "dominated by three mutually orthogonal directions. Hoiem, Efros and Hebert [9] linked horizon "
     "estimation to object scale. Denis, Elder and Estrada [10] published the York Urban Database, 102 "
     "calibrated images with hand-labelled line segments and ground-truth Manhattan vanishing points, "
     "which remains the standard benchmark for vanishing-point estimation. Grompone von Gioi et al. "
     "[11] contributed the Line Segment Detector, a parameterless sub-pixel line detector with false-"
     "detection control, which is the front end used throughout this project.")
para("Image forensics from geometry. Kee, O'Brien and Farid [3] formulated cast-shadow consistency as "
     "a linear programming feasibility problem: each shadow-to-object correspondence, with its "
     "annotation uncertainty, constrains the image of the light source to a wedge, and a physically "
     "consistent scene requires all wedges to intersect. Farid [4, 5] applied vanishing-point, shadow "
     "and reflection analysis to early text-to-image outputs, establishing the approach but on small, "
     "manually analysed samples.")
para("Learned geometric detection. Sarkar et al. [1] curated generated images that defeat pixel-based "
     "detectors, then trained classifiers on three derived geometric representations, namely line "
     "segments, perspective fields and object-shadow relations. Reported AUCs on the hardest subset "
     "were approximately 0.88 to 0.94 for lines, 0.86 to 0.92 for perspective fields and 0.77 to 0.79 "
     "for shadow cues.")
para("Geometric awareness of generative models. Du et al. [12], Chen et al. [13] and El Banani et al. "
     "[14] show that intrinsic images, depth and surface normals can be linearly decoded from "
     "generative and foundation-model activations, indicating that geometry is represented locally. "
     "Jin et al. [15] and Veicht et al. [16] provide learned single-image calibration through "
     "perspective fields and geometric optimisation.")

doc.add_heading("2.2 Key Findings from the Literature", level=2)
bullet("Generated images do violate projective geometry, strongly enough to support classification "
       "from geometric features alone (Sarkar et al., AUC 0.88-0.94 for line-based features).")
bullet("Cast-shadow consistency admits an exact, uncertainty-aware formulation as a linear program, "
       "avoiding arbitrary thresholds (Kee, O'Brien and Farid).")
bullet("Generative models encode local three-dimensional structure such as depth and normals, which "
       "can be recovered by linear probes.")
bullet("Perspective inconsistency is regarded as a known generation-side defect, to the point that "
       "methods now exist to constrain vanishing points during synthesis.")

doc.add_heading("2.3 Research Gaps", level=2)
para("Four gaps are identified; this project addresses the first three.")
number("Learned classifiers on geometric features report that a violation exists, but not which "
       "projective constraint failed, nor by how much. No published benchmark decomposes geometric "
       "failure constraint by constraint with calibrated statistical tests.")
number("Existing studies compare generated images against a single, usually hand-curated, real "
       "dataset. The dependence of the conclusion on the choice of real reference has not been "
       "examined, and this work finds that dependence to be decisive.")
number("The distinction between local and global geometric consistency has been stated informally but "
       "never quantified. In particular, no study separates whether a generator fails at scene "
       "orientation or at camera intrinsics.")
number("The applicability of the three-vanishing-point camera test to uncurated imagery has not been "
       "treated. Scenes that are not Manhattan worlds produce large residuals that carry no "
       "information about the camera.")

# ---------------------------------------------------------------- 3
doc.add_heading("3. Problem Statement and Objectives", level=1)

doc.add_heading("3.1 Research Questions", level=2)
number("Do images produced by current diffusion models satisfy the projective constraints that a "
       "single pinhole camera imposes, when compared against real photographs under matched scene "
       "content and matched camera configuration?")
number("If violations exist, which constraint fails: the orthogonality of the scene's dominant "
       "directions, or the consistency of the implied camera intrinsics across the image?")
number("Does the violation diminish as generator capability increases, as would be expected if scale "
       "alone were sufficient to acquire an implicit camera model?")
number("Are explicit, interpretable geometric residuals competitive with learned classifiers on "
       "geometric features for the detection task?")

doc.add_heading("3.2 Problem Statement", level=2)
para("Given a single image, determine whether its geometric content is consistent with formation by "
     "one pinhole camera; express any inconsistency as an interpretable residual attributable to a "
     "specific projective constraint; calibrate that residual against the distribution obtained from "
     "real photographs under the same measurement pipeline; and use the resulting profile to compare "
     "generative models.")

doc.add_heading("3.3 Objectives", level=2)
number("O1: Implement and validate a measurement pipeline for line-based projective constraints, "
       "specifically vanishing-point concurrency and single-camera coherence, with ground-truth "
       "validation.")
number("O2: Establish real-image null distributions for every residual, using both a curated benchmark "
       "and an uncurated internet corpus with diverse cameras.")
number("O3: Construct content-matched generated image sets from multiple diffusion models with fully "
       "logged generation parameters.")
number("O4: Define an applicability criterion, independent of the residual being measured, that "
       "determines whether an image can support the camera test, and validate it against ground truth.")
number("O5: Compare generators against real references under matched content and camera configuration, "
       "and evaluate standard classification algorithms on the resulting residual vectors.")
number("O6: Implement the shadow-consistency constraint as a linear program and validate it on "
       "synthetic scenes with a known light source.")

doc.add_heading("3.4 Scope and Limitations", level=2)
para("Scope. Single-image analysis only. Two line-based constraint levels are implemented and "
     "validated in full, namely vanishing-point concurrency and camera coherence, together with a "
     "regional camera-consistency analysis and the shadow constraint at the geometry level. Two "
     "locally generated models are evaluated, Stable Diffusion 1.5 and SDXL, against two real "
     "references.")
para("Limitations. Closed frontier models such as Gemini and GPT-image are not yet included, as no API "
     "access was available; the prompt set and analysis are prepared so that such images can be added "
     "without modification. Multi-view constraints such as epipolar consistency do not apply to single "
     "images and are excluded by design. The shadow constraint is validated geometrically but is not "
     "yet deployed at scale, because automatic shadow-to-object association remains unsolved in this "
     "implementation. Constraint levels covering projective invariants, conics, reflections and "
     "cross-modal agreement are specified but not implemented.")

# ---------------------------------------------------------------- 4
doc.add_heading("4. Methodology", level=1)

doc.add_heading("4.1 Overview of Methodology", level=2)
para("The pipeline converts an image into a vector of interpretable geometric residuals in five "
     "stages: line-segment detection; unconstrained vanishing-point estimation; applicability "
     "assessment; residual computation for each constraint level; and statistical comparison against "
     "calibrated real-image null distributions. A deliberate design decision runs through the whole "
     "system: the vanishing-point estimator is never given a Manhattan or orthogonality prior, because "
     "the camera test asks precisely whether the recovered directions are mutually orthogonal, and an "
     "estimator that assumed this would make the test vacuous.")
placeholder("System architecture flowchart. Draw a left-to-right block diagram: Image -> LSD line "
            "detection -> sequential RANSAC vanishing-point estimation (no Manhattan prior) -> "
            "applicability rule (decision diamond, with a rejected branch) -> residual computation "
            "(L2 concurrency, L3 camera coherence, Atlanta focal consistency, regional windows, "
            "L7 shadows) -> comparison against real-image null distributions -> failure profile.")
caption("Figure 4.1: Overall architecture of the geometric-consistency measurement pipeline.")

doc.add_heading("4.2 Objective-wise Methodology", level=2)
table(["Objective", "Method employed", "Validation performed"],
      [["O1 Pipeline implementation",
        "LSD line detection; sequential RANSAC vanishing-point estimation with angular least-squares "
        "refinement on the unit sphere; closed-form and least-squares focal recovery",
        "Synthetic scenes with known cameras; York Urban ground-truth vanishing points"],
       ["O2 Real-image calibration",
        "Full pipeline on York Urban (102 images) and a Wikimedia Commons corpus (358 images, 135 "
        "camera models) with EXIF focal lengths",
        "Fitted focal length compared against EXIF-derived focal length"],
       ["O3 Generated corpora",
        "Local generation with Stable Diffusion 1.5 and SDXL; prompt strata mirroring the real "
        "content; seeds, steps, guidance scales and dates logged per image",
        "Line-density and content matching verified statistically"],
       ["O4 Applicability rule",
        "Support, localisation, separation and spatial-spread criteria computed from evidence only",
        "Agreement with York Urban ground truth; invariance under injected violations"],
       ["O5 Comparison and classification",
        "Matched-content and matched-field-of-view comparisons; six standard classifiers on residual "
        "vectors",
        "Five-fold cross-validation; bootstrap confidence intervals"],
       ["O6 Shadow constraint",
        "Wedge constraints solved as a linear program minimising the largest violation",
        "Synthetic scenes with a known sun direction and injected shadow rotations"]],
      widths=[1.5, 3.0, 2.0])
caption("Table 4.1: Mapping of objectives to methods and the validation performed for each.")

doc.add_heading("4.3 Design: The Constraint Hierarchy", level=2)
para("Each level of the hierarchy is one rule that a pinhole camera cannot break, paired with a "
     "residual in interpretable units. The levels implemented in this work are marked accordingly.")
table(["Level", "Constraint", "Residual", "Status"],
      [["L1", "Straight 3D edges project to straight image lines", "Curvature (px)", "Not implemented"],
       ["L2", "3D-parallel lines meet at a single vanishing point", "Angular deviation (deg)",
        "Implemented, validated"],
       ["L3", "Three orthogonal directions fix one focal length and principal point",
        "Deviation from 90 deg; focal spread", "Implemented, validated"],
       ["L3b", "Every horizontal direction implies the same focal length with the vertical "
        "(Atlanta worlds)", "Spread of log focal length", "Implemented; primary statistic"],
       ["L4-L6", "Horizon consistency; projective invariants; imaged circular points", "Various",
        "Specified, not implemented"],
       ["L7", "All cast shadows are consistent with one light source", "LP violation (px)",
        "Geometry implemented and validated"],
       ["L8-L9", "Reflection geometry; cross-modal normal agreement", "Degrees",
        "Specified, not implemented"]],
      widths=[0.6, 3.0, 1.7, 1.2])
caption("Table 4.2: Constraint hierarchy, residual units and implementation status.")

doc.add_heading("4.4 Materials and Methods", level=2)
doc.add_heading("4.4.1 Hardware and software", level=3)
table(["Component", "Specification"],
      [["Compute", "NVIDIA GeForce RTX 5060 Laptop GPU, 8 GB VRAM; Windows 11"],
       ["Language and runtime", "Python 3.14"],
       ["Vision library", "OpenCV 4.13 (Line Segment Detector, morphology, connected components)"],
       ["Numerical and statistical",
        "NumPy, SciPy (least squares, linear programming, statistical tests), scikit-learn, "
        "statsmodels, pandas"],
       ["Generative models",
        "PyTorch 2.14 with CUDA 13.0; diffusers 0.40; Stable Diffusion 1.5 and SDXL-base-1.0 with "
        "model CPU offload for the 8 GB budget"],
       ["Project code",
        "projgeo package: lines, vp, camera, selection, locality, regional, shadows, distortion, "
        "prompts, datasets"]],
      widths=[1.8, 4.7])
caption("Table 4.3: Hardware and software environment.")

doc.add_heading("4.4.2 Core algorithms", level=3)
para("Line detection. The Line Segment Detector is applied to the greyscale image, followed by a "
     "length filter at two per cent of the image diagonal to suppress texture clutter. Standard "
     "refinement is used rather than advanced refinement, the latter having been measured to take up "
     "to fifty seconds on certain images with no benefit in segment quality.")
para("Vanishing-point estimation. Segments are mapped to normalised coordinates. Vanishing points are "
     "found sequentially: pairs of segments are sampled with probability proportional to length, their "
     "intersection forms a candidate, and support is measured as the total inlier length within an "
     "angular threshold. The best candidate is refined by weighted angular least squares parameterised "
     "on the unit sphere, which handles vanishing points at infinity without special cases. Inliers "
     "are removed and the process repeats.")
para("Camera coherence. With the principal point placed at the image centre, the focal length that "
     "best makes the back-projected vanishing-point rays mutually orthogonal is found by bounded "
     "one-dimensional optimisation, and the residual is the largest pairwise deviation from ninety "
     "degrees. For three finite vanishing points the principal point of a consistent camera must lie "
     "at the orthocentre of the vanishing-point triangle, and each pair yields a closed-form focal "
     "estimate; a negative value indicates a configuration no camera can produce.")
para("Atlanta focal consistency. The vertical vanishing point is identified by its direction from the "
     "image centre alone, never by orthogonality. Each horizontal vanishing point must then imply the "
     "same focal length with it. This holds in Manhattan worlds and in Atlanta worlds, which contain "
     "several horizontal frames, and is therefore valid on uncurated photographs where the three-"
     "vanishing-point orthogonality test is not.")
para("Uncertainty quantification. Each vanishing point's inlier set is resampled with replacement and "
     "re-refined, giving a bootstrap angular standard deviation in ray space. This distinguishes "
     "vanishing points that are genuinely well determined from those that slide along a family of "
     "nearly parallel lines.")

doc.add_heading("4.4.3 The applicability rule", level=3)
para("The three-vanishing-point camera test is defined only for scenes that actually exhibit three "
     "visible, well-separated, well-supported directions. An image is admitted if three vanishing-"
     "point families each carry at least eight per cent of the total detected line length, each is "
     "localised to better than one degree by the bootstrap, each pair is separated by at least ten "
     "degrees and by at least five times its own uncertainty, and each family's inliers span at least "
     "twelve per cent of the image diagonal. Real photographs additionally require a standard sensor "
     "aspect ratio, since cropping displaces the principal point. Orthogonality, focal length, the "
     "orthocentre and the shape of the vanishing-point triangle are deliberately excluded from the "
     "rule, because those quantities constitute the measurement.")
para("Two validations confirm that the rule is sound. Against York Urban ground truth, admitted images "
     "have ninety per cent of their vanishing points within five degrees of the hand-labelled values, "
     "compared with fifty-seven per cent for rejected images. A unit test injects a controlled camera "
     "violation that leaves the line layout unchanged and asserts that the admission decision does not "
     "change, which establishes that the rule cannot be selecting real images for being consistent.")

doc.add_heading("4.5 Data Acquisition", level=2)
table(["Dataset", "Size", "Role", "Provenance and parameters"],
      [["York Urban", "102 images, 640x480",
        "Curated real reference; ground-truth vanishing points and calibration",
        "Elder Laboratory, York University; single camera, focal length 675 px"],
       ["Wikimedia Commons", "358 images, 135 camera models",
        "Uncurated real reference with diverse cameras",
        "Commons API; filtered for EXIF camera model and focal length, landscape aspect, width at "
        "least 1024; CC licences with attribution recorded"],
       ["SD 1.5 sets", "200 + 250 images, 640x480", "Older UNet diffusion baseline",
        "30 steps, guidance 6.0, seeds and prompts logged per image"],
       ["SDXL sets", "200 + 250 + 120 + 80 images", "Current-generation baseline",
        "30 steps, guidance 6.0, model CPU offload; 1024x768 plus 1:1 and 16:9 aspect variants"],
       ["Synthetic scenes", "Generated on demand", "Ground-truth validation and violation injection",
        "Known intrinsics and rotation; controlled violations of each constraint"]],
      widths=[1.2, 1.2, 1.7, 2.4])
caption("Table 4.4: Datasets, their role in the study and acquisition parameters.")
para("Prompt design. Generated content mirrors the real corpora. A first stratum covers building "
     "facades, streets, corridors, lecture halls and offices. A second stratum was introduced to "
     "guarantee three visible orthogonal directions by describing corners where two surfaces meet, and "
     "a third, refined stratum additionally requires repeating line-rich features such as tiled "
     "floors, shelving, window grids and brick courses, because the first attempt produced scenes that "
     "were structurally correct but too sparse in lines to be measurable. All generated images carry a "
     "metadata record with model identifier, prompt, negative prompt, seed, sampler, step count, "
     "guidance scale, resolution and generation date.")

doc.add_heading("4.6 Implementation", level=2)
para("The system is implemented as a Python package with a test suite of eighteen tests. Validation is "
     "layered. Synthetic scenes with known cameras verify that the estimators recover the truth, and "
     "controlled violation injectors verify that each residual responds to its own constraint and not "
     "to others: one injector perturbs line directions to break concurrency alone, one displaces a "
     "vanishing point so that concurrency is preserved but camera coherence is broken, one makes a "
     "vanishing point drift with image position, and one splits the image between two different "
     "cameras. Residuals are required to increase monotonically with the injected violation magnitude.")
para("One implementation detail proved to matter for correctness. The inlier root-mean-square residual "
     "saturates once violations exceed the inlier threshold, because badly violating segments are "
     "simply excluded from the inlier set. A length-weighted capped mean over all segments, together "
     "with the fraction of line length that no vanishing point explains, was therefore introduced and "
     "verified to be monotone across the full range of injected violations.")
placeholder("Screenshot of the per-image analysis output. Run: python scripts/analyze_image.py "
            "<image> --out outputs/ and insert the generated overlay PNG, which shows detected "
            "segments coloured by vanishing-point cluster, the vanishing points, and the orthocentre "
            "marked against the image centre.")
caption("Figure 4.2: Per-image analysis output showing line segments grouped by vanishing point.")

# ---------------------------------------------------------------- 5
doc.add_heading("5. Results and Discussion", level=1)

doc.add_heading("5.1 Validation of the Instrument", level=2)
para("Before any comparison between real and generated imagery, the measurement pipeline was validated "
     "against known ground truth. On synthetic scenes with known intrinsics, vanishing points are "
     "recovered to within 0.3 degrees and focal length to within one per cent. On the York Urban "
     "database the unconstrained estimator recovers 81 per cent of ground-truth vanishing points "
     "within two degrees and 94 per cent within five degrees, and the median ratio of fitted to true "
     "focal length is 1.02 with an interquartile range of 0.99 to 1.05. The camera-coherence machinery "
     "therefore recovers the real camera of real photographs, which is the necessary precondition for "
     "interpreting any residual measured on generated images.")
table(["Validation", "Quantity", "Result"],
      [["Synthetic scenes", "Vanishing-point direction error", "Below 0.3 deg"],
       ["Synthetic scenes", "Focal length error", "Below 1 per cent"],
       ["York Urban", "Ground-truth VPs recovered within 2 deg / 5 deg", "81 per cent / 94 per cent"],
       ["York Urban", "Fitted focal / true focal, median [IQR]", "1.02 [0.99, 1.05]"],
       ["Commons (EXIF)", "Fitted focal vs EXIF focal, well-conditioned images",
        "Median ratio +6 per cent; 58 per cent within 20 per cent"],
       ["Violation injection", "Monotonicity of each residual in its own violation",
        "Confirmed for all four injectors"]],
      widths=[1.5, 2.9, 2.1])
caption("Table 5.1: Validation of the measurement pipeline against ground truth.")
figure("commons_focal_validation.png", 3.3)
caption("Figure 5.1: Fitted focal length against EXIF-derived focal length for real photographs from "
        "135 different camera models. Dashed lines indicate a twenty per cent band.")

doc.add_heading("5.2 Real-Image Null Distributions", level=2)
para("Residual distributions were established on both real references. On York Urban the concurrency "
     "residual has a median of 1.31 degrees and a ninety-fifth percentile of 2.46 degrees; the camera-"
     "coherence residual has a median of 0.69 degrees. These values are not zero, and treating them as "
     "zero would be the single most common error in applying such tests. Two sources were identified "
     "and quantified: radial lens distortion, for which a per-image single-coefficient fit recovers a "
     "median value consistent with a dataset-wide fit, and the fact that real scenes are only "
     "approximately Manhattan.")
figure("yorkurban_ecdf.png", 6.0)
caption("Figure 5.2: Empirical cumulative distributions of each residual on the curated real "
        "reference, with the estimator-only floor shown for comparison.")

doc.add_heading("5.3 The Decisive Role of the Real Reference", level=2)
para("The second real corpus, drawn from Wikimedia Commons with diverse cameras, produced the most "
     "consequential methodological finding of the study. Measured without an applicability criterion, "
     "uncurated real photographs score a median camera-coherence residual of 12.2 degrees, which is "
     "worse than Stable Diffusion 1.5 and far worse than SDXL. Taken at face value this would imply "
     "that generated images are more camera-consistent than photographs, which is not credible.")
para("Inspection of the failing photographs explains the result. They are curved streets, adjacent "
     "building facades at oblique angles and near-frontal views: scenes that contain three well-"
     "supported, well-localised, clearly distinct vanishing-point families that are simply not "
     "mutually orthogonal. These are Atlanta worlds rather than Manhattan worlds, and the three-"
     "vanishing-point orthogonality test is not defined for them. The failure is one of applicability, "
     "not of photographic geometry, and no evidence-based filtering removes it: raising the support "
     "threshold makes the residual worse, and ninety-eight per cent of the affected images already "
     "have standard aspect ratios, which excludes cropping as the mechanism.")
placeholder("Montage of selected uncurated real photographs spanning the residual range, available at "
            "results/commons_selected_montage.png. It shows that low and mid-range images are genuine "
            "three-direction scenes while the extreme tail consists of angled streets and near-frontal "
            "facades. Note: these are CC-licensed photographs; reproduce the author and licence from "
            "data/real/commons/metadata.jsonl if the montage is included.")
caption("Figure 5.3: Real photographs spanning the residual range, illustrating that the high-residual "
        "tail consists of non-Manhattan scenes.")
para("Two corrections follow, and both are adopted in the results below. First, images are admitted "
     "only through the applicability rule of Section 4.4.3. Applying it reduces the uncurated real "
     "median from 12.2 degrees to 2.19 degrees. Second, the primary statistic is changed from three-"
     "vanishing-point orthogonality to Atlanta focal consistency, which is valid in both Manhattan and "
     "Atlanta worlds.")

doc.add_heading("5.4 Primary Result: Camera Coherence", level=2)
para("The primary comparison uses the Atlanta focal-consistency residual on images admitted by the "
     "applicability rule. The statistic is the spread of the logarithm of the focal length implied by "
     "each horizontal direction together with the vertical direction. A value of zero means every part "
     "of the scene agrees on how zoomed-in the camera is.")
table(["Quantity", "York Urban (curated real)", "Commons (uncurated real)", "SD 1.5 (line-rich)",
       "SDXL (line-rich)"],
      [["Images admitted by the rule", "72", "121", "92", "112"],
       ["With at least two horizontal families", "72", "120", "87", "109"],
       ["Log-focal spread, median [95% CI]", "0.142 [0.106, 0.221]", "0.152 [0.093, 0.220]",
        "0.465 [0.324, 0.709]", "0.355 [0.272, 0.529]"],
       ["Images with an impossible pair", "28% [19, 39]", "44% [36, 53]", "68% [57, 77]",
        "58% [48, 66]"],
       ["Manhattan orthogonality (secondary)", "0.65 deg", "2.82 deg", "2.93 deg", "1.94 deg"]],
      widths=[1.8, 1.3, 1.3, 1.1, 1.0])
caption("Table 5.2: Atlanta focal consistency on admitted images. Intervals are bootstrap intervals "
        "for medians and Wilson intervals for proportions.")
figure("atlanta_scaling.png", 6.0)
caption("Figure 5.4: Distribution of the log-focal spread (left) and the share of images containing a "
        "vanishing-point pair for which no camera exists (right).")
para("The two real references agree with one another to within their confidence intervals, at 0.142 "
     "and 0.152, while both generated sets lie clearly above them with non-overlapping intervals, at "
     "0.355 and 0.465. Mann-Whitney tests give p of approximately three by ten to the minus five "
     "against either real reference. Expressed plainly: in a real photograph the horizontal directions "
     "agree on a single focal length to within about fifteen per cent, whereas in generated images "
     "they disagree by thirty-five to sixty per cent. The result holds against a hand-curated "
     "benchmark and against uncurated internet photographs alike, which is what makes it defensible.")

doc.add_heading("5.5 Comparative Analysis Across Generators", level=2)
para("Stable Diffusion 1.5 and SDXL were compared on identical prompts with matched field-of-view "
     "distributions and matched line density, using 250 generated images per model. The comparison "
     "separates two capabilities that are often conflated.")
table(["Measure", "SD 1.5", "SDXL", "p", "Interpretation"],
      [["Manhattan orthogonality", "2.93 deg", "1.94 deg", "0.0002",
        "Improves with model capability"],
       ["Atlanta log-focal spread", "0.465", "0.355", "0.55 (n.s.)", "Unchanged"],
       ["Images with an impossible pair", "68%", "58%", "0.18 (n.s.)", "Unchanged"]],
      widths=[1.8, 1.0, 1.0, 1.0, 1.7])
caption("Table 5.3: Scaling comparison on identical prompts, 87 and 109 usable images respectively.")
para("Scaling from Stable Diffusion 1.5 to SDXL improves the consistency of scene orientation "
     "significantly, while camera coherence is statistically unchanged and remains roughly two and a "
     "half to three times worse than either real reference. The honest reading is that orientation "
     "improves with model capability whereas camera coherence does not, which implies that scale alone "
     "is not on course to remove the deficit.")

doc.add_heading("5.6 Where the Inconsistency Lives", level=2)
para("Two further analyses locate the failure spatially. A regional analysis fits an independent "
     "camera inside each cell of an overlapping three-by-three grid and measures how much the cells "
     "disagree, reporting a consistency radius defined as the smallest deviation such that one global "
     "camera lies within that distance of every local camera. Generated images show substantially "
     "larger disagreement in implied focal length between regions than real photographs, and the gap "
     "widens as the analysis window grows, whereas real photographs converge towards a single camera "
     "at large windows.")
para("A complementary analysis tests whether the inconsistency takes the form of a smooth spatial "
     "drift within a single family of parallel lines, using the spatial correlation of signed angular "
     "residuals. This statistic is indistinguishable between real and generated images for every set "
     "tested. The inconsistency is therefore not a gradual warping of the image; it is disagreement "
     "between distinct structures and regions.")
figure("scale_curve_sdxl_vs_real.png", 6.0)
caption("Figure 5.5: Disagreement in implied focal length between image regions as a function of "
        "window size, for real and generated images.")

doc.add_heading("5.7 Classification from Geometric Residuals", level=2)
para("To place the work beside the learned-classifier literature, six standard classification "
     "algorithms were trained on the per-image residual vector alone, never on pixels, and evaluated "
     "by five-fold stratified cross-validation. Feature groups were ablated so that camera-"
     "configuration and content descriptors could be excluded from the geometry-only condition.")
table(["Task", "Best AUC, geometry only", "Classifier"],
      [["Curated real versus SDXL", "0.916", "Support vector machine"],
       ["Curated real versus SD 1.5", "0.916", "Support vector machine"],
       ["Uncurated real versus SDXL", "0.824", "Random forest"],
       ["All real versus all generated", "0.835", "Random forest"],
       ["Field-of-view matched", "0.810", "Random forest"]],
      widths=[2.4, 2.1, 2.0])
caption("Table 5.4: Detection performance from interpretable geometric residuals, five-fold "
        "cross-validated.")
figure("classifier_roc.png", 5.6)
caption("Figure 5.6: Receiver operating characteristic curves for detection from geometric residuals "
        "alone.")
para("For reference, Sarkar et al. report approximately 0.88 to 0.94 AUC for a learned line-based "
     "classifier on their hardest subset. Explicit, unit-bearing residuals therefore reach a "
     "comparable band against a curated reference and retain 0.81 to 0.82 in the two most demanding "
     "conditions, namely uncurated real photographs and matched field of view. The purpose of this "
     "comparison is not to win on AUC but to show that interpretability is obtained at little cost in "
     "discriminative power.")

doc.add_heading("5.8 Shadow Consistency", level=2)
para("The shadow constraint was implemented following the wedge formulation. A shadow point together "
     "with the object region that may have cast it defines a wedge of admissible light positions, "
     "expressed as two half-planes, and a physically consistent scene requires all wedges to "
     "intersect. The problem is solved as a linear program that minimises the largest half-plane "
     "violation, so the output is a violation in pixels rather than a binary verdict. On synthetic "
     "scenes with a known sun the image of the light source is recovered exactly, the violation grows "
     "monotonically with injected shadow rotation, and wider annotation uncertainty is strictly more "
     "permissive, which is the property that makes the test safe to apply to hand-annotated data.")
para("Shadow detection itself is implemented with the classical sequence of a grey-value "
     "transformation that exploits the fact that shadows are both darker and bluer, Otsu thresholding, "
     "morphological closing and opening with structuring elements scaled to the image diagonal, and "
     "connected-component analysis with an area filter.")
placeholder("Shadow detection example, available at results/example_shadow_mask_works.png. Show the "
            "original sunlit image beside the detected shadow mask overlaid in colour.")
caption("Figure 5.7: Shadow detection by grey-value transformation, thresholding and morphology on a "
        "sunlit scene.")
para("An attempt to avoid manual annotation, by testing whether the major axes of shadow regions "
     "converge at the sun's azimuth vanishing point, was evaluated and rejected. The real-photograph "
     "null for this statistic is fourteen degrees, and Stable Diffusion 1.5 scores better than real "
     "photographs, which shows that the statistic measures the detector rather than the light. "
     "Inspection confirms that the mask responds to dark glass, signage and shaded interiors as "
     "readily as to cast shadows. The shadow constraint therefore requires genuine shadow-to-object "
     "association, by instance shadow detection or manual annotation, before it can contribute to the "
     "comparison.")

doc.add_heading("5.9 Interpretation of Results", level=2)
para("Four independent lines of evidence converge on the same conclusion. The Atlanta focal-"
     "consistency comparison, the regional camera analysis, the classifier feature importances and the "
     "behaviour of the residuals under changes of scene structure all indicate that the deficit of "
     "current generators is specifically a failure to commit to one focal length and one principal "
     "point across an image, rather than a failure to represent the orientation structure of the "
     "scene.")
para("This is a narrower and more precise claim than a naive comparison would support, and it is the "
     "claim that survives control of scene content, camera configuration and choice of real reference. "
     "It is also mechanistically plausible: the orientation of a dominant direction can be inferred "
     "from local evidence anywhere in the image, whereas the focal length depends on the separation "
     "between vanishing points and therefore requires the whole image to be integrated into one "
     "representation.")

doc.add_heading("5.10 Significance of Findings", level=2)
bullet("A measurement methodology that reports which projective constraint failed and by how much, "
       "rather than a single opaque score.")
bullet("Evidence that the choice of real reference can reverse the direction of a published-style "
       "comparison, which is a methodological warning for the field.")
bullet("An applicability criterion with an explicit non-circularity guarantee, validated against "
       "ground truth, that makes the camera test usable on uncurated imagery.")
bullet("A powered, replicated result that generated images fail camera coherence by a factor of two "
       "and a half to three relative to real photographs, while matching them on scene orientation.")
bullet("Evidence that increasing model capability improves orientation but not camera coherence, "
       "indicating that scale alone will not close the gap.")

doc.add_heading("5.11 Limitations", level=2)
para("Frontier closed models are not yet evaluated, so the conclusions apply to locally reproducible "
     "open models. The shadow constraint is not deployed at scale. Generated images are analysed after "
     "downsampling to the resolution of the curated real reference, and the effect of resampling on "
     "line detection has not been isolated, although the comparison against the uncurated corpus is "
     "resampling-matched and gives the same conclusion. Several constraint levels remain unimplemented.")
para("Two claims made during the study were withdrawn after further testing, and are recorded here "
     "because the methodological lesson is part of the contribution. A statement that real photographs "
     "never contain an impossible vanishing-point pair was based on reading a median fraction rather "
     "than a proportion of images; the correct figures form a gradient rather than a categorical "
     "difference. A statement that camera coherence degrades with model scale was based on a focal-"
     "spread statistic computed over all vanishing-point pairs, including pairs that are not "
     "orthogonal, for which the focal formula is undefined; with a statistic restricted to pairs that "
     "are orthogonal by construction, and with four times the sample size, the difference disappears. "
     "The general rule adopted is that any focal-length statistic must be built only from vanishing-"
     "point pairs whose orthogonality is guaranteed by construction.")

doc.add_heading("5.12 Summary of Results", level=2)
table(["Finding", "Evidence"],
      [["The instrument recovers real cameras",
        "Focal length within 2 per cent on York Urban; vanishing points within 0.3 deg on synthetic "
        "scenes"],
       ["Real-image residuals are not zero and must be calibrated",
        "Concurrency median 1.31 deg; lens distortion and non-Manhattan structure quantified"],
       ["The choice of real reference can reverse conclusions",
        "Uncurated real photographs score worse than generated images on the orthogonality residual"],
       ["Generated images fail camera coherence",
        "Log-focal spread 0.355 and 0.465 versus 0.142 and 0.152 for real; p approximately 3e-5"],
       ["Orientation is matched, intrinsics are not",
        "Orthogonality comparable after control; focal coherence two and a half to three times worse"],
       ["Scale improves orientation only",
        "SD 1.5 to SDXL: orthogonality p = 0.0002; focal coherence p = 0.55"],
       ["Interpretable residuals are competitive detectors",
        "AUC 0.92 curated, 0.82 uncurated, versus 0.88 to 0.94 reported for learned geometric "
        "features"]],
      widths=[2.4, 4.1])
caption("Table 5.5: Summary of principal results.")

# ---------------------------------------------------------------- 6
doc.add_heading("6. References", level=1)
REFS = [
    "[1] A. Sarkar, H. Mai, A. Mahapatra, S. Lazebnik, D. A. Forsyth and A. Bhattad, “Shadows Don’t Lie and Lines Can’t Bend! Generative Models don’t know Projective Geometry…for now,” in Proc. IEEE/CVF Conf. Computer Vision and Pattern Recognition (CVPR), 2024.",
    "[2] R. Hartley and A. Zisserman, Multiple View Geometry in Computer Vision, 2nd ed. Cambridge, U.K.: Cambridge Univ. Press, 2004.",
    "[3] E. Kee, J. F. O’Brien and H. Farid, “Exposing photo manipulation with inconsistent shadows,” ACM Transactions on Graphics, vol. 32, no. 3, 2013.",
    "[4] H. Farid, “Perspective (in)consistency of paint by text,” arXiv preprint, 2022.",
    "[5] H. Farid, “Lighting (in)consistency of paint by text,” arXiv preprint, 2022.",
    "[6] A. Desolneux, L. Moisan and J.-M. Morel, From Gestalt Theory to Image Analysis: A Probabilistic Approach. New York, NY, USA: Springer, 2008.",
    "[7] A. Criminisi, I. Reid and A. Zisserman, “Single view metrology,” International Journal of Computer Vision, vol. 40, no. 2, pp. 123–148, 2000.",
    "[8] J. M. Coughlan and A. L. Yuille, “Manhattan world: Compass direction from a single image by Bayesian inference,” in Proc. IEEE Int. Conf. Computer Vision (ICCV), 1999.",
    "[9] D. Hoiem, A. A. Efros and M. Hebert, “Putting objects in perspective,” International Journal of Computer Vision, vol. 80, no. 1, pp. 3–15, 2008.",
    "[10] P. Denis, J. H. Elder and F. J. Estrada, “Efficient edge-based methods for estimating Manhattan frames in urban imagery,” in Proc. European Conf. Computer Vision (ECCV), 2008.",
    "[11] R. Grompone von Gioi, J. Jakubowicz, J.-M. Morel and G. Randall, “LSD: A fast line segment detector with a false detection control,” IEEE Trans. Pattern Analysis and Machine Intelligence, vol. 32, no. 4, pp. 722–732, 2010.",
    "[12] X. Du et al., “Generative models: What do they know? Do they know things? Let’s find out!” in Advances in Neural Information Processing Systems (NeurIPS), 2023.",
    "[13] Y. Chen, F. Viégas and M. Wattenberg, “Beyond surface statistics: Scene representations in a latent diffusion model,” arXiv preprint, 2023.",
    "[14] M. El Banani et al., “Probing the 3D awareness of visual foundation models,” in Proc. CVPR, 2024.",
    "[15] L. Jin et al., “Perspective fields for single image camera calibration,” in Proc. CVPR, 2023.",
    "[16] A. Veicht et al., “GeoCalib: Learning single-image calibration with geometric optimization,” in Proc. ECCV, 2024.",
    "[17] J. Lezama, R. Grompone von Gioi, G. Randall and J.-M. Morel, “Finding vanishing points via point alignments in image primal and dual domains,” in Proc. CVPR, 2014.",
    "[18] M. Robinson, “Sheaves are the canonical data structure for sensor integration,” Information Fusion, vol. 36, pp. 208–224, 2017.",
    "[19] D. Podell et al., “SDXL: Improving latent diffusion models for high-resolution image synthesis,” in Proc. Int. Conf. Learning Representations (ICLR), 2024.",
    "[20] R. Rombach, A. Blattmann, D. Lorenz, P. Esser and B. Ommer, “High-resolution image synthesis with latent diffusion models,” in Proc. CVPR, 2022.",
]
for ref in REFS:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.add_run(ref).font.size = Pt(10)
p = doc.add_paragraph()
r = p.add_run("Note on sources: verify reference details against the publishers' records before final "
              "submission. Image credits for the Wikimedia Commons corpus, including author and "
              "licence for each photograph used in figures, are recorded in the project metadata file "
              "and must be reproduced if those images appear in the submitted report.")
r.italic = True
r.font.size = Pt(9.5)

doc.save(str(OUT))
print("written:", OUT)
