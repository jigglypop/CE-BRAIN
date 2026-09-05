"""Song 소규모 기록의 입출력 연결 수를 보존한 모든 그래프를 열거한다."""
import json
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from population_reciprocity import sha
from superficial_ee_eligibility import save
from reciprocity_exact_support import distribution

HERE=Path(__file__).resolve().parent
path=HERE/'song2005_inventory_result.json'
r=json.loads(path.read_text());assert r['status']=='PASS'
save('song2005_exact_degrees_contract.json',{
    'question':'각 기록의 세포별 입력·출력 연결 수를 보존하면 상호연결 수가 얼마나 설명되는가?',
    'scope':'816개2~4세포 기록; 자기연결 없음; 각 기록 내 모든 방향 검사; 고립 채널은 익명 노드로 보충',
    'reference':'각 기록의 지정된 입력·출력 차수와 일치하는 단순 유향 그래프의 균등 분포',
    'endpoint':'관측 상호연결 합, 정확한 조건부 기대 합, 가능한 범위, 상호연결 수가 변할 수 있는 기록 수',
    'verification':'모든 비트마스크 그래프 전수열거와 별도 행별 재귀 열거의 히스토그램 일치; 분수 기대값',
    'limits':'균등 참조가 실제 생물 생성모형이라는 보장 없음; 같은 동물 상관 미확인; 독립 곱분포 p값 없음; 거리·검출편향 미교정; 고정으로 제거한 차수 자체의 생물 효과는 검정하지 않음',
    'source_sha256':sha(path),'code_sha256':sha(Path(__file__)),
    'verifier_code_sha256':sha(HERE/'reciprocity_exact_support.py')})
lookup={}
for n in (2,3,4):
    positions=[(i,j) for i in range(n) for j in range(n) if i!=j]
    groups=defaultdict(Counter)
    for bits in range(1<<len(positions)):
        edges={edge for k,edge in enumerate(positions) if bits&(1<<k)}
        outgoing=tuple(sum(a==i for a,b in edges) for i in range(n))
        incoming=tuple(sum(b==i for a,b in edges) for i in range(n))
        mutual=sum((b,a) in edges for a,b in edges)//2
        groups[outgoing,incoming][mutual]+=1
    assert sum(sum(v.values()) for v in groups.values())==1<<(n*(n-1))
    lookup[n]=groups
records=[];expected=Fraction(0);minimum=maximum=observed=variable=0
for row in r['records']:
    n={2:2,6:3,12:4}[row['tested_directions']]
    nodes=sorted({v for e in row['edges'] for v in (e['pre'],e['post'])})
    nodes+=list(range(-1,-1-(n-len(nodes)),-1))
    edges={(nodes.index(e['pre']),nodes.index(e['post'])) for e in row['edges']}
    out=tuple(sum(a==i for a,b in edges) for i in range(n));inc=tuple(sum(b==i for a,b in edges) for i in range(n))
    hist=lookup[n][out,inc]
    other=distribution({'cell_ids':nodes,'allowed_destination_masks':[((1<<n)-1)^(1<<i) for i in range(n)],
                        'outgoing':list(out),'incoming':list(inc)})
    assert hist==other and row['mutual'] in hist
    mean=Fraction(sum(k*v for k,v in hist.items()),sum(hist.values()))
    expected+=mean;minimum+=min(hist);maximum+=max(hist);observed+=row['mutual'];variable+=len(hist)>1
    records.append({'row':row['row'],'date':row['date'],'observed':row['mutual'],'expected_fraction':str(mean),
                    'allowed_graphs':sum(hist.values()),'mutual_histogram':dict(hist)})
assert observed==218 and len(records)==816
result={'contract_sha256':sha(HERE/'song2005_exact_degrees_contract.json'),
    'observed':observed,'expected':float(expected),'expected_fraction':str(expected),
    'residual':float(observed-expected),'sum_local_minimum':minimum,'sum_local_maximum':maximum,
    'variable_records':variable,'fixed_statistic_records':len(records)-variable,
    'records':records,'verification':'PASS: bitmask exhaustive and recursive counts match for every record'}
result=json.loads(json.dumps(result))
save('song2005_exact_degrees_result.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
