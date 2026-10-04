# Demo app model: evaluation

Images that pass the applicability rule: 819 of 1842 (191 real, 628 generated, after holding out 6 demo examples; training share generated = 0.77, re-based to 0.50 for display).
Features (10, geometry only): l2_rms_deg, l2_mean_deg, l2_capped_mean_deg, l2_unexplained_frac, vp_std_max_deg, ortho_err_max_deg, ortho_err_rms_deg, orthocenter_offset, atl_logf_spread, atl_frac_impossible.

## 5-fold cross-validation

* AUC 0.768
* Brier score 0.144 (at the training prior)
* At the 50 % line after re-basing: 78% of generated images called generated, 62% of real photos called real

| shown score (50/50 prior) | images | share actually generated, re-weighted to 50/50 |
|---|---|---|
| 0% to 20% | 47 | 8% |
| 20% to 40% | 117 | 25% |
| 40% to 60% | 277 | 51% |
| 60% to 80% | 377 | 74% |
| 80% to 100% | 1 | 100% |

## Real photographs vs each generator (same CV predictions)

| generator | AUC | images |
|---|---|---|
| ChatGPT | 0.615 | 35 |
| Flux | 0.730 | 194 |
| Gemini | 0.738 | 56 |
| SD 1.5 | 0.829 | 152 |
| SDXL | 0.795 | 191 |

## Leave one generator out (never seen in training)

| held-out generator | AUC vs real photos | images |
|---|---|---|
| ChatGPT | 0.628 | 35 |
| Flux | 0.635 | 194 |
| Gemini | 0.734 | 56 |
| SD 1.5 | 0.809 | 152 |
| SDXL | 0.762 | 191 |