"""연결쌍의 양방향 표지를 함께 가린 존재 예측."""
import csv
import hashlib
import io
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;archive=ROOT/'data/external/planert2025_human/humandata.zip'
assert sha(archive)=='6b0d7244dec5c665a88d0d1828ae842d084bb737a6df9f86561d53d8564c4bfd'
save('planert2025_masked_presence_parsed_contract.json',{
    'repair':'Treat literal NA distance as missing, as declared; retain original failed parser and contract; no model change',
    'question':'Do observed other connections predict hidden connection presence beyond geometry and intrinsic physiology?',
    'population':'all s11 tested pairs with both type1 cells satisfying prior four QC flags, finite pia<1200, positive Rin and rheobase; exclude whole duplicate-key clusters',
    'mask':'all eligible unordered pairs, regardless of labels; seed0 hash order alternating two groups per record; hide BOTH directions of target group',
    'baseline':'intercept, log1p(pair distance/100), mean pia/1000, signed pia difference/100, log Rin ratio, log rheobase ratio',
    'network_features':'visible sender outgoing rate and receiver incoming rate, each Beta(1,1) smoothed (positive+1)/(tested+2); no hidden labels',
    'fit':'leave whole patient out; train-only RMS scaling nonintercept features; ridge1 nonintercept, no intercept penalty; no tuning',
    'endpoint':'directional marginal logloss and Brier; equal-patient logloss; not independent dyads or joint graph likelihood',
    'checks':'all hidden labels flipped leave features unchanged; previous 523 one-way QC support recovered before distance filter; gradient<1e-8',
    'limits':'author QC, six excluded clusters, same lineage; conditional partial-graph completion not full brain reconstruction',
    'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
with zipfile.ZipFile(archive) as z:
    def read(n):return list(csv.DictReader(io.StringIO(z.read('humandata/data_tables/'+n).decode('utf-8-sig'))))
    cells={r['cellid']:r for r in read('tcell_all_psdn.csv')};raw=read('tconnection_all_psdn.csv')
pg=defaultdict(list)
for r in raw:pg[r['cellid_pre'],r['cellid_post']].append(r)
bad={r['clusterid'] for rr in pg.values() if len(rr)>1 for r in rr}
lookup={(r['cellid_pre'],r['cellid_post']):r for r in raw if r['clusterid'] not in bad}
def good(c):
    if c['type']!='1' or not all(c[k]=='1' for k in ('resting_bool','access_bool','false_high_access_bool','false_low_access_bool')):return False
    try:d,ri,rh=(float(c[k]) for k in ('piadistance','R_in','rheo'))
    except ValueError:return False
    return all(map(math.isfinite,(d,ri,rh))) and d<1200 and ri>0 and rh>0
pairs=[];oneway=0;missing_distance=0
for (a,b),r in lookup.items():
    if a>=b or r['synapse_type']!='s11' or not(good(cells[a]) and good(cells[b])):continue
    rev=lookup[b,a];assert r['connected'] in ('0','1') and rev['connected'] in ('0','1')
    ca,cb=cells[a],cells[b];assert ca['patientid']==cb['patientid']==r['patientid'] and ca['clusterid']==cb['clusterid']==r['clusterid']
    labels=[int(r['connected']),int(rev['connected'])];oneway+=int(sum(labels)==1)
    try:d=float(r['distance'])
    except ValueError:d=float('nan')
    if not math.isfinite(d):missing_distance+=1;continue
    assert d>=0 and abs(d-float(rev['distance']))<1e-6
    pairs.append({'a':a,'b':b,'patient':r['patientid'],'cluster':r['clusterid'],'distance':d,'labels':labels})
assert oneway==523
groups=defaultdict(list)
for i,r in enumerate(pairs):groups[r['cluster']].append(i)
mask={}
for cluster,indices in groups.items():
    order=sorted(indices,key=lambda i:hashlib.sha256(f"seed0|{pairs[i]['a']}|{pairs[i]['b']}".encode()).hexdigest())
    for j,i in enumerate(order):mask[i]=j%2
def rates(i,pre,post,flip=False):
    out=incoming=out_n=in_n=0
    for j in groups[pairs[i]['cluster']]:
        r=pairs[j];labels=[1-v for v in r['labels']] if flip and mask[j]==mask[i] else r['labels']
        if mask[j]==mask[i]:continue
        for a,b,y in ((r['a'],r['b'],labels[0]),(r['b'],r['a'],labels[1])):
            if a==pre:out+=y;out_n+=1
            if b==post:incoming+=y;in_n+=1
    return [(out+1)/(out_n+2),(incoming+1)/(in_n+2)]
features=[];labels=[];patients=[]
for i,r in enumerate(pairs):
    for a,b,y in ((r['a'],r['b'],r['labels'][0]),(r['b'],r['a'],r['labels'][1])):
        ca,cb=cells[a],cells[b];da,db=float(ca['piadistance']),float(cb['piadistance'])
        network=rates(i,a,b);assert network==rates(i,a,b,True)
        features.append([1,np.log1p(r['distance']/100),(da+db)/2000,(da-db)/100,
                         np.log(float(ca['R_in'])/float(cb['R_in'])),np.log(float(ca['rheo'])/float(cb['rheo']))]+network)
        labels.append(y);patients.append(r['patient'])
allx=np.array(features);y=np.array(labels);pid=np.array(patients);pnames=sorted(set(pid));models={};losses={}
for width,name in ((6,'baseline'),(8,'network')):
    loss=np.zeros(len(y));pred=np.zeros(len(y));folds=[]
    for patient in pnames:
        test=pid==patient;train=~test;scale=np.sqrt(np.mean(allx[train,:width]**2,axis=0));scale[scale<1e-10]=1;scale[0]=1
        x=allx[train,:width]/scale;target=y[train];beta=np.zeros(width);penalty=np.ones(width);penalty[0]=0
        def obj(b):return float(np.sum(np.logaddexp(0,x@b)-target*(x@b))+.5*np.sum(penalty*b*b))
        for _ in range(150):
            p=expit(x@beta);g=x.T@(p-target)+penalty*beta
            if np.max(np.abs(g))<1e-8:break
            h=x.T@((p*(1-p))[:,None]*x)+np.diag(penalty);step=np.linalg.solve(h,g);s=1.
            while np.max(np.abs(g))>=1e-5 and obj(beta-s*step)>obj(beta)-1e-4*s*float(g@step):
                s*=.5;assert s>1e-12
            beta-=s*step
        assert np.max(np.abs(g))<1e-8
        eta=(allx[test,:width]/scale)@beta;pred[test]=expit(eta);loss[test]=np.logaddexp(0,eta)-y[test]*eta
        folds.append({'patient':str(patient),'directions':int(test.sum()),'logloss':float(loss[test].mean()),'coefficients':beta.tolist(),'scale':scale.tolist()})
    models[name]={'logloss':float(loss.mean()),'equal_patient_logloss':float(np.mean([f['logloss'] for f in folds])),
                  'brier':float(np.mean((pred-y)**2)),'predicted_positive':float(pred.sum()),'folds':folds,'probabilities':pred.tolist()};losses[name]=loss
delta=losses['network']-losses['baseline']
out={'contract_sha256':sha(HERE/'planert2025_masked_presence_parsed_contract.json'),'dyads':len(pairs),'directions':len(y),'positive_directions':int(y.sum()),
     'missing_distance_dyads':missing_distance,'patients':len(pnames),'models':models,
     'patients_improved':sum(float(delta[pid==p].mean())<0 for p in pnames),'delta_logloss':float(delta.mean()),
     'pairs':pairs,'mask':[mask[i] for i in range(len(pairs))],'verification':'PASS: full dyad mask, QC support, hidden-label exclusion and fit gradients'}
save('planert2025_masked_presence_parsed_result.json',out)
print(json.dumps({**{k:v for k,v in out.items() if k not in ('models','pairs','mask')},'models':{n:{k:v for k,v in m.items() if k not in ('folds','probabilities')} for n,m in models.items()}},indent=2))
