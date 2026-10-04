### Atlanta focal consistency (selected images only)

| quantity | real (YorkUrban) | real-commons | sd15_rich | sdxl_rich | flux_rich |
|---|---|---|---|---|---|
| selected images | 72 | 121 | 92 | 112 | 194 |
| with >= 2 horizontal families | 72 | 120 | 87 | 109 | 194 |
| **log-f spread**, median [95% CI] | 0.142 [0.106, 0.221] | 0.152 [0.093, 0.220] | 0.465 [0.324, 0.709] | 0.355 [0.272, 0.529] | 0.179 [0.136, 0.299] |
| **images with an impossible (h,v) pair** | 28% [19%, 39%] (n=72) | 44% [36%, 53%] (n=120) | 68% [57%, 77%] (n=87) | 58% [48%, 66%] (n=111) | 48% [41%, 55%] (n=194) |
| Manhattan orthogonality (secondary) | 0.65 [0.58, 0.84] | 2.82 [2.06, 4.02] | 2.93 [2.72, 4.00] | 1.94 [1.47, 2.28] | 1.16 [0.97, 1.68] |

**Mann-Whitney p for log-f spread:**

* vs real (YorkUrban): sd15_rich: p = 3.49e-05; sdxl_rich: p = 5.63e-05; flux_rich: p = 0.18
* vs real-commons: sd15_rich: p = 2.62e-05; sdxl_rich: p = 9.75e-05; flux_rich: p = 0.16* flux_rich vs sd15_rich: p = 0.00173; vs sdxl_rich: p = 0.00353 (Flux has the lower spread)
