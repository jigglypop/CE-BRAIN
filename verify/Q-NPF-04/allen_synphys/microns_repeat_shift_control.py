"""회차 정렬을 깨는 순환 이동 대조. 교환가능성을 가정한 인과 검정이 아니다."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts

HERE=Path(__file__).resolve().parent


def weights(pairs):
    labels=np.array([p['linked'] for p in pairs]);simple=np.where(labels,1/labels.sum(),-1/(~labels).sum())
    groups=defaultdict(list)
    for i,p in enumerate(pairs):groups[(tuple(p['fields']),p['distance_bin'])].append(i)
    matched=np.zeros(len(pairs));total=0
    for ids in groups.values():
        a=[i for i in ids if labels[i]];b=[i for i in ids if not labels[i]]
        if a and b:
            matched[a]=1;matched[b]=-len(a)/len(b);total+=len(a)
    matched/=total
    assert abs(simple.sum())<1e-12 and abs(matched.sum())<1e-12
    return simple,matched


def main():
    path=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_clips.npz'
    receipt=json.loads((HERE/'microns_repeat_response_acquisition.json').read_text())
    assert sha(path)==receipt['artifact_sha256']
    save('microns_repeat_shift_contract.json',dict(question='Is the observed structural residual-correlation contrast dependent on keeping cells in the same recording repeat?',
        control='999 independently drawn per-cell circular shifts of repeat order, same shift across all6 conditions and all57 within-trial samples. Seed20260905. Reuse shifts for timing/exclusion sensitivities.',
        analysis='All10, first5, last5; common/positive-delay; include/exclude3151; original mean and field-distance matched contrasts.',
        limits='Descriptive misalignment control only. Repeat exchangeability/stationarity not established; circular wrap and behavioral drift matter. Tail fraction is not a calibrated p-value. Shifts disrupt all same-repeat common causes as well as direct coupling.',
        centering='Residuals sum to zero over repeats. Mean covariance over all circular offsets is algebraically zero; that null center is not independent evidence.',
        code_sha256=sha(Path(__file__)),response_sha256=sha(path)))
    data=np.load(path);units=data['unit_ids'].tolist();lookup={u:i for i,u in enumerate(units)}
    original=json.loads((HERE/'microns_structure_response_pairs.json').read_text())[0]['pairs']
    previous=json.loads((HERE/'microns_repeat_structure_result.json').read_text())['results']
    rng=np.random.default_rng(20260905);out=[];draws={}
    for subset,selection in [('all10',slice(None)),('first5',slice(0,5)),('last5',slice(5,10))]:
        n=data['values'][0,:,selection].shape[1];shifts=rng.integers(0,n,size=(999,len(units)))
        for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
            x=data['values'][mode,:,selection];residual=x-(x.sum(axis=1,keepdims=True)-x)/(n-1)
            flat=residual.reshape(-1,len(units));flat-=flat.mean(axis=0);norm=np.sqrt((flat*flat).sum(axis=0))
            matrices=np.stack([flat.T@np.roll(residual,k,axis=1).reshape(-1,len(units))/np.outer(norm,norm) for k in range(n)])
            assert np.allclose(matrices.mean(axis=0),0,atol=1e-12)
            # Verify relative-offset lookup against explicit whole-block shifts.
            s=shifts[0]
            shifted=np.stack([np.roll(residual[:,:,:,i],int(s[i]),axis=1) for i in range(len(units))],axis=-1)
            direct=np.corrcoef(shifted.reshape(-1,len(units)),rowvar=False)
            ii,jj=np.indices((len(units),len(units)))
            assert np.allclose(direct,matrices[(s[jj]-s[ii])%n,ii,jj],atol=1e-12)
            for exclude in (False,True):
                pairs=[p for p in original if not exclude or 3151 not in (p['unit_a'],p['unit_b'])]
                a=np.array([lookup[p['unit_a']] for p in pairs]);b=np.array([lookup[p['unit_b']] for p in pairs])
                simple,matched=weights(pairs);observed=matrices[0,a,b]
                old=next(r for r in previous if r['timing']==timing and r['repeat_subset']==subset and r['component']=='leave_one_repeat_out_residual' and r['exclude_disputed']==exclude)
                assert np.isclose(observed@matched,old['matched_mean_difference'],rtol=0,atol=1e-12)
                values=matrices[(shifts[:,b]-shifts[:,a])%n,a,b]
                summaries={}
                for name,w in [('mean_difference',simple),('matched_mean_difference',matched)]:
                    null=values@w;actual=float(observed@w)
                    summaries[name]=dict(observed=actual,shift_mean=float(null.mean()),shift_quantiles=np.quantile(null,[.025,.5,.975]).tolist(),at_least_observed=int((null>=actual).sum()),draws=999,tail_fraction=float((null>=actual).mean()))
                    draws[f'{subset}_{mode}_{int(exclude)}_{name}']=null
                out.append(dict(repeat_subset=subset,timing=timing,exclude_disputed=exclude,**summaries))
    dest=HERE/'microns_repeat_shift_draws.npz'
    if not dest.exists():
        with dest.open('xb') as f:np.savez_compressed(f,**draws)
    save('microns_repeat_shift_result.json',dict(results=out,draws_sha256=sha(dest),status='DESCRIPTIVE_REPEAT_ALIGNMENT_CONTROL',limits='Not an experimental randomization p-value or synaptic causal identification.'))
    for r in out:
        if r['timing']=='positive_delay_sensitivity' and not r['exclude_disputed']:print(r['repeat_subset'],r['matched_mean_difference'])


if __name__=='__main__':main()
