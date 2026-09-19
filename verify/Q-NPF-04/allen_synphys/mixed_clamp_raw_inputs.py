"""SI source voltages, target current and commands on a common NWB clock.

Retain every mixed sweep and source, including failed QC. This extraction is
not a spike detector, a synaptic-current separation or a plasticity estimate.
"""
import argparse
import json
from pathlib import Path
import platform

import h5py
import numpy as np

from vc20hz_source_inputs import HERE, ROOT, LayeredRanges, sha, text

BASE=ROOT/'data/external/allen_synphys_r21/raw_ranges/1630015960.701'
BASE_SHA='efa3db9f607a22360391ed8220b05bd8a577d9fb348f5c3f98032f67559ec75b'
OVERLAY=ROOT/'data/external/allen_synphys_r21/mixed_clamp_raw_ranges/v1'
PULSES=HERE/'mixed_clamp_pulses_result.json'
PULSES_SHA='f023db5b41d40c4ccbb5bb91c89af926898f38d7fb607c09b8446bb341aa76c7'
DEVICES=(0,1,3,5,6)
SWEEPS=tuple(range(64,88))
MAX_NEW=64*1024*1024
DEPENDENCIES={
    'vc20hz_source_inputs.py':'2a10fbf34a3c15b0f33765baf6b335249ebb06647d47cda6429b4d6b123227cb',
    'raw_metadata.py':'5aa32fce7a19372183cf304ecf70bcd1d168dc723ffcffbc74f0711d83db50ae',
}


def si_values(values, conversion, offset):
    values=np.asarray(values)
    if values.ndim!=1 or not len(values) or not np.isfinite(values).all():
        raise ValueError('Invalid signal samples')
    if not np.isfinite([conversion,offset]).all() or conversion<=0:
        raise ValueError('Invalid SI conversion')
    converted=values.astype(np.float64)*conversion+offset
    if not np.isfinite(converted).all():raise ValueError('Nonfinite SI signal')
    return converted


def command_intervals(values, rate, unit):
    """Excursions from initial command in SI; retain negative and terminal runs."""
    values=np.asarray(values,float)
    if unit not in ('A','V') or values.ndim!=1 or not len(values) or not np.isfinite(values).all() or not np.isfinite(rate) or rate<=0:
        raise ValueError('Invalid command or units')
    threshold={'A':1e-15,'V':1e-7}[unit]
    delta=values-values[0]
    active=np.abs(delta)>threshold
    edges=np.diff(np.r_[False,active,False].astype(np.int8))
    return [dict(start_index=int(a),stop_index=int(b),start_s=float(a/rate),stop_s=float(b/rate),
        duration_s=float((b-a)/rate),delta_min=float(delta[a:b].min()),delta_max=float(delta[a:b].max()),unit=unit)
        for a,b in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1))]


def validate_records(rows):
    keys={(r['device'],r['kind']) for r in rows}
    if len(rows)!=10 or keys!={(d,k) for d in DEVICES for k in ('acquisition','command')}:
        raise ValueError('Missing or duplicate channel identity')
    clocks={(r['start'],r['rate'],r['samples']) for r in rows}
    if len(clocks)!=1:raise ValueError('Channel clock mismatch')
    for row in rows:
        expected=('A' if row['device']==1 else 'V') if row['kind']=='acquisition' else ('V' if row['device']==1 else 'A')
        if row['unit']!=expected or row['electrode']!='electrode_'+str(row['device']):
            raise ValueError('Measurement mode or electrode mismatch')
        if row['rate']<=0 or row['samples']<=0 or not np.isfinite([row['start'],row['rate']]).all():
            raise ValueError('Invalid signal clock')


