import numpy as np

from research import c6_1_reactivation as c6


def test_explained_variance_follows_history_direction():
    rng = np.random.default_rng(0)
    pre = rng.normal(0, 1, 2000)
    run = 0.3 * pre + rng.normal(0, 1, 2000)
    post = 0.5 * pre + 0.6 * run + rng.normal(0, 1, 2000)  # POST carries RUN beyond PRE
    r = c6.explained(run, pre, post)
    assert r["ev"] > 0.1 and r["rev"] < 0.02
    back = c6.explained(run, post, pre)  # time reversed: roles swap
    assert back["rev"] > 0.1 and back["ev"] < 0.02
