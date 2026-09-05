"""QC 고정 표본에서 깊이 외 내재 생리의 환자 제외 방향 예측."""
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;source=HERE/'planert2025_qc_inventory_result.json'
save('planert2025_intrinsic_direction_contract.json',{
    'question':'Do input resistance and rheobase improve directional prediction beyond pia depth on the fixed QC subset?',
    'scope':'523 previously eligible one-way type1 dyads, 22 patient labels; same research lineage, no independence claim',
    'models':{'depth':[0],'depth_intrinsic':[0,1,2]},
    'features':'(pia_a-pia_b)/100; log(Rin_a/Rin_b); log(rheo_a/rheo_b); no connectivity-derived predictors',
    'fit':'leave whole patient out; logistic no intercept; ridge identity; fixed units/scaling; no tuning',
    'endpoint':'pooled and equal-patient logloss, patient improvements; no causal effect',
    'checks':'finite features and positivity; patient split; gradient<1e-9; swapped endpoints imply complementary probability',
    'limits':'author QC includes pooled AP/access distribution; analysis conditional on that preprocessed selection; nonlinear depth and measurement remain alternatives',
    'source_sha256':sha(source),'code_sha256':sha(Path(__file__))})
data=json.loads(source.read_text(encoding='utf-8'))['selected'];assert len(data)==523
features=np.array([[(r['pia'][0]-r['pia'][1])/100,np.log(r['R_in'][0]/r['R_in'][1]),np.log(r['rheo'][0]/r['rheo'][1])] for r in data])
assert np.isfinite(features).all()
y=np.array([r['y'] for r in data]);ids=np.array([r['patient'] for r in data]);patients=sorted(set(ids));assert len(patients)==22
models={};losses={}
for name,cols in {'depth':[0],'depth_intrinsic':[0,1,2]}.items():
    loss=np.zeros(len(data));pred=np.zeros(len(data));folds=[]
    for patient in patients:
        test=ids==patient;train=~test;assert not set(ids[test])&set(ids[train])
        x=features[train][:,cols];target=y[train];beta=np.zeros(len(cols))
        def obj(b):return float(np.sum(np.logaddexp(0,x@b)-target*(x@b))+.5*b@b)
        for _ in range(150):
            p=expit(x@beta);g=x.T@(p-target)+beta
            if np.max(np.abs(g))<1e-9:break
            h=x.T@((p*(1-p))[:,None]*x)+np.eye(len(cols));step=np.linalg.solve(h,g);scale=1.
            while np.max(np.abs(g))>=1e-6 and obj(beta-scale*step)>obj(beta)-1e-4*scale*float(g@step):
                scale*=.5;assert scale>1e-12
            beta-=scale*step
        assert np.max(np.abs(g))<1e-9
        eta=features[test][:,cols]@beta;pred[test]=expit(eta)
        assert np.allclose(expit(-eta),1-pred[test])
        loss[test]=np.logaddexp(0,eta)-y[test]*eta
        folds.append({'patient':str(patient),'coefficients':beta.tolist(),'logloss':float(loss[test].mean())})
    models[name]={'logloss':float(loss.mean()),'equal_patient_logloss':float(np.mean([f['logloss'] for f in folds])),
                  'folds':folds,'probabilities':pred.tolist()};losses[name]=loss
delta=losses['depth_intrinsic']-losses['depth'];pd=[float(delta[ids==p].sum()) for p in patients]
out={'contract_sha256':sha(HERE/'planert2025_intrinsic_direction_contract.json'),'directions':len(data),'patients':len(patients),
     'fair_logloss':float(np.log(2)),'models':models,'patients_improved':sum(d<0 for d in pd),
     'delta_logloss':float(delta.mean()),'delete_one_patient_delta_sum_range':[sum(pd)-max(pd),sum(pd)-min(pd)],
     'verification':'PASS: fixed cohort, patient exclusion, finite features, gradients and reversal symmetry'}
save('planert2025_intrinsic_direction_result.json',out)
print(json.dumps({**{k:v for k,v in out.items() if k!='models'},'models':{k:{a:b for a,b in v.items() if a not in ('folds','probabilities')} for k,v in models.items()}},indent=2))
