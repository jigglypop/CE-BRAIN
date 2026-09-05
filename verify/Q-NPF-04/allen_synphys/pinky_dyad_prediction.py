"""Pinky에서 일정한 양방향 의존성의 내부 예측과 Minnie 계수 전이를 검사한다."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
import masked_neighbor_prediction_polished as marginal
import masked_dyad_dependence as joint

HERE=marginal.HERE
BASE=marginal.BASE
STORE=BASE.ROOT/'data/external/pinky_dyad_prediction'


def write_once(path,value):
    if path.exists():assert json.loads(path.read_text(encoding='utf-8'))==value,path
    else:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def load_data():
    contract=json.loads((HERE/'pinky_local_contract.json').read_text())
    for path,digest in contract['source_sha256'].items():assert BASE.sha(BASE.ROOT/path)==digest
    folder=BASE.ROOT/'data/external/microns_pinky_v185'
    with (folder/'soma_valence_v185.csv').open(newline='') as f:
        cells=sorted([r for r in csv.DictReader(f) if r['cell_type']=='e'],key=lambda r:int(r['pt_root_id']))
    roots=[int(r['pt_root_id']) for r in cells];index={r:i for i,r in enumerate(roots)}
    assert len(roots)==len(index)==362
    xyz=np.array([list(map(int,r['pt_position'].strip('[]').split())) for r in cells])*[.00354,.00354,.04]
    a=np.zeros((362,362),dtype=bool);self_count=0
    with (folder/'soma_subgraph_synapses_spines_v185.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            u,v=index[int(r['pre_root_id'])],index[int(r['post_root_id'])]
            if u==v:self_count+=1
            else:a[u,v]=True
    assert self_count==2 and a.sum()==1734 and (a&a.T).sum()//2==31
    assert np.sum((a.sum(0)+a.sum(1))==0)==28
    c=np.digitize(np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=2),[50,100,200,400,800])
    return roots,xyz,a,c


def main():
    previous_path=HERE/'masked_dyad_dependence_result.json'
    previous=json.loads(previous_path.read_text())
    coefficients=[r['coefficients'][0] for r in previous['records'] if r['model']=='constant']
    assert len(coefficients)==5
    transfer=float(np.mean(coefficients))
    spec=dict(question='Does fixed-marginal reciprocal dependence improve masked prediction in Pinky, including a coefficient frozen from Minnie?',
              scope='As-released362Pinky e-labelled cells, retain28zero-degreecells, threshold1, omit2selfannotations; source discrepancies and proofreading limitations unchanged',
              split='Same balanced5fold procedure, new fixedseed2026092600, both directions of eachdyad hidden together',
              baseline='Same fixed ridge sender/receiver/distance model, fitted only on Pinky training labels in eachfold; no neighbor features; same Newton correction and1e-5gradientgate',
              models=['independent','pinky_fitted_constant','minnie_frozen_constant'],
              transfer_log_odds=transfer,transfer_rule='Unweighted mean of five previously saved Minnie constant log-odds coefficients, fixed before Pinky prediction; only dependence coefficient transferred, not marginal model',
              endpoint='Primary heldoutfourstate logloss; secondarymutual logloss/Brier and predictedcount; no pvalue',
              interpretation='Different tissue but already inspected data, different age/volume/QC. Adaptive transport and internal validation, not independent preregistered confirmation or causal feedback inference.',
              prior_sha256=BASE.sha(previous_path),source_contract_sha256=BASE.sha(HERE/'pinky_local_contract.json'),
              marginal_code_sha256=BASE.sha(Path(marginal.__file__)),joint_code_sha256=BASE.sha(Path(joint.__file__)),code_sha256=BASE.sha(Path(__file__)))
    cp=HERE/'pinky_dyad_prediction_contract.json';write_once(cp,spec)
    roots,xyz,a,c=load_data();n=len(a);u,v=np.triu_indices(n,1)
    assignment=np.empty(len(u),dtype=np.int8)
    assignment[np.random.default_rng(2026092600).permutation(len(u))]=np.arange(len(u))%5
    folds=np.full((n,n),-1,dtype=np.int8);folds[u,v]=assignment;folds[v,u]=assignment
    STORE.mkdir(exist_ok=True);split_path=STORE/'split.npz'
    if split_path.exists():
        with np.load(split_path,allow_pickle=False) as f:assert np.array_equal(f['folds'],folds) and f['roots'].tolist()==roots
    else:
        with split_path.open('xb') as stream:np.savez_compressed(stream,folds=folds,roots=np.array(roots,dtype=np.int64))
    records=[];feature=np.zeros((n,n,0))
    for fold in range(5):
        test=folds==fold;train=(folds>=0)&~test;tr=train[u,v];te=test[u,v]
        receipt=STORE/f'{fold}_marginal.json';path=receipt.with_suffix('.npz')
        if receipt.exists():
            base=json.loads(receipt.read_text());assert base['contract_sha256']==BASE.sha(cp) and BASE.sha(path)==base['fitted_sha256']
            with np.load(path,allow_pickle=False) as f:theta=f['theta'];center=f['center'];scale=f['scale']
        else:
            theta,center,scale,diag=marginal.fit(a&train,train,c,feature,[])
            assert diag['gate_pass'],diag
            with path.open('xb') as stream:np.savez_compressed(stream,theta=theta,center=center,scale=scale)
            base=dict(contract_sha256=BASE.sha(cp),diagnostic=diag,fitted_sha256=BASE.sha(path));write_once(receipt,base)
        p=expit(marginal.logits(theta,center,scale,c,feature,[],u,v,n));q=expit(marginal.logits(theta,center,scale,c,feature,[],v,u,n))
        y=2*a[u,v].astype(int)+a[v,u].astype(int)
        for name in spec['models']:
            rp=STORE/f'{fold}_{name}.json';fp=rp.with_suffix('.npz')
            if rp.exists():
                r=json.loads(rp.read_text());assert r['contract_sha256']==BASE.sha(cp) and BASE.sha(fp)==r['fitted_sha256']
            else:
                if name=='independent':coef=np.zeros(1);diag=dict(gate_pass=True)
                elif name=='minnie_frozen_constant':coef=np.array([transfer]);diag=dict(gate_pass=True,fit_on_pinky=False)
                else:coef,diag=joint.fit(np.ones((tr.sum(),1)),p[tr],q[tr],y[tr])
                assert diag['gate_pass'],diag
                table,_,_=joint.distribution(p[te],q[te],np.full(te.sum(),coef[0]))
                with fp.open('xb') as stream:np.savez_compressed(stream,probabilities=table,coef=coef)
                r=dict(fold=fold,model=name,coefficient=float(coef[0]),diagnostic=diag,metrics=joint.metrics(table,y[te]),
                       fitted_sha256=BASE.sha(fp),contract_sha256=BASE.sha(cp));write_once(rp,r)
            records.append(r);print(json.dumps(r),flush=True)
    summary={}
    for name in spec['models']:
        rows=[r for r in records if r['model']==name];total=sum(r['metrics']['dyads'] for r in rows)
        summary[name]={key:sum(r['metrics'][key]*r['metrics']['dyads'] for r in rows)/total for key in ('joint_logloss','mutual_logloss','mutual_brier')}
        summary[name].update(mutual_observed=sum(r['metrics']['mutual_observed'] for r in rows),mutual_predicted_sum=sum(r['metrics']['mutual_predicted_sum'] for r in rows),
                             fold_joint_change_vs_independent=[r['metrics']['joint_logloss']-next(z['metrics']['joint_logloss'] for z in records if z['fold']==r['fold'] and z['model']=='independent') for r in rows])
    result=dict(contract_sha256=BASE.sha(cp),split_sha256=BASE.sha(split_path),graph_sha256=hashlib.sha256(a.tobytes()).hexdigest(),transfer_log_odds=transfer,
                summary=summary,records=records,receipt_sha256={p.name:BASE.sha(p) for p in sorted(STORE.glob('*.json'))})
    write_once(HERE/'pinky_dyad_prediction_result.json',result);print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
