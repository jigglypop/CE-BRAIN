from examples.brain import ce_brain_chemistry_candidate_audit as candidate_audit


def test_no_candidate_contains_the_joint_direct_write_gate_axes():
    result = candidate_audit.audit()
    assert result["decision"] == "CHEMICAL_WRITE_GATE_NOT_IDENTIFIABLE_IN_AUDITED_CANDIDATES"
    assert result["eligible"] == []
    assert all(not item["direct_write_gate_identifiable"] for item in result["candidates"])


def test_modalities_in_one_dandiset_are_not_treated_as_simultaneous():
    result = candidate_audit.audit()
    by_id = {item["dandiset"]: item for item in result["candidates"]}
    candidate = by_id["001955@0.260828.0749"]
    assert candidate["ephys_assets"] == 34
    assert candidate["chemical_assets"] == 32
    assert candidate["joint_assets"] == 0
    assert candidate["overlapping_subjects"] == 0
