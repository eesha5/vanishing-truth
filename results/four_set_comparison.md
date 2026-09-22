### All images

| metric | real (YorkUrban) (n=102) | real-commons (n=358) | sd15_pilot (n=200) | sdxl_pilot (n=200) | MWU p (vs real) |
|---|---|---|---|---|---|
| L2 capped mean (deg) (higher = worse) | 1.314 [1.042, 1.726] | 1.887 [1.297, 2.735] | 1.475 [1.085, 2.133] | 1.225 [0.874, 1.804] | 9.1e-10, 0.053, 0.11 |
| L2 unexplained fraction (higher = worse) | 0.169 [0.124, 0.221] | 0.232 [0.148, 0.331] | 0.191 [0.127, 0.281] | 0.146 [0.092, 0.228] | 5.2e-07, 0.047, 0.11 |
| L3 ortho error max (deg) (higher = worse) | 0.694 [0.462, 1.318] | 12.207 [1.945, 69.796] | 10.410 [2.490, 78.388] | 4.359 [1.391, 47.761] | 5.3e-22, 7.5e-25, 1.5e-17 |
| L3 focal spread (higher = worse) | 0.097 [0.033, 0.208] | 0.174 [0.078, 0.464] | 0.257 [0.126, 0.529] | 0.409 [0.163, 0.605] | 3.9e-06, 1.6e-09, 5.2e-14 |
| Regional camera radius: rotation (deg) (higher = no global camera) | 5.799 [4.000, 8.469] | 7.202 [5.015, 9.471] | 6.938 [4.707, 9.547] | 7.179 [5.020, 8.965] | 0.0057, 0.018, 0.021 |
| Regional camera radius: |log f|  (higher = no global camera) | 0.317 [0.191, 0.534] | 0.402 [0.241, 0.802] | 0.516 [0.318, 0.864] | 0.891 [0.440, 1.720] | 0.009, 3.3e-05, 3.2e-14 |
| Adjacent-window frame rotation (deg) (higher = worse gluing) | 4.318 [2.803, 7.135] | 5.918 [3.527, 8.671] | 6.529 [4.052, 9.244] | 5.578 [3.518, 7.781] | 0.0034, 7.5e-05, 0.036 |
| Pairwise |log f_i/f_j| (median) (higher = worse) | 0.208 [0.120, 0.329] | 0.325 [0.184, 0.667] | 0.483 [0.294, 0.791] | 0.628 [0.391, 1.320] | 2.4e-05, 4.3e-12, 7.6e-21 |
|   ... same, consistent-twin noise floor (estimator noise) | 0.084 [0.045, 0.180] | 0.172 [0.069, 0.402] | 0.277 [0.097, 0.653] | 0.422 [0.189, 1.190] | 4.5e-06, 7.8e-10, 1.5e-18 |
|   ... excess over twin (higher = genuine inconsistency) | 0.115 [0.040, 0.199] | 0.123 [0.017, 0.295] | 0.189 [-0.002, 0.427] | 0.193 [-0.164, 0.536] | 0.54, 0.044, 0.15 |
| Focal radius, excess over twin (higher = genuine inconsistency) | 0.127 [-0.001, 0.275] | 0.114 [-0.038, 0.275] | 0.125 [-0.172, 0.338] | 0.118 [-0.174, 0.381] | 0.22, 0.28, 0.26 |
| Frame rotation, excess over twin (deg) (higher = genuine inconsistency) | 2.645 [0.975, 4.930] | 2.550 [0.503, 5.111] | 2.981 [1.006, 5.123] | 2.239 [0.479, 4.636] | 0.49, 0.63, 0.25 |
| # windows with a camera (coverage) | 7.000 [5.000, 8.000] | 6.000 [4.000, 7.000] | 5.000 [3.000, 7.000] | 6.000 [5.000, 8.000] | 6.5e-06, 3.2e-09, 0.0021 |
| Locality index (rho_near - rho_far) (higher = more local) | 0.163 [-0.022, 0.371] | 0.198 [0.001, 0.449] | 0.145 [0.012, 0.351] | 0.184 [0.037, 0.413] | 0.28, 0.97, 0.33 |
| Locality index, distortion-corrected (higher = more local) | 0.132 [-0.038, 0.391] | 0.189 [-0.004, 0.456] | 0.139 [-0.019, 0.343] | 0.173 [0.017, 0.388] | 0.17, 0.83, 0.36 |
| Fitted radial distortion k1 (nuisance) | 0.062 [0.025, 0.087] | 0.000 [-0.069, 0.044] | -0.019 [-0.159, 0.012] | 0.000 [-0.122, 0.094] | 8e-12, 1.6e-18, 7e-06 |
| # reliable VPs (lower = fewer coherent VPs) | 3.000 [3.000, 3.000] | 3.000 [2.000, 3.000] | 2.000 [1.000, 3.000] | 2.000 [2.000, 3.000] | 1.4e-08, 6.2e-10, 2.8e-10 |
| # LSD segments (content-match check) | 386.500 [336.250, 504.000] | 418.000 [325.500, 512.750] | 396.000 [292.000, 543.750] | 426.000 [287.000, 561.750] | 0.13, 0.5, 0.13 |
| Fitted HFOV (deg) (camera configuration) | 49.906 [48.451, 51.085] | 51.312 [26.601, 68.241] | 42.569 [15.438, 61.630] | 34.602 [14.962, 52.446] | 0.45, 0.082, 6.3e-08 |
| l2_capped_mean_deg: exceedance | 5% above real p95 | 30% above real p95 | 12% above real p95 | 8% above real p95 | |
| ortho_err_max_deg: exceedance | 5% above real p95 | 27% above real p95 | 31% above real p95 | 22% above real p95 | |
| reg_radius_rot_deg: exceedance | 5% above real p95 | 12% above real p95 | 13% above real p95 | 11% above real p95 | |
| reg_radius_logf: exceedance | 5% above real p95 | 10% above real p95 | 8% above real p95 | 30% above real p95 | |
| loc_index: exceedance | 5% above real p95 | 9% above real p95 | 4% above real p95 | 6% above real p95 | |

