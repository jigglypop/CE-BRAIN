"""행동 라벨에 따른 사후 선택 민감도. 주 집합은 바꾸지 않는다."""
import json
from pathlib import Path
import numpy as np
from rowland_prestate_adjustment import fit, synthetic_check
from randi_target_response import HERE, save, sha


def main():
    parents = ['rowland_prestate_adjustment_result.json', 'rowland_loader_audit_result.json']
    save('rowland_lick_selection_contract.json', {
        'question': '저자 라벨 변경 대상 제외가 기존 세션별 대비에 미치는 영향',
        'parents': {p: sha(HERE/p) for p in parents}, 'code_sha256': sha(Path(__file__)),
        'helper_sha256': sha(HERE/'rowland_prestate_adjustment.py'),
        'selection': '전체 11세션; 기존 유한시각 catch/test 집합과 라벨 변경 대상 제외 집합 비교',
        'models': ['무보정 test-catch', '시간과 자극 전 S1/S2 평균 보정 test 계수'],
        'windows': '기존 명목 pre[-2,-.5), post[1.5,3) 요약 재사용',
        'limits': ['사후 행동 선택 민감도이며 인과효과 아님', '독립 검증·논문 최종 분석 재현 아님'],
        'decision': '선택 전 주 분석 보존; 모든 세션과 두 모형 보고',
        'claim_ceiling': 'BIO_EVIDENCE_L1'})
    original = json.loads((HERE/parents[0]).read_text(encoding='utf-8'))['rows']
    labels = {(r['mouse'],r['run']):r for r in json.loads((HERE/parents[1]).read_text(encoding='utf-8'))['sessions']}
    synthetic_check()
    rows=[]
    for r in original:
        label=labels[(r['mouse'],r['run'])]
        idx=np.array(r['original_indices']); t=np.array(r['test']); y=np.array(r['s2_delta'])
        z=np.column_stack([r['elapsed_seconds'],r['s1_pre'],r['s2_pre']])
        removed=np.isin(idx,label['changed_original_indices']); keep=~removed
        assert np.all(t[removed]==1) and int(removed.sum())==label['changed_eligible_test']
        models={}
        for name,cov in [('raw',np.empty((len(y),0))),('time_prestate',z)]:
            full=fit(y,t,cov)
            assert abs(full['coefficient']-r[name]['coefficient'])<1e-12
            selected=fit(y[keep],t[keep],cov[keep])
            models[name]={'full':full,'selected':selected,
                          'shift':selected['coefficient']-full['coefficient'],
                          'sign_changed':bool(full['coefficient']*selected['coefficient']<0)}
        omitted_mean=float(y[removed].mean()) if removed.any() else None
        selected_mean=float(y[keep & (t==1)].mean())
        decomposition=float(removed.sum()/sum(t==1)*(selected_mean-omitted_mean)) if removed.any() else 0.
        assert abs(decomposition-models['raw']['shift'])<1e-12
        rows.append({'mouse':r['mouse'],'run':r['run'],'removed_n':int(removed.sum()),
                     'removed_indices':idx[removed].tolist(),'test_full_n':int(sum(t==1)),
                     'test_selected_n':int(sum(keep & (t==1))),'catch_n':int(sum(t==0)),
                     'removed_mean':omitted_mean,'selected_test_mean':selected_mean,
                     'raw_shift_decomposition':decomposition,'models':models})
    assert len(rows)==11 and sum(r['removed_n'] for r in rows)==48
    save('rowland_lick_selection_result.json',{'contract_sha256':sha(HERE/'rowland_lick_selection_contract.json'),'rows':rows})
    for r in rows:
        print(r['mouse'],r['run'],r['removed_n'],*[round(r['models'][m][x]['coefficient'],8) for m in ['raw','time_prestate'] for x in ['full','selected']])


if __name__=='__main__':
    main()
