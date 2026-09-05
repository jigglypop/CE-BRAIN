"""VC command and instrument-metadata eligibility; never opens ADC data."""
import argparse
import json
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, OfflineRanges, raw, sha, text

HERE = Path(__file__).resolve().parent
OUTPUT = HERE/'electrical_star_vc_inputs_result.json'
DEVICES = [0,1,2,4,5,6,7]


def settings(comment, device):
    result = {}
    prefix = f'HS#{device}:'
    for line in str(comment).split('\r'):
        if line.startswith(prefix):
            key,separator,value = line[len(prefix):].partition(':')
            if separator and any(token in key for token in ['Holding','Bridge','Series','Cap','Comp','Resistance','LPF','Clamp','OperatingMode']):
                result[key] = value.strip()
    return result


def compress(values, rate):
    cuts = np.r_[0,np.flatnonzero(np.abs(np.diff(values))>.005)+1,len(values)]
    return [dict(start_s=float(a/rate),end_s=float(b/rate),duration_s=float((b-a)/rate),
                 command_mV=float(np.mean(values[a:b])),sd_mV=float(np.std(values[a:b])))
            for a,b in zip(cuts[:-1],cuts[1:])]


def rank_summary(matrix):
    singular = np.linalg.svd(matrix,compute_uv=False)/np.sqrt(matrix.shape[1])
    threshold = max(1e-6,1e-6*singular[0])
    return dict(singular_rms_mV=singular.tolist(),rank=int(np.sum(singular>threshold)),threshold_mV=float(threshold))


def main(fetch):
    if OUTPUT.exists(): raise FileExistsError(OUTPUT)
    protocol_path = HERE/'electrical_star_protocol_result.json'
    protocol = json.loads(protocol_path.read_text(encoding='utf8'))
    cache = BASE/'raw_ranges'/protocol['selection']['ext_id']
    manifest = json.loads((cache/'manifest.json').read_text())
    initial = sum(block['bytes'] for block in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT = protocol['remote']['url'],cache,initial+32*1024*1024
    records = {(r['kind'],r['sweep'],r['device']):r for r in protocol['records']}
    outputs = []
    with (raw.CachedRanges() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote == protocol['remote']
        with h5py.File(reader,'r') as f:
            for sweep in range(10):
                inputs,descriptions = [],[]
                for device in DEVICES:
                    command = records['command',sweep,device]
                    adc = records['acquisition',sweep,device]
                    assert command['unit']=='V' and adc['unit']=='A'
                    assert all(command[key]==adc[key] for key in ['samples','rate','start'])
                    assert command['rate']==50000
                    # This is the only waveform read; it is a stimulus, never an acquisition.
                    assert command['path'].startswith('/stimulus/presentation/')
                    node = f[command['path']]
                    values = (np.asarray(node['data'][()],float)*command['conversion']+command['offset'])*1000
                    assert np.isfinite(values).all()
                    baseline = float(np.median(values[:100]))
                    inputs.append(values-baseline)
                    adc_node = f[adc['path']]
                    descriptions.append(dict(device=device,baseline_command_mV=baseline,
                        acquisition_path=adc['path'],command_path=command['path'],
                        command_segments=compress(values,command['rate']),
                        incremental_instrument_settings=settings(text(adc_node.attrs.get('comment','')),device)))
                inputs = np.asarray(inputs)
                after = inputs[:,2500:]  # After the initial test pulse: t >= 50 ms.
                nonzero = np.abs(after)>.005
                solo = np.sum(nonzero,axis=0)==1
                outputs.append(dict(sweep=sweep,devices=descriptions,all_time=rank_summary(inputs),
                    after_50ms=rank_summary(after),peak_command_change_mV=np.max(np.abs(inputs),axis=1).tolist(),
                    peak_after_50ms_mV=np.max(np.abs(after),axis=1).tolist(),
                    exactly_one_driven_duration_s_by_device=[float(np.sum(solo & nonzero[i])/50000) for i in range(7)],
                    max_deviation_from_common_command_mV=float(np.max(np.abs(inputs-inputs[0])))))
                print('COMMAND_ELIGIBILITY',sweep,'rank',outputs[-1]['all_time']['rank'],
                      'after_50ms',outputs[-1]['after_50ms']['rank'],flush=True)
        provenance = dict(remote=reader.remote,initial_cached_bytes=initial,
            new_download_bytes=getattr(reader,'downloaded_this_session',0),
            blocks=reader.manifest['blocks'] if fetch else reader.used)
    result = dict(code_sha256=sha(Path(__file__)),protocol_sha256=sha(protocol_path),
        metadata_reader_sha256=sha(HERE/'allen_joint_inventory.py'),raw_reader_sha256=sha(Path(raw.__file__)),
        scope='Only command waveforms for VC sweeps 0..9 and acquisition attributes; no ADC data opened',
        question='Are independent source voltage perturbations available for electrical cross-current identification?',
        devices=DEVICES,sweeps=outputs,provenance=provenance,
        limitations=['Command changes exclude notebook holding, which must be separately reconstructed',
            'Incremental instrument comments are not independent series-resistance or capacitance calibration',
            'Command rank is input eligibility only, not a biological metric or conductance measurement'],
        claim_ceiling='BIO_EVIDENCE_L0 input eligibility')
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE',json.dumps(dict(new_bytes=provenance['new_download_bytes'],sha256=sha(OUTPUT))),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fetch-missing',action='store_true')
    main(parser.parse_args().fetch_missing)
