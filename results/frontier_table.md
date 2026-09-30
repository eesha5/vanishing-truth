### Atlanta focal consistency (selected images only)

| quantity | real (YorkUrban) | real-commons | sdxl_pilot | sd15_pilot | gemini | gptimage |
|---|---|---|---|---|---|---|
| selected images | 72 | 121 | 79 | 61 | 58 | 36 |
| with >= 2 horizontal families | 72 | 120 | 74 | 60 | 54 | 36 |
| **log-f spread**, median [95% CI] | 0.142 [0.106, 0.221] | 0.152 [0.093, 0.220] | 0.593 [0.355, 0.933] | 0.592 [0.381, 0.841] | 0.338 [0.182, 0.652] | 0.491 [0.320, 0.634] |
| **images with an impossible (h,v) pair** | 28% [19%, 39%] (n=72) | 44% [36%, 53%] (n=120) | 67% [56%, 76%] (n=79) | 55% [42%, 67%] (n=60) | 61% [48%, 73%] (n=57) | 39% [25%, 55%] (n=36) |
| Manhattan orthogonality (secondary) | 0.65 [0.58, 0.84] | 2.82 [2.06, 4.02] | 1.75 [1.32, 2.63] | 3.29 [2.26, 4.14] | 3.60 [1.89, 7.15] | 2.67 [1.78, 3.44] |

**Mann-Whitney p for log-f spread:**

* vs real (YorkUrban): sdxl_pilot: p = 7.05e-05; sd15_pilot: p = 2.78e-05; gemini: p = 0.0158; gptimage: p = 0.0144
* vs real-commons: sdxl_pilot: p = 0.000106; sd15_pilot: p = 2.22e-05; gemini: p = 0.0178; gptimage: p = 0.0147