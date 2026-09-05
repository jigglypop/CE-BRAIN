"""Allen 인간 단방향 연결의 절반 가림 역할 특징 평가."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;source=HERE/'allen_human_orientation_spikes_serialized_result.json'
prior=json.loads(source.read_text(encoding='utf-8'))
save('allen_human_masked_roles_serialized_contract.json',{
    'repair':'cast NumPy count to Python int for JSON; preserve original source, contract and partial file; no analysis change',
    'question':'Does the same masked cell-role feature improve direction prediction in Allen human upper TCx?',
    'scope':'existing 80 one-way dyads, 33 slices; no new amplitude/depth selection',
    'mask':'three fixed seeds0,1,2; per-record SHA256 sort seed|a|b then alternate two folds; only opposite fold observed',
    'feature':'net outgoing/(visible incident count+1) at a minus that at b; exclude entire target fold',
    'models':['log spike ratio','log spike ratio plus role'],
    'fit':'leave whole slice out; no intercept; ridge identity; no tuning; this is a new local fit, not fixed Peng coefficients',
    'checks':'hidden fold flip invariance, exact 80 records, gradient<1e-9, previous spike-only probabilities reproduced',
    'endpoint':'pooled/equal-slice logloss, informative feature coverage, slice improvement counts; all seeds reported',
    'limits':'no equivalent pia depth; slices not donors; not matched full-model independent replication; conditional completion only',
    'source_sha256':sha(source),'code_sha256':sha(Path(__file__))})
edges=prior['edges'];assert len(edges)==80
groups=defaultdict(list)
for i,e in enumerate(edges):groups[e['experiment']].append(i)
y=np.array([e['y'] for e in edges]);sids=np.array([e['slice'] for e in edges]);snames=sorted(set(sids));results={}
for seed in (0,1,2):
    mask={}
    for eid,indices in groups.items():
        order=sorted(indices,key=lambda i:hashlib.sha256(f"seed{seed}|{edges[i]['a']}|{edges[i]['b']}".encode()).hexdigest())
        for position,i in enumerate(order):mask[i]=position%2
    def role(i,labels):
        e=edges[i];net={e['a']:0,e['b']:0};degree={e['a']:0,e['b']:0}
        for j in groups[e['experiment']]:
            if mask[j]==mask[i]:continue
            o=edges[j];sign=2*labels[j]-1
            for node,s in ((o['a'],sign),(o['b'],-sign)):
                if node in net:net[node]+=s;degree[node]+=1
        return net[e['a']]/(degree[e['a']]+1)-net[e['b']]/(degree[e['b']]+1)
    roles=[]
    for i,e in enumerate(edges):
        r=role(i,y);flipped=y.copy()
        for j in groups[e['experiment']]:
            if mask[j]==mask[i]:flipped[j]=1-flipped[j]
        assert role(i,flipped)==r;roles.append(r)
    allx=np.column_stack(([e['x'] for e in edges],roles));metrics={};losses={}
    for width,name in ((1,'spikes'),(2,'spikes_role')):
        loss=np.zeros(len(edges));pred=np.zeros(len(edges));folds=[]
        for sid in snames:
            test=sids==sid;train=~test;x=allx[train,:width];target=y[train];beta=np.zeros(width)
            for _ in range(100):
                p=expit(x@beta);g=x.T@(p-target)+beta
                if np.max(np.abs(g))<1e-9:break
                h=x.T@((p*(1-p))[:,None]*x)+np.eye(width);beta-=np.linalg.solve(h,g)
            assert np.max(np.abs(g))<1e-9
            eta=allx[test,:width]@beta;loss[test]=np.logaddexp(0,eta)-y[test]*eta;pred[test]=expit(eta)
            folds.append({'slice':int(sid),'coefficients':beta.tolist(),'logloss':float(loss[test].mean())})
        metrics[name]={'logloss':float(loss.mean()),'equal_slice_logloss':float(np.mean([f['logloss'] for f in folds])),
                       'folds':folds,'probabilities':pred.tolist()};losses[name]=loss
    assert np.allclose(metrics['spikes']['probabilities'],[e['probability'] for e in edges],atol=1e-9)
    delta=losses['spikes_role']-losses['spikes']
    results[str(seed)]={'metrics':metrics,'delta_logloss':float(delta.mean()),
        'slices_improved':sum(float(delta[sids==s].mean())<0 for s in snames),
        'nonzero_role_targets':int(sum(r!=0 for r in roles)),'roles':roles,'mask':[mask[i] for i in range(len(edges))]}
    print(seed,json.dumps({name:{k:v for k,v in m.items() if k not in ('folds','probabilities')} for name,m in metrics.items()}),flush=True)
save('allen_human_masked_roles_serialized_result.json',{'contract_sha256':sha(HERE/'allen_human_masked_roles_serialized_contract.json'),
    'dyads':len(edges),'slices':len(snames),'results':results,
    'verification':'PASS: all fixed masks, hidden-label invariance, gradients and spike baseline predictions'})
