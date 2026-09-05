"""실제 세포 4개 묶음의 내부 연결을 경계 고정 조건에서 정확히 열거한다."""
import csv
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base

HERE = base.HERE
CONTRACT = HERE / 'microns_exact_quartets_contract.json'
OUTPUT = HERE / 'microns_exact_quartets_result.json'
DETAIL = HERE / 'microns_exact_quartets_rows.json'
PAIRS = [(u, v) for u in range(4) for v in range(4) if u != v]


def universe():
    graphs = np.zeros((4096, 4, 4), dtype=bool)
    for bit, (u, v) in enumerate(PAIRS):
        graphs[:, u, v] = (np.arange(4096) & (1 << bit)) != 0
    degree_index = defaultdict(list)
    for state, a in enumerate(graphs):
        degree_index[tuple(a.sum(axis=0)) + tuple(a.sum(axis=1))].append(state)
    reciprocal = (graphs & graphs.transpose(0, 2, 1)).sum(axis=(1, 2)) // 2
    assert len(degree_index) == 2656
    return graphs, degree_index, reciprocal


def summaries(rows):
    result = []
    for arm in ('uniform', 'nearby'):
        for threshold in (1, 3):
            selected = [r for r in rows if r['arm'] == arm and r['threshold'] == threshold]
            for kind in ('degrees', 'joint'):
                observed = sum(r['observed'] for r in selected)
                expected = sum((Fraction(r[kind]['reciprocal_sum'], r[kind]['count']) for r in selected), Fraction(0))
                variable = [r for r in selected if r[kind]['min'] != r[kind]['max']]
                result.append(dict(arm=arm, threshold=threshold, constraints=kind, quartets=len(selected),
                    unique_graphs=sum(r[kind]['count'] == 1 for r in selected), statistic_variable=len(variable),
                    observed_occurrences=observed, expected_occurrences_exact=str(expected), expected_occurrences=float(expected),
                    residual_exact=str(Fraction(observed) - expected), residual=float(Fraction(observed) - expected),
                    variable_positive=sum(r['observed'] * r[kind]['count'] > r[kind]['reciprocal_sum'] for r in variable),
                    variable_negative=sum(r['observed'] * r[kind]['count'] < r[kind]['reciprocal_sum'] for r in variable),
                    variable_zero=sum(r['observed'] * r[kind]['count'] == r[kind]['reciprocal_sum'] for r in variable)))
    return result


def main():
    spec = dict(question='Exact local reciprocal reference without swap reachability or mixing assumptions',
        scope='existing1348 selected MICrONS cells; all4096 directed loop-free labelled four-node graphs',
        selection='uniform:2048 distinct sorted quartets sampled without node replacement per quartet, fixed seed2026090507; nearby:each cell plus nearest3 selected somata, ties by selected index, sorted deduplicated; selection independent of edges',
        conditioning='hold every edge with any endpoint outside quartet fixed; preserve quartet internal in/out degrees; nested joint condition also preserves ordered broad-type x distance-bin edge counts',
        model='uniform over all exact admissible internal graphs, separately for each quartet; a stipulated local reference, not independent biological replicates',
        thresholds=[1, 3], distance_bins_um=[50, 100, 200, 400, 800],
        endpoints='all quartet counts including unique graph and statistic-fixed cases; exact rational expectation; summed observed-minus-expected, and signs among variable-statistic quartets',
        interpretation='overlapping quartets repeatedly count cells/dyads; aggregate is quartet-occurrence statistic, not global reciprocal count; no p-values, convergence claim or causal interpretation',
        gate='observed state must be admissible; joint subset of degree-only; original sources hash match; enumerate before interpretation; zero variable quartets is no information, not biological null',
        source_sha256=json.loads(base.CONTRACT.read_text())['source_sha256'],
        base_code_sha256=base.sha(Path(base.__file__)), code_sha256=base.sha(Path(__file__)), numpy=np.__version__)
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
    n = len(roots)
    assert n == 1348 and np.isfinite(xyz).all()
    rng = np.random.default_rng(2026090507)
    uniform = set()
    while len(uniform) < 2048:
        uniform.add(tuple(sorted(map(int, rng.choice(n, 4, replace=False)))))
    nearby = set()
    for i in range(n):
        d = ((xyz - xyz[i]) ** 2).sum(axis=1)
        d[i] = np.inf
        neighbors = np.lexsort((np.arange(n), d))[:3]
        nearby.add(tuple(sorted([i] + list(map(int, neighbors)))))
    graphs, index, reciprocal = universe()
    rows = []
    for arm, quartets in [('uniform', uniform), ('nearby', nearby)]:
        for threshold in spec['thresholds']:
            for q in sorted(quartets):
                ix = np.ix_(q, q)
                a, c = counts[ix] >= threshold, categories[ix]
                state = sum(1 << bit for bit, p in enumerate(PAIRS) if a[p])
                ids = index[tuple(a.sum(axis=0)) + tuple(a.sum(axis=1))]
                target = np.bincount(c[a], minlength=24)
                joint = [s for s in ids if np.array_equal(np.bincount(c[graphs[s]], minlength=24), target)]
                assert state in joint and set(joint) <= set(ids)
                row = dict(arm=arm, threshold=threshold, indices=list(q), root_ids=[roots[i] for i in q],
                           state=state, observed=int(reciprocal[state]))
                for kind, candidates in [('degrees', ids), ('joint', joint)]:
                    values = reciprocal[candidates]
                    row[kind] = dict(count=len(candidates), reciprocal_sum=int(values.sum()),
                                     min=int(values.min()), max=int(values.max()), admissible_states=list(map(int, candidates)))
                rows.append(row)
    detail = dict(contract_sha256=base.sha(CONTRACT), rows=rows)
    if DETAIL.exists():
        assert json.loads(DETAIL.read_text()) == detail
    else:
        DETAIL.write_text(json.dumps(detail, separators=(',', ':')), encoding='utf-8')
    result = dict(contract_sha256=base.sha(CONTRACT), detail_sha256=base.sha(DETAIL),
                  arm_quartet_overlap=len(uniform & nearby), summary=summaries(rows),
                  status='EXACT_LOCAL_CONDITIONAL_REFERENCE_NOT_GLOBAL_NULL_OR_CAUSAL_PROOF')
    if OUTPUT.exists():
        assert json.loads(OUTPUT.read_text()) == result
    else:
        OUTPUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
