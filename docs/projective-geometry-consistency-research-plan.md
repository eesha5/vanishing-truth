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
