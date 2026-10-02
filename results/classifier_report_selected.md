# Geometric-residual classifiers (no pixels)

Images: selected only (pass the applicability rule). Excluded as assumption-dependent: f_spread, f_boot_cv, n_negative_f2, all reg_* columns.

## curated real (YorkUrban) vs SDXL  (n real = 72, n generated = 79)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.842 ± 0.030 | 0.846 ± 0.038 |
| decision tree | 0.803 ± 0.055 | 0.805 ± 0.079 |
| SVM (RBF) | 0.832 ± 0.049 | 0.854 ± 0.049 |
| random forest | 0.903 ± 0.030 | 0.936 ± 0.022 |
| naive Bayes | 0.778 ± 0.077 | 0.815 ± 0.061 |
| k-nearest neighbours | 0.826 ± 0.033 | 0.817 ± 0.033 |

Random-forest AUC from each feature group alone: **L2** 0.794, **ATLANTA** 0.735, **MANHATTAN** 0.882, **LOCALITY** 0.512, **NUISANCE** 0.905

## curated real (YorkUrban) vs SD 1.5  (n real = 72, n generated = 61)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.888 ± 0.060 | 0.915 ± 0.032 |
| decision tree | 0.739 ± 0.120 | 0.827 ± 0.067 |
| SVM (RBF) | 0.875 ± 0.046 | 0.922 ± 0.026 |
| random forest | 0.926 ± 0.056 | 0.967 ± 0.025 |
| naive Bayes | 0.791 ± 0.087 | 0.822 ± 0.081 |
| k-nearest neighbours | 0.862 ± 0.040 | 0.891 ± 0.027 |

Random-forest AUC from each feature group alone: **L2** 0.872, **ATLANTA** 0.713, **MANHATTAN** 0.852, **LOCALITY** 0.508, **NUISANCE** 0.931

## wild real (Commons) vs SDXL  (n real = 121, n generated = 79)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.764 ± 0.072 | 0.811 ± 0.077 |
| decision tree | 0.674 ± 0.110 | 0.685 ± 0.078 |
| SVM (RBF) | 0.804 ± 0.056 | 0.762 ± 0.067 |
| random forest | 0.808 ± 0.087 | 0.791 ± 0.093 |
| naive Bayes | 0.622 ± 0.093 | 0.661 ± 0.093 |
| k-nearest neighbours | 0.743 ± 0.057 | 0.750 ± 0.064 |

Random-forest AUC from each feature group alone: **L2** 0.744, **ATLANTA** 0.614, **MANHATTAN** 0.765, **LOCALITY** 0.488, **NUISANCE** 0.654

## all real vs all generated  (n real = 193, n generated = 140)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.801 ± 0.053 | 0.826 ± 0.067 |
| decision tree | 0.709 ± 0.036 | 0.712 ± 0.033 |
| SVM (RBF) | 0.811 ± 0.035 | 0.810 ± 0.038 |
| random forest | 0.833 ± 0.024 | 0.826 ± 0.026 |
| naive Bayes | 0.704 ± 0.027 | 0.728 ± 0.057 |
| k-nearest neighbours | 0.760 ± 0.059 | 0.749 ± 0.065 |

Random-forest AUC from each feature group alone: **L2** 0.762, **ATLANTA** 0.633, **MANHATTAN** 0.714, **LOCALITY** 0.524, **NUISANCE** 0.695

## HFOV 40-60, all real vs generated  (n real = 91, n generated = 47)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.832 ± 0.077 | 0.799 ± 0.041 |
| decision tree | 0.594 ± 0.072 | 0.645 ± 0.091 |
| SVM (RBF) | 0.810 ± 0.055 | 0.808 ± 0.055 |
| random forest | 0.863 ± 0.073 | 0.835 ± 0.054 |
| naive Bayes | 0.686 ± 0.085 | 0.659 ± 0.048 |
| k-nearest neighbours | 0.785 ± 0.045 | 0.768 ± 0.067 |

Random-forest AUC from each feature group alone: **L2** 0.723, **ATLANTA** 0.691, **MANHATTAN** 0.752, **LOCALITY** 0.531, **NUISANCE** 0.711

## Permutation importance (random forest, curated real vs SDXL)

| feature | drop in AUC when shuffled |
|---|---|
| orthocenter_offset | 0.062 |
| vp_std_max_deg | 0.022 |
| ortho_err_max_deg | 0.004 |
| atl_logf_spread | 0.003 |
| ortho_err_rms_deg | 0.002 |
| atl_frac_impossible | 0.002 |
| n_outliers | 0.002 |
| l2_unexplained_frac | 0.001 |
| l2_capped_mean_deg | 0.001 |
| l2_rms_deg | 0.000 |
| loc_rho_near | 0.000 |
| ortho_err_max_boot_std | -0.000 |