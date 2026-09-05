"""같은 기록에서 비교해 표본 변경과 세포 효과 제거를 구분한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
sp=HERE/'song2005_strength_cell_effects_result.json';ip=HERE/'song2005_inventory_result.json'
prior=json.loads(sp.read_text());source=json.loads(ip.read_text());rows={r['row']:r for r in source['records']}
save('song2005_strength_matched_support_contract.json',{
    'question':'세포 효과를 고려한 강도 대비 변화는 기록 선택만으로 나타나는가?',
    'selection':'이전 sender/receiver/sender_receiver 모형에 정보가 있던 기록 ID를 그대로 사용',
    'method':'각 고정 기록집합에서 기록절편만 제거한 대비와 이전 세포효과 대비를 비교; 동일가중 기록별 대비도 비교',
    'limits':'동일 기록이라도 투영·정보가중치가 다름; 인과 분해 아님; 한 기록뿐인 동시교정은 기술만',
    'source_sha256':sha(ip),'prior_sha256':sha(sp),'code_sha256':sha(Path(__file__))})
results={}
for model in ('sender','receiver','sender_receiver'):
    selected=prior['models'][model]['records'];base_num=base_den=0.;details=[]
    for old in selected:
        row=rows[old['row']];edges=row['edges'];keys={(e['pre'],e['post']) for e in edges}
        y=np.log([1000*e['amplitude_V'] for e in edges]);z=np.array([(e['post'],e['pre']) in keys for e in edges],float)
        ry=y-y.mean();rz=z-z.mean();info=float(rz@rz);assert info>1e-10
        beta=float(rz@ry/info)
        # Direct group means independently verify intercept-only coefficient.
        assert abs(beta-(y[z==1].mean()-y[z==0].mean()))<1e-12
        base_num+=float(rz@ry);base_den+=info
        details.append({'row':row['row'],'date':row['date'],'baseline_beta':beta,'adjusted_beta':old['record_beta']})
    adjusted=prior['models'][model]
    assert len(details)==adjusted['informative_records']
    results[model]={'records':len(details),'baseline_same_records_beta':base_num/base_den,
        'baseline_same_records_ratio':float(np.exp(base_num/base_den)),
        'adjusted_ratio':adjusted['exp_beta'],
        'equal_record_baseline_beta':float(np.mean([x['baseline_beta'] for x in details])),
        'equal_record_adjusted_beta':float(np.mean([x['adjusted_beta'] for x in details])),
        'records_with_reduced_contrast':sum(x['adjusted_beta']<x['baseline_beta'] for x in details),'details':details}
result={'contract_sha256':sha(HERE/'song2005_strength_matched_support_contract.json'),
    'models':results,'verification':'PASS: prior record IDs fixed; intercept projection equals direct within-record log-mean contrast'}
save('song2005_strength_matched_support_result.json',result)
print(json.dumps({k:{a:b for a,b in v.items() if a!='details'} for k,v in results.items()},indent=2))
