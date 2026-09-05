"""저장된 원본 대응과 추출 배열을 네트워크 없이 대조한다."""
import hashlib
import json
from datetime import datetime,timedelta
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    mapping=json.loads((HERE/'raw_sweep_map_result.json').read_text(encoding='utf-8'))
    clock=json.loads((HERE/'raw_clock_audit_result.json').read_text(encoding='utf-8'))
    merged={}
    for e in clock['entries']:
        dst=merged.setdefault(e['sweep'],{})
        for key,values in e['values'].items():
            target=dst.setdefault(key,[None]*9)
            for i,v in enumerate(values):
                if v is not None:target[i]=v
    checks=[]
    for row in mapping['rows']:
        hs=row['headstage'];vals=merged[row['sweep']]
        mode=vals['Clamp Mode'][hs]
        holding=vals['V-Clamp Holding Level'][hs]
        carried=float(row['metadata']['V-Clamp Holding Level'].split()[0])
        checks.append({'sweep':row['sweep'],'headstage':hs,'clamp_matches':(mode==0)==(row['unit']=='A'),
            'holding_note_mV':carried,'holding_notebook_mV':holding,
            'holding_agrees_to_printed_precision':holding is not None and abs(holding-carried)<=.006})
    times=[]
    start=datetime.fromisoformat(mapping['session_start_utc'].replace('Z','+00:00')).replace(tzinfo=None)
    for sw,vals in sorted(merged.items()):
        row=next(r for r in mapping['rows'] if r['sweep']==sw)
        notebook=datetime(1904,1,1)+timedelta(seconds=vals['TimeStamp'][0])
        hdf_local=start+timedelta(seconds=row['start_s'],hours=-8)
        times.append({'sweep':sw,'notebook_naive':notebook.isoformat(),'hdf_start_minus8h':hdf_local.isoformat(),
            'notebook_minus_hdf_s':(notebook-hdf_local).total_seconds(),'waveform_duration_s':row['samples']/row['rate']})
    expected=json.loads((HERE/'raw_binding_validation.json').read_text(encoding='utf-8'))
    assert expected['checks']==checks and expected['clocks']==times
    assert all(c['clamp_matches'] for c in checks)
    assert all(c['holding_agrees_to_printed_precision'] for c in checks if c['holding_notebook_mV'] is not None)
    result=json.loads((HERE/'raw_pulse_windows_result.json').read_text(encoding='utf-8'))
    contract=HERE/'raw_pulse_windows_contract.json'
    assert hashlib.sha256(contract.read_bytes()).hexdigest()==result['contract_sha256']
    spec=json.loads(contract.read_text(encoding='utf-8'))
    assert hashlib.sha256((HERE/'raw_pulse_windows.py').read_bytes()).hexdigest()==spec['code_sha256']
    assert hashlib.sha256((HERE/'raw_sweep_map_result.json').read_bytes()).hexdigest()==spec['mapping_sha256']
    archive=HERE.parents[2]/result['array_archive']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==result['array_sha256']
    with np.load(archive,allow_pickle=False) as arrays:
        for row in result['records']:
            fs=row['rate_hz'];before=round(.010*fs)
            assert all(c['holding_agrees_to_printed_precision'] for c in checks if c['sweep']==row['sweep'])
            for e in row['events']:
                for name in ('pre','post','command'):
                    values=arrays[f'sweep{row["sweep"]}_pulse{e["pulse"]}_{name}']
                    scale=1e3 if name=='command' else 1e12
                    difference=(values[before+round(.002*fs):before+round(.005*fs)].mean()-values[:round(.007*fs)].mean())*scale
                    assert np.isclose(difference,e[name]['response_minus_baseline'],rtol=1e-12,atol=1e-12)
    print('RAW_BINDING_PASS: clamp20/20, available holding14/14, selected180 array summaries and hashes match; absolute clocks remain distinct')


if __name__=='__main__':main()
