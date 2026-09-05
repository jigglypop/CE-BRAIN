"""Fixed-window cross-transfer predictions in a metadata-selected electrical star."""
import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, OfflineRanges, raw, sha
from electrical_star_structure import predict_unseen_leaf_pairs, tetrad_products

HERE = Path(__file__).resolve().parent
CONTRACT = HERE/'electrical_star_transfer_contract.json'
OUTPUT = HERE/'electrical_star_transfer_result.json'


def save(path,value):
    with path.open('x',encoding='utf8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')


def freeze():
    protocol = json.loads((HERE/'electrical_star_protocol_result.json').read_text(encoding='utf8'))
    commands = json.loads((HERE/'electrical_star_commands_result.json').read_text(encoding='utf8'))
    assert commands['target_sweeps'] == [10,11,12,13,14,15]
    sources = ['electrical_star_protocol_result.json','electrical_star_commands_result.json',
               'allen_electrical_inventory_result.json','electrical_star_structure.py','allen_joint_inventory.py']
    contract = dict(created_utc=datetime.now(timezone.utc).isoformat(),code_sha256=sha(Path(__file__)),
        sources_sha256={name:sha(HERE/name) for name in sources},raw_reader_sha256=sha(Path(raw.__file__)),
        execution=dict(python=platform.python_version(),numpy=np.__version__,h5py=h5py.__version__,
                       executable=sys.executable,runner='.codex/hooks/python.cmd'),
        objective='Fixed neuron positions -> independently driven electrical cross-transfer -> star-specific predictions -> only after calibration, conductance and spatial metric',
        biological_model='Passive reciprocal incremental membrane/gap-junction ports with diagonal series-electrode terms; unobserved circuits remain alternatives',
        ce_mapping='Positive calibrated edge conductances would give K=sum_e c_e*d_e*d_e^T; K must not be computed as biological evidence before identification',
        selection='Experiment2771 chosen from position and manual electrical annotations; annotation may use the same experiment, so selection is not independent of all responses',
        prior_exposure='Protocol/command arrays and instrument settings only; no acquisition array values opened before this freeze',
        remote=protocol['remote'],cells=sorted(protocol['selection']['cells'],key=lambda c:c['device_id']),
        train_sweep=10,heldout_sweeps=[11,12],unopened_larger_input_sweeps=[13,14,15],
        star_devices_center_then_leaves=[4,1,2,5],star_cells_center_then_leaves=[15834,15832,15833,15835],
        fit_star_pairs='All three center-leaf pairs and leaf A-B only, average reciprocal training slopes',
        heldout_star_pairs='Leaf A-C and B-C in both directions; these pairs unused by the star fit even in training',
        comparisons=['zero nonstimulated response','unrestricted measured training Z','symmetrized training Z',
                     'cross-only star predictions for two unused leaf pairs'],
        windows_relative_onset_s=dict(baseline=[-.3,-.2],sham=[-.2,-.1],early=[.6,.7],late=[.8,.9],recovery=[1.1,1.2]),
        full_quality_interval=[0,1],expected_pulse_duration_s=1.,expected_rate_Hz=50000.,command_tolerance_pA=.05,
        quality=dict(max_source_change_mV=10.,spike_threshold_mV=-20.,max_baseline_shift_from_train_mV=5.),
        gate=dict(max_offdiagonal_rmse_ratio_to_zero=.8,required_heldout_sweeps=[11,12],
            required_star_training_signal_to_sham=3.,
            interpretation='Necessary pilot prediction checks only; two heldout sweeps do not provide animal-level uncertainty or mechanism identification'),
        limits=['Manual electrical selection is not independent anatomical validation',
                'Holding and bridge settings are recorded but not an independent access-resistance calibration',
                'Star product equality is necessary, not sufficient; a hidden common hub can pass',
                'Coupling ratio asymmetry can arise from unequal input resistances in a reciprocal circuit',
                'Tetrad equality at zero signal is uninformative; no clipping, ridge or SPD forcing',
                'Same current/voltage channels cannot provide an independent energetic endpoint'],
        claim_ceiling='BIO_EVIDENCE_L1 pilot cross-transfer; actual conductance, metric and brain structure remain unestablished')
    save(CONTRACT,contract)
    print('FROZEN',sha(CONTRACT),flush=True)


