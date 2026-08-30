import numpy as np

from examples.brain.ce_brain_stage3f_optofmri_state_rdm import (
    analyze_subject_rdms,
    exact_signflip_p,
    response_rdms,
)


def test_cross_half_rdm_is_repeat_stable() -> None:
    rng = np.random.default_rng(3)
    base = rng.normal(size=(6, 500))
    odd = base + rng.normal(scale=0.03, size=base.shape)
    even = base + rng.normal(scale=0.03, size=base.shape)
    odd_rdm, even_rdm, cross = response_rdms(odd, even)
    assert len(cross) == 15
    assert np.corrcoef(odd_rdm, even_rdm)[0, 1] > 0.99


def test_exact_signflip_has_expected_minimum() -> None:
    assert exact_signflip_p(np.ones(6)) == 1 / 64
    assert exact_signflip_p(-np.ones(6)) == 1.0


def test_common_geometry_candidate() -> None:
    rng = np.random.default_rng(5)
    template = np.linspace(0, 1, 15)
    rows = []
    for genotype in ("Thy1", "VGAT"):
        for index in range(6):
            rows.append(
                {
                    "genotype": genotype,
                    "repeat_reliability": 0.9,
                    "cross_half_rdm": (template + rng.normal(scale=0.01, size=15)).tolist(),
                }
            )
    result = analyze_subject_rdms(rows)
    assert result["status"] == "COMMON_SOURCE_RELATION_GEOMETRY_CANDIDATE"
