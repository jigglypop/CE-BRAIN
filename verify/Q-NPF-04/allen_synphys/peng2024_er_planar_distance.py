"""기존 ER 정보 지지집합에서 거리 조정 민감도; 결과 확인 후의 탐색."""
import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
archive = ROOT/'data/external/peng2024_human/data.zip'
prior_path = HERE/'peng2024_er_strength_result.json'
assert sha(archive) == '3711f8b8b911a24b0e5fd69e6e6c845f9e8601539807a9b960118c77ba5ad68d'
save('peng2024_er_planar_distance_contract.json', {
    'question': '기존 정보 있는 ER 21기록에서 거리 조정 후 상호연결 진폭 대비',
    'status': 'exploratory sensitivity after prior result; no confirmation or causal inference',
    'revision': 'original 3D assumption failed; 261/261 distances match XY norm; preserve failed contract; use planar distance',
    'source_audit_sha256': sha(HERE/'peng2024_er_distance_source_audit.json'),
    'support': 'prior author_published informative records; finite positive amplitudes; require all distances finite and coordinate consistent',
    'models': ['sender_receiver', 'plus common linear distance/100', 'plus common linear and quadratic distance/100'],
    'patient': 'delete one patient and refit each model; no p-values or confidence intervals',
    'gates': 'XY coordinate norm and reverse distance agree; prior coefficient reproduced; direct augmented least squares agrees',
    'archive_sha256': sha(archive), 'prior_sha256': sha(prior_path), 'code_sha256': sha(Path(__file__))})
prior = json.loads(prior_path.read_text(encoding='utf-8'))['branches']['author_published']
with zipfile.ZipFile(archive) as z:
    def read(name):
        return list(csv.DictReader(io.StringIO(z.read('data/'+name+'_er.csv').decode('utf-8-sig'))))
    rows = read('tconnection')
    cells = {r['cellid'].replace(' ', ''): r for r in read('tcell')}
lookup = {(r['cellid_pre'], r['cellid_post']): r for r in rows}
groups = defaultdict(list)
for r in rows:
    groups[r['clusterid']].append(r)
residuals = []
max_error = 0.
distances = []
for record in prior['records']:
    selected = [r for r in groups[record['cluster']] if r['connected']=='1'
                and np.isfinite(float(r['avg_psp_amplitude'])) and float(r['avg_psp_amplitude'])>0]
    assert len(selected) == record['directions']
    nodes = sorted({r[k] for r in selected for k in ('cellid_pre','cellid_post')})
    x = np.array([[int(r['cellid_pre']==n) for n in nodes]+[int(r['cellid_post']==n) for n in nodes] for r in selected],float)
    y, features = [], []
    for r in selected:
        a,b = r['cellid_pre'],r['cellid_post']
        d = float(r['distance'])
        assert np.isfinite(d) and d >= 0
        ca,cb = cells[a],cells[b]
        assert ca['clusterid']==cb['clusterid']==r['clusterid']
        coords = [float(ca['coordinate_'+str(k)])-float(cb['coordinate_'+str(k)]) for k in (1,2)]
        error = abs(d-np.linalg.norm(coords)); max_error=max(max_error,error)
        assert error < 1e-5
        assert abs(d-float(lookup[b,a]['distance'])) < 1e-8
        distances.append(d)
        features.append([int(lookup[b,a]['connected']),d/100,(d/100)**2])
        y.append(np.log(float(r['avg_psp_amplitude'])))
    v = np.column_stack((y,features))
    rv = v-x@np.linalg.lstsq(x,v,rcond=1e-10)[0]
    residuals.append((record['patient'],rv,x,v))
results = {}
for count in (1,2,3):
    def fit(exclude=None):
        v=np.concatenate([r for p,r,_,_ in residuals if p!=exclude])
        design=v[:,1:count+1]; target=v[:,0]
        beta,_,rank,_=np.linalg.lstsq(design,target,rcond=1e-10)
        assert rank==count
        return beta
    beta=fit()
    # One joint fit uses the original unprojected outcomes and nuisance columns.
    from scipy.linalg import block_diag
    raw=np.concatenate([v for _,_,_,v in residuals])
    joint=np.column_stack((block_diag(*[x for _,_,x,_ in residuals]),raw[:,1:count+1]))
    direct=np.linalg.lstsq(joint,raw[:,0],rcond=1e-10)[0][-count:]
    assert np.allclose(beta,direct,atol=1e-9,rtol=0)
    leave=[float(fit(p)[0]) for p in sorted({p for p,_,_,_ in residuals})]
    results[str(count)]={'coefficients':beta.tolist(),'reciprocal_ratio':float(np.exp(beta[0])),
        'leave_one_patient_ratio_range':np.exp([min(leave),max(leave)]).tolist()}
assert np.isclose(results['1']['coefficients'][0],prior['beta'],atol=1e-10)
out={'contract_sha256':sha(HERE/'peng2024_er_planar_distance_contract.json'),
     'directions':len(distances),'coordinate_max_error':max_error,'distance_range': [min(distances),max(distances)],
     'models':results,'verification':'PASS: coordinate, reverse, baseline and independent joint-fit checks'}
save('peng2024_er_planar_distance_result.json',out)
print(json.dumps(out,indent=2))
