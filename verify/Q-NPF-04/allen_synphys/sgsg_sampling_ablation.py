"""동일 공간 그래프에서 보호 단계의 정수 선택과 확률 선택을 비교한다."""
import copy
import hashlib
import json
from pathlib import Path
import warnings
import numpy as np
from scipy import sparse
import sgsg_calibration_grid as shared

HERE = shared.HERE
STORE = shared.source.base.ROOT / 'data/external/sgsg_sampling_ablation'


def rounded_count(target, capacity, uniform):
    target = min(max(float(target), 0.), int(capacity))
    floor = int(np.floor(target))
    return floor + int(uniform < target - floor)


def stochastic_protected(p_mat, adjust=None):
    """저자 가중 비복원 선택은 유지하고 선택 수만 확률 반올림한다."""
    m = p_mat.tocsr()
    assert np.isfinite(m.data).all() and (m.data >= 0).all()
    rows, cols = [], []
    for i, (start, end) in enumerate(zip(m.indptr[:-1], m.indptr[1:])):
        weights = m.data[start:end]
        total = float(weights.sum())
        if total == 0:
            continue
        target = total if adjust is None else total * adjust[i]
        count = rounded_count(target, np.count_nonzero(weights > 0), np.random.random())
        if count:
            picked = np.random.choice(m.indices[start:end], count, p=weights / total, replace=False)
            rows.extend([i] * count)
            cols.extend(picked.tolist())
    return sparse.coo_matrix((np.ones(len(rows), dtype=bool), (rows, cols)), shape=m.shape)


def fixtures():
    for target, capacity in [(0, 3), (.25, 3), (1.5, 3), (2.75, 3), (5., 2)]:
        values = [rounded_count(target, capacity, u) for u in (.125, .375, .625, .875)]
        assert np.mean(values) == min(target, capacity)
        assert min(values) >= 0 and max(values) <= capacity
    np.random.seed(2026092099)
    m = sparse.csr_matrix([[0., 1., 1.], [0., 0., 0.], [1., 0., 0.]])
    selected = stochastic_protected(m, np.array([.75, 0., 2.]))
    assert selected.shape == m.shape and not selected.diagonal().any()
    assert selected.toarray()[1].sum() == 0 and selected.toarray()[2].sum() == 1


def branch(m, xyz, instance_config, mode, seed, spread):
    original = spread._evaluate_probs_less_random
    cfg = copy.deepcopy(instance_config)
    if mode == 'bernoulli_all':
        cfg['n_protected'] = 0
    elif mode == 'stochastic_round':
        spread._evaluate_probs_less_random = stochastic_protected
    np.random.seed(seed)
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            g, history, _ = spread.build_instance(xyz, m.copy(), **cfg)
        assert all(str(w.message) == 'invalid value encountered in divide' for w in caught)
        assert np.isfinite(g.data).all() and np.isfinite(history).all()
        a = g.toarray()
        assert np.isin(a, [0, 1]).all() and not np.diag(a).any()
        if mode != 'original':
            assert not caught
        return a.astype(bool), [float(x) for x in history], len(caught)
    finally:
        spread._evaluate_probs_less_random = original


