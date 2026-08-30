from examples.brain import ce_brain_stage7_r2_selector as selector


def test_endpoint_blind_selector_is_deterministic_and_independent():
    result = selector.select()
    assert result["decision"] == "STAGE7_R2_ENDPOINT_BLIND_SESSION_SELECTED"
    assert result["topdir"] == "ec016.17"
    assert result["session"] == "ec016.234"
    assert result["ca1_pyramidal_units"] == 84
    assert result["endpoint_opened"] is False
    assert result["archive_md5"] == "3b350f3b76d7f0c903ee4afab89db9ec"
