"""60회 반복의 행동을 관측 범위 안에서 정렬하고 결측을 보존한다."""
import json
from pathlib import Path
import h5py,numpy as np
import raw_metadata as raw
from microns_repeat_response import prefetch
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def align(t,v,q):
    assert np.isfinite(t).all() and (np.diff(t)>0).all()
    flat=q.ravel();right=np.searchsorted(t,flat,side='right');left=right-1
    inside=(left>=0)&(right<len(t));left=np.clip(left,0,len(t)-1);right=np.clip(right,0,len(t)-1)
    dt=t[right]-t[left];max_gap=3*float(np.median(np.diff(t)))
    valid=inside&(dt>0)&(dt<=max_gap)&np.isfinite(v[left])&np.isfinite(v[right])
    out=np.full(len(flat),np.nan);a=(flat[valid]-t[left[valid]])/dt[valid]
    out[valid]=v[left[valid]]*(1-a)+v[right[valid]]*a
    return out.reshape(q.shape),dict(max_interpolation_gap_seconds=max_gap,valid=int(valid.sum()),total=len(valid),outside=int((~inside).sum()),long_gap=int((inside&(dt>max_gap)).sum()))


def main():
    data_path=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_clips.npz'
    data=np.load(data_path);query=data['trial_starts'][:,:,None]+data['relative_time'][None,None,:]
    save('microns_repeat_behavior_contract.json',dict(question='Are measured running and eye/pupil state stable and sufficiently observed across the60 selected repeats?',
        selection='All previously fixed60 repeats and57 relative samples; no outcome-dependent exclusions.',
        interpolation='Linear using adjacent original samples only; both endpoints finite, bracket within source, gap<=3 median source intervals. No filling across NaN.',
        units='Apply source conversion and offset once. Running summary uses absolute speed in m/s; pupil/eye in px.',
        missing='Keep valid masks; trial summaries require>=80% valid aligned samples, otherwise null. Preserve all trial rows.',
        limits='Same animal; descriptive state drift and missingness. No causal confounder sufficiency claim.',code_sha256=sha(Path(__file__)),response_sha256=sha(data_path)))
    paths={'speed':'acquisition/treadmill_velocity','pupil_major':'acquisition/PupilTracking/pupil_major_radius','pupil_minor':'acquisition/PupilTracking/pupil_minor_radius','eye':'acquisition/EyeTracking/eye_position'}
    raw.URL=json.loads((HERE/'microns_nwb_processing_result.json').read_text())['remote']['url']
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges';raw.LIMIT=256*1024*1024
    arrays={};metadata={}
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            spans=set()
            for path in paths.values():
                for key in ('timestamps','data'):
                    ds=f[path+'/'+key]
                    if ds.chunks:
                        shape=tuple((s+c-1)//c for s,c in zip(ds.shape,ds.chunks))
                        for index in np.ndindex(*shape):
                            info=ds.id.get_chunk_info_by_coord(tuple(i*c for i,c in zip(index,ds.chunks)))
                            assert info.byte_offset is not None
                            spans.add((int(info.byte_offset),int(info.size)))
                    else:spans.add((int(ds.id.get_offset()),ds.size*ds.dtype.itemsize))
            prefetch(reader,spans)
            for name,path in paths.items():
                g=f[path];t=g['timestamps'][:];ds=g['data'];conversion=float(ds.attrs.get('conversion',1));offset=float(ds.attrs.get('offset',0));v=ds[:].astype(float)*conversion+offset
                columns=[(name,v)] if v.ndim==1 else [('eye_x',v[:,0]),('eye_y',v[:,1])]
                for key,values in columns:
                    aligned,stats=align(t,values,query);arrays[key]=aligned
                    metadata[key]=dict(**stats,unit=str(ds.attrs.get('unit','')),conversion=conversion,offset=offset)
    dest=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_behavior.npz'
    if not dest.exists():
        with dest.open('xb') as f:np.savez_compressed(f,query_time=query,**arrays)
    else:
        old=np.load(dest);assert all(np.array_equal(old[k],a,equal_nan=True) for k,a in arrays.items())
    trial_rows=[]
    for c in range(6):
        for r in range(10):
            row=dict(condition=str(data['conditions'][c]),repeat=r,start=float(data['trial_starts'][c,r]))
            for key,values in arrays.items():
                x=values[c,r];valid=np.isfinite(x);x=np.abs(x) if key=='speed' else x
                row[key]=dict(valid=int(valid.sum()),mean=float(x[valid].mean()) if valid.mean()>=.8 else None)
            trial_rows.append(row)
    summary={}
    for key,values in arrays.items():
        x=np.abs(values) if key=='speed' else values
        summary[key]=dict(first5_mean=float(np.nanmean(x[:,:5])),last5_mean=float(np.nanmean(x[:,5:])),per_repeat_valid=[int(np.isfinite(x[:,r]).sum()) for r in range(10)],per_repeat_mean=[float(np.nanmean(x[:,r])) if np.isfinite(x[:,r]).any() else None for r in range(10)],trials_passing_80percent=sum(row[key]['mean'] is not None for row in trial_rows))
    save('microns_repeat_behavior_result.json',dict(metadata=metadata,summary=summary,trials=trial_rows,arrays_sha256=sha(dest),complete_case_samples=int(np.logical_and.reduce([np.isfinite(x) for x in arrays.values()]).sum())))
    print(json.dumps(dict(metadata=metadata,summary=summary),indent=2))


if __name__=='__main__':main()
