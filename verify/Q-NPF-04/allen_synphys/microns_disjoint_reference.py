"""겹치지 않는 네 세포 묶음의 정확한 조건부 합계 분포. 탐색 분석."""
import csv
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base
from microns_exact_quartets import universe, PAIRS

HERE = base.HERE
CONTRACT = HERE / 'microns_disjoint_contract.json'
OUTPUT = HERE / 'microns_disjoint_result.json'
DETAIL = HERE / 'microns_disjoint_rows.json'


def convolve(left, right):
    result = Counter()
    for x, nx in left.items():
        for y, ny in right.items():
            result[x + y] += nx * ny
    return result


def distribution(rows, kind):
    dist = Counter({0: 1})
    product = 1
    expected = Fraction(0)
    for r in rows:
        hist = Counter({int(k): v for k, v in r[kind]['histogram'].items()})
        total = sum(hist.values())
        product *= total
        expected += Fraction(sum(k * v for k, v in hist.items()), total)
        dist = convolve(dist, hist)
    assert sum(dist.values()) == product
    assert Fraction(sum(k * v for k, v in dist.items()), product) == expected
    observed = sum(r['observed'] for r in rows)
    assert observed in dist
    def quantile(numerator, denominator):
        cumulative = 0
        for x, count in sorted(dist.items()):
            cumulative += count
            if cumulative * denominator >= numerator * product:
                return x
    tail = Fraction(sum(v for k, v in dist.items() if k >= observed), product)
    return dict(observed=observed, mean=float(expected), mean_exact=str(expected),
                residual_exact=str(observed - expected), upper_tail_exact=str(tail), upper_tail=float(tail),
                central95_reference_range=[quantile(1, 40), quantile(39, 40)],
                variable_quartets=sum(len(r[kind]['histogram']) > 1 for r in rows),
                unique_graph_quartets=sum(sum(r[kind]['histogram'].values()) == 1 for r in rows),
                total_combinations=str(product), histogram={str(k): str(v) for k, v in sorted(dist.items())})


def main():
    spec = dict(question='Remove overlapping quartet counts and calculate exact conditional sum distribution',
        design='one primary nearby partition seed2026090509, sensitivity nearby seeds2026090510 and2026090511, uniform partition seed2026090509; all reported, no selection of best result',
        partition='seeded permutation of all1348 selected indices; nearby:next unused anchor plus nearest3 unused somata, ties by selected index; uniform:consecutive fours of permutation',
        conditioning='all between-block edges fixed; within each block exact in/out degrees, with or without exact ordered broad-type x distance-bin counts',
        null='uniform over Cartesian product of admissible block graphs; factorization follows stipulated product space, not biological independence',
        inference='same previously inspected specimen; exploratory exact inclusive upper tail P(T>=observed), no confirmatory rejection threshold or independent replication claim; central95 range is null reference not confidence interval',
        thresholds=[1, 3], endpoints='all337 blocks, exact sum distribution and rational mean/tail, fixed and variable counts, partition sensitivity',
        gate='each cell exactly once; observed graph in each admissible set; convolution counts and mean match product and sum of local means; boundary remains fixed',
        limitation='strong per-block conditioning; four-node interiors cover only selected dyads, may freeze statistic; no global-null or causal claim',
        source_sha256=json.loads(base.CONTRACT.read_text())['source_sha256'],
        code_sha256=base.sha(Path(__file__)), enumeration_sha256=base.sha(HERE / 'microns_exact_quartets.py'),
        base_sha256=base.sha(Path(base.__file__)), numpy=np.__version__)
    if CONTRACT.exists():
        assert json.loads(CONTRACT.read_text()) == spec
    else:
        CONTRACT.write_text(json.dumps(spec, indent=2), encoding='utf-8')
    for name, digest in spec['source_sha256'].items():
        p = HERE / name if (HERE / name).exists() else base.DATA / name
        assert base.sha(p) == digest
    counts, categories = base.load_graph()
    roots = json.loads(base.SELECTED.read_text())['selected_roots']
    with (base.DATA / 'v1718_cell_info.csv').open(encoding='utf-8', newline='') as stream:
        cells = {int(r['pt_root_id']): r for r in csv.DictReader(stream)}
    xyz = np.array([[float(cells[r]['pt_position_' + axis + '_tform']) for axis in 'xyz'] for r in roots])
    assert len(roots) == 1348 and np.isfinite(xyz).all()
    graphs, index, reciprocal = universe()
    details, results = [], []
    for arm, seed in [('nearby', 2026090509), ('nearby', 2026090510), ('nearby', 2026090511), ('uniform', 2026090509)]:
        order = list(map(int, np.random.default_rng(seed).permutation(len(roots))))
        blocks = []
        remaining = set(order)
        for anchor in order:
            if anchor not in remaining:
                continue
            if arm == 'uniform':
                q = [i for i in order if i in remaining][:4]
            else:
                candidates = sorted(remaining - {anchor})
                d = ((xyz[candidates] - xyz[anchor]) ** 2).sum(axis=1)
                neighbors = np.lexsort((np.array(candidates), d))[:3]
                q = [anchor] + [candidates[k] for k in neighbors]
            assert len(q) == 4
            blocks.append(sorted(q))
            remaining.difference_update(q)
        assert not remaining and sorted(i for q in blocks for i in q) == list(range(len(roots)))
        for threshold in spec['thresholds']:
            rows = []
            for q in blocks:
                a, c = counts[np.ix_(q, q)] >= threshold, categories[np.ix_(q, q)]
                state = sum(1 << bit for bit, p in enumerate(PAIRS) if a[p])
                ids = index[tuple(a.sum(axis=0)) + tuple(a.sum(axis=1))]
                target = np.bincount(c[a], minlength=24)
                joint = [s for s in ids if np.array_equal(np.bincount(c[graphs[s]], minlength=24), target)]
                assert state in joint
                row = dict(indices=q, root_ids=[roots[i] for i in q], state=state, observed=int(reciprocal[state]))
                for kind, candidates in [('degrees', ids), ('joint', joint)]:
                    row[kind] = dict(admissible_states=list(map(int, candidates)),
                                     histogram={str(k): v for k, v in sorted(Counter(map(int, reciprocal[candidates])).items())})
                rows.append(row)
            details.append(dict(arm=arm, seed=seed, threshold=threshold, rows=rows))
            for kind in ('degrees', 'joint'):
                results.append(dict(arm=arm, seed=seed, threshold=threshold, constraints=kind, quartets=len(rows), **distribution(rows, kind)))
    detail = dict(contract_sha256=base.sha(CONTRACT), partitions=details)
    if DETAIL.exists():
        assert json.loads(DETAIL.read_text()) == detail
    else:
        DETAIL.write_text(json.dumps(detail, separators=(',', ':')), encoding='utf-8')
    result = dict(contract_sha256=base.sha(CONTRACT), detail_sha256=base.sha(DETAIL), results=results,
                  status='EXACT_EXPLORATORY_PRODUCT_NULL_NOT_INDEPENDENT_REPLICATION')
    if OUTPUT.exists():
        assert json.loads(OUTPUT.read_text()) == result
    else:
        OUTPUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k, v in r.items() if k not in ('histogram', 'total_combinations')} for r in results], indent=2))


if __name__ == '__main__':
    main()
