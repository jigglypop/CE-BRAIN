"""정확 차수 참조의 잔차가 어느 기록과 조건에서 발생하는지 확인한다."""
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
ep=HERE/'song2005_exact_degrees_result.json';ip=HERE/'song2005_inventory_result.json'
exact=json.loads(ep.read_text());inventory=json.loads(ip.read_text())
save('song2005_residual_support_contract.json',{
    'question':'입출력 차수 보존 후 잔차는 몇 날짜와 어떤 기록 조건에 분포하는가?',
    'scope':'전체816개 보존; 잔차 변동 가능29개는 정보량 기술용; 유리한 부분집합 선택 없음',
    'endpoints':'날짜·연령·칼슘별 잔차합, 양/음/영 기록 수; 날짜 하나를 제외한 잔차합 범위',
    'limits':'사후 기술분해; 날짜는 독립 동물 아님; 여러 그룹의 합을 중복 증거로 세지 않음; p값 없음',
    'exact_sha256':sha(ep),'inventory_sha256':sha(ip),'code_sha256':sha(Path(__file__))})
meta={v['row']:v for v in inventory['records']};groups={k:defaultdict(list) for k in ('date','age','calcium_mM')}
rows=[];signs={'positive':0,'negative':0,'zero':0};total=Fraction(0)
for record in exact['records']:
    residual=Fraction(record['observed'])-Fraction(record['expected_fraction'])
    variable=len(record['mutual_histogram'])>1
    if not variable:assert residual==0
    entry={'row':record['row'],'residual_fraction':str(residual),'residual':float(residual),'variable':variable}
    entry.update({key:meta[record['row']][key] for key in groups})
    rows.append(entry);total+=residual
    if variable:signs['positive' if residual>0 else 'negative' if residual<0 else 'zero']+=1
    for key in groups:groups[key][str(entry[key])].append(entry)
summaries={}
for key,values in groups.items():
    summaries[key]=[]
    for label,entries in sorted(values.items()):
        residual=sum((Fraction(e['residual_fraction']) for e in entries),Fraction(0))
        summaries[key].append({'group':label,'records':len(entries),'variable_records':sum(e['variable'] for e in entries),
                               'residual_fraction':str(residual),'residual':float(residual)})
    assert sum((Fraction(v['residual_fraction']) for v in summaries[key]),Fraction(0))==total
assert len(rows)==816 and sum(signs.values())==29
assert total==Fraction(exact['observed'])-Fraction(exact['expected_fraction'])
date_residuals=[Fraction(v['residual_fraction']) for v in summaries['date']]
remaining=[total-v for v in date_residuals]
result={'contract_sha256':sha(HERE/'song2005_residual_support_contract.json'),
    'total_residual_fraction':str(total),'variable_record_signs':signs,
    'dates_with_variable_records':sum(v['variable_records']>0 for v in summaries['date']),
    'delete_one_date_residual_range':[float(min(remaining)),float(max(remaining))],
    'groups':summaries,'variable_records':[v for v in rows if v['variable']],
    'verification':'PASS: each partition preserves all816 records and exact265/21 residual; fixed records zero'}
assert total==Fraction(265,21)
save('song2005_residual_support_result.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('groups','variable_records')},indent=2))
print(json.dumps({k:v for k,v in summaries.items() if k!='date'},indent=2))
