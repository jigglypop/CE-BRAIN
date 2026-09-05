"""고정 예측 손실의 연결 상태별 기여와 동물 재가중 민감도."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'allen_donor_prediction_result.json'
    receipt=json.loads((HERE/'allen_donor_prediction_verification.json').read_text(encoding='utf-8'))
    assert sha(path)==receipt['result_sha256'] and receipt['status']=='PASS'
    r=json.loads(path.read_text(encoding='utf-8'))
    save('allen_prediction_score_audit_contract.json',{
        'question':'관측한 예측 개선이 어느 연결 상태와 동물의 점수에 의존하는가?',
        'scope':'저장된 190쌍, 59 donor 예측을 고정; 모델 재적합이나 사례 재선택 없음',
        'analysis':'00/one-way/11 손실합 분해; 각 donor 점수만 하나씩 제외; donor 59개를 복원추출해 20000회 재가중',
        'seed':2026092700,'resampling':'예측 고정, donor별 손실합·쌍 수 함께 복원추출; 2.5/97.5 백분위는 조건부 재가중 범위',
        'limits':'겹치는 학습집합의 적합 불확도 미포함; 유효한 일반화 신뢰구간/p값/새 생물 표본이 아님; 제외는 평가점수만이며 원분석을 대체하지 않음',
        'result_sha256':sha(path),'code_sha256':sha(Path(__file__))})
    y=np.array(r['labels']);idx=np.arange(len(y))
    base=np.array(r['predictions']['independent'])
    base_loss=-np.log(base[idx,y]);out={}
    counts=np.array([x['test_dyads'] for x in r['records']])
    assert counts.sum()==len(y)==190 and len(counts)==59
    draw=np.random.default_rng(2026092700).integers(0,len(counts),size=(20000,len(counts)))
    for name in ('minnie_frozen','allen_fitted'):
        loss=-np.log(np.array(r['predictions'][name])[idx,y]);delta=loss-base_loss
        donor_sum=np.array([(x['metrics'][name]['joint_logloss']-x['metrics']['independent']['joint_logloss'])*x['test_dyads'] for x in r['records']])
        assert abs(donor_sum.sum()-delta.sum())<1e-12
        state={}
        for label,mask in [('neither',y==0),('one_way',(y==1)|(y==2)),('mutual',y==3)]:
            state[label]={'dyads':int(mask.sum()),'loss_change_sum':float(delta[mask].sum()),'loss_change_mean':float(delta[mask].mean())}
        assert abs(sum(x['loss_change_sum'] for x in state.values())-delta.sum())<1e-12
        delete=(donor_sum.sum()-donor_sum)/(counts.sum()-counts)
        resampled=donor_sum[draw].sum(1)/counts[draw].sum(1)
        out[name]={'loss_change_mean':float(delta.mean()),'states':state,
            'delete_one_donor_score_range':[float(delete.min()),float(delete.max())],
            'reweight_percentile_2_5_97_5':np.quantile(resampled,[.025,.975]).tolist(),
            'reweight_fraction_below_zero':float(np.mean(resampled<0)),
            'nonmutual_score_change_mean':float(delta[y!=3].mean()),
            'donor_score_changes':[{'donor':x['donor'],'loss_change_sum':float(v)} for x,v in zip(r['records'],donor_sum)]}
    result={'contract_sha256':sha(HERE/'allen_prediction_score_audit_contract.json'),
            'models':out,'verification':'PASS: state and donor loss sums equal direct dyad loss sum; original190 scores conserved'}
    save('allen_prediction_score_audit_result.json',result)
    print(json.dumps({k:{a:b for a,b in v.items() if a!='donor_score_changes'} for k,v in out.items()},indent=2))


if __name__=='__main__':main()
