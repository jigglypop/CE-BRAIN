"""공개 Donor 표의 비식별 ID와 완전한 표본 접두사 대응을 검사한다."""
import json
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path
from collections import defaultdict
from population_reciprocity import DB, ROOT, sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
inventory=HERE/'allen_human_joint_input_inventory_result.json'
records=json.loads(inventory.read_text(encoding='utf-8'))['records']
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    names=dict(db.execute('select id,lims_specimen_name from slice'))
sids=sorted({r['slice_id'] for r in records})
prefix={str(sid):'.'.join(names[sid].split('.')[:3]) for sid in sids}
assert all(len(v.split('.'))==3 and v.startswith('H') for v in prefix.values())
criteria="model::Donor,rma::criteria,[name$in"+','.join("'"+s+"'" for s in sorted(set(prefix.values())))+"],rma::options[num_rows$eqall][only$eqid,name]"
url='https://api.brain-map.org/api/v2/data/query.json?'+urllib.parse.urlencode({'criteria':criteria})
asset=ROOT/'data/external/allen_synphys_r21/public_donor_name_match.json'
save('allen_human_public_donor_match_contract.json',{
    'question':'Do complete three-component prefixes match official public Donor names and IDs?',
    'scope':'Exact name match only; no demographic or medical fields requested. Missing or duplicate names remain unresolved.',
    'limits':'Donor name lookup is not direct slice-to-donor API association; do not extrapolate missing names or infer real identities.',
    'inventory_sha256':sha(inventory),'db_sha256':sha(DB),'code_sha256':sha(Path(__file__)), 'url':url})
if not asset.exists():
    payload=urllib.request.urlopen(url,timeout=45).read()
    parsed=json.loads(payload);assert parsed['success'] is True
    with asset.open('xb') as f:f.write(payload)
data=json.loads(asset.read_text(encoding='utf-8'))
assert data['success'] and data['total_rows']==len(data['msg'])
byname=defaultdict(list)
for row in data['msg']:
    assert set(row)=={'id','name'}
    byname[row['name']].append(row['id'])
duplicates=[k for k,v in byname.items() if len(v)!=1]
assert not duplicates
mapping={sid:byname[name][0] for sid,name in prefix.items() if name in byname}
missing=sorted(set(prefix.values())-set(byname))
summary={}
for label,subset in [('all_511',records),('numeric_362',[r for r in records if r['flags']['all_positive_physiology']])]:
    matched=[r for r in subset if str(r['slice_id']) in mapping]
    summary[label]={'dyads':len(subset),'matched_dyads':len(matched),'matched_donor_ids':len({mapping[str(r['slice_id'])] for r in matched}),
                    'full_prefix_groups':len({prefix[str(r['slice_id'])] for r in subset})}
out={'contract_sha256':sha(HERE/'allen_human_public_donor_match_contract.json'),'asset_sha256':sha(asset),
     'requested_names':len(set(prefix.values())),'returned_names':len(byname),'missing_names':missing,
     'slice_to_full_prefix':prefix,'slice_to_public_donor_id':mapping,'summary':summary,
     'gate':'PASS_COMPLETE_NAME_MATCH' if not missing else 'PARTIAL_PUBLIC_NAME_MATCH',
     'limitation':'Exact public donor-name match supports matched prefixes only; slice association and unmatched prefixes remain unverified.'}
save('allen_human_public_donor_match_result.json',out)
print(json.dumps({k:v for k,v in out.items() if not k.startswith('slice_to')},indent=2))
print('SOURCE_URL',url)
