"""새 64개 그래프의 통계·조건 판정과 상호연결 직접 집계를 검증한다."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
import sgsg_stochastic_evaluation as study


def main():
    shared=study.run.shared
    result_path=study.HERE/'sgsg_stochastic_evaluation_result.json'
    result=json.loads(result_path.read_text())
    roots,xyz,observed,_=shared.source.data()
    bins=np.digitize(cdist(xyz,xyz),[50,100,200,400,800])
    cfg,geometry,spread=shared.source.load_modules()
    cfg['nngraph'].update(dist_neighbors=65.,p_pick=.1)
    cfg['instance']['step_tgt']=1.5
    entries=[];mutual=[];replayed=[]
    for name,digest in sorted(result['receipt_sha256'].items()):
        receipt=study.STORE/name
        assert shared.source.base.sha(receipt)==digest
        r=json.loads(receipt.read_text())
        assert r['contract_sha256']==result['contract_sha256']
        path=receipt.with_suffix('.npz')
        assert shared.source.base.sha(path)==r['file_sha256']
        with np.load(path,allow_pickle=False) as f:
            a=f['adjacency'];assert f['roots'].tolist()==roots
        assert a.dtype==bool and not np.diag(a).any() and r['warning_events']==0
        u,v=np.nonzero(a)
        out=np.bincount(u,minlength=len(a)); inc=np.bincount(v,minlength=len(a))
        assert r['features']['edges']==len(u)
        assert r['features']['distance_counts']==np.bincount(bins[u,v],minlength=6).tolist()
        assert r['features']['out_degree_sd']==float(out.std())
        assert r['features']['in_degree_sd']==float(inc.std())
        assert r['features']['zero_degree_cells']==int(np.sum((out+inc)==0))
        if result['reciprocal_endpoint'] is not None:
            mutual.append(sum(bool(a[i,j] and a[j,i]) for i in range(len(a)) for j in range(i+1,len(a))))
        np.random.seed(r['geometry_seed'])
        m=geometry.cand2_point_nn_matrix(xyz,**cfg['nngraph'])
        assert hashlib.sha256(m.toarray().tobytes()).hexdigest()==r['spatial_graph_sha256']
        if r['index'] in (0,63):
            replay,history,w=study.run.branch(m,xyz,cfg['instance'],'stochastic_round',r['spread_seed'],spread)
            assert np.array_equal(a,replay) and history==r['history'] and w==r['warning_events']
            replayed.append(r['index'])
        entries.append(r)
    assert len(entries)==64
    assert shared.assess(entries,shared.features(observed,bins))==result['assessment']
    if result['reciprocal_endpoint'] is not None:
        endpoint=result['reciprocal_endpoint']
        assert result['assessment']['pass_all'] and mutual==endpoint['simulated']
        direct_obs=sum(bool(observed[i,j] and observed[j,i]) for i in range(len(observed)) for j in range(i+1,len(observed)))
        assert endpoint['observed']==direct_obs and endpoint['mean']==float(np.mean(mutual))
        assert endpoint['observed_minus_mean']==direct_obs-float(np.mean(mutual))
    else:
        assert not result['assessment']['pass_all']
    output=dict(result_sha256=shared.source.base.sha(result_path),verifier_sha256=shared.source.base.sha(Path(__file__)),
                graphs_verified=64,spatial_graphs_regenerated=64,full_graph_replays=replayed,
                reciprocal_direct_count_checked=result['reciprocal_endpoint'] is not None,
                adequacy_recalculated=True,biological_validation=False)
    shared.source.write_once(study.HERE/'sgsg_stochastic_evaluation_verification.json',output)
    print(json.dumps(output))


if __name__=='__main__':main()
