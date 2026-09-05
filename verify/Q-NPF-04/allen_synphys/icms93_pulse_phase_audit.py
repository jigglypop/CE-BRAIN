"""정규 펄스 근사에 대한 발화 시각의 관측 범위를 검사한다."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    path=ROOT/'data/external/xie_icms_plasticity_2025/sub-ICMS93_ses-2023-10-06_behavior+ecephys+ophys.nwb'
    assert sha(path)=='843e8cfabc9d4e8c8413f3c7f3e3046f47976e83328f98c9144f1e0b26993187'
    save('icms93_pulse_phase_contract.json',dict(question='Do stored spikes exhibit a phase-specific deficit near nominal pulses consistent with processing censoring?',
        method='Approximate 70 pulses at 100Hz from each train start. Partition [-.5,9.5) ms pulse phase into 20 equal bins. Train support start-.5ms through start+699.5ms. Equal-duration pseudo-train one second before each stimulated train and catch trial-start pseudo-trains. All units and trials retained, current/good-trial labels retained.',
        assumptions='No per-pulse timestamps found in inspected dataset paths; nominal pulse grid is not measured timing. Baseline/catch phase counts diagnose recording, not exchangeable causal controls.',
        limits='No suppression estimate, p-value, exposure correction or causal conclusion. Processing provenance and sample jitter unresolved.',input_sha256=sha(path),code_sha256=sha(Path(__file__))))
    rows=[]
    with h5py.File(path,'r') as f:
        unitids=f['units/id'][:];end=f['units/spike_times_index'][:].astype(int);start=np.r_[0,end[:-1]];allspikes=f['units/spike_times'][:]
        assert end[-1]==len(allspikes) and (end>=start).all() and np.isfinite(allspikes).all()
        spikes=[allspikes[a:b] for a,b in zip(start,end)]
        assert all((np.diff(s)>=0).all() for s in spikes)
        tr=f['intervals/trials'];st=f['intervals/electrical_stimulation'];lookup={int(v):i for i,v in enumerate(st['trial_index'][:])}
        assert np.all(st['frequency_hz'][:]==100) and np.all(st['pulse_count'][:]==70)
        for i,tid in enumerate(tr['trial_index'][:]):
            current=float(tr['current_uA'][i]);j=lookup.get(int(tid));assert (j is None)==(current==0)
            anchor=float(st['start_time'][j]) if j is not None else float(tr['start_time'][i])
            modes=[('stimulated',anchor),('prestim_pseudo',anchor-1.)] if j is not None else [('catch_pseudo',anchor)]
            for mode,origin in modes:
                for uid,s in zip(unitids,spikes):
                    lower=origin-.0005;upper=lower+.7;a,b=np.searchsorted(s,[lower,upper],side='left');times=s[a:b]
                    phase=np.remainder(times-lower,.01);counts=np.histogram(phase,bins=np.linspace(0,.01,21))[0]
                    assert counts.sum()==len(times)
                    rows.append(dict(trial_index=int(tid),unit_id=int(uid),current_uA=current,is_good_trial=bool(tr['is_good_trial'][i]),mode=mode,
                        phase_counts=counts.tolist(),blank_window_count=int(counts[:4].sum()),other_window_count=int(counts[4:].sum())))
        assert len(rows)==(184*2+20)*len(unitids)
        summaries=[]
        for mode,current in sorted({(r['mode'],r['current_uA']) for r in rows}):
            rr=[r for r in rows if r['mode']==mode and r['current_uA']==current];counts=np.array([r['phase_counts'] for r in rr]).sum(axis=0)
            unit_trials=len(rr);blank_exposure=unit_trials*70*.002;other_exposure=unit_trials*70*.008
            summaries.append(dict(mode=mode,current_uA=current,unit_trials=unit_trials,phase_counts=counts.tolist(),
                blank_count=int(counts[:4].sum()),other_count=int(counts[4:].sum()),
                blank_rate_per_unit_second=float(counts[:4].sum()/blank_exposure),other_rate_per_unit_second=float(counts[4:].sum()/other_exposure)))
    save('icms93_pulse_phase_result.json',dict(results=rows,summaries=summaries,bin_edges_ms=np.linspace(-.5,9.5,21).tolist(),code_sha256=sha(Path(__file__))))
    for s in summaries:print({k:v for k,v in s.items() if k!='phase_counts'})
if __name__=='__main__':main()
