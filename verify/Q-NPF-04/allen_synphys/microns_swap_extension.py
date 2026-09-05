"""저장 그래프에서90블록을 추가하며 그래프·edge 순서·RNG를 checkpoint에 보존한다."""
import argparse
import json
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base

HERE=base.HERE;ROOT=base.ROOT
CONTRACT=HERE/'microns_swap_extension_contract.json'
OUTPUT=HERE/'microns_swap_extension_result.json'
STORE=base.DATA/'swap_extension'


def validate(a,edges,initial,categories):
    assert all(np.array_equal(x,y) for x,y in zip(base.signature(initial,categories),base.signature(a,categories)))
    assert not np.diag(a).any() and len(edges)==int(a.sum())
    assert a[edges[:,0],edges[:,1]].all() and len(set(map(tuple,edges)))==len(edges)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    prior=json.loads(base.OUTPUT.read_text());original_spec=json.loads(base.CONTRACT.read_text())
    for name,digest in original_spec['source_sha256'].items():
        path=(HERE/name) if (HERE/name).exists() else base.DATA/name
        assert base.sha(path)==digest
    spec=dict(source_result_sha256=base.sha(base.OUTPUT),source_code_sha256=base.sha(Path(base.__file__)),
        code_sha256=base.sha(Path(__file__)),start='saved block30 adjacency, reindex edges deterministically, fresh fixed seed=prior_seed+1000',
        run='90 additional blocks, E proposals per block; checkpoint at total60,90,120; no new biological data',
        diagnostics='blocks91..120 mean/range and last15-minus-first15 drift; overlap and acceptance; no convergence threshold or uniformity claim',
        interpretation='trajectory stabilization only; constrained-space reachability and arbitrary-start sensitivity remain unproven',numpy=np.__version__)
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text())
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x') as stream:json.dump(spec,stream,indent=2)
    counts,categories=base.load_graph();STORE.mkdir(exist_ok=True);summaries=[]
    for old in prior['chains']:
        threshold=old['threshold'];seed=old['seed'];initial=counts>=threshold;m=int(initial.sum())
        start=base.STORE/f't{threshold}_seed{seed}.npz';assert base.sha(start)==old['graph_sha256']
        with np.load(start,allow_pickle=False) as saved:a=saved['adjacency'].copy()
        edges=np.argwhere(a);rng=np.random.default_rng(seed+1000);trajectory=[];accepted=0;previous_hash=old['graph_sha256']
        for end in (60,90,120):
            prefix=STORE/f't{threshold}_seed{seed}_block{end}'
            rp=prefix.with_suffix('.json');gp=prefix.with_suffix('.npz')
            if rp.exists():
                checkpoint=json.loads(rp.read_text());assert checkpoint['contract_sha256']==base.sha(CONTRACT)
                assert checkpoint['parent_state_sha256']==previous_hash and checkpoint['graph_sha256']==base.sha(gp)
                with np.load(gp,allow_pickle=False) as saved:a=saved['adjacency'].copy();edges=saved['edges'].copy()
                rng.bit_generator.state=checkpoint['rng_state'];trajectory=checkpoint['trajectory'];accepted=checkpoint['accepted']
            else:
                if args.verify:raise RuntimeError('checkpoint 없음')
                for block in range(end-29,end+1):
                    for i,j in rng.integers(0,m,size=(m,2)):accepted+=base.propose(a,edges,i,j,categories)
                    validate(a,edges,initial,categories)
                    trajectory.append(dict(block=block,reciprocal=int(np.sum(a&a.T)//2),
                        original_overlap=float(np.sum(a&initial)/m),accepted=accepted))
                if gp.exists():raise RuntimeError('영수증 없는 checkpoint 그래프 확인 필요')
                with gp.open('xb') as stream:np.savez_compressed(stream,adjacency=a,edges=edges)
                checkpoint=dict(contract_sha256=base.sha(CONTRACT),parent_state_sha256=previous_hash,
                    graph_sha256=base.sha(gp),rng_state=rng.bit_generator.state,trajectory=trajectory,accepted=accepted)
                with rp.open('x') as stream:json.dump(checkpoint,stream,indent=2)
                print('saved',threshold,seed,'block',end,'reciprocal',trajectory[-1]['reciprocal'],flush=True)
            validate(a,edges,initial,categories)
            assert len(trajectory)==end-30 and trajectory[-1]['block']==end
            assert trajectory[-1]['reciprocal']==int(np.sum(a&a.T)//2)
            previous_hash=base.sha(gp)
        late=[r['reciprocal'] for r in trajectory[-30:]]
        summaries.append(dict(threshold=threshold,seed=seed,observed_reciprocal=old['observed_reciprocal'],
            late_mean=float(np.mean(late)),late_range=[min(late),max(late)],
            late_half_drift=float(np.mean(late[15:])-np.mean(late[:15])),
            final_overlap=trajectory[-1]['original_overlap'],extension_acceptance=accepted/(90*m),
            final_checkpoint=rp.relative_to(ROOT).as_posix(),final_checkpoint_sha256=base.sha(rp),final_graph_sha256=base.sha(gp)))
    result=dict(contract_sha256=base.sha(CONTRACT),chains=summaries,status='EXTENDED_TRAJECTORY_DIAGNOSTIC_NOT_UNIFORM_NULL_PROOF')
    if args.verify:
        assert result==json.loads(OUTPUT.read_text());print('EXTENSION_CHECKPOINTS_AND_INVARIANTS_VERIFIED')
    else:
        with OUTPUT.open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
