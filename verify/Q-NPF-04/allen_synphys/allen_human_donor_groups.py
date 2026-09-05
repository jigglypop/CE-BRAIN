"""공식 비식별 표본 명명 규칙으로 평가 그룹을 복원한다."""
import ast
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from population_reciprocity import DB, sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
source=HERE/'qc_sources/lims.py'
inventory=HERE/'allen_human_joint_input_inventory_result.json'
assert sha(source)=='af1eff74b14ed4344f3cc0ff3e3dc7a536a0e0435005dc7841b86f264cedd2d8'
assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
patterns=[n.value for n in ast.walk(ast.parse(source.read_text(encoding='utf-8')))
          if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith(r'H(\d+)')]
assert len(patterns)==1
pattern=patterns[0]
save('allen_human_donor_groups_contract.json', {
    'question':'Can official human donor site/number fields group existing eligible slices without treating slices as people?',
    'scope':'Existing 511 dyads and 362 numeric candidates; no fitting or biological endpoint.',
    'identity':'Official lims.py human regex; groups()[1] site plus groups()[2] donor number. No real-world identity inference or demographic linkage.',
    'gates':'All relevant names match; each site/number has one first prefix; all slices map once. Prefix ambiguity blocks grouping.',
    'limits':'Name-derived donor groups, not live LIMS donor-table verification; source code and release pipeline versions may differ.',
    'source_sha256':sha(source),'inventory_sha256':sha(inventory),'code_sha256':sha(Path(__file__))})
prior=json.loads(inventory.read_text(encoding='utf-8'))
records=prior['records']; sids={r['slice_id'] for r in records}
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    names=dict(db.execute('select id,lims_specimen_name from slice'))
    metadata=[json.loads(r[0]) for r in db.execute('select meta from metadata')]
    pipeline_count=db.execute('select count(*) from pipeline').fetchone()[0]
mapping={};prefixes=defaultdict(set);unmatched=[]
for sid in sorted(sids):
    m=re.fullmatch(pattern,names[sid] or '')
    if m is None:
        unmatched.append(sid);continue
    prefix,site,number=m.groups()[:3]
    key=f'{int(site)}:{int(number)}'
    prefixes[key].add(int(prefix));mapping[str(sid)]=key
ambiguous=[k for k,v in prefixes.items() if len(v)!=1]
summary={}
for label,subset in [('all_511',records),('numeric_362',[r for r in records if r['flags']['all_positive_physiology']])]:
    counts=defaultdict(list)
    for r in subset:
        if str(r['slice_id']) in mapping:counts[mapping[str(r['slice_id'])]].append(r)
    summary[label]={'dyads':len(subset),'mapped_dyads':sum(map(len,counts.values())), 'groups':len(counts),
                    'per_group':[{'group':k,'dyads':len(v),'slices':len({r['slice_id'] for r in v}),
                                  'experiments':len({r['experiment_id'] for r in v})} for k,v in sorted(counts.items())]}
out={'contract_sha256':sha(HERE/'allen_human_donor_groups_contract.json'),
     'gate':'PASS_NAME_GROUPING' if not unmatched and not ambiguous else 'STOP_NAME_GROUPING',
     'unmatched_slice_ids':unmatched,'prefix_ambiguity_groups':ambiguous,
     'slice_to_group':mapping,'summary':summary,'db_metadata':metadata,'pipeline_rows':pipeline_count,
     'generation_provenance':'Metadata is descriptive; no exact source/dependency version recovered from these fields.'}
save('allen_human_donor_groups_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ('slice_to_group','summary')},indent=2))
print(json.dumps({k:{a:b for a,b in v.items() if a!='per_group'} for k,v in summary.items()},indent=2))
