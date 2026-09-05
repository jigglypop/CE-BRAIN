"""확률 반올림 q1.5를 고정하고 새 시뮬레이션 표본에서 적합성을 검사한다."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import sgsg_sampling_ablation as run

HERE=run.HERE
STORE=run.shared.source.base.ROOT/'data/external/sgsg_stochastic_evaluation'


def main():
    prior=HERE/'sgsg_sampling_ablation_result.json'
    assert json.loads(prior.read_text())['adequacy']['stochastic_round_1.5']['pass_all']
    spec=dict(question='Does the fixed stochastic-round SGSG pass the same five adequacy checks on new simulation seeds, and if so what reciprocity does it generate?',
              design='Adaptive exploratory choice after six-branch ablation; separate simulation randomness only, not a new biological specimen or confirmatory hypothesis test',
              parameters=dict(dist_neighbors=65.,p_pick=.1,step_tgt=1.5,mode='stochastic_round'),
              geometry_seeds=list(range(2026092300,2026092364)),spread_seeds=list(range(2026092400,2026092464)),
              gate='Exactly shared assess five mean-feature thresholds, all64successful; do not weaken thresholds or choose a different parameter if failure',
              endpoint='Only after gate pass count reciprocal pairs in all64stored graphs; descriptive mean/range, observed-minus-mean and MC standard error of mean. No tail pvalue or causal claim.',
              prior_sha256=run.shared.source.base.sha(prior),prior_contract_sha256=run.shared.source.base.sha(HERE/'sgsg_sampling_ablation_contract.json'),
              code_sha256=run.shared.source.base.sha(Path(__file__)),adapter_sha256=run.shared.source.base.sha(Path(run.__file__)))
    contract=HERE/'sgsg_stochastic_evaluation_contract.json'
    run.shared.source.write_once(contract,spec)
    roots,xyz,obs,bins=run.shared.source.data()
    cfg,geometry,spread=run.shared.source.load_modules()
    cfg['nngraph'].update(dist_neighbors=65.,p_pick=.1)
    cfg['instance']['step_tgt']=1.5
    STORE.mkdir(exist_ok=True)
    records=[]
    for i,(gs,ss) in enumerate(zip(spec['geometry_seeds'],spec['spread_seeds'])):
        receipt=STORE/f'{i:02}.json';path=STORE/f'{i:02}.npz'
        if receipt.exists():
            r=json.loads(receipt.read_text())
            assert r['contract_sha256']==run.shared.source.base.sha(contract)
            assert r['file_sha256']==run.shared.source.base.sha(path)
        else:
            np.random.seed(gs)
            m=geometry.cand2_point_nn_matrix(xyz,**cfg['nngraph'])
            a,history,w=run.branch(m,xyz,cfg['instance'],'stochastic_round',ss,spread)
            with path.open('xb') as stream:
                np.savez_compressed(stream,adjacency=a,roots=np.array(roots,dtype=np.int64))
            r=dict(status='PASS',index=i,geometry_seed=gs,spread_seed=ss,features=run.shared.features(a,bins),
                   history=history,warning_events=w,spatial_graph_sha256=hashlib.sha256(m.toarray().tobytes()).hexdigest(),
                   file_sha256=run.shared.source.base.sha(path),contract_sha256=run.shared.source.base.sha(contract))
            run.shared.source.write_once(receipt,r)
        records.append(r)
        if i%16==15:print('fixed candidate evaluated',i+1,flush=True)
    assessment=run.shared.assess(records,run.shared.features(obs,bins))
    endpoint=None
    if assessment['pass_all']:
        values=[]
        for r in records:
            with np.load(STORE/f'{r["index"]:02}.npz',allow_pickle=False) as f:
                a=f['adjacency']
            values.append(int((a&a.T).sum()//2))
        observed=int((obs&obs.T).sum()//2)
        endpoint=dict(observed=observed,simulated=values,mean=float(np.mean(values)),
                      observed_minus_mean=observed-float(np.mean(values)),range=[min(values),max(values)],
                      mc_se_of_mean=float(np.std(values,ddof=1)/np.sqrt(64)),
                      claim='Approximate low-order-matched adaptive generative comparison, not exact degree-conditioned residual or biological validation')
    result=dict(contract_sha256=run.shared.source.base.sha(contract),assessment=assessment,reciprocal_endpoint=endpoint,
                receipt_sha256={p.name:run.shared.source.base.sha(p) for p in sorted(STORE.glob('*.json'))})
    run.shared.source.write_once(HERE/'sgsg_stochastic_evaluation_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='receipt_sha256'}),flush=True)


if __name__=='__main__':main()
