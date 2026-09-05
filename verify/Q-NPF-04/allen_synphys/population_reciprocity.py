"""양방향 검사된 세포쌍의 저자 화학적 연결 표지와 상호 연결 구조를 집계한다."""
import argparse
import csv
import io
import itertools
import json
import sqlite3
from collections import Counter,defaultdict
from pathlib import Path
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DB=ROOT/'data/external/allen_synphys_r21/synphys_r2.1_small.sqlite'
CONTRACT=HERE/'population_reciprocity_contract.json'
OUTPUT=HERE/'population_reciprocity_result.json'
TABLE=DB.parent/'derived/reciprocal_dyads.csv'
SQL='''SELECT p.id,p.experiment_id,p.pre_cell_id,p.post_cell_id,p.has_synapse,p.reciprocal_id,
 e.slice_id,e.ext_id AS experiment_ext_id,e.target_region,s.species,
 a.experiment_id AS pre_experiment,b.experiment_id AS post_experiment,
 a.cell_class_nonsynaptic AS pre_class,b.cell_class_nonsynaptic AS post_class,
 a.target_layer AS pre_layer,b.target_layer AS post_layer,p.distance
 FROM pair p JOIN experiment e ON e.id=p.experiment_id JOIN slice s ON s.id=e.slice_id
 JOIN cell a ON a.id=p.pre_cell_id JOIN cell b ON b.id=p.post_cell_id
 ORDER BY p.experiment_id,p.pre_cell_id,p.post_cell_id'''


def expectation(d,k):
    return d*k*(k-1)/(2*d*(2*d-1)) if d else 0.


def fixture():
    # Enumerate every placement of k positive labels among two bidirectional dyads.
    for k in range(5):
        counts=[sum(a in c and b in c for a,b in ((0,1),(2,3))) for c in itertools.combinations(range(4),k)]
        assert abs(sum(counts)/len(counts)-expectation(2,k))<1e-12


