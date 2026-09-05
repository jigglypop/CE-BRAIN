"""고정 분할/관측량과 비선형 깊이 기준에 대한 방향 예측 민감도."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;source=HERE/'peng2024_pia_direction_result.json'
save('peng2024_role_mask_sensitivity_contract.json',{
    'question':'Does conditional cell-role prediction survive three fixed masks, fewer observed directions, and a cubic depth-difference baseline?',
    'scope':'same 881 ER dyads/22 patients; no new biological replication',
    'masks':'seed0,seed1,seed2; per-record hash sorted endpoints round-robin into k=2 or4 groups; target group g sees only (g+1)%k',
    'models':{'linear':[0], 'cubic':[0,1], 'linear_role':[0,2], 'cubic_role':[0,1,2]},
    'features':'x=depth difference/100; x^3/10; role imbalance on visible edges only; all features reverse sign on endpoint swap',
    'fit':'leave whole patient out; no intercept; ridge identity; fixed scaling and no selection among settings',
    'checks':'all hidden-label flip invariance; no target visible; gradient<1e-9; seed0 k2 reproduces existing linear-role predictions',
    'endpoint':'pooled/equal-patient logloss for every setting; patients improved vs corresponding depth baseline',
    'limits':'cubic depth difference is one alternative, not all spatial confounding; conditional completion not joint graph generation or causal role',
    'source_sha256':sha(source),'code_sha256':sha(Path(__file__))})
prior=json.loads(source.read_text(encoding='utf-8'));edges=prior['edges'];groups=defaultdict(list)
for i,e in enumerate(edges):groups[e['cluster']].append(i)
y=np.array([e['y'] for e in edges]);patients=np.array([e['patient'] for e in edges]);pnames=sorted(set(patients))
depth=np.array([e['x'] for e in edges]);models={'linear':[0],'cubic':[0,1],'linear_role':[0,2],'cubic_role':[0,1,2]}
def evaluate(features,cols):
    losses=np.zeros(len(edges));probs=np.zeros(len(edges));folds=[]
    for patient in pnames:
        test=patients==patient;train=~test
        x=features[train][:,cols];target=y[train];beta=np.zeros(len(cols))
        def obj(b):return float(np.sum(np.logaddexp(0,x@b)-target*(x@b))+.5*(b@b))
        for _ in range(150):
            p=expit(x@beta);g=x.T@(p-target)+beta
            if np.max(np.abs(g))<1e-9:break
            h=x.T@((p*(1-p))[:,None]*x)+np.eye(len(cols));step=np.linalg.solve(h,g);scale=1.
            while np.max(np.abs(g))>=1e-6 and obj(beta-scale*step)>obj(beta)-1e-4*scale*float(g@step):
                scale*=.5;assert scale>1e-12
            beta-=scale*step
        assert np.max(np.abs(g))<1e-9
        eta=features[test][:,cols]@beta;losses[test]=np.logaddexp(0,eta)-y[test]*eta;probs[test]=expit(eta)
        folds.append({'patient':str(patient),'beta':beta.tolist(),'logloss':float(losses[test].mean())})
    return {'logloss':float(losses.mean()),'equal_patient_logloss':float(np.mean([f['logloss'] for f in folds])),
            'folds':folds,'probabilities':probs.tolist()},losses
results={};baseline_cache={}
for k in (2,4):
    for seed in (0,1,2):
        mask={}
        for cluster,indices in groups.items():
            order=sorted(indices,key=lambda i:hashlib.sha256((f'seed{seed}|'+edges[i]['a']+'|'+edges[i]['b']).encode()).hexdigest())
            for position,i in enumerate(order):mask[i]=position%k
        roles=[];visible_counts=[]
        def role(i,labels):
            e=edges[i];net={e['a']:0,e['b']:0};degree={e['a']:0,e['b']:0}
            visible=[j for j in groups[e['cluster']] if mask[j]==(mask[i]+1)%k]
            assert i not in visible
            for j in visible:
                other=edges[j];sgn=2*labels[j]-1
                for node,s in ((other['a'],sgn),(other['b'],-sgn)):
                    if node in net:net[node]+=s;degree[node]+=1
            return net[e['a']]/(degree[e['a']]+1)-net[e['b']]/(degree[e['b']]+1),len(visible)
        for i,e in enumerate(edges):
            r,n=role(i,y);roles.append(r);visible_counts.append(n)
            flipped=y.copy()
            for j in groups[e['cluster']]:
                if mask[j]!=(mask[i]+1)%k:flipped[j]=1-flipped[j]
            assert role(i,flipped)[0]==r
        features=np.column_stack((depth,depth**3/10,roles));metrics={};losses={}
        for name,cols in models.items():
            if name in ('linear','cubic') and name in baseline_cache:
                metric,loss=baseline_cache[name]
            else:
                metric,loss=evaluate(features,cols)
                if name in ('linear','cubic'):baseline_cache[name]=(metric,loss)
            metrics[name]=metric;losses[name]=loss
        if k==2 and seed==0:
            previous=json.loads((HERE/'peng2024_half_mask_roles_result.json').read_text(encoding='utf-8'))
            assert np.allclose(metrics['linear_role']['probabilities'],previous['predictions']['pia_role'],atol=1e-9)
        comparison={base:{'delta_logloss':float((losses[base+'_role']-losses[base]).mean()),
                          'patients_improved':sum(float((losses[base+'_role']-losses[base])[patients==p].mean())<0 for p in pnames)} for base in ('linear','cubic')}
        key=f'k{k}_seed{seed}';results[key]={'models':metrics,'comparison':comparison,'zero_visible_targets':sum(n==0 for n in visible_counts),
            'mask':[mask[i] for i in range(len(edges))],'roles':roles}
        print(key,json.dumps({n:round(v['logloss'],6) for n,v in metrics.items()}),flush=True)
save('peng2024_role_mask_sensitivity_result.json',{'contract_sha256':sha(HERE/'peng2024_role_mask_sensitivity_contract.json'),
     'results':results,'verification':'PASS: all six masks, hidden-label invariance, gradients and previous prediction reproduction'})
