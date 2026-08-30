from examples.brain import ce_brain_human_memory_apparatus as apparatus


def test_human_memory_file_has_exact_encoding_recognition_identity_without_neural_scores():
    result = apparatus.audit()
    assert result["decision"] == "HUMAN_MEMORY_RELATIONAL_APPARATUS_ELIGIBLE"
    assert result["learning_trials"] == 100
    assert result["exact_image_old_trials"] == 50
    assert result["exact_image_new_trials"] == 50
    assert result["metadata_label_zero_exact_old"] == 0
    assert result["metadata_label_one_exact_old"] == 50
    assert result["claim_ceiling"].endswith("confirmation")


def test_unopened_p16_replication_file_passes_the_same_apparatus_gate():
    result = apparatus.audit_file(apparatus.P16_FILE, apparatus.P16_SHA256)
    assert result["decision"] == "HUMAN_MEMORY_RELATIONAL_APPARATUS_ELIGIBLE"
    assert result["learning_trials"] == 100
    assert result["exact_image_old_trials"] == 50
    assert result["units_present"] == 21
