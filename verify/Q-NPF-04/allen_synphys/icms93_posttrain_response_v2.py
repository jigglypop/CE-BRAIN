"""펄스열과 떨어진 고정 전후 구간의 탐색적 발화 비교."""
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
    save('icms93_posttrain_v2_contract.json',dict(revision='v2 computes mean paired differences directly so catch minus itself is exactly zero; v1 floating point cancellation produced spurious signs near zero. Windows and selection unchanged.',question='In this exploratory session, how does post-train stored firing differ from prestimulus firing and the same nominal catch windows?',
        windows=dict(pre=[-.7,-.2],post=[.8,1.3]),anchor='Stim onset for stimulated trials, trial start for catch. Post begins100ms after nominal700ms train. Half-open intervals.',
        selection='All33 units; retain all trials and quality labels. Primary uses is_good_trial and geometry-pass, all-quality sensitivity also reported. Geometry-pass requires both windows inside provided session duration proxy and zero overlap with any electrical train. No outcome-based selection.',
        analysis='Count spikes in both500ms windows. Per-unit post-minus-pre Hz averaged across trials within each current, subtract per-unit catch mean difference, then equal-weight units for descriptive summary. No pooled-unit p-value.',
        limits='Single session previously inspected; exploratory not confirmation. Wheel stream duration is only a session coverage proxy; continuous per-unit detection not proven. Catch assignment/randomization and movement confounding unverified. Stored spikes are processed; post-train artifacts or adaptation remain possible.',
        code_sha256=sha(Path(__file__)),input_sha256=sha(path)))
    with h5py.File(path,'r') as f:
        tr=f['intervals/trials'];st=f['intervals/electrical_stimulation'];ids=tr['trial_index'][:];sids=st['trial_index'][:];lookup={int(k):i for i,k in enumerate(sids)}
        starts=st['start_time'][:];stops=st['stop_time'][:]
        wheel=f['processing/behavior/wheel/wheel_position_processed'];lower=float(wheel['starting_time'][()]);upper=lower+len(wheel['data'])/float(wheel['starting_time'].attrs['rate'])
        units=f['units/id'][:];ends=f['units/spike_times_index'][:].astype(int);begs=np.r_[0,ends[:-1]];sp=f['units/spike_times'][:]
        assert ends[-1]==len(sp) and np.isfinite(sp).all()
        trains=[sp[a:b] for a,b in zip(begs,ends)];assert all(np.all(np.diff(s)>=0) for s in trains)
        counts=np.zeros((len(ids),len(units),2),dtype=int);rows=[]
        for i,tid in enumerate(ids):
            j=lookup.get(int(tid));current=float(tr['current_uA'][i]);assert (j is None)==(current==0)
            anchor=float(starts[j]) if j is not None else float(tr['start_time'][i]);windows=[]
            for wi,(lo,hi) in enumerate([(-.7,-.2),(.8,1.3)]):
                a,b=anchor+lo,anchor+hi;overlap=np.flatnonzero((starts<b)&(stops>a))
                for u,s in enumerate(trains):
                    ia,ib=np.searchsorted(s,[a,b],side='left');counts[i,u,wi]=ib-ia
                windows.append(dict(start=a,stop=b,inside_session_proxy=bool(a>=lower and b<=upper),overlapping_stim_trial_ids=[int(sids[k]) for k in overlap]))
            rows.append(dict(trial_index=int(tid),current_uA=current,is_good_trial=bool(tr['is_good_trial'][i]),is_hit=bool(tr['is_hit'][i]),anchor=anchor,
                geometry_pass=all(w['inside_session_proxy'] and not w['overlapping_stim_trial_ids'] for w in windows),windows=windows))
        deltas=(counts[:,:,1]-counts[:,:,0])/.5;summaries=[];perunit=[]
        for quality in ('good_only','all_quality'):
            eligible=np.array([r['geometry_pass'] and (quality=='all_quality' or r['is_good_trial']) for r in rows]);currents=np.array([r['current_uA'] for r in rows]);catch=eligible&(currents==0);assert catch.any()
            cdelta=deltas[catch].mean(axis=0)
            for current in sorted(set(currents)):
                mask=eligible&(currents==current);assert mask.any();pre=counts[mask,:,0].mean(axis=0)/.5;post=counts[mask,:,1].mean(axis=0)/.5;delta=deltas[mask].mean(axis=0);contrast=delta-cdelta
                assert np.allclose(delta,deltas[mask].mean(axis=0),atol=1e-12)
                summaries.append(dict(quality=quality,current_uA=float(current),trials=int(mask.sum()),mean_pre_hz=float(pre.mean()),mean_post_hz=float(post.mean()),
                    mean_delta_hz=float(delta.mean()),mean_catch_adjusted_delta_hz=float(contrast.mean()),positive_units=int((contrast>0).sum()),negative_units=int((contrast<0).sum())))
                for i,u in enumerate(units):perunit.append(dict(quality=quality,current_uA=float(current),unit_id=int(u),pre_hz=float(pre[i]),post_hz=float(post[i]),delta_hz=float(delta[i]),catch_adjusted_delta_hz=float(contrast[i])))
    dest=HERE/'icms93_posttrain_v2_counts.npz'
    arrays=dict(counts=counts,trial_ids=ids,unit_ids=units)
    if not dest.exists():
        with dest.open('xb') as out:np.savez_compressed(out,**arrays)
    else:
        with np.load(dest) as a:assert all(np.array_equal(a[k],v) for k,v in arrays.items())
    save('icms93_posttrain_v2_result.json',dict(trials=rows,per_unit=perunit,summaries=summaries,session_proxy=[lower,upper],geometry_failures=sum(not r['geometry_pass'] for r in rows),counts_sha256=sha(dest),code_sha256=sha(Path(__file__))))
    print('geometry failures',sum(not r['geometry_pass'] for r in rows))
    for s in summaries:print(s)
if __name__=='__main__':main()
