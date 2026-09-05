"""전반 적합·후반 예측에서 자극 표지의 추가 예측 기여; 사후 탐색."""
import json
from pathlib import Path
import numpy as np
from randi_target_response import HERE,save,sha


def predict(xtrain,ytrain,xeval):
    mean=xtrain.mean(axis=0);scale=xtrain.std(axis=0)
    assert np.all(scale>0)
    train=np.column_stack([np.ones(len(xtrain)),(xtrain-mean)/scale])
    test=np.column_stack([np.ones(len(xeval)),(xeval-mean)/scale])
    beta,_,rank,_=np.linalg.lstsq(train,ytrain,rcond=None)
    assert rank==train.shape[1] and np.linalg.cond(train)<1e8
    out=test@beta
    assert np.isfinite(out).all()
    return out,{'mean':mean.tolist(),'scale':scale.tolist(),'beta':beta.tolist(),
                'rank':int(rank),'condition_number':float(np.linalg.cond(train))}


def validate():
    rng=np.random.default_rng(20260905)
    x=rng.normal(size=(80,3)); future=rng.normal(size=(20,3))+3
    b=np.array([.1,-.4,.7]); y=.5+x@b
    pred,meta=predict(x,y,future)
    assert np.allclose(pred,.5+future@b,atol=1e-12)
    _,changed=predict(x,y,future+100)
    assert meta==changed


def main():
    validate()
    source=HERE/'rowland_prestate_adjustment_result.json'
    contract=save('rowland_forward_prediction_contract.json',{
        'question':'전반에서 적합한 자극 표지의 기여가 후반 S2 반응 예측 오차를 줄이는가',
        'source_sha256':sha(source),'parent_sha256':sha(HERE/'rowland_prestate_adjustment_contract.json'),
        'code_sha256':sha(Path(__file__)),'helper_sha256':sha(HERE/'randi_target_response.py'),
        'inherit':'자료·시행 제외·명목 전후 창·관측 척도는 전 상태 보정 계약 유지',
        'split':'첫~마지막 유효 시행의 galvo 시간 중간 이전 적합; 중간+10초 이상 평가',
        'gap':'평가 시작을 중간에서 10초 지연; 명목 반응 창 겹침 감소, 전처리 시간 혼입 제거를 보장하지 않음',
        'models':{'baseline':['elapsed_seconds','S1_pre','S2_pre'],
                  'stimulus_added':['elapsed_seconds','S1_pre','S2_pre','test_indicator']},
        'training':'절편 포함 OLS, 표준화는 학습 자료만; 후반 결과는 적합·모형 선택에 사용 안 함',
        'minimum':'학습·평가 각각 catch와 test 최소 6시행; 실패 기록 명시, 다른 split으로 교체 없음',
        'endpoints':['평가 MSE baseline와 stimulus_added','1-MSE_added/MSE_baseline','시행별 두 예측과 오차'],
        'decision':'상대 오차 감소가 양수이면 이 split의 예측 개선; 인과 또는 독립 복제 판정 아님',
        'selection':'이미 본 11세션 모두 사용한 사후 탐색; tuning 없음',
        'limits':['전처리된 pre 입력에 미래 정보 혼입 가능','실제 프레임 시각 미확인',
                  '시간 외삽·상태 변화','자극 강도·표적 수는 이 모형에 없음',
                  '세션별 개선을 독립 동물 복제로 합산하지 않음','L2 독립 calibration·holdout 조건 미충족'],
        'claim_ceiling':'BIO_EVIDENCE_L1 exploratory temporal prediction'})
    rows=[]
    for row in json.loads(source.read_text(encoding='utf-8'))['rows']:
        time=np.array(row['elapsed_seconds']);t=np.array(row['test']);y=np.array(row['s2_delta'])
        idx=np.array(row['original_indices']);cut=(time[0]+time[-1])/2
        train=time<cut;test=time>=cut+10
        assert not (train&test).any()
        result={'mouse':row['mouse'],'run':row['run'],'cut_seconds':float(cut),
                'train_indices':idx[train].tolist(),'eval_indices':idx[test].tolist(),
                'gap_indices':idx[~(train|test)].tolist(),
                'counts':{name:{'catch':int(np.sum(mask&(t==0))),'test':int(np.sum(mask&(t==1)))} for name,mask in [('train',train),('eval',test)]}}
        if min(v for counts in result['counts'].values() for v in counts.values())<6:
            rows.append({**result,'status':'INSUFFICIENT_GROUP_COUNT'});continue
        x=np.column_stack([time,row['s1_pre'],row['s2_pre']])
        xa=np.column_stack([x,t])
        try:
            p0,m0=predict(x[train],y[train],x[test]);p1,m1=predict(xa[train],y[train],xa[test])
        except (AssertionError,np.linalg.LinAlgError):
            rows.append({**result,'status':'NUMERIC_OR_RANK_FAILURE'});continue
        error0=(y[test]-p0)**2;error1=(y[test]-p1)**2
        mse0=float(error0.mean());mse1=float(error1.mean());assert mse0>0
        rows.append({**result,'status':'EVALUATED','mse_baseline':mse0,'mse_added':mse1,
                     'relative_mse_reduction':1-mse1/mse0,'baseline_fit':m0,'added_fit':m1,
                     'train_stimulus_coefficient':m1['beta'][-1]/m1['scale'][-1],
                     'observed':y[test].tolist(),'baseline_prediction':p0.tolist(),'added_prediction':p1.tolist(),
                     'squared_error_difference':(error0-error1).tolist()})
    save('rowland_forward_prediction_result.json',{'contract_sha256':sha(contract),'synthetic_validation_passed':True,'rows':rows})
    print(json.dumps([{k:v for k,v in r.items() if k in ['mouse','run','status','counts','mse_baseline','mse_added','relative_mse_reduction','train_stimulus_coefficient']} for r in rows]))


if __name__=='__main__':main()
