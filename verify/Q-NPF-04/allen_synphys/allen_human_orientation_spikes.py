"""절편 제외 자극량 방향 예측과 불균형의 독립 방향 기대값."""
import json
import sqlite3
from collections import defaultdict
from itertools import product
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
prior_path=HERE/'allen_human_directional_roles_result.json'
assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
save('allen_human_orientation_spikes_contract.json',{
    'question':'Can directional test-spike imbalance predict orientation and change expected input-output imbalance?',
    'scope':'same 511 human upper TCx dyads; condition on 80 one-way dyads; no amplitude selection',
    'model':'p(low-ID to high-ID)=sigmoid(beta * log(nspikes_forward/nspikes_reverse)); no intercept; ridge beta^2/2; no tuning',
    'split':'leave entire slice out; slices not donors; prior observation makes this exploratory',
    'endpoint':'held-out directional logloss vs log(2); observed S vs expected S=sum_v[(sum incident signed means)^2+sum incident variances]',
    'null':'independent orientations conditional on existing skeleton and cross-fitted probabilities; no joint dependence fit',
    'gates':'80 one-way dyads; coefficient gradient<1e-9; endpoint expectation checked by complete orientation enumeration per real record; reversal symmetry',
    'limits':'spike count may respond to recording decisions; not randomized cause or full QC adjustment; no independent patient claim',
    'db_sha256':sha(DB),'prior_sha256':sha(prior_path),'code_sha256':sha(Path(__file__))})
prior=json.loads(prior_path.read_text(encoding='utf-8'))
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    rows=[dict(r) for r in db.execute('''select p.id,p.experiment_id,p.pre_cell_id,p.post_cell_id,p.has_synapse,p.n_ex_test_spikes,e.slice_id
      from pair p join cell a on a.id=p.pre_cell_id join cell b on b.id=p.post_cell_id
      join experiment e on e.id=p.experiment_id join slice s on s.id=e.slice_id
      where s.species='human' and e.target_region='TCx'
      and a.cell_class_nonsynaptic='ex' and b.cell_class_nonsynaptic='ex'
      and a.target_layer in ('2','2/3','3') and b.target_layer in ('2','2/3','3')''')]
lookup={(r['experiment_id'],r['pre_cell_id'],r['post_cell_id']):r for r in rows}
edges=[];qualified=0
for r in rows:
    if r['pre_cell_id']>=r['post_cell_id']:continue
    rev=lookup.get((r['experiment_id'],r['post_cell_id'],r['pre_cell_id']))
    if rev is None or any(v['has_synapse'] is None or v['n_ex_test_spikes'] is None or v['n_ex_test_spikes']<=10 for v in (r,rev)):continue
    qualified+=1
    if r['has_synapse']+rev['has_synapse']!=1:continue
    edges.append({'experiment':r['experiment_id'],'slice':r['slice_id'],'a':r['pre_cell_id'],'b':r['post_cell_id'],
                  'x':float(np.log(r['n_ex_test_spikes']/rev['n_ex_test_spikes'])),'y':int(r['has_synapse'])})
assert qualified==511 and len(edges)==80
folds=[]
for sid in sorted({e['slice'] for e in edges}):
    train=[e for e in edges if e['slice']!=sid];test=[e for e in edges if e['slice']==sid]
    x=np.array([e['x'] for e in train]);y=np.array([e['y'] for e in train]);beta=0.
    for iteration in range(100):
        p=expit(beta*x);g=float(x@(p-y)+beta);h=float((x*x)@(p*(1-p))+1)
        if abs(g)<1e-10:break
        beta-=g/h
    assert abs(g)<1e-9
    assert np.allclose(expit(-beta*x),1-expit(beta*x))
    for e in test:
        e['probability']=float(expit(beta*e['x']))
        e['loss']=float(np.logaddexp(0,beta*e['x'])-e['y']*beta*e['x'])
    folds.append({'slice':sid,'beta':beta,'gradient':g,'dyads':len(test),'logloss':float(np.mean([e['loss'] for e in test]))})
groups=defaultdict(list)
for e in edges:groups[e['experiment']].append(e)
records=[]
for eid,ee in groups.items():
    nodes=sorted({e[k] for e in ee for k in ('a','b')})
    incidence=np.zeros((len(nodes),len(ee)))
    for j,e in enumerate(ee):incidence[nodes.index(e['a']),j]=1;incidence[nodes.index(e['b']),j]=-1
    p=np.array([e['probability'] for e in ee]);mu=2*p-1
    expectation=float(np.sum((incidence@mu)**2)+2*np.sum(1-mu*mu))
    observed=int(np.sum((incidence@np.array([2*e['y']-1 for e in ee]))**2))
    # Exact independent-direction enumeration checks each real graph expectation.
    assert len(ee)<=16
    brute=0.;mass=0.
    for bits in product((0,1),repeat=len(ee)):
        b=np.array(bits);prob=float(np.prod(np.where(b,p,1-p)))
        brute+=prob*float(np.sum((incidence@(2*b-1))**2));mass+=prob
    assert abs(mass-1)<1e-10 and abs(brute-expectation)<1e-9
    records.append({'experiment':eid,'slice':ee[0]['slice'],'observed':observed,'expected':expectation})
observed=sum(r['observed'] for r in records);expected=sum(r['expected'] for r in records)
assert observed==prior['observed']
out={'contract_sha256':sha(HERE/'allen_human_orientation_spikes_contract.json'),'dyads':len(edges),'slices_with_oneway_edges':len(folds),
     'equal_spike_dyads':sum(e['x']==0 for e in edges),
     'fair_logloss':float(np.log(2)),'spike_logloss':float(np.mean([e['loss'] for e in edges])),
     'equal_slice_spike_logloss':float(np.mean([f['logloss'] for f in folds])),
     'slices_improved':sum(f['logloss']<np.log(2)-1e-12 for f in folds),
     'beta_range':[min(f['beta'] for f in folds),max(f['beta'] for f in folds)],
     'observed':observed,'fair_expected':prior['expected'],'spike_expected':expected,'spike_residual':observed-expected,
     'folds':folds,'edges':edges,'records':records,'verification':'PASS: split, gradients, reversal symmetry, exact expected-score enumeration'}
save('allen_human_orientation_spikes_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ('folds','edges','records')},indent=2))
