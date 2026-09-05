"""Pinky 분할·학습 입력·주변 확률 보존·고정 계수 전이를 검증한다."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
import pinky_dyad_prediction as run


def main():
    path=run.HERE/'pinky_dyad_prediction_result.json';result=json.loads(path.read_text())
    roots,xyz,a,c=run.load_data();n=len(a)
    assert hashlib.sha256(a.tobytes()).hexdigest()==result['graph_sha256']
    split=run.STORE/'split.npz';assert run.BASE.sha(split)==result['split_sha256']
    with np.load(split,allow_pickle=False) as f:
        folds=f['folds'];assert f['roots'].tolist()==roots
    assert np.array_equal(folds,folds.T) and np.all(np.diag(folds)==-1)
    old=json.loads((run.HERE/'masked_dyad_dependence_result.json').read_text())
    transferred=float(np.mean([r['coefficients'][0] for r in old['records'] if r['model']=='constant']))
    assert transferred==result['transfer_log_odds']
    u,v=np.triu_indices(n,1);feature=np.zeros((n,n,0));maximum=0.;gradmax=0.
    for name,digest in result['receipt_sha256'].items():assert run.BASE.sha(run.STORE/name)==digest
    for fold in range(5):
        test=folds==fold;train=(folds>=0)&~test;tr=train[u,v];te=test[u,v]
        changed=a.copy();changed[test]=~changed[test];assert np.array_equal(changed&train,a&train)
        with np.load(run.STORE/f'{fold}_marginal.npz',allow_pickle=False) as f:theta=f['theta'];center=f['center'];scale=f['scale']
        ti,tj=np.nonzero(train);z=run.marginal.logits(theta,center,scale,c,feature,[],ti,tj,n)
        e=expit(z)-a[train]
        g=np.concatenate([[e.sum()],np.bincount(ti,weights=e,minlength=n),np.bincount(tj,weights=e,minlength=n),np.bincount(c[train],weights=e,minlength=6)])
        g[1:]+=theta[1:];assert abs(g).max()<=1e-5;gradmax=max(gradmax,float(abs(g).max()))
        p=expit(run.marginal.logits(theta,center,scale,c,feature,[],u,v,n));q=expit(run.marginal.logits(theta,center,scale,c,feature,[],v,u,n))
        y=2*a[u,v].astype(int)+a[v,u].astype(int)
        for model in ('independent','pinky_fitted_constant','minnie_frozen_constant'):
            r=next(r for r in result['records'] if r['model']==model and r['fold']==fold)
            fp=run.STORE/f'{fold}_{model}.npz';assert run.BASE.sha(fp)==r['fitted_sha256']
            with np.load(fp,allow_pickle=False) as f:table=f['probabilities'];coef=f['coef']
            if model=='minnie_frozen_constant':assert coef[0]==transferred and r['diagnostic']['fit_on_pinky'] is False
            eta=coef[0];odds=np.exp(eta);b=1+np.expm1(eta)*(p[te]+q[te])
            t=2*odds*p[te]*q[te]/(b+np.sqrt(b*b-4*np.expm1(eta)*odds*p[te]*q[te]))
            assert np.allclose(t,table[:,3],atol=1e-12,rtol=0)
            error=max(abs(table[:,2]+table[:,3]-p[te]).max(),abs(table[:,1]+table[:,3]-q[te]).max())
            maximum=max(maximum,float(error));assert error<1e-12
            assert np.allclose(table.sum(1),1,atol=1e-12) and (table>0).all()
            assert run.joint.metrics(table,y[te])==r['metrics']
            if model=='pinky_fitted_constant':
                _,g=run.joint.objective(coef,np.ones((tr.sum(),1)),p[tr],q[tr],y[tr]);assert abs(g).max()<=1e-5
    for model in result['summary']:
        rows=[r['metrics'] for r in result['records'] if r['model']==model]
        assert sum(r['dyads'] for r in rows)==65341 and sum(r['mutual_observed'] for r in rows)==31
        for key in ('joint_logloss','mutual_logloss','mutual_brier'):
            assert np.isclose(sum(r[key]*r['dyads'] for r in rows)/65341,result['summary'][model][key],atol=1e-12)
    output=dict(result_sha256=run.BASE.sha(path),verifier_sha256=run.BASE.sha(Path(__file__)),marginal_fits_verified=5,joint_tables_verified=15,
                fixed_minnie_coefficient_verified=True,folds_with_training_label_invariance=5,max_marginal_error=maximum,max_baseline_gradient=gradmax,
                biological_preregistered_confirmation=False)
    run.write_once(run.HERE/'pinky_dyad_prediction_verification.json',output);print(json.dumps(output))


if __name__=='__main__':main()
