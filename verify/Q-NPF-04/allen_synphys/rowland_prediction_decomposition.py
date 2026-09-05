"""고정된 예측의 집단별 오차와 영향 집중도; 재적합·유의성 검정 없음."""
import json
from pathlib import Path
import numpy as np
from randi_target_response import HERE,save,sha


def summarize(e0,e1):
    assert len(e0)==len(e1)>0 and e0.sum()>0
    return {'n':len(e0),'mse_baseline':float(e0.mean()),'mse_added':float(e1.mean()),
            'sse_improvement':float((e0-e1).sum()),'relative_reduction':float(1-e1.sum()/e0.sum())}


def main():
    predpath=HERE/'rowland_forward_prediction_result.json'
    sourcepath=HERE/'rowland_prestate_adjustment_result.json'
    contract=save('rowland_prediction_decomposition_contract.json',{
        'question':'추가 예측 개선은 어느 시행 집단에서 나오며 소수 시행에 집중되는가',
        'parent_sha256':sha(HERE/'rowland_forward_prediction_contract.json'),
        'prediction_sha256':sha(predpath),'source_sha256':sha(sourcepath),
        'code_sha256':sha(Path(__file__)),'helper_sha256':sha(HERE/'randi_target_response.py'),
        'inherit':'기존 학습·평가·모형·예측·측정모형·시행 제외 유지; 재적합 없음',
        'groups':'원래 시행 번호로 연결한 catch/test, 두 집단 모두 보고',
        'endpoints':['각 집단 MSE 및 SSE 개선','단일 평가 시행을 각각 제외한 상대 개선 최솟값·최댓값',
                     '오차 개선이 가장 큰 ceil(0.1*n) 시행을 제외한 상대 개선'],
        'ranking':'squared_error_baseline-squared_error_added 내림차순; 동률은 기존 시행 순서',
        'limits':['결과 기반 제거는 개선 집중도 스트레스 검사이며 새 확인 성능이나 신뢰구간 아님',
                  '집단별 개선은 자극 표지 외 다른 계수의 재추정도 포함','재적합 없이 예측을 고정한 영향 검사',
                  '독립 동물 통합·인과효과·다중비교 유의성 판정 없음'],
        'claim_ceiling':'BIO_EVIDENCE_L1 post-hoc prediction decomposition'})
    preds=json.loads(predpath.read_text(encoding='utf-8'))['rows']
    sources={(r['mouse'],r['run']):r for r in json.loads(sourcepath.read_text(encoding='utf-8'))['rows']}
    rows=[]
    for p in preds:
        assert p['status']=='EVALUATED'
        source=sources[(p['mouse'],p['run'])]
        mapping=dict(zip(source['original_indices'],source['test']))
        indices=np.array(p['eval_indices']);t=np.array([mapping[i] for i in indices])
        y=np.array(p['observed']);e0=(y-np.array(p['baseline_prediction']))**2;e1=(y-np.array(p['added_prediction']))**2
        assert np.allclose(e0-e1,p['squared_error_difference'],atol=1e-14)
        whole=summarize(e0,e1)
        assert abs(whole['relative_reduction']-p['relative_mse_reduction'])<1e-12
        groups={name:summarize(e0[t==code],e1[t==code]) for name,code in [('catch',0),('test',1)]}
        assert abs(sum(g['sse_improvement'] for g in groups.values())-whole['sse_improvement'])<1e-12
        assert np.all(e0.sum()-e0>0)
        leave=1-(e1.sum()-e1)/(e0.sum()-e0)
        count=int(np.ceil(.1*len(y)));order=np.argsort(-(e0-e1),kind='stable')
        keep=np.ones(len(y),dtype=bool);keep[order[:count]]=False
        rows.append({'mouse':p['mouse'],'run':p['run'],'all':whole,'groups':groups,
            'leave_one_min':float(leave.min()),'leave_one_max':float(leave.max()),
            'leave_one_reductions':leave.tolist(),'eval_indices':indices.tolist(),
            'largest_gain_removed_indices':indices[order[:count]].tolist(),
            'largest_gain_removed':summarize(e0[keep],e1[keep])})
    save('rowland_prediction_decomposition_result.json',{'contract_sha256':sha(contract),'rows':rows})
    print(json.dumps([{'mouse':r['mouse'],'run':r['run'],'gain':r['all']['relative_reduction'],
      'group_gain':{k:v['relative_reduction'] for k,v in r['groups'].items()},
      'leave_one':[r['leave_one_min'],r['leave_one_max']],
      'remove_top_tenth':r['largest_gain_removed']['relative_reduction']} for r in rows]))


if __name__=='__main__':main()
