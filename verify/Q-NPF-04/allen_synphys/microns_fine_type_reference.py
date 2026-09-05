"""기존 국소 허용 그래프에 세부 세포형 및 교정 전략 조건을 추가한다."""
import csv
import json
from collections import Counter
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base
from microns_exact_quartets import universe, PAIRS
from microns_disjoint_reference import distribution

HERE = base.HERE
CONTRACT = HERE / 'microns_fine_type_contract.json'
OUTPUT = HERE / 'microns_fine_type_result.json'
DETAIL = HERE / 'microns_fine_type_rows.json'


def signature(a, labels, bins):
    return Counter((labels[u],labels[v],int(bins[u,v])) for u,v in PAIRS if a[u,v])


def main():
    dp, rp = HERE/'microns_disjoint_rows.json', HERE/'microns_disjoint_result.json'
    original = json.loads(base.CONTRACT.read_text())
    spec = dict(question='Does fixed local residual persist under finer metadata conditioning, and how much support remains?',
        scope='all8 prior partition/threshold combinations; retain all337 blocks, no repartition or exclusion',
        nested_conditions=['old joint plus ordered (broad_type,cell_type) pair x existing distance bin counts',
            'preceding condition refined with each endpoint strategy_axon and strategy_dendrite'],
        missing='three selected cells with empty cell_type treated as explicit MISSING category; no imputation',
        endpoints='exact old and new means, inclusive upper tails descriptive only, variable and unique graph counts, all metadata counts',
        interpretation='post-hoc sensitivity, not cell-type causality or missing-synapse correction; strategy labels not completeness guarantees; loss of support is reported',
        gates='new admissible set nested in old, observed included, every row root identity, source hashes, exact distribution bookkeeping',
        sources={dp.name:base.sha(dp),rp.name:base.sha(rp),'v1718_cell_info.csv':original['source_sha256']['v1718_cell_info.csv'],
                 base.SELECTED.name:original['source_sha256'][base.SELECTED.name]},
        code_sha256=base.sha(Path(__file__)),enumeration_sha256=base.sha(HERE/'microns_exact_quartets.py'),
        distribution_sha256=base.sha(HERE/'microns_disjoint_reference.py'),base_sha256=base.sha(Path(base.__file__)))
    if CONTRACT.exists():
        assert json.loads(CONTRACT.read_text())==spec
    else:
        CONTRACT.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    for name,digest in spec['sources'].items():
        p=HERE/name if (HERE/name).exists() else base.DATA/name
        assert base.sha(p)==digest
    detail,prior=json.loads(dp.read_text()),json.loads(rp.read_text())
    assert prior['detail_sha256']==base.sha(dp)
    roots=json.loads(base.SELECTED.read_text())['selected_roots']
    with (base.DATA/'v1718_cell_info.csv').open(encoding='utf-8',newline='') as stream:
        cells={int(r['pt_root_id']):r for r in csv.DictReader(stream)}
    selected=[cells[r] for r in roots]
    metadata={k:dict(Counter(r[k] or 'MISSING' for r in selected)) for k in ('cell_type','mtype','meso_type','status_axon','status_dendrite','strategy_axon','strategy_dendrite')}
    counts,categories=base.load_graph()
    graphs,_,reciprocal=universe()
    results,details=[],[]
    for partition in detail['partitions']:
        rows=[]
        for row in partition['rows']:
            q=row['indices'];assert row['root_ids']==[roots[i] for i in q]
            a=counts[np.ix_(q,q)]>=partition['threshold'];assert np.array_equal(a,graphs[row['state']])
            bins=categories[np.ix_(q,q)]%6
            labels=[(selected[i]['broad_type'],selected[i]['cell_type'] or 'MISSING') for i in q]
            strategies=[label+(selected[i]['strategy_axon'] or 'MISSING',selected[i]['strategy_dendrite'] or 'MISSING') for i,label in zip(q,labels)]
            oldids=row['joint']['admissible_states']
            target=signature(a,labels,bins)
            fine=[s for s in oldids if signature(graphs[s],labels,bins)==target]
            target=signature(a,strategies,bins)
            quality=[s for s in fine if signature(graphs[s],strategies,bins)==target]
            assert row['state'] in quality and set(quality)<=set(fine)<=set(oldids)
            out=dict(indices=q,root_ids=row['root_ids'],state=row['state'],observed=row['observed'])
            for kind,ids in [('fine_type',fine),('fine_type_strategy',quality)]:
                out[kind]=dict(admissible_states=ids,histogram={str(k):v for k,v in sorted(Counter(map(int,reciprocal[ids])).items())})
            rows.append(out)
        identity={k:partition[k] for k in ('arm','seed','threshold')}
        details.append(dict(**identity,rows=rows))
        before=next(r for r in prior['results'] if r['constraints']=='joint' and all(r[k]==identity[k] for k in identity))
        for kind in ('fine_type','fine_type_strategy'):
            results.append(dict(**identity,constraints=kind,old_joint_mean=before['mean'],old_variable=before['variable_quartets'],**distribution(rows,kind)))
    data=dict(contract_sha256=base.sha(CONTRACT),partitions=details)
    if DETAIL.exists():
        assert json.loads(DETAIL.read_text())==data
    else:
        DETAIL.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    output=dict(contract_sha256=base.sha(CONTRACT),detail_sha256=base.sha(DETAIL),metadata=metadata,results=results,
                status='NESTED_METADATA_SENSITIVITY_NOT_MISSINGNESS_CORRECTION')
    if OUTPUT.exists():
        assert json.loads(OUTPUT.read_text())==output
    else:
        OUTPUT.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k not in ('histogram','total_combinations')} for r in results],indent=2))


if __name__=='__main__':
    main()
