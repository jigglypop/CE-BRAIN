from examples.brain import ce_brain_human_memory_inventory as inventory


def test_subject_roles_are_deterministic_and_opened_subject_cannot_be_confirmation():
    assert inventory.role("P19HMH") == "development_opened"
    assert inventory.role("P16HMH") == "development"
    assert inventory.role("P17HMH") == "calibration"
    assert inventory.role("P23HMH") == "calibration"
    assert inventory.role("P16HMH") == inventory.role("P16HMH")
