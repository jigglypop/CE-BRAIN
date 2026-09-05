"""마스킹 누출 공격, 독립 특징·기울기·평가 재계산 및 대표 재적합."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
import masked_neighbor_prediction_polished as run


def main():
    result_path=run.HERE/'masked_neighbor_prediction_polished_result.json'
    result=json.loads(result_path.read_text());assert result['all_fits_pass']
    roots,xyz,a,c=run.source.source.run.shared.source.data();n=len(a)
    assert hashlib.sha256(a.tobytes()).hexdigest()==result['graph_sha256']
    split_path=run.STORE/'split.npz';assert run.BASE.sha(split_path)==result['split_sha256']
    with np.load(split_path,allow_pickle=False) as f:
        folds=f['folds'];assert f['roots'].tolist()==roots
    assert np.array_equal(folds,folds.T) and np.all(np.diag(folds)==-1)
    all_predictions={name:np.full(a.shape,np.nan) for name in run.MODELS}
    maximum=0.;checked=0
    for fold in range(5):
        test=folds==fold;train=(folds>=0)&~test;training=a&train
        changed=a.copy();changed[test]=~changed[test]
        assert np.array_equal(training,changed&train)
        features=run.features(a,train)
        assert np.array_equal(features,run.features(changed,train))
        # Independent bitset counts on every unordered pair.
        bits_in=[int.from_bytes(np.packbits(row,bitorder='little').tobytes(),'little') for row in training.T]
        bits_out=[int.from_bytes(np.packbits(row,bitorder='little').tobytes(),'little') for row in training]
        for i in range(n):
            for j in range(i+1,n):
                assert features[i,j,0]==np.log1p((bits_in[i]&bits_in[j]).bit_count())
                assert features[i,j,1]==np.log1p((bits_out[i]&bits_out[j]).bit_count())
        u,v=np.nonzero(train);ii,jj=np.nonzero(test);y=training[u,v].astype(float)
        for name,columns in run.MODELS.items():
            path=run.STORE/f'{fold}_{name}.npz'
            record=next(r for r in result['records'] if r['fold']==fold and r['model']==name)
            assert run.BASE.sha(path)==record['fitted_sha256']
            with np.load(path,allow_pickle=False) as f:
                theta=f['theta'];mean=f['mean'];scale=f['scale'];pred=f['heldout_logits']
            raw=features[u,v][:,columns]
            assert np.allclose(raw.mean(0),mean,rtol=0,atol=1e-12)
            assert np.allclose(np.where(raw.std(0)>0,raw.std(0),1),scale,rtol=0,atol=1e-12)
            x=(raw-mean)/scale
            z=theta[0]+theta[1+u]+theta[1+n+v]+theta[1+2*n+c[u,v]]+x@theta[1+2*n+6:]
            e=expit(z)-y
            grad=np.concatenate([[e.sum()],np.bincount(u,weights=e,minlength=n),np.bincount(v,weights=e,minlength=n),np.bincount(c[u,v],weights=e,minlength=6),x.T@e])
            grad[1:]+=theta[1:];maximum=max(maximum,float(abs(grad).max()));assert abs(grad).max()<=1e-5
            predicted=run.logits(theta,mean,scale,c,features,columns,ii,jj,n)
            assert np.allclose(pred,predicted,rtol=0,atol=1e-12)
            full=np.zeros(a.shape);full[test]=pred
            assert run.metrics(a,test,full)==record['metrics']
            all_predictions[name][test]=pred
            if fold==0 and name=='both':
                new,_,_,diag=run.fit(training,train,c,features,columns)
                assert diag['gate_pass'] and np.allclose(new,theta,rtol=0,atol=1e-7)
            checked+=1
    for name,z in all_predictions.items():
        assert np.isfinite(z[folds>=0]).all()
        combined=run.metrics(a,folds>=0,z)
        for key in ('direction_logloss','direction_brier','mutual_logloss','mutual_brier','mutual_predicted_sum'):
            assert np.isclose(combined[key],result['summary'][name][key],rtol=0,atol=1e-10)
    output=dict(result_sha256=run.BASE.sha(result_path),verifier_sha256=run.BASE.sha(Path(__file__)),
                fits_verified=checked,folds_with_heldout_label_flip_invariance=5,
                all_pair_bitset_feature_check=True,all_heldout_predictions_covered_once=True,
                representative_refit='fold0both',max_gradient=maximum,biological_holdout=False)
    run.source.source.run.shared.source.write_once(run.HERE/'masked_neighbor_prediction_verification.json',output)
    print(json.dumps(output))


if __name__=='__main__':main()
