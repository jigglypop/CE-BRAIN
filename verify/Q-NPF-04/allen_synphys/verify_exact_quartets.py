"""독립 12비트 표현으로 국소 열거 결과의 완전성을 다시 확인한다."""
import itertools
import json
from collections import Counter
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base

HERE = Path(__file__).resolve().parent
source = HERE / 'microns_exact_quartets_rows.json'
rows = json.loads(source.read_text())['rows']
counts, categories = base.load_graph()
pairs = list(itertools.permutations(range(4), 2))
bits = ((np.arange(4096)[:, None] >> np.arange(12)) & 1).astype(np.int8)
incoming = np.column_stack([bits[:, [k for k, p in enumerate(pairs) if p[1] == v]].sum(axis=1) for v in range(4)])
outgoing = np.column_stack([bits[:, [k for k, p in enumerate(pairs) if p[0] == v]].sum(axis=1) for v in range(4)])
mutual = sum(bits[:, pairs.index((u, v))] * bits[:, pairs.index((v, u))] for u, v in itertools.combinations(range(4), 2))
chosen = set(map(int, np.random.default_rng(2026090508).choice(len(rows), 64, replace=False)))
chosen.update(i for i, r in enumerate(rows) if r['joint']['min'] != r['joint']['max'])
for i in sorted(chosen):
    row = rows[i]
    ix = np.ix_(row['indices'], row['indices'])
    a, cat = counts[ix] >= row['threshold'], categories[ix]
    mask = np.all(incoming == a.sum(axis=0), axis=1) & np.all(outgoing == a.sum(axis=1), axis=1)
    assert np.flatnonzero(mask).tolist() == row['degrees']['admissible_states']
    for category in set(map(int, cat[~np.eye(4, dtype=bool)])):
        positions = [k for k, p in enumerate(pairs) if cat[p] == category]
        mask &= bits[:, positions].sum(axis=1) == sum(int(a[pairs[k]]) for k in positions)
    candidates = np.flatnonzero(mask)
    assert candidates.tolist() == row['joint']['admissible_states']
    assert int(mutual[candidates].sum()) == row['joint']['reciprocal_sum']
    assert int(mutual[row['state']]) == row['observed']
variable = [r for r in rows if r['arm'] == 'nearby' and r['threshold'] == 1 and r['joint']['min'] != r['joint']['max']]
cell_occurrences = Counter(v for r in variable for v in r['indices'])
dyads = Counter(p for r in variable for p in itertools.combinations(r['indices'], 2))
result = dict(source_sha256=base.sha(source), verifier_sha256=base.sha(Path(__file__)),
              exhaustive_rechecks=len(chosen), all_joint_variable_quartets_included=True,
              nearby_threshold1_joint_variable_quartets=len(variable), unique_cells=len(cell_occurrences),
              max_cell_occurrences=max(cell_occurrences.values()), unique_dyads=len(dyads),
              max_dyad_occurrences=max(dyads.values()), status='INDEPENDENT_BIT_ENUMERATION_MATCH')
out = HERE / 'microns_exact_quartets_verification.json'
if out.exists():
    assert json.loads(out.read_text()) == result
else:
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
