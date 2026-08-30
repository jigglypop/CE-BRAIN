import numpy as np

from examples.brain.ce_brain_stage3i_optofmri_time_kernel import analyze, percent_trajectory


def test_percent_trajectory_preserves_time_and_reverses_mion_sign() -> None:
    data = np.full((2, 1, 1, 120), 100.0, dtype=np.float32)
    data[0, 0, 0, 40:100] = np.arange(100.0, 40.0, -1.0)
    mask = np.array([[[True]], [[False]]])
    result = percent_trajectory(data, mask)
    assert result.shape == (1, 60)
    assert result[0, 0] == 0.0
    assert result[0, -1] == 59.0


def test_repeatability_gate_is_condition_specific() -> None:
    rows = []
    for genotype, value in (("Thy1", 0.6), ("VGAT", -0.1)):
        for index in range(6):
            rows.append(
                {
                    "subject": f"{genotype}-{index}",
                    "genotype": genotype,
                    "repeat_reliability": value,
                    "cross_half_rdm": [0.0] * 15,
                }
            )
    result = analyze(rows)
    assert result["gates"]["Thy1"]["passed"] is True
    assert result["gates"]["VGAT"]["passed"] is False
    assert result["status"] == "SPATIOTEMPORAL_KERNEL_REPEATABILITY_NOT_ESTABLISHED"
