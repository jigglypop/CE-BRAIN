import numpy as np

from examples.brain.ce_brain_stage3h_optofmri_structural_relation import analyze


def _fixture(reliable_vgat: bool = True):
    rng = np.random.default_rng(7)
    mono = np.linspace(0, 1, 15) + rng.normal(0, 0.02, 15)
    bi = rng.normal(size=15)
    tri = np.linspace(1, 0, 15) + rng.normal(0, 0.02, 15)
    structural = {
        "response_data_used": False,
        "structural_rdms": {
            "incremental_order_1": mono.tolist(),
            "incremental_order_2": bi.tolist(),
            "incremental_order_3": tri.tolist(),
        },
    }
    subjects = []
    for genotype, response in (("Thy1", mono), ("VGAT", tri)):
        for index in range(6):
            subjects.append(
                {
                    "subject": f"{genotype}-{index}",
                    "genotype": genotype,
                    "repeat_reliability": 0.6 if genotype == "Thy1" or reliable_vgat else -0.1,
                    "cross_half_rdm": (response + rng.normal(0, 0.01, 15)).tolist(),
                }
            )
    return structural, {"subjects": subjects}


def test_fixed_condition_specific_orders_can_both_pass() -> None:
    structural, response = _fixture()
    result = analyze(structural, response)
    assert result["status"] == "STRUCTURAL_OPERATOR_RELATION_CANDIDATE"
    assert result["gates"]["Thy1"]["primary_order"] == 1
    assert result["gates"]["VGAT"]["primary_order"] == 3


def test_unreliable_condition_cannot_be_promoted() -> None:
    structural, response = _fixture(reliable_vgat=False)
    result = analyze(structural, response)
    assert result["status"] == "CONDITION_LIMITED_STRUCTURAL_OPERATOR_CANDIDATE"
    assert result["gates"]["VGAT"]["passed"] is False
