import numpy as np

from examples.brain import ce_brain_stage7_r2c_memory_trajectory as r2c


def test_config_grid_is_frozen_to_sixteen_candidates():
    assert len(r2c.CONFIGS) == 16
    assert len(set(r2c.CONFIGS)) == 16


def test_present_ca1_units_are_locked_before_scores():
    units, identities = r2c.load_units()
    assert len(units) == len(identities) == 75
    assert all(np.all(np.diff(spikes) >= 0) for spikes in units)


def test_replicated_decision_mapping_preserves_failure():
    encoding = {"median_absolute_error": 0.2, "improvement": 0.5}
    replay = {"coverage_stop": True}
    assert r2c.r1.decide(encoding, replay) == "TRAJECTORY_MEMORY_NOT_ESTABLISHED"
