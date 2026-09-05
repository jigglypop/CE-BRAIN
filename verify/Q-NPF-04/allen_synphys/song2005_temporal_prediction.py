"""Song 표에서 날짜 순 전이 예측을 검사한다. 동물 독립 검증은 아니다."""
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import sha
from superficial_ee_eligibility import save
from allen_detection_adjusted_prediction import fit
import masked_dyad_dependence as joint

HERE=Path(__file__).resolve().parent
source=HERE/'song2005_inventory_result.json'
r=json.loads(source.read_text());assert r['status']=='PASS'
prior=HERE/'pinky_dyad_prediction_contract.json'
gamma=json.loads(prior.read_text())['transfer_log_odds']
dates=sorted({x['date'] for x in r['records']});cut=int(.7*len(dates))
save('song2005_temporal_prediction_contract.json',{
    'question':'고정 Minnie 의존성 계수가 다른 종·층의 후기 기록 예측을 개선하는가?',
    'scope':'P12-P20 rat V1 L5; 공개816attempt 전체; 동물 ID/거리 없음',
    'split':'고유 날짜 정렬 앞 floor(0.7*N)일 학습, 나머지 평가; 날짜 내 분리 없음; 동물 독립성 미확인',
    'baseline':'학습 표준화 age와 calcium_mM 연속 선형항; ridge1, 무벌점 절편; 방향 공통 주변확률',
    'models':['independent','minnie_frozen','song_fitted'],
    'dependence':'방향 주변확률 고정; local상수 ridge1; Minnie logOR 고정 '+str(gamma),
    'endpoint':'후기 모든 dyad 공동logloss; mutual logloss/Brier/count; 방향동일확률이므로 단방향 상태 01/10 구분은 점수에 영향 없음',
    'limits':'사전등록 독립 확증 아님; 전체집계 이미 관찰; 날짜 경향·동물 누락·소규모기록 선택편향; 인과 없음',
    'input_sha256':sha(source),'code_sha256':sha(Path(__file__)),
    'baseline_code_sha256':sha(HERE/'allen_detection_adjusted_prediction.py'),
    'joint_code_sha256':sha(Path(joint.__file__)), 'transfer_contract_sha256':sha(prior),
    'last_train_date':dates[cut-1],'first_test_date':dates[cut]})
raw=[];labels=[];group=[]
for row in r['records']:
    for state,key in [(0,'neither'),(2,'one_way'),(3,'mutual')]:
        for _ in range(row[key]):
            raw.append([row['age'],row['calcium_mM']]);labels.append(state);group.append(row['date'])
y=np.array(labels);raw=np.array(raw);train=np.array([d<dates[cut] for d in group]);test=~train
assert len(y)==4025 and set(np.array(group)[train]).isdisjoint(set(np.array(group)[test]))
center=raw[train].mean(0);scale=raw[train].std(0);assert np.all(scale>0)
x=np.column_stack([np.ones(len(y)),(raw-center)/scale])
direction_y=np.column_stack([y//2,y%2]).ravel()
theta,error=fit(np.repeat(x[train],2,axis=0),direction_y[np.repeat(train,2)])
p=expit(x@theta)
coef,diag=joint.fit(np.ones((train.sum(),1)),p[train],p[train],y[train]);assert diag['gate_pass']
summary={};predictions={}
for name,eta in [('independent',0.),('minnie_frozen',gamma),('song_fitted',float(coef[0]))]:
    table,_,_=joint.distribution(p[test],p[test],np.full(test.sum(),eta))
    odds=np.exp(eta);b=1+2*(odds-1)*p[test]
    t=2*odds*p[test]**2/(b+np.sqrt(b*b-4*(odds-1)*odds*p[test]**2))
    assert np.allclose(t,table[:,3],atol=1e-12,rtol=0)
    summary[name]=joint.metrics(table,y[test]);predictions[name]=table.tolist()
result={'contract_sha256':sha(HERE/'song2005_temporal_prediction_contract.json'),
    'train_dates':cut,'test_dates':len(dates)-cut,'train_dyads':int(train.sum()),'test_dyads':int(test.sum()),
    'train_mutual':int(sum(y[train]==3)),'test_mutual':int(sum(y[test]==3)),
    'baseline_gradient':error,'dependence_diagnostic':diag,'baseline_coef':theta.tolist(),
    'local_logOR':float(coef[0]),'summary':summary,'predictions':predictions,
    'test_labels':y[test].tolist(),'all_gates_pass':True}
save('song2005_temporal_prediction_result.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('predictions','test_labels')},indent=2))
