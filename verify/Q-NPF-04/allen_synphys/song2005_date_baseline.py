"""학습 기간 내부 선택으로 선형 날짜 기준선을 평가한다."""
import json
from datetime import datetime
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import sha
from superficial_ee_eligibility import save
from allen_detection_adjusted_prediction import fit
from masked_dyad_dependence import distribution,metrics

HERE=Path(__file__).resolve().parent
ip=HERE/'song2005_inventory_result.json'
r=json.loads(ip.read_text());dates=sorted({v['date'] for v in r['records']})
assert len(dates)==186
save('song2005_date_baseline_contract.json',{
    'question':'나이·칼슘 기준선에 선형 날짜 항을 추가하면 후기 방향별 연결 예측 오차가 줄어드는가?',
    'split':'최초90일 내부학습, 다음40일 내부검증; 기존 앞130일로 재적합, 마지막56일 평가',
    'candidates':['age_calcium','age_calcium_date'],
    'selection':'내부검증 방향별 logloss 낮은 후보 선택; 동률은 기존 기준선; 날짜 항 하나만 비교',
    'fitting':'학습 부분만 표준화; 절편 무벌점, 기울기 ridge1; 가중치/시간창 탐색 없음',
    'test':'후기 전체1394쌍; 선택 고정 후 두 후보 모두 공개; Minnie 계수도 고정',
    'limits':'후기 결과를 이미 본 탐색적 설계; 날짜는 동물ID 아님; 시간 외삽은 인과설명 아님',
    'source_sha256':sha(ip),'code_sha256':sha(Path(__file__)),
    'fit_code_sha256':sha(HERE/'allen_detection_adjusted_prediction.py')})
raw=[];y=[];day=[]
for row in r['records']:
    for state,key in [(0,'neither'),(2,'one_way'),(3,'mutual')]:
        count=row[key]
        raw.extend([[row['age'],row['calcium_mM'],datetime.fromisoformat(row['date']).toordinal()]]*count)
        y.extend([state]*count);day.extend([row['date']]*count)
raw=np.array(raw);y=np.array(y);day=np.array(day);direction=np.column_stack([y//2,y%2]).ravel()
inner=day<dates[90];valid=(day>=dates[90])&(day<dates[130]);train=day<dates[130];test=~train
def run(mask,n):
    center=raw[mask,:n].mean(0);scale=raw[mask,:n].std(0);assert np.all(scale>0)
    x=np.column_stack([np.ones(len(y)),(raw[:,:n]-center)/scale])
    coef,error=fit(np.repeat(x[mask],2,axis=0),direction[np.repeat(mask,2)])
    return expit(x@coef),coef,error
def directional_loss(p,mask):
    k=(y//2+y%2)[mask];v=p[mask]
    return float(-np.mean(k*np.log(v)+(2-k)*np.log1p(-v))/2)
validation={}
for name,n in [('age_calcium',2),('age_calcium_date',3)]:
    p,coef,error=run(inner,n)
    validation[name]={'direction_logloss':directional_loss(p,valid),'gradient':error,'coef':coef.tolist()}
selected=min(validation,key=lambda k:validation[k]['direction_logloss'])
save('song2005_date_baseline_selection.json',{'contract_sha256':sha(HERE/'song2005_date_baseline_contract.json'),
     'validation':validation,'selected':selected,'inner_dyads':int(inner.sum()),'validation_dyads':int(valid.sum())})
results={}
for name,n in [('age_calcium',2),('age_calcium_date',3)]:
    p,coef,error=run(train,n);out={}
    for label,eta in [('independent',0.),('minnie_frozen',.3386424856601824)]:
        table,_,_=distribution(p[test],p[test],np.full(test.sum(),eta))
        assert np.allclose(table[:,2]+table[:,3],p[test],atol=1e-12)
        out[label]=metrics(table,y[test])
    results[name]={'direction_logloss':directional_loss(p,test),'predicted_direction_count':float(2*p[test].sum()),
                   'gradient':error,'coef':coef.tolist(),'joint':out}
old=json.loads((HERE/'song2005_temporal_prediction_result.json').read_text())
assert abs(results['age_calcium']['joint']['independent']['joint_logloss']-old['summary']['independent']['joint_logloss'])<1e-12
result={'selection_sha256':sha(HERE/'song2005_date_baseline_selection.json'),'selected':selected,
        'results':results,'observed_test_directions':int(sum((y//2+y%2)[test])),
        'test_dyads':int(test.sum()),'all_gates_pass':True}
save('song2005_date_baseline_result.json',result)
print(json.dumps({'validation':validation,**result},indent=2))
