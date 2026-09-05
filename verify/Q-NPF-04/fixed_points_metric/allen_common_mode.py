"""첫 시행의 공통 시험 펄스가 닫힌 연결 전류 가정과 맞는지 관측한다."""
import json
from pathlib import Path
import h5py
import numpy as np
from allen_joint_inventory import HERE, BASE, OfflineRanges, sha


def main():
    inventory = HERE/'allen_spatial_recordings_result.json'
    prior = json.loads(inventory.read_text(encoding='utf-8'))
    rows = sorted(prior['joined'],key=lambda r:r['cell']['device'])
    assert len(rows)==5 and all(r['mode']=='vc' and r['acquisition']['sweep']==0 for r in rows)
    # 메타데이터 시험 펄스 [0.0158308,0.0258292) 안팎에 고정한다.
    windows = {'baseline':[.008,.013],'pulse_late':[.023,.025]}
    records = []
    with OfflineRanges(BASE/'raw_ranges/1630015960.701') as reader:
        with h5py.File(reader,'r') as f:
            for row in rows:
                record = {'cell_id':row['cell']['cell'],'device':row['cell']['device']}
                for kind in ('acquisition','command'):
                    meta = row[kind]
                    node = f[meta['path']+'/data']
                    stats = {}
                    for name,(start,stop) in windows.items():
                        a,b = round(start*meta['rate']),round(stop*meta['rate'])
                        values = np.asarray(node[a:b],dtype=float)*meta['conversion']+meta['offset']
                        assert values.size==b-a and np.isfinite(values).all()
                        stats[name] = {'samples':len(values),'mean':float(values.mean()),'sd':float(values.std()),
                                       'minimum':float(values.min()),'maximum':float(values.max())}
                    stats['delta'] = stats['pulse_late']['mean']-stats['baseline']['mean']
                    record[kind] = stats
                records.append(record)
        provenance = {'remote':reader.remote,'used_blocks':reader.used,'new_bytes':0}
    voltage = np.array([r['command']['delta'] for r in records])
    current = np.array([r['acquisition']['delta'] for r in records])
    summary = {'devices':[r['device'] for r in records],'delta_command_mV':(voltage*1000).tolist(),
               'delta_clamp_current_pA':(current*1e12).tolist(),'sum_delta_clamp_current_pA':float(current.sum()*1e12),
               'command_common_mode_residual_V':float(np.max(np.abs(voltage-voltage.mean()))),
               'baseline_current_sd_pA':[r['acquisition']['baseline']['sd']*1e12 for r in records]}
    result = {'code_sha256':sha(Path(__file__)),'inventory_sha256':sha(inventory),
              'offline_reader_sha256':sha(HERE/'allen_joint_inventory.py'),'windows_s':windows,
              'records':records,'summary':summary,'provenance':provenance,
              'model_comparison':'For the ideal closed balanced Y, Y*1=0 and 1^T*Y=0. Uniform actual voltage changes predict zero connection current changes; any voltage predicts zero net connection current.',
              'scope':'Exploratory measurement-model check in one preselected sweep, not a statistical mechanism-intervention experiment',
              'limits':['Commands are not access-corrected membrane voltage',
                        'Measured clamp current includes leak, capacitive and unobserved-circuit terms',
                        'Baseline SD is descriptive; temporal correlation and trial uncertainty not used for a p-value',
                        'Nonzero clamp response does not refute a corrected connection-only metric or the overall fixed-point hypothesis'],
              'claim_ceiling':'BIO_EVIDENCE_L1_CLAMP_RESPONSE_ONLY; metric remains L0'}
    with (HERE/'allen_common_mode_result.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps(summary))


if __name__=='__main__':
    main()
