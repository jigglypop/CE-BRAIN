"""기준선 대조와 실제 첫 자극 주변의 모든 저장 DA 명령을 확인한다."""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from raw_sweep_map import text
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CONTRACT=HERE/'ic_command_context_contract.json'
OUTPUT=HERE/'ic_command_context_result.json'
ARCHIVE=raw.CACHE/'ic_all_command_context.npz'
INV=HERE/'ic_extended_inventory_result.json'
RESP=HERE/'ic_extension_first_result.json'


def metrics(v,fs):
    assert np.isfinite(v).all()
    transitions=np.flatnonzero(np.diff(v)!=0)+1
    return dict(minimum=float(v.min()),maximum=float(v.max()),range=float(np.ptp(v)),
                transition_indices=transitions.tolist(),constant=bool(len(transitions)==0))


def analyze(arrays,metadata,responses):
    rows=[]
    for entry in metadata:
        key=entry['key'];fs=entry['rate']
        rows.append(dict(**entry,baseline=metrics(arrays[key+'_baseline'],fs),event=metrics(arrays[key+'_event'],fs)))
    edges=[]
    for r in responses:
        entry=next(e for e in metadata if e['sweep']==r['sweep'] and e['electrode']=='electrode_5')
        v=arrays[entry['key']+'_event'];fs=entry['rate'];t=np.arange(len(v))/fs-.01
        base=v[t<-.003].mean();height=v.max()-base;active=np.flatnonzero(v-base>height/2)
        assert len(active)>1 and np.all(np.diff(active)==1)
        start=float(t[active[0]]);end=float(t[active[-1]]+1/fs)
        spike=r['spikes'][0]['max_slope_time']
        edges.append(dict(sweep=r['sweep'],command_start_s=start,command_end_s=end,
            max_slope_after_command_ms=(spike-start)*1000,command_end_relative_spike_ms=(end-spike)*1000))
    return dict(rows=rows,edges=edges,summary=dict(command_channels=len(rows),
        changing_baseline_channels=sum(not r['baseline']['constant'] for r in rows),
        changing_event_channels=sum(not r['event']['constant'] for r in rows),
        changing_event_electrodes=sorted(set(r['electrode'] for r in rows if not r['event']['constant'])),
        spike_delay_ms=[min(e['max_slope_after_command_ms'] for e in edges),max(e['max_slope_after_command_ms'] for e in edges)],
        command_end_relative_spike_ms=[min(e['command_end_relative_spike_ms'] for e in edges),max(e['command_end_relative_spike_ms'] for e in edges)]))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    spec=dict(scope='all stored DA presentation channels in sweeps37..56; excludes unrecorded external stimulus sources',
        baseline_window_s=[.08,.53],event_window_relative_first_command_s=[-.01,.012],
        criterion='exact stored command constancy in baseline; no holding-current removal required for constancy; all transitions retained',
        claim='Tests commanded changes, not spontaneous spikes or absence of all biological input; command-edge coincidence is not causal proof of artifact',
        inventory_sha256=sha(INV),response_sha256=sha(RESP),code_sha256=sha(Path(__file__)),
        shared_reader_sha256=sha(Path(raw.__file__)),max_cache_bytes=160*1024*1024)
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,ensure_ascii=False,indent=2)
    responses=json.loads(RESP.read_text(encoding='utf-8'))['analysis']['records']
    if args.verify:
        result=json.loads(OUTPUT.read_text(encoding='utf-8'))
        assert sha(CONTRACT)==result['contract_sha256'] and sha(ARCHIVE)==result['archive_sha256']
        with np.load(ARCHIVE,allow_pickle=False) as arrays:
            assert analyze(arrays,result['metadata'],responses)==result['analysis']
        print('ALL_STORED_COMMAND_CONTEXT_REPRODUCED');return
    if OUTPUT.exists():raise RuntimeError('기존 결과 보존')
    inventory=json.loads(INV.read_text(encoding='utf-8'))
    raw.LIMIT=spec['max_cache_bytes'];arrays={};metadata=[]
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            group=f['stimulus/presentation'];names=list(group)
            for sweep in inventory['selected']:
                sw=sweep['sweep']
                if not 37<=sw<=56:continue
                matching=sorted(n for n in names if n.startswith(f'data_{sw:05d}_DA'))
                assert matching
                for name in matching:
                    node=group[name];ds=node['data'];fs=float(node['starting_time'].attrs['rate'])
                    assert fs==sweep['nodes']['pre']['rate']
                    assert float(node['starting_time'][()][0])==sweep['nodes']['pre']['start_s']
                    mid=round(sweep['onset_times_s'][0]*fs)
                    windows={'baseline':(round(.08*fs),round(.53*fs)), 'event':(mid-round(.01*fs),mid+round(.012*fs))}
                    for label,(lo,hi) in windows.items():
                        values=np.array(ds[lo:hi],dtype=float)*float(ds.attrs['conversion']);assert len(values)==hi-lo
                        arrays[name+'_'+label]=values
                    metadata.append(dict(key=name,sweep=sw,path=node.name,electrode=text(node['electrode_name'][()][0]),
                        unit=text(ds.attrs['unit']),rate=fs))
                print('command channels checked',sw,len(matching),flush=True)
        new_bytes=reader.downloaded_this_session
    if ARCHIVE.exists():
        with np.load(ARCHIVE,allow_pickle=False) as saved:
            assert set(saved.files)==set(arrays) and all(np.array_equal(saved[k],v) for k,v in arrays.items())
    else:
        with ARCHIVE.open('xb') as stream:np.savez_compressed(stream,**arrays)
    result=dict(contract_sha256=sha(CONTRACT),archive_sha256=sha(ARCHIVE),new_bytes=new_bytes,metadata=metadata,
                analysis=analyze(arrays,metadata,responses))
    with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps(result['analysis']['summary'],indent=2))


if __name__=='__main__':main()
