"""Predict unseen IC test-pulse voltages from already fixed VC circuit fits."""
import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import HERE, BASE, OfflineRanges, describe, raw, sha

SOURCE = HERE/'allen_testpulse_model_result.json'
CONTRACT = HERE/'allen_crossclamp_contract.json'
OUTPUT = HERE/'allen_crossclamp_result.json'
EXT = '1630015960.701'


def save(path, obj):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)


def ic_prediction(time, onset, offset, amplitude_pA, rs_MOhm, rm_MOhm, cm_pF, bridge_MOhm):
    tau_s = rm_MOhm*cm_pF*1e-6
    active_on = (time >= onset).astype(float)
    active_off = (time >= offset).astype(float)
    u = amplitude_pA*(active_on-active_off)
    lowpass = amplitude_pA*(active_on*(-np.expm1(-np.maximum(time-onset, 0)/tau_s))
                           - active_off*(-np.expm1(-np.maximum(time-offset, 0)/tau_s)))
    return ((rs_MOhm-bridge_MOhm)*u+rm_MOhm*lowpass)*1e-3


def fields(note, device):
    if isinstance(note, bytes):
        note = note.decode()
    out = {}
    wanted = ('Bridge Bal Enable', 'Bridge Bal Enabled', 'Bridge Bal Value', 'Neut Cap Enable',
              'Neut Cap Enabled', 'Neut Cap Value', 'I-Clamp Holding Level', 'LPF Cutoff',
              'OperatingModeString', 'Epochs')
    for line in str(note).split('\r'):
        if line.startswith(f'HS#{device}:'):
            line = line[len(f'HS#{device}:'):]
        elif line.startswith('HS#'):
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            if key in wanted:
                out[key] = value.strip()
    return out


def freeze():
    prior = json.loads(SOURCE.read_text(encoding='utf-8'))
    parser_source = HERE.parent/'allen_synphys/qc_sources/miesnwb_pinned.py'
    save(CONTRACT, {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'question': 'Do effective passive circuit parameters inferred in VC predict IC test-pulse voltage without refitting?',
        'objective_chain': 'same fixed cell identity -> independent clamp-mode test of nuisance circuit -> only then connection inference',
        'model': 'delta V=(Rs-Rbridge)*u+Rm*LP_(RmCm)(u); known acquisition bridge compensation applied; pA*MOhm=1e-3mV',
        'ce_delta': 'none; test the physical interpretation of the measurement model before CE attribution',
        'source_sha256': sha(SOURCE), 'code_sha256': sha(Path(__file__)),
        'helper_sha256': sha(HERE/'allen_joint_inventory.py'), 'raw_reader_sha256': sha(Path(raw.__file__)),
        'bridge_parser_source_sha256': sha(parser_source),
        'bridge_parser_source': str(parser_source.relative_to(HERE.parents[2])),
        'remote': prior['provenance']['remote'],
        'cells': [{'cell_id': c['cell_id'], 'device': c['device'], 'parameters': c['fit']['conditional_effective_circuit']} for c in prior['cells']],
        'sweeps': list(range(10,16)), 'split': 'all IC sweeps are evaluation only; parameters copied from frozen VC train 0..2; no IC fitting',
        'prior_exposure': 'Metadata only examined for this analysis; earlier unrelated analyses of the source may exist; no claim of pristine external confirmation',
        'preparation': 'same five mouse VisP cells, same NWB recording, later IC TargetV acquisition',
        'baseline_s': [.008,.013], 'extract_s': [.008,.041], 'evaluate_until_s': .040,
        'edge_exclusion_s': .0002, 'expected_rate_Hz': 50000.,
        'pulse_A': -50e-12, 'amplitude_tolerance_A': 1e-14, 'duration_s': .010, 'duration_tolerance_s': 4e-5,
        'predicted_models': ['VC-derived dynamic circuit with recorded bridge', 'VC-derived quasi-static total resistance with recorded bridge', 'zero voltage change'],
        'prediction_adequacy': 'descriptive per-cell pooled RMSE <=3 times baseline SD RMS; all cells retained; not a significance level',
        'near_operating_point': 'Measured pre-pulse IC voltage within 5mV of nominal VC -70mV; report separately, no outcome exclusion',
        'noise_multiplier': 3., 'voltage_match_mV': 5., 'nominal_vc_holding_mV': -70.,
        'limits': ['Bridge values are recorded settings, not independent calibration.',
                   'IC capacitance neutralization differs by cell; transfer function not independently calibrated. Edge exclusion cannot prove its removal.',
                   'Unresolved electrode/dendrite/active conductance/current calibration may cause failure; cannot assign failure uniquely to Rm,Cm or CE.',
                   'A successful mode transfer would not identify connections from common input or prove a spatial metric.'],
        'claim_ceiling': 'BIO_EVIDENCE_L1 measurement-model transfer only; connection and metric remain L0',
    })
    print('FROZEN', CONTRACT.name, sha(CONTRACT), flush=True)