### Fitted HFOV in [40, 60] deg (matched camera configuration)

| metric | real (YorkUrban) (n=85) | real-commons (n=77) | sd15_pilot (n=50) | sdxl_pilot (n=42) | MWU p (vs real) |
|---|---|---|---|---|---|
| L2 capped mean (deg) (higher = worse) | 1.301 [1.036, 1.601] | 2.008 [1.331, 2.513] | 1.595 [1.318, 2.146] | 1.372 [1.047, 1.981] | 3.4e-08, 0.00019, 0.26 |
| L2 unexplained fraction (higher = worse) | 0.164 [0.120, 0.218] | 0.241 [0.161, 0.324] | 0.228 [0.165, 0.306] | 0.179 [0.130, 0.267] | 7.7e-06, 0.00011, 0.18 |
| L3 ortho error max (deg) (higher = worse) | 0.618 [0.403, 1.021] | 9.933 [2.008, 81.173] | 4.324 [1.750, 20.664] | 2.082 [0.969, 4.474] | 3.6e-19, 3.4e-15, 5.2e-09 |
| L3 focal spread (higher = worse) | 0.077 [0.030, 0.137] | 0.128 [0.069, 0.337] | 0.176 [0.069, 0.319] | 0.385 [0.212, 0.493] | 0.00021, 0.00022, 1.5e-10 |
| Regional camera radius: rotation (deg) (higher = no global camera) | 5.329 [3.788, 8.134] | 7.156 [4.951, 9.671] | 7.056 [5.489, 8.648] | 7.274 [5.813, 8.902] | 0.017, 0.031, 0.067 |
| Regional camera radius: |log f|  (higher = no global camera) | 0.295 [0.181, 0.518] | 0.418 [0.260, 0.716] | 0.433 [0.284, 0.682] | 0.645 [0.373, 1.233] | 0.0094, 0.0076, 7.9e-05 |
| Adjacent-window frame rotation (deg) (higher = worse gluing) | 4.085 [2.803, 6.302] | 5.576 [3.923, 7.912] | 5.967 [4.399, 7.715] | 4.718 [3.228, 6.720] | 0.02, 0.0031, 0.55 |
| Pairwise |log f_i/f_j| (median) (higher = worse) | 0.192 [0.119, 0.283] | 0.287 [0.199, 0.496] | 0.391 [0.233, 0.593] | 0.496 [0.281, 0.873] | 2e-05, 1.3e-06, 5.8e-08 |
|   ... same, consistent-twin noise floor (estimator noise) | 0.065 [0.039, 0.138] | 0.167 [0.070, 0.360] | 0.117 [0.059, 0.481] | 0.210 [0.093, 0.485] | 5.7e-06, 0.0013, 1.2e-05 |
|   ... excess over twin (higher = genuine inconsistency) | 0.112 [0.040, 0.187] | 0.128 [0.011, 0.295] | 0.182 [0.011, 0.424] | 0.180 [0.032, 0.455] | 0.38, 0.057, 0.039 |
| Focal radius, excess over twin (higher = genuine inconsistency) | 0.127 [0.002, 0.266] | 0.148 [-0.027, 0.390] | 0.189 [-0.031, 0.329] | 0.115 [-0.009, 0.479] | 0.88, 0.94, 0.93 |
| Frame rotation, excess over twin (deg) (higher = genuine inconsistency) | 2.645 [1.263, 4.862] | 2.337 [0.122, 4.439] | 3.756 [2.148, 5.195] | 2.550 [1.005, 5.320] | 0.3, 0.19, 0.79 |
| # windows with a camera (coverage) | 8.000 [6.000, 9.000] | 6.000 [5.000, 8.000] | 6.000 [4.250, 7.000] | 7.000 [6.000, 8.000] | 0.003, 0.00085, 0.038 |
| Locality index (rho_near - rho_far) (higher = more local) | 0.161 [-0.008, 0.364] | 0.213 [0.011, 0.481] | 0.085 [-0.003, 0.226] | 0.245 [0.082, 0.487] | 0.32, 0.37, 0.12 |
| Locality index, distortion-corrected (higher = more local) | 0.136 [-0.020, 0.371] | 0.150 [0.008, 0.442] | 0.092 [-0.007, 0.246] | 0.215 [0.082, 0.375] | 0.29, 0.32, 0.18 |
| Fitted radial distortion k1 (nuisance) | 0.062 [0.031, 0.081] | 0.000 [-0.038, 0.062] | -0.019 [-0.044, 0.025] | 0.025 [0.000, 0.075] | 6.3e-06, 3.6e-10, 0.018 |
| # reliable VPs (lower = fewer coherent VPs) | 3.000 [3.000, 3.000] | 3.000 [2.000, 3.000] | 3.000 [2.000, 3.000] | 3.000 [2.000, 3.000] | 2.8e-05, 0.001, 0.0022 |
| # LSD segments (content-match check) | 386.000 [329.000, 506.000] | 426.000 [291.000, 483.000] | 366.500 [309.000, 486.750] | 397.500 [288.750, 555.000] | 0.37, 0.69, 0.4 |
| Fitted HFOV (deg) (camera configuration) | 49.958 [48.933, 51.073] | 50.520 [46.011, 55.172] | 50.512 [49.035, 55.733] | 50.262 [46.600, 53.388] | 0.35, 0.051, 0.85 |
| l2_capped_mean_deg: exceedance | 5% above real p95 | 27% above real p95 | 20% above real p95 | 14% above real p95 | |
| ortho_err_max_deg: exceedance | 5% above real p95 | 78% above real p95 | 74% above real p95 | 55% above real p95 | |
| reg_radius_rot_deg: exceedance | 5% above real p95 | 5% above real p95 | 8% above real p95 | 5% above real p95 | |
| reg_radius_logf: exceedance | 5% above real p95 | 3% above real p95 | 4% above real p95 | 10% above real p95 | |
| loc_index: exceedance | 5% above real p95 | 5% above real p95 | 2% above real p95 | 7% above real p95 | |