"""저장 예측의 원본 표지와 닫힌 형태 확률 해를 독립 대조한다."""
import json
import sqlite3
from pathlib import Path
import numpy as np
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
path=HERE/'allen_donor_prediction_result.json'
r=json.loads(path.read_text(encoding='utf-8'))
c=json.loads((HERE/'allen_donor_prediction_contract.json').read_text(encoding='utf-8'))
assert r['contract_sha256']==sha(HERE/'allen_donor_prediction_contract.json')
assert c['db_sha256']==sha(DB)
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    labels=dict(db.execute('select id,has_synapse from pair'))
y=np.array([2*labels[a]+labels[b] for a,b in r['pair_ids']])
assert y.tolist()==r['labels'] and len(set(map(tuple,r['pair_ids'])))==190
base=np.array(r['predictions']['independent']);p=base[:,2]+base[:,3]
odds=np.exp(c['gamma']);b=1+2*p*(odds-1)
t=2*odds*p*p/(b+np.sqrt(b*b-4*(odds-1)*odds*p*p))
expected=np.column_stack([1-2*p+t,p-t,p-t,t])
error=float(np.max(abs(expected-np.array(r['predictions']['minnie_frozen']))))
assert error<1e-12
for name,values in r['predictions'].items():
    table=np.array(values);assert np.all(table>0) and np.allclose(table.sum(1),1)
    loss=float(-np.log(table[np.arange(190),y]).mean())
    assert abs(loss-r['summary'][name]['joint_logloss'])<1e-12
    assert abs(sum(table[:,3])-r['summary'][name]['mutual_predicted_sum'])<1e-12
assert len(r['records'])==59 and sum(x['test_dyads'] for x in r['records'])==190
assert max(x['baseline_gradient'] for x in r['records'])<=1e-5
assert max(x['dependence_gradient'] for x in r['records'])<=1e-5
save('allen_donor_prediction_verification.json',{'result_sha256':sha(path),
    'verifier_sha256':sha(Path(__file__)),'closed_form_transfer_max_error':error,
    'checks':'DB labels; unique pairs; closed-form fixed-OR solution; all joint losses; predicted mutual sums; recorded gradient gates',
    'limits':'saved gradients checked, not independent refit; split exclusion asserted by execution code', 'status':'PASS'})
print('ALLEN_DONOR_PREDICTION_VERIFIED',error)
