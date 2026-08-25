from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "history_edge_subspace.py"


def _load_standalone_module():
    """Load the finite seam without importing the optional torch package facade."""

    name = "ce_history_edge_subspace"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


_history_edge_subspace = _load_standalone_module()
EdgeContribution = _history_edge_subspace.EdgeContribution
FiniteEdgeMetric = _history_edge_subspace.FiniteEdgeMetric
effective_dimension = _history_edge_subspace.effective_dimension
mobility_scale = _history_edge_subspace.mobility_scale
orthogonal_concentration = _history_edge_subspace.orthogonal_concentration
spectral_subspace = _history_edge_subspace.spectral_subspace
topology_with_deleted_edges = _history_edge_subspace.topology_with_deleted_edges


def _edge_metric() -> FiniteEdgeMetric:
    return FiniteEdgeMetric(
        np.diag([1.0, 1.5, 2.0]),
        (
            EdgeContribution(
                np.array([[1.0, -1.0, 0.0], [0.0, 1.0, -1.0]]),
                np.diag([0.7, 0.2]),
            ),
        ),
        declared_adjacency=(True,),
    )


def test_coercive_edge_metric_and_baseline_free_counterexample() -> None:
    model = _edge_metric()
    metric = model.metric((1.0,))

    assert np.linalg.eigvalsh(metric).min() >= model.baseline_coercivity
    singular_edge = EdgeContribution(np.array([[1.0, -1.0]]), np.array([[1.0]])).operator()
    assert np.allclose(singular_edge @ np.ones(2), 0.0)
    with pytest.raises(ValueError, match="coercive"):
        FiniteEdgeMetric(np.zeros((2, 2)), (EdgeContribution(np.eye(2), np.eye(2)),))


def test_tolerance_accepted_symmetric_input_is_canonicalized() -> None:
    almost_symmetric = np.array([[1.0, 5e-11], [0.0, 1.0]])
    edge = EdgeContribution(np.eye(2), almost_symmetric)

    assert np.allclose(edge.weight, edge.weight.T)
    assert np.allclose(edge.weight, 0.5 * (almost_symmetric + almost_symmetric.T))


def test_psd_roundoff_band_is_projected_and_material_negative_is_rejected() -> None:
    projected = effective_dimension(np.array([[-5e-11]]), 1.0)

    assert projected.eigenvalues[0] == 0.0
    assert projected.effective_dimension == 0.0
    with pytest.raises(ValueError, match="positive semidefinite"):
        effective_dimension(np.array([[-2e-10]]), 1.0)


def test_perturbation_certificate_bounds_actual_change() -> None:
    model = _edge_metric()
    certificate = model.perturbation_certificate((1.0,), (0.9,))
    deletion = model.perturbation_certificate((1.0,), (0.0,))

    assert certificate.actual_spectral_norm <= certificate.theorem_upper_bound + 1e-12
    assert certificate.baseline_coercivity == 1.0
    assert certificate.normalized_upper_bound > 0.0
    assert certificate.small_perturbation
    assert not deletion.small_perturbation
    assert np.linalg.eigvalsh(model.metric((0.0,))).min() >= model.baseline_coercivity


def test_metric_availability_does_not_mutate_declared_adjacency() -> None:
    model = _edge_metric()
    before = model.declared_adjacency
    assert not np.allclose(model.metric((1.0,)), model.metric((0.0,)))
    assert model.declared_adjacency == before == (True,)
    assert topology_with_deleted_edges(before, (0,)) == (False,)


def test_symmetric_spectral_cluster_returns_orthogonal_projector_rank_and_gap() -> None:
    transition = np.diag([0.1, 0.2, 0.8, 0.95])
    subspace = spectral_subspace(transition, interval=(0.75, 1.0), min_gap=0.1)

    assert subspace.numerical_rank == subspace.real_dimension == 2
    assert subspace.rank_tolerance == 1e-10
    assert subspace.input_canonicalization_residual == 0.0
    assert subspace.spectral_gap > 0.1
    assert np.allclose(subspace.projector, subspace.projector.T)
    assert np.allclose(subspace.projector @ subspace.projector, subspace.projector)


def test_symmetric_transition_certificate_reports_canonicalization_residual() -> None:
    transition = np.diag([0.1, 0.2, 0.8, 0.95])
    transition[0, 1] = 5e-11
    subspace = spectral_subspace(transition, indices=(2, 3), min_gap=0.1)

    assert subspace.input_canonicalization_residual > 0.0
    assert subspace.normality_residual <= subspace.certificate_tolerance
    assert subspace.invariance_residual <= subspace.certificate_tolerance


def test_spectral_subspace_rejects_nonnormal_transition() -> None:
    with pytest.raises(ValueError, match="nonnormal"):
        spectral_subspace(np.array([[1.0, 1.0], [0.0, 1.0]]), indices=(0,))


