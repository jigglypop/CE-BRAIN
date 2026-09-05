"""고정 방향별 주변 확률에서 환자 제외 양방향 결합 예측."""
import csv
import io
import json
import zipfile
from pathlib import Path
import numpy as np
from scipy.special import expit
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from masked_dyad_dependence import distribution,fit,metrics,fixtures

HERE=Path(__file__).resolve().parent;source=HERE/'planert2025_masked_presence_parsed_result.json'
prior=json.loads(source.read_text(encoding='utf-8'));archive=ROOT/'data/external/planert2025_human/humandata.zip'
save('planert2025_joint_presence_contract.json',{
    'question':'Does a training-only constant directional odds ratio improve held-out four-state predictions?',
    'scope':'same 2060 dyads/21 patients and both-direction masks from full-presence analysis',
    'margins':'reconstruct each held-patient network model from saved coefficients and training RMS; apply same model to its training dyads for dependence fit',
    'leakage_gate':'do NOT fit dependence on pooled OOF training predictions, whose models may include held patient; all fitting uses only current outer training patients',
    'models':'independent eta=0; train-only constant eta with eta^2/2 penalty; marginals identical',
    'probabilities':'00=1-p-q+t,01=q-t,10=p-t,11=t; eta=log(P11*P00/(P10*P01))',
    'endpoints':'joint logloss, equal-patient logloss, mutual Brier and expected count; no causal reciprocity claim',
    'checks':'recover all existing held-out probabilities; gradient gate; probability sums and margins; eta0 equals products; analytic probability fixtures',
    'limits':'training margins use training labels; exploratory; constant dyad dependence not full graph distribution; same lineage/QC limitations',
    'source_sha256':sha(source),'helper_sha256':sha(HERE/'masked_dyad_dependence.py'),'code_sha256':sha(Path(__file__))})
assert sha(archive)=='6b0d7244dec5c665a88d0d1828ae842d084bb737a6df9f86561d53d8564c4bfd'
fixtures()
with zipfile.ZipFile(archive) as z:
    cells={r['cellid']:r for r in csv.DictReader(io.StringIO(z.read('humandata/data_tables/tcell_all_psdn.csv').decode('utf-8-sig')))}
pairs=prior['pairs'];mask=prior['mask'];features=[]
for i,r in enumerate(pairs):
    for a,b in ((r['a'],r['b']),(r['b'],r['a'])):
        ca,cb=cells[a],cells[b];da,db=float(ca['piadistance']),float(cb['piadistance'])
        out=incoming=out_n=in_n=0
        for j,o in enumerate(pairs):
            if o['cluster']!=r['cluster'] or mask[j]==mask[i]:continue
            for pre,post,y in ((o['a'],o['b'],o['labels'][0]),(o['b'],o['a'],o['labels'][1])):
                if pre==a:out+=y;out_n+=1
                if post==b:incoming+=y;in_n+=1
        features.append([1,np.log1p(r['distance']/100),(da+db)/2000,(da-db)/100,
                         np.log(float(ca['R_in'])/float(cb['R_in'])),np.log(float(ca['rheo'])/float(cb['rheo'])),
                         (out+1)/(out_n+2),(incoming+1)/(in_n+2)])
x=np.array(features);pid=np.array([r['patient'] for r in pairs]);truth=np.array([2*r['labels'][0]+r['labels'][1] for r in pairs])
tables={n:np.zeros((len(pairs),4)) for n in ('independent','constant')};folds=[]
saved=np.array(prior['models']['network']['probabilities']).reshape(-1,2)
for patient in sorted(set(pid)):
    test=pid==patient;train=~test
    row=next(f for f in prior['models']['network']['folds'] if f['patient']==patient)
    probability=expit((x/np.array(row['scale']))@np.array(row['coefficients'])).reshape(-1,2)
    assert np.allclose(probability[test],saved[test],atol=1e-12)
    # Training probabilities come from THIS outer fold, not other folds.
    p,q=probability[:,0],probability[:,1]
    theta,diagnostic=fit(np.ones((int(train.sum()),1)),p[train],q[train],truth[train]);assert diagnostic['gate_pass']
    fold={'patient':str(patient),'eta':float(theta[0]),'diagnostic':diagnostic,'metrics':{}}
    for name,eta in (('independent',0.),('constant',float(theta[0]))):
        table,_,_=distribution(p[test],q[test],np.full(int(test.sum()),eta))
        assert np.allclose(table.sum(1),1) and np.allclose(table[:,2]+table[:,3],p[test]) and np.allclose(table[:,1]+table[:,3],q[test])
        if eta==0:assert np.allclose(table[:,3],p[test]*q[test],atol=1e-13)
        tables[name][test]=table;fold['metrics'][name]=metrics(table,truth[test])
    folds.append(fold)
summary={name:{**metrics(table,truth),'equal_patient_logloss':float(np.mean([f['metrics'][name]['joint_logloss'] for f in folds]))} for name,table in tables.items()}
assert np.isclose(summary['independent']['joint_logloss'],2*prior['models']['network']['logloss'],atol=1e-12)
out={'contract_sha256':sha(HERE/'planert2025_joint_presence_contract.json'),'summary':summary,
     'patients_improved':sum(f['metrics']['constant']['joint_logloss']<f['metrics']['independent']['joint_logloss'] for f in folds),
     'eta_range':[min(f['eta'] for f in folds),max(f['eta'] for f in folds)],'folds':folds,
     'probabilities':{k:v.tolist() for k,v in tables.items()},'verification':'PASS: outer-fold marginal reconstruction, training-only dependence, gradients and fixed margins'}
save('planert2025_joint_presence_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ('folds','probabilities')},indent=2))
