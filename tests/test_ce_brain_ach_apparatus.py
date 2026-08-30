from examples.brain import ce_brain_ach_apparatus as apparatus


def test_combined_file_has_ach_axon_and_behavior_but_no_write_endpoint():
    result = apparatus.audit()
    assert result["decision"] == "ACH_FAST_DYNAMICS_PRESENT_WRITE_GATE_NOT_IDENTIFIABLE"
    combined = result["files"]["simultaneous_axon_ach"]
    assert combined["has_ach"] is True
    assert combined["has_cholinergic_axon_gcamp"] is True
    assert combined["has_behavior_state"] is True
    assert combined["has_ephys"] is False
    assert combined["has_persistent_update_endpoint"] is False
    assert result["claim_ceiling"].endswith("claim")