def test_normal_rotation_pair_returns_a_real_orthogonal_two_subspace() -> None:
    transition = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 3.0]])
    eigenvalues = np.linalg.eigvals(transition)
    pair = tuple(index for index, value in enumerate(eigenvalues) if abs(value.imag) > 0.5)
    subspace = spectral_subspace(transition, indices=pair, min_gap=0.1)

    assert subspace.numerical_rank == subspace.real_dimension == 2
    assert np.allclose(subspace.projector, subspace.projector.T)
    assert np.allclose(subspace.projector @ subspace.projector, subspace.projector)
    assert subspace.normality_residual <= subspace.certificate_tolerance
    assert subspace.invariance_residual <= subspace.certificate_tolerance


def test_normal_repeated_conjugate_pairs_have_one_to_one_real_cluster_certificate() -> None:
    transition = np.array(
        [[0.0, -1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0, 0.0],
         [0.0, 0.0, 0.0, -1.0, 0.0], [0.0, 0.0, 1.0, 0.0, 0.0],
         [0.0, 0.0, 0.0, 0.0, 3.0]]
    )
    pair = tuple(index for index, value in enumerate(np.linalg.eigvals(transition)) if abs(value.imag) > 0.5)
    subspace = spectral_subspace(transition, indices=pair, min_gap=0.1)

    assert subspace.numerical_rank == subspace.real_dimension == 4
    assert np.allclose(subspace.projector, subspace.projector.T)
    assert np.allclose(subspace.projector @ subspace.projector, subspace.projector)
    assert subspace.invariance_residual <= subspace.certificate_tolerance


def test_near_nonnormal_transition_fails_the_scale_aware_certificate() -> None:
    near_nonnormal = np.array([[0.0, -1.0, 1e-7], [1.0, 0.0, 0.0], [0.0, 0.0, 3.0]])

    with pytest.raises(ValueError, match="nonnormal"):
        spectral_subspace(near_nonnormal, indices=(0, 1), min_gap=0.1)


def test_normal_near_real_eigenvalue_is_rejected_as_ambiguous() -> None:
    transition = np.array([[0.0, -1e-6, 0.0], [1e-6, 0.0, 0.0], [0.0, 0.0, 3.0]])
    one_eigenvalue = (0,)

    with pytest.raises(ValueError, match="ambiguous near-real"):
        spectral_subspace(
            transition,
            indices=one_eigenvalue,
            min_gap=1e-7,
            certificate_tolerance=1e-4,
        )


def test_orthogonal_concentration_returns_a_certificate_for_exact_projector() -> None:
    covariance = np.array([[1.0, 1.0], [1.0, 1.0]])
    certificate = orthogonal_concentration(np.diag([1.0, 0.0]), covariance)

    assert certificate.value == 0.5
    assert certificate.input_symmetry_residual == 0.0
    assert certificate.input_idempotence_residual == 0.0
    assert np.allclose(certificate.canonical_projector, np.diag([1.0, 0.0]))


def test_orthogonal_concentration_canonicalizes_near_projector_and_rejects_material_errors() -> None:
    covariance = np.array([[1.0, 1.0], [1.0, 1.0]])
    near_projector = np.diag([1.0 + 5e-11, -4e-11])
    certificate = orthogonal_concentration(near_projector, covariance)

    assert certificate.input_idempotence_residual > 0.0
    assert np.allclose(certificate.canonical_projector, np.diag([1.0, 0.0]))
    assert certificate.value == 0.5
    with pytest.raises(ValueError, match="idempotent"):
        orthogonal_concentration(np.diag([0.8, 0.2]), covariance)
    with pytest.raises(ValueError, match="symmetric"):
        orthogonal_concentration(np.array([[1.0, 2.0], [0.0, 0.0]]), covariance)


def test_effective_dimension_is_bounded_monotone_and_distinct_from_numerical_rank() -> None:
    gram = np.diag([4.0, 1.0, 0.25, 0.0])
    at_one = effective_dimension(gram, 1.0)
    at_two = effective_dimension(gram, 2.0)

    assert math.isclose(at_one.effective_dimension, 1.5)
    assert at_one.positive_spectrum_rank == 3
    assert at_one.numerical_hard_rank == 3
    assert at_one.rank_tolerance == 1e-10
    assert 0.0 <= at_one.effective_dimension <= at_one.positive_spectrum_rank
    assert at_two.effective_dimension < at_one.effective_dimension
    assert at_one.effective_dimension != at_one.numerical_hard_rank


def test_effective_dimension_positive_spectrum_rank_is_not_threshold_rank() -> None:
    tiny_positive = effective_dimension(np.diag([5e-11]), 1e-20)

    assert math.isclose(tiny_positive.effective_dimension, 1.0, rel_tol=1e-9)
    assert tiny_positive.positive_spectrum_rank == 1
    assert tiny_positive.numerical_hard_rank == 0
    assert tiny_positive.effective_dimension <= tiny_positive.positive_spectrum_rank


def test_mobility_scale_requires_positive_finite_reference_scales() -> None:
    assert mobility_scale(2.0, 2.0, 1.0) == 2.0
    with pytest.raises(ValueError, match="positive finite"):
        mobility_scale(1.0, 0.0, 1.0)
