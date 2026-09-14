import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

SPEC = importlib.util.spec_from_file_location(
    "connection_fisher", Path(__file__).resolve().parents[1] / "verify/MaleCNS/connection_fisher.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def fixture():
    weights = np.array([[2, 0, 3], [1, 4, 0], [3, 1, 2], [1, 4, 2], [3, 1, 3]], dtype=float)
    totals = weights.sum(axis=0)
    a, b = sparse.csc_array(weights[:3] / totals), sparse.csc_array(weights[3:] / totals)
    codes, assigned = np.array([0, 0, 1]), np.array([True, False])
    o, u = module.prior.observation_and_lift(codes, totals, 2, "uniform")
    initial = u.toarray()
    raw_features = np.zeros((4, 5, 3))
    for target in range(5):
        for source in range(3):
            raw_features[0, target, source] = target < 3
            target_code = codes[target] if target < 3 else target - 3
            raw_features[1, target, source] = assigned[codes[source]] and assigned[target_code] and codes[source] == target_code
            raw_features[2, target, source] = target < 3 and target != source and weights[source, target] > 0
            raw_features[3, target, source] = 1
    return weights, a, b, codes, assigned, o, initial, raw_features


def dense_forward(weights, feature, theta, initial, observed, steps):
    tilted = weights * np.exp(np.einsum("k,kij->ij", theta, feature))
    tilted /= tilted.sum(axis=0)
    transition = np.block([[tilted[:3], np.zeros((3, 2))], [tilted[3:], np.eye(2)]])
    output_map = sparse.block_diag((observed, np.eye(2))).toarray()
    state = np.vstack((initial, np.zeros((2, initial.shape[1]))))
    rows = []
    for _ in range(steps + 1):
        rows.append(output_map @ state)
        state = transition @ state
    return np.asarray(rows)


def test_raw_feature_definition_includes_terminal_same_category_and_excludes_self():
    weights, a, b, codes, assigned, _, _, raw = fixture()
    fa, fb, means = module.features(a, b, codes, assigned)
    p = weights / weights.sum(axis=0)
    for k in range(3):
        np.testing.assert_allclose(np.vstack((fa[k].toarray(), fb[k].toarray())), p * raw[k])
        np.testing.assert_allclose(means[k], (p * raw[k]).sum(axis=0))
    assert fb[1].nnz == 2
    assert fa[2].nnz == 2
    assert np.all(fa[2].diagonal() == 0)


def test_tangent_matches_independent_dense_raw_tilt_and_nested_fisher():
    weights, a, b, codes, assigned, observed, initial, raw = fixture()
    fa, fb, means = module.features(a, b, codes, assigned)
    truth, jac, g, checks = module.tangent_trajectory(a, b, observed, fa, fb, means, initial, 6)
    expected = dense_forward(weights, raw, np.zeros(4), initial, observed, 6)
    np.testing.assert_allclose(truth, expected, atol=1e-14)
    for k in range(4):
        theta = np.zeros(4)
        theta[k] = 1e-4
        fd = (dense_forward(weights, raw, theta, initial, observed, 6) -
              dense_forward(weights, raw, -theta, initial, observed, 6)) / 2e-4
        np.testing.assert_allclose(jac[..., k], fd, atol=2e-9)
    assert np.max(np.abs(jac[0])) == 0
    assert np.max(np.abs(g[..., 3, :])) == 0
    assert np.min(np.linalg.eigvalsh(g[:, :, 1] - g[:, :, 0])) > -1e-14
    assert np.min(np.linalg.eigvalsh(g[:, :, 2] - g[:, :, 1])) > -1e-14
    assert checks["tangent_mass_max_error"] < 1e-14
    # A parameter-dependent transition need not contract endpoint information in time.
    assert np.max(np.diagonal(g[1], axis1=-2, axis2=-1)) > 0


def test_axis_tilt_matches_raw_exponentiation_without_mutating_inputs():
    weights, a, b, codes, assigned, _, _, raw = fixture()
    fa, fb, _ = module.features(a, b, codes, assigned)
    before = a.toarray(), b.toarray()
    for k in range(3):
        for h in (-.2, .2):
            changed_a, changed_b = module.axis_tilt(a, b, fa[k], fb[k], h)
            wanted = weights * np.exp(h * raw[k])
            wanted /= wanted.sum(axis=0)
            np.testing.assert_allclose(np.vstack((changed_a.toarray(), changed_b.toarray())), wanted, atol=1e-15)
    np.testing.assert_array_equal(a.toarray(), before[0])
    np.testing.assert_array_equal(b.toarray(), before[1])


def test_arbitrary_source_common_scaling_cancels_with_overlapping_features():
    weights, _, _, _, _, observed, initial, raw = fixture()
    theta = np.array([.2, -.3, .1, 0.])
    reference = dense_forward(weights, raw, theta, initial, observed, 6)
    scaled = weights * np.exp(np.array([-.7, .3, 1.1]))
    np.testing.assert_allclose(dense_forward(scaled, raw, theta, initial, observed, 6), reference, atol=1e-14)


def test_fisher_uses_exact_support_and_full_cross_coordinate_terms():
    p = np.array([[.25], [.75], [0.]])
    j = np.array([[[1.], [-1.], [0.]], [[2.], [-2.], [0.]]])
    expected = (1 / .25 + 1 / .75) * np.array([[[1., 2.], [2., 4.]]])
    np.testing.assert_allclose(module.fisher(p, j, block_size=1), expected)
    j[0, -1, 0] = 1e-20
    with pytest.raises(ValueError, match="outside fixed support"):
        module.fisher(p, j)


def test_one_destination_per_source_is_structurally_unidentifiable():
    a = sparse.csc_array([[0., 0.], [1., 0.]])
    b = sparse.csc_array([[0., 1.]])
    codes, assigned = np.array([0, 0]), np.array([True])
    observed = sparse.csr_array([[1., 1.]])
    fa, fb, means = module.features(a, b, codes, assigned)
    _, jac, g, _ = module.tangent_trajectory(a, b, observed, fa, fb, means, np.eye(2), 4)
    np.testing.assert_array_equal(jac, 0)
    np.testing.assert_array_equal(g, 0)


def test_parent_ancestry_and_reciprocal_census_fail_closed(tmp_path):
    dyad_path, hidden_path, parent_path = [tmp_path / name for name in ("dyad.json", "hidden.json", "parent.json")]
    dyad = {"schema": "malecns-raw-dyad-return-v1", "reciprocal_directed_dyads": 2,
            "category_reciprocal_weights": [[0, 3], [5, 0]]}
    dyad_path.write_text(json.dumps(dyad), encoding="utf-8")
    hidden_path.write_text(json.dumps({"dyad_result_sha256": module.prior.base.digest(dyad_path)}), encoding="utf-8")
    parent_path.write_text(json.dumps({"schema": "malecns-observation-memory-v1", "parent_result": str(hidden_path),
                                     "parent_result_sha256": module.prior.base.digest(hidden_path)}), encoding="utf-8")
    _, checked, _ = module.read_ancestry(parent_path, dyad_path)
    module.check_reciprocal_census({"directed_dyads": 2, "contact_weight": 8}, checked)
    with pytest.raises(ValueError, match="census"):
        module.check_reciprocal_census({"directed_dyads": 2, "contact_weight": 7}, checked)
    dyad_path.write_text(json.dumps({**dyad, "reciprocal_directed_dyads": 4}), encoding="utf-8")
    with pytest.raises(ValueError, match="ancestry"):
        module.read_ancestry(parent_path, dyad_path)
    hidden_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="hidden parent"):
        module.read_ancestry(parent_path, dyad_path)
