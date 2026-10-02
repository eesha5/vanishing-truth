# Geometric-residual classifiers (no pixels)

Images: all. Excluded as assumption-dependent: f_spread, f_boot_cv, n_negative_f2, all reg_* columns.

## curated real (YorkUrban) vs SDXL  (n real = 102, n generated = 200)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.779 ± 0.077 | 0.841 ± 0.061 |
| decision tree | 0.777 ± 0.056 | 0.799 ± 0.049 |
| SVM (RBF) | 0.788 ± 0.028 | 0.843 ± 0.032 |
| random forest | 0.875 ± 0.038 | 0.908 ± 0.040 |
| naive Bayes | 0.747 ± 0.049 | 0.814 ± 0.018 |
| k-nearest neighbours | 0.741 ± 0.053 | 0.821 ± 0.035 |

Random-forest AUC from each feature group alone: **L2** 0.796, **ATLANTA** 0.691, **MANHATTAN** 0.841, **LOCALITY** 0.517, **NUISANCE** 0.883

## curated real (YorkUrban) vs SD 1.5  (n real = 102, n generated = 200)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.863 ± 0.070 | 0.915 ± 0.053 |
| decision tree | 0.813 ± 0.088 | 0.855 ± 0.042 |
| SVM (RBF) | 0.865 ± 0.055 | 0.929 ± 0.038 |
| random forest | 0.919 ± 0.041 | 0.946 ± 0.033 |
| naive Bayes | 0.817 ± 0.040 | 0.886 ± 0.033 |
| k-nearest neighbours | 0.816 ± 0.041 | 0.896 ± 0.053 |

Random-forest AUC from each feature group alone: **L2** 0.863, **ATLANTA** 0.735, **MANHATTAN** 0.875, **LOCALITY** 0.452, **NUISANCE** 0.902

## wild real (Commons) vs SDXL  (n real = 358, n generated = 200)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.780 ± 0.026 | 0.775 ± 0.037 |
| decision tree | 0.705 ± 0.030 | 0.737 ± 0.038 |
| SVM (RBF) | 0.781 ± 0.039 | 0.779 ± 0.034 |
| random forest | 0.807 ± 0.022 | 0.811 ± 0.011 |
| naive Bayes | 0.660 ± 0.054 | 0.687 ± 0.050 |
| k-nearest neighbours | 0.717 ± 0.051 | 0.732 ± 0.052 |

Random-forest AUC from each feature group alone: **L2** 0.753, **ATLANTA** 0.576, **MANHATTAN** 0.732, **LOCALITY** 0.489, **NUISANCE** 0.707

## all real vs all generated  (n real = 460, n generated = 400)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.752 ± 0.020 | 0.770 ± 0.015 |
| decision tree | 0.696 ± 0.043 | 0.696 ± 0.033 |
| SVM (RBF) | 0.774 ± 0.027 | 0.783 ± 0.016 |
| random forest | 0.804 ± 0.023 | 0.806 ± 0.027 |
| naive Bayes | 0.637 ± 0.037 | 0.683 ± 0.057 |
| k-nearest neighbours | 0.720 ± 0.032 | 0.729 ± 0.028 |

Random-forest AUC from each feature group alone: **L2** 0.758, **ATLANTA** 0.602, **MANHATTAN** 0.687, **LOCALITY** 0.494, **NUISANCE** 0.677

## HFOV 40-60, all real vs generated  (n real = 162, n generated = 92)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.768 ± 0.066 | 0.756 ± 0.067 |
| decision tree | 0.716 ± 0.009 | 0.716 ± 0.024 |
| SVM (RBF) | 0.783 ± 0.028 | 0.749 ± 0.041 |
| random forest | 0.814 ± 0.027 | 0.798 ± 0.038 |
| naive Bayes | 0.640 ± 0.055 | 0.675 ± 0.043 |
| k-nearest neighbours | 0.742 ± 0.078 | 0.689 ± 0.045 |

Random-forest AUC from each feature group alone: **L2** 0.743, **ATLANTA** 0.627, **MANHATTAN** 0.701, **LOCALITY** 0.538, **NUISANCE** 0.618

## Permutation importance (random forest, curated real vs SDXL)

| feature | drop in AUC when shuffled |
|---|---|
| orthocenter_offset | 0.114 |
| l2_capped_mean_deg | 0.010 |
| l2_rms_deg | 0.008 |
| l2_unexplained_frac | 0.008 |
| loc_index_undist | 0.006 |
| loc_rho_near | 0.005 |
| atl_logf_spread | 0.005 |
| n_outliers | 0.004 |
| loc_index | 0.003 |
| vp_std_max_deg | 0.003 |
| atl_frac_impossible | 0.003 |
| ortho_err_rms_deg | 0.003 |