import numpy as np

from examples.brain.ce_brain_stage3h_optofmri_structural_operator import (
    incremental_residuals,
    normalize_targets,
    parcel_weights,
    profile_rdm,
)


def test_parcel_weights_preserve_voxel_multiplicity() -> None:
    atlas = np.array([[[10]], [[10]], [[20]], [[20]]])
    tessellation = np.array([[[1]], [[1]], [[2]], [[3]]])
    weights = parcel_weights(atlas, tessellation, [(10,), (20,)], 3)
    assert np.allclose(weights[0], (1.0, 0.0, 0.0))
    assert np.allclose(weights[1], (0.0, 0.5, 0.5))


def test_incremental_order_removes_lower_order_linear_content() -> None:
    first = np.arange(1.0, 7.0)
    independent = np.array((1.0, -1.0, 2.0, -2.0, 1.0, -1.0))
    independent -= np.column_stack((first, np.ones(6))) @ np.linalg.lstsq(
        np.column_stack((first, np.ones(6))), independent, rcond=None
    )[0]
    beta = np.stack((first, 3.0 * first + independent), axis=1)[None, :, :]
    residual = incremental_residuals(beta)
    assert np.allclose(residual[0, :, 1], independent)


def test_profile_rdm_is_zero_for_same_and_large_for_opposite_profiles() -> None:
    profiles = normalize_targets(np.array(((1, 2, 3, 4), (1, 2, 3, 4), (4, 3, 2, 1)), dtype=float))
    rdm = profile_rdm(profiles)
    assert np.allclose(rdm, (0.0, 2.0, 2.0))
