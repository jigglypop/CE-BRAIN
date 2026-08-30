from examples.brain import ce_brain_stage9_da_r3_apparatus as apparatus


def test_dcohort_schema_contains_behavior_and_real_photometry():
    result = apparatus.audit()
    assert result["decision"] == "STAGE9_DA_DCOHORT_SCHEMA_ELIGIBLE"
    assert result["chemical_values_scored"] is False
    assert result["confirmation_opened"] is False
    assert all(row["photometry_data_shape"] == row["photometry_timestamp_shape"] for row in result["conditions"].values())
