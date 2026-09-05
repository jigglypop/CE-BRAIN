"""관측 위치·세포별 차수·종류별 방향·거리별 양성 수를 동시에 보존한다."""
import argparse
import csv
import itertools
import json
import sqlite3
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from population_reciprocity import DB,TABLE,HERE,sha
from reciprocity_stratified_reference import distance_bin

DEGREE=HERE/'reciprocity_fixed_degrees_result.json'
CONTRACT=HERE/'reciprocity_joint_contract.json'
OUTPUT=HERE/'reciprocity_joint_result.json'


def graphs(row):
    n=len(row['cell_ids']);masks=row['allowed_destination_masks'];out=row['outgoing']
    def visit(i,remaining,chosen):
        if i==n:
            if not any(remaining):yield tuple(chosen)
            return
        choices=[j for j in range(n) if masks[i]&(1<<j) and remaining[j]>0]
        for selected in itertools.combinations(choices,out[i]):
            nxt=list(remaining)
            for j in selected:nxt[j]-=1
            if any(nxt[j]>sum(bool(masks[k]&(1<<j)) for k in range(i+1,n)) for j in range(n)):continue
            yield from visit(i+1,nxt,chosen+[sum(1<<j for j in selected)])
    yield from visit(0,row['incoming'],[])


def run():
    degree=json.loads(DEGREE.read_text(encoding='utf-8'))
    groups=defaultdict(list)
    with TABLE.open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):groups[int(row['experiment_id'])].append(row)
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        classes={r[0]:r[1] or 'unknown' for r in db.execute('SELECT id,cell_class_nonsynaptic FROM cell')}
    results=[]
    for row in degree['analysis']['per_experiment']:
        ids=row['cell_ids'];index={v:i for i,v in enumerate(ids)};n=len(ids)
        categories={};observed=[0]*n;target=Counter()
        for d in groups[row['experiment_id']]:
            a=index[int(d['cell_a'])];b=index[int(d['cell_b'])];dist=distance_bin(d['distance_m'])
            for pre,post,label in ((a,b,int(d['label_ab'])),(b,a,int(d['label_ba']))):
                category=(classes[ids[pre]],classes[ids[post]],dist)
                categories[pre,post]=category
                if label:target[category]+=1;observed[pre]|=1<<post
        histogram=Counter();seen=0;found=False
        for adjacency in graphs(row):
            seen+=1;counts=Counter(categories[a,b] for a in range(n) for b in range(n) if adjacency[a]&(1<<b))
            if counts!=target:continue
            found |= adjacency==tuple(observed)
            reciprocal=sum(bool(adjacency[a]&(1<<b) and adjacency[b]&(1<<a)) for a in range(n) for b in range(a+1,n))
            histogram[reciprocal]+=1
        assert seen==row['admissible_graphs'] and found
        total=sum(histogram.values());expected=Fraction(sum(k*v for k,v in histogram.items()),total)
        results.append(dict(experiment_id=row['experiment_id'],slice_id=row['slice_id'],species=row['species'],
            dyads=row['dyads'],degree_graphs=seen,joint_graphs=total,observed=row['observed_reciprocal'],
            expected=float(expected),expected_numerator=expected.numerator,expected_denominator=expected.denominator,
            histogram={str(k):v for k,v in sorted(histogram.items())},variable=len(histogram)>1))
    summaries={};slice_rows=[]
    for species in sorted(set(r['species'] for r in results)):
        rows=[r for r in results if r['species']==species];slices=defaultdict(lambda:dict(observed=0,expected=Fraction(),experiments=0))
        for r in rows:
            s=slices[r['slice_id']];s['observed']+=r['observed'];s['expected']+=Fraction(r['expected_numerator'],r['expected_denominator']);s['experiments']+=1
        residual=sum((Fraction(s['observed'])-s['expected'] for s in slices.values()),Fraction())
        changed=[]
        for sid,s in sorted(slices.items()):
            delta=Fraction(s['observed'])-s['expected'];remaining=residual-delta
            slice_rows.append(dict(species=species,slice_id=sid,experiments=s['experiments'],observed=s['observed'],expected=float(s['expected']),residual=float(delta),leave_one_slice_out_residual=float(remaining)))
            if delta:changed.append(float(remaining))
        variable=[r for r in rows if r['variable']]
        summaries[species]=dict(experiments=len(rows),observed=sum(r['observed'] for r in rows),
            expected=float(sum((s['expected'] for s in slices.values()),Fraction())),residual=float(residual),
            variable_experiments=len(variable),variable_slices=len(set(r['slice_id'] for r in variable)),
            variable_dyads=sum(r['dyads'] for r in variable),observed_in_variable=sum(r['observed'] for r in variable),
            expected_in_variable=sum(r['expected'] for r in variable),
            leave_one_nonzero_slice_out_residual_range=[min(changed),max(changed)] if changed else None)
    return dict(summaries=summaries,per_experiment=results,per_slice=slice_rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    spec=dict(timing='post-result sensitivity; not new independent confirmation',
        condition='per-experiment assessed mask, per-cell in/out degrees, and counts of positive edges in ordered nonsynaptic class x distance-bin categories simultaneously',
        distance_bins='same fixed0/50/100/200um boundaries plus missing; no retuning',
        method='filter every exact degree-constrained graph by observed category counts; uniform over retained graphs; observed graph must be retained',
        summary='species observed/expected, variability support, slice-summed residual and leave-one-nonzero-slice-out total; no p-values or resampling inference',
        limits='conditions may fix away biological structure; coarse/missing covariates, author-label selection, unknown detection bias; whole brain unestablished',
        source_hashes={str(p.name):sha(p) for p in (DEGREE,TABLE,DB,HERE/'reciprocity_stratified_reference.py')},code_sha256=sha(Path(__file__)))
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,indent=2)
    result=dict(contract_sha256=sha(CONTRACT),analysis=run())
    if args.verify:
        assert result==json.loads(OUTPUT.read_text(encoding='utf-8'));print('JOINT_CONSTRAINTS_REPRODUCED')
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result['analysis']['summaries'],indent=2))


if __name__=='__main__':main()