def analyze(rows):
    lookup={(r['experiment_id'],r['pre_cell_id'],r['post_cell_id']):r for r in rows}
    assert len(lookup)==len(rows)
    dyads=[];coverage=Counter();experiments=defaultdict(list)
    for r in rows:
        assert r['pre_experiment']==r['post_experiment']==r['experiment_id']
        assert r['pre_cell_id']!=r['post_cell_id'] and r['has_synapse'] in (None,0,1)
        coverage['directed_rows']+=1
        coverage['directed_unassessed' if r['has_synapse'] is None else 'directed_assessed']+=1
        reverse=lookup.get((r['experiment_id'],r['post_cell_id'],r['pre_cell_id']))
        if reverse is None:
            coverage['missing_reverse_rows']+=1;continue
        if r['reciprocal_id'] is not None:assert r['reciprocal_id']==reverse['id']
        if r['pre_cell_id']>r['post_cell_id']:continue
        coverage['unordered_total']+=1
        if r['has_synapse'] is None or reverse['has_synapse'] is None:
            coverage['unordered_not_both_assessed']+=1;continue
        positives=r['has_synapse']+reverse['has_synapse']
        d=dict(experiment_id=r['experiment_id'],experiment_ext_id=r['experiment_ext_id'],slice_id=r['slice_id'],
            species=r['species'] or 'unknown',region=r['target_region'] or 'unknown',
            cell_a=r['pre_cell_id'],cell_b=r['post_cell_id'],pair_ab=r['id'],pair_ba=reverse['id'],
            label_ab=r['has_synapse'],label_ba=reverse['has_synapse'],positive_directions=positives,
            class_pair='|'.join(sorted([r['pre_class'] or 'unknown',r['post_class'] or 'unknown'])),
            layer_pair='|'.join(sorted([str(r['pre_layer'] or 'unknown'),str(r['post_layer'] or 'unknown')])),
            distance_m=r['distance'])
        dyads.append(d);experiments[r['experiment_id']].append(d)
    coverage['both_assessed_dyads']=len(dyads)
    per_experiment=[]
    for eid,ds in sorted(experiments.items()):
        k=sum(d['positive_directions'] for d in ds);counts=Counter(d['positive_directions'] for d in ds)
        per_experiment.append(dict(experiment_id=eid,slice_id=ds[0]['slice_id'],species=ds[0]['species'],region=ds[0]['region'],
            dyads=len(ds),positive_directions=k,neither=counts[0],one_way=counts[1],reciprocal=counts[2],
            exchangeable_label_expected_reciprocal=expectation(len(ds),k)))
    def group_summary(group):
        groups=defaultdict(list)
        for d in dyads:groups[d[group]].append(d)
        return {key:dict(dyads=len(ds),experiments=len(set(d['experiment_id'] for d in ds)),
            slices=len(set(d['slice_id'] for d in ds)),neither=sum(d['positive_directions']==0 for d in ds),
            one_way=sum(d['positive_directions']==1 for d in ds),reciprocal=sum(d['positive_directions']==2 for d in ds))
            for key,ds in sorted(groups.items())}
    species=group_summary('species')
    for key,entry in species.items():
        entry['exchangeable_label_expected_reciprocal']=sum(e['exchangeable_label_expected_reciprocal'] for e in per_experiment if e['species']==key)
    return dyads,dict(coverage=dict(coverage),species=species,regions=group_summary('region'),
        nonsynaptic_class_pairs=group_summary('class_pair'),target_layer_pairs=group_summary('layer_pair'),per_experiment=per_experiment)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    fixture()
    digest=sha(DB);assert digest=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
    spec=dict(question='How are author-labelled chemical connections distributed as neither, one-way, or reciprocal among bidirectionally assessed cell dyads?',
        objective='Move from single-pair measurement diagnosis to sampled local directed wiring structure; not whole-brain reconstruction or new independent discovery',
        selection='all database rows; primary dyad denominator requires BOTH has_synapse non-NULL; no amplitude or QC-based new selection',
        primary='counts by species; region and nonsynaptic cell class and target-layer pairs descriptive, missing labels explicit',
        reference='within each experiment, uniformly reassign fixed k positive labels to2D assessed directions; expected reciprocal D*k*(k-1)/(2D*(2D-1)); expectation only, no hypothesis test',
        limits='reference ignores cell identity, distance, class and recording detectability; slices and cells correlated; selection/detection bias; author functional labels not anatomical ground truth',
        claim_ceiling='L1 observational reanalysis of published labels, no CE-specific mechanism or whole-brain closure',
        db_sha256=digest,code_sha256=sha(Path(__file__)),sql=SQL,fixture='exhaustive two-dyad finite-population expectation')
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,ensure_ascii=False,indent=2)
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row;rows=[dict(r) for r in db.execute(SQL)]
    dyads,analysis=analyze(rows)
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(dyads[0]),lineterminator='\n');writer.writeheader();writer.writerows(dyads)
    table=stream.getvalue().encode('utf-8')
    if args.verify:
        result=json.loads(OUTPUT.read_text(encoding='utf-8'))
        assert TABLE.read_bytes()==table and sha(TABLE)==result['dyad_table_sha256']
        assert analysis==result['analysis'] and sha(CONTRACT)==result['contract_sha256']
        print('POPULATION_RECIPROCITY_REPRODUCED')
    else:
        TABLE.parent.mkdir(exist_ok=True)
        with TABLE.open('xb') as out:out.write(table)
        result=dict(contract_sha256=sha(CONTRACT),dyad_table_sha256=sha(TABLE),analysis=analysis)
        with OUTPUT.open('x',encoding='utf-8') as out:json.dump(result,out,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({k:analysis[k] for k in ('coverage','species','nonsynaptic_class_pairs')},indent=2))


if __name__=='__main__':main()
