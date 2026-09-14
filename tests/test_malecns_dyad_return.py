import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "dyad_return", Path(__file__).resolve().parents[1] / "verify/MaleCNS/dyad_return_paths.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_uint32_keys_are_exact_and_reversible():
    pre = np.array([0, 2**32 - 1, 2**31 + 3], dtype=np.uint64)
    post = np.array([2**32 - 1, 0, 4], dtype=np.uint64)
    keys = module.packed_keys(pre, post)
    assert np.array_equal(module.reverse_keys(keys), module.packed_keys(post, pre))
    assert np.array_equal(module.reverse_keys(module.reverse_keys(keys)), keys)
    with pytest.raises(ValueError):
        module.packed_keys(np.array([-1]), np.array([1]))
    with pytest.raises(ValueError):
        module.packed_keys(np.array([2**32]), np.array([1]))


def test_unsorted_duplicate_dyads_aggregate_weight_without_extra_paths():
    pre, post = np.array([2, 1, 1, 3, 1]), np.array([1, 2, 2, 1, 2])
    weights = np.array([5, 2, 3, 1, 4], dtype=np.uint32)
    keys, weights, info = module.canonicalize(module.packed_keys(pre, post), weights)
    assert keys.tolist() == module.packed_keys(np.array([1, 2, 3]), np.array([2, 1, 1])).tolist()
    assert weights.tolist() == [9, 5, 1]
    assert info['duplicate_extra_rows'] == 2 and info['duplicate_keys'] == 1
    assert not info['original_sorted']


def test_actual_middle_id_join_matches_brute_force_not_category_product():
    edges = [(1, 10, 2), (10, 2, 3), (3, 11, 1), (11, 3, 1),
             (1, 20, 1), (21, 2, 1), (1, 1, 7), (1, 10, 3)]
    pre, post, w = (np.array(x) for x in zip(*edges))
    keys, weights, _ = module.canonicalize(module.packed_keys(pre, post), w)
    labels = ['A', 'B', *module.SPECIAL]
    ids, codes = np.array([1, 2, 3]), np.array([0, 1, 0])
    result, arrays = module.analyze(keys, weights, ids, codes, labels, chunk_size=2)
    unique = {(a, b) for a, b, _ in edges if a != b}
    reciprocal = {(a, b) for a, b in unique if (b, a) in unique}
    assert result['reciprocal_directed_dyads'] == len(reciprocal) == 2
    walks = {(a, v, b) for a, v in unique for vv, b in unique if v == vv and a in ids and b in ids}
    unknown = next(r for r in result['two_edge_paths'] if r['middle_group'] == 'UNANNOTATED_SEGMENT')
    assert unknown['two_edge_walks_assigned_to_assigned'] == len(walks) == 2
    assert unknown['closed_two_edge_walks_same_start_id'] == 1
    assert unknown['three_distinct_id_paths'] == 1
    assert result['self_dyads'] == 1 and result['self_weight'] == 7
    # The disconnected middle IDs 20 and 21 must not form an artificial path.
    assert (1, 20, 2) not in walks and (1, 21, 2) not in walks
    for witness in unknown['witnesses']:
        assert (witness['start_id'], witness['middle_id'], witness['end_id']) in walks
    assert int(arrays['source_out_weight'].sum()) == sum(e[2] for e in edges)


def test_self_loop_only_is_preserved_but_not_counted_as_recurrence():
    keys, weights, _ = module.canonicalize(module.packed_keys(np.array([1]), np.array([1])), np.array([4]))
    labels = ['A', *module.SPECIAL]
    result, arrays = module.analyze(keys, weights, np.array([1]), np.array([0]), labels)
    assert result['nonself_unique_dyads'] == 0
    assert result['reciprocal_directed_fraction'] is None
    assert all(r['two_edge_walks_assigned_to_assigned'] == 0 for r in result['two_edge_paths'])
    assert arrays['source_out_weight'].tolist() == [4]


def test_resource_and_weight_guards():
    keys = module.packed_keys(np.array([1]), np.array([2]))
    with pytest.raises(ValueError, match='weights'):
        module.canonicalize(keys, np.array([2**32], dtype=np.uint64))
    with pytest.raises(ValueError, match='weights'):
        module.canonicalize(np.repeat(keys, 2), np.array([2**64 - 1, 1], dtype=np.uint64))
    with pytest.raises(MemoryError):
        module.analyze(keys, np.array([1], dtype=np.uint32), np.array([1]), np.array([0]),
                       ['A', *module.SPECIAL], max_working_gib=0)


def test_reciprocal_weight_denominators_exclude_self_not_terminal():
    pre, post = np.array([1, 1, 2, 2]), np.array([1, 2, 1, 3])
    keys, weights, _ = module.canonicalize(module.packed_keys(pre, post), np.array([100, 9, 3, 6]))
    labels = ['A', *module.SPECIAL]
    result, _ = module.analyze(keys, weights, np.array([1, 2]), np.array([0, 0]), labels)
    assert result['reciprocal_directed_fraction'] == pytest.approx(2 / 3)
    assert result['weight_on_reciprocal_edges_fraction'] == pytest.approx(12 / 18)
    assert result['balanced_reciprocal_weight_fraction'] == pytest.approx(6 / 18)
    assert result['terminal_target_dyads'] == 1 and result['terminal_target_weight'] == 6
