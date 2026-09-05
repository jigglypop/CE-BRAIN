"""Planert 계수 앙상블을 고정한 Allen 연결 존재 예측."""
import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
source=HERE/'planert2025_masked_presence_parsed_result.json'
inventory=HERE/'allen_human_joint_input_inventory_result.json'
save('allen_human_frozen_presence_contract.json',{
    'question':'Does the previously fitted network-feature model transfer beyond fixed geometry/physiology predictions to Allen?',
    'population':'Fixed prior 362 numeric dyads; no new target outcome selection or QC equivalence claim.',
    'models':'Equal probability average of all 21 saved Planert outer-fold models, separately baseline and network; no Allen fitting, intercept adjustment or model selection.',
    'features':'Original six baseline and two network features, Allen pia and pair distance m to um; steady resistance and rheobase ratios in native units.',
    'mask':'seed0|a|b SHA256 ordering, alternating two groups per experiment, both directions hidden; only opposite-group edges feed rates.',
    'endpoints':'Directional logloss, Brier and predicted count; descriptive equal-slice loss, no patient SE or p values.',
    'checks':'Hidden-label flips must preserve features/predictions; reversed direction flips signed baseline features; independent scalar ensemble reconstruction.',
    'limits':'Exploratory external application with known source/QC/coordinate differences and target visible context; not prospective replication or patient-independent validation.',
    'source_sha256':sha(source),'inventory_sha256':sha(inventory),'db_sha256':sha(DB),'code_sha256':sha(Path(__file__))})
assert sha(DB)=='7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
prior=json.loads(source.read_text(encoding='utf-8'))
chosen=[r for r in json.loads(inventory.read_text(encoding='utf-8'))['records'] if r['flags']['all_positive_physiology']]
assert len(chosen)==362
with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    table={r['id']:dict(r) for r in db.execute('select * from pair')}
    intrinsic={r['cell_id']:dict(r) for r in db.execute('select * from intrinsic')}
    location={r['cell_id']:dict(r) for r in db.execute('select * from cortical_cell_location')}
pairs=[];groups=defaultdict(list)
for r in chosen:
    f,b=(table[k] for k in r['pair_ids'])
    assert f['pre_cell_id']==b['post_cell_id'] and f['post_cell_id']==b['pre_cell_id']
    assert f['distance']>=0 and np.isclose(f['distance'],b['distance'],atol=1e-12,rtol=0)
    assert all(x['has_synapse'] in (0,1) and x['n_ex_test_spikes']>10 for x in (f,b))
    groups[r['experiment_id']].append(len(pairs))
    pairs.append({**r,'a':f['pre_cell_id'],'b':f['post_cell_id'],'distance':f['distance']*1e6,
                  'labels':[f['has_synapse'],b['has_synapse']]})
mask={}
for indices in groups.values():
    order=sorted(indices,key=lambda i:hashlib.sha256(f"seed0|{pairs[i]['a']}|{pairs[i]['b']}".encode()).hexdigest())
    for j,i in enumerate(order):mask[i]=j%2
def features(i,labels):
    r=pairs[i];rows=[]
    for a,b in ((r['a'],r['b']),(r['b'],r['a'])):
        da,db=(location[x]['distance_to_pia']*1e6 for x in (a,b))
        outgoing=incoming=out_n=in_n=0
        for j in groups[r['experiment_id']]:
            if mask[j]==mask[i]:continue
            o=pairs[j]
            for pre,post,y in ((o['a'],o['b'],labels[j][0]),(o['b'],o['a'],labels[j][1])):
                if pre==a:outgoing+=y;out_n+=1
                if post==b:incoming+=y;in_n+=1
        rows.append([1,np.log1p(r['distance']/100),(da+db)/2000,(da-db)/100,
                     np.log(intrinsic[a]['input_resistance_ss']/intrinsic[b]['input_resistance_ss']),
                     np.log(intrinsic[a]['rheobase']/intrinsic[b]['rheobase']),
                     (outgoing+1)/(out_n+2),(incoming+1)/(in_n+2)])
    return np.array(rows)
labels=np.array([r['labels'] for r in pairs]);rows=[]
for i,r in enumerate(pairs):
    x=features(i,labels);altered=labels.copy()
    for j in groups[r['experiment_id']]:
        if mask[j]==mask[i]:altered[j]=1-altered[j]
    assert np.array_equal(x,features(i,altered))
    assert np.allclose(x[0,3:6],-x[1,3:6]) and np.allclose(x[0,:3],x[1,:3])
    rows.extend(x.tolist())
x=np.array(rows);assert np.isfinite(x).all()
y=labels.ravel();sids=np.repeat([r['slice_id'] for r in pairs],2);models={};losses={}
for name,width in (('baseline',6),('network',8)):
    folds=prior['models'][name]['folds'];assert len(folds)==21
    predictions=np.array([expit((x[:,:width]/np.array(f['scale']))@np.array(f['coefficients'])) for f in folds])
    p=predictions.mean(axis=0)
    scalar=np.array([sum(float(expit(sum(row[k]*f['coefficients'][k]/f['scale'][k] for k in range(width)))) for f in folds)/21 for row in x])
    assert np.allclose(p,scalar,atol=1e-14,rtol=0)
    p=np.clip(p,1e-15,1-1e-15);loss=-(y*np.log(p)+(1-y)*np.log1p(-p));losses[name]=loss
    models[name]={'logloss':float(loss.mean()),'brier':float(np.mean((p-y)**2)),
                  'predicted_positive':float(p.sum()),'equal_slice_logloss':float(np.mean([loss[sids==sid].mean() for sid in set(sids)])),
                  'probabilities':p.tolist()}
delta=losses['network']-losses['baseline']
out={'contract_sha256':sha(HERE/'allen_human_frozen_presence_contract.json'),
     'dyads':len(pairs),'directions':len(y),'positive_directions':int(y.sum()),
     'experiments':len(groups),'slices':len(set(sids)),
     'models':models,'delta_logloss':float(delta.mean()),
     'slices_improved':sum(float(delta[sids==sid].mean())<0 for sid in set(sids)),
     'pia_at_least_1200_directions':int(np.sum(x[:,2]*1000+np.abs(x[:,3])*50>=1200)),
     'pairs':pairs,'mask':[mask[i] for i in range(len(pairs))],
     'verification':'PASS hidden-label exclusion, direction reversal, finite inputs, fixed 21-model ensemble and scalar reconstruction'}
save('allen_human_frozen_presence_result.json',out)
print(json.dumps({**{k:v for k,v in out.items() if k not in ('pairs','mask','models')},'models':{n:{k:v for k,v in m.items() if k!='probabilities'} for n,m in models.items()}},indent=2))
