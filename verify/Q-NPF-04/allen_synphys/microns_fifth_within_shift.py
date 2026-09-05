"""시행 내 성분의 회차 정렬 대조. 꼬리 비율은 검정 p값이 아니다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save
from microns_repeat_shift_control import weights

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))


def main():
    specs = [('6_2','microns_fifth_trial_level_contract.json','microns_fifth_trial_level_result.json','microns_fifth_scan_contrast_pairs.json')]
    inputs = []
    for scan,contract,result,pairs in specs:
        path = ROOT/f'data/external/microns_functional_nwb/scan_{scan}_repeated_clips.npz'
        assert sha(path)==read(contract)['input_sha256']
        inputs.append(dict(scan=scan,path=str(path),sha256=sha(path),pairs_sha256=sha(HERE/pairs),previous_result_sha256=sha(HERE/result)))
    save('microns_fifth_within_shift_contract.json',dict(
        question='Does within-trial structural covariance contribution distinguish actual repeat alignment from per-cell circular repeat shifts?',
        method='Same LOO condition-time residual, subtract each57-point trial mean. Normalize by original total residual SD products, fixed per-scan field-distance weights. 999 independent per-cell circular shifts; same shift for all conditions and within-trial samples.',
        selection='Fifth scan6/2; both timings; all10/first5/last5; all42 registered targets. All6 scenarios; no favorable selection.',
        seed=20260906,draws=999,inputs=inputs,code_sha256=sha(Path(__file__)),weights_sha256=sha(HERE/'microns_repeat_shift_control.py'),
        limits='Post-observation diagnosis. No repeat exchangeability established, no calibrated p-value, no causal interpretation. Shifts break shared state and direct coupling. Mean over all offsets zero by construction. Same animal.'))
    rng=np.random.default_rng(20260906)
    out=[]
    for scan,contract,result,pairfile in specs:
        data=np.load(ROOT/f'data/external/microns_functional_nwb/scan_{scan}_repeated_clips.npz')
        units=data['unit_ids'].tolist();lookup={u:i for i,u in enumerate(units)}
        original=read(pairfile)[0]['pairs'];prior=read(result)['results']
        subsets=[('all10',slice(None)),('first5',slice(0,5)),('last5',slice(5,10))]
        if scan=='5_3':subsets.append(('last_without10',slice(5,9)))
        for subset,selection in subsets:
            n=data['values'][0,:,selection].shape[1]
            shifts=rng.integers(0,n,size=(999,len(units)))
            for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
                x=data['values'][mode,:,selection]
                residual=x-(x.sum(axis=1,keepdims=True)-x)/(n-1)
                total=residual.reshape(-1,len(units));total=total-total.mean(axis=0)
                denominator=np.outer(np.linalg.norm(total,axis=0),np.linalg.norm(total,axis=0))
                within=residual-residual.mean(axis=2,keepdims=True)
                flat=within.reshape(total.shape)
                matrices=np.stack([flat.T@np.roll(within,k,axis=1).reshape(total.shape)/denominator for k in range(n)])
                assert np.allclose(matrices.mean(axis=0),0,atol=1e-12)
                s=shifts[0]
                explicit=np.stack([np.roll(within[:,:,:,i],int(s[i]),axis=1) for i in range(len(units))],axis=-1).reshape(total.shape)
                ii,jj=np.indices((len(units),len(units)))
                assert np.allclose(explicit.T@explicit/denominator,matrices[(s[jj]-s[ii])%n,ii,jj],atol=1e-12)
                for exclude in ((False,True) if scan=='4_7' else (False,)):
                    pairs=[p for p in original if not exclude or 3151 not in (p['unit_a'],p['unit_b'])]
                    a=np.array([lookup[p['unit_a']] for p in pairs]);b=np.array([lookup[p['unit_b']] for p in pairs])
                    _,w=weights(pairs)
                    observed=float(w@matrices[0,a,b])
                    old=next(r for r in prior if r['timing']==timing and r['subset']==subset and r.get('exclude_disputed',False)==exclude)
                    assert abs(observed-old['within_trial_component'])<1e-12
                    draws=matrices[(shifts[:,b]-shifts[:,a])%n,a,b]@w
                    out.append(dict(scan=scan,subset=subset,timing=timing,exclude_disputed=exclude,observed=observed,
                        shift_quantiles=np.quantile(draws,[.025,.5,.975]).tolist(),at_least_observed=int((draws>=observed).sum()),draws=draws.tolist()))
    save('microns_fifth_within_shift_result.json',dict(results=out,status='DESCRIPTIVE_WITHIN_TRIAL_ALIGNMENT_CONTROL',limits='Not calibrated p-values or independent animal replication.'))
    for r in out:
        if r['timing']=='positive_delay_sensitivity' and not r['exclude_disputed']:
            print({k:v for k,v in r.items() if k!='draws'})


if __name__=='__main__':
    main()
