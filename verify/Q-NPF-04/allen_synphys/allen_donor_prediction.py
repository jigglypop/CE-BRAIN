"""동물 단위 제외 검증으로 Allen 상층 E-E 양방향 의존성을 비교한다."""
import csv
import json
import sqlite3
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import DB, TABLE, sha
from superficial_ee_eligibility import save
import masked_dyad_dependence as joint

HERE=Path(__file__).resolve().parent


def baseline(x, positive):
    # Each row contains two assessed directions sharing the same distance.
    theta=np.zeros(x.shape[1]); penalty=np.array([0.,1.])
    for _ in range(100):
        z=x@theta; p=expit(z)
        g=x.T@(2*p-positive)+penalty*theta
        if max(abs(g))<1e-8:break
        h=x.T@(x*(2*p*(1-p))[:,None])+np.diag(penalty)
        step=np.linalg.solve(h,g)
        loss=(2*np.logaddexp(0,z)-positive*z).sum()+.5*np.dot(penalty*theta,theta)
        for factor in (1.,.5,.25,.125,.0625,.03125):
            candidate=theta-factor*step; zz=x@candidate
            new=(2*np.logaddexp(0,zz)-positive*zz).sum()+.5*np.dot(penalty*candidate,candidate)
            if new<=loss+1e-12:theta=candidate;break
        else:raise AssertionError('Newton line search failed')
    error=float(max(abs(x.T@(2*expit(x@theta)-positive)+penalty*theta)))
    assert error<=1e-5
    return theta,error


def main():
    assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
    assert sha(TABLE)=='92675aaf6fc7e032fc262cc7666998cb8009ce54e6422146d40d00ff6ae28700'
    donor_path=HERE/'superficial_ee_donors_result.json'
    donors=json.loads(donor_path.read_text());assert donors['gate']=='PASS'
    prior_path=HERE/'pinky_dyad_prediction_contract.json'
    gamma=json.loads(prior_path.read_text())['transfer_log_odds']
    save('allen_donor_prediction_contract.json', {
        'question':'Minnie에서 고정한 양방향 의존성 계수가 Allen 상층 E-E의 다른 동물 연결 예측을 개선하는가?',
        'selection':'기존 양방향 검사 수>10인 190쌍, 공식 이름에서 복원한 59개 donor 그룹',
        'split':'leave-one-donor-out; 같은 donor의 모든 방향·절편·실험을 함께 제외',
        'baseline':'방향 공통 logit=절편+표준화 log1p(distance_m/0.0001); 표준화는 학습 자료만; 기울기 ridge 1, 절편 무벌점; 세포별 효과 없음',
        'models':['independent','minnie_frozen','allen_fitted'],
        'dependence':'방향 주변확률 고정; local 상수 logOR ridge1, 학습 자료만; 전이 상수는 기존 Minnie 값',
        'gamma':gamma,'primary':'모든 가린 쌍의 4상태 logloss; donor 동일가중 평균도 보고',
        'secondary':'상호연결 logloss/Brier/예측 합, donor별 차이',
        'limits':'이미 관찰한 3개 상호연결의 탐색적 내부 검증; 표본/검출 차이; 독립 사전등록 확증·인과 검정 아님; 거리 기준선도 새로 설정됨',
        'gate':'학습 gradient<=1e-5; 모든 쌍 정확히 한번 예측; 가린 donor가 학습 집합에 없음; 확률합과 주변확률 일치',
        'code_sha256':sha(Path(__file__)),'joint_code_sha256':sha(Path(joint.__file__)),
        'donor_result_sha256':sha(donor_path),'transfer_contract_sha256':sha(prior_path),
        'db_sha256':sha(DB),'table_sha256':sha(TABLE)})
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        spikes=dict(db.execute('select id,n_ex_test_spikes from pair'))
    with TABLE.open(encoding='utf-8',newline='') as f:
        rows=[r for r in csv.DictReader(f) if r['species']=='mouse' and r['region']=='VisP'
              and r['class_pair']=='ex|ex' and all(v in ('2','2/3','3') for v in r['layer_pair'].split('|'))
              and all(spikes[int(r[k])] is not None and spikes[int(r[k])]>10 for k in ('pair_ab','pair_ba'))]
    groups=np.array([donors['slice_to_donor'][r['slice_id']] for r in rows])
    raw=np.log1p(np.array([float(r['distance_m']) for r in rows])/0.0001)
    a=np.array([int(r['label_ab']) for r in rows]);b=np.array([int(r['label_ba']) for r in rows]);y=2*a+b
    assert len(rows)==190 and len(set(groups))==59
    predictions={k:np.zeros((len(rows),4)) for k in ('independent','minnie_frozen','allen_fitted')}
    seen=np.zeros(len(rows),int);records=[]
    for donor in sorted(set(groups)):
        te=groups==donor;tr=~te;assert donor not in groups[tr]
        center=raw[tr].mean();scale=raw[tr].std();assert scale>0
        x=np.column_stack([np.ones(len(rows)),(raw-center)/scale])
        theta,error=baseline(x[tr],(a+b)[tr]);p=expit(x@theta)
        coef,diag=joint.fit(np.ones((tr.sum(),1)),p[tr],p[tr],y[tr]);assert diag['gate_pass']
        record={'donor':donor,'test_dyads':int(te.sum()),'test_mutual':int(sum(y[te]==3)),
                'baseline_coef':theta.tolist(),'baseline_gradient':error,'local_gamma':float(coef[0]),
                'dependence_gradient':diag['max_gradient'],'metrics':{}}
        for name,eta in [('independent',0.),('minnie_frozen',gamma),('allen_fitted',float(coef[0]))]:
            table,_,_=joint.distribution(p[te],p[te],np.full(te.sum(),eta))
            assert np.allclose(table.sum(1),1,atol=1e-12)
            assert np.allclose(table[:,2]+table[:,3],p[te],atol=1e-12)
            assert np.allclose(table[:,1]+table[:,3],p[te],atol=1e-12)
            if eta==0:assert np.allclose(table[:,3],p[te]**2,atol=1e-12)
            predictions[name][te]=table;record['metrics'][name]=joint.metrics(table,y[te])
        seen[te]+=1;records.append(record)
    assert np.all(seen==1)
    summary={k:joint.metrics(v,y) for k,v in predictions.items()}
    for name in summary:
        summary[name]['equal_donor_joint_logloss']=float(np.mean([r['metrics'][name]['joint_logloss'] for r in records]))
        summary[name]['donors_improved_vs_independent']=sum(r['metrics'][name]['joint_logloss']<r['metrics']['independent']['joint_logloss'] for r in records)
    result={'contract_sha256':sha(HERE/'allen_donor_prediction_contract.json'),'summary':summary,'records':records,
            'predictions':{k:v.tolist() for k,v in predictions.items()},
            'pair_ids':[[int(r['pair_ab']),int(r['pair_ba'])] for r in rows], 'labels':y.tolist(),
            'all_gates_pass':True}
    save('allen_donor_prediction_result.json',result)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
