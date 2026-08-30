import numpy as np

from examples.brain import ce_brain_stage7_xmaze_choice_code as choice


def test_logistic_model_learns_a_separable_signal():
    rng = np.random.default_rng(7)
    x = rng.normal(size=(120, 3))
    y = (x[:, 0] - 0.5 * x[:, 1] > 0).astype(int)
    weights = choice._logistic_fit(x, y, 0.1)
    probability = choice._predict(x, weights)
    assert choice._balanced_accuracy(y, probability) > 0.95
    assert choice._loss_rows(y, probability).mean() < 0.2


def test_real_sessions_return_only_preregistered_claim_classes():
    result = choice.run()
    allowed = {
        "APPARATUS_CONTRACT_MISMATCH_EXPLORATORY",
        "CHOICE_RELATED_TEMPORAL_CODE_CANDIDATE",
        "STATIC_CHOICE_CODE_CANDIDATE",
        "ALTERNATIVE_MEMORY_CODE_NOT_ESTABLISHED",
    }
    assert set(session["decision"] for session in result["sessions"].values()) <= allowed
    assert result["claim_ceiling"].endswith("correction claim")
