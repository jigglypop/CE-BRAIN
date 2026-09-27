"""MaleCNS v1.0 연결체: 고정 뉴런과 방향 있는 시냅스.

뉴런 그래프 캐시(out-CSR, 행 = 보내는 뉴런, 값 = 시냅스 수), 영역별 시냅스 캐시, 주석·신경전달물질 표를
읽는다. 파일과 sha256은 자료 원장에서 가져온다(`SOURCES`). 행렬은 모두 W[받는 뉴런, 보내는 뉴런] 순서다.
"""

from __future__ import annotations

import re
from collections import Counter
from functools import cache

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
from scipy import sparse

from research import harness

SOURCES = {
    "graph": ("malecns-analysis", "neuron_graph.npz"),
    "roi": ("malecns-analysis", "neuron_roi.npz"),
    "annotations": ("malecns", "annotations.feather"),
    "transmitters": ("malecns", "neurotransmitters.feather"),
}
INHIBITORY = {"gaba", "glutamate"}  # 중심복합체의 글루탐산은 GluCl 억제로 본다
GLOMERULUS = re.compile(r"_([LR])(\d)$")


@cache
def ledger():
    """The single ledger record of each file this module reads."""
    records = {}
    for key, source in SOURCES.items():
        (records[key],) = harness.registered(*source)
    return records


def file(key):
    return harness.path(ledger()[key])


def available():
    try:
        return all(file(key).is_file() for key in SOURCES)
    except (LookupError, FileNotFoundError):
        return False


def verify():
    """Raise unless every file matches its ledger sha256."""
    harness.verify(ledger().values())


@cache
def _graph():
    with np.load(file("graph")) as z:
        n = len(z["node_ids"])
        pre_post = sparse.csr_matrix(
            (z["weight"].astype(np.float32), z["indices"], z["indptr"]), shape=(n, n))
        return z["node_ids"], z["type_code"], z["type_labels"].tolist(), pre_post


@cache
def _roi():
    with np.load(file("roi")) as z:
        return z["dyad_roi_key"], z["count"], z["roi_names"].tolist(), int(z["node_count"])


def _lookup(key, column, ids, table):
    """{body id: value} for the given bodies from one feather table."""
    rows = feather.read_table(file(table), columns=[key, column], memory_map=True)
    rows = rows.filter(pc.is_in(rows[key], value_set=pa.array(np.asarray(ids, dtype=np.int64))))
    return dict(zip(rows[key].to_pylist(), rows[column].to_pylist()))


def neurons(types):
    """Graph indices of every neuron whose cell type is in `types`, in body-id order."""
    _, code, labels, _ = _graph()
    return np.flatnonzero(np.isin(code, [labels.index(t) for t in types]))


def weights(index):
    """W[post, pre] synapse counts among the given neurons."""
    return _graph()[3][index][:, index].T.toarray().astype(float)


def weights_in(index, roi=None):
    """W[post, pre] synapse counts among the given neurons, only those in `roi` when given."""
    key, count, names, n = _roi()
    hit = np.ones(len(key), bool) if roi is None else key % len(names) == names.index(roi)
    pre, post = np.divmod(key[hit] // len(names), n)
    local = np.full(n, -1)
    local[index] = np.arange(len(index))
    keep = (local[pre] >= 0) & (local[post] >= 0)
    w = np.zeros((len(index), len(index)))
    np.add.at(w, (local[post[keep]], local[pre[keep]]), count[hit][keep])
    return w


def cell_types(index):
    _, code, labels, _ = _graph()
    return [labels[c] for c in code[index]]


def instances(index):
    ids = _graph()[0][index]
    lookup = _lookup("bodyId", "instance", ids, "annotations")
    return [lookup.get(int(b)) or "" for b in ids]


def glomerulus(instance):
    """PB glomerulus of an instance such as 'EPG(PB08)_L4' -> ('L', 4); None if absent."""
    match = GLOMERULUS.search(instance)
    return (match.group(1), int(match.group(2))) if match else None


def signs(index):
    """+1 or −1 per neuron from the majority consensus transmitter of its cell type."""
    ids, kinds = _graph()[0][index], cell_types(index)
    nt = _lookup("body", "consensus_nt", ids, "transmitters")
    votes = {}
    for body, kind in zip(ids, kinds):
        value = nt.get(int(body), "unclear")
        if value != "unclear":
            votes.setdefault(kind, Counter())[value] += 1
    majority = {kind: count.most_common(1)[0][0] for kind, count in votes.items()}
    return np.array([-1.0 if majority.get(kind) in INHIBITORY else 1.0 for kind in kinds])
