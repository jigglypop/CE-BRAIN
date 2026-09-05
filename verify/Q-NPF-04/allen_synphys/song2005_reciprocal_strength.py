"""상호연결과 단방향 연결의 관측 EPSP 강도를 기록 내부에서도 비교한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
ip=HERE/'song2005_inventory_result.json'
r=json.loads(ip.read_text());assert r['status']=='PASS'
save('song2005_reciprocal_strength_contract.json',{
    'question':'상호연결의 각 방향은 단방향 연결보다 관측 EPSP 진폭이 큰가?',
    'scope':'저자 공개931개 검출 연결; 무연결에 진폭0을 대입하지 않음; 관측 진폭V를mV로 변환',
    'endpoints':'상호/단방향 진폭 평균·중앙값·합; 두 종류가 공존한 기록 내부 log진폭 평균 차이; 날짜별 동일가중 차이',
    'selection':'전체 검출 연결 유지; 기록 내부 비교만 두 종류 공존 필요; 범위를 명시하고 전체로 확대하지 않음',
    'gate':'모든 진폭 유한·양수; 436상호 방향+495단방향=931; 강도합 보존',
    'limits':'검출된 연결 조건부 관측; 강한 연결 검출 편향 가능; EPSP는 해부학적 시냅스 수나 실제 총흥분 입력이 아님; 동물독립성·인과 없음',
    'input_sha256':sha(ip),'code_sha256':sha(Path(__file__))})
all_mutual=[];all_single=[];mixed=[]
for row in r['records']:
    edges={(e['pre'],e['post']):e['amplitude_V']*1000 for e in row['edges']}
    mutual=[v for (a,b),v in edges.items() if (b,a) in edges]
    single=[v for (a,b),v in edges.items() if (b,a) not in edges]
    assert all(np.isfinite(v) and v>0 for v in edges.values())
    all_mutual.extend(mutual);all_single.extend(single)
    if mutual and single:
        difference=float(np.mean(np.log(mutual))-np.mean(np.log(single)))
        mixed.append({'row':row['row'],'date':row['date'],'mutual_directions':len(mutual),'one_way_directions':len(single),
                      'log_mean_difference':difference,'geometric_mean_ratio':float(np.exp(difference))})
assert len(all_mutual)==436 and len(all_single)==495
def summary(values):
    return {'directions':len(values),'mean_mV':float(np.mean(values)),'median_mV':float(np.median(values)),
            'sum_mV':float(sum(values))}
by_date={d:float(np.mean([x['log_mean_difference'] for x in mixed if x['date']==d])) for d in sorted({x['date'] for x in mixed})}
result={'contract_sha256':sha(HERE/'song2005_reciprocal_strength_contract.json'),
    'reciprocal':summary(all_mutual),'one_way':summary(all_single),
    'reciprocal_fraction_of_amplitude_sum':float(sum(all_mutual)/(sum(all_mutual)+sum(all_single))),
    'mixed_records':len(mixed),'mixed_dates':len(by_date),
    'mixed_record_positive':sum(x['log_mean_difference']>0 for x in mixed),
    'mixed_record_equal_weight_log_difference':float(np.mean([x['log_mean_difference'] for x in mixed])),
    'mixed_date_equal_weight_log_difference':float(np.mean(list(by_date.values()))),
    'records':mixed,'date_log_differences':by_date,'verification':'PASS: positive finite amplitudes;931 directions partitioned without omission'}
assert abs(result['reciprocal']['sum_mV']+result['one_way']['sum_mV']-sum(e['amplitude_V']*1000 for row in r['records'] for e in row['edges']))<1e-8
save('song2005_reciprocal_strength_result.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('records','date_log_differences')},indent=2))
