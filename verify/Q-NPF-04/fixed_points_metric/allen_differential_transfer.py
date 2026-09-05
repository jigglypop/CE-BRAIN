"""Fixed-window cross-cell current-to-voltage transfer; no inferred metric."""
import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import HERE, BASE, OfflineRanges, describe, raw, sha

CONTRACT=HERE/'allen_differential_transfer_contract.json'
OUTPUT=HERE/'allen_differential_transfer_result.json'
SOURCE=HERE/'allen_spatial_recordings_result.json'
EXT='1630015960.701'


def save(path,obj):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(obj,stream,ensure_ascii=False,indent=2,allow_nan=False)


def estimate_transfer(input_pA, voltage_mV):
    if np.linalg.matrix_rank(input_pA)!=input_pA.shape[0]:
        raise ValueError('Input does not identify a full transfer matrix')
    return np.linalg.solve(input_pA.T,voltage_mV.T).T*1000


def offdiagonal_errors(prediction, diagonal_prediction, voltage):
    mask=~np.eye(voltage.shape[0],dtype=bool)
    rms=lambda x:float(np.sqrt(np.mean(x*x)))
    full=rms((prediction-voltage)[mask]);diagonal=rms((diagonal_prediction-voltage)[mask])
    return full,diagonal,full/diagonal if diagonal else None


def freeze():
    source=json.loads(SOURCE.read_text(encoding='utf-8'))
    cells=sorted([{'cell_id':r['cell']['cell'],'device':r['cell']['device'],'position_m':r['cell']['position']} for r in source['joined']],key=lambda r:r['device'])
    save(CONTRACT,{
        'created_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':sha(Path(__file__)),
        'execution':{'python':platform.python_version(),'executable':sys.executable,'numpy':np.__version__,'h5py':h5py.__version__,
                     'runner':'.codex/hooks/python.cmd','runner_sha256':sha(HERE.parents[2]/'.codex/hooks/python.cmd')},
        'source_sha256':sha(SOURCE),'helper_sha256':sha(HERE/'allen_joint_inventory.py'),'raw_reader_sha256':sha(Path(raw.__file__)),
        'question':'Do independently injected small currents identify reproducible cross-cell voltage transfer at fixed neuronal positions?',
        'objective_chain':'fixed P -> independent current basis -> observed cross-cell voltage operator -> only if identified, assess mechanism and spatial metric',
        'preparation':'same five mouse VisP cells, IC TargetV sweeps 10..15, NWB 1630015960.701',
        'remote':source['provenance']['remote'],'cells':cells,
        'train_sweep':10,'signed_holdout_sweeps':[11,12],'extrapolation_sweeps':[13,14,15],
        'onsets_s':[.741660,2.641660,4.541660,6.441660,8.341660],'duration_s':1.,
        'windows_relative_onset_s':{'baseline':[-.3,-.2],'sham':[-.2,-.1],'late_early':[.6,.7],'late':[.8,.9]},
        'input_scope':'Pulse epochs and sparse command values inspected before voltage responses. Actual five-channel command vectors averaged in all windows, not rounded metadata amplitudes.',
        'model':'V_mV=1e-3*Z_MOhm*I_pA; columns are stimulated cells, rows measured cells. Z is a specified-window effective transfer, not an anatomical adjacency or a steady state unless plateau checked.',
        'ce_delta':'Off-diagonal effective transfer over diagonal-only response; mechanistic/metric interpretation deferred',
        'comparators':['full Z from sweep10','diagonal-only Z from same training','zero response on nonstimulated cells','pre-stimulus sham change'],
        'command_tolerance_pA':.05,'expected_rate_Hz':50000.,
        'small_input_checks':{'maximum_source_late_change_mV':10.,'spike_flag_voltage_mV':-20.},
        'decision':{'offdiagonal_rmse_ratio_max':.8,'required_signed_sweeps':[11,12],
                    'interpretation':'20 percent lower nonstimulated RMSE than diagonal-only prediction in EACH signed holdout is necessary for predictive cross-cell support; zero is a separate comparator; plateau, drift, quality and calibration remain separate gates'},
        'uncertainty':'Per-pulse and per-sweep descriptive errors; baseline sample SD and sham changes are technical comparators, not independent animal inference or p-values.',
        'falsifier':'No off-diagonal holdout improvement, unresolved input rank, non-small/spiking response or drifting plateau prevents connection inference from this candidate.',
        'limits':['Hyperpolarizing subthreshold currents need not engage chemical synapses; null transfer does not mean no synaptic connection.',
                  'Common reference, stimulation crosstalk, drift and hidden neurons can produce off-diagonal voltage changes.',
                  'Own-cell voltage includes membrane and electrode effects; off-diagonal response is an observation, not calibrated synaptic conductance.',
                  'Six sweeps of one recording are not independent animals; no SPD forcing, inversion into a metric, or graph reconstruction.'],
        'claim_ceiling':'BIO_EVIDENCE_L1 specified-window transfer only; mechanism, metric and whole-brain structure unestablished',
    })
    print('FROZEN',CONTRACT.name,sha(CONTRACT),flush=True)


