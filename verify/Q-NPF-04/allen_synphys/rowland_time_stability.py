"""동일 관측 대비의 시간 반분·연속 구간 제외 민감도; 신뢰구간 아님."""
import json
from pathlib import Path

import numpy as np

from randi_target_response import HERE, save, sha
from rowland_prestate_adjustment import fit


def partitions(time):
    assert len(time)>1 and np.all(np.diff(time)>0)
    fraction=(time-time[0])/(time[-1]-time[0])
    quarter=np.minimum((4*fraction).astype(int),3)
    masks={'all':np.ones(len(time),dtype=bool), 'early':fraction<.5, 'late':fraction>=.5}
    masks.update({f'omit_q{k+1}':quarter!=k for k in range(4)})
    assert np.all(masks['early'] ^ masks['late'])
    assert np.all(sum(~masks[f'omit_q{k+1}'] for k in range(4))==1)
    return masks


def evaluate(row, mask):
    t=np.array(row['test'])[mask]
    counts={'catch':int((t==0).sum()),'test':int((t==1).sum())}
    indices=np.array(row['original_indices'])[mask]
    result={'n':int(mask.sum()),'counts':counts,'original_indices':indices.tolist()}
    if min(counts.values())<6:
        return {**result,'status':'INSUFFICIENT_GROUP_COUNT'}
    y=np.array(row['s2_delta'])[mask]
    z=np.column_stack([row['elapsed_seconds'],row['s1_pre'],row['s2_pre']])[mask]
    try:
        models={'raw':fit(y,t,[]),'time_only':fit(y,t,z[:,:1]),'time_prestate':fit(y,t,z)}
    except (AssertionError,np.linalg.LinAlgError):
        return {**result,'status':'NUMERIC_OR_RANK_FAILURE'}
    return {**result,'status':'EVALUATED','models':models}


def main():
    fixture=partitions(np.array([0.,1.,2.,3.,4.,5.,6.,7.,8.]))
    assert np.flatnonzero(fixture['early']).tolist()==[0,1,2,3]
    assert np.flatnonzero(~fixture['omit_q4']).tolist()==[6,7,8]
    source=HERE/'rowland_prestate_adjustment_result.json'
    parent=HERE/'rowland_prestate_adjustment_contract.json'
    contract=save('rowland_time_stability_contract.json',{
        'question':'보정된 S2 대비가 전후반 및 특정 연속 시간 구간의 제외에 안정적인가',
        'parent_contract_sha256':sha(parent),'input_sha256':sha(source),
        'code_sha256':sha(Path(__file__)),
        'dependencies':{n:sha(HERE/n) for n in ['rowland_prestate_adjustment.py','randi_target_response.py']},
        'inherit':'원 계약의 자료·측정모형·시행 제외·세 모형·비인과적 추정량·주장 상한 유지',
        'split':'이미 본 11세션의 사후 탐색; 각각 별도 적합, 독립 예측검증 아님',
        'partition':'각 세션 첫~마지막 유효 catch/test galvo 시간의 중간으로 반분, 4등분 구간을 차례로 제외',
        'boundaries':'왼쪽 포함·오른쪽 제외; 마지막 끝점은 마지막 구간 포함',
        'models':'무보정·시간·시간과 S1/S2 전 상태; 각 부분집합에서 재표준화 및 재적합',
        'minimum':'각 집단 최소 6시행; 부족/수치실패는 명시하고 표본 교체 없음',
        'endpoint':'세션별 계수와 제외 4회 최솟값·최댓값; 신뢰구간 또는 jackknife 표준오차 아님',
        'decision':'두 반분 부호 불일치 또는 제외 계수 범위가 0을 가로지르면 부호 민감성 기록',
        'limits':['세션 내부 시점별 상태·표본 구성도 함께 변함','비정상성·자기상관의 통계적 제거 아님',
                  '여러 비교의 유의성 판정 없음','같은 동물의 반복 기록을 독립 동물로 세지 않음',
                  '특정 구간 영향만으로 생물학적 원인이나 인과 연결 판정 불가'],
        'claim_ceiling':'BIO_EVIDENCE_L1 exploratory descriptive sensitivity'})
    data=json.loads(source.read_text(encoding='utf-8')); rows=[]
    for row in data['rows']:
        parts={name:evaluate(row,mask) for name,mask in partitions(np.array(row['elapsed_seconds'])).items()}
        assert parts['all']['status']=='EVALUATED'
        for model in ['raw','time_only','time_prestate']:
            assert abs(parts['all']['models'][model]['coefficient']-row[model]['coefficient'])<1e-12
        rows.append({'mouse':row['mouse'],'run':row['run'],'partitions':parts})
    save('rowland_time_stability_result.json',{'contract_sha256':sha(contract),'partition_fixture_passed':True,'rows':rows})
    print(json.dumps([{'mouse':r['mouse'],'run':r['run'],
        'parts':{n:({'n':p['n'],**{m:v['coefficient'] for m,v in p['models'].items()}} if p['status']=='EVALUATED' else p['status']) for n,p in r['partitions'].items()}} for r in rows]))


if __name__=='__main__':
    main()
