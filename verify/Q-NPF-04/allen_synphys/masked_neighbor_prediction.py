"""양방향을 함께 가린 5분할 내부 연결 예측. 탐색적 검증이다."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import expit
import sgsg_refit_residual as source

HERE=source.HERE
BASE=source.BASE
STORE=BASE.ROOT/'data/external/masked_neighbor_prediction'
MODELS={'base':[], 'input':[0], 'output':[1], 'both':[0,1]}


def features(a,train):
    x=(a&train).astype(np.int32)
    return np.stack([np.log1p(x.T@x),np.log1p(x@x.T)],axis=-1)


def fit(train_a,train,c,f,columns):
    n=len(train_a);u,v=np.nonzero(train);y=train_a[u,v].astype(float)
    raw=f[u,v][:,columns]
    mean=raw.mean(0);scale=raw.std(0);scale=np.where(scale>0,scale,1.)
    x=(raw-mean)/scale
    b=c[u,v];length=1+2*n+6+len(columns)
    def objective(theta):
        z=theta[0]+theta[1+u]+theta[1+n+v]+theta[1+2*n+b]+x@theta[1+2*n+6:]
        e=expit(z)-y
        grad=np.concatenate([[e.sum()],np.bincount(u,weights=e,minlength=n),np.bincount(v,weights=e,minlength=n),np.bincount(b,weights=e,minlength=6),x.T@e])
        grad[1:]+=theta[1:]
        loss=float(np.sum(np.logaddexp(0,z)-y*z)+.5*np.dot(theta[1:],theta[1:]))
        return loss,grad
    start=np.zeros(length);start[0]=np.log(y.mean()/(1-y.mean()))
    solved=minimize(objective,start,jac=True,method='L-BFGS-B',options=dict(maxiter=2000,gtol=1e-6,ftol=0.,maxls=50))
    loss,g=objective(solved.x)
    error=float(np.max(abs(g)))
    return solved.x,mean,scale,dict(gate_pass=bool(error<=1e-5 and np.isfinite(solved.x).all()),max_gradient=error,
                                   optimizer_success=bool(solved.success),message=str(solved.message),iterations=int(solved.nit),penalized_training_loss=loss)


def logits(theta,mean,scale,c,f,columns,u,v,n):
    x=(f[u,v][:,columns]-mean)/scale
    return theta[0]+theta[1+u]+theta[1+n+v]+theta[1+2*n+c[u,v]]+x@theta[1+2*n+6:]


def metrics(a,test,z):
    y=a[test].astype(float);scores=z[test];p=expit(scores)
    u,v=np.nonzero(np.triu(test,1));truth=(a[u,v]&a[v,u]).astype(float)
    logq=-np.logaddexp(0,-z[u,v])-np.logaddexp(0,-z[v,u]);q=np.exp(logq)
    dyad_loss=-truth*logq-(1-truth)*np.log(-np.expm1(logq))
    return dict(directions=len(y),positive_directions=int(y.sum()),direction_logloss=float(np.mean(np.logaddexp(0,scores)-y*scores)),
                direction_brier=float(np.mean((y-p)**2)),dyads=len(truth),mutual_observed=int(truth.sum()),mutual_predicted_sum=float(q.sum()),
                mutual_logloss=float(dyad_loss.mean()),mutual_brier=float(np.mean((truth-q)**2)))


def main():
    spec=dict(question='Do common-input features improve masked-edge prediction beyond regularized node effects and distance?',
              population='existing347Minnie23Pcells, threshold1; all60031dyads; both directions hidden together',
              split='default_rng(2026092500).permutation of lexicographicupperdyads, assign permutedpositions modulo5; balanced without outcome stratification',
              leakage='All heldout edges removed before all common-neighbor features. Train labels only under train mask. Train feature means/scales only. No degree computed from heldout labels.',
              models=MODELS,features='log1p common inputs/outputs in masked training graph; standardized using training directional pairs',
              baseline='intercept + sender effect + receiver effect + six distance-bin offsets; all parameters except intercept get fixed ridge penalty0.5*sum(theta^2); same penalty for added features',
              fit='L-BFGS-B max2000 gtol1e-6 ftol0; require max absolute penalized gradient<=1e-5. Any failed fit stops aggregate interpretation; no retuning.',
              endpoints='Primary heldout directional logloss; secondary directionalBrier, mutualBernoulli logloss/Brier and sum of product probabilities. Mutual prediction assumes conditional independence given training graph.',
              inference='Adaptive internal5fold assessment on already inspected dataset. Report weighted means and pairedfold changes, no pvalue, independent biological holdout, or causal claim.',
              code_sha256=BASE.sha(Path(__file__)),prior_sha256=BASE.sha(HERE/'sgsg_common_neighbors_result.json'),
              loader_sha256=BASE.sha(Path(source.__file__)),python=sys.version,numpy=np.__version__,scipy=scipy.__version__)
    cp=HERE/'masked_neighbor_prediction_contract.json'
    source.source.run.shared.source.write_once(cp,spec)
    roots,xyz,a,c=source.source.run.shared.source.data();n=len(a)
    u,v=np.triu_indices(n,1);order=np.random.default_rng(2026092500).permutation(len(u))
    folds=np.full((n,n),-1,dtype=np.int8);assignment=np.empty(len(u),dtype=np.int8);assignment[order]=np.arange(len(u))%5
    folds[u,v]=assignment;folds[v,u]=assignment
    STORE.mkdir(exist_ok=True)
    split_path=STORE/'split.npz'
    if split_path.exists():
        with np.load(split_path,allow_pickle=False) as f:assert np.array_equal(f['folds'],folds) and f['roots'].tolist()==roots
    else:
        with split_path.open('xb') as stream:np.savez_compressed(stream,folds=folds,roots=np.array(roots,dtype=np.int64))
    records=[]
    for fold in range(5):
        test=folds==fold;train=(folds>=0)&~test;train_a=a&train;f=features(a,train)
        for name,columns in MODELS.items():
            receipt=STORE/f'{fold}_{name}.json';path=receipt.with_suffix('.npz')
            if receipt.exists():
                r=json.loads(receipt.read_text());assert r['contract_sha256']==BASE.sha(cp)
                if r['diagnostic']['gate_pass']:assert BASE.sha(path)==r['fitted_sha256']
            else:
                theta,mean,scale,diag=fit(train_a,train,c,f,columns)
                r=dict(fold=fold,model=name,diagnostic=diag,contract_sha256=BASE.sha(cp))
                if diag['gate_pass']:
                    ii,jj=np.nonzero(test);z=np.zeros_like(a,dtype=float)
                    z[ii,jj]=logits(theta,mean,scale,c,f,columns,ii,jj,n)
                    with path.open('xb') as stream:np.savez_compressed(stream,theta=theta,mean=mean,scale=scale,heldout_logits=z[test])
                    r.update(metrics=metrics(a,test,z),fitted_sha256=BASE.sha(path))
                source.source.run.shared.source.write_once(receipt,r)
            records.append(r);print(json.dumps(r),flush=True)
    complete=all(r['diagnostic']['gate_pass'] for r in records)
    summary=None
    if complete:
        summary={}
        for name in MODELS:
            rows=[r['metrics'] for r in records if r['model']==name]
            summary[name]={key:float(sum(x[key]*x['directions' if key.startswith('direction_') else 'dyads'] for x in rows)/sum(x['directions' if key.startswith('direction_') else 'dyads'] for x in rows)) for key in ('direction_logloss','direction_brier','mutual_logloss','mutual_brier')}
            summary[name]['mutual_observed']=sum(x['mutual_observed'] for x in rows)
            summary[name]['mutual_predicted_sum']=sum(x['mutual_predicted_sum'] for x in rows)
            summary[name]['fold_direction_logloss_change_vs_base']=[rows[i]['direction_logloss']-next(r['metrics']['direction_logloss'] for r in records if r['model']=='base' and r['fold']==i) for i in range(5)]
    result=dict(contract_sha256=BASE.sha(cp),split_sha256=BASE.sha(split_path),graph_sha256=hashlib.sha256(a.tobytes()).hexdigest(),all_fits_pass=complete,summary=summary,records=records)
    source.source.run.shared.source.write_once(HERE/'masked_neighbor_prediction_result.json',result)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
