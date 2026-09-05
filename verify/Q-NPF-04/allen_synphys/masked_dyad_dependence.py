"""방향별 주변 확률을 고정한 양방향 공동 확률 예측."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
import masked_neighbor_prediction_polished as source

HERE=source.HERE
BASE=source.BASE
STORE=BASE.ROOT/'data/external/masked_dyad_dependence'
MODELS={'independent':None,'constant':[],'input':[0],'output':[1],'both':[0,1]}


def distribution(p,q,eta):
    """Solve log(P11 P00 / P10 P01)=eta under fixed Bernoulli margins."""
    lower=np.maximum(0.,p+q-1);upper=np.minimum(p,q)
    for _ in range(56):
        t=(lower+upper)/2
        with np.errstate(divide='ignore'):
            value=np.log(t)+np.log(1-p-q+t)-np.log(p-t)-np.log(q-t)
        less=value<eta
        lower=np.where(less,t,lower);upper=np.where(less,upper,t)
    t=(lower+upper)/2
    probs=np.column_stack([1-p-q+t,q-t,p-t,t])
    assert np.isfinite(probs).all() and np.all(probs>0)
    s=np.sum(1/probs,axis=1)
    first=1/s
    ds=-1/probs[:,3]**2-1/probs[:,0]**2+1/probs[:,2]**2+1/probs[:,1]**2
    second=-ds/s**3
    return probs,first,second


def objective(theta,x,p,q,y,hessian=False):
    probabilities,first,second=distribution(p,q,x@theta)
    chosen=probabilities[np.arange(len(y)),y]
    signs=np.where((y==0)|(y==3),1.,-1.)
    loss=float(-np.log(chosen).sum()+.5*np.dot(theta,theta))
    grad=x.T@(-signs*first/chosen)+theta
    if hessian:
        weights=(first/chosen)**2-signs*second/chosen
        return loss,grad,x.T@(x*weights[:,None])+np.eye(len(theta))
    return loss,grad


def fixtures():
    p=np.array([.01,.2,.8,.7]);q=np.array([.03,.4,.9,.15])
    for eta in (-3.,0.,3.):
        table,_,_=distribution(p,q,np.full(4,eta))
        assert np.allclose(table.sum(1),1) and np.allclose(table[:,2]+table[:,3],p)
        assert np.allclose(table[:,1]+table[:,3],q)
        assert np.allclose(np.log(table[:,3]*table[:,0]/(table[:,2]*table[:,1])),eta,atol=1e-9)
        if eta==0:assert np.allclose(table[:,3],p*q,atol=1e-14)
    x=np.column_stack([np.ones(4),[-1.,.2,.5,1.]])
    y=np.arange(4);theta=np.array([.3,-.1]);_,g=objective(theta,x,p,q,y)
    for k in range(2):
        d=np.eye(2)[k]*1e-5
        finite=(objective(theta+d,x,p,q,y)[0]-objective(theta-d,x,p,q,y)[0])/2e-5
        assert abs(finite-g[k])<1e-7


def fit(x,p,q,y):
    solved=minimize(objective,np.zeros(x.shape[1]),args=(x,p,q,y),jac=True,method='BFGS',options=dict(gtol=1e-6,maxiter=1000))
    theta=solved.x;errors=[]
    for i in range(4):
        loss,g,h=objective(theta,x,p,q,y,hessian=True)
        error=float(abs(g).max());errors.append(error)
        if error<=1e-7 or i==3:break
        step=np.linalg.solve(h,g)
        for factor in (1.,.5,.25,.125,.0625):
            candidate=theta-factor*step
            if objective(candidate,x,p,q,y)[0]<=loss+1e-8:
                theta=candidate;break
        else:break
    loss,g=objective(theta,x,p,q,y)
    return theta,dict(gate_pass=bool(abs(g).max()<=1e-5),max_gradient=float(abs(g).max()),
                      optimizer_success=bool(solved.success),message=str(solved.message),gradient_history=errors,training_penalized_loss=loss)


def metrics(probabilities,y):
    truth=y==3;t=probabilities[:,3]
    return dict(dyads=len(y),joint_logloss=float(-np.log(probabilities[np.arange(len(y)),y]).mean()),
                mutual_logloss=float(-(truth*np.log(t)+(~truth)*np.log1p(-t)).mean()),
                mutual_brier=float(np.mean((truth-t)**2)),mutual_observed=int(truth.sum()),mutual_predicted_sum=float(t.sum()))


def main():
    fixtures()
    prior_path=HERE/'masked_neighbor_prediction_polished_result.json'
    prior=json.loads(prior_path.read_text());assert prior['all_fits_pass']
    spec=dict(question='Does modeling directional dependence improve masked dyad prediction with unchanged directional marginals?',
              design='Same exploratory five dyad folds and training-only features; no biological holdout',
              models=MODELS,probabilities='P11=t,P10=p-t,P01=q-t,P00=1-p-q+t;logoddsratio=eta;fixed p,q from previous base sender/receiver/distance fit',
              eta='0 for independent; intercept for constant; intercept+standardizedlog1p masked common neighbors for input/output/both',
              fitting='Train dyads only, ridge0.5*sum(coefficients^2) including dependence intercept; BFGS then up to3Newton updates, absolute gradient<=1e-5',
              endpoint='Primary heldout four-state joint logloss; secondary mutual logloss/Brier and expectedcount. Directional marginals unchanged by construction.',
              interpretation='Training baseline margins estimated on same training labels, adaptive selection of model forms after earlier outcomes, overlapping folds. No pvalue, causal feedback inference, or claim of unchanged marginal improvement.',
              code_sha256=BASE.sha(Path(__file__)),prior_sha256=BASE.sha(prior_path),prior_verification_sha256=BASE.sha(HERE/'masked_neighbor_prediction_verification.json'),
              source_code_sha256=BASE.sha(Path(source.__file__)),split_sha256=prior['split_sha256'])
    cp=HERE/'masked_dyad_dependence_contract.json'
    source.source.source.run.shared.source.write_once(cp,spec)
    roots,xyz,a,c=source.source.source.run.shared.source.data();n=len(a)
    assert BASE.sha(source.STORE/'split.npz')==prior['split_sha256']
    with np.load(source.STORE/'split.npz',allow_pickle=False) as f:
        folds=f['folds'];assert f['roots'].tolist()==roots
    STORE.mkdir(exist_ok=True);records=[]
    for fold in range(5):
        test=folds==fold;train=(folds>=0)&~test;f=source.features(a,train)
        baseline=next(r for r in prior['records'] if r['fold']==fold and r['model']=='base')
        pp=source.STORE/f'{fold}_base.npz';assert BASE.sha(pp)==baseline['fitted_sha256']
        with np.load(pp,allow_pickle=False) as saved:
            theta=saved['theta'];mean=saved['mean'];scale=saved['scale']
        u,v=np.triu_indices(n,1);tr=train[u,v];te=test[u,v]
        p=expit(source.logits(theta,mean,scale,c,f,[],u,v,n));q=expit(source.logits(theta,mean,scale,c,f,[],v,u,n))
        y=2*a[u,v].astype(int)+a[v,u].astype(int)
        for name,cols in MODELS.items():
            receipt=STORE/f'{fold}_{name}.json';path=receipt.with_suffix('.npz')
            if receipt.exists():
                r=json.loads(receipt.read_text());assert r['contract_sha256']==BASE.sha(cp)
                if r['diagnostic']['gate_pass']:assert BASE.sha(path)==r['fitted_sha256']
            else:
                columns=[] if cols is None else cols
                raw=f[u,v][:,columns];center=raw[tr].mean(0);sd=raw[tr].std(0);sd=np.where(sd>0,sd,1.)
                x=np.column_stack([np.ones(len(u)),(raw-center)/sd])
                if name=='independent':coef=np.zeros(1);diag=dict(gate_pass=True,max_gradient=None)
                else:coef,diag=fit(x[tr],p[tr],q[tr],y[tr])
                r=dict(fold=fold,model=name,diagnostic=diag,contract_sha256=BASE.sha(cp))
                if diag['gate_pass']:
                    table,_,_=distribution(p[te],q[te],x[te]@coef)
                    assert np.allclose(table[:,2]+table[:,3],p[te],atol=1e-12) and np.allclose(table[:,1]+table[:,3],q[te],atol=1e-12)
                    with path.open('xb') as stream:np.savez_compressed(stream,coef=coef,center=center,scale=sd,probabilities=table)
                    r.update(metrics=metrics(table,y[te]),coefficients=coef.tolist(),fitted_sha256=BASE.sha(path))
                source.source.source.run.shared.source.write_once(receipt,r)
            records.append(r);print(json.dumps(r),flush=True)
    summary=None
    if all(r['diagnostic']['gate_pass'] for r in records):
        summary={}
        for name in MODELS:
            rows=[r for r in records if r['model']==name];count=sum(r['metrics']['dyads'] for r in rows)
            summary[name]={key:sum(r['metrics'][key]*r['metrics']['dyads'] for r in rows)/count for key in ('joint_logloss','mutual_logloss','mutual_brier')}
            summary[name]['mutual_predicted_sum']=sum(r['metrics']['mutual_predicted_sum'] for r in rows)
            for reference in ('independent','constant'):
                summary[name]['fold_joint_change_vs_'+reference]=[r['metrics']['joint_logloss']-next(z['metrics']['joint_logloss'] for z in records if z['fold']==r['fold'] and z['model']==reference) for r in rows]
        assert np.isclose(summary['independent']['joint_logloss'],2*prior['summary']['base']['direction_logloss'],atol=1e-12)
    result=dict(contract_sha256=BASE.sha(cp),summary=summary,records=records)
    source.source.source.run.shared.source.write_once(HERE/'masked_dyad_dependence_result.json',result)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
