"""같은 전세포와 양성·음성 표적이 함께 기록된 첫 IC pulse-train 시행을 찾는다."""
import json
import argparse
import sqlite3
from pathlib import Path
import h5py
from raw_metadata import CachedRanges
from raw_sweep_map import fields,text
from raw_pulse_windows import onset_times

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def describe(node):
    data=node['data']
    return {'path':node.name,'electrode':text(node['electrode_name'][()][0]),
        'unit':text(data.attrs['unit']),'conversion':float(data.attrs['conversion']),
        'rate':float(node['starting_time'].attrs['rate']),'start_s':float(node['starting_time'][()][0]),
        'samples':data.shape[0]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',default='SPulsTrn')
    parser.add_argument('--output',type=Path,default=HERE/'ic_pair_inventory_result.json')
    args=parser.parse_args()
    output=args.output
    if output.exists():raise RuntimeError('기존 IC 재고 보존')
    dbpath=ROOT/'data/external/allen_synphys_r21/synphys_r2.1_small.sqlite'
    with sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True) as db:
        rows=db.execute('SELECT c.id,c.ext_id,el.device_id FROM cell c JOIN electrode el ON el.id=c.electrode_id WHERE c.experiment_id=3337 AND c.ext_id IN (\'3\',\'5\',\'6\') ORDER BY c.ext_id').fetchall()
    assert [(r[1],r[2]) for r in rows]==[('3',2),('5',4),('6',5)]
    selected=[];scanned=[];carried={}
    with CachedRanges() as r:
        with h5py.File(r,'r') as f:
            acq=f['acquisition/timeseries']
            names=[n for n in acq if n.endswith('_AD9')]
            for name in names:
                sweep=int(name.split('_')[1])
                if sweep>=40:break
                node=acq[name]
                assert text(node['electrode_name'][()][0])=='electrode_5'
                carried.update(fields(node.attrs['comment'],5))
                stimulus=text(node['stimulus_description'][()][0])
                unit=text(node['data'].attrs['unit'])
                scanned.append({'sweep':sweep,'unit':unit,'stimulus':stimulus})
                if unit!='V' or args.protocol not in stimulus:continue
                times=onset_times(carried.get('Epochs',''))
                if len(times)!=12:continue
                paths={'pre':name,'positive':f'data_{sweep:05d}_AD8','negative':f'data_{sweep:05d}_AD2'}
                if not all(n in acq for n in paths.values()):continue
                nodes={k:describe(acq[n]) for k,n in paths.items()}
                assert [nodes[k]['electrode'] for k in ('pre','positive','negative')]==['electrode_5','electrode_4','electrode_2']
                if any(n['unit']!='V' for n in nodes.values()):continue
                command=describe(f[f'stimulus/presentation/data_{sweep:05d}_DA5'])
                assert command['electrode']=='electrode_5' and command['unit']=='A'
                assert len({n['start_s'] for n in list(nodes.values())+[command]})==1
                assert len({n['rate'] for n in list(nodes.values())+[command]})==1
                selected.append({'sweep':sweep,'stimulus':stimulus,'onset_times_s':times,'nodes':nodes,'command':command})
                print('selected IC sweep',sweep,flush=True)
                if len(selected)==5:break
        result={'selection':'first5 triple-current-clamp pulse trains among sweepIDs<40;12pulses; units/identity/same relative clock checked before reading responses',
                'protocol_substring':args.protocol,
                'db_cells':rows,'scanned':scanned,'selected':selected,'new_bytes':r.downloaded_this_session,
                'cached_bytes':sum(b['bytes'] for b in r.manifest['blocks'].values()),
                'status':'READY' if len(selected)==5 else 'INSUFFICIENT_MATCHED_SWEEPS'}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('scanned','selected')},indent=2))


if __name__=='__main__':main()
