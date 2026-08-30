import numpy as np

from examples.brain import ce_brain_stage7_xmaze_apparatus as apparatus


def test_endpoint_extractor_keeps_cross_side_order():
    rate = 10.0
    points = []
    for corner in ((1, 0), (0, 1), (1, 1), (0, 0)):
        points.extend([corner] * 5)
        points.extend([(0.5, 0.5)] * 12)
    position = np.asarray(points, dtype=float)
    visits = apparatus.endpoint_visits(position, rate)
    transitions = apparatus.cross_maze_transitions(visits, rate)
    assert [visit["endpoint"] for visit in visits] == [2, 1, 3, 0]
    assert [item["direction"] for item in transitions] == ["east_to_west", "west_to_east", "east_to_west"]


def test_real_xmaze_files_pass_behavior_only_gate_without_trial_semantics():
    result = apparatus.audit()
    assert result["decision"] == "STAGE7_XMAZE_BEHAVIOR_APPARATUS_ELIGIBLE"
    for session in result["sessions"].values():
        assert session["trial_semantics"] == "absent"
        assert min(session["cross_maze_transition_counts"].values()) >= 40
    assert result["claim_ceiling"].endswith("unit spike times unopened")
