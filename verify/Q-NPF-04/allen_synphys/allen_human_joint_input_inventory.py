"""독립 결합 예측에 필요한 Allen 입력의 보유 여부만 검사한다."""
import json
import math
import sqlite3
from pathlib import Path
from population_reciprocity import DB, sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
save('allen_human_joint_input_inventory_contract.json', {
    'question': 'Are the existing 511 Allen human upper TCx dyads equipped for matched Planert joint prediction?',
    'scope': 'Reuse exact prior eligible dyads; inventory only, no outcome-model fitting or inference of donor identities.',
    'fields': 'Both-cell cortical distance_to_pia, steady-state input resistance, rheobase; pair distance; explicit donor/patient schema fields and slice metadata key names only.',
    'gate': 'Finite numeric inputs are availability, not verified units or protocol/QC equivalence. Slice/specimen names are not donor IDs.',
    'source_sha256': sha(HERE/'allen_human_directional_roles_result.json'),
    'db_sha256': sha(DB), 'code_sha256': sha(Path(__file__))})
assert sha(DB) == '7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
with sqlite3.connect(DB.as_uri()+'?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    rows = [dict(r) for r in db.execute('''
      select p.id,p.experiment_id,p.pre_cell_id,p.post_cell_id,p.has_synapse,p.n_ex_test_spikes,p.distance,e.slice_id
      from pair p join cell a on a.id=p.pre_cell_id join cell b on b.id=p.post_cell_id
      join experiment e on e.id=p.experiment_id join slice s on s.id=e.slice_id
      where s.species='human' and e.target_region='TCx'
      and a.cell_class_nonsynaptic='ex' and b.cell_class_nonsynaptic='ex'
      and a.target_layer in ('2','2/3','3') and b.target_layer in ('2','2/3','3')''')]
    tables = {}
    for name in ('intrinsic', 'cortical_cell_location'):
        records = [dict(r) for r in db.execute('select * from '+name)]
        tables[name] = {r['cell_id']: r for r in records}
        assert len(records) == len(tables[name]), 'Nonunique cell join'
    schema_identity_fields = {}
    for row in db.execute("select name from sqlite_master where type='table'"):
        name = row[0]
        columns = [r[1] for r in db.execute('pragma table_info("'+name.replace('"','""')+'")')]
        found = [c for c in columns if 'donor' in c.lower() or 'patient' in c.lower()]
        if found: schema_identity_fields[name] = found
    metadata_keys = set()
    for row in db.execute("select meta from slice where species='human'"):
        obj = json.loads(row[0]) if row[0] else {}
        if isinstance(obj, dict): metadata_keys.update(obj)

lookup = {(r['experiment_id'],r['pre_cell_id'],r['post_cell_id']):r for r in rows}
assert len(lookup) == len(rows)
def finite(value):
    return isinstance(value, (int,float)) and math.isfinite(value)

dyads = []
for r in rows:
    if r['pre_cell_id'] >= r['post_cell_id']: continue
    reverse = lookup.get((r['experiment_id'],r['post_cell_id'],r['pre_cell_id']))
    if reverse is None or any(x['has_synapse'] is None or x['n_ex_test_spikes'] is None or x['n_ex_test_spikes'] <= 10 for x in (r,reverse)): continue
    flags = {}
    for label, table, field in [('pia','cortical_cell_location','distance_to_pia'), ('steady_resistance','intrinsic','input_resistance_ss'), ('rheobase','intrinsic','rheobase')]:
        values = [tables[table].get(r[k], {}).get(field) for k in ('pre_cell_id','post_cell_id')]
        flags[label] = all(finite(v) for v in values)
        if label != 'pia': flags[label+'_positive'] = all(finite(v) and v > 0 for v in values)
    flags['distance'] = finite(r['distance']) and finite(reverse['distance'])
    flags['all_numeric'] = all(flags[k] for k in ('pia','steady_resistance','rheobase','distance'))
    flags['all_positive_physiology'] = flags['all_numeric'] and flags['steady_resistance_positive'] and flags['rheobase_positive']
    dyads.append({'pair_ids':[r['id'],reverse['id']], 'experiment_id':r['experiment_id'], 'slice_id':r['slice_id'], 'flags':flags})
assert len(dyads) == 511
prior = json.loads((HERE/'allen_human_directional_roles_result.json').read_text(encoding='utf-8'))
assert {r['experiment_id'] for r in dyads} == {r['experiment_id'] for r in prior['records']}
out = {'contract_sha256':sha(HERE/'allen_human_joint_input_inventory_contract.json'),
       'dyads':len(dyads), 'experiments':len({r['experiment_id'] for r in dyads}), 'slices':len({r['slice_id'] for r in dyads}),
       'both_cell_or_pair_available':{k:sum(r['flags'][k] for r in dyads) for k in dyads[0]['flags']},
       'explicit_identity_columns':schema_identity_fields, 'human_slice_metadata_keys':sorted(metadata_keys),
       'records':dyads, 'verification':'PASS: readonly inventory, unique joins, prior 511 dyads and experiment set reproduced; no biological result'}
save('allen_human_joint_input_inventory_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k != 'records'},indent=2))
