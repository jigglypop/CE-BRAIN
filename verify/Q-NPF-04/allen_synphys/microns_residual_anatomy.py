"""고정된 국소 비교의 상호연결 잔차를 세포 종류와 거리로 정확히 분해한다."""
import csv
import itertools
import json
from fractions import Fraction
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base

HERE = base.HERE
CONTRACT = HERE / 'microns_residual_anatomy_contract.json'
OUTPUT = HERE / 'microns_residual_anatomy_result.json'
PAIRS = list(itertools.permutations(range(4), 2))


def main():
    dp, rp = HERE / 'microns_disjoint_rows.json', HERE / 'microns_disjoint_result.json'
    cp = HERE / 'microns_disjoint_contract.json'
    old = json.loads(cp.read_text())
    spec = dict(question='Which labelled cell-type pairs and existing distance bins account for the fixed local reciprocal residual?',
        selection='all8 stored partition/threshold combinations; joint constraints only; no new seeds, thresholds or subset selection',
        strata='unordered broad type EE/EI/II crossed with existing distance bins [0,50),[50,100),[100,200),[200,400),[400,800),[800,infinity)',
        estimator='each dyad exact mutual probability = number of admissible states containing both directions / all admissible states; sum observed-minus-probability by stratum',
        denominators='all within-block dyads; observed mutual, expected mutual, number with probability strictly between0and1; do not call fixed-zero strata evidence of absence',
        interpretation='post-result descriptive localization; metadata broad labels, not measured transmitter or physiological action; no causal attribution or per-stratum significance test',
        gate='strata partition all2022 dyads; observed and rational expectations re-sum to frozen total; root identity matches; source hashes checked',
        sources={dp.name:base.sha(dp), rp.name:base.sha(rp), cp.name:base.sha(cp),
                 'v1718_cell_info.csv':old['source_sha256']['v1718_cell_info.csv'],
                 base.SELECTED.name:old['source_sha256'][base.SELECTED.name]},
        code_sha256=base.sha(Path(__file__)), bins=[50,100,200,400,800])
    if CONTRACT.exists():
        assert json.loads(CONTRACT.read_text()) == spec
    else:
        CONTRACT.write_text(json.dumps(spec, indent=2), encoding='utf-8')
    for name, digest in spec['sources'].items():
        path = HERE / name if (HERE / name).exists() else base.DATA / name
        assert base.sha(path) == digest
    detail, totals = json.loads(dp.read_text()), json.loads(rp.read_text())
    assert totals['detail_sha256'] == base.sha(dp)
    roots = json.loads(base.SELECTED.read_text())['selected_roots']
    with (base.DATA / 'v1718_cell_info.csv').open(encoding='utf-8', newline='') as stream:
        cells = {int(r['pt_root_id']):r for r in csv.DictReader(stream)}
    xyz = np.array([[float(cells[r]['pt_position_'+axis+'_tform']) for axis in 'xyz'] for r in roots])
    labels = [{'excitatory':'E','inhibitory':'I'}[cells[r]['broad_type']] for r in roots]
    results = []
    for partition in detail['partitions']:
        strata = {(t,b):dict(dyads=0, observed=0, expected=Fraction(0), variable_probability_dyads=0) for t in ('EE','EI','II') for b in range(6)}
        residual_dyads = []
        for row in partition['rows']:
            q = row['indices']
            assert row['root_ids'] == [roots[i] for i in q]
            states = row['joint']['admissible_states']
            for u,v in itertools.combinations(range(4),2):
                i,j = q[u],q[v]
                mask = (1<<PAIRS.index((u,v))) | (1<<PAIRS.index((v,u)))
                observed = int(row['state'] & mask == mask)
                probability = Fraction(sum(s & mask == mask for s in states),len(states))
                distance = float(np.linalg.norm(xyz[i]-xyz[j]))
                key = (''.join(sorted((labels[i],labels[j]))),int(np.digitize(distance,spec['bins'])))
                s = strata[key]
                s['dyads'] += 1
                s['observed'] += observed
                s['expected'] += probability
                s['variable_probability_dyads'] += 0 < probability < 1
                if observed != probability:
                    residual_dyads.append(dict(root_ids=[roots[i],roots[j]],type=key[0],distance_um=distance,
                        observed=observed,expected_exact=str(probability),residual_exact=str(observed-probability)))
        expected = next(r for r in totals['results'] if r['constraints']=='joint' and all(r[k]==partition[k] for k in ('arm','seed','threshold')))
        assert sum(s['dyads'] for s in strata.values()) == 2022
        assert sum(s['observed'] for s in strata.values()) == expected['observed']
        assert sum(s['expected'] for s in strata.values()) == Fraction(expected['mean_exact'])
        records = []
        for (t,b),s in strata.items():
            records.append(dict(type=t,distance_bin=b,dyads=s['dyads'],observed=s['observed'],expected_exact=str(s['expected']),
                expected=float(s['expected']),residual_exact=str(s['observed']-s['expected']),residual=float(s['observed']-s['expected']),
                variable_probability_dyads=int(s['variable_probability_dyads'])))
        result = {k:partition[k] for k in ('arm','seed','threshold')}
        result.update(strata=records,residual_dyads=residual_dyads)
        results.append(result)
    output = dict(contract_sha256=base.sha(CONTRACT),partitions=results,status='EXACT_ADDITIVE_LOCALIZATION_NOT_CAUSAL_ATTRIBUTION')
    if OUTPUT.exists():
        assert json.loads(OUTPUT.read_text()) == output
    else:
        OUTPUT.write_text(json.dumps(output,indent=2),encoding='utf-8')
    for r in results:
        print(r['arm'],r['seed'],r['threshold'])
        for s in r['strata']:
            if s['observed'] or s['variable_probability_dyads']:
                print(json.dumps(s))


if __name__ == '__main__':
    main()
