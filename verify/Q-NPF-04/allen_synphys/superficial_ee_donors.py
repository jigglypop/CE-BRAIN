"""공식 명명 규칙으로 상층 E-E 절편의 동물 그룹을 복원한다."""
import ast
import csv
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from population_reciprocity import DB, TABLE, sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    source=HERE/'qc_sources/lims.py'
    assert sha(source)=='af1eff74b14ed4344f3cc0ff3e3dc7a536a0e0435005dc7841b86f264cedd2d8'
    assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
    assert sha(TABLE)=='92675aaf6fc7e032fc262cc7666998cb8009ce54e6422146d40d00ff6ae28700'
    patterns=[n.value for n in ast.walk(ast.parse(source.read_text(encoding='utf-8')))
              if isinstance(n,ast.Constant) and isinstance(n.value,str) and '(?P<donor_id>' in n.value]
    assert len(patterns)==1
    pattern=patterns[0]
    save('superficial_ee_donors_contract.json',{
        'question':'검출 기준을 통과한 상층 E-E 쌍은 몇 동물에 속하며 상호연결이 동물별로 어떻게 분포하는가?',
        'selection':'앞선 mouse VisP ex/ex target_layer 2,2/3,3; 양방향 비결측 및 n_ex_test_spikes>10',
        'identity':'고정 공식 lims.py의 donor_id 정규식; live LIMS donor table 대조는 아님',
        'gate':'정규식 미일치 또는 같은 donor의 성별·생년월일·유전형 모순 시 후속 그룹 분석 중지',
        'claim':'기술적 그룹 복원; 독립성 또는 생물 기전의 검정 아님',
        'source_sha256':sha(source),'code_sha256':sha(Path(__file__)), 'pattern':pattern})
    with TABLE.open(encoding='utf-8',newline='') as f:
        rows=[r for r in csv.DictReader(f) if r['species']=='mouse' and r['region']=='VisP'
              and r['class_pair']=='ex|ex' and all(x in ('2','2/3','3') for x in r['layer_pair'].split('|'))]
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        spikes=dict(db.execute('select id,n_ex_test_spikes from pair'))
        slices={r[0]:r[1:] for r in db.execute('select id,lims_specimen_name,sex,date_of_birth,genotype from slice')}
    groups=defaultdict(list); metadata=defaultdict(set); mapping={}
    for row in rows:
        sid=int(row['slice_id']); name,*meta=slices[sid]
        match=re.fullmatch(pattern,name)
        assert match is not None, name
        donor=match.group('donor_id');mapping[str(sid)]=donor
        metadata[donor].add(tuple(meta))
        if all(spikes[int(row[k])] is not None and spikes[int(row[k])]>10 for k in ('pair_ab','pair_ba')):
            groups[donor].append(row)
    conflicts={k:[list(x) for x in v] for k,v in metadata.items() if len(v)>1}
    per_donor=[{'donor_name_id':k,'dyads':len(v),'mutual':sum(int(r['positive_directions'])==2 for r in v),
                'positive_directions':sum(int(r['positive_directions']) for r in v),
                'slices':len({r['slice_id'] for r in v}),'experiments':len({r['experiment_id'] for r in v})}
               for k,v in sorted(groups.items())]
    assert sum(r['dyads'] for r in per_donor)==190
    assert sum(r['mutual'] for r in per_donor)==3
    result={'all_231_dyads_donors':len(set(mapping.values())), 'qualified_190_dyads_donors':len(groups),
        'donors_with_mutual':sum(r['mutual']>0 for r in per_donor),
        'metadata_conflicts':conflicts,'slice_to_donor':mapping,'per_donor':per_donor,
        'gate':'PASS' if not conflicts else 'STOP_METADATA_CONFLICT',
        'contract_sha256':sha(HERE/'superficial_ee_donors_contract.json')}
    save('superficial_ee_donors_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('slice_to_donor','per_donor')},indent=2))
    print('Mutual donors:', [r for r in per_donor if r['mutual']])


if __name__=='__main__':main()
