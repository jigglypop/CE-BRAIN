import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

SPEC = importlib.util.spec_from_file_location(
    "history_fisher", Path(__file__).resolve().parents[1] / "verify/MaleCNS/history_fisher.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def fixture():
    weights = np.array([[2, 0, 3], [1, 4, 0], [3, 1, 2],
                        [1, 1, 0], [0, 3, 2], [2, 0, 1], [1, 1, 2]], dtype=float)
    codes, terminal_codes, assigned = np.array([0, 0, 1]), np.array([0, 0, 1, 1]), np.array([True, False])
    p = weights / weights.sum(axis=0)
    a = sparse.csc_array(p[:3])
    b = sparse.csc_array(np.stack([p[3:][terminal_codes == c].sum(axis=0) for c in range(2)]))
    observed, _ = module.base.prior.observation_and_lift(codes, weights.sum(axis=0), 2, "uniform")
    initial = np.array([[.7, 0], [.3, 0], [0, 1.]])
    raw_features = np.zeros((3, 7, 3))
    for target in range(7):
        for source in range(3):
            target_code = codes[target] if target < 3 else terminal_codes[target - 3]
            raw_features[0, target, source] = target < 3
            raw_features[1, target, source] = assigned[codes[source]] and assigned[target_code] and codes[source] == target_code
            raw_features[2, target, source] = target < 3 and target != source and weights[source, target] > 0
    return weights, codes, terminal_codes, assigned, a, b, observed, initial, raw_features


def enumerate_paths(weights, raw_features, theta, codes, terminal_codes, initial, steps):
    active_count, total_count = weights.shape[1], weights.shape[0]
    categories, probes = int(max(codes.max(), terminal_codes.max()) + 1), initial.shape[1]
    observed_code = np.r_[codes, categories + terminal_codes]
    changed = weights * np.exp(np.einsum("k,kij->ij", theta, raw_features))
    changed /= changed.sum(axis=0)
    transition = np.block([[changed[:active_count], np.zeros((active_count, total_count - active_count))],
                           [changed[active_count:], np.eye(total_count - active_count)]])
    means = np.einsum("ij,kij->kj", changed, raw_features)
    output = np.zeros((steps + 1, 2 * categories, 2 * categories, probes))
    full_fisher = np.zeros((steps + 1, probes, 3, 3))
    states = [((i,), initial[i].copy(), np.zeros(3)) for i in range(active_count) if np.any(initial[i])]
    for path, probability, _ in states:
        c = observed_code[path[-1]]
        output[0, c, c] += probability
    for step in range(1, steps + 1):
        new_states = []
        for path, probability, score in states:
            source = path[-1]
            for target in np.flatnonzero(transition[:, source]):
                mass = probability * transition[target, source]
                next_score = score + (raw_features[:, target, source] - means[:, source] if source < active_count else 0)
                new_states.append(((*path, int(target)), mass, next_score))
                output[step, observed_code[source], observed_code[target]] += mass
                full_fisher[step] += mass[:, None, None] * np.outer(next_score, next_score)
        states = new_states
    return output, full_fisher, states


def run_fixture(a, b, observed, codes, assigned, initial, steps):
    fa, fb, means = module.base.features(a, b, codes, assigned)
    w = module.pair_operator(a, b, observed, codes)
    wk = [module.pair_operator(fa[k], fb[k], observed, codes) for k in range(3)]
    covariance, _ = module.source_covariance(fa, fb, means, codes, assigned)
    truth, jac, endpoint, _ = module.base.tangent_trajectory(a, b, observed, fa, fb, means, initial, steps)
    return module.tangent_run(a, b, observed, fa, fb, means, w, wk, covariance, initial, steps, truth, jac, endpoint)


def test_pair_operator_matches_raw_edge_categories_and_retains_sparse_shape():
    weights, codes, terminal_codes, assigned, a, b, observed, _, raw = fixture()
    fa, fb, means = module.base.features(a, b, codes, assigned)
    w = module.pair_operator(a, b, observed, codes)
    expected = np.zeros((16, 3))
    feature_expected = np.zeros((3, 16, 3))
    p = weights / weights.sum(axis=0)
    for target, source in zip(*np.nonzero(weights)):
        destination = codes[target] if target < 3 else 2 + terminal_codes[target - 3]
        row = codes[source] * 4 + destination
        expected[row, source] += p[target, source]
        feature_expected[:, row, source] += raw[:, target, source] * p[target, source]
    assert sparse.issparse(w) and w.shape == (16, 3) and w.has_canonical_format
    np.testing.assert_allclose(w.toarray(), expected, atol=1e-15)
    for k in range(3):
        wk = module.pair_operator(fa[k], fb[k], observed, codes)
        np.testing.assert_allclose(wk.toarray(), feature_expected[k], atol=1e-15)
        np.testing.assert_allclose(module.base.columns(wk), means[k], atol=1e-15)


def test_feature_covariance_includes_raw_overlap_before_observation_grouping():
    weights, codes, _, assigned, a, b, _, _, raw = fixture()
    fa, fb, means = module.base.features(a, b, codes, assigned)
    covariance, _ = module.source_covariance(fa, fb, means, codes, assigned)
    p = weights / weights.sum(axis=0)
    score = raw - np.einsum("ij,kij->kj", p, raw)[:, None, :]
    expected = np.einsum("ij,kij,lij->klj", p, score, score)
    np.testing.assert_allclose(covariance, expected, atol=1e-15)
    assert np.max(np.abs(covariance[0, 2])) > .01


def test_joint_tangent_and_path_fisher_match_independent_raw_path_enumeration():
    weights, codes, terminal_codes, assigned, a, b, observed, initial, raw = fixture()
    pair, jac, information, checks = run_fixture(a, b, observed, codes, assigned, initial, 3)
    expected, path_fisher, _ = enumerate_paths(weights, raw, np.zeros(3), codes, terminal_codes, initial, 3)
    np.testing.assert_allclose(pair, expected, atol=1e-14)
    np.testing.assert_allclose(information[:, :, 5, :3, :3], path_fisher, atol=1e-14)
    for k in range(3):
        theta = np.zeros(3)
        theta[k] = 1e-4
        plus, _, _ = enumerate_paths(weights, raw, theta, codes, terminal_codes, initial, 3)
        minus, _, _ = enumerate_paths(weights, raw, -theta, codes, terminal_codes, initial, 3)
        np.testing.assert_allclose(jac[..., k], (plus - minus) / 2e-4, atol=2e-9)
    assert checks["marginal_probability_max_error"] < 1e-14
    assert checks["marginal_tangent_max_error"] < 1e-14
    np.testing.assert_array_equal(jac[..., 3], 0)
    np.testing.assert_array_equal(information[..., 3, :], 0)
    assert np.min(np.linalg.eigvalsh(np.diff(information[:, :, 5], axis=0))) > -1e-14


def test_terminal_id_sufficiency_requires_full_pre_id_path_not_endpoint_only():
    weights, codes, terminal_codes, _, _, _, _, initial, raw = fixture()
    _, full, states = enumerate_paths(weights, raw, np.zeros(3), codes, terminal_codes, initial, 3)
    groups = {}
    endpoint_raw, endpoint_jac = np.zeros((7, 2)), np.zeros((3, 7, 2))
    endpoint_compressed, compressed_jac = np.zeros((5, 2)), np.zeros((3, 5, 2))
    for path, probability, score in states:
        compressed = tuple(state if state < 3 else 3 + terminal_codes[state - 3] for state in path)
        if compressed not in groups:
            groups[compressed] = [np.zeros(2), np.zeros((3, 2))]
        groups[compressed][0] += probability
        groups[compressed][1] += score[:, None] * probability
        endpoint_raw[path[-1]] += probability
        endpoint_jac[:, path[-1]] += score[:, None] * probability
        endpoint_compressed[compressed[-1]] += probability
        compressed_jac[:, compressed[-1]] += score[:, None] * probability
    probability = np.stack([value[0] for value in groups.values()])
    tangent = np.stack([value[1] for value in groups.values()], axis=1)
    np.testing.assert_allclose(module.base.fisher(probability, tangent), full[-1], atol=1e-14)
    difference = module.base.fisher(endpoint_raw, endpoint_jac) - module.base.fisher(endpoint_compressed, compressed_jac)
    assert np.trace(difference, axis1=-2, axis2=-1).max() > 1e-5


def test_pair_and_refined_endpoint_are_nonnested_and_pair_can_lose_information():
    a = sparse.csc_array([[0, 0, 0, 0, 0], [.5, 0, 0, .5, 0], [.5, 0, 0, .5, 0],
                          [0, .5, .5, 0, 0], [0, .5, .5, 0, 1.]])
    b = sparse.csc_array((3, 5))
    codes, assigned = np.array([0, 0, 1, 2, 2]), np.ones(3, dtype=bool)
    observed, _ = module.base.prior.observation_and_lift(codes, np.ones(5), 3, "uniform")
    initial = np.array([[1.], [0], [0], [0], [0]])
    _, _, information, _ = run_fixture(a, b, observed, codes, assigned, initial, 3)
    difference = information[2, 0, 4] - information[2, 0, 2]
    eigen = np.linalg.eigvalsh(difference)
    assert eigen.min() < -.1 and eigen.max() > .1
    assert np.linalg.eigvalsh(information[3, 0, 4] - information[2, 0, 4]).min() < -.1
    assert np.min(np.linalg.eigvalsh(information[3, 0, 5] - information[2, 0, 5])) > -1e-14


def test_deterministic_sources_have_zero_path_and_pair_information():
    a = sparse.csc_array([[0., 0.], [1., 0.]])
    b = sparse.csc_array([[0., 1.]])
    codes, assigned = np.array([0, 0]), np.array([True])
    observed = sparse.csr_array([[1., 1.]])
    pair, jac, information, _ = run_fixture(a, b, observed, codes, assigned, np.eye(2), 4)
    np.testing.assert_allclose(pair.sum(axis=(1, 2)), 1, atol=0)
    np.testing.assert_array_equal(jac, 0)
    np.testing.assert_array_equal(information, 0)


def test_pair_fisher_and_psd_guards_reject_invalid_inputs():
    pair = np.zeros((2, 2, 1))
    pair[0, 0, 0] = 1
    tangent = np.zeros((3, 2, 2, 1))
    tangent[0, 1, 1, 0] = 1e-20
    with pytest.raises(ValueError, match="outside fixed support"):
        module.joint_fisher(pair, tangent)
    with pytest.raises(ValueError, match="not PSD"):
        module.psd_min(np.diag([1., -.1, 0.]), "negative control")
    with pytest.raises(ValueError, match="nonfinite"):
        module.psd_min(np.full((3, 3), np.nan), "nonfinite control")