def run(fetch):
    if OUTPUT.exists():raise FileExistsError('Preserve transfer result')
    c=json.loads(CONTRACT.read_text(encoding='utf-8'))
    assert sha(Path(__file__))==c['code_sha256'] and sha(SOURCE)==c['source_sha256']
    assert sha(HERE/'allen_joint_inventory.py')==c['helper_sha256'] and sha(Path(raw.__file__))==c['raw_reader_sha256']
    cache=BASE/'raw_ranges'/EXT;manifest=json.loads((cache/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['remote']==c['remote'];raw.URL,raw.CACHE=c['remote']['url'],cache
    raw.LIMIT=sum(b['bytes'] for b in manifest['blocks'].values())+64*1024*1024
    sweep_results=[]
    with (raw.CachedRanges() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote==c['remote']
        with h5py.File(reader,'r') as f:
            for sweep in [c['train_sweep']]+c['signed_holdout_sweeps']+c['extrapolation_sweeps']:
                paired={}
                for section,group in [('acquisition','acquisition/timeseries'),('command','stimulus/presentation')]:
                    for name in sorted(f[group]):
                        if not name.startswith(f'data_{sweep:05d}_'):continue
                        node=f[group][name]
                        if 'electrode_name' not in node:continue
                        meta=describe(node)
                        key=(section,meta['device']);assert key not in paired;paired[key]=meta
                matrices={name:np.zeros((5,5)) for name in ('input','voltage','sham','plateau_drift','baseline_sd','baseline_voltage')}
                records=[]
                for column,(source_cell,onset) in enumerate(zip(c['cells'],c['onsets_s'])):
                    for row,cell in enumerate(c['cells']):
                        acq,cmd=paired['acquisition',cell['device']],paired['command',cell['device']]
                        assert (acq['unit'],cmd['unit'])==('V','A')
                        assert all(acq[k]==cmd[k] for k in ('start','rate','samples'))
                        assert acq['rate']==c['expected_rate_Hz']
                        stats={}
                        for label,(lo,hi) in c['windows_relative_onset_s'].items():
                            a,b=[round((onset+x)*acq['rate']) for x in (lo,hi)]
                            values={}
                            for kind,meta,scale in [('voltage',acq,1000.),('current',cmd,1e12)]:
                                x=(np.asarray(f[meta['path']+'/data'][a:b],float)*meta['conversion']+meta['offset'])*scale
                                assert x.size==b-a and np.isfinite(x).all()
                                values[kind]={'mean':float(x.mean()),'sd':float(x.std()),'min':float(x.min()),'max':float(x.max())}
                            stats[label]=values
                        delta_u=stats['late']['current']['mean']-stats['baseline']['current']['mean']
                        assert max(stats[name]['current']['sd'] for name in stats)<=c['command_tolerance_pA']
                        assert abs(stats['sham']['current']['mean']-stats['baseline']['current']['mean'])<=c['command_tolerance_pA']
                        assert abs(stats['late_early']['current']['mean']-stats['late']['current']['mean'])<=c['command_tolerance_pA']
                        if row!=column:assert abs(delta_u)<=c['command_tolerance_pA']
                        else:assert abs(delta_u)>c['command_tolerance_pA']
                        matrices['input'][row,column]=delta_u
                        matrices['voltage'][row,column]=stats['late']['voltage']['mean']-stats['baseline']['voltage']['mean']
                        matrices['sham'][row,column]=stats['sham']['voltage']['mean']-stats['baseline']['voltage']['mean']
                        matrices['plateau_drift'][row,column]=stats['late']['voltage']['mean']-stats['late_early']['voltage']['mean']
                        matrices['baseline_sd'][row,column]=stats['baseline']['voltage']['sd']
                        matrices['baseline_voltage'][row,column]=stats['baseline']['voltage']['mean']
                        quality=None
                        if row==column:
                            a,b=[round(x*acq['rate']) for x in (onset,onset+c['duration_s'])]
                            pulse=(np.asarray(f[acq['path']+'/data'][a:b],float)*acq['conversion']+acq['offset'])*1000
                            assert pulse.size==b-a and np.isfinite(pulse).all()
                            quality={'minimum_voltage_mV':float(pulse.min()),'maximum_voltage_mV':float(pulse.max()),
                                     'spike_threshold_crossed':bool(pulse.max()>=c['small_input_checks']['spike_flag_voltage_mV']),
                                     'source_late_change_small':bool(abs(matrices['voltage'][row,column])<=c['small_input_checks']['maximum_source_late_change_mV'])}
                        records.append({'source_device':source_cell['device'],'target_device':cell['device'],'onset_s':onset,
                                        'stats':stats,'source_quality':quality,'acquisition':acq,'command':cmd})
                assert len({r['acquisition']['start'] for r in records})==1
                sweep_results.append({'sweep':sweep,**{k+'_matrix':v.tolist() for k,v in matrices.items()},'records':records,
                                      'input_rank':int(np.linalg.matrix_rank(matrices['input'])),
                                      'input_condition_number':float(np.linalg.cond(matrices['input']))})
                print('EXTRACTED_DIFFERENTIAL_SWEEP',sweep,flush=True)
        provenance={'remote':reader.remote,'blocks':reader.manifest['blocks'] if fetch else reader.used,
                    'new_bytes':getattr(reader,'downloaded_this_session',0)}
    train=sweep_results[0];z=estimate_transfer(np.array(train['input_matrix']),np.array(train['voltage_matrix']))
    diag=np.diag(np.diag(z));off=~np.eye(5,dtype=bool);results=[]
    rms=lambda x:float(np.sqrt(np.mean(x*x)))
    for r in sweep_results:
        u,v=np.array(r['input_matrix']),np.array(r['voltage_matrix'])
        prediction=z@u*1e-3;diagonal=diag@u*1e-3;sham=np.array(r['sham_matrix'])
        zero=rms(v[off]);error,diag_error,ratio=offdiagonal_errors(prediction,diagonal,v)
        quality=[x['source_quality'] for x in r['records'] if x['source_quality'] is not None]
        result={'sweep':r['sweep'],'full_rmse_mV':rms(prediction-v),'diagonal_rmse_mV':rms(diagonal-v),
                'nonstimulated_full_rmse_mV':error,'nonstimulated_zero_rmse_mV':zero,
                'nonstimulated_diagonal_rmse_mV':diag_error,'nonstimulated_rmse_ratio':ratio,
                'nonstimulated_sham_rms_mV':rms(sham[off]),
                'nonstimulated_baseline_sd_rms_mV':rms(np.array(r['baseline_sd_matrix'])[off]),
                'nonstimulated_plateau_drift_rms_mV':rms(np.array(r['plateau_drift_matrix'])[off]),
                'all_source_late_changes_small':all(x['source_late_change_small'] for x in quality),
                'any_source_spike_threshold_crossed':any(x['spike_threshold_crossed'] for x in quality),
                'full_prediction_mV':prediction.tolist(),'diagonal_prediction_mV':diagonal.tolist()}
        results.append(result)
    holdout=[r for r in results if r['sweep'] in c['signed_holdout_sweeps']]
    predictive=all(r['nonstimulated_rmse_ratio'] is not None and r['nonstimulated_rmse_ratio']<=c['decision']['offdiagonal_rmse_ratio_max'] for r in holdout)
    quality=all(r['all_source_late_changes_small'] and not r['any_source_spike_threshold_crossed'] for r in results if r['sweep'] in [10,11,12])
    out={'contract_sha256':sha(CONTRACT),'code_sha256':sha(Path(__file__)),'provenance':provenance,
         'transfer_MOhm':z.tolist(),'rows_target_devices':[x['device'] for x in c['cells']],
         'columns_source_devices':[x['device'] for x in c['cells']],
         'sweeps':sweep_results,'summary':results,
         'necessary_predictive_gate':predictive,'source_small_signal_checks_pass':quality,
         'verdict':'NECESSARY_PREDICTIVE_GATE_PASS_NOT_MECHANISM' if predictive and quality else 'CROSS_CELL_TRANSFER_NOT_ESTABLISHED',
         'metric_verdict':'NOT_EVALUATED','claim_ceiling':c['claim_ceiling'],'limits':c['limits']}
    save(OUTPUT,out)
    print(json.dumps({'verdict':out['verdict'],'new_bytes':provenance['new_bytes'],'transfer_MOhm':z.tolist(),
                      'summary':[{k:v for k,v in r.items() if 'prediction_mV' not in k} for r in results]}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--fetch-missing',action='store_true')
    args=parser.parse_args();freeze() if args.freeze else run(args.fetch_missing)
