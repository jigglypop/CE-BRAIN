import numpy as np

from examples.brain import ce_brain_stage7_r1_memory_trajectory as stage7


def test_detect_traversals_finds_both_directions():
    forward = np.linspace(0, 1, 100)
    reverse = np.linspace(1, 0, 100)
    position = np.r_[forward, reverse]
    rows = stage7.detect_traversals(position, np.ones(len(position), dtype=bool))
    assert {row["direction"] for row in rows} == {-1, 1}


def test_score_path_rewards_order_and_distance_structure():
    ordered = stage7.score_path(np.linspace(0, 1, 10))
    scrambled = stage7.score_path(np.array([0, 1, 0.2, 0.8, 0.4, 0.6, 0.3, 0.7, 0.1, 0.9]))
    assert ordered[0] > scrambled[0]
    assert ordered[1] > scrambled[1]


def test_decision_requires_encoding_and_both_nulls():
    encoding = {"median_absolute_error": 0.1, "improvement": 0.3}
    passed = {"difference": 0.2, "lower_95": 0.1, "median": 0.2}
    replay = {"coverage_stop": False, "comparisons": {"order_vs_time": passed, "order_vs_cell": passed, "distance_vs_time": passed, "distance_vs_cell": passed}, "double_significant_fraction": 0.2, "binomial_p": 0.001}
    assert stage7.decide(encoding, replay) == "DEVELOPMENT_MEMORY_TRAJECTORY_SUPPORTED"
    replay["comparisons"]["order_vs_cell"] = {"difference": 0.05, "lower_95": 0.01, "median": 0.05}
    assert stage7.decide(encoding, replay) == "ENCODING_TRAJECTORY_ONLY_REPLAY_NOT_ESTABLISHED"

