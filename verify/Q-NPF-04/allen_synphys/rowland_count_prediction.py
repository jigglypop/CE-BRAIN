"""기존 시간 분할에서 명목 표적 수 선형항의 추가 예측 기여."""
import json
from pathlib import Path
import numpy as np
from randi_target_response import HERE,save,sha
from rowland_forward_prediction import predict,validate


def main():
    validate()
    names=['rowland_forward_prediction_result.json','rowland_prestate_adjustment_result.json','rowland_target_inventory_result.json']
    contract=save('rowland_count_prediction_contract.json',{
        'question':'기존 이진 자극 모형에 명목 표적 수를 추가하면 후반 예측 오차가 감소하는가',
        'inputs':{n:sha(HERE/n) for n in names},'code_sha256':sha(Path(__file__)),
        'dependencies':{n:sha(HERE/n) for n in ['rowland_forward_prediction.py','randi_target_response.py']},
        'inherit':'기존 전반 학습·후반 평가·10초 완충·명목 신호 창·시행 제외 유지',
        'baseline':'절편+시간+S1_pre+S2_pre+시험 자극 여부',
        'additional':'명목 표적 수 0,5,10,20,30,40,50의 선형항 한 개; 공간 ROI 수는 사용 안 함',
        'fit':'학습 시행만 표준화·OLS 적합; 튜닝 및 범주별 계수 선택 없음',
        'endpoint':'후반 MSE; 기존 이진 모형 대비 1-MSE_count/MSE_binary; 집단별 MSE도 모두 보고',
        'rank_gate':'rank 부족·상수 열·조건수>=1e8은 미평가; 표본이나 분할 교체 없음',
        'limits':['이미 본 자료의 사후 탐색','명목 수와 반응의 선형성 가정',
                  'J064 run11의 명목30은 학습에 없음; 선형 보간이며 해당 수준 직접 학습 아님',
                  '명목 수는 활성 세포 수·광출력·표적 identity 아님','작은 학습 표본과 시간 변화',
                  '추가항과 함께 기존 계수도 재적합','독립 확인·인과효과·뇌 구조 판정 아님'],
        'claim_ceiling':'BIO_EVIDENCE_L1 exploratory temporal prediction'})
    preds=json.loads((HERE/names[0]).read_text(encoding='utf-8'))['rows']
    summaries={(r['mouse'],r['run']):r for r in json.loads((HERE/names[1]).read_text(encoding='utf-8'))['rows']}
    inventories={(r['mouse'],r['run']):r for r in json.loads((HERE/names[2]).read_text(encoding='utf-8'))['rows']}
    rows=[]
    for p in preds:
        key=(p['mouse'],p['run']);s=summaries[key];inv=inventories[key]
        idx=s['original_indices'];lookup={v:i for i,v in enumerate(idx)}
        countmap=dict(zip(inv['original_indices'],inv['nominal_counts']))
        count=np.array([countmap[i] for i in idx]);t=np.array(s['test']);assert np.array_equal(count>0,t==1)
        train=np.array([lookup[i] for i in p['train_indices']]);test=np.array([lookup[i] for i in p['eval_indices']])
        x=np.column_stack([s['elapsed_seconds'],s['s1_pre'],s['s2_pre'],t]);y=np.array(s['s2_delta'])
        binary,_=predict(x[train],y[train],x[test])
        assert np.allclose(binary,p['added_prediction'],atol=1e-12)
        assert np.allclose(y[test],p['observed'],atol=1e-12)
        xc=np.column_stack([x,count])
        result={'mouse':key[0],'run':key[1],'train_indices':p['train_indices'],'eval_indices':p['eval_indices'],
                'unseen_eval_levels':inv['unseen_eval_levels']}
        try:pred,meta=predict(xc[train],y[train],xc[test])
        except (AssertionError,np.linalg.LinAlgError):
            rows.append({**result,'status':'NUMERIC_OR_RANK_FAILURE'});continue
        e0=(y[test]-binary)**2;e1=(y[test]-pred)**2
        groups={}
        for name,mask in [('catch',t[test]==0),('test',t[test]==1)]:
            groups[name]={'n':int(mask.sum()),'mse_binary':float(e0[mask].mean()),'mse_count':float(e1[mask].mean())}
        rows.append({**result,'status':'EVALUATED','mse_binary':float(e0.mean()),'mse_count':float(e1.mean()),
            'relative_reduction_vs_binary':float(1-e1.mean()/e0.mean()),
            'relative_reduction_vs_no_stimulus':float(1-e1.mean()/p['mse_baseline']),
            'count_coefficient':meta['beta'][-1]/meta['scale'][-1],
            'fit':meta,'groups':groups,'observed':y[test].tolist(),'count_prediction':pred.tolist(),
            'eval_nominal':count[test].tolist(),'squared_error_improvement':(e0-e1).tolist()})
    save('rowland_count_prediction_result.json',{'contract_sha256':sha(contract),'rows':rows})
    print(json.dumps([{k:v for k,v in r.items() if k in ['mouse','run','status','mse_binary','mse_count','relative_reduction_vs_binary','relative_reduction_vs_no_stimulus','count_coefficient']} for r in rows]))


if __name__=='__main__':main()
