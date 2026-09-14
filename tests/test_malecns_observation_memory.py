import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

SPEC = importlib.util.spec_from_file_location(
    "observation_memory", Path(__file__).resolve().parents[1] / "verify/MaleCNS/observation_memory.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def fixture():
    a = sparse.csc_array([[.2, .0, .3], [.1, .4, .0], [.3, .1, .2]])
    b = sparse.csc_array([[.1, .4, .2], [.3, .1, .3]])
    codes, totals = np.array([0, 0, 1]), np.array([4, 1, 3])
    o, u = module.observation_and_lift(codes, totals, 2, "uniform")
    _, w = module.observation_and_lift(codes, totals, 2, "out_weight")
    return a, b, o, u, w


def test_boundary_observation_refines_category_and_preserves_parent():
    a, b, o, u, w = fixture()
    initial = module.initial_block(u, w, [0, 1])
    truth, fisher = module.truth_trajectory(a, b, o, initial, 5)
    full = np.block([[a.toarray(), np.zeros((3, 2))], [b.toarray(), np.eye(2)]])
    c = np.block([[o.toarray(), np.zeros((2, 2))], [np.zeros((2, 3)), np.eye(2)]])
    state = np.vstack((initial, np.zeros((2, 4))))
    for step in range(6):
        np.testing.assert_allclose(truth[step], c @ state, atol=1e-14)
        state = full @ state
    assert fisher[0, 0, 0] == pytest.approx(0)
    assert fisher[0, 0, 1] == pytest.approx(0)
    assert fisher[1, 0, 1] > fisher[1, 0, 0]
    assert np.all(fisher[:, :, 0] <= fisher[:, :, 1] + 1e-14)
    assert np.all(fisher[:, :, 1] <= fisher[:, :, 2] + 1e-14)


@pytest.mark.parametrize("reference_index", [0, 1])
def test_exact_memory_and_initial_term_match_dense_full_dynamics(reference_index):
    a, b, o, u, w = fixture()
    lifted = (u, w)[reference_index]
    initial = module.initial_block(u, w, [0, 1])
    truth, _ = module.truth_trajectory(a, b, o, initial, 6)
    m, kernels, _ = module.memory_operators(a, b, o, lifted, 5)
    residual = initial - lifted @ truth[0, :2]
    forcing = module.initial_forcing(a, b, o, lifted, residual, 6)
    exact = module.forecast(m, kernels, forcing, truth[0], 5, True)
    np.testing.assert_allclose(exact, truth, atol=1e-13)
    omitted = module.forecast(m, kernels, forcing, truth[0], 5, False)
    np.testing.assert_allclose(omitted[:, :, reference_index::2], truth[:, :, reference_index::2], atol=1e-13)
    assert np.max(np.abs(omitted[:, :, 1-reference_index] - truth[:, :, 1-reference_index])) > .01
    memoryless = module.forecast(m, kernels, forcing, truth[0], 0, False)
    np.testing.assert_allclose(memoryless[1, :, reference_index::2], truth[1, :, reference_index::2], atol=1e-13)
    assert np.max(np.abs(memoryless[2:, :, reference_index] - truth[2:, :, reference_index])) > 1e-4


def test_exactly_lumpable_chain_has_zero_memory_output():
    a = sparse.csc_array([[.1, .3, .1], [.4, .2, .3], [.2, .2, .1]])
    b = sparse.csc_array([[.2, .2, .3], [.1, .1, .2]])
    o, r = module.observation_and_lift(np.array([0, 0, 1]), np.array([1, 4, 2]), 2, "uniform")
    m, kernels, _ = module.memory_operators(a, b, o, r, 5)
    np.testing.assert_allclose(kernels, 0, atol=1e-14)
    initial = np.array([[1.], [0.], [0.]])
    state = initial
    dead = np.zeros((2, 1))
    y = np.vstack((o @ state, dead))
    for _ in range(6):
        dead = dead + b @ state
        state = a @ state
        y = m @ y
        np.testing.assert_allclose(y, np.vstack((o @ state, dead)), atol=1e-14)


def test_signed_finite_memory_is_not_clipped_or_renormalized():
    m = np.eye(2)
    kernels = np.array([[[-2.], [2.]]])
    forcing = np.zeros((2, 2, 1))
    initial = np.array([[1.], [0.]])
    predicted = module.forecast(m, kernels, forcing, initial, 1, True)
    np.testing.assert_allclose(predicted[-1, :, 0], [-1, 2])
    summary = module.forecast_summary(predicted, np.repeat(initial[None], 3, axis=0))
    assert summary['invalid_step_probe_distributions'] == 1
    assert summary['minimum_probability'] == -1
    assert summary['max_half_l1'] == 2
    assert summary['max_mass_error'] == 0


def test_invalid_lifting_and_initial_residual_fail_closed():
    with pytest.raises(ValueError, match="every active category"):
        module.observation_and_lift(np.array([0]), np.array([1]), 2, "uniform")
    with pytest.raises(ValueError, match="out-weight"):
        module.observation_and_lift(np.array([0]), np.array([0]), 1, "uniform")
    a, b, o, u, _ = fixture()
    with pytest.raises(ValueError, match="zero category sums"):
        module.initial_forcing(a, b, o, u, np.ones((3, 1)), 3)
