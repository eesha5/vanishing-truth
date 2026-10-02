import numpy as np

from projgeo.appmodel import feature_matrix, rebase
from projgeo.explain import FEATURES


def test_rebase_is_identity_at_equal_priors():
    p = np.array([0.01, 0.3, 0.5, 0.9])
    assert np.allclose(rebase(p, 0.5), p, atol=1e-6)


def test_rebase_maps_training_prior_to_half():
    # a classifier that only knows the base rate outputs the base rate; at a
    # 50/50 prior that must read as 50 %
    assert abs(float(rebase(0.7, 0.7)) - 0.5) < 1e-9


def test_rebase_is_monotone_and_lowers_scores_when_training_was_mostly_positive():
    p = np.linspace(0.05, 0.95, 19)
    q = rebase(p, 0.7)
    assert np.all(np.diff(q) > 0)
    assert np.all(q < p)


def test_feature_matrix_order_and_missing():
    row = {k: float(i) for i, k in enumerate(FEATURES)}
    row["atl_logf_spread"] = None
    X = feature_matrix([row])
    assert X.shape == (1, len(FEATURES))
    assert np.isnan(X[0, FEATURES.index("atl_logf_spread")])
    assert X[0, 0] == 0.0
