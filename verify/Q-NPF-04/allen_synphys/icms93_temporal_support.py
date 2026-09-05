"""ICMS93 영상 유효 구간과 자극·행동 표의 시각 대응을 조사한다."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    base=ROOT/'data/external/xie_icms_plasticity_2025'
    path=base/'sub-ICMS93_ses-2023-10-06_behavior+ecephys+ophys.nwb'
    meta=json.loads((base/'dandi_001868_schema_candidate_asset.json').read_text(encoding='utf-8'))
    assert sha(path)==meta['digest']['dandi:sha2-256']
    save('icms93_temporal_support_contract.json',dict(question='Which actual imaging samples overlap stimulation/catch events on the provided master clock?',
        method='Read all imaging values for finite-mask audit only; retain contiguous valid blocks. Join electrical stimulation by trial_index, not row number. Stim trials anchored at stimulation start and zero-current trials at trial start, as file description states. Count full-ROI finite samples in [-1,0), [0,.7), [.7,1.4) diagnostic windows without imposing eligibility thresholds.',
        limits='Input QC only; no neural-effect estimate. Windows are diagnostic, not a preregistered biological endpoint. Nominal plane rate does not establish per-ROI acquisition timing or independent samples.',code_sha256=sha(Path(__file__)),input_sha256=sha(path)))
    with h5py.File(path,'r') as f:
        group=f['processing/ophys/DfOverF/DfOverF_Volumetric'];data=group['data'][:];finite=np.isfinite(data)
        rate=float(group['starting_time'].attrs['rate']);start=float(group['starting_time'][()]);t=start+np.arange(len(data))/rate
        counts=finite.sum(axis=1);full=counts==data.shape[1];anyvalid=counts>0
        change=np.diff(np.r_[False,full,False].astype(int));beg=np.flatnonzero(change==1);end=np.flatnonzero(change==-1)
        blocks=[dict(start_frame=int(a),stop_frame_exclusive=int(b),samples=int(b-a),first_time=float(t[a]),last_time=float(t[b-1])) for a,b in zip(beg,end)]
        assert sum(b['samples'] for b in blocks)==int(full.sum())
        trials=f['intervals/trials'];stim=f['intervals/electrical_stimulation'];ids=trials['trial_index'][:];sids=stim['trial_index'][:]
        assert len(set(ids.tolist()))==len(ids) and len(set(sids.tolist()))==len(sids)
        lookup={int(v):i for i,v in enumerate(sids)};assert set(lookup)<=set(ids.tolist())
        rows=[]
        for i,index in enumerate(ids):
            current=float(trials['current_uA'][i]);j=lookup.get(int(index));assert (j is None)==(current==0)
            if j is not None:
                assert current==float(stim['current_uA'][j]) and trials['stim_channel'][i]==stim['stim_channel'][j]
            anchor=float(stim['start_time'][j]) if j is not None else float(trials['start_time'][i])
            windows=[]
            for lo,hi in [(-1.,0.),(0.,.7),(.7,1.4)]:
                mask=(t>=anchor+lo)&(t<anchor+hi);ix=np.flatnonzero(mask&full)
                windows.append(dict(relative_interval=[lo,hi],nominal_samples=int(mask.sum()),full_roi_samples=len(ix),
                    first_relative=float(t[ix[0]]-anchor) if len(ix) else None,last_relative=float(t[ix[-1]]-anchor) if len(ix) else None))
            rows.append(dict(trial_index=int(index),current_uA=current,is_good_trial=bool(trials['is_good_trial'][i]),anchor=anchor,
                trial_start=float(trials['start_time'][i]),trial_stop=float(trials['stop_time'][i]),
                stim_stop=float(stim['stop_time'][j]) if j is not None else None,windows=windows))
        summary=[]
        for current in sorted({r['current_uA'] for r in rows}):
            rr=[r for r in rows if r['current_uA']==current]
            summary.append(dict(current_uA=current,trials=len(rr),good=sum(r['is_good_trial'] for r in rr),
                windows=[dict(interval=rr[0]['windows'][k]['relative_interval'],zero_samples=sum(r['windows'][k]['full_roi_samples']==0 for r in rr),
                    count_range=[min(r['windows'][k]['full_roi_samples'] for r in rr),max(r['windows'][k]['full_roi_samples'] for r in rr)]) for k in range(3)]))
        result=dict(input_sha256=sha(path),code_sha256=sha(Path(__file__)),imaging_shape=list(data.shape),rate=rate,
            finite_values=int(finite.sum()),nan_values=int(np.isnan(data).sum()),infinite_values=int(np.isinf(data).sum()),
            fully_finite_rows=int(full.sum()),partly_finite_rows=int((anyvalid&~full).sum()),all_invalid_rows=int((~anyvalid).sum()),
            finite_count_per_roi_range=[int(finite.sum(axis=0).min()),int(finite.sum(axis=0).max())],
            description=str(group.attrs['description']),blocks=blocks,trials=rows,current_summary=summary,
            stim_duration_range=[float(np.min(stim['stop_time'][:]-stim['start_time'][:])),float(np.max(stim['stop_time'][:]-stim['start_time'][:]))],
            trial_stop_before_stim_stop=sum(r['stim_stop'] is not None and r['trial_stop']<r['stim_stop'] for r in rows))
    save('icms93_temporal_support_result.json',result)
    print({k:v for k,v in result.items() if k not in ('blocks','trials','current_summary','description')});print('blocks',len(blocks));print(summary)
if __name__=='__main__':main()
