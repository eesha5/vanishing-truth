# Projective Geometry Consistency in AI-Generated Images
### Evaluating Geometric Artifacts in Modern Generative Models — Research Plan

---

## Table of Contents

1. [Motivation](#1-motivation)
2. [Related Work: What Already Exists](#2-related-work-what-already-exists)
3. [Proposed Approach](#3-proposed-approach)
4. [Untried Theoretical Models](#4-untried-theoretical-models)
5. [Minimum Viable Version](#5-minimum-viable-version)
6. [References](#6-references)
7. [Execution Plan & Decisions (living section)](#7-execution-plan--decisions-living-section)
8. [Plain-Language Glossary of the Constraint Levels](#8-plain-language-glossary-of-the-constraint-levels)

---

## 1. Motivation

Modern text-to-image generators produce images that are photorealistic at the pixel level, yet they often violate the rules of projective geometry: parallel lines that fail to meet at a single vanishing point, shadows that imply multiple suns, reflections that don't line up with their objects. Prior work shows these errors exist and can be used to detect generated images, but it doesn't measure *which* projective constraint is violated, *by how much*, or *why*.

This project proposes a constraint-by-constraint, statistically calibrated evaluation of geometric consistency across current generators, plus new theoretical tools for quantifying global geometric coherence.

**Central hypothesis:** generative models are *locally* geometrically consistent but lack a *global* camera model. Errors should therefore grow with spatial separation in the image.

---

## 2. Related Work: What Already Exists

### 2.1 Anchor paper

**Sarkar, Mai, Mahapatra, Lazebnik, Forsyth & Bhattad — *Shadows Don't Lie and Lines Can't Bend! Generative Models don't know Projective Geometry…for now* (CVPR 2024).**

- Curated generated images that fool pixel/signal-based detectors ("prequalification").
- Trained three classifiers that see only derived geometric features, never pixels: perspective fields, detected line segments, and object–shadow relations.
- On the hardest test set (where the pixel-based prequalifier failed completely), geometric classifiers still achieved high AUCs: roughly 0.88–0.94 for lines, 0.86–0.92 for perspective fields, 0.77–0.79 for object–shadow cues.

**Gap:** these are *learned* classifiers on geometric features. They show errors exist but do not identify which projective constraint fails or quantify violation magnitude.

### 2.2 Forensic geometry (explicit tests)

- **Kee, O'Brien & Farid (ACM TOG 2013)** — inconsistent shadows detected via wedge constraints solved as a linear program.
- **Farid (2022)** — *Perspective (In)consistency of Paint by Text* and *Lighting (In)consistency of Paint by Text*, applying vanishing point, shadow, and reflection analysis to DALL·E 2.

**Gap:** rigorous but manual, small samples, older generators.

### 2.3 Geometry in AI-generated video

- **Grab-3D (arXiv 2512.13665, Dec 2025)** — uses vanishing-point-based representations as explicit 3D descriptors and checks their temporal consistency to detect generated video.

### 2.3b Generation-side and multi-view work (to verify before citing)

- **ControlVP (WACV 2026)** — reported to enforce consistent vanishing points *during* generation because generated buildings often contain incompatible VPs. Generation-side; we are evaluation-side, so complementary, and it confirms the community treats VP consistency as a known weakness.
- **Epipolar-consistency work in novel-view synthesis** — diffusion models violate epipolar constraints / camera-pose consistency across views; epipolar losses are used to fix this. Requires two or more views, so it does not apply to single-image evaluation; cite as adjacent only.

### 2.4 "Do generative models understand 3D?"

- **Bhattad et al.** — StyleGAN encodes normals, depth, albedo.
- **Du et al. (NeurIPS 2023)** — *Generative Models: What do they know?* Intrinsic images recoverable from generators.
- **Chen et al. (2023)** — *Beyond Surface Statistics*: linear depth probes in latent diffusion.
- **El Banani et al. (CVPR 2024)** — *Probing the 3D Awareness of Visual Foundation Models*.

These show models encode geometry **locally**. The tension with forensic findings (global violations) motivates the locality hypothesis.

### 2.5 Adjacent benchmarks

- **T2I-CompBench++, SmartSpatial** — spatial relations, not projective correctness.
- **PhyGenBench, VideoPhy, Physics-IQ** — physical plausibility in video.

### 2.6 Instruments (tools to use, not competitors)

| Task | Tools |
|---|---|
| Line detection | DeepLSD, SOLD2 |
| Vanishing points | NeurVPS, J-linkage, RANSAC-based estimators |
| Camera calibration | Perspective Fields (Jin et al., CVPR 2023), GeoCalib (2024) |
| Depth | Depth Anything V2, MoGe, Metric3D |
| Normals | DSINE, StableNormal |
| Segmentation / shadows | SAM 2, instance shadow detection (SSIS) |

> **Novelty note:** to our knowledge, no benchmark decomposes geometric failure into specific projective constraints with calibrated statistical tests across current generators. Verify with an up-to-date literature search before submission.

---

## 3. Proposed Approach

### 3.1 Core idea

Treat every image as an implicit claim: *a single pinhole camera photographed this scene.* Test that claim against a hierarchy of projective constraints. Each test outputs an interpretable residual (pixels, degrees, ratio error), giving each generator a **failure profile** rather than a single score.

### 3.2 Constraint hierarchy

| Level | Constraint | Test | Residual |
|---|---|---|---|
| **L1** | Straightness | 3D straight edges project to straight lines (after undistortion) | Curvature of long edges |
| **L2** | VP concurrency | Images of 3D-parallel lines meet at one point | Angular deviation from best-fit VP |
| **L3** | Camera coherence | Three orthogonal VPs → principal point at orthocenter of VP triangle; each pair gives `f² = −(v₁ − p)·(v₂ − p)` | Spread of the three focal estimates; orthocenter offset; negative `f²` = impossible configuration |
| **L4** | Horizon consistency | Horizontal VPs lie on one horizon; agrees with perspective-field latitude and object heights (Hoiem-style) | Horizon disagreement across estimators |
| **L5** | Projective invariants | Cross-ratio preserved for equally spaced collinear features; coplanar repeated texture related by a homography | Cross-ratio error; homography residual |
| **L6** | Conics | Coplanar circles project to ellipses sharing the imaged circular points on the plane's vanishing line | Algebraic distance to shared circular points |
| **L7** | Shadows | Shadow→object lines converge at the light's image (sun → VP) | Feasibility of wedge constraints (linear program) |
| **L8** | Reflections | Lines joining points to planar-mirror reflections are 3D-parallel → converge to one VP | VP concurrency residual |
| **L9** | Cross-modal | VP-derived plane normals agree with monocular normal/depth estimates | Angular disagreement |

### 3.3 Separating generator error from estimator error

This is the most important methodological component. Detectors and estimators are imperfect even on real photographs.

1. **Real-image null distributions.** Run the full pipeline on real photos, including datasets with ground-truth VPs/calibration (YorkUrban, HoliCity, ScanNet, SUN RGB-D).
2. **Content matching.** Caption real images and generate from those captions, matching scene type, clutter, and line density. Combine with Sarkar et al.–style prequalification to remove low-level signal cues.
3. **Calibrated effect sizes.** Report residuals as percentiles relative to the real-image null, with confidence intervals. (Formalized via the a contrario framework, §4.1.)
4. **Synthetic validation.** Render Blender scenes with known geometry, inject controlled violations (perturb one VP, rotate one shadow), and measure detection rate vs. violation magnitude for every level.

### 3.4 Dataset design

**Generators (span architectures):**
- UNet diffusion: SD 1.5, SDXL
- DiT / flow matching: SD 3.5, FLUX
- Autoregressive and unified multimodal generators
- Closed APIs: Midjourney, Imagen, GPT-image family, and other current models

**Prompt strata (each exercises specific levels):**

| Stratum | Examples | Levels |
|---|---|---|
| Manhattan scenes | Interiors, corridors, offices | L2–L4 |
| Repetitive facades | Streets, tiled floors, fences | L5 |
| Circular objects on planes | Plates on tables, vehicles | L6 |
| Sunlit outdoor scenes | People, poles, benches | L7 |
| Reflective scenes | Mirrors, still water, storefront glass | L8 |
| Control | Non-Manhattan natural scenes | Baseline |

**Sampling variables:** resolution, aspect ratio, CFG scale, number of sampling steps, sampler.

### 3.5 Analyses

**A. Locality hypothesis.** Plot VP concurrency residual as a function of image distance between line segments. If models are locally consistent but globally inconsistent, residuals grow with separation. Check whether the transition length scale relates to patch size, attention span, or VAE downsampling factor.

**B. Denoising-time formation.** Decode the predicted clean image `x̂₀` at each timestep and run the constraint suite. Determine whether camera geometry is established early and later corrupted, or never globally established.

**C. Scaling and architecture.** Constraint profiles vs. parameter count and model family. Which levels improve with scale, and which plateau?

**D. Perceptibility.** Psychophysics study: at what residual magnitude do humans notice errors? Separates forensically detectable from visually salient violations.

**E. Mitigation (optional).** Use differentiable L2–L3 residuals as rewards for preference optimization (DPO / GRPO-style). Test whether geometry improves without degrading aesthetics, and whether fixing one level transfers to others.

### 3.6 Pitfalls

- **Cropping** moves the principal point off-center in real photos.
- **Lens distortion** violates L1 unless images are undistorted first.
- **Stylized prompts** ("cinematic", illustration) may deliberately violate perspective → keep a photorealistic-only primary set.
- **Non-pinhole outputs** (tilt-shift, panoramas, fisheye) must be excluded or modeled separately.
- **API drift:** closed models change silently → log dates and versions for every generation.

---

## 4. Untried Theoretical Models

Ordered from most immediately usable to most speculative. To our knowledge, none has been applied to evaluating geometric consistency of AI-generated images.

### 4.1 A contrario detection (Helmholtz principle)
*Desolneux, Moisan & Morel*

Score a structure by its **Number of False Alarms (NFA)**: the expected count of equally (in)consistent configurations under a background noise model. Used for VP detection (Lezama et al., 2014), but not for certifying *inconsistency* in generated imagery. Provides principled thresholds (e.g., NFA < 1) instead of ad hoc cutoffs, directly addressing estimator noise.

### 4.2 Image of the Absolute Conic as a unified consistency object

Orthogonal VP pairs, imaged circular points (from L6 ellipses), and square-pixel assumptions each give **linear constraints on ω** (the image of the absolute conic). A real pinhole camera implies one ω satisfying all of them. Stack every available constraint into an overdetermined system; the least-squares residual or smallest singular value is a **single camera-coherence score** that fuses L3, L4, and L6. Machinery from single-view metrology (Criminisi, Reid & Zisserman, 2000).

### 4.3 Low-rank incidence tests

Homogeneous coordinates of lines through a common VP form a **rank-2 matrix**. The nuclear-norm gap from rank 2 is a continuous, differentiable concurrency measure. It avoids brittle RANSAC inlier decisions and doubles as a training loss for mitigation (§3.5E).

### 4.4 Sheaf theory: cohomology of local-to-global consistency ⭐

The most promising tool for the locality hypothesis.

- **Sections:** local camera estimates per image patch (up-vector, local VP directions, focal length).
- **Restriction maps:** agreement conditions on patch overlaps.
- **Real images** admit a global section (one camera explains all patches).
- **Generated images** may be locally consistent everywhere but fail to glue; the obstruction lives in **first cohomology**.
- **Quantification:** sheaf Laplacian energy or Robinson's **consistency radius**.

Gives "locally right, globally wrong" a precise mathematical definition and a number.

### 4.5 Integrability and Hodge decomposition of the perspective field

For a pinhole camera, the up-vector field is generated by a low-dimensional family (all up-vectors point toward one vertical VP).

1. Fit the best camera-induced field.
2. Apply **Helmholtz–Hodge decomposition** to the residual field.
3. Nonzero **curl** = geometry no camera can produce.
4. Line integrals around closed loops give a **holonomy-style** inconsistency measure.

Perspective Fields and GeoCalib estimate these fields but do not test integrability.

### 4.6 Bayesian model comparison over world hypotheses

Compare via Bayes factors / marginal likelihood:
- **Manhattan world** (Coughlan & Yuille)
- **Atlanta world** (multiple horizontal frames)
- **No single camera**

Handles non-Manhattan scenes gracefully and outputs probabilities rather than raw residuals.

### 4.7 Topological data analysis of line intersections

Pairwise intersections of detected segments form a point cloud. Real images → a few tight, **persistent clusters** (the VPs). Generated images → hypothesized diffuse or fragmented clusters. **Persistence diagrams** are noise-stable and independent of any particular VP-estimation algorithm.

### 4.8 Minimum Description Length

A coherent scene compresses better under a "one camera + planes" model than an unconstrained line model. The **MDL gap** between the two codes is an information-theoretic consistency score, related in spirit to coding-cost detectors (Cozzolino et al., 2024) but grounded in geometry rather than pixels.

### 4.9 Distributional distances on residual profiles

Define a **Fréchet Geometry Distance (FGD)** or Wasserstein distance between the distribution of L1–L9 residual vectors for a generator and for real photos. FID asks whether images *look* real in feature space; FGD asks whether their *cameras* look real.

### 4.10 Mechanistic probes for camera parameters

Existing probes target depth and normals. Probe DiT/UNet activations across layers and timesteps for **horizon line, focal length, and VP directions**. Use **activation patching** to locate where a global camera is (or isn't) represented, linking directly to the locality hypothesis and §3.5B.

### 4.11 Conformal prediction for flagging

Wrap any residual in **split-conformal calibration** on real images to obtain guaranteed false-positive rates when flagging images as geometrically inconsistent. Important for any forensic deployment.

---

## 5. Minimum Viable Version

For a first paper:

1. **Implement** L2 (VP concurrency), L3 (camera coherence), L7 (shadows).
2. **Calibrate** on YorkUrban / HoliCity plus a Blender violation-injection suite.
3. **Evaluate** 5–6 generators spanning architectures on content-matched prompts.
4. **Add one theoretical contribution:** the sheaf-cohomology consistency radius (§4.4), paired with the distance-vs-residual locality analysis (§3.5A).

**Narrative:** *current generators satisfy projective constraints locally but lack a global camera.*

Everything else (L4–L9, mitigation, psychophysics, remaining theoretical models) becomes follow-up work.

---

## 6. References

- Sarkar, A., Mai, H., Mahapatra, A., Lazebnik, S., Forsyth, D. A., & Bhattad, A. (2024). *Shadows Don't Lie and Lines Can't Bend! Generative Models don't know Projective Geometry…for now.* CVPR. https://arxiv.org/abs/2311.17138
- Grab-3D: *Detecting AI-Generated Videos from 3D Geometric Temporal Consistency* (2025). https://arxiv.org/abs/2512.13665
- Kee, E., O'Brien, J. F., & Farid, H. (2013). *Exposing Photo Manipulation with Inconsistent Shadows.* ACM TOG.
- Farid, H. (2022). *Perspective (In)consistency of Paint by Text.* arXiv.
- Farid, H. (2022). *Lighting (In)consistency of Paint by Text.* arXiv.
- Du, X., et al. (2023). *Generative Models: What do they know? Do they know things? Let's find out!* NeurIPS.
- Chen, Y., Viégas, F., & Wattenberg, M. (2023). *Beyond Surface Statistics: Scene Representations in a Latent Diffusion Model.* arXiv.
- El Banani, M., et al. (2024). *Probing the 3D Awareness of Visual Foundation Models.* CVPR.
- Jin, L., et al. (2023). *Perspective Fields for Single Image Camera Calibration.* CVPR.
- Veicht, A., et al. (2024). *GeoCalib: Learning Single-image Calibration with Geometric Optimization.* ECCV.
- Criminisi, A., Reid, I., & Zisserman, A. (2000). *Single View Metrology.* IJCV.
- Hoiem, D., Efros, A. A., & Hebert, M. (2008). *Putting Objects in Perspective.* IJCV.
- Coughlan, J. M., & Yuille, A. L. (1999). *Manhattan World.* ICCV.
- Desolneux, A., Moisan, L., & Morel, J.-M. (2008). *From Gestalt Theory to Image Analysis: A Probabilistic Approach.* Springer.
- Lezama, J., Grompone von Gioi, R., Randall, G., & Morel, J.-M. (2014). *Finding Vanishing Points via Point Alignments in Image Primal and Dual Domains.* CVPR.
- Robinson, M. (2017). *Sheaves are the Canonical Data Structure for Sensor Integration.* Information Fusion.
- Cozzolino, D., et al. (2024). *Zero-Shot Detection of AI-Generated Images.* ECCV.
- Hartley, R., & Zisserman, A. (2004). *Multiple View Geometry in Computer Vision* (2nd ed.). Cambridge University Press.

> Some references are cited from memory; verify author lists, venues, and years before use.

---

## 7. Execution Plan & Decisions (living section)

*Added 2026-09-20. Update as phases complete.*

### 7.1 Framing

Sarkar et al. (CVPR 2024) already established convincingly that generated images violate projective geometry, so "AI images break perspective" is **not** the claim. The paper is a **benchmark of geometric understanding**: *which camera constraints do modern generators actually satisfy, and does consistency degrade with spatial separation?* Headline contribution = the local-vs-global analysis (§3.5A, §4.4); the constraint-by-constraint diagnostic table and cross-generator comparison are the supporting contributions.

This is a computer-vision project at its core: single-image projective geometry (line detection, vanishing points, camera calibration, shadow geometry) applied as a measurement instrument to generative models.

### 7.2 Decisions taken

| Decision | Choice | Why |
|---|---|---|
| Scope | Full §5 MVP, delivered in phases | Research paper is the goal; college "mini-project" is only the framing |
| Generated images | Local SD 1.5 / SDXL on RTX 5060 (8 GB) + public corpora (GenImage, Sarkar et al. release) for closed models | No API budget; public corpora cover Midjourney/DALL·E/etc. |
| Primary output | Per-constraint residual **vector** (failure profile); a single aggregate (e.g. FGD, §4.9) only as a headline convenience | One fused score would just be a worse classifier; diagnostics are the point |
| Dataset scale | Stratified 3–5k images with ground-truth VPs on the real side, not 50k+ | Scale does not fix estimator noise; calibration does; many constraints only apply to specific scene types |
| VP estimation | Unconstrained (no Manhattan/orthogonality prior) | If the estimator assumes a pinhole camera, L3 cannot test for one |
| L2 summary statistic | Uncensored *capped mean* + length-weighted *unexplained fraction*, in addition to inlier RMS | Inlier RMS saturates at the inlier threshold (censoring); the capped mean is monotone in violation magnitude (verified synthetically) |
| Thresholds for ✓/✗ tables | Derived from real-photo null distributions (a contrario / conformal), never hand-set | The hardest reviewer objection is "your detector is just worse on AI textures"; calibration is the answer |
| Human-perception study (Gap 6) | **Follow-up paper**, not in scope for paper 1 | Needs ethics approval and a study design; see §7.5 |

### 7.3 Phases (revised order: de-risk the headline early)

| Phase | Content | Status |
|---|---|---|
| 1 | Geometry core: L2 + L3 on classical tools; synthetic scenes with known cameras; violation injectors (`jitter_directions` → L2, `shift_vp` → L3, `drift_vp` → locality); tests | **done 2026-09-20** |
| 2 | Real-image calibration: YorkUrban (102 imgs, GT VPs), HoliCity subset. Null distributions of every residual; estimator accuracy vs ground truth | **YorkUrban done 2026-09-20** (7.7); **2b Commons wild set done 2026-09-22** (7.12); HoliCity dropped (single virtual camera) |
| 3a | **Pilot**: ~200 real vs ~200 SDXL content-matched images; run the distance-vs-error locality curve. Go/no-go for the headline narrative | **done 2026-09-22 - GO** (see 7.9) |
| 3b | Full corpus: SD 1.5, SDXL, (FLUX if VRAM allows), public corpora for closed models; prompt strata of §3.4; log seeds/steps/CFG/dates | SD 1.5 + SDXL done (200 each); frontier models via `data/generated/prompts.txt` pending |
| 4 | L7 shadows: Kee–O'Brien–Farid wedge constraints as an LP; shadow/object pairs via SSIS or SAM 2 (semi-automatic first) | **geometry done + validated 2026-09-28 (7.16); association front-end unsolved** |
| 5 | Locality analysis formalized: pairwise → windowed cameras → sheaf consistency radius (§4.4) | **first version done 2026-09-22** (7.10); bootstrap CIs + per-structure sections pending |
| 6 | Blender injection suite (photoreal version of the Phase-1 synthetic tests, incl. shadows) → detection rate vs violation magnitude per level | |
| 7 | Evaluation across generators, figures, writing | |

### 7.4 The locality metric — definition and its known confound

Three candidate definitions, increasing in rigor; all three will be reported:

1. **Pairwise.** Two segments in the same VP cluster intersect at a "local VP"; measure its angular disagreement with the global VP as a function of the distance between the segments.
2. **Windowed.** Estimate a full camera (VPs, f) inside sliding windows; disagreement between windows vs. window separation. Real photo → flat curve; generator → rising curve. The transition length scale is the quantity of interest (compare to patch size / attention span / VAE factor).
3. **Sheaf consistency radius** (§4.4): the smallest perturbation that makes all local camera sections glue into one global section.

**Confound to model explicitly:** nearby, nearly-parallel segments give ill-conditioned intersections, so estimator noise in (1) is *largest* at small separation and decreases with distance — opposite to the hypothesized trend. This makes a positive result conservative, but the real-image control curve must be shown, and the Phase-1 `drift_vp` injector verifies the metric recovers a known drift above that noise floor.

### 7.7 Phase 2 results (YorkUrban, n = 102, 640×480)

- **VP recovery** (LSD + unconstrained RANSAC): 81 % of GT VPs within 2°, 94 % within 5°. On the hand-labelled lines the estimator alone reaches 0.54° median error, so most of the gap is the detector / non-Manhattan clutter, not the estimator.
- **Focal length**: median `f_fit / f_true` = 1.02 (IQR 0.99–1.05) from LSD lines, 1.00 on GT lines. The L3 machinery recovers the real camera.
- **Null distributions** (`results/yorkurban_null_percentiles.json`): L2 capped mean p50 = 1.3°, p95 = 2.5°; unexplained fraction p50 = 17 %; L3 ortho error p50 = 0.7°, p90 = 6.8°, p95 = 64° (raw) → p90 = 1.6°, p95 = 2.8° when restricted to images with three *reliable* VPs (84/102).
- **Two failure modes of the estimator, both now measured**: (i) *spurious third VP* from leftover clutter (cars, awnings) when the true third family is weak — ~10 % of images; (ii) *far-VP conditioning*: near-parallel families let the VP slide along their direction, which at f ≈ 675 px is several degrees in ray space. (ii) is captured by bootstrap uncertainty (`vp_std_deg`); (i) only partially (a self-consistent spurious cluster looks confident). Reliability flag: bootstrap std < 1° and support ≥ 5 % of line length.
- **Implication for the benchmark**: the spurious-VP rate depends on line density and clutter, so generated images must be *content-matched* (§3.3) or L3 differences are confounded. Report "fraction of images with three reliable VPs" as its own statistic.
- **Follow-ups**: better multi-model VP estimator (J-linkage / Gaussian-sphere accumulator) and DeepLSD lines to cut the spurious rate; HoliCity subset for higher-resolution real images (generated images will be 1024²; residual scaling with resolution must be checked).

### 7.8 Locality metric: what survived validation (2026-09-20)

Implemented in `projgeo/locality.py` and validated on synthetic scenes with known drift:

| Candidate | Verdict |
|---|---|
| Pairwise two-line VP vs global VP | **Rejected as primary.** Dominated by conditioning: on clean scenes disagreement *falls* with distance (2° → 0.6°), and under drift the near bins *rise* because ill-conditioning amplifies small VP differences. |
| Image-minus-"consistent twin" excess | Removes the conditioning confound (clean → 0) but absorbs drift into the matched noise level, leaving only a slope signature. Kept as secondary. |
| **Signed-residual variogram** | **Primary.** ρ(d) = spatial correlation of signed angular residuals between same-VP segments at separation d. Independent noise → flat 0; random jitter → 0 (correctly *not* locality); drift → ρ > 0 near, ρ < 0 far. Locality index = ρ_near − ρ_far. Uses uncensored nearest-VP assignment (cap 10°) so large drifts are not thrown out. |

**Key finding — real photos are not at zero.** YorkUrban gives a locality index of +0.26 (LSD pipeline) and +0.38 on the *hand-labelled* lines vs GT VPs, so it is in the photographs, not the pipeline. A single dataset-wide radial distortion fit (k₁ ≈ +0.06) halves it (0.39 → 0.19); the remainder is the world not being perfectly Manhattan (sub-families with their own VPs, spatially clustered). Consequences:

1. The hypothesis test is **"generated > content-matched real"**, not "real = 0". Report the real-photo distribution alongside every generator.
2. Lens distortion is a nuisance parameter: report the index raw and after a per-image radial-distortion fit.
3. Collinear LSD fragments of one edge inflate short-range correlation (+0.05); exclude near-collinear pairs (perpendicular distance < 6 px and angle < 2°).
4. The framing sharpens: *the world is only locally Manhattan — are generators more local than the world?*

### 7.9 Phase 3a pilot results (2026-09-22): GO, with the hypothesis refined

Setup: 102 YorkUrban photos vs 200 SDXL-base images (1024x768, 30 steps, CFG 6, prompts mirroring YorkUrban content, downscaled to 640 px for analysis). Identical pipeline. Content match confirmed: LSD segment counts do not differ (p = 0.13). Files: `results/pilot_sdxl_vs_yorkurban.{md,png}`, `results/pilot_summary.csv`.

| Test | Real (median [IQR]) | SDXL | p (Mann-Whitney) |
|---|---|---|---|
| L2 concurrency, capped mean | 1.31 [1.04, 1.73] deg | 1.23 [0.87, 1.80] deg | 0.11 (n.s.) |
| L3 orthogonality error (max pair) | 0.69 [0.46, 1.32] deg | 4.36 [1.39, 47.8] deg | 1.5e-17 |
| L3, images with 3 reliable VPs only | 0.66 deg (n = 84, 82 %) | 2.88 deg (n = 93, 46 %) | 4e-14 |
| L3 focal spread across VP pairs | 0.10 | 0.41 | 5e-14 |
| Share above real p95 (L3) | 5 % | 22 % (51 % among 3-reliable-VP images) | |
| Locality index (within-family variogram) | 0.16 | 0.18 | 0.33 (n.s.) |
| Focal ratio left half / right half | 1.20 | 1.63 | 6e-6 |
| Outdoor vs indoor L3 (SDXL) | | 13.6 deg vs 1.9 deg | |

**Reading.**
1. *Each family of parallel lines converges as well as in a real photo* (L2 identical). The generator has learned "lines that go together meet at a point".
2. *The families do not share a camera* (L3). Half of the coherent SDXL images imply pairwise focal lengths that disagree by more than any real photo in the null; example `results/example_sdxl_0010_three_cameras.png` implies f = 1626 / 321 / 951 px from its three VP pairs. Only 46 % of SDXL Manhattan-prompted images even yield three reliable VPs (82 % real).
3. *The inconsistency is between structures/regions, not a smooth drift within a family.* The signed-residual variogram - which detects spatially smooth VP drift within one line family - is indistinguishable from real photos. But cameras fitted to the left and right halves of an SDXL image disagree on f by 63 % (real: 20 %).

**Refined hypothesis for the paper:** the unit of local consistency is a *structure* (a facade, a floor, a row of windows), each internally coherent; the generator lacks the global camera that ties structures together. "Locally right, globally wrong" holds at the level of structures and image regions, not of pixel-distance within a family. This is exactly what the sheaf formulation (4.4) models if sections are per-structure cameras rather than per-patch VPs.

**Consequences for the plan.** Phase 5 should build the *windowed / per-structure camera* comparison (half-image focal ratio -> grid of cameras -> sheaf consistency radius) as the headline metric; keep the variogram as the negative control that rules out smooth drift. Phase 3b adds more generators; outdoor scenes are the sensitive stratum.

### 7.10 Phase 5, first version: regional camera consistency (2026-09-22)

`projgeo/regional.py`. A 3x3 grid of half-size overlapping windows; each window gets its own unconstrained camera (VPs + focal, shared principal point). Windows = open cover, local cameras = sections, restriction maps = identity, so pairwise camera distance on overlaps is the gluing failure and the **consistency radius** = min over one global camera of the max distance to every local camera (min-max fit; rotation part solved by Nelder-Mead, focal part = half the log-range). Validated on synthetic scenes with an injected two-camera split (`synth.two_cameras`): recovers half the injected log-focal ratio and half the injected rotation to within noise, and detects a x1.3 focal split that the global L3 test barely registers (0.31 deg).

Real vs SDXL (same pilot sets):

| Regional metric | Real | SDXL | p |
|---|---|---|---|
| Consistency radius, focal (|log f|) | 0.32 [0.19, 0.53] | 0.89 [0.44, 1.72] | 3e-14 |
| Pairwise |log f_i / f_j| (median) | 0.21 | 0.63 | 8e-21 (strongest separation of any metric) |
| Consistency radius, rotation | 5.8 deg | 7.2 deg | 0.02 (weak) |
| Adjacent-window frame rotation | 4.3 deg | 5.6 deg | 0.04 (weak) |
| Share above real p95 (focal radius) | 5 % | 30 % | |

**Reading.** What varies across regions of a generated image is the *focal length* - the strength of perspective - not the orientation of the Manhattan frame. Physically sensible: VP directions are pinned by the dominant lines in every window, but the focal length is set by the *distances between* VPs, i.e. by how fast lines converge, and that is what the generator fails to keep consistent from one part of the image to another. The rotation component has a high real-photo noise floor (5.8 deg) from windows with only two matched VPs; needs bootstrap CIs and larger windows before it can be interpreted.

**Length scale (2026-09-22, `results/scale_curve_sdxl_vs_real.png`, 80 images per set).** Median pairwise |log f_i/f_j| between windows vs window size (fraction of image side):

| window | 0.30 | 0.40 | 0.50 | 0.65 | 0.80 |
|---|---|---|---|---|---|
| real | 0.30 | 0.26 | 0.21 | 0.09 | **0.03** |
| SDXL | 0.83 | 0.91 | 0.59 | 0.48 | **0.25** |
| ratio | 2.8x | 3.5x | 2.8x | 5.1x | 8.2x |

Real photos converge to a single camera as the window grows (3 % focal disagreement at 80 %); SDXL never converges (29 % at 80 %) and the gap *widens* with scale. There is no window size at which SDXL keeps one camera. The rotation component peaks at mid-size windows for both sets (estimator noise shape) with SDXL only modestly above real - again focal length, not orientation.

*Consistent-twin control* (same segments re-aimed at the global VPs, uncensored membership within 10 deg, noise from tight inliers): excess over twin is positive for SDXL at every scale (0.07-0.18 vs 0.01-0.09 real) but with wide per-image spread; the control is conservative for generated images because lines further than 10 deg from every VP are left as they are. Report raw + real-control as primary, twin-excess as the lower bound.

**Still to do in Phase 5:** (i) bootstrap CIs per window; (ii) sections per *structure* (segment clusters by VP pair / plane) rather than fixed windows; (iii) sheaf-Laplacian energy as the aggregate; (iv) FLUX / frontier models on the same curve.

### 7.11 Three generators and a confound (2026-09-22)

`results/three_way_real_sd15_sdxl.{md,png}`: YorkUrban (102) vs SD 1.5 (200, 640x480) vs SDXL (200).

**Scaling.** SD 1.5 -> SDXL improves every level: L2 1.48 -> 1.23 deg (real 1.31, i.e. SDXL reaches real-photo concurrency), L3 10.4 -> 4.4 deg raw, 5.1 -> 2.9 deg on 3-reliable-VP images (real 0.66). Lines learned to converge; a shared camera did not. First data point for the scaling analysis (3.5C).

**Confound found: camera-configuration diversity.** Real YorkUrban is one camera (fitted HFOV 48-51 deg). Generated images imply HFOV from 15 to 62 deg. Telephoto-like views put the VPs far away, where focal length is ill-determined in *every* window, so raw regional focal disagreement is inflated by conditioning as well as by inconsistency. The consistent-twin noise floor makes this visible (0.07 real vs 0.33 SDXL on 3-reliable-VP images). After subtracting the floor, the regional excess stays positive for both generators (0.17-0.19 vs 0.11 real) but is only borderline significant at n ~ 90 (SD 1.5 p = 0.05, SDXL p = 0.21).

**Consequences.**
1. L3 (with bootstrap-reliability filtering) is the robust headline; the regional-focal length-scale result (7.10) must be reported with the twin floor and stratified by fitted HFOV.
2. **Phase 2b needed: a real set with diverse cameras** (EXIF focal lengths), because comparing a single-camera real set against generators that emit a distribution of cameras is unfair on every focal-based metric. Candidates: building/street photos with EXIF from a public dataset, or the real split of the Sarkar et al. release; HoliCity is also a single synthetic pinhole per panorama.
3. Stratify all comparisons by fitted HFOV (or match on it) in Phase 7.
4. Frontier models (Gemini, GPT-image) via the exported prompts `data/generated/prompts.txt`.

### 7.12 Phase 2b: a second real set changes the picture (2026-09-22)

`scripts/collect_commons.py` -> `data/real/commons/`: 358 Wikimedia Commons photos (CC-licensed, attribution in metadata.jsonl) from **135 camera models** with EXIF focal lengths, same content strata as the prompts (241 outdoor / 117 indoor). Focal validation against EXIF (`results/commons_focal_validation.png`): L3 fit unbiased (median +6 %) but only 58 % within 20 % on well-conditioned images - EXIF 35 mm-equivalents are rounded, many photos are cropped.

**Four-set comparison** (`results/four_set_comparison.{md,png}`), L3 orthogonality error, median:

| | YorkUrban | Commons (wild real) | SD 1.5 | SDXL |
|---|---|---|---|---|
| all images | 0.69 deg | **12.2 deg** | 10.4 deg | 4.4 deg |
| HFOV in [40, 60] deg | 0.62 | 9.9 | 4.3 | 2.1 |
| 3 reliable VPs | 0.66 | 5.0 | 5.1 | 2.9 |
| orthocentre offset (/diag), median | 0.07 | 1.0 | 2.0 | 1.6 |
| negative f^2 with centred pp | 21 % | 58 % | 72 % | 73 % |

**Wild real photos fail the centred-principal-point L3 test as badly as SD 1.5, and worse than SDXL.** Cropping explains part (cropped-aspect Commons photos: 24 deg vs 11 deg) but uncropped Commons photos still sit at 11 deg with orthocentres ~0.8 diagonals off-centre. Remaining causes are legitimate pinhole images that violate the *centred-pp* assumption - perspective-corrected / shift-lens architecture photographs (ubiquitous on Commons for facades), plus frontal views where the third VP is spurious and general non-Manhattan clutter. YorkUrban was hand-curated to have none of this.

**Consequences (the central methodological lesson so far).**
1. *The null distribution is not a property of "real photos"; it is a property of the real set.* Against YorkUrban SDXL looks broken; against Commons it looks better than real. Any paper claim must state the real set and its selection criteria, and should use both an idealised set (YorkUrban) and a wild set.
2. The current L3 (pp fixed at centre) is the right test for *controlled* images (uncropped, unshifted - which includes generated images by construction) but not for wild photographs. A **principal-point-free L3** is needed as the wild-photo-valid necessary condition: with three finite VPs a camera exists iff the VP triangle is acute; the implied pp offset then measures crop/shift. (`scripts/l3_ppfree.py`, results in 7.13 when available.)
3. Real-set selection must be made explicit and mirrored for generated images: e.g. require three reliable, well-separated VPs *and* an acute triangle, then compare residual magnitudes.
4. Regional focal disagreement: Commons 0.33, SD 1.5 0.48, SDXL 0.63 (YorkUrban 0.21) - generators still worst, but the real-set dependence is again large. Twin-excess: Commons 0.12, SD 1.5 0.19, SDXL 0.19, borderline.
5. The within-family variogram remains null for every set - smooth spatial drift is not the failure mode for any generator or real set.

### 7.13 Principal-point-free L3 (2026-09-22): the estimator, not the photos

`scripts/l3_ppfree.py`, 80 images per set, images with three reliable VPs only. With the principal point free, a pinhole camera exists iff the VP triangle is acute.

| | YorkUrban | Commons (wild real) | SD 1.5 | SDXL |
|---|---|---|---|---|
| n with 3 reliable VPs | 64 | 41 | 41 | 36 |
| obtuse triangle (no camera for any pp) | 12 % | **71 %** | 51 % | 53 % |
| acute: implied HFOV (median) | 51 deg | 65 deg | 59 deg | 25 deg |
| acute: implied pp offset > 0.25 diag | 4 % | 25 % | 40 % | 47 % |

Real photographs were taken by cameras, so 71 % "no camera" on Commons is **estimator failure on uncurated content** (spurious third VPs from clutter, non-Manhattan scenes, rectified facades with two VPs at infinity), not photo geometry. On wild content the estimator error swamps any generator signal; the reliability flag (bootstrap std + support) does not catch self-consistent spurious clusters.

**Re-prioritisation.**
1. VP *significance* is now the top engineering task: a contrario NFA with a structured background model, J-linkage / T-linkage multi-model fitting, or a Gaussian-sphere accumulator with a Manhattan-*agnostic* significance test; plus better lines (DeepLSD) if installable. Success criterion: obtuse-triangle rate on Commons drops toward YorkUrban's 12 % without touching generated images' rate.
2. Real-set curation must be explicit and mirrored on the generated side: the paper reports (a) a curated Manhattan set (YorkUrban) and (b) a wild set, both with the same selection rule applied to generated images, and states the selection rate per set as a result in itself.
3. Until (1) is done, the defensible headline is the YorkUrban-vs-generated comparison on Manhattan-prompted images, with the caveat that the generated sets are less Manhattan than YorkUrban (46 % vs 82 % three-reliable-VP rate).

Among acute-triangle SDXL images the implied HFOV is 25 deg (telephoto-like) and 47 % have the implied principal point more than a quarter-diagonal off centre - both consistent with "each structure gets its own camera" (7.9), but only interpretable once the estimator is trustworthy.

### 7.14 VP significance: what was tried and what it taught (2026-09-22)

Goal (7.13 item 1): cut the "no camera exists" rate on wild real photos without touching generated images. Three attempts, 80 images per set:

| Attempt | Result |
|---|---|
| **Permutation null** (`vp.permutation_null`): compare each VP's support with RANSAC on the same lines with directions permuted (same layout, same orientation histogram, no convergence) | Does not separate: spurious VPs on YorkUrban still have z ~ 4-5. They are *genuinely concurrent* lines - real 3D directions that are simply not orthogonal to the other two (roof pitches, diagonal streets, a second facade). Kept as opt-in (`n_perm`). |
| **Best-triple model selection** (`camera.select_manhattan_triple`, plan 4.6): up to 5 candidate VPs, pick the triple most consistent with one camera | YorkUrban 91 % pass the real-null threshold (2.8 deg); SDXL 50 %, SD 1.5 42 %, **Commons 27 %**. Support-gating the triple makes Commons *worse* (strongly supported triples still fail, median 27-45 deg). |
| **Atlanta focal consistency** (`camera.atlanta_focal_consistency`): vertical VP found by direction only; every horizontal VP must give the same f with it | Orders the sets: impossible-pair rate YorkUrban 18 % < Commons 48 % < SD 1.5 57 % ~ SDXL 54 %; log-f spread 0.13 < 0.38 < 0.30 / 0.55. Applies to Atlanta worlds, but the wild-real vs generated gap is small. |

Visual inspection of the failing Commons images settles it: e.g. `outputs/commons_bad_100038573.png` is a curved street with two facades - two horizontal VPs that are *legitimately* non-orthogonal plus verticals. **The three-VP camera test is only defined for scenes with three visible orthogonal directions; on uncurated content its failure is an applicability failure, not an estimator failure and not a photo failure.** Cropping, shift-lens / software perspective correction (common on Commons architecture photos) add a second, independent violation of the centred-principal-point assumption.

**Decisions.**
1. The paper's L3 experiment is **content-controlled by construction**: prompts that guarantee three visible directions (corridors, room corners, street corners) vs a real set curated the same way (YorkUrban qualifies; a diverse-camera curated set still needs building - hand-select ~100 Commons images with three visible directions, or use a horizon/VP dataset of internet photos). Wild Commons stays as the *wild* reference with the applicability caveat.
2. Pipeline now reports three L3 variants: top-3 (`L3`), best-triple (`L3_best`), Atlanta (`L3_atlanta`); `pilot_compare.py` includes them.
3. VP-estimator improvement is demoted from top priority: the estimator is adequate on Manhattan content (81 % GT VPs within 2 deg); the limit is the test's applicability. DeepLSD / J-linkage remain nice-to-have.

### 7.15 Residual classifiers: comparison with Sarkar et al. (2026-09-28)

`scripts/classify_residuals.py` -> `results/classifier_report.md`, `results/classifier_roc.png`. Six classifiers (logistic regression, decision tree, SVM-RBF, random forest, naive Bayes, kNN) on the **per-image residual vector only** - never pixels. 5-fold stratified CV AUC. Features are grouped so that camera-configuration / content columns (HFOV, f, k1, segment counts) can be excluded from the "geometry" condition.

| Task | best AUC, geometry only | + configuration features |
|---|---|---|
| YorkUrban vs SDXL | 0.916 (SVM) | 0.927 (RF) |
| YorkUrban vs SD 1.5 | 0.916 | 0.943 |
| Commons (wild) vs SDXL | 0.824 (RF) | 0.817 |
| all real vs all generated | 0.835 (RF) | 0.836 |
| HFOV 40-60 deg matched | 0.810 (RF) | 0.796 |

Sarkar et al. (CVPR 2024) report roughly 0.88-0.94 AUC for their *learned* line classifier and 0.86-0.92 for perspective fields on their hardest set. Our explicit residuals reach the same band (0.92) against a curated real set, and hold 0.81-0.82 in the two hardest conditions - **wild real photos** and **HFOV-matched** - where a naive detector could not rely on camera configuration. The point is not to win on AUC but that interpretable, unit-bearing residuals are competitive with black-box features while saying *which* constraint failed.

**Per-group AUC (random forest, alone):** L3 is the strongest single group everywhere (0.91 curated / 0.78 wild), REGIONAL second (0.84 / 0.71), L2 third (0.67-0.79), **LOCALITY at chance (0.45-0.54)** - the variogram carries no real-vs-generated signal, consistent with 7.9-7.11. Configuration features alone give 0.89 against YorkUrban but only 0.69 against Commons, quantifying the confound of 7.11: a large part of "detection" against a single-camera real set is just camera diversity, which is why the geometry-only and HFOV-matched columns are the honest ones.

**Permutation importance (held-out folds, curated vs SDXL):** `orthocenter_offset` 0.034, `f_boot_cv` 0.016, `reg_logf_pairwise` 0.013, `f_spread` 0.007, `reg_radius_logf` 0.005 - every leading feature is about *focal-length / principal-point coherence*, none about line straightness or concurrency. Same conclusion as 7.10 from an independent direction.

*Caveat:* SDXL images are downsampled 1024 -> 640 for analysis while YorkUrban is native 640; resampling changes LSD statistics. The Commons-vs-SDXL comparison is resampling-matched (both downsampled) and still gives 0.82, so resampling is not driving the result, but the curated comparison should be repeated with native-resolution generation at 640.

### 7.16 L7 shadows: geometry solved, association is the blocker (2026-09-28)

`projgeo/shadows.py`, `tests/test_shadows.py` (6 tests), `scripts/l7_shadows.py`.

**What works (validated).**
- **Wedge-constraint LP** (Kee, O'Brien & Farid 2013). A shadow point plus the object region it may have come from defines a wedge of admissible light positions (two half-planes); one light exists iff all wedges intersect. Implemented as `min t s.t. A L - b <= t` with unit normals, so `t` is in **pixels**: `t <= 0` means feasible with margin, `t > 0` is how far the constraints are from admitting any light. A zero-width wedge (exact correspondence) degenerates correctly into a line constraint. A distant sun is handled by bounding `|L|` at 50 image diagonals rather than a separate projective branch.
- **Synthetic scenes** (`synth.make_shadow_scene`, y-down world, base points back-projected from image space onto the ground plane): the light-VP fit recovers the sun's image exactly (|est . gt| = 1.0000, residual 0.06-0.66 deg). Injected shadow rotation makes the LP violation grow monotonically (feasible at 0 deg, infeasible from 10 deg at 5 px annotation width), and wider annotation wedges are strictly more permissive - the test never cries foul below the annotation uncertainty.
- **Shadow detection** (syllabus Unit 1: gray-value transformation, Otsu thresholding, morphological closing/opening, connected components with an area filter). Clean on clearly sunlit outdoor scenes: `results/example_shadow_mask_works.png`.

**What does not work: automatic shadow-object association.** To avoid needing object segmentation I tried an association-free variant: shadows of upright objects run along the sun's azimuth, so their major axes should converge at one VP, which should lie on the horizon. Measured on 640 px images:

| | YorkUrban | Commons | SDXL (sunlit) | SD 1.5 (sunlit) |
|---|---|---|---|---|
| shadow-axis concurrency RMS | 14.4 deg | 14.9 deg | 32.5 deg | **3.0 deg** |
| sun VP distance from horizon | 0.20 | 0.26 | 1.19 | 0.30 |
| images with >= 3 axes | 48 % | 44 % | 65 % | 35 % |

The real-photo null is 14 deg and **SD 1.5 scores better than real photographs** - the test is measuring the detector, not the light. `results/example_shadow_axes_fail.png` shows why: the mask fires on dark glass, signs and shaded interiors, and the extracted "axes" are signs and glass panels. Blurrier SD 1.5 images give fewer, smoother blobs whose axes agree by accident. Same failure shape as 7.13-7.14: an untested applicability assumption (here "elongated dark region = cast shadow of an upright object on a horizontal plane") rather than an estimator bug.

**Consequences.**
1. The association-free variant is **dropped** as a primary metric. Kee et al. hand-annotated correspondences for exactly this reason.
2. L7 needs real association: instance shadow detection (SSIS) or SAM 2 masks for object-shadow pairs, or a hand-annotated subset (~50 images per set is enough for the LP, which uses few pairs per image).
3. The content must match the test: a **sunlit outdoor stratum with upright objects** on both sides. YorkUrban is largely indoor/overcast, so it is the wrong real set for L7; a targeted Commons collection (sunlit streets with poles/bollards/people) is needed.
4. Everything above the association layer is done and validated, so once pairs exist the residual is one function call.

### 7.17 Content-controlled L3: the headline narrows (2026-09-28)

`projgeo/selection.py`, `scripts/l3_controlled.py`, `results/l3_controlled_table.md`.

**The applicability rule.** An image is *identifiable* when three VP families are each supported by >= 8 % of detected line length, localised to < 1 deg (bootstrap), resolvably distinct (VP separation >= 10 deg and >= 5x its own uncertainty) and spatially spread (>= 0.12 diagonal). Orthogonality, focal length, orthocentre and triangle shape are excluded by construction - they are the measurement. Real photographs additionally need a standard aspect ratio (cropping moves the principal point). Two validations:
* against YorkUrban ground truth, selected images have 90 % of VPs within 5 deg of the hand-labelled truth vs 57 % of rejected ones, and the L3 > 5 deg rate falls from 30 % to 7 %;
* `tests/test_geometry.py::test_identifiability_is_independent_of_orthogonality` injects a `shift_vp` violation (breaks L3, preserves the line layout) and asserts the selection decision is unchanged - so the rule cannot be selecting real images for being consistent.

**Selection rates are themselves a result.** Curated real 71 %, SDXL 40 %, wild real 30 %, SD 1.5 30 %.

**L3 among selected images** (medians; n = 72 / 109 / 61 / 79):

| | YorkUrban | Commons (wild real) | SD 1.5 | SDXL |
|---|---|---|---|---|
| orthogonality error, max pair | 0.65 deg | 2.19 | 3.29 | 1.75 |
| focal spread across VP pairs | 0.08 | 0.11 | 0.22 | 0.43 |
| orthocentre offset (/diag) | 0.06 | 0.18 | 0.33 | 0.94 |
| above YorkUrban p95 | 6 % | **23 %** | 15 % | 9 % |

Filtering cuts wild-real L3 from 12.2 deg (7.12) to 2.19 deg, confirming the 7.14 diagnosis: the wild-photo failure was applicability, not photo geometry.

**Selected *and* HFOV-matched to 40-60 deg** (n = 65 / 22 / 23 / 24), the cleanest comparison available:

| vs reference | L3 ortho | focal spread | orthocentre offset |
|---|---|---|---|
| SDXL vs **curated** real | 1.52 vs 0.62, p = 4e-5 | 0.46 vs 0.08, p = 5e-7 | 0.63 vs 0.06 |
| SD 1.5 vs curated real | 2.26 vs 0.62, p = 3e-6 | 0.19 vs 0.08, p = 0.002 | 0.24 vs 0.06 |
| SDXL vs **wild** real | p = **0.47 (n.s.)** | p = 0.003 | p = 0.036 |
| SD 1.5 vs wild real | p = **0.94 (n.s.)** | p = 0.25 (n.s.) | p = 0.76 (n.s.) |

**Revision of the headline.** Once content and camera configuration are controlled, **generated images' orthogonality error is statistically indistinguishable from wild real photographs**. The large gap reported in 7.9-7.11 was measured against a hand-curated, single-camera dataset and is substantially an artefact of that reference. What survives against wild real photographs is narrower and more specific: **the coherence of the implied focal length and principal point** (SDXL focal spread 0.46 vs 0.075, p = 0.003; orthocentre offset 0.63 vs 0.22, p = 0.036) - and for SDXL only, not SD 1.5. This agrees with the two independent lines of evidence in 7.10 (regional focal disagreement) and 7.15 (every top classifier feature is a focal / principal-point feature).

So the defensible claim is: *generators satisfy the orthogonality of the Manhattan frame about as well as ordinary photographs, but do not commit to one focal length and one principal point across the image.* The "no global camera" thesis stands; "fails the three-VP orthogonality test" does not.

**Caveats / next.** The matched band has only 22-24 images per generated set; the three-direction prompt stratum (`projgeo.prompts.three_direction`, `data/generated/sdxl_3d`) exists to raise the selection rate and restore power, and must be run for SD 1.5 and the frontier models too. A curated *diverse-camera* real set remains the missing reference: Commons-selected is the closest available but still differs in HFOV distribution.

### 7.18 Three-direction stratum: a failed fix with a useful by-product (2026-09-28)

120 SDXL images from `prompts.three_direction` (room corners, corridor turns, building corners) vs the original street/facade stratum, same pipeline and selection rule (`results/l3_3d_table.md`):

| | YorkUrban | Commons | SDXL street/facade | SDXL 3-direction |
|---|---|---|---|---|
| selected (identifiable + uncropped) | 71 % | 30 % | **40 %** | **30 %** |
| median detected segments | 386 | 418 | 426 | **318** |
| L3 orthogonality error | 0.65 deg | 2.19 | 1.75 | **1.32** |
| best-triple L3 | 0.62 | 1.85 | 1.37 | **0.99** |
| focal spread | 0.08 | 0.11 | 0.43 | **0.46** |
| orthocentre offset | 0.06 | 0.18 | 0.94 | 0.59 |

**The fix failed for a diagnosable reason.** Prompting for corners *lowered* the selection rate (40 % -> 30 %) because corner scenes as written are line-*sparse* - empty rooms, plain walls - so the weakest VP family falls below the 8 %-of-line-length support threshold. Dominant rejection reasons are unchanged in kind ("weakest family supports only x %", "worst VP localised to y deg"), just more frequent. Scene *structure* was improved at the cost of scene *evidence*. Hence `prompts.three_direction_rich` (v2): every template now pairs the corner with at least two repeating line-rich features (tiles, shelving, window grids, panelled ceilings, brick courses).

**The useful by-product.** In the three-direction scenes SDXL's orthogonality improves markedly (1.75 -> 1.32 deg; best-triple 1.37 -> 0.99, approaching the curated-real 0.62) while **focal spread does not move at all** (0.43 -> 0.46). Giving the model an easier, well-structured Manhattan scene buys better orientation consistency and buys nothing for focal coherence. That is independent support for the narrowed claim of 7.17: the deficit is a single-camera *focal length / principal point* deficit, not an orientation deficit.

### 7.5 Follow-up paper: human perception of geometric violations (Gap 6)

If paper 1 succeeds: psychophysics study pairing human ratings with measured residuals. Question: *which violations are mathematically severe but visually unnoticed, and vice versa?* Separates forensically detectable from perceptually salient errors, and gives a perceptual weighting for any aggregate score. Needs ethics approval, a stimulus set drawn from the paper-1 corpus with known residuals, and a 2AFC or rating design. Related: §3.5D.

### 7.6 Other follow-ups kept out of paper 1

- Mitigation via differentiable L2–L3 residuals as rewards (§3.5E).
- Mechanistic probes / activation patching for camera parameters (§4.10).
- Denoising-time formation analysis (§3.5B).
- Remaining levels L4–L6, L8–L9 and theoretical models §4.5–§4.9, §4.11.

---

## 8. Plain-Language Glossary of the Constraint Levels

Each level is one rule a real pinhole camera cannot break. A residual is "how badly the rule is broken", in interpretable units.

| Level | Rule in one sentence | Residual unit | Status |
|---|---|---|---|
| **L1 Straightness** | Straight edges in 3D stay straight in the photo (after removing lens distortion). | curvature (px) | later |
| **L2 VP concurrency** | Lines that are parallel in 3D all meet at one vanishing point in the image. | degrees | **implemented** |
| **L3 Camera coherence** | The three VPs of a room/building must correspond to three perpendicular 3D directions for *some* focal length; equivalently the image centre is the orthocentre of the VP triangle. | degrees from 90°, focal spread | **implemented** |
| **L4 Horizon consistency** | All horizontal VPs lie on a single horizon line, which must agree with other horizon estimates (perspective field, object heights). | px / degrees | later |
| **L5 Projective invariants** | Equally spaced things (fence posts, tiles) keep a fixed cross-ratio; repeated planar texture is related by one homography. | ratio error, px | later |
| **L6 Conics** | Circles on one plane (plates on a table) become ellipses that share the same two "circular points" on that plane's horizon. | algebraic distance | later |
| **L7 Shadows** | Lines from shadow points to the object points that cast them all converge to the light source's image (one sun → one point). | LP feasibility / degrees | MVP, phase 4 |
| **L8 Reflections** | Lines joining points to their mirror reflections are parallel in 3D, so they converge to one VP. | degrees | later |
| **L9 Cross-modal** | Plane normals derived from VPs must agree with normals from a monocular depth/normal network. | degrees | later |

L2, L3 and L7 form the minimum viable paper (§5).
