"""원본의 첫 10개 sweep에서 대상 두 headstage 메타데이터를 교차 확인한다."""
import json
from collections import Counter
from pathlib import Path

import h5py
from raw_metadata import CachedRanges

HERE = Path(__file__).resolve().parent


def text(value):
    return value.decode() if isinstance(value, bytes) else str(value)


def fields(note, headstage):
    result = {}
    wanted = ['Clamp Mode','ADC','DAC','V-Clamp Holding Level','I-Clamp Holding Level',
              'OperatingModeString','Delay onset oodDAQ','Epochs','TP Insert Checkbox','TimeStamp']
    for line in text(note).split('\r'):
        prefix = f'HS#{headstage}:'
        if line.startswith(prefix): line=line[len(prefix):]
        elif line.startswith('HS#'): continue
        if ':' not in line: continue
        key,value=line.split(':',1)
        if key in wanted: result[key]=value.strip()
    return result


def main():
    output=HERE/'raw_sweep_map_result.json'
    if output.exists(): raise RuntimeError('원 sweep 대응 보존')
    rows=[]
    carried={4:{},5:{}}
    with CachedRanges() as r:
        with h5py.File(r,'r') as f:
            session=text(f['session_start_time'][()][0])
            acq=f['acquisition/timeseries']
            for name in acq:
                if int(name.split('_')[1])>=10: break
                if not name.endswith(('_AD8','_AD9')): continue
                node=acq[name]
                src=dict(item.split('=',1) for item in text(node.attrs['source']).split(';'))
                electrode=text(node['electrode_name'][()][0])
                hs=int(electrode.split('_')[-1])
                assert hs in (4,5) and int(src['ElectrodeNumber'])==hs
                meta=fields(node.attrs['comment'],hs)
                carried[hs].update(meta)
                meta=dict(carried[hs])
                if 'DAC' not in meta:
                    raise RuntimeError(f'{name}: headstage {hs}의 DAC 메타데이터 없음; {repr(node.attrs["comment"])[:80]}')
                da=int(float(meta['DAC'].split()[0]))
                sweep=int(src['Sweep'])
                command=f[f'stimulus/presentation/data_{sweep:05d}_DA{da}']
                assert text(command['electrode_name'][()][0])==electrode
                a,b=float(node['starting_time'][()][0]),float(command['starting_time'][()][0])
                assert abs(a-b)<1e-9
                ds=node['data']
                rows.append({'sweep':sweep,'headstage':hs,'ad':int(src['AD']),'da':da,
                    'acquisition':node.name,'command':command.name,'start_s':a,
                    'rate':float(node['starting_time'].attrs['rate']),
                    'unit':text(ds.attrs['unit']),'conversion':float(ds.attrs['conversion']),
                    'samples':ds.shape[0], 'ancestry':[text(x) for x in node.attrs['ancestry']],
                    'stimulus':text(node['stimulus_description'][()][0]),'metadata':meta})
                if len(rows)%40==0: print('mapped channels:',len(rows),flush=True)
        result={'session_start_utc':session,'rows':rows,'new_bytes':r.downloaded_this_session,
                'scope':'sweep IDs 0..9 only. Wider scan intentionally stopped after cache reached ~26MB; cached bytes preserved. Original diagnostic needs first5 eligible sweeps; no response outcomes used to select scope.',
                'metadata_method':'Comments contain changed fields only; headstage-specific values carried forward. Electrode IDs, units, clamp ancestry, command identity and timestamps checked directly for every record. Holding metadata still needs labnotebook validation.',
                'total_cached_bytes':sum(b['bytes'] for b in r.manifest['blocks'].values())}
    result['summary']={str(hs):{'records':sum(row['headstage']==hs for row in rows),
        'modes':dict(Counter(row['ancestry'][-1] for row in rows if row['headstage']==hs)),
        'stimuli':dict(Counter(row['stimulus'] for row in rows if row['headstage']==hs))} for hs in (4,5)}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__': main()
