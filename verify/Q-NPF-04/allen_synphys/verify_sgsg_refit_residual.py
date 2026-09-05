"""저장 확률의 여백·상호확률 합을 직접 확인하고 대표 두 적합을 재계산한다."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
import sgsg_refit_residual as run


def main():
    path=run.HERE/'sgsg_refit_residual_result.json'
    result=json.loads(path.read_text())
    assert result['failed']==0
    roots,xyz,observed,_=run.source.run.shared.source.data()
    c=np.digitize(cdist(xyz,xyz),[50,100,200,400,800])
    residuals=[];mean_values=[];r_values=[];replayed=[];max_error=0.
    for r in result['records']:
        name=f'{r["index"]:02}.json'
        receipt=run.STORE/name
        assert run.BASE.sha(receipt)==result['receipt_sha256'][name]
        assert json.loads(receipt.read_text())==r
        source_path=(run.source.STORE/name).with_suffix('.npz')
        assert run.BASE.sha(source_path)==r['input_sha256']
        with np.load(source_path,allow_pickle=False) as f:
            a=f['adjacency'];assert f['roots'].tolist()==roots
        fit_path=receipt.with_suffix('.npz')
        assert run.BASE.sha(fit_path)==r['fitted_sha256']
        with np.load(fit_path,allow_pickle=False) as f:
            p=f['p'];assert f['roots'].tolist()==roots
        assert np.isfinite(p).all() and np.all((p>=0)&(p<=1)) and not np.diag(p).any()
        errors=[abs(float(p[i,:].sum())-int(a[i,:].sum())) for i in range(len(a))]
        errors += [abs(float(p[:,i].sum())-int(a[:,i].sum())) for i in range(len(a))]
        errors += [abs(float(p[c==b].sum())-int(a[c==b].sum())) for b in range(6)]
        assert max(errors)<=1e-5
        max_error=max(max_error,max(errors))
        mean=sum(float(p[i,j]*p[j,i]) for i in range(len(a)) for j in range(i+1,len(a)))
        mutual=sum(bool(a[i,j] and a[j,i]) for i in range(len(a)) for j in range(i+1,len(a)))
        assert np.isclose(mean,r['fit_mean'],rtol=0,atol=1e-9) and mutual==r['mutual']
        assert np.isclose(mutual-mean,r['residual'],rtol=0,atol=1e-9)
        if r['index'] in (0,63):
            regenerated,diag=run.refine(a,c)
            assert diag['gate_pass'] and np.allclose(regenerated,p,rtol=0,atol=1e-7)
            replayed.append(r['index'])
        residuals.append(mutual-mean);mean_values.append(mean);r_values.append(mutual)
    comp=result['comparison']
    assert len(residuals)==64
    assert np.isclose(np.mean(residuals),comp['generated_residual_mean'],atol=1e-9)
    assert np.isclose(comp['raw_gap'],comp['fit_mean_gap']+comp['residual_gap'],atol=1e-9)
    output=dict(result_sha256=run.BASE.sha(path),verifier_sha256=run.BASE.sha(Path(__file__)),
                graphs_and_fitted_margins_verified=64,direct_pair_sums_verified=64,
                refitted_indices=replayed,max_margin_error=max_error,biological_validation=False)
    run.source.run.shared.source.write_once(run.HERE/'sgsg_refit_residual_verification.json',output)
    print(json.dumps(output))


if __name__=='__main__':main()
