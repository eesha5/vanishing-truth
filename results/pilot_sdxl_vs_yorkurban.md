| metric | real (YorkUrban) | sdxl_pilot | MWU p (vs real) |
|---|---|---|---|
| L2 capped mean (deg) (higher = worse) | 1.314 [1.042, 1.726] | 1.225 [0.874, 1.804] | 0.11 |
| L2 unexplained fraction (higher = worse) | 0.169 [0.124, 0.221] | 0.146 [0.092, 0.228] | 0.11 |
| L3 ortho error max (deg) (higher = worse) | 0.694 [0.462, 1.318] | 4.359 [1.391, 47.761] | 1.5e-17 |
| L3 focal spread (higher = worse) | 0.097 [0.033, 0.208] | 0.409 [0.163, 0.605] | 5.2e-14 |
| Regional camera radius: rotation (deg) (higher = no global camera) | 5.799 [4.000, 8.469] | 7.179 [5.020, 8.965] | 0.021 |
| Regional camera radius: |log f|  (higher = no global camera) | 0.317 [0.191, 0.534] | 0.891 [0.440, 1.720] | 3.2e-14 |
| Adjacent-window frame rotation (deg) (higher = worse gluing) | 4.318 [2.803, 7.135] | 5.578 [3.518, 7.781] | 0.036 |
| Pairwise |log f_i/f_j| (median) (higher = worse) | 0.208 [0.120, 0.329] | 0.628 [0.391, 1.320] | 7.6e-21 |
| # windows with a camera (coverage) | 7.000 [5.000, 8.000] | 6.000 [5.000, 8.000] | 0.0021 |
| Locality index (rho_near - rho_far) (higher = more local) | 0.163 [-0.022, 0.371] | 0.184 [0.037, 0.413] | 0.33 |
| Locality index, distortion-corrected (higher = more local) | 0.132 [-0.038, 0.391] | 0.173 [0.017, 0.388] | 0.36 |
| Fitted radial distortion k1 (nuisance) | 0.062 [0.025, 0.087] | 0.000 [-0.122, 0.094] | 7e-06 |
| # reliable VPs (lower = fewer coherent VPs) | 3.000 [3.000, 3.000] | 2.000 [2.000, 3.000] | 2.8e-10 |
| # LSD segments (content-match check) | 386.500 [336.250, 504.000] | 426.000 [287.000, 561.750] | 0.13 |
| l2_capped_mean_deg: exceedance | 5% above real p95 | 8% above real p95 | |
| ortho_err_max_deg: exceedance | 5% above real p95 | 22% above real p95 | |
| reg_radius_rot_deg: exceedance | 5% above real p95 | 11% above real p95 | |
| reg_radius_logf: exceedance | 5% above real p95 | 30% above real p95 | |
| loc_index: exceedance | 5% above real p95 | 6% above real p95 | |