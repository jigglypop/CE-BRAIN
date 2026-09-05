"""MICrONS 관측 그래프의 제약 보존 재배치 탐색. 균등 표본화의 증명은 아님."""
import argparse
import csv
import json
import sys
from pathlib import Path
import numpy as np
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DATA=ROOT/'data/external/microns_v1718_cosyne'
CONTRACT=HERE/'microns_swaps_contract.json'
OUTPUT=HERE/'microns_swaps_result.json'
STORE=DATA/'constrained_swaps'
SELECTED=HERE/'microns_structural_inventory_result.json'
SEEDS=[2026090501,2026090502,2026090503,2026090504]


def propose(a,edges,i,j,categories):
    u,v=map(int,edges[i]);x,y=map(int,edges[j])
    if len({u,v,x,y})!=4 or a[u,y] or a[x,v]:return False
    if sorted((int(categories[u,v]),int(categories[x,y])))!=sorted((int(categories[u,y]),int(categories[x,v]))):return False
    a[u,v]=False;a[x,y]=False;a[u,y]=True;a[x,v]=True
    edges[i]=(u,y);edges[j]=(x,v)
    return True


def fixtures():
    a=np.zeros((4,4),dtype=bool);a[0,1]=True;a[2,3]=True;edges=np.argwhere(a);c=np.zeros((4,4),dtype=np.int16)
    assert propose(a,edges,0,1,c)
    assert a[0,3] and a[2,1] and a.sum()==2
    assert propose(a,edges,0,1,c) and a[0,1] and a[2,3]
    c[0,3]=1;before=a.copy();assert not propose(a,edges,0,1,c) and np.array_equal(before,a)


def load_graph():
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    selected=json.loads(SELECTED.read_text(encoding='utf-8'))['selected_roots'];index={v:i for i,v in enumerate(selected)};n=len(selected)
    with (DATA/'v1718_cell_info.csv').open(encoding='utf-8',newline='') as stream:cells={int(r['pt_root_id']):r for r in csv.DictReader(stream)}
    xyz=np.array([[float(cells[r]['pt_position_'+axis+'_tform']) for axis in ('x','y','z')] for r in selected]);assert np.isfinite(xyz).all()
    types=np.array([{'excitatory':0,'inhibitory':1}[cells[r]['broad_type']] for r in selected])
    distance=np.sqrt(sum((xyz[:,axis,None]-xyz[None,:,axis])**2 for axis in range(3)))
    bins=np.digitize(distance,[50,100,200,400,800])
    categories=((types[:,None]*2+types[None,:])*6+bins).astype(np.int16)
    t=feather.read_table(DATA/'v1718_v1_column_synapses.feather',columns=['pre_pt_root_id','post_pt_root_id'])
    counts=np.zeros((n,n),dtype=np.int32)
    for pre,post in zip(t['pre_pt_root_id'].to_pylist(),t['post_pt_root_id'].to_pylist()):
        if pre in index and post in index and pre!=post:counts[index[pre],index[post]]+=1
    return counts,categories


def signature(a,categories):
    return a.sum(axis=0),a.sum(axis=1),np.bincount(categories[a],minlength=24)


