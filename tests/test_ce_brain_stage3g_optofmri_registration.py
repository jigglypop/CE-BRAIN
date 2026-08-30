import numpy as np

from examples.brain.ce_brain_stage3g_optofmri_registration import (
    SOURCE_BASES,
    expanded_labels,
    judge_sample,
    label_dice,
    select_development_anatomy_entries,
    scaled_origin_preserving_center,
)


def test_author_label_families_include_layers_and_both_hemispheres() -> None:
    m_op = expanded_labels(SOURCE_BASES["MOp"])
    assert (18, 23, 2018, 2023) == (m_op[0], m_op[5], m_op[6], m_op[-1])
    assert 298 in expanded_labels(SOURCE_BASES["RSP"])
    assert 2359 in expanded_labels(SOURCE_BASES["VISarl"])


def test_label_dice_uses_correct_source_families() -> None:
    reference = np.array([18, 19, 185, 2185, 298, 2325, 346, 2353, 0])
    candidate = reference.copy()
    scores = label_dice(candidate, reference)
    assert all(value == 1.0 for value in scores.values())


def test_sample_gate_refuses_a_bad_local_source_mask() -> None:
    scores = {"foreground": 0.95, **{name: 0.70 for name in SOURCE_BASES}}
    scores["VISarl"] = 0.20
    result = judge_sample(scores)
    assert result["status"] == "SAMPLE_REGISTRATION_GATE_FAIL"
    assert result["minimum_source_dice"] == 0.20


def test_sample_gate_passes_only_all_three_locked_thresholds() -> None:
    scores = {"foreground": 0.91, **{name: 0.60 for name in SOURCE_BASES}}
    scores["VISarl"] = 0.36
    result = judge_sample(scores)
    assert result["status"] == "SAMPLE_REGISTRATION_GATE_PASS"


def test_selects_one_anatomy_for_each_locked_development_subject() -> None:
    subjects = (
        "Thy1-sub05", "Thy1-sub08", "Thy1-sub09", "Thy1-sub10", "Thy1-sub07", "Thy1-sub06",
        "VGAT-sub07", "VGAT-sub08", "VGAT-sub05", "VGAT-sub02", "VGAT-sub03", "VGAT-sub09",
    )
    manifest = [{"filename": f"{subject}/anat/T2w.nii.gz"} for subject in reversed(subjects)]
    selected = select_development_anatomy_entries(manifest)
    assert [row["filename"].split("/")[0] for row in selected] == list(subjects)


def test_xyz_scale_preserves_physical_center() -> None:
    origin = scaled_origin_preserving_center(
        (160, 100, 120),
        (0.1, 0.1, 0.1),
        (-0.1, -0.1, 0.1),
        (-1, 0, 0, 0, -1, 0, 0, 0, 1),
        10.0,
    )
    assert np.allclose(origin, (71.45, 44.45, -53.45))
