"""기존 ICMS100/101 세션에 고정 경계·근접제외 PC를 적용."""
import json
from pathlib import Path
import h5py
import numpy as np
from scipy.ndimage import gaussian_filter1d
from icms98_unit_overlap import nearest
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_text(encoding='utf-8'))
def main():
    dates={'ICMS100':'2023-10-26','ICMS101':'2023-10-27'};base=ROOT/'data/external/xie_icms_plasticity_2025'
    save('icms_coupling_other_animals_contract.json',dict(code_sha256=sha(Path(__file__)),subjects=dates,
        inputs={s:read(s.lower()+'_external_execution_contract.json')['input_sha256'] for s in dates},
        method='All first-session trials from original fixed external files. Good catch with neither hit nor finite response_time; pre[-.7,-.2),post[.8,1.3) relative trialstart must fit wheel range and avoid every actual electrical train. Post500ms bins1ms; separate Gaussian10ms truncate4; fixed interior100:400 target spikes. Target excluded from population. Compare original PC and PC after removing other-unit events within15 samples of any target spike in same postwindow. Same definition and mean centering as ICMS98.',
        gate='At least2 units with>=50 interior spikes per subject; otherwise UNASSESSED. All eligible censored PCs strictly positive -> DIRECTION_SUPPORTED; any nonpositive -> DIRECTION_FAILED.',
        limits='Other animals, but previously explored datasets; transfer check not blinded confirmatory test. Positive PC is coactivity not direct neural connection. No unit merging.'))
    outputs=[]
    for subject,date in dates.items():
        p=base/f'sub-{subject}_ses-{date}_behavior+ecephys+ophys.nwb';assert sha(p)==read(subject.lower()+'_external_execution_contract.json')['input_sha256']
        with h5py.File(p,'r') as f:
            tr=f['intervals/trials'];st=f['intervals/electrical_stimulation'];ss=st['start_time'][:];se=st['stop_time'][:]
            wg=f['processing/behavior/wheel/wheel_position_processed'];lo=float(wg['starting_time'][()]);hi=lo+len(wg['data'])/float(wg['starting_time'].attrs['rate'])
            sp=f['units/spike_times'][:];ends=f['units/spike_times_index'][:].astype(int);ids=f['units/id'][:]
            assert np.isfinite(sp).all() and ends[-1]==len(sp) and np.max(abs(sp*30000-np.rint(sp*30000)))<1e-5
            trains=[sp[a:b] for a,b in zip(np.r_[0,ends[:-1]],ends)];events=[];bins=[];selected=[];rejected=[]
            for i in range(len(tr['id'])):
                if tr['current_uA'][i]!=0 or not tr['is_good_trial'][i] or tr['is_hit'][i] or np.isfinite(tr['response_time'][i]):continue
                start=float(tr['start_time'][i]);windows=[(start-.7,start-.2),(start+.8,start+1.3)]
                if not all(a>=lo and b<=hi and not np.any((ss<b)&(se>a)) for a,b in windows):rejected.append(int(tr['trial_index'][i]));continue
                selected.append(int(tr['trial_index'][i]));ev=[];bi=[];start+=.8
                for s in trains:
                    a,b=np.searchsorted(s,[start,start+.5]);v=s[a:b];ix=np.floor((v-start)/.001).astype(int);assert ((ix>=0)&(ix<500)).all()
                    ev.append(np.rint(v*30000).astype(np.int64));bi.append(ix)
                events.append(ev);bins.append(bi)
        rows=[]
        for u,uid in enumerate(ids):
            weights=np.array([np.bincount(b[u],minlength=500) for b in bins]);weights[:,:100]=0;weights[:,400:]=0;n=int(weights.sum())
            if not n:rows.append(dict(unit=int(uid),eligible=False,interior_spikes=0));continue
            original=np.zeros((len(bins),500));removed=np.zeros_like(original)
            for t in range(len(bins)):
                for v in range(len(ids)):
                    if u==v:continue
                    original[t]+=np.bincount(bins[t][v],minlength=500)
                    match=nearest(events[t][v],events[t][u])<=15
                    removed[t]+=np.bincount(bins[t][v][match],minlength=500)
            def pc(a):
                rate=a/.001;sm=gaussian_filter1d(rate,10,axis=1,truncate=4,mode='nearest')
                return float(np.sum(weights*(sm-rate.mean()))/n)
            raw=pc(original);rem=pc(removed);kept=pc(original-removed);assert abs(raw-rem-kept)<1e-9
            rows.append(dict(unit=int(uid),eligible=n>=50,interior_spikes=n,original_pc=raw,removed_pc=rem,retained_pc=kept,removed_events=int(removed.sum()),other_events=int(original.sum())))
        eligible=[r for r in rows if r['eligible']];nonpositive=[r['unit'] for r in eligible if r['retained_pc']<=0]
        result=dict(subject=subject,trials=selected,geometry_rejected=rejected,units=rows,eligible_units=len(eligible),nonpositive_units=nonpositive,
            status='UNASSESSED' if len(eligible)<2 else ('DIRECTION_FAILED' if nonpositive else 'DIRECTION_SUPPORTED'),
            median_retained_pc=float(np.median([r['retained_pc'] for r in eligible])) if eligible else None)
        outputs.append(result);print({k:v for k,v in result.items() if k not in ('units','trials')},'catch',len(selected))
    save('icms_coupling_other_animals_result.json',dict(subjects=outputs))
if __name__=='__main__':main()