def run(fetch):
    if OUTPUT.exists():
        raise FileExistsError('Preserve prior cross-clamp result')
    c = json.loads(CONTRACT.read_text(encoding='utf-8'))
    assert sha(SOURCE)==c['source_sha256'] and sha(Path(__file__))==c['code_sha256']
    assert sha(HERE/'allen_joint_inventory.py')==c['helper_sha256']
    assert sha(Path(raw.__file__))==c['raw_reader_sha256']
    assert sha(HERE.parents[2]/c['bridge_parser_source'])==c['bridge_parser_source_sha256']
    cache = BASE/'raw_ranges'/EXT
    manifest = json.loads((cache/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['remote']==c['remote']
    raw.URL,raw.CACHE = c['remote']['url'],cache
    raw.LIMIT = sum(b['bytes'] for b in manifest['blocks'].values())+16*1024*1024
    rows=[]; carried={cell['device']:{} for cell in c['cells']}
    with (raw.CachedRanges() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote==c['remote']
        with h5py.File(reader,'r') as f:
            # Preserve changed-field semantics from the start without reading earlier responses.
            for sweep in range(max(c['sweeps'])+1):
                paired={}
                for section,group in [('acquisition','acquisition/timeseries'),('command','stimulus/presentation')]:
                    for name in sorted(f[group]):
                        if not name.startswith(f'data_{sweep:05d}_'): continue
                        node=f[group][name]
                        if 'electrode_name' not in node: continue
                        meta=describe(node); device=meta['device']
                        if device not in carried: continue
                        carried[device].update(fields(node.attrs.get('comment',''),device))
                        assert (section,device) not in paired
                        paired[section,device]=meta
                if sweep not in c['sweeps']: continue
                starts=[]
                for cell in c['cells']:
                    device=cell['device']; acq,cmd=paired['acquisition',device],paired['command',device]
                    assert (acq['unit'],cmd['unit'])==('V','A')
                    assert all(acq[k]==cmd[k] for k in ('start','rate','samples'))
                    assert acq['rate']==c['expected_rate_Hz']; starts.append(acq['start'])
                    note=carried[device]
                    enabled=note.get('Bridge Bal Enable',note.get('Bridge Bal Enabled'))
                    assert enabled in ('On','Off'), note
                    bridge=float(note['Bridge Bal Value'].split()[0]) if enabled=='On' else 0.
                    assert 'MOhm' in note['Bridge Bal Value']
                    a,b=[round(t*acq['rate']) for t in c['extract_s']]
                    time=np.arange(a,b)/acq['rate']; baseline=(time>=.008)&(time<.013)
                    u=np.asarray(f[cmd['path']+'/data'][a:b],float)*cmd['conversion']+cmd['offset']
                    assert u.size==b-a and np.isfinite(u).all(); command_baseline=float(u[baseline].mean());u-=command_baseline
                    active=np.flatnonzero(u<c['pulse_A']/2)
                    assert len(active)>0 and np.all(np.diff(active)==1) and active[-1]+1<len(time)
                    on,off=time[active[0]],time[active[-1]+1]; amp=float(u[active].mean())
                    ideal=np.zeros(len(u));ideal[active]=amp
                    assert abs(amp-c['pulse_A'])<=c['amplitude_tolerance_A']
                    assert np.max(np.abs(u-ideal))<=c['amplitude_tolerance_A']
                    assert abs(off-on-c['duration_s'])<=c['duration_tolerance_s']
                    voltage=(np.asarray(f[acq['path']+'/data'][a:b],float)*acq['conversion']+acq['offset'])*1000
                    assert voltage.size==b-a and np.isfinite(voltage).all()
                    base=float(voltage[baseline].mean());sd=float(voltage[baseline].std());voltage-=base
                    p=cell['parameters'];assert p is not None
                    prediction=ic_prediction(time,on,off,amp*1e12,p['Rs_MOhm'],p['Rm_MOhm'],p['Cm_pF'],bridge)
                    static=ideal*1e12*(p['Rs_MOhm']+p['Rm_MOhm']-bridge)*1e-3
                    edge=c['edge_exclusion_s']
                    mask=(((time>=on+edge)&(time<off-edge))|(time>=off+edge))&(time<c['evaluate_until_s'])
                    rms=lambda x:float(np.sqrt(np.mean(x[mask]**2)))
                    rows.append({'sweep':sweep,'cell_id':cell['cell_id'],'device':device,'bridge_MOhm':bridge,
                                 'baseline_voltage_mV':base,'baseline_sd_mV':sd,'command_baseline_A':command_baseline,
                                 'amplitude_pA':amp*1e12,'onset_s':float(on),'offset_s':float(off),
                                 'near_operating_point':abs(base-c['nominal_vc_holding_mV'])<=c['voltage_match_mV'],
                                 'rc_rmse_mV':rms(prediction-voltage),'static_rmse_mV':rms(static-voltage),'zero_rmse_mV':rms(voltage),
                                 'n_evaluated':int(mask.sum()),'metadata':dict(note),'acquisition':acq,'command':cmd,
                                 'trace':{'time_ms':(time[::5]*1000).tolist(),'voltage_mV':voltage[::5].tolist(),
                                          'rc_mV':prediction[::5].tolist(),'static_mV':static[::5].tolist()}})
                assert len(set(starts))==1
                print('EVALUATED_IC_SWEEP',sweep,flush=True)
        provenance={'remote':reader.remote,'blocks':reader.manifest['blocks'] if fetch else reader.used,
                    'new_bytes':getattr(reader,'downloaded_this_session',0)}
    summary=[]
    for cell in c['cells']:
        selected=[r for r in rows if r['device']==cell['device']]
        strata={}
        for name,rr in [('all',selected),('near_nominal_vc_holding',[r for r in selected if r['near_operating_point']])]:
            if not rr:
                strata[name]={'sweeps':0,'evaluated':False};continue
            rms=lambda key:float(np.sqrt(np.average([r[key]**2 for r in rr],weights=[r['n_evaluated'] for r in rr])))
            noise=rms('baseline_sd_mV');error=rms('rc_rmse_mV')
            strata[name]={'sweeps':len(rr),'evaluated':True,'rc_rmse_mV':error,'static_rmse_mV':rms('static_rmse_mV'),
                           'zero_rmse_mV':rms('zero_rmse_mV'),'baseline_sd_rms_mV':noise,'error_to_noise':error/noise,
                           'prediction_adequate':error<=c['noise_multiplier']*noise,
                           'baseline_voltage_range_mV':[min(r['baseline_voltage_mV'] for r in rr),max(r['baseline_voltage_mV'] for r in rr)]}
        summary.append({'cell_id':cell['cell_id'],'device':cell['device'],'strata':strata})
    out={'contract_sha256':sha(CONTRACT),'code_sha256':sha(Path(__file__)),'source_sha256':sha(SOURCE),
         'environment':{'python':platform.python_version(),'numpy':np.__version__,'h5py':h5py.__version__},
         'provenance':provenance,'summary':summary,'records':rows,'claim_ceiling':c['claim_ceiling'],'limits':c['limits'],
         'metric_verdict':'NOT_EVALUATED','fit_parameters_updated':False}
    save(OUTPUT,out)
    print(json.dumps({'summary':summary,'new_bytes':provenance['new_bytes']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--fetch-missing',action='store_true')
    args=parser.parse_args()
    freeze() if args.freeze else run(args.fetch_missing)
