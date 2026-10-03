# Demo app model: alternatives and shortcuts

625 images (191 real, 434 generated), 5-fold CV AUC, mean over fold seeds 0, 1, 2.

## Classifier, same 10 geometry features

| classifier | AUC |
|---|---|
| Random forest + calibration (the app) | 0.802 |
| Random forest, no calibration | 0.803 |
| Extra trees | 0.781 |
| Gradient boosting | 0.775 |
| Logistic regression | 0.772 |

## Image shape (width / height): a shortcut, not used

| input | AUC |
|---|---|
| shape alone | 0.615 |
| 10 features + shape | 0.846 |

## Each feature on its own (AUC, direction-free)

| feature | AUC |
|---|---|
| l2_rms_deg | 0.647 |
| l2_mean_deg | 0.629 |
| l2_capped_mean_deg | 0.554 |
| l2_unexplained_frac | 0.505 |
| vp_std_max_deg | 0.529 |
| ortho_err_max_deg | 0.590 |
| ortho_err_rms_deg | 0.589 |
| orthocenter_offset | 0.708 |
| atl_logf_spread | 0.669 |
| atl_frac_impossible | 0.628 |
