### Atlanta focal consistency (selected images only)

| quantity | real (YorkUrban) | real-commons | sdxl_rich | sdxl_pilot |
|---|---|---|---|---|
| selected images | 72 | 121 | 112 | 79 |
| with >= 2 horizontal families | 72 | 120 | 109 | 74 |
| **log-f spread**, median [95% CI] | 0.142 [0.106, 0.221] | 0.152 [0.093, 0.220] | 0.355 [0.272, 0.529] | 0.593 [0.355, 0.933] |
| **images with an impossible (h,v) pair** | 28% [19%, 39%] (n=72) | 44% [36%, 53%] (n=120) | 58% [48%, 66%] (n=111) | 67% [56%, 76%] (n=79) |
| Manhattan orthogonality (secondary) | 0.65 [0.58, 0.84] | 2.82 [2.06, 4.02] | 1.94 [1.47, 2.28] | 1.75 [1.32, 2.63] |

**Mann-Whitney p for log-f spread:**

* vs real (YorkUrban): sdxl_rich: p = 5.63e-05; sdxl_pilot: p = 7.05e-05
* vs real-commons: sdxl_rich: p = 9.75e-05; sdxl_pilot: p = 0.000106