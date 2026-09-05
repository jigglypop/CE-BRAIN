"""미검사 위치와 세포별 입출력 연결 수를 보존한 유향 그래프의 정확한 참조값."""
import argparse
import csv
import itertools
import json
from collections import defaultdict
from functools import lru_cache
from fractions import Fraction
from pathlib import Path
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent
TABLE=HERE.parents[2]/'data/external/allen_synphys_r21/derived/reciprocal_dyads.csv'
CONTRACT=HERE/'reciprocity_fixed_degrees_contract.json'
OUTPUT=HERE/'reciprocity_fixed_degrees_result.json'


def count_graphs(outgoing,incoming,masks,forced=()):
    outgoing=list(outgoing);incoming=list(incoming);masks=list(masks)
    for a,b in forced:
        if not masks[a]&(1<<b):return 0
        masks[a]&=~(1<<b);outgoing[a]-=1;incoming[b]-=1
    if min(outgoing+incoming)<0:return 0
    n=len(masks)
    @lru_cache(None)
    def count(i,remaining):
        if i==n:return int(not any(remaining))
        for col,needed in enumerate(remaining):
            if needed>sum(bool(masks[row]&(1<<col)) for row in range(i,n)):return 0
        choices=[j for j in range(n) if masks[i]&(1<<j) and remaining[j]>0]
        if len(choices)<outgoing[i]:return 0
        total=0
        for selected in itertools.combinations(choices,outgoing[i]):
            next_remaining=list(remaining)
            for j in selected:next_remaining[j]-=1
            total+=count(i+1,tuple(next_remaining))
        return total
    return count(0,tuple(incoming))


def expectation(outgoing,incoming,masks):
    total=count_graphs(outgoing,incoming,masks);assert total>0
    terms=[]
    for a in range(len(masks)):
        for b in range(a+1,len(masks)):
            if masks[a]&(1<<b) and masks[b]&(1<<a):
                terms.append(count_graphs(outgoing,incoming,masks,((a,b),(b,a))))
    return total,Fraction(sum(terms),total)


def fixtures():
    # Enumerate every loop-free three-node graph, grouping by exact row/column sums.
    edges=[(a,b) for a in range(3) for b in range(3) if a!=b]
    groups=defaultdict(list)
    for bits in itertools.product((0,1),repeat=6):
        chosen={edge for edge,on in zip(edges,bits) if on}
        out=tuple(sum(a==i for a,b in chosen) for i in range(3))
        inc=tuple(sum(b==i for a,b in chosen) for i in range(3))
        reciprocal=sum((a,b) in chosen and (b,a) in chosen for a in range(3) for b in range(a+1,3))
        groups[out,inc].append(reciprocal)
    masks=tuple(7^(1<<i) for i in range(3))
    for (out,inc),values in groups.items():
        total,mean=expectation(out,inc,masks)
        assert total==len(values) and mean==Fraction(sum(values),len(values))
    assert expectation((1,)*4,(1,)*4,tuple(15^(1<<i) for i in range(4)))==(9,Fraction(2,3))
    assert expectation((1,1,0),(1,1,0),(2,1,0))==(1,Fraction(1))


def run():
    with TABLE.open(encoding='utf-8',newline='') as stream:dyads=list(csv.DictReader(stream))
    groups=defaultdict(list)
    for row in dyads:groups[int(row['experiment_id'])].append(row)
    rows=[]
    for step,(eid,ds) in enumerate(sorted(groups.items()),1):
        ids=sorted({int(d[k]) for d in ds for k in ('cell_a','cell_b')});index={v:i for i,v in enumerate(ids)}
        n=len(ids);masks=[0]*n;out=[0]*n;inc=[0]*n
        for d in ds:
            a=index[int(d['cell_a'])];b=index[int(d['cell_b'])]
            masks[a]|=1<<b;masks[b]|=1<<a
            for pre,post,label in ((a,b,int(d['label_ab'])),(b,a,int(d['label_ba']))):
                out[pre]+=label;inc[post]+=label
        total,expected=expectation(tuple(out),tuple(inc),tuple(masks))
        observed=sum(int(d['positive_directions'])==2 for d in ds)
        rows.append(dict(experiment_id=eid,species=ds[0]['species'],slice_id=int(ds[0]['slice_id']),
            cell_ids=ids,allowed_destination_masks=masks,outgoing=out,incoming=inc,dyads=len(ds),
            observed_reciprocal=observed,admissible_graphs=total,
            expected_numerator=expected.numerator,expected_denominator=expected.denominator,
            expected_reciprocal=float(expected)))
        if step%500==0:print('exact graphs counted',step,'/',len(groups),flush=True)
    species={}
    for key in sorted(set(r['species'] for r in rows)):
        selected=[r for r in rows if r['species']==key];mobile=[r for r in selected if r['admissible_graphs']>1]
        expected=sum((Fraction(r['expected_numerator'],r['expected_denominator']) for r in selected),Fraction())
        species[key]=dict(experiments=len(selected),dyads=sum(r['dyads'] for r in selected),
            observed=sum(r['observed_reciprocal'] for r in selected),expected=float(expected),
            unique_graph_experiments=sum(r['admissible_graphs']==1 for r in selected),
            multiple_graph_experiments=len(mobile),multiple_graph_dyads=sum(r['dyads'] for r in mobile),
            observed_in_multiple_graph_experiments=sum(r['observed_reciprocal'] for r in mobile),
            expected_in_multiple_graph_experiments=sum(r['expected_reciprocal'] for r in mobile),
            max_admissible_graphs=max(r['admissible_graphs'] for r in selected))
    return dict(species=species,per_experiment=rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    fixtures()
    spec=dict(question='Does observed reciprocity exceed the exact uniform graph expectation conditioned on observed per-cell in/out degree and assessed dyad mask?',
        timing='post-result follow-up to species/class/distance descriptive analyses',
        scope='all both-assessed dyads, per experiment; degrees refer only to this observed subgraph',
        method='exact binary directed adjacency counts by row-wise dynamic programming; mutual-edge marginal by forcing both entries',
        decision='report observed and exact expectation, number of uniquely determined and non-unique graphs; no causal or whole-brain claim and no p-value',
        limitations='class and distance not additionally fixed here; degree conditioning may absorb real structure; non-unique graphs need not vary in reciprocity; author labels and sampling bias remain',
        fixture='all64 three-node directed graphs; four-node derangements; restricted-mask unique graph',
        table_sha256=sha(TABLE),code_sha256=sha(Path(__file__)))
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,indent=2)
    analysis=run();result=dict(contract_sha256=sha(CONTRACT),analysis=analysis)
    if args.verify:
        assert result==json.loads(OUTPUT.read_text(encoding='utf-8'));print('FIXED_DEGREES_EXACT_REFERENCE_REPRODUCED')
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(analysis['species'],indent=2))


if __name__=='__main__':main()
