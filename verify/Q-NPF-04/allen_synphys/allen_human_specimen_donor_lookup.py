"""공식 세포 표본 ID로 공개 donor 외래키를 조회한다."""
import json
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path
from population_reciprocity import DB, ROOT, sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
inventory=HERE/'allen_human_joint_input_inventory_result.json'
records=[r for r in json.loads(inventory.read_text(encoding='utf-8'))['records'] if r['flags']['all_positive_physiology']]
assert len(records)==362
assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    pairs={r[0]:r[1:] for r in db.execute('select id,pre_cell_id,post_cell_id from pair')}
    cells={v for r in records for pid in r['pair_ids'] for v in pairs[pid]}
    specimen={cid:json.loads(meta)['lims_specimen_id'] for cid,meta in db.execute('select id,meta from cell') if cid in cells}
assert len(specimen)==218 and all(isinstance(v,int) for v in specimen.values())
ids=sorted(set(specimen.values()))
criteria='model::Specimen,rma::criteria,[id$in'+','.join(map(str,ids))+'],rma::options[num_rows$eqall][only$eqid,donor_id]'
url='https://api.brain-map.org/api/v2/data/query.json?'+urllib.parse.urlencode({'criteria':criteria})
save('allen_human_specimen_donor_lookup_contract.json',{
    'question':'Does the public Specimen table expose donor foreign keys for the 218 cells in the 362 numeric dyads?',
    'selection':'Fixed prior numeric candidates; exact stored lims_specimen_id only; no naming or demographic inference.',
    'gates':'API success and complete returned row count; IDs unique and requested; both endpoints share donor for a dyad; missing IDs remain unresolved.',
    'limits':'API noncoverage does not invalidate internal LIMS IDs; no substitution from other subjects.',
    'url':url,'inventory_sha256':sha(inventory),'code_sha256':sha(Path(__file__))})
asset=ROOT/'data/external/allen_synphys_r21/public_specimen_donor_lookup.json'
if not asset.exists():
    payload=urllib.request.urlopen(url,timeout=45).read()
    data=json.loads(payload);assert data['success'] is True
    with asset.open('xb') as f:f.write(payload)
data=json.loads(asset.read_text(encoding='utf-8'))
assert data['success'] and data['total_rows']==len(data['msg'])
mapping={r['id']:r.get('donor_id') for r in data['msg']}
assert len(mapping)==len(data['msg']) and set(mapping)<=set(ids)
assert all(set(r)<={'id','donor_id'} for r in data['msg'])
matched=[];conflicts=[]
for r in records:
    a,b=pairs[r['pair_ids'][0]]
    da,db=(mapping.get(specimen[x]) for x in (a,b))
    if da is None or db is None:continue
    if da!=db:conflicts.append(r['pair_ids'])
    else:matched.append({'pair_ids':r['pair_ids'],'donor_id':da})
out={'contract_sha256':sha(HERE/'allen_human_specimen_donor_lookup_contract.json'),
     'asset_sha256':sha(asset),'requested_specimens':len(ids),'returned_specimens':len(mapping),
     'with_donor':sum(v is not None for v in mapping.values()),'matched_dyads':len(matched),
     'conflicting_dyads':conflicts,'matched':matched,'cell_to_specimen':specimen,
     'gate':'PASS_FULL_LINKAGE' if len(matched)==362 and not conflicts else 'INCOMPLETE_PUBLIC_LINKAGE'}
save('allen_human_specimen_donor_lookup_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ('matched','cell_to_specimen')},indent=2))
