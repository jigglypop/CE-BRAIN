"""표적 방향을 가린 국소 역할 특징의 환자 제외 예측."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
source=HERE/'peng2024_pia_direction_result.json'
prior=json.loads(source.read_text(encoding='utf-8'))
save('peng2024_masked_roles_polished_contract.json',{
    'repair':'Original optimizer failed unchanged gradient gate; near convergence use full Newton correction to avoid objective subtraction cancellation; preserve failed source and contract',
    'question':'Does other-edge directional imbalance improve masked orientation prediction beyond pia depth?',
    'scope':'same ER 881 finite-pia one-way dyads; 22 patients; use only other retained dyads in the same recording',
    'feature':'for each target (a,b), omit target entirely; r=(out_a-in_a)/(incident_a+1)-(out_b-in_b)/(incident_b+1) on other edges',
    'models':['pia difference/100 only','pia difference/100 and r'],
    'fit':'leave entire patient out of coefficient training; ridge identity, no intercept or tuning; each training target likewise omitted from its own features',
    'task':'conditional network completion with all other same-record orientations observed, not prediction of a fully unseen graph; no joint graph likelihood',
    'checks':'target flip leaves features unchanged; vertex swap negates role; train/test patient split; gradient; reproduce earlier depth-only losses',
    'endpoint':'masked directional logloss; pooled and equal-patient means; count patient improvements; delete-one-patient fixed-score sensitivity',
    'limits':'posthoc exploration; roles may encode layer nonlinearities, geometry or detection; not intrinsic cell-type or causal evidence',
    'source_sha256':sha(source),'code_sha256':sha(Path(__file__))})
edges=prior['edges'];groups=defaultdict(list)
for i,e in enumerate(edges):groups[e['cluster']].append(i)
def role(target,a,b):
    net={a:0,b:0};degree={a:0,b:0}
    for j in groups[edges[target]['cluster']]:
        if j==target:continue
        e=edges[j];sign=2*e['y']-1
        for node,sgn in ((e['a'],sign),(e['b'],-sign)):
            if node in net:net[node]+=sgn;degree[node]+=1
    return net[a]/(degree[a]+1)-net[b]/(degree[b]+1)
features=[]
for i,e in enumerate(edges):
    r=role(i,e['a'],e['b']);assert np.isclose(role(i,e['b'],e['a']),-r)
    e['y']=1-e['y'];assert role(i,e['a'],e['b'])==r;e['y']=1-e['y']
    features.append([e['x'],r])
xall=np.array(features);yall=np.array([e['y'] for e in edges]);pids=np.array([e['patient'] for e in edges])
folds=[];losses={};predictions={}
for width,name in ((1,'pia'),(2,'pia_role')):
    loss=np.zeros(len(edges));pred=np.zeros(len(edges));rows=[]
    for patient in sorted(set(pids)):
        test=pids==patient;train=~test;assert not set(pids[train])&set(pids[test])
        x=xall[train,:width];y=yall[train];beta=np.zeros(width)
        def objective(b):return float(np.sum(np.logaddexp(0,x@b)-y*(x@b))+.5*(b@b))
        for _ in range(100):
            p=expit(x@beta);g=x.T@(p-y)+beta
            if np.max(np.abs(g))<1e-9:break
            h=x.T@((p*(1-p))[:,None]*x)+np.eye(width);step=np.linalg.solve(h,g);scale=1.
            while np.max(np.abs(g))>=1e-6 and objective(beta-scale*step)>objective(beta)-1e-4*scale*float(g@step):
                scale*=.5;assert scale>1e-10
            beta-=scale*step
        assert np.max(np.abs(g))<1e-9
        eta=xall[test,:width]@beta;pred[test]=expit(eta);loss[test]=np.logaddexp(0,eta)-yall[test]*eta
        rows.append({'patient':str(patient),'directions':int(test.sum()),'coefficients':beta.tolist(),'logloss':float(loss[test].mean())})
    losses[name]=loss;predictions[name]=pred.tolist();folds.append({'model':name,'folds':rows})
assert np.isclose(losses['pia'].mean(),prior['pia_logloss'],atol=1e-10)
patient_delta=[float(np.sum((losses['pia_role']-losses['pia'])[pids==p])) for p in sorted(set(pids))]
summary={name:{'pooled_logloss':float(loss.mean()),'equal_patient_logloss':float(np.mean([loss[pids==p].mean() for p in sorted(set(pids))]))} for name,loss in losses.items()}
out={'contract_sha256':sha(HERE/'peng2024_masked_roles_polished_contract.json'),'directions':len(edges),'patients':len(set(pids)),
     'summary':summary,'patients_improved':sum(d<0 for d in patient_delta),
     'delta_loss_sum':sum(patient_delta),'delete_one_patient_delta_sum_range':[sum(patient_delta)-max(patient_delta),sum(patient_delta)-min(patient_delta)],
     'folds':folds,'predictions':predictions,'features':features,
     'verification':'PASS: target-flip exclusion, swap symmetry, patient separation, gradients and depth baseline reproduction'}
save('peng2024_masked_roles_polished_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ('folds','predictions','features')},indent=2))
