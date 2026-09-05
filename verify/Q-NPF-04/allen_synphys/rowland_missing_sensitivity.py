"""분석 대상 밖 시행의 평균 반응에 대한 가정별 무보정 대비 범위."""
import json
from pathlib import Path
import numpy as np
from randi_target_response import HERE, save, sha


def main():
    parents=['rowland_prestate_adjustment_result.json','rowland_trial_history_result.json']
    save('rowland_missing_sensitivity_contract.json', {
        'question':'분석 대상 밖 시행의 집단 평균 편이가 얼마나 커야 무보정 대비 부호가 바뀌는가',
        'code_sha256':sha(Path(__file__)), 'parents':{p:sha(HERE/p) for p in parents},
        'estimand':'보존된 원래 catch/test 시행 전체의 기술적 평균 대비; 인과효과 아님',
        'model':'D_full = D_observed + q_test * delta_test - q_catch * delta_catch',
        'delta':'대상 밖 시행 평균에서 같은 유형 관측 시행 평균을 뺀 값',
        'scale':'관측 test/catch의 집단 내 pooled sample SD',
        'bounds':'각 유형에서 abs(delta)<=k*SD; k in [0.25,0.5,1,2]',
        'report':'전체 11세션과 부호가 0에 닿는 최소 대칭 경계 k',
        'limits':['경계 크기는 검증되지 않은 시나리오', '신뢰구간 또는 누락값 복원 아님',
                  '전처리·배정·직접경로 식별 문제를 해결하지 않음'],
        'claim_ceiling':'BIO_EVIDENCE_L1'})
    responses=json.loads((HERE/parents[0]).read_text(encoding='utf-8'))['rows']
    histories={(r['mouse'],r['run']):r for r in json.loads((HERE/parents[1]).read_text(encoding='utf-8'))['sessions']}
    rows=[]
    for r in responses:
        h=histories[(r['mouse'],r['run'])]
        idx=np.array(r['original_indices']); t=np.array(r['test']); y=np.array(r['s2_delta'])
        assert np.array_equal(idx,np.array([i for i in h['eligible_indices'] if h['original_nominal'][i]!=150]))
        yt,yc=y[t==1],y[t==0]
        nt,nc=h['groups']['test']['original'],h['groups']['catch']['original']
        mt,mc=nt-len(yt),nc-len(yc)
        qt,qc=mt/nt,mc/nc
        sd=float(np.sqrt(((len(yt)-1)*yt.var(ddof=1)+(len(yc)-1)*yc.var(ddof=1))/(len(y)-2)))
        d=float(yt.mean()-yc.mean())
        assert sd>0 and qt+qc>0 and abs(d-r['raw']['coefficient'])<1e-12
        limits=[]
        for k in [.25,.5,1.,2.]:
            radius=(qt+qc)*k*sd
            lo,hi=d-radius,d+radius
            # 두 끝점을 집단 평균의 가중합으로도 확인한다.
            for sign,bound in [(-1,lo),(1,hi)]:
                direct=(yt.sum()+mt*(yt.mean()+sign*k*sd))/nt-(yc.sum()+mc*(yc.mean()-sign*k*sd))/nc
                assert abs(direct-bound)<1e-12
            limits.append({'k':k,'lower':lo,'upper':hi,'contains_zero':bool(lo<=0<=hi)})
        threshold=abs(d)/((qt+qc)*sd)
        rows.append({'mouse':r['mouse'],'run':r['run'],'test_outside':mt,'catch_outside':mc,
                     'test_original':nt,'catch_original':nc,'q_test':qt,'q_catch':qc,
                     'observed_contrast':d,'pooled_observed_sd':sd,
                     'zero_boundary_sd_units':threshold,'scenario_ranges':limits,
                     'test_outside_export':nt-h['groups']['test']['exported'],
                     'catch_outside_export':nc-h['groups']['catch']['exported']})
    assert len(rows)==11
    save('rowland_missing_sensitivity_result.json',{'contract_sha256':sha(HERE/'rowland_missing_sensitivity_contract.json'),'rows':rows})
    for r in rows: print(r['mouse'],r['run'],r['test_outside'],r['catch_outside'],round(r['zero_boundary_sd_units'],3))


if __name__=='__main__':
    main()
