# One Camera or Not? Projective Geometry Consistency of AI-Generated Images

A real photograph is taken by one camera, so every part of it has to agree on a single focal
length and a single lens centre. AI image generators have no camera inside them. This project
measures whether an image's straight lines are consistent with one pinhole camera, and reports
*which* geometric rule fails and by how much, instead of a black-box "fake" score.

The package is called `projgeo`. It includes the measurement code, the experiment scripts that
produced every number in the report, and a Streamlit demo app that scores uploaded images.

## How it works

1. **Resize** the image to 640 px wide, so every image set is measured at the same resolution.
2. **Detect line segments** with LSD (Line Segment Detector, OpenCV).
3. **Find vanishing points** with sequential RANSAC. The estimator never assumes the directions
   are at right angles, so the right-angle test that comes later is a genuine test.
4. **Applicability rule.** The image must have enough lines in enough directions to be measured.
   Images that fail get "cannot measure" instead of a guess.
5. **Residuals.** The vertical direction is at right angles to every horizontal one, so pairing
   the vertical vanishing point with each horizontal one gives the focal length:

   ```
   f^2 = -(v1 - p) . (v2 - p)      p = principal point (image centre)
   ```

   In a real photo every pair gives the same f. The residuals are:

   | Residual | What it checks | Role |
   |---|---|---|
   | Atlanta log-focal spread | Do all (vertical, horizontal) pairs agree on one focal length? | primary |
   | Impossible pair | Does any pair give f^2 <= 0, which no real camera can produce? | primary |
   | Manhattan orthogonality | Are three detected directions mutually perpendicular? | secondary |
   | Orthocentre offset | How far is the implied lens centre from the image centre? | secondary |
   | L2 concurrency | Do the lines in one family actually meet at one point? | secondary |

6. **Compare with real photos** using bootstrap 95% confidence intervals on the median and
   Mann-Whitney tests. Comparisons are only made between images generated from the same prompt set.

## Main results

Atlanta log-focal spread (median with 95% CI; lower means more camera-consistent), on the
line-rich prompt set:

| Image set | Images measured | Log-focal spread | Images with an impossible pair |
|---|---|---|---|
| York Urban (real) | 72 | 0.142 [0.106, 0.221] | 28% |
| Wikimedia Commons (real) | 120 | 0.152 [0.093, 0.220] | 44% |
| Stable Diffusion 1.5 | 87 | 0.465 [0.324, 0.709] | 68% |
| SDXL | 109 | 0.355 [0.272, 0.529] | 58% |

Both local models differ from both real sets (Mann-Whitney p < 0.0001). On the first prompt set,
the frontier models also differ from real photos: Gemini 0.338 (p = 0.016, n = 54) and ChatGPT
0.491 (p = 0.014, n = 36). They do not differ significantly from the local models on that set.
The result holds when tilted cameras are excluded and when the vertical direction is required
to be far from the image centre (`scripts/vertical_guard_sensitivity.py`).

**Demo app score.** A calibrated random forest on the 10 geometry measurements only (it never
sees pixels): 5-fold cross-validated AUC 0.80. On a generator held out of training the AUC is
0.63 to 0.82. Full evaluation: [results/app_model_report.md](results/app_model_report.md).

**Limits.** This is a geometry check, not proof. It needs scenes with straight lines in three
directions (buildings, rooms, streets). Cropped or edited photos can look inconsistent, because
cropping moves the image centre. Some AI images pass the check.

## Quick start

Python 3.11 or newer.

```bash
pip install -e ".[app,dev]"
python -m pytest -q
```

Run the demo app:

```bash
python -m streamlit run app/streamlit_app.py
```

Then open http://localhost:8501. Upload one or more images, or pick a built-in example. The
built-in examples need the `data/` folder (see below). `http://localhost:8501/?examples=all`
opens with every example loaded. See [app/README.md](app/README.md) for a suggested demo order.

Analyse single images from the command line:

```bash
python scripts/analyze_image.py path/to/image.jpg --out outputs/
```

This writes a JSON report, an overlay PNG (segments coloured by vanishing point) and a
`summary.csv`.

## Data

The images are too large for the repository itself (about 1.3 GB). They are attached as zip
files to the **data-v1** release on this repository's Releases page. Unzip them in the project
root and they land in the right folders:

