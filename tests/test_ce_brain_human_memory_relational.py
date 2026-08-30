import numpy as np

from examples.brain import ce_brain_human_memory_relational as relational
from examples.brain import ce_brain_human_memory_apparatus as apparatus


def test_category_permutation_stays_within_category():
    categories = np.asarray(["a", "a", "b", "b", "b"])
    order = relational._category_permutation(categories, np.random.default_rng(3))
    assert np.array_equal(categories, categories[order])
    assert sorted(order.tolist()) == list(range(len(categories)))


def test_human_relational_analysis_has_bounded_claim():
    result = relational.analyze()
    assert result["decision"] in {
        "TEMPORAL_RELATIONAL_RETRIEVAL_DEVELOPMENT_CANDIDATE",
        "RELATIONAL_RETRIEVAL_DEVELOPMENT_CANDIDATE",
        "HUMAN_RELATIONAL_RETRIEVAL_NOT_ESTABLISHED",
    }
    assert result["old_pairs"] == 50
    assert result["remembered_pairs"] + result["forgotten_pairs"] == 50
    assert result["claim_ceiling"].endswith("confirmation")


def test_p16_fixed_replication_does_not_open_confirmation_gate():
    result = relational.analyze(apparatus.P16_FILE, apparatus.P16_SHA256)
    assert result["decision"] == "HUMAN_RELATIONAL_RETRIEVAL_NOT_ESTABLISHED"
    assert result["old_pairs"] == 50
    assert result["eligible_units"] == 21
