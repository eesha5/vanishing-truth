# Geometric-residual classifiers (no pixels)

## curated real (YorkUrban) vs SDXL  (n real = 102, n generated = 200)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.909 ± 0.024 | 0.910 ± 0.028 |
| decision tree | 0.785 ± 0.066 | 0.787 ± 0.058 |
| SVM (RBF) | 0.916 ± 0.032 | 0.921 ± 0.041 |
| random forest | 0.915 ± 0.037 | 0.927 ± 0.037 |
| naive Bayes | 0.870 ± 0.024 | 0.884 ± 0.023 |
| k-nearest neighbours | 0.895 ± 0.032 | 0.908 ± 0.035 |

Random-forest AUC from each feature group alone: **L2** 0.672, **L3** 0.906, **REGIONAL** 0.837, **LOCALITY** 0.517, **NUISANCE** 0.889

## curated real (YorkUrban) vs SD 1.5  (n real = 102, n generated = 200)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.916 ± 0.048 | 0.941 ± 0.036 |
| decision tree | 0.795 ± 0.055 | 0.836 ± 0.027 |
| SVM (RBF) | 0.916 ± 0.038 | 0.943 ± 0.030 |
| random forest | 0.913 ± 0.040 | 0.943 ± 0.034 |
| naive Bayes | 0.883 ± 0.039 | 0.902 ± 0.037 |
| k-nearest neighbours | 0.901 ± 0.043 | 0.928 ± 0.030 |

Random-forest AUC from each feature group alone: **L2** 0.795, **L3** 0.897, **REGIONAL** 0.762, **LOCALITY** 0.452, **NUISANCE** 0.895

## wild real (Commons) vs SDXL  (n real = 358, n generated = 200)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.807 ± 0.041 | 0.801 ± 0.058 |
| decision tree | 0.746 ± 0.041 | 0.765 ± 0.024 |
| SVM (RBF) | 0.821 ± 0.034 | 0.821 ± 0.040 |
| random forest | 0.824 ± 0.027 | 0.817 ± 0.026 |
| naive Bayes | 0.701 ± 0.037 | 0.716 ± 0.025 |
| k-nearest neighbours | 0.782 ± 0.037 | 0.778 ± 0.047 |

Random-forest AUC from each feature group alone: **L2** 0.742, **L3** 0.782, **REGIONAL** 0.714, **LOCALITY** 0.489, **NUISANCE** 0.694

## all real vs all generated  (n real = 460, n generated = 400)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.803 ± 0.029 | 0.804 ± 0.033 |
| decision tree | 0.724 ± 0.016 | 0.729 ± 0.023 |
| SVM (RBF) | 0.833 ± 0.027 | 0.835 ± 0.021 |
| random forest | 0.835 ± 0.045 | 0.836 ± 0.044 |
| naive Bayes | 0.716 ± 0.052 | 0.721 ± 0.050 |
| k-nearest neighbours | 0.788 ± 0.034 | 0.784 ± 0.030 |

Random-forest AUC from each feature group alone: **L2** 0.724, **L3** 0.752, **REGIONAL** 0.677, **LOCALITY** 0.494, **NUISANCE** 0.672

## HFOV 40-60, all real vs generated  (n real = 162, n generated = 92)

| classifier | AUC, geometry only | AUC, + camera/content features |
|---|---|---|
| logistic regression | 0.798 ± 0.045 | 0.789 ± 0.048 |
| decision tree | 0.682 ± 0.108 | 0.648 ± 0.095 |
| SVM (RBF) | 0.799 ± 0.065 | 0.789 ± 0.084 |
| random forest | 0.810 ± 0.078 | 0.796 ± 0.082 |
| naive Bayes | 0.700 ± 0.047 | 0.709 ± 0.059 |
| k-nearest neighbours | 0.746 ± 0.071 | 0.716 ± 0.073 |

Random-forest AUC from each feature group alone: **L2** 0.708, **L3** 0.758, **REGIONAL** 0.645, **LOCALITY** 0.538, **NUISANCE** 0.611

## Permutation importance (random forest, curated real vs SDXL)

| feature | drop in AUC when shuffled |
|---|---|
| orthocenter_offset | 0.034 |
| f_boot_cv | 0.016 |
| reg_logf_pairwise | 0.013 |
| f_spread | 0.007 |
| reg_radius_logf | 0.005 |
| n_negative_f2 | 0.005 |
| reg_rot_pairwise_deg | 0.004 |
| reg_rot_adjacent_deg | 0.004 |
| l2_rms_deg | 0.003 |
| vp_std_max_deg | 0.002 |
| ortho_err_max_boot_std | 0.001 |
| l2_capped_mean_deg | 0.001 |