import numpy as np

from examples.brain.ce_brain_stage3j_optofmri_motion_kernel import (
    _motion_summary,
    add_motion_diagnostic,
)


def test_motion_summary_uses_afni_column_convention(tmp_path) -> None:
    motion = tmp_path / "motion.1D"
    displacement = tmp_path / "disp.1D"
    np.savetxt(motion, [[1, -2, 3, 0.1, -0.2, 0.3]])
    np.savetxt(displacement, [0.2, 0.4])
    result = _motion_summary(motion, displacement)
    assert result["max_abs_rotation_deg"] == 3.0
    assert result["max_abs_translation_mm"] == 0.3
    assert result["max_displacement_mm"] == 0.4


def test_motion_explanation_requires_repeatability_and_delta_gate() -> None:
    subjects = []
    raw_subjects = []
    for genotype in ("Thy1", "VGAT"):
        for index in range(6):
            corrected = 0.6 if genotype == "VGAT" else 0.4
            subjects.append({"subject": f"{genotype}-{index}", "genotype": genotype, "repeat_reliability": corrected})
            raw_subjects.append({"subject": f"{genotype}-{index}", "repeat_reliability": -0.1})
    result = {
        "subjects": subjects,
        "gates": {"VGAT": {"passed": True}},
    }
    updated = add_motion_diagnostic(result, {"subjects": raw_subjects})
    assert updated["status"] == "VGAT_MOTION_EXPLANATION_CANDIDATE"
    assert updated["vgat_motion_explanation"]["passed"] is True
