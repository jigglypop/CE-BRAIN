from examples.brain import ce_brain_stage6_r2_replication as r2


def test_r2_keeps_r1_candidate_grid_and_threshold_logic():
    assert r2.r1.RANKS == (4, 8, 16, 32)
    assert r2.r1.RIDGES == (1e-3, 1e-2, 1e-1, 1.0)
    passed = {"improvement": 0.02, "lower_95": 0.01, "median": 0.02}
    assert r2.r1.decide({"R_vs_N": passed, "R_vs_D": passed, "R_vs_M": passed}) == "DEVELOPMENT_RECURRENT_PREDICTIVE_MODES_SUPPORTED"


def test_r2_identity_is_frozen():
    assert r2.EXPECTED_SESSION == "759883607"
    assert r2.EXPECTED_SHA256 == "689b5fdc793343c9b874a1080252ec8c7d08f790274500c1344b925a692cfea2"

