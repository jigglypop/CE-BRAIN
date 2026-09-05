"""다음 스캔의 6조건 10회 반복을 같은 시간 정렬로 수집한다."""
import json
from collections import defaultdict
from pathlib import Path
import h5py,numpy as np
import raw_metadata as raw
from microns_repeat_response import prefetch
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    targets=json.loads((HERE/'microns_seventh_scan_result.json').read_text())['targets']
    save('microns_seventh_repeats_contract.json',dict(selection='scan6/6 all49 fixed targets, all Clip conditions appearing10 times; same .5<=relative_time<9.5 grid at median imaging interval, both timing conventions.',
        analysis='Reuse original structural pair labels and fixed distance cuts. Raw, repeat mean, leave-one-repeat-out residual for all10/first5/last5. 999 per-cell circular shifts, seed20260905, same shift across6 conditions.',
        limits='Same mouse, no independent animal claim, no calibrated permutation p-value, no behavior correction. Prior first-window values already viewed; no selective trial exclusions.',code_sha256=sha(Path(__file__))))
    dest=ROOT/'data/external/microns_functional_nwb/scan_6_6_repeated_clips.npz'
    if dest.exists():
        receipt=json.loads((HERE/'microns_seventh_repeats_acquisition.json').read_text());assert sha(dest)==receipt['artifact_sha256'];print('NEXT_REPEATS_CACHE_VERIFIED');return
    raw.URL=next(u for u in json.loads((HERE/'microns_scan_6_6_asset.json').read_text())['contentUrl'] if u.startswith('https://dandiarchive.s3.amazonaws.com/'))
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_6_6_ranges';raw.LIMIT=160*1024*1024
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            g=f['intervals/Clip'];groups=defaultdict(list)
            for start,stop,h in zip(g['start_time'][:],g['stop_time'][:],g['condition_hash'][:]):
                groups[h.decode() if isinstance(h,bytes) else str(h)].append(dict(start=float(start),stop=float(stop)))
            groups={k:sorted(v,key=lambda t:t['start']) for k,v in sorted(groups.items()) if len(v)==10};assert len(groups)==6
            frames=f['processing/ophys/Fluorescence/RoiResponseSeries2/timestamps'][:];assert np.isfinite(frames).all() and (np.diff(frames)>0).all()
            relative=np.arange(.5,9.5,float(np.median(np.diff(frames))));windows=[]
            delay=max(t['ms_delay'] for t in targets)/1000
            for c,rows in enumerate(groups.values()):
                for r,t in enumerate(rows):
                    start=max(0,int(np.searchsorted(frames,t['start']+.5-delay))-2);stop=min(len(frames),int(np.searchsorted(frames,t['start']+relative[-1]))+2)
                    assert t['start']+relative[-1]<t['stop'];windows.append((c,r,t['start'],start,stop))
            spans=set()
            for field in sorted({t['field'] for t in targets}):
                series=f[f'processing/ophys/Fluorescence/RoiResponseSeries{field}'];assert np.array_equal(series['timestamps'][:],frames)
                ds=series['data'];ch=ds.chunks
                cols={int((t['mask_id']-1)//ch[1]*ch[1]) for t in targets if t['field']==field}
                rr={i for _,_,_,start,stop in windows for i in range(start//ch[0]*ch[0],stop,ch[0])}
                for row in sorted(rr):
                    for col in sorted(cols):
                        info=ds.id.get_chunk_info_by_coord((row,col));spans.add((int(info.byte_offset),int(info.size)))
            prefetch(reader,spans);aligned=np.empty((2,6,10,len(relative),len(targets)))
            for field in sorted({t['field'] for t in targets}):
                indices=[i for i,t in enumerate(targets) if t['field']==field];cols=[targets[i]['mask_id']-1 for i in indices]
                ds=f[f'processing/ophys/Fluorescence/RoiResponseSeries{field}/data']
                for c,r,start_time,start,stop in windows:
                    values=ds[start:stop,cols];assert np.isfinite(values).all()
                    for j,i in enumerate(indices):
                        for mode,d in enumerate((0,targets[i]['ms_delay']/1000)):
                            t=frames[start:stop]+d;query=start_time+relative;assert query[0]>=t[0] and query[-1]<=t[-1]
                            aligned[mode,c,r,:,i]=np.interp(query,t,values[:,j])
    with dest.open('xb') as out:np.savez_compressed(out,values=aligned,relative_time=relative,unit_ids=np.array([t['unit_id'] for t in targets]),conditions=np.array(list(groups)),trial_starts=np.array([[t['start'] for t in rows] for rows in groups.values()]))
    first=json.loads((HERE/'microns_repeat_response_acquisition.json').read_text())['conditions']
    save('microns_seventh_repeats_acquisition.json',dict(shape=list(aligned.shape),artifact_sha256=sha(dest),all_finite=bool(np.isfinite(aligned).all()),conditions=list(groups),same_condition_hashes_as_first=set(groups)==set(first),trial_start_min=min(t[2] for t in windows),trial_start_max=max(t[2] for t in windows)))
    print('NEXT_REPEATS_ACQUIRED',aligned.shape,flush=True)


if __name__=='__main__':main()
