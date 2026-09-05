"""同一 공간 그래프 대조, 저장 통계 및 대표 여섯 분기의 재실행 검사."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
import sgsg_sampling_ablation as run


def main():
    result_path=run.HERE/'sgsg_sampling_ablation_result.json'
    result=json.loads(result_path.read_text())
    contract=run.HERE/'sgsg_sampling_ablation_contract.json'
    assert result['contract_sha256']==run.shared.source.base.sha(contract)
    spec=json.loads(contract.read_text())
    roots,xyz,obs,_=run.shared.source.data()
    bins=np.digitize(cdist(xyz,xyz),[50,100,200,400,800])
    entries=[]
    for name,digest in result['receipt_sha256'].items():
        receipt=run.STORE/name
        assert run.shared.source.base.sha(receipt)==digest
        r=json.loads(receipt.read_text())
        assert r['contract_sha256']==result['contract_sha256']
        path=receipt.with_suffix('.npz')
        assert run.shared.source.base.sha(path)==r['file_sha256']
        with np.load(path,allow_pickle=False) as f:
            a=f['adjacency']; assert f['roots'].tolist()==roots
        assert a.dtype==bool and not np.diag(a).any()
        u,v=np.nonzero(a)
        out=np.bincount(u,minlength=len(roots)); inc=np.bincount(v,minlength=len(roots))
        assert len(u)==r['features']['edges']
        assert np.bincount(bins[u,v],minlength=6).tolist()==r['features']['distance_counts']
        assert float(out.std())==r['features']['out_degree_sd']
        assert float(inc.std())==r['features']['in_degree_sd']
        assert int(np.sum((out+inc)==0))==r['features']['zero_degree_cells']
        entries.append(r)
    assert len(entries)==192
    cfg,geometry,spread=run.shared.source.load_modules()
    cfg['nngraph'].update(dist_neighbors=65.,p_pick=.1)
    replayed=[]
    for i,seed in enumerate(spec['geometry_seeds']):
        np.random.seed(seed)
        m=geometry.cand2_point_nn_matrix(xyz,**cfg['nngraph'])
        digest=hashlib.sha256(m.toarray().tobytes()).hexdigest()
        rows=[r for r in entries if r['index']==i]
        assert len(rows)==6 and all(r['spatial_graph_sha256']==digest for r in rows)
        if i==0:
            for r in rows:
                instance=copy.deepcopy(cfg['instance']); instance['step_tgt']=r['q']
                a,history,w=run.branch(m,xyz,instance,r['mode'],r['spread_seed'],spread)
                name=f'{i:02}_{r["mode"]}_{r["q"]}.npz'
                with np.load(run.STORE/name,allow_pickle=False) as f:
                    assert np.array_equal(a,f['adjacency'])
                assert history==r['history'] and w==r['warning_events']
                replayed.append(name)
    for mode in spec['modes']:
        delta=[]
        for i in range(32):
            pair={r['q']:r['features']['edges'] for r in entries if r['index']==i and r['mode']==mode}
            delta.append(pair[1.55]-pair[1.5])
        assert delta==result['contrasts'][mode]['per_seed_change']
        assert float(np.mean(delta))==result['contrasts'][mode]['mean']
    output=dict(result_sha256=run.shared.source.base.sha(result_path),verifier_sha256=run.shared.source.base.sha(Path(__file__)),
                graphs_verified=192,spatial_graphs_regenerated=32,replayed_branches=replayed,
                exact_shared_geometry_verified=True,biological_validation=False)
    run.shared.source.write_once(run.HERE/'sgsg_sampling_ablation_verification.json',output)
    print(json.dumps(output))


if __name__=='__main__':main()
