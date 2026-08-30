from examples.brain import ce_brain_stage9_da_apparatus as apparatus


def test_condition_parser_does_not_merge_protocol_variants():
    assert apparatus.condition("sub-60s-F10") == "60s"
    assert apparatus.condition("sub-60s-few-M3") == "60s-few"
    assert apparatus.condition("sub-600sD-F7") == "600sD"


def test_hash_split_is_disjoint_and_complete():
    subjects = [f"sub-60s-F{i}" for i in range(1, 7)]
    result = apparatus.split_subjects(subjects)
    flattened = sum(result.values(), [])
    assert sorted(flattened) == sorted(subjects)
    assert len(flattened) == len(set(flattened))
    assert all(result[name] for name in result)
