from examples.brain import ce_brain_update_task_r2_inventory as inventory


def test_eligibility_requires_both_trial_types_and_both_regions():
    passing = {"switch": 30, "stay": 10, "CA1": 20, "PFC": 20}
    assert inventory.eligible(passing) is True
    for key in passing:
        failing = dict(passing)
        failing[key] -= 1
        assert inventory.eligible(failing) is False


def test_missing_region_metadata_cannot_pass():
    assert inventory.eligible({"switch": 99, "stay": 99, "CA1": 0, "PFC": 0}) is False
