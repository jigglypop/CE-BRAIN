import numpy as np

from examples.brain import ce_brain_update_task_poisson_r2 as poisson


def test_poisson_log_odds_tracks_the_higher_rate_choice():
    rates = np.array([[1.0, 5.0], [5.0, 1.0]])
    counts = np.array([[5.0, 1.0], [1.0, 5.0]])
    odds = poisson._log_odds(counts, np.ones(2), rates)
    assert odds[0] > 0
    assert odds[1] < 0


def test_did_is_switch_minus_stay():
    assert poisson._did(np.array([3.0, 1.0, 0.5, -0.5]), np.array([2, 2, 3, 3])) == 2.0
