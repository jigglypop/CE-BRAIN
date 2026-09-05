"""첫 반응 구간의 자극 소속과 동시 행동 기록을 확보한다."""
import json
from pathlib import Path
from collections import Counter
import h5py,numpy as np
import raw_metadata as raw
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    response=ROOT/'data/external/microns_functional_nwb/scan_4_7_first1250.npz'
    times=np.load(response)['frame_times']
    save('microns_stimulus_behavior_contract.json',dict(question='Which named stimulus trials and behavioral signals overlap the existing first1250 frames?',
        interval_rule='Half-open start<=t<stop; retain gaps and multiple coverage explicitly. Source condition hashes define repeats, not stimulus type alone.',
        behavior='Read a prefix that covers the response window plus its bracketing samples. Preserve NaN and units; no extrapolation or outcome-based exclusion.',
        scope='Input alignment, not stimulus removal, causal adjustment, or independent replication.',code_sha256=sha(Path(__file__)),response_sha256=sha(response)))
    output=ROOT/'data/external/microns_functional_nwb/scan_4_7_behavior_prefix.npz'
    raw.URL=json.loads((HERE/'microns_nwb_processing_result.json').read_text())['remote']['url']
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges';raw.LIMIT=96*1024*1024
    arrays={};trials=[];metadata=[]
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            for kind in ('Clip','Monet2','Trippy'):
                g=f['intervals/'+kind];starts=g['start_time'][:];stops=g['stop_time'][:];hashes=g['condition_hash'][:]
                assert np.isfinite(starts).all() and np.isfinite(stops).all() and (stops>starts).all()
                for i,(start,stop,h) in enumerate(zip(starts,stops,hashes)):
                    trials.append(dict(kind=kind,row=i,start=float(start),stop=float(stop),condition_hash=h.decode() if isinstance(h,bytes) else str(h)))
            for name,path in [('treadmill','acquisition/treadmill_velocity'),('pupil_major','acquisition/PupilTracking/pupil_major_radius'),('pupil_minor','acquisition/PupilTracking/pupil_minor_radius'),('eye','acquisition/EyeTracking/eye_position')]:
                g=f[path];n=min(len(g['timestamps']),32768);t=g['timestamps'][:n]
                assert np.isfinite(t).all() and (np.diff(t)>0).all()
                assert t[0]<=times[0] and t[-1]>=times[-1]
                end=min(len(t),int(np.searchsorted(t,times[-1],side='right'))+1)
                t=t[:end];v=g['data'][:end]
                arrays[name+'_time']=t;arrays[name+'_value']=v
                metadata.append(dict(name=name,path=path,shape=list(v.shape),time_start=float(t[0]),time_stop=float(t[-1]),finite=int(np.isfinite(v).sum()),total=int(v.size),unit=str(g['data'].attrs.get('unit','')),conversion=str(g['data'].attrs.get('conversion','')),offset=str(g['data'].attrs.get('offset',''))))
        print('NEW_BYTES',reader.downloaded_this_session,flush=True)
    if not output.exists():
        with output.open('xb') as f:np.savez_compressed(f,**arrays)
    else:
        old=np.load(output)
        assert all(np.array_equal(old[k],v,equal_nan=True) for k,v in arrays.items())
    membership=[[] for t in times]
    overlap=[]
    for trial in trials:
        which=np.flatnonzero((times>=trial['start'])&(times<trial['stop']))
        if len(which):
            overlap.append(dict(**trial,frames=len(which)))
            for i in which:membership[i].append(trial['kind'])
    repeat=Counter((t['kind'],t['condition_hash']) for t in trials)
    result=dict(total_trials=len(trials),trial_counts=dict(Counter(t['kind'] for t in trials)),
        first_window_frames=dict(Counter('+'.join(m) if m else 'unassigned' for m in membership)),
        multiple_membership_frames=sum(len(m)>1 for m in membership),overlap=overlap,
        repeated_conditions=[dict(kind=k,condition_hash=h,count=n) for (k,h),n in sorted(repeat.items()) if n>1],
        behavior=metadata,arrays_sha256=sha(output),limits='Named interval assignment does not remove stimulus drive; simultaneous measured behavior does not imply confounder sufficiency.')
    save('microns_stimulus_trials.json',trials)
    save('microns_stimulus_behavior_result.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
