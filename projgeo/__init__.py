"""projgeo: projective-geometry consistency tests for AI-generated images.

Every image is treated as the claim "a single pinhole camera photographed
this scene".  Each constraint level (L1..L9 in the research plan) tests that
claim and returns an interpretable residual.
"""

from .lines import Segments, detect_lsd
from .vp import estimate_vps, angular_residuals
from .camera import l3_report, fit_focal, vp_rays
from .pipeline import analyze_segments, analyze_image

__all__ = [
    "Segments", "detect_lsd",
    "estimate_vps", "angular_residuals",
    "l3_report", "fit_focal", "vp_rays",
    "analyze_segments", "analyze_image",
]
