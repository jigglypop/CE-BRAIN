"""25개 시행·두 표적의 notebook 기준선과 전체 전압 기록 재구성 QC."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from reference_spike_audit import sha, reference

HERE=Path(__file__).resolve().parent
META=HERE/'ic_baseline_metadata_result.json'
INV=HERE/'ic_extended_inventory_result.json'
CONTRACT=HERE/'ic_full_recording_qc_contract.json'
OUTPUT=HERE/'ic_full_recording_qc_result.json'
STORE=raw.CACHE/'full_ic_targets'


class Reader(raw.CachedRanges):
    def prefetch(self, offset, length):
        if offset is None: return
        first=(offset//raw.BLOCK)*raw.BLOCK
        stops=range(first,offset+length,raw.BLOCK)
        missing=[s for s in stops if str(s) not in self.manifest['blocks']]
        while missing:
            start=missing.pop(0);last=start
            while missing and missing[0]==last+raw.BLOCK and missing[0]-start<2*1024*1024:
                last=missing.pop(0)
            end=min(last+raw.BLOCK,self.remote['bytes'])-1
            assert sum(b['bytes'] for b in self.manifest['blocks'].values())+end-start+1<=raw.LIMIT
            req=urllib.request.Request(raw.URL,headers={'Range':f'bytes={start}-{end}','If-Match':self.remote['etag']})
            with urllib.request.urlopen(req,timeout=30) as response:
                assert response.status==206 and response.headers['ETag']==self.remote['etag']
                assert response.headers['Content-Range']==f"bytes {start}-{end}/{self.remote['bytes']}"
                content=response.read(end-start+2)
            assert len(content)==end-start+1
            for pos in range(start,end+1,raw.BLOCK):
                block=content[pos-start:pos-start+raw.BLOCK];path=raw.CACHE/f'{pos:012d}.bin'
                if path.exists(): assert path.read_bytes()==block
                else:
                    with path.open('xb') as stream:stream.write(block)
                self.manifest['blocks'][str(pos)]={'bytes':len(block),'sha256':hashlib.sha256(block).hexdigest()}
            temp=self.manifest_path.with_suffix('.tmp')
            temp.write_text(json.dumps(self.manifest,indent=2),encoding='utf-8');temp.replace(self.manifest_path)
            self.downloaded_this_session+=len(content)


def measure(voltage, row, node, float_mode):
    fs=node['rate'];finite=np.isfinite(voltage)
    regions=row['notebook_baseline_regions_s']
    chunks=[voltage[round(a*fs):round(b*fs)] for a,b in regions]
    baseline=np.concatenate(chunks);base=baseline[np.isfinite(baseline)]
    potential=float(float_mode(base)) if len(base) else None
    sd=float(base.std()) if len(base) else None
    current=row['fields']['I-Clamp Holding Level']
    zeros=int(np.sum(voltage==0));fail=[]
    if not finite.all():fail.append('nonfinite_samples')
    if zeros>len(voltage)//10:fail.append('over_10_percent_zeros')
    if current is None or not -800<=current<=800:fail.append('holding_current')
    if potential is None or not -.085<=potential<=-.045:fail.append('baseline_voltage')
    if sd is None or sd>.005:fail.append('baseline_noise')
    return dict(sweep=row['sweep'],target=row['target'],samples=len(voltage),nonfinite=int((~finite).sum()),zeros=zeros,
        baseline_samples=len(base),baseline_mV=None if potential is None else potential*1000,
        baseline_sd_uV=None if sd is None else sd*1e6,holding_pA=current,
        baseline_segment_means_mV=[float(np.mean(v[np.isfinite(v)]))*1000 for v in chunks],
        failures=fail,reconstructed_recording_pass=not fail)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    reference()
    from neuroanalysis.baseline import float_mode
    inventory=json.loads(INV.read_text(encoding='utf-8'))
    metadata=json.loads(META.read_text(encoding='utf-8'))
    spec=dict(scope='sweeps32..56, positive/negative target full primary; reconstructed QC, not original producer QC',
        baseline='notebook intervals, finite samples, pinned float_mode histogram and population SD',
        criteria='full trace finite; zeros<=floor(n/10); holding within +/-800pA; baseline[-85,-45]mV inclusive; SD<=5mV',
        limitations='no access resistance or causal specificity; source version gap retained; no response re-selection',
        max_cache_bytes=160*1024*1024,code_sha256=sha(Path(__file__)),metadata_sha256=sha(META),inventory_sha256=sha(INV),
        baseline_source_sha256=sha(HERE.parents[2]/'data/external/analysis_tools/neuroanalysis_source/neuroanalysis/baseline.py'),
        cache_reader_sha256=sha(Path(raw.__file__)))
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,ensure_ascii=False,indent=2)
    STORE.mkdir(exist_ok=True)
    prior_archives=[np.load(raw.CACHE/name,allow_pickle=False) for name in ('ic_positive_negative_windows.npz','ic_extension_first_windows.npz')]
    previous=json.loads(OUTPUT.read_text(encoding='utf-8')) if args.verify else None
    if not args.verify and OUTPUT.exists():raise RuntimeError('기존 결과 보존')
    # Scoped cap extension; frozen shared reader file remains unchanged.
    raw.LIMIT=spec['max_cache_bytes']
    reader=None if args.verify else Reader()
    hdf=None if reader is None else h5py.File(reader,'r')
    rows=[]
    try:
        for row in metadata['rows']:
            sw=row['sweep'];target=row['target'];sweep=next(s for s in inventory['selected'] if s['sweep']==sw)
            node=sweep['nodes'][target];path=STORE/f'{sw}_{target}.npz'
            if not path.exists():
                assert hdf is not None
                ds=hdf[node['path']+'/data'];assert ds.shape==(node['samples'],)
                reader.prefetch(ds.id.get_offset(),ds.size*ds.dtype.itemsize)
                voltage=np.array(ds[:],dtype=float)*float(ds.attrs['conversion'])
                with path.open('xb') as stream:np.savez_compressed(stream,voltage=voltage)
            with np.load(path,allow_pickle=False) as data:voltage=data['voltage']
            assert len(voltage)==node['samples']
            fs=node['rate'];mid=round(sweep['onset_times_s'][0]*fs)
            key=f'sweep{sw}_pulse1_{target}' if sw<=36 else f'{sw}_{target}'
            expected=prior_archives[0 if sw<=36 else 1][key]
            assert np.array_equal(voltage[mid-round(.01*fs):mid+round(.012*fs)],expected)
            result=measure(voltage,row,node,float_mode)
            result.update(array_path=path.relative_to(HERE.parents[2]).as_posix(),array_sha256=sha(path),first_pulse_exact_match=True)
            rows.append(result)
            print('full recording checked',sw,target,flush=True)
        analysis=dict(records=rows,passed=sum(r['reconstructed_recording_pass'] for r in rows),total=len(rows))
        if args.verify:
            assert previous['contract_sha256']==sha(CONTRACT) and previous['analysis']==analysis
            print('FULL_RECORDING_QC_REPRODUCED_OFFLINE')
        else:
            output=dict(contract_sha256=sha(CONTRACT),new_bytes=reader.downloaded_this_session,analysis=analysis)
            with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(output,stream,ensure_ascii=False,indent=2,allow_nan=False)
            print('reconstructed QC pass',analysis['passed'],'/',analysis['total'],flush=True)
    finally:
        if hdf is not None:hdf.close()
        if reader is not None:reader.close()
        for archive in prior_archives:archive.close()


if __name__=='__main__':main()
