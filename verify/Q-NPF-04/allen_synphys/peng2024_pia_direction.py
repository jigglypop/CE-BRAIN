"""ER 연질막 거리 차이의 환자 제외 방향 예측."""
import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;archive=ROOT/'data/external/peng2024_human/data.zip'
assert sha(archive)=='3711f8b8b911a24b0e5fd69e6e6c845f9e8601539807a9b960118c77ba5ad68d'
save('peng2024_pia_direction_contract.json',{
    'question':'Does ER pia-distance difference predict one-way orientation and explain directional imbalance?',
    'scope':'ER one-way dyads with finite piadistance at both cells; all available, no amplitude selection; TR availability only until coordinate transformation provenance confirmed',
    'provenance_gate':'ER difference equals rotated-y difference plus distance_pia offset difference within 1e-5',
    'model':'p(lexicographic a to b)=sigmoid(beta*(pia_a-pia_b)/100); no intercept; ridge beta^2/2; leave entire patient out',
    'endpoint':'held-out logloss vs log2; expected S under independent biased directions on same retained skeleton; no causal inference',
    'limits':'posthoc exploratory model; missing positions change sample; patient exclusion not independent confirmation; no TR effect claim',
    'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
cohorts={};availability={}
with zipfile.ZipFile(archive) as z:
    for co in ('er','tr'):
        def read(n):return list(csv.DictReader(io.StringIO(z.read('data/'+n+'_'+co+'.csv').decode('utf-8-sig'))))
        cells={r['cellid'].replace(' ',''):r for r in read('tcell')};rows=read('tconnection')
        lookup={(r['cellid_pre'],r['cellid_post']):r for r in rows};edges=[];count=0;errors=[]
        for r in rows:
            a,b=r['cellid_pre'],r['cellid_post']
            if a>=b or int(r['connected'])+int(lookup[b,a]['connected'])!=1:continue
            count+=1;ca,cb=cells[a],cells[b];da,db=float(ca['piadistance']),float(cb['piadistance'])
            if not np.isfinite(da) or not np.isfinite(db):continue
            assert ca['patientid']==cb['patientid']==r['patientid']
            if co=='er':
                diff=float(ca['coordinate_rotated_2'])-float(cb['coordinate_rotated_2'])+float(ca['distance_pia'])-float(cb['distance_pia'])
                error=abs(da-db-diff);assert np.isfinite(error) and error<1e-5;errors.append(error)
            edges.append({'a':a,'b':b,'cluster':r['clusterid'],'patient':r['patientid'],'x':(da-db)/100,'y':int(r['connected'])})
        availability[co]={'oneway_dyads':count,'finite_pia_dyads':len(edges),'excluded':count-len(edges),'patients':len({e['patient'] for e in edges}),
                          'coordinate_max_error':max(errors) if errors else None}
        cohorts[co]=edges
edges=cohorts['er'];folds=[]
for patient in sorted({e['patient'] for e in edges}):
    train=[e for e in edges if e['patient']!=patient];test=[e for e in edges if e['patient']==patient]
    x=np.array([e['x'] for e in train]);y=np.array([e['y'] for e in train]);beta=0.
    for _ in range(100):
        p=expit(beta*x);g=float(x@(p-y)+beta)
        if abs(g)<1e-10:break
        beta-=g/float((x*x)@(p*(1-p))+1)
    assert abs(g)<1e-9 and np.allclose(expit(-beta*x),1-expit(beta*x))
    for e in test:
        eta=beta*e['x'];e['p']=float(expit(eta));e['loss']=float(np.logaddexp(0,eta)-e['y']*eta)
    folds.append({'patient':patient,'beta':beta,'count':len(test),'logloss':float(np.mean([e['loss'] for e in test]))})
groups=defaultdict(list)
for e in edges:groups[e['cluster']].append(e)
records=[]
for cluster,ee in groups.items():
    nodes=sorted({e[k] for e in ee for k in ('a','b')});inc=np.zeros((len(nodes),len(ee)))
    for j,e in enumerate(ee):inc[nodes.index(e['a']),j]=1;inc[nodes.index(e['b']),j]=-1
    mu=np.array([2*e['p']-1 for e in ee]);net=inc@mu
    expected=float(net@net+2*np.sum(1-mu*mu));obs=int(np.sum((inc@np.array([2*e['y']-1 for e in ee]))**2))
    # Independent pairwise edge expansion of the expected quadratic score.
    gram=inc.T@inc;off=gram-np.diag(np.diag(gram));alternative=float(2*len(ee)+mu@off@mu)
    assert abs(expected-alternative)<1e-9
    records.append({'cluster':cluster,'patient':ee[0]['patient'],'observed':obs,'expected':expected,'fair_expected':2*len(ee)})
out={'contract_sha256':sha(HERE/'peng2024_pia_direction_contract.json'),'availability':availability,
     'fair_logloss':float(np.log(2)),'pia_logloss':float(np.mean([e['loss'] for e in edges])),
     'equal_patient_logloss':float(np.mean([f['logloss'] for f in folds])),
     'patients_improved':int(sum(f['logloss']<np.log(2)-1e-12 for f in folds)),
     'beta_range':[min(f['beta'] for f in folds),max(f['beta'] for f in folds)],
     'observed':sum(r['observed'] for r in records),'fair_expected':sum(r['fair_expected'] for r in records),
     'pia_expected':sum(r['expected'] for r in records),'folds':folds,'records':records,'edges':edges,
     'verification':'PASS: coordinate difference, patient split, gradient, reversal, quadratic identity'}
save('peng2024_pia_direction_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ('folds','records','edges')},indent=2))
