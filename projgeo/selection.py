"""Applicability ("identifiability") test for the L3 camera experiment.

Plan 7.13-7.14: the three-VP camera test is only *defined* for scenes that
show three visible, well-separated, well-supported directions.  Applying it to
a curved street or a rectified facade produces a large residual that says
nothing about the camera, which is why wild photographs scored worse than
generated images.

The rule below decides whether an image admits the measurement **without
looking at the residual it would produce**.  Every criterion is about the
evidence available to the estimator, never about whether a single camera
explains it:

  * three VP families, each supported by at least `min_support_frac` of the
    total detected line length,
  * each family localised to better than `max_vp_std_deg` (bootstrap angular
    std in ray space) - so near-parallel, sliding VPs are excluded,
  * pairwise VP separation (as an angle between back-projected rays at a
    fixed probe focal length) of at least `min_separation_deg` *and* at least
    `separation_snr` times the two families' localisation error - so families
    that are really one, or whose VPs are not resolvably distinct, are
    excluded,
  * inliers of each family spread over at least `min_spatial_spread` of the
    image diagonal - so a family confined to one small object is excluded.

Orthogonality, focal length, the orthocentre and the VP-triangle shape are
deliberately *not* used: those are the measurement.
"""

from __future__ import annotations

import numpy as np

from .camera import vp_rays
from .geometry import unit
from .lines import Segments
from .vp import VPResult, bootstrap_vps


def identifiability(segs: Segments, vpr: VPResult, width: int, height: int,
                    min_support_frac: float = 0.08, max_vp_std_deg: float = 1.0,
                    min_separation_deg: float = 10.0, separation_snr: float = 5.0,
                    min_spatial_spread: float = 0.12,
                    n_boot: int = 20, f_probe: float | None = None) -> dict:
    """Is the three-VP camera measurement well posed for this image?

    `f_probe` is only used to turn VP positions into ray directions for the
    bootstrap spread; it is a fixed probe value (image diagonal by default),
    not a fitted focal length, so no measurement leaks into the decision.
    """
    diag = float(np.hypot(width, height))
    f_probe = f_probe or diag
    out: dict = {"n_vps": int(len(vpr.vps)), "identifiable": False, "reasons": []}
    if len(vpr.vps) < 3:
        out["reasons"].append("fewer than three VP families")
        return out

    total = float(max(segs.lengths.sum(), 1e-9))
    support = (vpr.support / total)[:3]
    out["support_frac"] = support.tolist()

    samples = bootstrap_vps(segs, vpr, B=n_boot)
    pp = np.array([width / 2.0, height / 2.0])
    stds = []
    for k in range(3):
        r0 = vp_rays(vpr.vps[k][None], f_probe, pp)[0]
        rk = vp_rays(samples[:, k], f_probe, pp)
        ang = np.degrees(np.arccos(np.clip(np.abs(rk @ r0), 0, 1)))
        stds.append(float(np.sqrt(np.mean(ang ** 2))))
    out["vp_std_deg"] = stds

    spreads = []
    for k in range(3):
        m = vpr.labels == k
        if m.sum() == 0:
            spreads.append(0.0)
            continue
        mid = segs.midpoints[m]
        spreads.append(float(np.max(np.linalg.norm(mid - mid.mean(axis=0), axis=1)) / diag))
    rays = vp_rays(vpr.vps[:3], f_probe, pp)
    seps, snr = [], []
    for i in range(3):
        for j in range(i + 1, 3):
            a = float(np.degrees(np.arccos(np.clip(abs(rays[i] @ rays[j]), 0, 1))))
            seps.append(a)
            snr.append(a / max(stds[i], stds[j], 1e-6))
    out["separation_deg"] = seps
    out["separation_snr"] = snr
    out["spatial_spread"] = spreads

    if min(support) < min_support_frac:
        out["reasons"].append(f"weakest family supports only {min(support):.1%} of line length")
    if max(stds) > max_vp_std_deg:
        out["reasons"].append(f"worst VP localised to {max(stds):.2f} deg")
    if min(seps) < min_separation_deg:
        out["reasons"].append(f"two VPs separated by only {min(seps):.1f} deg")
    if min(snr) < separation_snr:
        out["reasons"].append(f"VP separation only {min(snr):.1f}x its uncertainty")
    if min(spreads) < min_spatial_spread:
        out["reasons"].append(f"a family spans only {min(spreads):.2f} of the diagonal")
    out["identifiable"] = not out["reasons"]
    return out


def vpr_mean_direction(segs: Segments, mask: np.ndarray) -> np.ndarray:
    """Length-weighted mean undirected image direction of the masked segments."""
    d = segs.directions[mask]
    w = segs.lengths[mask]
    # undirected: align signs to the first segment before averaging
    d = d * np.sign(d @ d[0] + 1e-12)[:, None]
    return unit((w[:, None] * d).sum(axis=0))


STANDARD_ASPECTS = (3 / 2, 4 / 3, 16 / 9, 5 / 4, 1.0)


def looks_uncropped(width: int, height: int, tol: float = 0.02) -> bool:
    """True when the aspect ratio matches a standard sensor ratio.

    A cropped photograph usually has an arbitrary ratio, and cropping moves the
    principal point away from the image centre, which our centred-pp L3
    assumes.  This is a metadata criterion: it never looks at image content.
    """
    a = max(width, height) / max(min(width, height), 1)
    return bool(min(abs(a - s) for s in STANDARD_ASPECTS) <= tol)
