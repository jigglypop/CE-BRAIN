"""동일 QC 표본의 생리 특징과 가림 역할 특징을 비교한다."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;source=HERE/'planert2025_qc_inventory_result.json'
previous=HERE/'planert2025_intrinsic_direction_result.json'
save('planert2025_matched_role_physiology_contract.json',{
    'question':'On identical QC-selected dyads, do visible connection roles add information beyond depth and intrinsic physiology?',
    'scope':'same 523 dyads, 22 patients; no new cohort; existing author QC and duplicate-cluster exclusions retained',
    'masks':'seed0,1,2; per-record sorted SHA256(seed|a|b), alternating folds; target sees only opposite fold',
    'features':'depth difference/100, log Rin ratio, log rheobase ratio, visible net-degree normalized role contrast',
    'models':{'depth':[0],'physiology':[0,1,2],'role':[0,3],'both':[0,1,2,3]},
    'fit':'leave whole patient out, no intercept, ridge identity, no tuning; observed other directions permitted as task input',
    'checks':'hidden-fold direction flips do not change features; original depth/physiology probabilities reproduced; gradients<1e-9',
    'limits':'conditional completion; no causal mediation or stable cell identity; author pooled QC; all seeds reported',
    'source_sha256':sha(source),'previous_sha256':sha(previous),'code_sha256':sha(Path(__file__))})
data=json.loads(source.read_text(encoding='utf-8'))['selected'];prior=json.loads(previous.read_text(encoding='utf-8'))
base=np.array([[(r['pia'][0]-r['pia'][1])/100,np.log(r['R_in'][0]/r['R_in'][1]),np.log(r['rheo'][0]/r['rheo'][1])] for r in data])
y=np.array([r['y'] for r in data]);pid=np.array([r['patient'] for r in data]);patients=sorted(set(pid));groups=defaultdict(list)
for i,r in enumerate(data):groups[r['cluster']].append(i)
def fit(features,cols):
    loss=np.zeros(len(data));pred=np.zeros(len(data));folds=[]
    for patient in patients:
        test=pid==patient;train=~test;x=features[train][:,cols];target=y[train];b=np.zeros(len(cols))
        def obj(v):return float(np.sum(np.logaddexp(0,x@v)-target*(x@v))+.5*v@v)
        for _ in range(150):
            p=expit(x@b);g=x.T@(p-target)+b
            if np.max(np.abs(g))<1e-9:break
            h=x.T@((p*(1-p))[:,None]*x)+np.eye(len(cols));step=np.linalg.solve(h,g);scale=1.
            while np.max(np.abs(g))>=1e-6 and obj(b-scale*step)>obj(b)-1e-4*scale*float(g@step):
                scale*=.5;assert scale>1e-12
            b-=scale*step
        assert np.max(np.abs(g))<1e-9
        eta=features[test][:,cols]@b;pred[test]=expit(eta);loss[test]=np.logaddexp(0,eta)-y[test]*eta
        folds.append({'patient':str(patient),'beta':b.tolist(),'logloss':float(loss[test].mean())})
    return {'logloss':float(loss.mean()),'equal_patient_logloss':float(np.mean([f['logloss'] for f in folds])),
            'folds':folds,'probabilities':pred.tolist()},loss
results={};cache={}
for seed in (0,1,2):
    mask={}
    for cluster,indices in groups.items():
        order=sorted(indices,key=lambda i:hashlib.sha256(f"seed{seed}|{data[i]['a']}|{data[i]['b']}".encode()).hexdigest())
        for j,i in enumerate(order):mask[i]=j%2
    def role(i,labels):
        r=data[i];net={r['a']:0,r['b']:0};degree={r['a']:0,r['b']:0}
        for j in groups[r['cluster']]:
            if mask[i]==mask[j]:continue
            other=data[j];sign=2*labels[j]-1
            for node,s in ((other['a'],sign),(other['b'],-sign)):
                if node in net:net[node]+=s;degree[node]+=1
        return net[r['a']]/(degree[r['a']]+1)-net[r['b']]/(degree[r['b']]+1)
    roles=[]
    for i,r in enumerate(data):
        value=role(i,y);flipped=y.copy()
        for j in groups[r['cluster']]:
            if mask[j]==mask[i]:flipped[j]=1-flipped[j]
        assert role(i,flipped)==value;roles.append(value)
    features=np.column_stack((base,roles));metrics={};losses={}
    for name,cols in {'depth':[0],'physiology':[0,1,2],'role':[0,3],'both':[0,1,2,3]}.items():
        if name in cache:m,l=cache[name]
        else:m,l=fit(features,cols)
        if name in ('depth','physiology'):cache[name]=m,l
        metrics[name]=m;losses[name]=l
    assert np.allclose(metrics['depth']['probabilities'],prior['models']['depth']['probabilities'],atol=1e-9)
    assert np.allclose(metrics['physiology']['probabilities'],prior['models']['depth_intrinsic']['probabilities'],atol=1e-9)
    comparisons={}
    for label,new,old in (('roles_after_physiology','both','physiology'),('physiology_after_roles','both','role')):
        delta=losses[new]-losses[old]
        comparisons[label]={'delta_logloss':float(delta.mean()),'patients_improved':sum(float(delta[pid==p].mean())<0 for p in patients)}
    results[str(seed)]={'metrics':metrics,'comparisons':comparisons,'mask':[mask[i] for i in range(len(data))],'roles':roles}
    print(seed,json.dumps({n:round(m['logloss'],6) for n,m in metrics.items()}),flush=True)
save('planert2025_matched_role_physiology_result.json',{'contract_sha256':sha(HERE/'planert2025_matched_role_physiology_contract.json'),
    'results':results,'verification':'PASS: fixed sample, hidden-label invariance, prior predictions and all gradients'})
