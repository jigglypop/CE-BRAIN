from examples.brain import ce_brain_update_task_apparatus as apparatus


def test_subject_split_is_hash_determined_and_sealed():
    assert apparatus.subject_split() == {
        "development": ["S34", "S29", "S20", "S25"],
        "calibration": ["S17"],
        "confirmation": ["S33", "S28"],
    }


def test_two_development_sessions_pass_the_rapid_correction_apparatus_gate():
    result = apparatus.audit()
    assert result["decision"] == "UPDATE_TASK_RAPID_CORRECTION_APPARATUS_ELIGIBLE"
    assert result["eligible_development"] == ["S34-220623", "S25-210916"]
    assert result["sessions"]["S29-211123"]["eligible"] is False
    assert result["sessions"]["S20-210521"]["eligible"] is False
    assert result["claim_ceiling"].startswith("within-trial")
