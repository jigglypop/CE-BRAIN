"""실제 catch의 고정500ms 창: 연결 경계와 trigger 선택의 분리."""
import json
from pathlib import Path
import h5py
import numpy as np
from scipy.ndimage import gaussian_filter1d
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    prior=HERE/'icms98_next_session_result.json';data=json.loads(prior.read_text(encoding='utf-8'))
    p=ROOT/'data/external/xie_icms_plasticity_2025/sub-ICMS98_ses-2023-10-24_behavior+ecephys+ophys.nwb'
    expected=json.loads((HERE/'icms98_next_session_execution_contract.json').read_text(encoding='utf-8'))['input_sha256'];assert sha(p)==expected
    save('icms98_catch_boundary_comparison_contract.json',dict(code_sha256=sha(Path(__file__)),input_sha256=expected,selection_sha256=sha(prior),
        selection='Reuse36 geometry-valid no-response good catches from original next-session analysis; trial-start+0.8 to+1.3 seconds.',
        method='All21 units; fixed500 one-ms bins per trial, count spikes. Exclude target from population sum, smooth sigma10bins truncate4. Compare concatenated all eligible triggers; same concatenated signal using only trial-interior triggers; per-trial smoothed signal with identical interior triggers. Full-window mean centering. Require >=50 interior trigger spikes for descriptive direction counts. Fixed duration, not last-spike-derived duration.',
        boundary='New exploratory measurement sensitivity on task catches, not reproduction of passive source estimator. Internal trigger bin range100..399; endpoint PC at zero lag. No shuffle significance or causal claim.'))
    with h5py.File(p,'r') as f:
        tr=f['intervals/trials'];lookup={int(t):i for i,t in enumerate(tr['trial_index'][:])}
        starts=np.array([float(tr['start_time'][lookup[r['trial_id']]])+.8 for r in data['trials']]);assert len(starts)==36
        allsp=f['units/spike_times'][:];ends=f['units/spike_times_index'][:].astype(int);uids=f['units/id'][:]
        trains=[allsp[a:b] for a,b in zip(np.r_[0,ends[:-1]],ends)]
        counts=np.zeros((36,len(uids),500),dtype=int)
        for t,start in enumerate(starts):
            for u,sp in enumerate(trains):
                lo,hi=np.searchsorted(sp,[start,start+.5]);rel=sp[lo:hi]-start
                bins=np.floor(rel/.001).astype(int);assert ((bins>=0)&(bins<500)).all()
                counts[t,u]=np.bincount(bins,minlength=500)
    total=counts.sum(axis=1);rows=[];interior=np.zeros((36,500),bool);interior[:,100:400]=True
    overall=np.ones(36*500,bool);overall[:100]=False;overall[-100:]=False
    for u,uid in enumerate(uids):
        target=counts[:,u];population=(total-target)/.001
        concat=gaussian_filter1d(population.ravel(),10,truncate=4,mode='nearest').reshape(36,500)
        separate=gaussian_filter1d(population,10,axis=1,truncate=4,mode='nearest')
        # Center both by same unsmoothed population mean to isolate boundary filtering.
        center=float(population.mean());concat-=center;separate-=center
        allweights=target.ravel()*overall;weights=target*interior
        nall=int(allweights.sum());n=int(weights.sum())
        pc_all=float(np.sum(concat.ravel()*allweights)/nall) if nall else None
        pc_common=float(np.sum(concat*weights)/n) if n else None
        pc_trial=float(np.sum(separate*weights)/n) if n else None
        if n:assert np.allclose(concat[interior],separate[interior],rtol=1e-12,atol=1e-12)
        rows.append(dict(unit=int(uid),all_trigger_spikes=nall,interior_trigger_spikes=n,excluded_join_trigger_spikes=nall-n,
            pc_concatenated_all=pc_all,pc_concatenated_same_interior=pc_common,pc_trialwise_same_interior=pc_trial,eligible=n>=50))
    eligible=[r for r in rows if r['eligible']]
    flips=[r['unit'] for r in eligible if np.sign(r['pc_concatenated_all'])!=np.sign(r['pc_trialwise_same_interior'])]
    save('icms98_catch_boundary_comparison_result.json',dict(trial_ids=[r['trial_id'] for r in data['trials']],units=rows,eligible_units=len(eligible),direction_changed_units=flips,
        limits='Changes all-versus-interior combine trigger selection and boundary effects; identical-interior smoothing check isolates direct filter leakage. Data-driven event selection unchanged; no independent cell inference.'))
    print('eligible',len(eligible),'direction_changed',flips)
    for r in rows:print(r)
if __name__=='__main__':main()