def main():
    fixtures()
    config, geometry, spread = shared.source.load_modules()
    config['nngraph'].update(dist_neighbors=65., p_pick=.1)
    spec = dict(question='Does the q1.5-to1.55 density jump depend on deterministic protected-step rounding?',
                scope='Previously inspected Minnie v1718 347-cell 23P coordinates; synthetic sampling-mechanism ablation, no biological intervention',
                modes=['original','stochastic_round','bernoulli_all'], q_values=[1.5,1.55],
                config=config, geometry_seeds=list(range(2026092100,2026092132)),
                spread_seeds=list(range(2026092200,2026092232)),
                pairing='Generate one weighted spatial graph per geometry seed; reuse identical graph in all6branches, reset spread RNG separately to common seed. Different algorithms consume draws differently, not matched individual edge draws.',
                stochastic_round='First6steps only: floor(target)+Bernoulli(fraction), target=min(q*s/(s+0.001),positive_candidates), weighted without-replacement target selection unchanged. New model variant, original archive preserved.',
                bernoulli_all='n_protected0 also changes variance and within-row selection dependence; not a pure rounding-only control',
                endpoint='Per seed E(q1.55)-E(q1.5) by mode, paired mode-minus-original difference; mean, sampleSD/sqrt32 and min/max as Monte Carlo diagnostics, not biological confidence intervals',
                gate='All192graphs finite binary loop-free with identical spatial inputs. Compare existing5feature adequacy without selecting parameters; reciprocity not evaluated.',
                source_sha256=shared.source.base.sha(shared.source.ARCHIVE), code_sha256=shared.source.base.sha(Path(__file__)),
                shared_code_sha256=shared.source.base.sha(Path(shared.__file__)),
                predecessor_sha256=shared.source.base.sha(HERE/'sgsg_rounding_diagnostic.json'))
    contract = HERE/'sgsg_sampling_ablation_contract.json'
    shared.source.write_once(contract,spec)
    roots, xyz, obs, bins = shared.source.data()
    STORE.mkdir(exist_ok=True)
    records=[]
    for index,(gseed,sseed) in enumerate(zip(spec['geometry_seeds'],spec['spread_seeds'])):
        np.random.seed(gseed)
        m=geometry.cand2_point_nn_matrix(xyz,**config['nngraph'])
        mh=hashlib.sha256(m.toarray().tobytes()).hexdigest()
        for mode in spec['modes']:
            for q in spec['q_values']:
                name=f'{index:02}_{mode}_{q}'
                receipt=STORE/(name+'.json')
                path=STORE/(name+'.npz')
                cfg=copy.deepcopy(config['instance']); cfg['step_tgt']=q
                if receipt.exists():
                    r=json.loads(receipt.read_text())
                    assert r['contract_sha256']==shared.source.base.sha(contract) and r['spatial_graph_sha256']==mh
                    assert r['file_sha256']==shared.source.base.sha(path)
                else:
                    a,history,warnings_count=branch(m,xyz,cfg,mode,sseed,spread)
                    with path.open('xb') as stream:
                        np.savez_compressed(stream,adjacency=a,roots=np.array(roots,dtype=np.int64))
                    r=dict(status='PASS',index=index,mode=mode,q=q,geometry_seed=gseed,spread_seed=sseed,
                           features=shared.features(a,bins),history=history,warning_events=warnings_count,
                           spatial_graph_sha256=mh,file_sha256=shared.source.base.sha(path),
                           contract_sha256=shared.source.base.sha(contract))
                    shared.source.write_once(receipt,r)
                records.append(r)
        if index%8==7:print('paired spatial graphs completed',index+1,flush=True)
    contrasts={}
    changes={mode:[next(r['features']['edges'] for r in records if r['index']==i and r['mode']==mode and r['q']==1.55)-next(r['features']['edges'] for r in records if r['index']==i and r['mode']==mode and r['q']==1.5) for i in range(32)] for mode in spec['modes']}
    for mode,values in changes.items():
        contrasts[mode]=dict(per_seed_change=values,mean=float(np.mean(values)),mc_se=float(np.std(values,ddof=1)/np.sqrt(32)),range=[min(values),max(values)])
        diff=np.array(values)-np.array(changes['original'])
        contrasts[mode]['paired_difference_from_original']=dict(mean=float(diff.mean()),mc_se=float(diff.std(ddof=1)/np.sqrt(32)))
    adequacy={f'{mode}_{q}':shared.assess([r for r in records if r['mode']==mode and r['q']==q],shared.features(obs,bins)) for mode in spec['modes'] for q in spec['q_values']}
    result=dict(contract_sha256=shared.source.base.sha(contract),contrasts=contrasts,adequacy=adequacy,
                observed_features=shared.features(obs,bins),reciprocal_endpoint=None,
                receipt_sha256={p.name:shared.source.base.sha(p) for p in sorted(STORE.glob('*.json'))})
    shared.source.write_once(HERE/'sgsg_sampling_ablation_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='receipt_sha256'}),flush=True)


if __name__=='__main__':main()
