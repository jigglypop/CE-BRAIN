"""절단면 깊이 가용성 및 같은 표본의 절편 제외 방향 예측."""
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
source=HERE/'allen_human_orientation_spikes_serialized_result.json'
schema=HERE/'source_snapshots/aisynphys__database__schema__experiment.py'
assert 'from the cut surface of the slice' in schema.read_text(encoding='utf-8')
assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
save('allen_human_cut_depth_contract.json',{
    'question':'Does cut-surface depth difference improve orientation prediction beyond spike counts on matched complete cases?',
    'scope':'prior 80 one-way dyads; require both depths finite; no imputation; target_layer availability only, not actual laminar depth',
    'models':['spike log ratio','spike log ratio plus (depth_a-depth_b)/100um'],
    'fit':'leave whole slice out; no intercept; ridge identity; Newton gradient<1e-9; no tuning',
    'score':'logloss and expected imbalance on identical retained skeleton; fair p=.5 comparator',
    'checks':'source schema semantics; prior file hash; reversal symmetry; expected S exact orientation enumeration',
    'limits':'cut depth is not pia depth; complete-case selection changes support; exploratory; slices not donors',
    'schema_sha256':sha(schema),'prior_sha256':sha(source),'db_sha256':sha(DB),'code_sha256':sha(Path(__file__))})
old=json.loads(source.read_text(encoding='utf-8'))['edges']
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    cells={r[0]:r[1:] for r in db.execute('select id,depth,target_layer from cell')}
edges=[]
for e in old:
    a,b=cells[e['a']],cells[e['b']]
    if any(v is None or not np.isfinite(v) for v in (a[0],b[0])):continue
    edges.append({**e,'features':[e['x'],(a[0]-b[0])/1e-4]})
results={}
for count,name in ((1,'spikes'),(2,'spikes_cut_depth')):
    predictions={};folds=[]
    for sid in sorted({e['slice'] for e in edges}):
        train=[e for e in edges if e['slice']!=sid];test=[(i,e) for i,e in enumerate(edges) if e['slice']==sid]
        x=np.array([e['features'][:count] for e in train]);y=np.array([e['y'] for e in train]);beta=np.zeros(count)
        for _ in range(100):
            prob=expit(x@beta);g=x.T@(prob-y)+beta
            if np.max(np.abs(g))<1e-10:break
            h=x.T@((prob*(1-prob))[:,None]*x)+np.eye(count);beta-=np.linalg.solve(h,g)
        assert np.max(np.abs(g))<1e-9
        assert np.allclose(expit(-x@beta),1-expit(x@beta))
        losses=[]
        for i,e in test:
            eta=float(np.array(e['features'][:count])@beta)
            predictions[i]=float(expit(eta));losses.append(float(np.logaddexp(0,eta)-e['y']*eta))
        folds.append({'slice':sid,'coefficients':beta.tolist(),'count':len(test),'loss_sum':sum(losses)})
    groups=defaultdict(list)
    for i,e in enumerate(edges):groups[e['experiment']].append((i,e))
    records=[]
    for eid,ee in groups.items():
        nodes=sorted({e[k] for _,e in ee for k in ('a','b')});inc=np.zeros((len(nodes),len(ee)))
        for j,(_,e) in enumerate(ee):inc[nodes.index(e['a']),j]=1;inc[nodes.index(e['b']),j]=-1
        p=np.array([predictions[i] for i,_ in ee]);mu=2*p-1
        expected=float(np.sum((inc@mu)**2)+2*np.sum(1-mu**2))
        observed=float(np.sum((inc@np.array([2*e['y']-1 for _,e in ee]))**2))
        assert len(ee)<=16
        brute=0.
        for bits in product((0,1),repeat=len(ee)):
            b=np.array(bits);brute+=float(np.prod(np.where(b,p,1-p))*np.sum((inc@(2*b-1))**2))
        assert abs(brute-expected)<1e-9
        records.append({'experiment':eid,'observed':observed,'expected':expected})
    results[name]={'logloss':sum(f['loss_sum'] for f in folds)/len(edges),
       'equal_slice_logloss':float(np.mean([f['loss_sum']/f['count'] for f in folds])),
       'observed':sum(r['observed'] for r in records),'expected':sum(r['expected'] for r in records),
       'folds':folds,'records':records,'probabilities':[predictions[i] for i in range(len(edges))]}
out={'contract_sha256':sha(HERE/'allen_human_cut_depth_contract.json'),
     'original_dyads':len(old),'both_depth_dyads':len(edges),'excluded':len(old)-len(edges),
     'slices':len({e['slice'] for e in edges}),'different_target_layer_dyads_original':sum(cells[e['a']][1]!=cells[e['b']][1] for e in old),
     'fair_logloss':float(np.log(2)),'fair_expected':2*len(edges),'models':results,
     'verification':'PASS: schema, complete cases, split, gradients, reversal and exact expectation'}
save('allen_human_cut_depth_result.json',out)
print(json.dumps({**{k:v for k,v in out.items() if k!='models'},'models':{k:{a:b for a,b in v.items() if a not in ('folds','records','probabilities')} for k,v in results.items()}},indent=2))
