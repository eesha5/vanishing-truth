| metric | real (YorkUrban) | sd15_pilot | sdxl_pilot | MWU p (vs real) |
|---|---|---|---|---|
| L2 capped mean (deg) (higher = worse) | 1.314 [1.042, 1.726] | 1.475 [1.085, 2.133] | 1.225 [0.874, 1.804] | 0.053, 0.11 |
| L2 unexplained fraction (higher = worse) | 0.169 [0.124, 0.221] | 0.191 [0.127, 0.281] | 0.146 [0.092, 0.228] | 0.047, 0.11 |
| L3 ortho error max (deg) (higher = worse) | 0.694 [0.462, 1.318] | 10.410 [2.490, 78.388] | 4.359 [1.391, 47.761] | 7.5e-25, 1.5e-17 |
| L3 focal spread (higher = worse) | 0.097 [0.033, 0.208] | 0.257 [0.126, 0.529] | 0.409 [0.163, 0.605] | 1.6e-09, 5.2e-14 |
| Regional camera radius: rotation (deg) (higher = no global camera) | 5.799 [4.000, 8.469] | 6.938 [4.707, 9.547] | 7.179 [5.020, 8.965] | 0.018, 0.021 |
| Regional camera radius: |log f|  (higher = no global camera) | 0.317 [0.191, 0.534] | 0.516 [0.318, 0.864] | 0.891 [0.440, 1.720] | 3.3e-05, 3.2e-14 |
| Adjacent-window frame rotation (deg) (higher = worse gluing) | 4.318 [2.803, 7.135] | 6.529 [4.052, 9.244] | 5.578 [3.518, 7.781] | 7.5e-05, 0.036 |
| Pairwise |log f_i/f_j| (median) (higher = worse) | 0.208 [0.120, 0.329] | 0.483 [0.294, 0.791] | 0.628 [0.391, 1.320] | 4.3e-12, 7.6e-21 |
|   ... same, consistent-twin noise floor (estimator noise) | 0.084 [0.045, 0.180] | 0.277 [0.097, 0.653] | 0.422 [0.189, 1.190] | 7.8e-10, 1.5e-18 |
|   ... excess over twin (higher = genuine inconsistency) | 0.115 [0.040, 0.199] | 0.189 [-0.002, 0.427] | 0.193 [-0.164, 0.536] | 0.044, 0.15 |
| Focal radius, excess over twin (higher = genuine inconsistency) | 0.127 [-0.001, 0.275] | 0.125 [-0.172, 0.338] | 0.118 [-0.174, 0.381] | 0.28, 0.26 |
| Frame rotation, excess over twin (deg) (higher = genuine inconsistency) | 2.645 [0.975, 4.930] | 2.981 [1.006, 5.123] | 2.239 [0.479, 4.636] | 0.63, 0.25 |
| # windows with a camera (coverage) | 7.000 [5.000, 8.000] | 5.000 [3.000, 7.000] | 6.000 [5.000, 8.000] | 3.2e-09, 0.0021 |
| Locality index (rho_near - rho_far) (higher = more local) | 0.163 [-0.022, 0.371] | 0.145 [0.012, 0.351] | 0.184 [0.037, 0.413] | 0.97, 0.33 |
| Locality index, distortion-corrected (higher = more local) | 0.132 [-0.038, 0.391] | 0.139 [-0.019, 0.343] | 0.173 [0.017, 0.388] | 0.83, 0.36 |
| Fitted radial distortion k1 (nuisance) | 0.062 [0.025, 0.087] | -0.019 [-0.159, 0.012] | 0.000 [-0.122, 0.094] | 1.6e-18, 7e-06 |
| # reliable VPs (lower = fewer coherent VPs) | 3.000 [3.000, 3.000] | 2.000 [1.000, 3.000] | 2.000 [2.000, 3.000] | 6.2e-10, 2.8e-10 |
| # LSD segments (content-match check) | 386.500 [336.250, 504.000] | 396.000 [292.000, 543.750] | 426.000 [287.000, 561.750] | 0.5, 0.13 |
| l2_capped_mean_deg: exceedance | 5% above real p95 | 12% above real p95 | 8% above real p95 | |
| ortho_err_max_deg: exceedance | 5% above real p95 | 31% above real p95 | 22% above real p95 | |
| reg_radius_rot_deg: exceedance | 5% above real p95 | 13% above real p95 | 11% above real p95 | |
| reg_radius_logf: exceedance | 5% above real p95 | 8% above real p95 | 30% above real p95 | |
| loc_index: exceedance | 5% above real p95 | 4% above real p95 | 6% above real p95 | |