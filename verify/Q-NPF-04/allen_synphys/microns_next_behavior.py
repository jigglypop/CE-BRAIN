"""추가 스캔의 모든 반복 행동을 기존 보간·결측 규칙으로 확인한다."""
import json
from pathlib import Path
import numpy as np,h5py
import raw_metadata as raw
from microns_repeat_response import prefetch
from microns_repeat_behavior import align
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    source=ROOT/'data/external/microns_functional_nwb/scan_5_3_repeated_clips.npz';data=np.load(source)
    query=data['trial_starts'][:,:,None]+data['relative_time'][None,None,:]
    save('microns_next_behavior_contract.json',dict(question='What observed behavior and missingness accompany all60 repeats in scan5/3, including influential repeat10?',
        method='Reuse original adjacent-finite-sample interpolation with maximum gap3 median source intervals. Apply units conversion once. Report every repeat; no outcome-based exclusions or imputation.',
        limits='Descriptive behavior audit; no causal attribution of influential repeat.',code_sha256=sha(Path(__file__)),source_sha256=sha(source)))
    raw.URL=next(u for u in json.loads((HERE/'microns_scan_5_3_asset.json').read_text())['contentUrl'] if u.startswith('https://dandiarchive.s3.amazonaws.com/'))
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_5_3_ranges';raw.LIMIT=160*1024*1024
    paths={'speed':'acquisition/treadmill_velocity','pupil_major':'acquisition/PupilTracking/pupil_major_radius','pupil_minor':'acquisition/PupilTracking/pupil_minor_radius','eye':'acquisition/EyeTracking/eye_position'}
    arrays={};metadata={}
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            spans=set()
            for p in paths.values():
                for key in ('data','timestamps'):
                    ds=f[p+'/'+key]
                    if ds.chunks:
                        for index in np.ndindex(*tuple((s+c-1)//c for s,c in zip(ds.shape,ds.chunks))):
                            info=ds.id.get_chunk_info_by_coord(tuple(i*c for i,c in zip(index,ds.chunks)));spans.add((int(info.byte_offset),int(info.size)))
                    else:spans.add((int(ds.id.get_offset()),ds.size*ds.dtype.itemsize))
            prefetch(reader,spans)
            for name,p in paths.items():
                ds=f[p+'/data'];t=f[p+'/timestamps'][:];conversion=float(ds.attrs.get('conversion',1));offset=float(ds.attrs.get('offset',0));v=ds[:]*conversion+offset
                cols=[(name,v)] if v.ndim==1 else [('eye_x',v[:,0]),('eye_y',v[:,1])]
                for key,values in cols:
                    arrays[key],stats=align(t,values,query);metadata[key]=dict(**stats,unit=str(ds.attrs.get('unit','')),conversion=conversion,offset=offset)
    dest=ROOT/'data/external/microns_functional_nwb/scan_5_3_repeated_behavior.npz'
    if not dest.exists():
        with dest.open('xb') as f:np.savez_compressed(f,query_time=query,**arrays)
    else:assert all(np.array_equal(np.load(dest)[k],v,equal_nan=True) for k,v in arrays.items())
    summary={}
    for key,v in arrays.items():
        x=np.abs(v) if key=='speed' else v
        summary[key]=dict(per_repeat_valid=[int(np.isfinite(x[:,r]).sum()) for r in range(10)],per_repeat_mean=[float(np.nanmean(x[:,r])) if np.isfinite(x[:,r]).any() else None for r in range(10)])
    save('microns_next_behavior_result.json',dict(metadata=metadata,summary=summary,complete_samples=int(np.logical_and.reduce([np.isfinite(v) for v in arrays.values()]).sum()),artifact_sha256=sha(dest),limits='Descriptive state, not causal explanation of repeat10.'))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
