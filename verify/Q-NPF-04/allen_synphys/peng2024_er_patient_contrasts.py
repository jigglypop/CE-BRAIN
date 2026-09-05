"""환자 분리로 세포 효과를 상쇄한 진폭 대비의 예측 오차를 평가한다."""
import csv
import io
import json
import zipfile
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
archive = ROOT/'data/external/peng2024_human/data.zip'
prior_path = HERE/'peng2024_er_strength_result.json'
assert sha(archive) == '3711f8b8b911a24b0e5fd69e6e6c845f9e8601539807a9b960118c77ba5ad68d'
save('peng2024_er_patient_contrasts_contract.json', {
    'question': 'Does reciprocity improve held-out patient amplitude contrasts beyond planar distance?',
    'status': 'exploratory cross-validation after observing this dataset; not independent confirmation',
    'support': 'prior 21 informative clusters, 11 patients; detected finite-positive amplitudes only',
    'target': 'orthonormal contrasts U_null.T log(mV); U_null from sender/receiver incidence ONLY; not individual amplitude prediction',
    'models': {'linear_base':[1], 'linear_reciprocal':[0,1], 'quadratic_base':[1,2], 'quadratic_reciprocal':[0,1,2]},
    'features': ['reciprocal','planar distance/100','(planar distance/100)^2'],
    'split': 'leave-one-patient-out; all clusters of held patient excluded from fitting',
    'score': 'held-out squared error, pooled per contrast and equally weighted patient MSE; count patient improvements',
    'gates': 'source hashes, topology-only null space, projection identity, train-test patient separation, full train rank, normal equations',
    'limits': 'sample selection and model choices already informed by data; no causal or L2 promotion; null-basis contrasts not independent biological units',
    'archive_sha256':sha(archive), 'prior_sha256':sha(prior_path), 'code_sha256':sha(Path(__file__))})
prior=json.loads(prior_path.read_text(encoding='utf-8'))['branches']['author_published']
with zipfile.ZipFile(archive) as z:
    rows=list(csv.DictReader(io.StringIO(z.read('data/tconnection_er.csv').decode('utf-8-sig'))))
lookup={(r['cellid_pre'],r['cellid_post']):r for r in rows}
records=[]
for rec in prior['records']:
    rr=[r for r in rows if r['clusterid']==rec['cluster'] and r['connected']=='1'
        and np.isfinite(float(r['avg_psp_amplitude'])) and float(r['avg_psp_amplitude'])>0]
    assert len(rr)==rec['directions'] and {r['patientid'] for r in rr}=={rec['patient']}
    nodes=sorted({r[k] for r in rr for k in ('cellid_pre','cellid_post')})
    x=np.array([[int(r['cellid_pre']==n) for n in nodes]+[int(r['cellid_post']==n) for n in nodes] for r in rr],float)
    u,s,_=np.linalg.svd(x,full_matrices=True)
    rank=int(sum(s>1e-10)); contrast=u[:,rank:].T
    assert np.max(np.abs(contrast@x))<1e-10
    assert np.allclose(contrast@contrast.T,np.eye(len(contrast)),atol=1e-10)
    features=np.array([[int(lookup[r['cellid_post'],r['cellid_pre']]['connected']),float(r['distance'])/100,(float(r['distance'])/100)**2] for r in rr])
    assert np.isfinite(features).all()
    y=np.log([float(r['avg_psp_amplitude']) for r in rr])
    transformed=np.column_stack((contrast@y,contrast@features))
    # Check the orthonormal representation against the original residual projection.
    raw=np.column_stack((y,features)); residual=raw-x@np.linalg.lstsq(x,raw,rcond=1e-10)[0]
    assert np.allclose(transformed.T@transformed,residual.T@residual,atol=1e-9)
    records.append((rec['patient'],transformed))
patients=sorted({p for p,_ in records})
models={'linear_base':[1], 'linear_reciprocal':[0,1], 'quadratic_base':[1,2], 'quadratic_reciprocal':[0,1,2]}
folds=[]
for patient in patients:
    train_ids={p for p,_ in records if p!=patient}
    assert patient not in train_ids and len(train_ids)==len(patients)-1
    train=np.concatenate([v for p,v in records if p!=patient])
    test=np.concatenate([v for p,v in records if p==patient])
    fold={'patient':patient,'contrasts':len(test),'models':{}}
    for name,cols in models.items():
        cols=np.array(cols)+1
        x=train[:,cols]; y=train[:,0]
        coef,_,rank,_=np.linalg.lstsq(x,y,rcond=1e-10)
        assert rank==len(cols)
        assert np.max(np.abs(x.T@(y-x@coef)))<1e-8
        predictions=test[:,cols]@coef
        error=test[:,0]-predictions
        fold['models'][name]={'coefficients':coef.tolist(),'sse':float(error@error),'predictions':predictions.tolist(),'targets':test[:,0].tolist()}
    folds.append(fold)
total=sum(f['contrasts'] for f in folds)
summary={name:{'sse':sum(f['models'][name]['sse'] for f in folds),
               'pooled_mse':sum(f['models'][name]['sse'] for f in folds)/total,
               'equal_patient_mse':float(np.mean([f['models'][name]['sse']/f['contrasts'] for f in folds]))} for name in models}
comparisons={}
for form in ('linear','quadratic'):
    delta=[f['models'][form+'_reciprocal']['sse']-f['models'][form+'_base']['sse'] for f in folds]
    comparisons[form]={'patients_improved':sum(d<0 for d in delta),'delta_sse':sum(delta),
        'delete_one_patient_delta_sse_range':[sum(delta)-max(delta),sum(delta)-min(delta)]}
out={'contract_sha256':sha(HERE/'peng2024_er_patient_contrasts_contract.json'),'patients':len(patients),'contrasts':total,
     'summary':summary,'comparisons':comparisons,'folds':folds,'verification':'PASS: topology projection, patient split, rank and normal equations'}
save('peng2024_er_patient_contrasts_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k!='folds'},indent=2))
