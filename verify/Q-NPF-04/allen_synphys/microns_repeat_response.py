"""반응을 보지 않고 고른 6개 Clip의 10회 반복을 전체 대상에서 읽는다."""
import json,hashlib,urllib.request
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from pathlib import Path
import h5py,numpy as np
import raw_metadata as raw
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def prefetch(reader,spans):
    missing=set()
    for start,size in spans:
        for b in range(start//raw.BLOCK*raw.BLOCK,((start+size-1)//raw.BLOCK+1)*raw.BLOCK,raw.BLOCK):
            if str(b) not in reader.manifest['blocks']:missing.add(b)
    assert sum(v['bytes'] for v in reader.manifest['blocks'].values())+len(missing)*raw.BLOCK<=raw.LIMIT
    groups=[]
    for b in sorted(missing):
        if groups and b==groups[-1][-1]+raw.BLOCK and len(groups[-1])<16:groups[-1].append(b)
        else:groups.append([b])
    def fetch(blocks):
        start=blocks[0];end=min(blocks[-1]+raw.BLOCK,reader.remote['bytes'])-1
        req=urllib.request.Request(raw.URL,headers={'Range':f'bytes={start}-{end}','If-Match':reader.remote['etag']})
        with urllib.request.urlopen(req,timeout=45) as r:
            assert r.status==206 and r.headers['ETag']==reader.remote['etag']
            assert r.headers['Content-Range']==f"bytes {start}-{end}/{reader.remote['bytes']}"
            data=r.read(end-start+2);assert len(data)==end-start+1
        return blocks,data
    print('PREFETCH',len(missing),'blocks',len(groups),'requests',flush=True)
    # Network reads may overlap; only this main thread writes the shared cache.
    with ThreadPoolExecutor(max_workers=8) as pool:
        for blocks,data in pool.map(fetch,groups):
            for i,b in enumerate(blocks):
                piece=data[i*raw.BLOCK:(i+1)*raw.BLOCK];path=raw.CACHE/f'{b:012d}.bin'
                if path.exists():assert path.read_bytes()==piece
                else:
                    with path.open('xb') as f:f.write(piece)
                reader.manifest['blocks'][str(b)]={'bytes':len(piece),'sha256':hashlib.sha256(piece).hexdigest()}
            tmp=reader.manifest_path.with_suffix('.tmp');tmp.write_text(json.dumps(reader.manifest,indent=2));tmp.replace(reader.manifest_path)


def main():
    trials=json.loads((HERE/'microns_stimulus_trials.json').read_text());groups=defaultdict(list)
    for t in trials:
        if t['kind']=='Clip':groups[t['condition_hash']].append(t)
    groups={k:sorted(v,key=lambda t:t['start']) for k,v in sorted(groups.items()) if len(v)==10};assert len(groups)==6
    targets=json.loads((HERE/'microns_scan_unit_decoding_result.json').read_text())['targets']
    targets=sorted(targets,key=lambda t:(t['field'],t['mask_id']))
    frames=np.load(ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges/roi_identity_arrays.npz')['RoiResponseSeries2_times']
    relative=np.arange(.5,9.5,float(np.median(np.diff(frames))))
    save('microns_repeat_response_contract.json',dict(question='Does the same structural contrast remain after separating repeated stimulus patterns from within-condition trial variation?',
        selection='All6 Clip condition hashes occurring10 times; all60 trials and fixed53 targets. No response-based exclusions.',
        alignment='Relative .5<=t<9.5 seconds at median imaging interval; linear interpolation, no extrapolation. Common frame and positive unit-delay sensitivity.',
        analysis='Report raw, condition-specific repeat mean, and leave-one-repeat-out residual correlations. All10 and chronological first5/last5; include/exclude unit3151; original field-distance contrasts unchanged.',
        limits='Same specimen; temporal replication not independent animal replication. Residual still includes behavior, common input, optical mixing and finite-repeat estimation error. No causal claim.',
        code_sha256=sha(Path(__file__)),trial_table_sha256=sha(HERE/'microns_stimulus_trials.json'),conditions=list(groups)))
    output=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_clips.npz'
    if output.exists():print('ALIGNED_REPEAT_CACHE_EXISTS');return
    raw.URL=json.loads((HERE/'microns_nwb_processing_result.json').read_text())['remote']['url']
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges';raw.LIMIT=256*1024*1024
    windows=[]
    for c,rows in enumerate(groups.values()):
        for r,t in enumerate(rows):
            start=max(0,int(np.searchsorted(frames,t['start']+.5-.154))-2)
            stop=min(len(frames),int(np.searchsorted(frames,t['start']+relative[-1]))+2)
            assert t['start']+relative[-1]<t['stop']
            windows.append((c,r,t['start'],start,stop))
    aligned=np.empty((2,6,10,len(relative),53))
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            spans=set()
            for field in (2,4,6,8):
                ds=f[f'processing/ophys/Fluorescence/RoiResponseSeries{field}/data'];ch=ds.chunks
                cols={int((t['mask_id']-1)//ch[1]*ch[1]) for t in targets if t['field']==field}
                rr={i for _,_,_,start,stop in windows for i in range(start//ch[0]*ch[0],stop,ch[0])}
                for row in sorted(rr):
                    for col in sorted(cols):
                        info=ds.id.get_chunk_info_by_coord((row,col));assert info.byte_offset is not None
                        spans.add((int(info.byte_offset),int(info.size)))
            prefetch(reader,spans)
            for field in (2,4,6,8):
                indices=[i for i,t in enumerate(targets) if t['field']==field];cols=[targets[i]['mask_id']-1 for i in indices]
                ds=f[f'processing/ophys/Fluorescence/RoiResponseSeries{field}/data']
                for c,r,start_time,start,stop in windows:
                    values=ds[start:stop,cols];assert np.isfinite(values).all()
                    for j,i in enumerate(indices):
                        for mode,delay in enumerate((0,targets[i]['ms_delay']/1000)):
                            t=frames[start:stop]+delay;query=start_time+relative
                            assert query[0]>=t[0] and query[-1]<=t[-1]
                            aligned[mode,c,r,:,i]=np.interp(query,t,values[:,j])
    with output.open('xb') as f:np.savez_compressed(f,values=aligned,relative_time=relative,unit_ids=np.array([t['unit_id'] for t in targets]),conditions=np.array(list(groups)),trial_starts=np.array([[t['start'] for t in rows] for rows in groups.values()]))
    save('microns_repeat_response_acquisition.json',dict(shape=list(aligned.shape),all_finite=bool(np.isfinite(aligned).all()),artifact_sha256=sha(output),conditions=list(groups),total_trials=60,limits='Aligned fluorescence, not spikes or causal effects.'))
    print('REPEATED_CLIPS_ACQUIRED',aligned.shape,flush=True)


if __name__=='__main__':main()