| Zip | Contents |
|---|---|
| `data-real-commons.zip` | 358 Wikimedia Commons photos with `metadata.jsonl` (author, licence, EXIF) |
| `data-generated-frontier.zip` | Gemini (181) and ChatGPT (51) images |
| `data-generated-local.zip` | Stable Diffusion 1.5 and SDXL sets, each with its generation log |

York Urban is not redistributed here; download it from the Elder Lab at York University and
place it in `data/real/YorkUrbanDB`. The prompt lists and per-set provenance files are tracked
in `data/generated/`.

| Set | Source | Folder |
|---|---|---|
| York Urban | Denis, Elder and Estrada, York Urban Line Segment Database (download from the Elder Lab) | `data/real/YorkUrbanDB` |
| Wikimedia Commons | `python scripts/collect_commons.py --per-query 60 --out data/real/commons` (keeps photos with EXIF camera and focal length; credits in `metadata.jsonl`) | `data/real/commons` |
| SD 1.5, SDXL | `python scripts/generate_sdxl.py --model sd15 --n 200 --out data/generated/sd15_pilot` (and `sdxl`) | `data/generated/*_pilot`, `*_rich` |
| Gemini, ChatGPT | Generated by hand from `data/generated/prompts.txt` (see each folder's `README.txt`) | `data/generated/gemini`, `gptimage` |

`prompts.txt` is the first prompt set; `prompts_rich.txt` is the line-rich set (250 prompts)
used for the primary result. Image `i` in a folder was made from prompt `i`.

## Reproducing the results

With the data in place:

```bash
python scripts/calibrate_yorkurban.py              # real-image baseline on York Urban
python scripts/atlanta_compare.py --real data/real/commons --gen data/generated/sdxl_rich data/generated/sd15_rich --out outputs/atlanta
python scripts/vertical_guard_sensitivity.py --out outputs/vguard
python scripts/classify_residuals.py --csv results/four_set_summary.csv
python scripts/train_app_model.py --refresh        # demo app model, about 20 minutes
python scripts/plot_dot_interval.py                # report figures from results/*.csv
python scripts/make_report_figures.py              # flowchart, example and montage figures
```

The report and slides are generated from code:

```bash
pip install -e ".[report]"
python docs/report/build_report.py
python docs/report/build_ppt.py
```

## Repository layout

```
projgeo/            the measurement library
  lines.py            LSD line detection
  vp.py               sequential RANSAC vanishing points
  selection.py        applicability rule ("can this image be measured?")
  camera.py           focal length, Atlanta and Manhattan residuals
  explain.py          the full per-image measurement used by the app and scripts
  appmodel.py         the demo app's calibrated classifier
  stats.py            bootstrap and Wilson confidence intervals
  synth.py            synthetic pinhole scenes for validation
  shadows.py          L7 shadow consistency (validated on synthetic data only)
  datasets/           York Urban and folder loaders
scripts/            experiments; each file's docstring gives its command line
app/                Streamlit demo app
models/             trained app model (app_model.joblib)
results/            committed tables, CSVs and figures used in the report
tests/              pytest suite (synthetic recovery, geometry, app model)
docs/               research plan, project notes, report and slide builders
data/generated/     prompt lists and provenance (images not tracked)
```

## Tests

```bash
python -m pytest -q
```

The synthetic tests build random pinhole scenes, check that vanishing points and focal length
are recovered (VPs within 0.5 degrees, f within 3%), and check that each residual grows when its
rule is deliberately broken.

## Team

CA-3 mini project, Computer Vision.

| Name | PRN | Contribution |
|---|---|---|
| | | |

## References

- J. Denis, J. H. Elder and F. Estrada, "Efficient edge-based methods for estimating Manhattan
  frames in urban imagery", ECCV 2008 (York Urban Database).
- R. Grompone von Gioi et al., "LSD: a fast line segment detector with a false detection
  control", IEEE TPAMI, 2010.
- G. Schindler and F. Dellaert, "Atlanta world: an expectation maximization framework for
  simultaneous low-level edge grouping and camera calibration in complex man-made environments",
  CVPR 2004.
- R. Hartley and A. Zisserman, *Multiple View Geometry in Computer Vision*, 2nd ed., Cambridge
  University Press, 2004.

The full reference list is in the report.

Wikimedia Commons photographs remain under their own licences. `collect_commons.py` records each
photo's author and licence in `data/real/commons/metadata.jsonl`; the photos shown in the report
are credited in `results/commons_montage_credited.txt`.
