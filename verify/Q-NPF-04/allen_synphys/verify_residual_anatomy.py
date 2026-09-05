"""행렬 표현으로 모든 세포 종류·거리별 분해를 원 그래프 및 허용 상태와 대조한다."""
import json
from fractions import Fraction
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base
from microns_exact_quartets import universe

HERE = Path(__file__).resolve().parent
rp = HERE / 'microns_residual_anatomy_result.json'
result = json.loads(rp.read_text())
detail = json.loads((HERE / 'microns_disjoint_rows.json').read_text())
counts, categories = base.load_graph()
graphs, _, _ = universe()
checked = 0
for output, partition in zip(result['partitions'], detail['partitions']):
    assert all(output[k] == partition[k] for k in ('arm','seed','threshold'))
    sums = {(t,b):[0,Fraction(0)] for t in ('EE','EI','II') for b in range(6)}
    for row in partition['rows']:
        ix = np.ix_(row['indices'],row['indices'])
        a, cat = counts[ix] >= partition['threshold'], categories[ix]
        assert np.array_equal(a,graphs[row['state']])
        candidates = graphs[row['joint']['admissible_states']]
        mutual = candidates & candidates.transpose(0,2,1)
        for u in range(4):
            for v in range(u+1,4):
                typ = {0:'EE',1:'EI',2:'EI',3:'II'}[int(cat[u,v]//6)]
                key = (typ,int(cat[u,v]%6))
                sums[key][0] += int(a[u,v] and a[v,u])
                sums[key][1] += Fraction(int(mutual[:,u,v].sum()),len(candidates))
                checked += 1
    for row in output['strata']:
        observed, expected = sums[(row['type'],row['distance_bin'])]
        assert observed == row['observed'] and expected == Fraction(row['expected_exact'])
receipt = dict(result_sha256=base.sha(rp),verifier_sha256=base.sha(Path(__file__)),
    dyads_checked=checked,strata_checked=18*len(result['partitions']),
    scope='all observed dyads from source adjacency and exact mutual means from matrix representation; categories from frozen graph loader',
    status='ALL_ADDITIVE_STRATA_MATCH')
out = HERE / 'microns_residual_anatomy_verification.json'
if out.exists():
    assert json.loads(out.read_text()) == receipt
else:
    out.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
