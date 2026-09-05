"""이차방정식 해와 저장 주변 확률로 공동 확률 예측을 대조한다."""
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
import masked_dyad_dependence as run


def main():
    path=run.HERE/'masked_dyad_dependence_result.json'
    result=json.loads(path.read_text());assert result['summary'] is not None
    roots,xyz,a,c=run.source.source.source.run.shared.source.data();n=len(a)
    with np.load(run.source.STORE/'split.npz',allow_pickle=False) as f:folds=f['folds']
    u,v=np.triu_indices(n,1);maximum=0.;gradmax=0.;checked=0
    for fold in range(5):
        test=folds==fold;train=(folds>=0)&~test;tr=train[u,v];te=test[u,v]
        hidden=a.copy();hidden[test]=~hidden[test]
        f=run.source.features(a,train)
        assert np.array_equal(f,run.source.features(hidden,train))
        assert np.array_equal(a[train],hidden[train])
        with np.load(run.source.STORE/f'{fold}_base.npz',allow_pickle=False) as saved:
            theta=saved['theta'];mean=saved['mean'];sd=saved['scale'];saved_z=saved['heldout_logits']
        p=expit(run.source.logits(theta,mean,sd,c,f,[],u,v,n));q=expit(run.source.logits(theta,mean,sd,c,f,[],v,u,n))
        baseline=np.zeros_like(a,dtype=float);baseline[test]=expit(saved_z)
        assert np.allclose(p[te],baseline[u[te],v[te]],atol=1e-14)
        y=2*a[u,v].astype(int)+a[v,u].astype(int)
        for name,columns in run.MODELS.items():
            record=next(r for r in result['records'] if r['fold']==fold and r['model']==name)
            fp=run.STORE/f'{fold}_{name}.npz';assert run.BASE.sha(fp)==record['fitted_sha256']
            with np.load(fp,allow_pickle=False) as saved:
                coef=saved['coef'];center=saved['center'];scale=saved['scale'];table=saved['probabilities']
            raw=f[u,v][:,[] if columns is None else columns]
            assert np.allclose(center,raw[tr].mean(0),atol=1e-12)
            assert np.allclose(scale,np.where(raw[tr].std(0)>0,raw[tr].std(0),1.),atol=1e-12)
            x=np.column_stack([np.ones(len(u)),(raw-center)/scale]);eta=x[te]@coef
            odds=np.exp(eta);b=1+np.expm1(eta)*(p[te]+q[te])
            discriminant=b*b-4*np.expm1(eta)*odds*p[te]*q[te]
            t=2*odds*p[te]*q[te]/(b+np.sqrt(discriminant))
            assert np.allclose(t,table[:,3],rtol=0,atol=1e-12)
            assert (table>0).all() and np.allclose(table.sum(1),1,atol=1e-14)
            error=max(abs(table[:,2]+table[:,3]-p[te]).max(),abs(table[:,1]+table[:,3]-q[te]).max())
            maximum=max(maximum,float(error));assert error<1e-12
            assert np.allclose(np.log(table[:,3])+np.log(table[:,0])-np.log(table[:,2])-np.log(table[:,1]),eta,atol=1e-10)
            loss=-sum(np.log(table[i,state]) for i,state in enumerate(y[te]))/te.sum()
            assert abs(loss-record['metrics']['joint_logloss'])<1e-12
            if name!='independent':
                _,g=run.objective(coef,x[tr],p[tr],q[tr],y[tr]);gradmax=max(gradmax,float(abs(g).max()));assert abs(g).max()<=1e-5
            checked+=1
    for name in run.MODELS:
        rows=[r['metrics'] for r in result['records'] if r['model']==name]
        assert sum(r['dyads'] for r in rows)==60031 and sum(r['mutual_observed'] for r in rows)==221
        assert abs(sum(r['joint_logloss']*r['dyads'] for r in rows)/60031-result['summary'][name]['joint_logloss'])<1e-12
    output=dict(result_sha256=run.BASE.sha(path),verifier_sha256=run.BASE.sha(Path(__file__)),
                tables_verified=checked,quadratic_solution_matches_bisection=True,all_marginals_preserved=True,
                max_marginal_error=maximum,max_train_gradient=gradmax,folds_with_label_flip_invariance=5,
                biological_holdout=False)
    run.source.source.source.run.shared.source.write_once(run.HERE/'masked_dyad_dependence_verification.json',output)
    print(json.dumps(output))


if __name__=='__main__':main()
