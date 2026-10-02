# Demo app model: evaluation

Images that pass the applicability rule: 625 of 1592 (191 real, 434 generated, after holding out 6 demo examples; training share generated = 0.69, re-based to 0.50 for display).
Features (10, geometry only): l2_rms_deg, l2_mean_deg, l2_capped_mean_deg, l2_unexplained_frac, vp_std_max_deg, ortho_err_max_deg, ortho_err_rms_deg, orthocenter_offset, atl_logf_spread, atl_frac_impossible.

## 5-fold cross-validation

* AUC 0.796
* Brier score 0.156 (at the training prior)
* At the 50 % line after re-basing: 78% of generated images called generated, 71% of real photos called real

| shown score (50/50 prior) | images | share actually generated, re-weighted to 50/50 |
|---|---|---|
| 0% to 20% | 90 | 11% |
| 20% to 40% | 80 | 32% |
| 40% to 60% | 128 | 49% |
| 60% to 80% | 242 | 74% |
| 80% to 100% | 85 | 79% |

## Real photographs vs each generator (same CV predictions)

| generator | AUC | images |
|---|---|---|
| ChatGPT | 0.592 | 35 |
| Gemini | 0.756 | 56 |
| SD 1.5 | 0.838 | 152 |
| SDXL | 0.812 | 191 |

## Leave one generator out (never seen in training)

| held-out generator | AUC vs real photos | images |
|---|---|---|
| ChatGPT | 0.627 | 35 |
| Gemini | 0.766 | 56 |
| SD 1.5 | 0.822 | 152 |
| SDXL | 0.771 | 191 |