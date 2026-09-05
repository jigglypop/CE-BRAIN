"""Unit 간 발화 시각 중복과 평균 파형의 탐색적 품질 점검."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def nearest(a,b):
    if not len(a) or not len(b):return np.full(len(a),np.iinfo(np.int64).max,dtype=np.int64)
    i=np.searchsorted(b,a);left=np.abs(a-b[np.clip(i-1,0,len(b)-1)]);right=np.abs(a-b[np.clip(i,0,len(b)-1)])
    return np.minimum(left,right)
def main():
    p=ROOT/'data/external/xie_icms_plasticity_2025/sub-ICMS98_ses-2023-10-24_behavior+ecephys+ophys.nwb';prior=HERE/'icms98_next_session_result.json'
    expected=json.loads((HERE/'icms98_next_session_execution_contract.json').read_text(encoding='utf-8'))['input_sha256'];assert sha(p)==expected
    save('icms98_unit_overlap_contract.json',dict(code_sha256=sha(Path(__file__)),input_sha256=expected,selection_sha256=sha(prior),
        method='All21 units and all210 pairs. Convert times to nearest recorded30kHz sample, verify deviation <=1e-5 sample. Count directed fraction with nearest other-unit event at0, <=3 and <=15 samples for full stored session and fixed36 catch post500ms windows. Same-event duplicates within a unit and ISI<1ms reported separately. Mean90-sample waveform centered correlation and peak-channel equality descriptive only.',
        limits='No automatic merging or exclusion thresholds. Full-session overlap includes stimulation. Average waveform similarity alone is not same-cell identity; no raw voltage available.'))
    with h5py.File(p,'r') as f:
        ids=f['units/id'][:];sp=f['units/spike_times'][:];ends=f['units/spike_times_index'][:].astype(int);channels=f['units/peak_channel_index'][:];wave=f['units/waveform_mean'][:]
        fs=1/float(f['units/spike_times'].attrs['resolution']);assert abs(fs-30000)<1e-8
        samples=np.rint(sp*fs).astype(np.int64);assert np.max(abs(samples-sp*fs))<1e-5
        trains=[samples[a:b] for a,b in zip(np.r_[0,ends[:-1]],ends)]
        tr=f['intervals/trials'];lookup={int(t):i for i,t in enumerate(tr['trial_index'][:])}
        priorrows=json.loads(prior.read_text(encoding='utf-8'))['trials'];windows=[(float(tr['start_time'][lookup[r['trial_id']]])+.8,float(tr['start_time'][lookup[r['trial_id']]])+1.3) for r in priorrows]
        catch=[]
        for a in trains:
            t=a/fs;mask=np.zeros(len(a),bool)
            for lo,hi in windows:mask|=(t>=lo)&(t<hi)
            catch.append(a[mask])
    units=[]
    for uid,a,b in zip(ids,trains,catch):
        diff=np.diff(a);assert (diff>=0).all()
        units.append(dict(unit=int(uid),spikes=len(a),catch_spikes=len(b),duplicate_adjacent=int((diff==0).sum()),isi_under1ms=int((diff<30).sum())))
    pairs=[]
    for i in range(len(ids)):
        for j in range(i+1,len(ids)):
            wi=wave[i]-wave[i].mean();wj=wave[j]-wave[j].mean();den=np.linalg.norm(wi)*np.linalg.norm(wj)
            row=dict(units=[int(ids[i]),int(ids[j])],peak_channels=[int(channels[i]),int(channels[j])],same_peak_channel=bool(channels[i]==channels[j]),waveform_correlation=float(np.dot(wi,wj)/den) if den>0 else None)
            for name,seq in [('session',trains),('catch',catch)]:
                a,b=seq[i],seq[j];da,db=nearest(a,b),nearest(b,a)
                row[name]=dict(spikes=[len(a),len(b)],matches={str(tol):[int((da<=tol).sum()),int((db<=tol).sum())] for tol in (0,3,15)},fractions={str(tol):[float((da<=tol).mean()) if len(a) else None,float((db<=tol).mean()) if len(b) else None] for tol in (0,3,15)})
            pairs.append(row)
    save('icms98_unit_overlap_result.json',dict(units=units,pairs=pairs))
    print('within-unit exact duplicates',sum(u['duplicate_adjacent'] for u in units))
    for name in ('session','catch'):
        top=sorted(pairs,key=lambda r:max(v or 0 for v in r[name]['fractions']['0']),reverse=True)[:5]
        print(name)
        for r in top:print(r['units'],r['same_peak_channel'],r['waveform_correlation'],r[name])
if __name__=='__main__':main()