def command_mean(row,start,end):
    pieces = []
    for segment in row['segments']:
        overlap = max(0.,min(end,segment['end_s'])-max(start,segment['start_s']))
        if overlap:
            pieces.append((overlap,segment['current_pA']))
    if not np.isclose(sum(p[0] for p in pieces),end-start,rtol=0,atol=1e-8):
        raise ValueError('Command window not fully covered')
    if np.ptp([p[1] for p in pieces])>.05:
        raise ValueError('Command changes within a measurement window')
    return sum(t*v for t,v in pieces)/(end-start)


def run(fetch):
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    c = json.loads(CONTRACT.read_text(encoding='utf8'))
    assert sha(Path(__file__))==c['code_sha256']
    for name,digest in c['sources_sha256'].items():
        assert sha(HERE/name)==digest
    assert sha(Path(raw.__file__))==c['raw_reader_sha256']
    protocol = json.loads((HERE/'electrical_star_protocol_result.json').read_text(encoding='utf8'))
    commands = json.loads((HERE/'electrical_star_commands_result.json').read_text(encoding='utf8'))
    adc = {(r['sweep'],r['device']):r for r in protocol['records'] if r['kind']=='acquisition'}
    cmd = {(r['sweep'],r['device']):r for r in commands['commands']}
    devices = [cell['device_id'] for cell in c['cells']]
    n = len(devices)
    cache = BASE/'raw_ranges'/protocol['selection']['ext_id']
    manifest = json.loads((cache/'manifest.json').read_text())
    initial_bytes = sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT = c['remote']['url'],cache,initial_bytes+128*1024*1024
    sweeps = []
    with (raw.CachedRanges() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote==c['remote']
        with h5py.File(reader,'r') as f:
            for sweep in [c['train_sweep']]+c['heldout_sweeps']:
                matrices = {key:np.zeros((n,n)) for key in ['input','voltage','sham','early_to_late_drift','baseline','baseline_sd','recovery','peak']}
                onsets,qualities = [], []
                assert len({adc[sweep,d]['start'] for d in devices})==1
                for col,source in enumerate(devices):
                    pulses = [s for s in cmd[sweep,source]['segments'] if abs(s['current_pA'])>c['command_tolerance_pA'] and s['duration_s']>=.1]
                    if len(pulses)!=1 or not np.isclose(pulses[0]['duration_s'],c['expected_pulse_duration_s']):
                        raise ValueError('Expected one long rectangular source pulse')
                    onset = pulses[0]['start_s'];onsets.append(onset)
                    for row,target in enumerate(devices):
                        a = adc[sweep,target]
                        assert a['unit']=='V' and a['rate']==c['expected_rate_Hz']
                        rate = a['rate']
                        start,end = round((onset-.3)*rate),round((onset+1.2)*rate)
                        values = (np.asarray(f[a['path']+'/data'][start:end],float)*a['conversion']+a['offset'])*1000
                        assert len(values)==end-start and np.isfinite(values).all()
                        stats = {}
                        for label,(lo,hi) in c['windows_relative_onset_s'].items():
                            left,right = round((onset+lo)*rate)-start,round((onset+hi)*rate)-start
                            window = values[left:right]
                            stats[label] = (float(window.mean()),float(window.std()))
                        baseline = stats['baseline'][0]
                        matrices['voltage'][row,col] = stats['late'][0]-baseline
                        matrices['sham'][row,col] = stats['sham'][0]-baseline
                        matrices['early_to_late_drift'][row,col] = stats['late'][0]-stats['early'][0]
                        matrices['baseline'][row,col] = baseline
                        matrices['baseline_sd'][row,col] = stats['baseline'][1]
                        matrices['recovery'][row,col] = stats['recovery'][0]-baseline
                        lo,hi = [round((onset+v)*rate)-start for v in c['full_quality_interval']]
                        matrices['peak'][row,col] = float(values[lo:hi].max())
                        command = cmd[sweep,target]
                        pre = command_mean(command,onset-.3,onset-.2)
                        late = command_mean(command,onset+.8,onset+.9)
                        assert abs(command_mean(command,onset-.2,onset-.1)-pre)<=c['command_tolerance_pA']
                        assert abs(command_mean(command,onset+.6,onset+.7)-late)<=c['command_tolerance_pA']
                        matrices['input'][row,col] = late-pre
                        if row!=col:
                            assert abs(late-pre)<=c['command_tolerance_pA']
                    print('EXTRACTED',sweep,'source',source,'new_bytes',getattr(reader,'downloaded_this_session',0),flush=True)
                assert np.linalg.matrix_rank(matrices['input'])==n
                sweeps.append(dict(sweep=sweep,onsets_s=onsets,**{key:value.tolist() for key,value in matrices.items()}))
        provenance = dict(remote=reader.remote,new_download_bytes=getattr(reader,'downloaded_this_session',0),
                          cached_bytes_before=initial_bytes,blocks=reader.manifest['blocks'] if fetch else reader.used)
    z = np.linalg.solve(np.asarray(sweeps[0]['input']).T,np.asarray(sweeps[0]['voltage']).T).T*1000
    sym = (z+z.T)/2
    indices = [devices.index(d) for d in c['star_devices_center_then_leaves']]
    zstar = z[np.ix_(indices,indices)]
    fit,fit_error = None,None
    try:
        candidate = predict_unseen_leaf_pairs(zstar)
        fit = {key:value.tolist() if isinstance(value,np.ndarray) else value for key,value in candidate.items()}
    except ValueError as error:
        fit_error = str(error)
    mask = ~np.eye(4,dtype=bool)
    direct = np.zeros((4,4),bool);direct[0,1:]=True;direct[1:,0]=True
    unused = np.zeros((4,4),bool)
    for a,b in [(1,3),(3,1),(2,3),(3,2)]:unused[a,b]=True
    rms = lambda a:float(np.sqrt(np.mean(a*a)))
    ratio = lambda a,b:float(a/b) if b>0 else None
    summaries = []
    for record in sweeps:
        u,v = np.asarray(record['input']),np.asarray(record['voltage'])
        zs = np.linalg.solve(u.T,v.T).T*1000
        observed = v[np.ix_(indices,indices)]
        predictions = {'unrestricted':(z@u/1000)[np.ix_(indices,indices)],
                       'symmetric':(sym@u/1000)[np.ix_(indices,indices)]}
        result = dict(sweep=record['sweep'],measured_star_transfer_MOhm=zs[np.ix_(indices,indices)].tolist(),
            zero_star_offdiagonal_rms_mV=rms(observed[mask]),zero_direct_rms_mV=rms(observed[direct]),
            zero_unused_leaf_rms_mV=rms(observed[unused]),
            sham_star_offdiagonal_rms_mV=rms(np.asarray(record['sham'])[np.ix_(indices,indices)][mask]),
            plateau_drift_star_offdiagonal_rms_mV=rms(np.asarray(record['early_to_late_drift'])[np.ix_(indices,indices)][mask]),
            recovery_star_offdiagonal_rms_mV=rms(np.asarray(record['recovery'])[np.ix_(indices,indices)][mask]),
            reciprocity_relative_error=float(np.linalg.norm(zs-zs.T)/np.linalg.norm(zs)),
            star_cross_reciprocity_relative_error=ratio(rms((zs[np.ix_(indices,indices)]-zs[np.ix_(indices,indices)].T)[mask]),rms(zs[np.ix_(indices,indices)][mask])),
            star_tetrad_products_MOhm2=tetrad_products(zs[np.ix_(indices,indices)]).tolist(),
            all_sources_small=bool(np.all(np.abs(np.diag(v))<=c['quality']['max_source_change_mV'])),
            no_detected_pulse_spikes=bool(np.max(record['peak'])<c['quality']['spike_threshold_mV']),
            max_baseline_shift_from_train_mV=float(np.max(np.abs(np.asarray(record['baseline'])-np.asarray(sweeps[0]['baseline'])))))
        for name,predicted in predictions.items():
            error = predicted-observed
            result[name] = dict(star_offdiagonal_rmse_mV=rms(error[mask]),direct_rmse_mV=rms(error[direct]),
                unused_leaf_rmse_mV=rms(error[unused]),offdiagonal_ratio_to_zero=ratio(rms(error[mask]),rms(observed[mask])),
                prediction_star_mV=predicted.tolist())
        if fit is not None:
            matrix = np.zeros((4,4))
            matrix[1,3]=matrix[3,1]=fit['predicted_leaf_ac']
            matrix[2,3]=matrix[3,2]=fit['predicted_leaf_bc']
            prediction = matrix@u[np.ix_(indices,indices)]/1000
            result['star_unused'] = dict(rmse_mV=rms((prediction-observed)[unused]),
                ratio_to_zero=ratio(rms((prediction-observed)[unused]),rms(observed[unused])),prediction_mV=prediction.tolist())
        summaries.append(result)
    train_sham = np.asarray(sweeps[0]['sham'])[np.ix_(indices,indices)]
    train_v = np.asarray(sweeps[0]['voltage'])[np.ix_(indices,indices)]
    pairs = [(0,1),(0,2),(0,3),(1,2)]
    signal_to_sham = [ratio(rms(np.array([train_v[a,b],train_v[b,a]])),rms(np.array([train_sham[a,b],train_sham[b,a]]))) for a,b in pairs]
    quality = all(r['all_sources_small'] and r['no_detected_pulse_spikes'] and
                  r['max_baseline_shift_from_train_mV']<=c['quality']['max_baseline_shift_from_train_mV'] for r in summaries)
    limit = c['gate']['max_offdiagonal_rmse_ratio_to_zero']
    full_gate = quality and all(r['unrestricted']['offdiagonal_ratio_to_zero'] is not None and r['unrestricted']['offdiagonal_ratio_to_zero']<=limit for r in summaries[1:])
    star_gate = quality and fit is not None and all(x is not None and x>=c['gate']['required_star_training_signal_to_sham'] for x in signal_to_sham) and all(r['star_unused']['ratio_to_zero'] is not None and r['star_unused']['ratio_to_zero']<=limit for r in summaries[1:])
    result = dict(contract_sha256=sha(CONTRACT),code_sha256=sha(Path(__file__)),provenance=provenance,
        devices=devices,training_transfer_MOhm=z.tolist(),star_fit=fit,star_fit_error=fit_error,
        star_training_signal_to_sham=signal_to_sham,sweeps=sweeps,summary=summaries,
        all_quality_checks_pass=quality,full_transfer_necessary_gate=full_gate,star_prediction_necessary_gate=star_gate,
        metric_verdict='NOT_IDENTIFIED; electrode/leak/boundary and independent metric cost not calibrated',
        claim_ceiling=c['claim_ceiling'],limits=c['limits'])
    save(OUTPUT,result)
    print('DONE',json.dumps(dict(quality=quality,full_transfer_gate=full_gate,star_gate=star_gate,
        fit_error=fit_error,star_training_signal_to_sham=signal_to_sham,new_bytes=provenance['new_download_bytes'],sha256=sha(OUTPUT))),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--fetch-missing',action='store_true')
    args = parser.parse_args()
    freeze() if args.freeze else run(args.fetch_missing)
