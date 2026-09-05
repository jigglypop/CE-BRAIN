"""제작자 선택 36기록의 실제 명령·전압을 수집하고 DB 주 자극과 대조한다."""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from same_cell_long_pulse import txt, analyze
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
INV = HERE / 'same_cell_intrinsic_inventory_result.json'
DB = HERE / 'medium_recording_lookup_result.json'
OUT = raw.CACHE / 'producer_intrinsic_waveforms'

def compare(v, i, fs, rec):
    meta = json.loads(rec['recording']['stim_meta'])
    pulses = [x['args'] for x in meta['items'] if x['type'] == 'SquarePulse' and x['args']['description'] == 'Epoch 1']
    assert len(pulses) == 1
    p = pulses[0]
    a, b = round(p['start_time'] * fs), round((p['start_time'] + p['duration']) * fs)
    assert 0 < a < b <= len(i)
    # One sample at each transition is excluded only from amplitude comparison.
    plateau = i[a+1:b-1]
    before = i[max(0, a-round(.05*fs)):a-1]
    err = float(np.max(np.abs(plateau - p['amplitude'])))
    return dict(pulse=p, start_index=a, stop_index=b, amplitude_max_error_A=err,
                amplitude_match=bool(err < 1e-15), before_command_max_abs_A=float(np.max(np.abs(before))),
                pre_50ms_median_mV=float(np.median(v[max(0,a-round(.05*fs)):a])*1000),
                last_100ms_median_mV=float(np.median(v[b-round(.1*fs):b])*1000),
                holding_current_A=rec['qc'][0]['baseline_current'])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    contract = dict(question='Do all36 producer-selected intrinsic traces match the DB main pulse amplitude and timing?',
        scope='All sweeps7..12 and90..95 on devices2,4,5. No outcome selection, no pooled early-late fit.',
        measurement='NWB conversion/offset applied to V/A arrays. DA current remains relative to holding; holding stored separately.',
        checks='Electrode, sample rate, time, units, shape, finite values; main plateau versus DB within1e-15 A excluding one boundary sample.',
        endpoint='Descriptive pre50ms and final100ms voltage medians; not independent resistance or spike classification.',
        limits='Boundary rounding is not exact edge reproduction; no historical producer environment reproduction or biological causal claim.',
        inventory_sha256=sha(INV), db_sha256=sha(DB), code_sha256=sha(Path(__file__)),
        reader_sha256=sha(Path(raw.__file__)), helper_sha256=sha(HERE/'same_cell_long_pulse.py'))
    save('intrinsic_waveforms_contract.json',contract)
    prior=json.loads(DB.read_text(encoding='utf-8'))
    db={(r['sweep'],r['device']):r for r in prior['records']}
    result_path=HERE/'intrinsic_waveforms_result.json'
    if args.verify:
        result=json.loads(result_path.read_text(encoding='utf-8'))
        assert result['contract_sha256']==sha(HERE/'intrinsic_waveforms_contract.json')
        for r in result['records']:
            path=raw.ROOT/r['array_path'];assert sha(path)==r['array_sha256']
            with np.load(path,allow_pickle=False) as z:
                assert analyze(z['voltage'],z['current'],r['rate'])==r['analysis']
                assert compare(z['voltage'],z['current'],r['rate'],db[r['sweep'],r['device']])==r['comparison']
        print('INTRINSIC_WAVEFORM_LOCAL_REPRODUCTION_PASS',len(result['records']));return
    assert not result_path.exists(),'Use --verify for completed extraction'
    selected=[r for r in json.loads(INV.read_text(encoding='utf-8'))['records'] if (r['sweep'],int(r['electrode'].split('_')[-1])) in db]
    assert len(selected)==len(db)==36
    OUT.mkdir(exist_ok=True);raw.LIMIT=128*1024*1024;rows=[]
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            for r in selected:
                hs=int(r['electrode'].split('_')[-1]);d=db[r['sweep'],hs]
                assert r['stimulus']==d['recording']['stim_name']
                target=OUT/f"{r['sweep']}_{hs}.npz";sidecar=target.with_suffix('.json')
                if target.exists() and sidecar.exists():
                    row=json.loads(sidecar.read_text());assert sha(target)==row['array_sha256']
                else:
                    assert not target.exists() and not sidecar.exists(),'Partial asset requires audit'
                    node=f[r['path']];cmd=f[f"/stimulus/presentation/data_{r['sweep']:05d}_DA{hs}"]
                    assert txt(node['electrode_name'][()][0])==txt(cmd['electrode_name'][()][0])==r['electrode']
                    assert txt(node['data'].attrs['unit'])=='V' and txt(cmd['data'].attrs['unit'])=='A'
                    assert float(node['starting_time'][()][0])==float(cmd['starting_time'][()][0])==r['start_s']
                    assert float(node['starting_time'].attrs['rate'])==float(cmd['starting_time'].attrs['rate'])==r['rate']
                    def values(ds):return np.asarray(ds[:],dtype=float)*float(ds.attrs['conversion'])+float(ds.attrs.get('offset',0))
                    v,i=values(node['data']),values(cmd['data'])
                    details=analyze(v,i,r['rate']);comparison=compare(v,i,r['rate'],d)
                    with target.open('xb') as stream:np.savez_compressed(stream,voltage=v,current=i)
                    row={**r,'device':hs,'array_path':target.relative_to(raw.ROOT).as_posix(),'array_sha256':sha(target),'analysis':details,'comparison':comparison}
                    with sidecar.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
                rows.append(row);print('cached',r['sweep'],hs,row['comparison']['amplitude_match'],flush=True)
        downloaded=reader.downloaded_this_session
    save('intrinsic_waveforms_result.json',dict(contract_sha256=sha(HERE/'intrinsic_waveforms_contract.json'),
        new_bytes=downloaded,records=rows,matched=sum(r['comparison']['amplitude_match'] for r in rows)))
    print('COMPLETE',len(rows),'new_bytes',downloaded)

if __name__=='__main__':main()
