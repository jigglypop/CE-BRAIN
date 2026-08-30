from examples.brain import ce_brain_stage7_r2b_apparatus as apparatus


def test_r2b_apparatus_applies_locked_cluster_gate_without_opening_scores():
    result = apparatus.audit()
    assert result["decision"] == "STAGE7_R2B_APPARATUS_STOP"
    assert result["position_valid_fraction"] >= 0.90
    assert result["ca1_pyramidal_units"] == 84
    assert result["ca1_units_present"] == 75
    assert result["claim_ceiling"].endswith("scores unopened")
