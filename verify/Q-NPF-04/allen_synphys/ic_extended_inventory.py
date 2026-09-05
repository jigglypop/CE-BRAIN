"""첫 100 sweep ID의 동시 IC 반복 자극 메타데이터. 전압 반응은 읽지 않는다."""
import json
import h5py
from ic_pair_inventory import HERE, describe, fields, text, onset_times, CachedRanges

output = HERE / 'ic_extended_inventory_result.json'
if output.exists(): raise RuntimeError('기존 재고 보존')
selected, scanned, carried = [], [], {}
with CachedRanges() as reader:
    with h5py.File(reader, 'r') as f:
        acq = f['acquisition/timeseries']
        names = sorted(n for n in acq if n.endswith('_AD9'))
        for name in names:
            sweep = int(name.split('_')[1])
            if sweep >= 100: break
            node = acq[name]
            assert text(node['electrode_name'][()][0]) == 'electrode_5'
            carried.update(fields(node.attrs['comment'], 5))
            stimulus = text(node['stimulus_description'][()][0])
            unit = text(node['data'].attrs['unit'])
            scanned.append(dict(sweep=sweep, unit=unit, stimulus=stimulus))
            if unit != 'V' or 'SRecovery' not in stimulus: continue
            onsets = onset_times(carried.get('Epochs', ''))
            if len(onsets) != 12: continue
            paths = dict(pre=name, positive=f'data_{sweep:05d}_AD8', negative=f'data_{sweep:05d}_AD2')
            if not all(p in acq for p in paths.values()): continue
            nodes = {k:describe(acq[p]) for k,p in paths.items()}
            if any(n['unit']!='V' for n in nodes.values()): continue
            assert [nodes[k]['electrode'] for k in ('pre','positive','negative')] == ['electrode_5','electrode_4','electrode_2']
            command = describe(f[f'stimulus/presentation/data_{sweep:05d}_DA5'])
            assert command['unit']=='A' and command['electrode']=='electrode_5'
            assert len({n['start_s'] for n in list(nodes.values())+[command]})==1
            assert len({n['rate'] for n in list(nodes.values())+[command]})==1
            selected.append(dict(sweep=sweep, stimulus=stimulus, onset_times_s=onsets, nodes=nodes, command=command))
            print('metadata candidate', sweep, flush=True)
    result = dict(scope='sweep IDs <100, source headstage5, simultaneous IC targets4 and2, SRecovery 12 pulses',
        status='METADATA_ONLY_NOT_QC_PASSED', selected=selected, scanned=scanned,
        new_bytes=reader.downloaded_this_session,
        cached_bytes=sum(b['bytes'] for b in reader.manifest['blocks'].values()))
with output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print('candidate sweep IDs:', [s['sweep'] for s in selected], flush=True)
