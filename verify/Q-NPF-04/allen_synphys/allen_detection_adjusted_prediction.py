"""검사 수와 실험 조건을 고려한 동물 제외 예측 민감도."""
import json
import sqlite3
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save
from masked_dyad_dependence import distribution,metrics

HERE=Path(__file__).resolve().parent


def fit(x,y):
    theta=np.zeros(x.shape[1]);penalty=np.ones(x.shape[1]);penalty[0]=0
    for _ in range(100):
        z=x@theta;p=expit(z);g=x.T@(p-y)+penalty*theta
        if max(abs(g))<1e-8:break
        h=x.T@(x*(p*(1-p))[:,None])+np.diag(penalty)
        step=np.linalg.solve(h,g)
        old=(np.logaddexp(0,z)-y*z).sum()+.5*np.dot(penalty*theta,theta)
        for factor in (1.,.5,.25,.125,.0625,.03125):
            candidate=theta-factor*step;zz=x@candidate
            loss=(np.logaddexp(0,zz)-y*zz).sum()+.5*np.dot(penalty*candidate,candidate)
            if loss<=old+1e-12:theta=candidate;break
        else:raise AssertionError('line search')
    error=float(max(abs(x.T@(expit(x@theta)-y)+penalty*theta)))
    assert error<=1e-5
    return theta,error


def main():
    prior_path=HERE/'allen_donor_prediction_result.json'
    prior=json.loads(prior_path.read_text(encoding='utf-8'))
    cp=HERE/'allen_donor_prediction_contract.json';old=json.loads(cp.read_text(encoding='utf-8'))
    assert sha(DB)==old['db_sha256']
    assert sha(prior_path)==json.loads((HERE/'allen_donor_prediction_verification.json').read_text())['result_sha256']
    donor_path=HERE/'superficial_ee_donors_result.json';assert sha(donor_path)==old['donor_result_sha256']
    donors=json.loads(donor_path.read_text())['slice_to_donor']
    save('allen_detection_adjusted_prediction_contract.json',{
        'question':'방향별 검사 수와 실험 조건을 고려해도 고정 Minnie logOR의 개선이 남는가?',
        'scope':'기존190쌍, 같은 leave-one-donor-out; label/사례/분할 변경 없음',
        'baselines':{'distance':'기존 log1p(distance/100um) 재현',
            'distance_spikes':'거리+방향별 log1p(n_ex_test_spikes)',
            'distance_spikes_conditions':'위 연속 변수+acsf/internal/project_name/target_temperature 범주'},
        'preprocessing':'연속 표준화와 범주 목록은 학습 방향만; 결측 범주 명시, 미지 범주 모두0; 절편 무벌점, 나머지 ridge1',
        'transfer':'고정 logOR '+str(old['gamma'])+'; 각 기준선의 방향별 확률 고정 후 독립과 비교',
        'endpoint':'가린 쌍 공동 logloss, 상호연결 logloss/Brier/예측합; 모든 기준선 보고, 최선만 선택하지 않음',
        'limits':'검사 수는 무작위 사전 공변량이 아니며 관측 과정과 연결될 수 있음; 조건부 예측 민감도, 검출편향의 인과 교정 아님; 알려진 작은 표본의 탐색',
        'gate':'gradient<=1e-5; 거리만 기존 예측 재현; 모든 쌍 한번; 전이 닫힌 해 및 주변확률 일치',
        'code_sha256':sha(Path(__file__)),'prior_sha256':sha(prior_path),'prior_contract_sha256':sha(cp)})
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        sql='''select p.id,p.has_synapse,p.distance,p.n_ex_test_spikes,e.slice_id,e.acsf,e.internal,e.project_name,e.target_temperature
               from pair p join experiment e on e.id=p.experiment_id'''
        lookup={r[0]:r[1:] for r in db.execute(sql)}
    pairs=prior['pair_ids'];flat=[lookup[k] for pair in pairs for k in pair]
    labels=np.array([r[0] for r in flat]);groups=np.array([donors[str(r[3])] for r in flat])
    assert np.all(groups[::2]==groups[1::2])
    y=2*labels[::2]+labels[1::2];assert y.tolist()==prior['labels']
    raw=np.array([[np.log1p(r[1]/.0001),np.log1p(r[2])] for r in flat])
    cats=np.array([[str(v) if v is not None else '<missing>' for v in r[4:]] for r in flat])
    result={};closed_error=0.
    for model,numeric,conditions in [('distance',1,False),('distance_spikes',2,False),('distance_spikes_conditions',2,True)]:
        predicted={name:np.zeros((190,4)) for name in ('independent','minnie_frozen')};seen=np.zeros(190,int);records=[]
        for donor in sorted(set(groups)):
            train=groups!=donor;test=~train;te=test[::2]
            center=raw[train,:numeric].mean(0);scale=raw[train,:numeric].std(0);scale=np.where(scale>0,scale,1)
            columns=[np.ones((380,1)),(raw[:,:numeric]-center)/scale]
            unseen=0
            if conditions:
                for j in range(cats.shape[1]):
                    values=sorted(set(cats[train,j]))
                    columns.append(np.column_stack([cats[:,j]==v for v in values]))
                    unseen+=sum(v not in values for v in cats[test,j])
            x=np.column_stack(columns);theta,error=fit(x[train],labels[train]);pr=expit(x@theta)
            p=pr[::2][te];q=pr[1::2][te]
            record={'donor':donor,'gradient':error,'unseen_test_category_entries':int(unseen),'metrics':{}}
            for name,eta in [('independent',0.),('minnie_frozen',old['gamma'])]:
                table,_,_=distribution(p,q,np.full(len(p),eta))
                assert np.allclose(table[:,2]+table[:,3],p,atol=1e-12)
                assert np.allclose(table[:,1]+table[:,3],q,atol=1e-12)
                odds=np.exp(eta);b=1+(odds-1)*(p+q)
                t=2*odds*p*q/(b+np.sqrt(b*b-4*(odds-1)*odds*p*q))
                closed_error=max(closed_error,float(max(abs(t-table[:,3]))))
                predicted[name][te]=table;record['metrics'][name]=metrics(table,y[te])
            records.append(record);seen[te]+=1
        assert np.all(seen==1)
        if model=='distance':
            assert np.allclose(predicted['independent'],prior['predictions']['independent'],atol=1e-8,rtol=0)
        result[model]={'summary':{k:metrics(v,y) for k,v in predicted.items()},'records':records,
                       'predictions':{k:v.tolist() for k,v in predicted.items()}}
    assert closed_error<1e-12
    save('allen_detection_adjusted_prediction_result.json',{'contract_sha256':sha(HERE/'allen_detection_adjusted_prediction_contract.json'),
        'models':result,'closed_form_max_error':closed_error,'all_gates_pass':True})
    print(json.dumps({k:v['summary'] for k,v in result.items()},indent=2))


if __name__=='__main__':main()
