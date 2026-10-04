# Demo app model: alternatives and shortcuts

819 images (191 real, 628 generated), 5-fold CV AUC, mean over fold seeds 0, 1, 2.

## Classifier, same 10 geometry features

| classifier | AUC |
|---|---|
| Random forest + calibration (the app) | 0.768 |
| Random forest, no calibration | 0.770 |
| Extra trees | 0.751 |
| Gradient boosting | 0.742 |
| Logistic regression | 0.740 |

## Image shape (width / height): a shortcut, not used

| input | AUC |
|---|---|
| shape alone | 0.612 |
| 10 features + shape | 0.818 |

## Each feature on its own (AUC, direction-free)

| feature | AUC |
|---|---|
| l2_rms_deg | 0.627 |
| l2_mean_deg | 0.613 |
| l2_capped_mean_deg | 0.562 |
| l2_unexplained_frac | 0.525 |
| vp_std_max_deg | 0.542 |
| ortho_err_max_deg | 0.555 |
| ortho_err_rms_deg | 0.555 |
| orthocenter_offset | 0.652 |
| atl_logf_spread | 0.631 |
| atl_frac_impossible | 0.596 |