def extract(reader, pulse_inventory):
    arrays,records={},[]
    by_sweep={s['sweep']:s for s in pulse_inventory['sweeps']}
    if set(by_sweep)!=set(SWEEPS):raise ValueError('Pulse inventory sweep mismatch')
    with h5py.File(reader,'r') as nwb:
        group_names={kind:list(nwb[path].keys()) for kind,path in (
            ('acquisition','acquisition/timeseries'),('command','stimulus/presentation'))}
        for sweep in SWEEPS:
            db={r['device_id']:r for r in by_sweep[sweep]['records']}
            if set(db)!=set(DEVICES):raise ValueError('DB device inventory mismatch')
            rows=[]
            for kind,path in (('acquisition','acquisition/timeseries'),('command','stimulus/presentation')):
                found=set()
                for name in group_names[kind]:
                    if not name.startswith(f'data_{sweep:05d}_'):continue
                    node=nwb[path+'/'+name]
                    if 'electrode_name' not in node:continue
                    electrode=text(np.asarray(node['electrode_name'][()]).reshape(-1)[0])
                    wanted={f'electrode_{d}':d for d in DEVICES}
                    if electrode not in wanted:continue
                    device=wanted[electrode]
                    if device in found:raise ValueError('Duplicate device channel')
                    found.add(device)
                    data=node['data']; unit=text(data.attrs['unit'])
                    rate=float(node['starting_time'].attrs['rate'])
                    start=float(np.asarray(node['starting_time'][()]).reshape(-1)[0])
                    conversion=float(data.attrs['conversion']); offset=float(data.attrs.get('offset',0.))
                    values=si_values(data[()],conversion,offset)
                    key=f's{sweep}_d{device}_{kind}_{unit}'
                    arrays[key]=values
                    row=dict(sweep=sweep,device=device,kind=kind,path=node.name,array_key=key,unit=unit,
                        electrode=electrode,recording_id=db[device]['id'],electrode_id=db[device]['electrode_id'],
                        recording_qc=db[device]['qc_pass'],clamp_mode=db[device]['clamp_mode'],
                        start=start,rate=rate,samples=len(values),conversion=conversion,offset=offset,
                        raw_dtype=str(data.dtype),raw_shape=list(data.shape),raw_chunks=data.chunks,
                        raw_compression=data.compression)
                    if kind=='command':
                        row.update(initial_command=float(values[0]),command_intervals=command_intervals(values,rate,unit))
                    rows.append(row)
            validate_records(rows)
            records.extend(rows)
            print(f'Extracted mixed sweep {sweep}: 10 SI channels',flush=True)
    return arrays,records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--allow-download',action='store_true')
    parser.add_argument('--output',type=Path,default=HERE/'mixed_clamp_raw_inputs_result.json')
    parser.add_argument('--array-output',type=Path,default=ROOT/'data/local/allen-synphys-analysis/mixed-clamp-inputs-v1/full_inputs.npz')
    args=parser.parse_args()
    if args.output.exists() or args.array_output.exists():raise FileExistsError('Preserve extraction outputs')
    if sha(PULSES)!=PULSES_SHA:raise ValueError('Frozen pulse inventory changed')
    for name,digest in DEPENDENCIES.items():
        if sha(HERE/name)!=digest:raise ValueError('Frozen dependency changed: '+name)
    inventory=json.loads(PULSES.read_text(encoding='utf-8'))
    with LayeredRanges(BASE,OVERLAY,args.allow_download,BASE_SHA,MAX_NEW) as reader:
        try:arrays,records=extract(reader,inventory)
        except Exception:
            print(json.dumps(dict(status='INCOMPLETE',missing_blocks=sorted(reader.missing),downloaded_this_session=reader.downloaded)),flush=True)
            raise
        provenance=dict(remote=reader.remote,base_manifest= (BASE/'manifest.json').relative_to(ROOT).as_posix(),
            base_manifest_sha256=reader.base_sha,used_base=reader.used_base,used_overlay=reader.used_overlay,
            overlay_manifest=reader.manifest_path.relative_to(ROOT).as_posix(),
            overlay_manifest_sha256=sha(reader.manifest_path) if reader.manifest_path.exists() else None,
            overlay_bytes=sum(r['bytes'] for r in reader.manifest['blocks'].values()),
            downloaded_this_session=reader.downloaded,max_overlay_bytes=MAX_NEW)
    if sha(BASE/'manifest.json')!=BASE_SHA:raise ValueError('Parent cache changed')
    args.array_output.parent.mkdir(parents=True,exist_ok=True)
    with args.array_output.open('xb') as stream:np.savez_compressed(stream,**arrays)
    result=dict(schema='allen.mixed-clamp.raw-inputs.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_mixed_clamp_raw_inputs.py'),dependency_sha256=DEPENDENCIES,
        pulse_inventory_sha256=PULSES_SHA,provenance=provenance,records=records,
        arrays=dict(path=args.array_output.relative_to(ROOT).as_posix(),bytes=args.array_output.stat().st_size,sha256=sha(args.array_output)),
        python=platform.python_version(),numpy=np.__version__,h5py=h5py.__version__,
        interpretation='All24 sweeps and five devices retained regardless of QC and reported connectivity. '
        'Source IC voltage and VC target current plus commands; common raw clock validated. '
        'No spike-count validation, PSC isolation, compensation correction or plasticity model fitted.')
    serialized=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    with args.output.open('x',encoding='utf-8') as stream:stream.write(serialized)
    print(json.dumps(dict(records=len(records),new_bytes=provenance['downloaded_this_session'],array_bytes=args.array_output.stat().st_size)))


if __name__=='__main__':main()
