| metric | real (YorkUrban) | sdxl_pilot | MWU p (vs real) |
|---|---|---|---|
| L2 capped mean (deg) (higher = worse) | 1.314 [1.042, 1.726] | 1.225 [0.874, 1.804] | 0.11 |
| L2 unexplained fraction (higher = worse) | 0.169 [0.124, 0.221] | 0.146 [0.092, 0.228] | 0.11 |
| L3 ortho error max (deg) (higher = worse) | 0.694 [0.462, 1.318] | 4.359 [1.391, 47.761] | 1.5e-17 |
| L3 focal spread (higher = worse) | 0.097 [0.033, 0.208] | 0.409 [0.163, 0.605] | 5.2e-14 |
| Locality index (rho_near - rho_far) (higher = more local) | 0.163 [-0.022, 0.371] | 0.184 [0.037, 0.413] | 0.33 |
| Locality index, distortion-corrected (higher = more local) | 0.132 [-0.038, 0.391] | 0.173 [0.017, 0.388] | 0.36 |
| Fitted radial distortion k1 (nuisance) | 0.062 [0.025, 0.087] | 0.000 [-0.122, 0.094] | 7e-06 |
| # reliable VPs (lower = fewer coherent VPs) | 3.000 [3.000, 3.000] | 2.000 [2.000, 3.000] | 2.8e-10 |
| # LSD segments (content-match check) | 386.500 [336.250, 504.000] | 426.000 [287.000, 561.750] | 0.13 |
| l2_capped_mean_deg: exceedance | 5% above real p95 | 8% above real p95 | |
| ortho_err_max_deg: exceedance | 5% above real p95 | 22% above real p95 | |
| loc_index: exceedance | 5% above real p95 | 6% above real p95 | |