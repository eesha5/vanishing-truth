# projgeo — Projective Geometry Consistency of AI-Generated Images

Every image is treated as the claim *"a single pinhole camera photographed this
scene"*. A hierarchy of projective constraints (L1–L9, see
[the research plan](docs/projective-geometry-consistency-research-plan.md))
tests that claim, each returning an interpretable residual instead of a
learned score.

## Status

| Phase | Content | State |
|---|---|---|
| 1 | Geometry core: L2 (VP concurrency) + L3 (camera coherence), synthetic validation | done |
| 2 | Real-image calibration (YorkUrban done; HoliCity pending) | in progress |
| 3a | Pilot: ~200 real vs ~200 SDXL, locality curve (go/no-go) | next |
| 3b | Full generated corpus (SD 1.5, SDXL local; public corpora for closed models) | |
| 4 | L7 shadows (wedge-constraint LP) | |
| 5 | Locality analysis + sheaf consistency radius | |
| 6 | Blender injection suite | |
| 7 | Evaluation & paper | |

## Usage

```bash
pip install -e .[dev]
python -m pytest -q
python scripts/analyze_image.py path/to/image.jpg --out outputs/
```

`analyze_image.py` writes a JSON report, an overlay PNG (segments coloured by
VP cluster, VPs, orthocentre `x` vs image centre `+`) and `summary.csv`.

## Residuals implemented

**L2 — concurrency.** Unconstrained sequential RANSAC + angular least squares
finds up to 3 VPs (no Manhattan prior, so L3 stays a genuine test).
Reported: inlier RMS, length-weighted *unexplained fraction* (segments no VP
explains within the threshold), and a *capped mean* residual over all
segments (uncensored, monotone in violation magnitude).

**L3 — camera coherence.** With principal point at the image centre, the best
single focal `f` is fitted; the residual is the pairwise deviation of the
back-projected VP rays from 90°. Also: per-pair closed-form `f² = −(vᵢ−p)·(vⱼ−p)`
(negative = impossible camera), spread of the focal estimates, and the offset
of the VP-triangle orthocentre from the image centre. Handles VPs at infinity.

## Synthetic validation (`projgeo/synth.py`)

Random pinhole cameras in a box of axis-aligned 3D segments, with three
injectors: `jitter_directions` (breaks L2 only), `shift_vp` (breaks L3 only,
L2 untouched) and `drift_vp` (VP moves with image position — the
"locally right, globally wrong" hypothesis). `tests/test_synth.py` checks
clean recovery (VPs < 0.5°, f < 3 %) and monotone residual response.

## Real-image calibration

```bash
python scripts/calibrate_yorkurban.py   # expects data/real/YorkUrbanDB (Elder Lab download)
```

Writes `outputs/yorkurban/{summary.csv,null_percentiles.json,ecdf.png,vp_accuracy.png}`.
Headline numbers are in `results/` and �7.7 of the plan.
