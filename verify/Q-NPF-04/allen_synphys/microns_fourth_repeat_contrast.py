"""추가 스캔에도 동일한 반복 분리와 회차 이동 대조를 적용한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts
from microns_repeat_shift_control import weights

HERE=Path(__file__).resolve().parent


def main():
    path=ROOT/'data/external/microns_functional_nwb/scan_5_7_repeated_clips.npz'
    receipt=json.loads((HERE/'microns_fourth_repeats_acquisition.json').read_text());assert sha(path)==receipt['artifact_sha256']
    data=np.load(path);units=data['unit_ids'].tolist();lookup={u:i for i,u in enumerate(units)}
    pairs=json.loads((HERE/'microns_fourth_scan_contrast_pairs.json').read_text())[0]['pairs'];a=np.array([lookup[p['unit_a']] for p in pairs]);b=np.array([lookup[p['unit_b']] for p in pairs]);simple,matched=weights(pairs)
    results=[];controls=[];rng=np.random.default_rng(20260905);draws={}
    for subset,sel in [('all10',slice(None)),('first5',slice(0,5)),('last5',slice(5,10))]:
        n=data['values'][0,:,sel].shape[1];shifts=rng.integers(0,n,size=(999,len(units)))
        for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
            x=data['values'][mode,:,sel];residual=x-(x.sum(axis=1,keepdims=True)-x)/(n-1);assert np.allclose(residual.sum(axis=1),0,atol=1e-8)
            for name,y in [('raw',x),('repeat_mean',x.mean(axis=1)),('leave_one_repeat_out_residual',residual)]:
                flat=y.reshape(-1,len(units));assert np.isfinite(flat).all() and (flat.std(axis=0)>0).all()
                corr=np.corrcoef(flat,rowvar=False);pp=[dict(p,correlation=float(corr[a[i],b[i]])) for i,p in enumerate(pairs)]
                results.append(dict(repeat_subset=subset,timing=timing,component=name,rows=len(flat),**contrasts(pp)))
            flat=residual.reshape(-1,len(units));norm=np.sqrt((flat*flat).sum(axis=0))
            matrices=np.stack([flat.T@np.roll(residual,k,axis=1).reshape(-1,len(units))/np.outer(norm,norm) for k in range(n)])
            assert np.allclose(matrices.mean(axis=0),0,atol=1e-12)
            corr=np.corrcoef(flat,rowvar=False);assert np.allclose(corr,matrices[0],atol=1e-12)
            s=shifts[0];shifted=np.stack([np.roll(residual[:,:,:,i],int(s[i]),axis=1) for i in range(len(units))],axis=-1)
            direct=np.corrcoef(shifted.reshape(-1,len(units)),rowvar=False)
            ii,jj=np.indices((len(units),len(units)));assert np.allclose(direct,matrices[(s[jj]-s[ii])%n,ii,jj],atol=1e-12)
            v=matrices[(shifts[:,b]-shifts[:,a])%n,a,b];obs=float(matrices[0,a,b]@matched);null=v@matched
            draws[f'{subset}_{mode}']=null
            controls.append(dict(repeat_subset=subset,timing=timing,observed=obs,shift_quantiles=np.quantile(null,[.025,.5,.975]).tolist(),at_least_observed=int((null>=obs).sum()),draws=999,limits='Descriptive shift control, not calibrated p-value or causal inference.'))
    output=HERE/'microns_fourth_repeat_shift_draws.npz'
    if not output.exists():
        with output.open('xb') as f:np.savez_compressed(f,**draws)
    save('microns_fourth_repeat_contrast_result.json',dict(results=results,controls=controls,code_sha256=sha(Path(__file__)),draws_sha256=sha(output),artifact_sha256=sha(path),limits='Same animal, nonoverlapping registered nuclei. Historical registration uncertainty and common inputs remain. No behavior correction.'))
    for r in results:
        if r['timing']=='positive_delay_sensitivity':print(r['repeat_subset'],r['component'],r['matched_mean_difference'])
    for r in controls:
        if r['timing']=='positive_delay_sensitivity':print('CONTROL',r)


if __name__=='__main__':main()
