"""Independent tiny-graph checks for the neuron graph cache, not biological validation."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "malecns_neuron_graph", Path(__file__).resolve().parents[1] / "verify/MaleCNS/neuron_graph.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_scope_drops_only_glia_and_codes_missing_labels():
    ids, superclass, sc_labels, type_code, type_labels = module.node_scope(
        [7, 3, 5, 9], ["Traced", "Glia", None, "Traced"], ["b", None, None, "a"], ["T1", None, "T1", None])
    assert ids.tolist() == [5, 7, 9]
    assert [sc_labels[c] if c >= 0 else None for c in superclass] == [None, "b", "a"]
    assert [type_labels[c] if c >= 0 else None for c in type_code] == ["T1", "T1", None]
    with pytest.raises(ValueError, match="duplicate"):
        module.node_scope([1, 1], ["Traced"] * 2, ["a"] * 2, ["t"] * 2)


def test_collector_matches_scalar_reference_and_conserves_boundary():
    ids = np.array([10, 20, 30])
    rows = [(10, 20, 3), (20, 10, 1), (10, 99, 5), (98, 30, 2), (30, 30, 4), (97, 96, 8), (20, 30, 6)]
    collector = module.EdgeCollector(ids)
    for chunk in (rows[:4], rows[4:]):
        collector.add(*(np.array(column) for column in zip(*chunk)))
    indptr, indices, weight = collector.finish()
    dense = np.zeros((3, 3), dtype=np.int64)
    for pre, post, w in rows:
        if pre in ids and post in ids:
            dense[list(ids).index(pre), list(ids).index(post)] += w
    rebuilt = np.zeros_like(dense)
    for i in range(3):
        rebuilt[i, indices[indptr[i]:indptr[i + 1]]] = weight[indptr[i]:indptr[i + 1]]
    assert np.array_equal(rebuilt, dense)
    assert collector.out_boundary.tolist() == [5, 0, 0]
    assert collector.in_boundary.tolist() == [0, 0, 2]
    assert collector.out_total.tolist() == [8, 7, 4] and collector.weight_sum == 29
    keys = module.dyad_keys(indptr, indices, 3)
    assert np.all(keys[1:] > keys[:-1])


def test_duplicate_dyads_and_invalid_weights_fail():
    collector = module.EdgeCollector(np.array([1, 2]))
    collector.add(np.array([1, 1]), np.array([2, 2]), np.array([1, 1]))
    with pytest.raises(ValueError, match="duplicate"):
        collector.finish()
    with pytest.raises(ValueError):
        module.EdgeCollector(np.array([1, 2])).add(np.array([1]), np.array([2]), np.array([0]))


def test_prebuilt_reader_round_trips_incoming_csr(tmp_path, monkeypatch):
    node_ids = np.array([5, 6, 7])
    # incoming CSR: target 0 <- {1}, target 2 <- {0, 1}
    indptr = np.array([0, 1, 1, 3], dtype=np.uint64)
    sources = np.array([1, 0, 1], dtype=np.uint32)
    synapses = np.array([4, 2, 9], dtype=np.uint32)
    signs = np.array([1, -1, 1], dtype=np.int8)
    header = b"CHKCSR01" + np.array([1, 3, 3, 0], dtype=np.uint32).tobytes()
    (tmp_path / "graph.bin").write_bytes(header + indptr.tobytes() + sources.tobytes()
                                         + synapses.tobytes() + signs.tobytes())
    np.savetxt(tmp_path / "node_ids.txt", node_ids, fmt="%d")
    monkeypatch.setitem(module.PREBUILT, "full", tmp_path)
    keys = np.array([0 * 3 + 2, 1 * 3 + 0, 1 * 3 + 2], dtype=np.int64)
    weight = np.array([2, 4, 9], dtype=np.uint32)
    report = module.compare_prebuilt("full", node_ids, keys, weight, np.zeros(3, dtype=np.int32))
    assert report["dyads_equal"] and report["synapses_equal"] and report["sources_with_mixed_sign"] == 0
    report = module.compare_prebuilt("full", node_ids, keys, weight + 1, np.zeros(3, dtype=np.int32))
    assert report["dyads_equal"] and not report["synapses_equal"]
