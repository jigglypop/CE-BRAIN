from examples.brain import ce_brain_human_memory_relational_r2 as r2


def test_r2_uses_official_memory_signal_window():
    assert r2.BIN_EDGES.tolist() == [0.2, 0.45, 0.7, 0.95, 1.2, 1.45, 1.7]


def test_r2_new_subjects_keep_calibration_sealed():
    result = r2.analyze()
    assert result["decision"] in {
        "HUMAN_RELATIONAL_RETRIEVAL_R2_REPLICATED_DEVELOPMENT_CANDIDATE",
        "HUMAN_RELATIONAL_RETRIEVAL_R2_NOT_ESTABLISHED_REPLICATED",
    }
    assert set(result["sessions"]) == {"P11HMH", "P48CS"}
    assert result["claim_ceiling"].endswith("sealed")
