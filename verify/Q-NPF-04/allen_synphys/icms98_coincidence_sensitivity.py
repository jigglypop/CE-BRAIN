"""고정 catch PC에 대한 근접 사건 제외의 기술적 민감도."""
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
    p=ROOT/'data/external/xie_icms_plasticity_2025/sub-ICMS98_ses-2023-10-24_behavior+ecephys+ophys.nwb';c=read('icms98_catch_boundary_comparison_contract.json');assert sha(p)==c['input_sha256']
    save('icms98_coincidence_sensitivity_contract.json',dict(code_sha256=sha(Path(__file__)),input_sha256=c['input_sha256'],parent_sha256=sha(HERE/'icms98_catch_boundary_comparison_result.json'),
        method='Reuse36 fixed catch windows and prior interior triggers, all21 units and same13 eligibility. Remove other-unit events whose nearest target-unit event in the same500ms window is within0/3/15 samples at30kHz. Keep target triggers fixed. Smooth per trial sigma10bins truncate4, subtract each retained population global mean. Also compute removed-event contribution; verify retained+removed=original PC.',
        limits='Target-dependent censoring removes true synchrony too. Not duplicate correction, causal effect or independent significance test. No source modification.'))
    prior=read('icms98_next_session_result.json');old={r['unit']:r for r in read('icms98_catch_boundary_comparison_result.json')['units']}
    with h5py.File(p,'r') as f:
        tr=f['intervals/trials'];lookup={int(t):i for i,t in enumerate(tr['trial_index'][:])};uids=f['units/id'][:];sp=f['units/spike_times'][:];ends=f['units/spike_times_index'][:].astype(int)
        trains=[sp[a:b] for a,b in zip(np.r_[0,ends[:-1]],ends)];events=[];bins=[]
        for row in prior['trials']:
            start=float(tr['start_time'][lookup[row['trial_id']]])+.8;ev=[];bi=[]
            for s in trains:
                a,b=np.searchsorted(s,[start,start+.5]);v=s[a:b];ix=np.floor((v-start)/.001).astype(int);assert ((ix>=0)&(ix<500)).all()
                ev.append(np.rint(v*30000).astype(np.int64));bi.append(ix)
            events.append(ev);bins.append(bi)
    results=[]
    for u,uid in enumerate(uids):
        weights=np.array([np.bincount(b[u],minlength=500) for b in bins]);weights[:,:100]=0;weights[:,400:]=0;n=int(weights.sum());assert n==old[int(uid)]['interior_trigger_spikes']
        if not n:continue
        variants=[]
        for tol in (0,3,15):
            kept=np.zeros((36,500));removed=np.zeros((36,500))
            for t in range(36):
                for v in range(len(uids)):
                    if v==u:continue
                    near=nearest(events[t][v],events[t][u])<=tol
                    kept[t]+=np.bincount(bins[t][v][~near],minlength=500)
                    removed[t]+=np.bincount(bins[t][v][near],minlength=500)
            def pc(counts):
                rate=counts/.001;smooth=gaussian_filter1d(rate,10,axis=1,truncate=4,mode='nearest')
                return float(np.sum(weights*(smooth-rate.mean()))/n)
            kp,rp=pc(kept),pc(removed);original=old[int(uid)]['pc_trialwise_same_interior']
            assert abs(kp+rp-original)<1e-9
            variants.append(dict(tolerance_samples=tol,retained_pc=kp,removed_pc=rp,removed_events=int(removed.sum()),original_other_events=int((kept+removed).sum())))
        results.append(dict(unit=int(uid),eligible=old[int(uid)]['eligible'],original_pc=old[int(uid)]['pc_trialwise_same_interior'],interior_triggers=n,variants=variants))
    eligible=[r for r in results if r['eligible']];summary=[]
    for k,tol in enumerate((0,3,15)):
        summary.append(dict(tolerance_samples=tol,positive_units=sum(r['variants'][k]['retained_pc']>0 for r in eligible),negative_units=sum(r['variants'][k]['retained_pc']<0 for r in eligible),median_retained_pc=float(np.median([r['variants'][k]['retained_pc'] for r in eligible])),median_removed_pc=float(np.median([r['variants'][k]['removed_pc'] for r in eligible]))))
    save('icms98_coincidence_sensitivity_result.json',dict(units=results,summary=summary))
    print(summary)
if __name__=='__main__':main()
