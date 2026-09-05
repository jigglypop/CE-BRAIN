"""원본 표에서 날짜 분할·연결 상태·적합·예측을 별도 재검산한다."""
import json
import re
import sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
sys.path.insert(0,str(ROOT/'data/external/analysis_tools/xls_reader'))
import xlrd

HERE=Path(__file__).resolve().parent
rp=HERE/'song2005_temporal_prediction_result.json'
r=json.loads(rp.read_text(encoding='utf-8'))
c=json.loads((HERE/'song2005_temporal_prediction_contract.json').read_text(encoding='utf-8'))
xls=ROOT/'data/external/song2005/Connectivity_v10.xls'
assert sha(xls)=='9a7b741f65445fb481ea0285f3884bc43eefcae7006ee98f7c2210682d8ab47f'
book=xlrd.open_workbook(str(xls));sheet=book.sheet_by_index(0)
features=[];dates=[];truth=[]
for row in range(1,sheet.nrows):
    date,attempt,nc,nt,age,ca,string=sheet.row_values(row)
    edges=[tuple(map(int,v)) for v in re.findall(r'(\d+)_(\d+)\s*,',str(string))]
    assert len(edges)==len(set(edges))==int(nc)
    nodes=sorted({v for edge in edges for v in edge});n={2:2,6:3,12:4}[int(nt)]
    # Anonymous isolated nodes suffice for counts; no real channel identity asserted.
    nodes+=list(range(-1,-1-(n-len(nodes)),-1));a=np.zeros((n,n),int)
    for pre,post in edges:a[nodes.index(pre),nodes.index(post)]=1
    u,v=np.triu_indices(n,1);states=a[u,v]+a[v,u]
    ordered=[0]*int(sum(states==0))+[2]*int(sum(states==1))+[3]*int(sum(states==2))
    truth.extend(ordered);features.extend([[age,ca]]*len(ordered))
    dates.extend([xlrd.xldate_as_datetime(date,book.datemode).isoformat()]*len(ordered))
y=np.array(truth);raw=np.array(features);tr=np.array([d<=c['last_train_date'] for d in dates]);te=~tr
assert y[te].tolist()==r['test_labels']
assert len(set(np.array(dates)[tr]))==r['train_dates'] and len(set(np.array(dates)[te]))==r['test_dates']
x=np.column_stack([np.ones(len(y)),(raw-raw[tr].mean(0))/raw[tr].std(0)])
positives=y//2+y%2;penalty=np.array([0.,1.,1.])
def objective(theta):
    z=x[tr]@theta
    return float(np.sum(2*np.logaddexp(0,z)-positives[tr]*z)+.5*np.dot(penalty*theta,theta)), x[tr].T@(2*expit(z)-positives[tr])+penalty*theta
fit=minimize(objective,np.zeros(3),jac=True,method='BFGS',options={'gtol':1e-8})
assert max(abs(objective(fit.x)[1]))<1e-5
assert np.max(abs(fit.x-np.array(r['baseline_coef'])))<1e-6
p=expit(x[te]@fit.x);max_error=0.
for name,eta in [('independent',0.),('minnie_frozen',.3386424856601824),('song_fitted',r['local_logOR'])]:
    odds=np.exp(eta);b=1+2*(odds-1)*p
    t=2*odds*p*p/(b+np.sqrt(b*b-4*(odds-1)*odds*p*p))
    table=np.column_stack([1-2*p+t,p-t,p-t,t]);saved=np.array(r['predictions'][name])
    max_error=max(max_error,float(np.max(abs(saved-table))))
    assert np.allclose(saved,table,atol=1e-7,rtol=0)
    loss=float(-np.log(saved[np.arange(te.sum()),y[te]]).mean())
    assert abs(loss-r['summary'][name]['joint_logloss'])<1e-12
pred=np.array(r['predictions']['independent']);marginal=pred[:,2]+pred[:,3]
result={'result_sha256':sha(rp),'verifier_sha256':sha(Path(__file__)),
    'status':'PASS','max_probability_difference_with_independent_refit':max_error,
    'train_direction_rate':float(positives[tr].sum()/(2*tr.sum())),
    'test_direction_rate':float(positives[te].sum()/(2*te.sum())),
    'test_predicted_direction_rate':float(marginal.mean()),
    'test_direction_observed':int(positives[te].sum()),'test_direction_predicted':float(2*marginal.sum()),
    'limits':'원본 표에서 독립 재계산. 방향 기준선은 재적합, 의존 계수는 저장값 사용. 주변확률 오차와 의존성 오차의 인과 분해 아님.'}
save('song2005_temporal_prediction_verification.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
