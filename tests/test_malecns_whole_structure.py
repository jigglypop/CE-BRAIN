"""Independent tiny-graph checks, not biological validation."""

import importlib.util
import itertools
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "malecns_whole_structure", Path(__file__).resolve().parents[1] / "verify/MaleCNS/whole_structure.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_partition_keeps_glia_missing_and_unknown_separate():
    ids, codes, labels = module.annotation_partition(
        np.array([4, 1, 2, 3]), [None, "Traced", "Glia", None], [None, "A", None, "B"])
    assert ids.tolist() == [1, 2, 3, 4]
    assert [labels[c] for c in codes] == ["A", module.GLIA, "B", module.UNCLASSIFIED]
    assert module.UNKNOWN in labels
    with pytest.raises(ValueError, match="duplicate"):
        module.annotation_partition(np.array([1, 1]), [None] * 2, ["A"] * 2)


def test_streaming_matches_scalar_reference_with_all_boundary_directions():
    ids, codes, labels = module.annotation_partition(
        np.array([1, 2, 3, 4]), ["Traced", "Traced", "Glia", None], ["A", "B", None, None])
    edges = [(1, 2, 3), (1, 9, 7), (9, 1, 5), (9, 10, 11), (3, 4, 2), (2, 2, 13), (1, 2, 4)]
    acc = module.CategoryAccumulator(ids, codes, labels)
    for chunk in (edges[:3], edges[3:]):
        acc.add(*(np.array(a) for a in zip(*chunk)))
    expected = np.zeros_like(acc.category_weight)
    per_neuron = np.zeros_like(acc.out_weight)
    mapping = {int(body): int(code) for body, code in zip(ids, codes)}
    for pre, post, w in edges:
        a, b = mapping.get(pre, labels.index(module.UNKNOWN)), mapping.get(post, labels.index(module.UNKNOWN))
        expected[a, b] += w
        if pre in mapping:
            per_neuron[list(ids).index(pre), b] += w
    assert np.array_equal(expected, acc.category_weight)
    assert np.array_equal(per_neuron, acc.out_weight)
    assert acc.self_rows == 1 and acc.self_weight == 13
    assert acc.rows == 7 and acc.weight == 45
    acc.validate()
    acc.out_weight[0, 0] += 1
    with pytest.raises(ValueError, match="conservation"):
        acc.validate()


@pytest.mark.parametrize("pre,post,weight", [([-1], [1], [2]), ([1], [2], [0]),
                                           ([1.0], [2], [1]), ([1, 2], [2], [1])])
def test_invalid_batches_fail(pre, post, weight):
    ids, codes, labels = module.annotation_partition(np.array([1]), ["Traced"], ["A"])
    with pytest.raises(ValueError):
        module.CategoryAccumulator(ids, codes, labels).add(pre, post, weight)


def test_lumpable_and_nonlumpable_counts_and_zero_degree():
    closed = module.closure_dispersion(np.array([[1, 2], [2, 4], [0, 0]]))
    assert closed["observed"] == 0
    assert closed["positive_sources"] == 2 and closed["zero_sources"] == 1
    open_result = module.closure_dispersion(np.array([[3, 0], [0, 3]]))
    assert open_result["observed"] == pytest.approx(.5)
    witness = module.closure_witness(np.array([[3, 0], [0, 3]]), np.array([5, 9]), ["A", "B"], 1)
    assert witness["total_variation"] == 1
    assert module.closure_dispersion(np.zeros((2, 2), dtype=np.int64))["observed"] is None


def test_stub_null_expectation_matches_exhaustive_fixed_margin_assignments():
    observed = []
    expected = []
    # Three source degrees 1, 2, 3; target totals 2 and 4. Every distinct assignment is equiprobable.
    for first_category in itertools.combinations(range(6), 2):
        stubs = np.ones(6, dtype=int)
        stubs[list(first_category)] = 0
        counts = np.array([np.bincount(a, minlength=2) for a in (stubs[:1], stubs[1:3], stubs[3:])])
        result = module.closure_dispersion(counts)
        observed.append(result["observed"])
        expected.append(result["null_expectation"])
    assert np.mean(observed) == pytest.approx(expected[0], abs=1e-14)
    assert max(expected) - min(expected) == 0


def test_integer_accumulation_does_not_round_above_float_exact_range():
    ids, codes, labels = module.annotation_partition(np.array([1, 2]), [None, None], ["A", "B"])
    acc = module.CategoryAccumulator(ids, codes, labels)
    weight = 2**53 + 1
    acc.add(np.array([1]), np.array([2]), np.array([weight], dtype=np.int64))
    assert int(acc.category_weight.sum()) == weight
    acc.validate()
