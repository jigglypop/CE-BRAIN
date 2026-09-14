import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

SPEC = importlib.util.spec_from_file_location(
    "hidden_walk", Path(__file__).resolve().parents[1] / "verify/MaleCNS/hidden_walk_information.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def fixture():
    # Terminal 20 and 21 share an observed label, but stay separate in the raw graph.
    edges = [(1, 1, 1), (1, 10, 2), (1, 20, 1), (2, 10, 1),
             (2, 21, 1), (10, 1, 1), (10, 10, 1), (10, 30, 2)]
    ids, codes = np.array([1, 2, 10], dtype=np.uint32), np.array([0, 0, 3])
    labels = ['A', *module.SPECIAL]
    totals = np.array([4, 2, 4], dtype=np.uint64)
    category = np.array([[1, 0, 0, 3], [0, 0, 0, 2], [3, 0, 0, 1]], dtype=np.uint32)
    keys = np.array([(a << 32) | b for a, b, _ in edges], dtype=np.uint64)
    weights = np.array([w for _, _, w in edges], dtype=np.uint32)
    p, b, c, scope = module.build_operators(keys, weights, ids, codes, totals, category, labels,
                                           expected_terminal_dyads=3, chunk_size=2)
    return p, b, c, scope, ids, codes, totals, category, labels


def test_whole_boundary_and_self_weights_are_preserved():
    p, b, c, scope, *_ = fixture()
    assert scope['terminal_target_dyads'] == 3 and scope['terminal_target_weight'] == 4
    assert scope['self_dyads'] == 2 and scope['self_weight'] == 2
    np.testing.assert_allclose(p.toarray(), [[.25, 0, .25], [0, 0, 0], [.5, .5, .25]])
    np.testing.assert_allclose(b.toarray()[0], [0, 0, .5])
    np.testing.assert_allclose(b.toarray()[3], [.25, .5, 0])
    np.testing.assert_allclose(np.asarray(p.sum(axis=0)) + np.asarray(b.sum(axis=0)), 1)
    assert c.shape == (4, 3)


def test_terminal_lumping_matches_explicit_id_absorbing_chain():
    p, b, c, _, _, _, totals, *_ = fixture()
    pair = module.initial_pair(totals, np.array([True, True, False]))
    records, observed = module.trajectory(p, b, c, pair, 5)
    full = np.zeros((6, 6))  # 1,2,10,20,21,30
    full[:3, :3] = p.toarray()
    full[3, 0], full[4, 1], full[5, 2] = .25, .5, .5
    full[3:, 3:] = np.eye(3)
    output = np.zeros((4, 6))
    output[[0, 0, 3, 3, 3, 0], np.arange(6)] = 1
    state = np.vstack((pair, np.zeros((3, 2))))
    for step in range(6):
        np.testing.assert_allclose(observed[step], (output @ state).T)
        state = full @ state
    assert records[0]['category_fisher'] == 0
    assert records[1]['category_fisher'] > 0


def test_first_hidden_return_includes_assigned_terminal_and_does_not_reenter():
    p, b, _, _, _, codes, totals, category, labels = fixture()
    pair = module.initial_pair(totals, np.array([True, True, False]))
    blocks = module.hidden_blocks(p, b, category, totals, codes, labels)
    result, arrivals, middle = module.first_excursion(blocks, b, pair, codes, labels, 5)
    np.testing.assert_allclose(result['active_hidden_entry_probability'], [.5, .5])
    # Hidden 10 returns to active 1 or terminal assigned 30 with probability 3/4.
    expected = .5 * .75 * np.power(.25, np.arange(4))
    np.testing.assert_allclose(arrivals[:, 0, 0], expected)
    np.testing.assert_allclose(arrivals[:, 1, 0], expected)
    np.testing.assert_allclose(middle.sum(axis=0), arrivals[0])
    assert result['steps'][-1]['unresolved_active_hidden_probability'][0] == pytest.approx(.5*.25**4)


def test_fisher_mixture_uses_exact_zero_support_and_contracts():
    pair = np.array([[1., 0.], [0., 1.], [0., 0.]])
    assert module.fisher_midpoint(pair) == 4
    projection = np.array([[1, 1, 0], [0, 0, 1.]])
    assert module.fisher_midpoint(projection @ pair) == 0
    delta = 1e-6
    midpoint = pair.mean(axis=1)
    derivative = ((.5+delta)*pair[:, 1]+(.5-delta)*pair[:, 0] -
                  ((.5-delta)*pair[:, 1]+(.5+delta)*pair[:, 0]))/(2*delta)
    positive = midpoint > 0
    assert np.sum(derivative[positive]**2/midpoint[positive]) == pytest.approx(4)


def test_invalid_cache_and_memory_budget_fail_closed():
    keys = np.array([(1 << 32) | 2], dtype=np.uint64)
    values = (keys, np.array([1], dtype=np.uint32), np.array([1], dtype=np.uint32), np.array([0]),
              np.array([1], dtype=np.uint64), np.array([[1, 0, 0, 0]], dtype=np.uint32), ['A', *module.SPECIAL])
    with pytest.raises(MemoryError):
        module.build_operators(*values, max_working_gib=0)
    with pytest.raises(MemoryError):
        module.build_operators(*values, max_working_gib=float('nan'))
    with pytest.raises(ValueError, match='terminal dyad count'):
        module.build_operators(*values, expected_terminal_dyads=0)
