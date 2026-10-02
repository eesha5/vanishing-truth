"""Interval estimates shared by the analysis scripts.

Every interval in the report comes from these two functions, so each number
is computed one way everywhere (percentile bootstrap, 2000 resamples, seed 0;
Wilson for proportions).
"""

import numpy as np
from statsmodels.stats.proportion import proportion_confint


def boot_median_ci(x, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """Median of the finite values of `x` and its percentile-bootstrap 95 %
    interval, as (median, low, high).  All NaN when fewer than 3 values."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    meds = [np.median(rng.choice(x, len(x), replace=True)) for _ in range(n_boot)]
    return float(np.median(x)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def wilson_ci(successes: int, n: int) -> tuple[float, float]:
    """Wilson 95 % interval for a proportion, as (low, high) fractions."""
    lo, hi = proportion_confint(int(successes), int(n), method="wilson")
    return float(lo), float(hi)
