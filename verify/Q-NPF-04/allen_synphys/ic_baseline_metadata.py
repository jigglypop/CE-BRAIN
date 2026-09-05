"""IC 기준선 복원에 필요한 notebook 입력을 수집한다. 파형 QC 판정은 하지 않는다."""
import json
from pathlib import Path
import h5py
import numpy as np
from raw_metadata import CachedRanges
from raw_sweep_map import text

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'ic_baseline_metadata_result.json'
if OUTPUT.exists(): raise RuntimeError('기존 메타데이터 보존')
requested=['Clamp Mode','I-Clamp Holding Level','Delay onset auto','Delay onset user','Delay termination','Bridge Bal Enable','Bridge Bal Value']
inventory=json.loads((HERE/'ic_extended_inventory_result.json').read_text(encoding='utf-8'))
with CachedRanges() as reader:
    with h5py.File(reader,'r') as f:
        nb=f['general/labnotebook/ITC1600_Dev_0']
        keys=[text(k) for k in nb['numericalKeys'][0]]
        assert all(k in keys for k in requested+['EntrySourceType'])
        indices=sorted(set([0]+[keys.index(k) for k in requested+['EntrySourceType']]))
        columns=[keys[i] for i in indices]
        data=nb['numericalValues'][:,indices,:]
        kind=columns.index('EntrySourceType'); merged={}
        for values in data:
            if not np.isfinite(values[0,0]) or values[kind,0]!=0: continue
            sw=int(values[0,0])
            if sw not in range(32,57): continue
            if sw not in merged: merged[sw]=values.copy()
            else:
                valid=np.isfinite(values);merged[sw][valid]=values[valid]
        rows=[]
        for sweep in inventory['selected']:
            sw=sweep['sweep'];values=merged[sw].copy()
            global_mask=np.isfinite(values[:,8]);values[global_mask]=values[global_mask,8:9]
            for label,hs in [('positive',4),('negative',2)]:
                fields={k:None if not np.isfinite(values[columns.index(k),hs]) else float(values[columns.index(k),hs]) for k in requested}
                assert fields['Clamp Mode']==1
                node=sweep['nodes'][label]; duration=node['samples']/node['rate']
                regions=[]
                if all(fields[k] is not None for k in ('Delay onset auto','Delay onset user','Delay termination')):
                    start=fields['Delay onset auto']/1000;delay=fields['Delay onset user']/1000;tail=fields['Delay termination']/1000
                    if delay>0: regions.append([start,start+delay])
                    if tail>0: regions.append([duration-tail,duration])
                    assert all(0<=a<b<=duration for a,b in regions)
                rows.append(dict(sweep=sw,target=label,headstage=hs,fields=fields,
                                 notebook_baseline_regions_s=regions,trace_duration_s=duration))
    result=dict(status='METADATA_ONLY_NOT_FULL_QC',method='sweep source type0; last finite per field within sweep; global column8 overrides channel; no across-sweep carry',
                baseline_definition='pinned MiesRecording notebook-delay regions; multi-cell pulse mask is a different definition',
                rows=rows,new_bytes=reader.downloaded_this_session)
with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
print(json.dumps(dict(records=len(rows),new_bytes=result['new_bytes'],examples=rows[:2]),ensure_ascii=False,indent=2))
