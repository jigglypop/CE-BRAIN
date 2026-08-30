import numpy as np

from examples.brain import ce_brain_human_memory_positive_control as control


def test_category_permutations_preserve_visual_categories():
    categories = np.asarray(["a", "a", "b", "b", "b"])
    orders = control._category_permutations(categories, np.random.default_rng(9))
    assert orders.shape == (control.PERMUTATIONS, len(categories))
    for order in orders[:10]:
        assert np.array_equal(categories, categories[order])


def test_positive_control_reports_only_sensitivity_status():
    result = control.analyze()
    assert result["decision"] in {
        "KNOWN_MEMORY_SIGNAL_DETECTED",
        "MEMORY_POSITIVE_CONTROL_ENROLLMENT_CONTINUES",
        "MEMORY_APPARATUS_SENSITIVITY_NOT_ESTABLISHED",
    }
    assert result["subjects"] >= 8
    assert result["claim_ceiling"].endswith("evidence")


def test_official_method_is_kept_as_outcome_known_diagnostic():
    result = control.official_method_diagnostic()
    assert result["status"] == "OUTCOME_KNOWN_OFFICIAL_METHOD_DIAGNOSTIC"
    assert result["cannot_replace_preregistered_decision"] is True
    assert result["units"] >= result["selective_units"]
