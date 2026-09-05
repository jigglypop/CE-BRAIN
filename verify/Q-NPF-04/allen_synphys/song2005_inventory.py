"""저자 공개 Song 2005 표의 검사 분모와 연결 문자열을 대조한다."""
import json
import sys
from collections import Counter
from pathlib import Path
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
sys.path.insert(0,str(ROOT/'data/external/analysis_tools/xls_reader'))
import xlrd

HERE=Path(__file__).resolve().parent
path=ROOT/'data/external/song2005/Connectivity_v10.xls'
save('song2005_inventory_contract.json',{
    'question':'저자 제공 연결 문자열과 검사 수로 양방향 쌍 분모를 복원할 수 있는가?',
    'selection':'제공한 모든 비어 있지 않은 실험 행; nTested=2,6,12이면 각각2,3,4세포의 모든 방향 검사라는 저자 설명 사용',
    'gate':'날짜/attempt 중복 검사, 문자열 연결 수=nConnections, 자기 연결/중복 없음, 식별된 세포 수<=검사 세포 수',
    'limits':'고립 세포의 실제 채널 ID는 문자열에서 미식별 가능; 날짜는 동물 ID가 아님; 랫드 L5 범위는 생쥐 상층과 별도',
    'input_sha256':sha(path),'code_sha256':sha(Path(__file__)),'reader_version':xlrd.__version__})
book=xlrd.open_workbook(str(path));sheet=book.sheet_by_index(0)
records=[];keys=set();totals=Counter();issues=[]
for i in range(1,sheet.nrows):
    date,attempt,nc,nt,age,calcium,string=sheet.row_values(i)
    key=(date,attempt)
    if key in keys:issues.append({'row':i+1,'issue':'duplicate date/attempt'})
    keys.add(key)
    edges={}
    for item in str(string).split(';'):
        item=item.strip()
        if not item or item=='NA':continue
        pair,amp,sd=item.split(',');a,b=map(int,pair.split('_'))
        assert a!=b and (a,b) not in edges
        edges[a,b]=(float(amp),float(sd))
    assert len(edges)==int(nc)
    assert nt in (2,6,12),nt
    n={2:2,6:3,12:4}[int(nt)]
    assert len({x for pair in edges for x in pair})<=n
    mutual=sum((b,a) in edges for a,b in edges)//2
    one=len(edges)-2*mutual;dyads=int(nt)//2;neither=dyads-one-mutual
    assert neither>=0
    totals.update({'experiments':1,'tested_directions':int(nt),'connections':len(edges),'dyads':dyads,
                   'neither':neither,'one_way':one,'mutual':mutual})
    records.append({'row':i+1,'date':xlrd.xldate_as_datetime(date,book.datemode).isoformat(),
        'attempt':attempt,'age':age,'calcium_mM':calcium,'tested_directions':int(nt),
        'dyads':dyads,'neither':neither,'one_way':one,'mutual':mutual,
        'edges':[{'pre':a,'post':b,'amplitude_V':v[0],'sd_V':v[1]} for (a,b),v in sorted(edges.items())]})
result={'contract_sha256':sha(HERE/'song2005_inventory_contract.json'),'totals':dict(totals),
        'unique_dates':len({r['date'] for r in records}),'issues':issues,'records':records,
        'status':'PASS' if not issues else 'REVIEW_DUPLICATE_KEYS'}
save('song2005_inventory_result.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
