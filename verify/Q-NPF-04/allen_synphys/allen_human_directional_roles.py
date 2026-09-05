"""Allen 인간 TCx 상층에서 고정된 입출력 불균형 지표를 평가한다."""
import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save
from peng2024_directional_roles import score

HERE=Path(__file__).resolve().parent
assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
save('allen_human_directional_roles_contract.json',{
    'question':'Does the same directional imbalance endpoint exceed the fair-orientation skeleton reference in Allen human upper TCx?',
    'scope':'human; TCx; nonsynaptic cell class ex/ex; both target layers 2,2/3,3; both has_synapse nonnull and n_ex_test_spikes>10',
    'endpoint':'sum per-record sum_v(out-in)^2; expectation 2*one-way dyads; preserve mutual/absent dyads; no amplitude selection',
    'units':'record and slice aggregates; slice is NOT a patient; no donor claims',
    'sensitivity':'delete-one-slice descriptive residual; no p-value; record information requires null variance>0',
    'verification':'1022 qualified directions/511 dyads and 102 positive directions; independent adjacency sum vs shared score; raw condition counts',
    'prior_audit_note':'older human strength contract gate retained stale mouse190/25 text; executable human check was parity only; this contract checks actual human denominator explicitly',
    'limits':'different institution dataset does not itself verify individual donor independence; slice sampling, layer selection and detection asymmetry persist',
    'db_sha256':sha(DB),'metric_code_sha256':sha(HERE/'peng2024_directional_roles.py'),'code_sha256':sha(Path(__file__))})
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    rows=[dict(r) for r in db.execute('''select p.id,p.experiment_id,p.pre_cell_id,p.post_cell_id,p.has_synapse,p.n_ex_test_spikes,e.slice_id
      from pair p join cell a on a.id=p.pre_cell_id join cell b on b.id=p.post_cell_id
      join experiment e on e.id=p.experiment_id join slice s on s.id=e.slice_id
      where s.species='human' and e.target_region='TCx'
      and a.cell_class_nonsynaptic='ex' and b.cell_class_nonsynaptic='ex'
      and a.target_layer in ('2','2/3','3') and b.target_layer in ('2','2/3','3')''')]
lookup={(r['experiment_id'],r['pre_cell_id'],r['post_cell_id']):r for r in rows}
assert len(lookup)==len(rows)
groups=defaultdict(list);qualified=positive=mutual_directions=0
for r in rows:
    rev=lookup.get((r['experiment_id'],r['post_cell_id'],r['pre_cell_id']))
    if rev is None or any(x['has_synapse'] is None or x['n_ex_test_spikes'] is None or x['n_ex_test_spikes']<=10 for x in (r,rev)):continue
    qualified+=1;positive+=int(r['has_synapse']==1)
    mutual_directions+=int(r['has_synapse']==rev['has_synapse']==1)
    groups[r['experiment_id']].append(r)
assert qualified==1022 and positive==102 and mutual_directions%2==0
records=[];slices=defaultdict(lambda:[0,0,0])
for eid,rr in sorted(groups.items()):
    nodes=sorted({r[k] for r in rr for k in ('pre_cell_id','post_cell_id')})
    edges=[]
    for r in rr:
        rev=lookup[eid,r['post_cell_id'],r['pre_cell_id']]
        if r['has_synapse']==1 and rev['has_synapse']==0:edges.append((nodes.index(r['pre_cell_id']),nodes.index(r['post_cell_id'])))
    observed,expected,variance=score(len(nodes),edges)
    # Independent total adjacency includes mutual edges; they cancel in net degree.
    matrix=[[0]*len(nodes) for _ in nodes]
    for r in rr:matrix[nodes.index(r['pre_cell_id'])][nodes.index(r['post_cell_id'])]=int(r['has_synapse'])
    direct=sum((sum(matrix[i])-sum(row[i] for row in matrix))**2 for i in range(len(nodes)))
    assert direct==observed
    sid=rr[0]['slice_id'];assert {r['slice_id'] for r in rr}=={sid}
    slices[sid][0]+=observed;slices[sid][1]+=expected;slices[sid][2]+=int(variance>0)
    records.append({'experiment_id':eid,'slice_id':sid,'qualified_dyads':len(rr)//2,'oneway_edges':len(edges),
                    'observed':observed,'expected':expected,'null_variance':variance})
obs=sum(r['observed'] for r in records);exp=sum(r['expected'] for r in records)
delta=[v[0]-v[1] for v in slices.values()]
out={'contract_sha256':sha(HERE/'allen_human_directional_roles_contract.json'),
     'qualified_dyads':qualified//2,'positive_directions':positive,'mutual_dyads':mutual_directions//2,
     'records_total':len(records),'slices_total':len(slices),
     'informative_records':sum(r['null_variance']>0 for r in records),'informative_slices':sum(v[2]>0 for v in slices.values()),
     'observed':obs,'expected':exp,'ratio':obs/exp,'residual':obs-exp,
     'slices_positive':sum(d>0 for d in delta),'slices_negative':sum(d<0 for d in delta),'slices_zero':sum(d==0 for d in delta),
     'delete_one_slice_residual_range':[obs-exp-max(delta),obs-exp-min(delta)],
     'records':records,'slices':{str(k):{'observed':v[0],'expected':v[1],'informative_records':v[2]} for k,v in slices.items()},
     'verification':'PASS: exact human denominators, label qualification and independent adjacency metric'}
save('allen_human_directional_roles_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ('records','slices')},indent=2))