def run_chain(initial,categories,seed):
    a=initial.copy();edges=np.argwhere(a);m=len(edges);rng=np.random.default_rng(seed);expected=signature(a,categories);records=[];accepted=0
    for block in range(1,31):
        proposals=rng.integers(0,m,size=(m,2))
        for i,j in proposals:accepted+=propose(a,edges,i,j,categories)
        assert all(np.array_equal(x,y) for x,y in zip(expected,signature(a,categories)))
        assert not np.diag(a).any() and a[edges[:,0],edges[:,1]].all() and len(set(map(tuple,edges)))==m
        records.append(dict(block=block,attempts=block*m,accepted=accepted,reciprocal=int(np.sum(a&a.T)//2),
            retained_original_edge_fraction=float(np.sum(a&initial)/m)))
        if block%10==0:print('chain',seed,'block',block,'reciprocal',records[-1]['reciprocal'],flush=True)
    return a,records


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args();fixtures()
    sources=[SELECTED,DATA/'v1718_cell_info.csv',DATA/'v1718_v1_column_synapses.feather',HERE/'microns_export_overlap_result.json']
    spec=dict(scope='1348 selected cells, thresholds1 and3, four fixed seeds per threshold',
        constraints='exact node in/out degree and global ordered broad-type x Euclidean transformed-soma-distance-bin edge counts',
        distance_bins_um=[50,100,200,400,800],proposal='uniform pair of current edge indices, four distinct endpoints, no self/duplicate edges; target swap if category multiset preserved',
        run='30 blocks of E proposals each; retain every block; last15 blocks descriptive only',
        interpretation='reachable-state trajectory diagnostic, not proven uniform graph sampler; no p-values; no causal or whole-brain claim',
        gates='exact invariants each block; report acceptance, original-edge overlap, between-chain ranges and late drift; failures stop interpretation',
        limitations='possible disconnected constrained state space and slow mixing; broad types/coarse distance, proofreading and missing annotations remain',
        seeds=SEEDS,source_sha256={p.name:sha(p) for p in sources},code_sha256=sha(Path(__file__)),numpy=np.__version__)
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,indent=2)
    counts,categories=load_graph();STORE.mkdir(exist_ok=True);results=[]
    for threshold in (1,3):
        initial=counts>=threshold;m=int(initial.sum());observed=int(np.sum(initial&initial.T)//2)
        for seed in SEEDS:
            record_path=STORE/f't{threshold}_seed{seed}.json';graph_path=STORE/f't{threshold}_seed{seed}.npz'
            if record_path.exists():
                entry=json.loads(record_path.read_text());assert entry['contract_sha256']==sha(CONTRACT) and entry['graph_sha256']==sha(graph_path)
                with np.load(graph_path,allow_pickle=False) as saved:a=saved['adjacency']
                assert all(np.array_equal(x,y) for x,y in zip(signature(initial,categories),signature(a,categories)))
                assert not np.diag(a).any() and int(np.sum(a&a.T)//2)==entry['trajectory'][-1]['reciprocal']
            else:
                if args.verify:raise RuntimeError('저장된 chain 없음')
                a,records=run_chain(initial,categories,seed)
                with graph_path.open('xb') as stream:np.savez_compressed(stream,adjacency=a)
                entry=dict(contract_sha256=sha(CONTRACT),threshold=threshold,seed=seed,edges=m,observed_reciprocal=observed,
                    trajectory=records,graph_sha256=sha(graph_path))
                with record_path.open('x') as stream:json.dump(entry,stream,indent=2)
            late=[r['reciprocal'] for r in entry['trajectory'][15:]]
            results.append(dict(threshold=threshold,seed=seed,edges=m,observed_reciprocal=observed,
                late_mean=float(np.mean(late)),late_range=[min(late),max(late)],
                late_half_drift=float(np.mean(late[-7:])-np.mean(late[:7])),
                final_overlap=entry['trajectory'][-1]['retained_original_edge_fraction'],
                accepted_fraction=entry['trajectory'][-1]['accepted']/(30*m),record_path=record_path.relative_to(ROOT).as_posix(),
                record_sha256=sha(record_path),graph_sha256=sha(graph_path)))
    result=dict(contract_sha256=sha(CONTRACT),chains=results,status='CONSTRAINTS_VERIFIED_EXPLORATORY_TRAJECTORIES_NOT_UNIFORMITY_PROOF')
    if args.verify:
        assert result==json.loads(OUTPUT.read_text());print('SWAP_ENDPOINT_INVARIANTS_AND_RECEIPTS_VERIFIED')
    else:
        with OUTPUT.open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(results,indent=2))


if __name__=='__main__':main()
