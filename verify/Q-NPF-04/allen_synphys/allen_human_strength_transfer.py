"""Allen의 단일 정보 기록에 Peng의 거리 없는 고정 강도 계수를 적용한다."""
import json
import sqlite3
from pathlib import Path
import numpy as np
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
inventory_path=HERE/'allen_human_strength_identifiability_result.json'
prior_path=HERE/'peng2024_er_strength_result.json'
inventory=json.loads(inventory_path.read_text(encoding='utf-8'))['scopes']['upper_layers']
prior=json.loads(prior_path.read_text(encoding='utf-8'))['branches']['author_published']
ids=[r['experiment_id'] for r in inventory['records'] if r['identifiable']]
save('allen_human_strength_transfer_contract.json',{
    'question':'One identifiable Allen human upper TCx record: prediction by fixed Peng reciprocity contrast coefficient',
    'scope':'all identifiable records from prior availability audit; no amplitude-based selection',
    'prediction':'topology-only projection removes sender/receiver; predicted residual=0.5249058466238167 * projected reciprocal; null zero',
    'coefficient':prior['beta'],
    'distance':'no distance model transfer: Peng XY distance and Allen distance convention not matched; this tests the unadjusted fixed model only',
    'endpoint':'squared error of projected log amplitude; individual-record fitted contrast for descriptive comparison',
    'limits':'one record; no population inference; no independent donor identity verification; amplitude and detection selection remain',
    'inventory_sha256':sha(inventory_path),'prior_sha256':sha(prior_path),'db_sha256':sha(DB),'code_sha256':sha(Path(__file__))})
assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    rows=[dict(r) for r in db.execute('''select p.id,p.experiment_id,p.pre_cell_id,p.post_cell_id,p.has_synapse,p.n_ex_test_spikes,
      sy.psp_amplitude,sy.synapse_type
      from pair p join cell a on a.id=p.pre_cell_id join cell b on b.id=p.post_cell_id
      join experiment e on e.id=p.experiment_id join slice s on s.id=e.slice_id
      left join synapse sy on sy.pair_id=p.id
      where s.species='human' and e.target_region='TCx'
      and a.cell_class_nonsynaptic='ex' and b.cell_class_nonsynaptic='ex'
      and a.target_layer in ('2','2/3','3') and b.target_layer in ('2','2/3','3')''')]
lookup={(r['experiment_id'],r['pre_cell_id'],r['post_cell_id']):r for r in rows}
assert len(lookup)==len(rows)
results=[]
for eid in ids:
    edges=[]
    for r in rows:
        if r['experiment_id']!=eid:continue
        rev=lookup.get((eid,r['post_cell_id'],r['pre_cell_id']))
        if rev is None or any(v['has_synapse'] is None or v['n_ex_test_spikes'] is None or v['n_ex_test_spikes']<=10 for v in (r,rev)):continue
        amp=r['psp_amplitude']
        if r['has_synapse']!=1 or r['synapse_type']!='ex' or amp is None or not np.isfinite(amp) or amp<=0:continue
        edges.append((r['pre_cell_id'],r['post_cell_id'],rev['has_synapse'],np.log(amp),r['id']))
    nodes=sorted({e[k] for e in edges for k in (0,1)})
    x=np.array([[int(e[0]==n) for n in nodes]+[int(e[1]==n) for n in nodes] for e in edges],float)
    z=np.array([e[2] for e in edges]); y=np.array([e[3] for e in edges])
    u,s,_=np.linalg.svd(x,full_matrices=True);rank=int(sum(s>1e-10));c=u[:,rank:].T
    rz=c@z;ry=c@y;info=float(rz@rz)
    assert info>1e-10 and np.allclose(c@x,0,atol=1e-10)
    prediction=prior['beta']*rz
    null=float(ry@ry);frozen=float((ry-prediction)@(ry-prediction))
    beta=float(rz@ry/info)
    joint=np.linalg.lstsq(np.column_stack((x,z)),y,rcond=1e-10)[0][-1]
    assert np.isclose(beta,joint,atol=1e-9)
    results.append({'experiment_id':eid,'directions':len(edges),'contrast_dimensions':len(ry),
        'pair_ids':[e[4] for e in edges],'information':info,'local_beta_descriptive':beta,
        'local_exp_beta_descriptive':float(np.exp(beta)), 'null_sse':null,'frozen_sse':frozen,'delta_sse':frozen-null})
out={'contract_sha256':sha(HERE/'allen_human_strength_transfer_contract.json'),'records':results,
     'verification':'PASS: qualified pair reconstruction, topology contrasts and independent joint fit'}
save('allen_human_strength_transfer_result.json',out)
print(json.dumps(out,indent=2))
