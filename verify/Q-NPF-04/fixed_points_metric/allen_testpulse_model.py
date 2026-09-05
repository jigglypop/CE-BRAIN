"""Fixed-neuron measurement model: fit 3 test pulses, predict the next 7.

This estimates an effective clamp response, never a connection-only current.
Freeze before reading responses; old contracts and outputs are not overwritten.
"""
import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
import scipy
from scipy.optimize import minimize_scalar, nnls

from allen_joint_inventory import BASE, HERE, OfflineRanges, describe, raw, sha

CONTRACT = HERE / 'allen_testpulse_model_contract.json'
OUTPUT = HERE / 'allen_testpulse_model_result.json'
EXT = '1630015960.701'


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def freeze():
    inventory = HERE / 'allen_spatial_recordings_result.json'
    prior = json.loads(inventory.read_text(encoding='utf-8'))
    contract = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'question': 'Can a fixed passive Rs+(Rm||Cm) measurement model predict repeated common test-pulse clamp currents before connection inference?',
        'objective_chain': 'fixed cell P -> corrected V,I -> identified connection response -> spatial metric; this cycle tests the measurement correction only',
        'external_id': EXT, 'experiment_id': 4863,
        'preparation': 'mouse VisP ex vivo multipatch; same five cells; exploratory temporal prediction within one recording',
        'inventory_sha256': sha(inventory), 'remote': prior['provenance']['remote'],
        'cells': [{'cell_id': r['cell']['cell'], 'device': r['cell']['device']} for r in prior['joined']],
        'train_sweeps': [0, 1, 2], 'holdout_sweeps': list(range(3, 10)),
        'holdout_strata': {'same_holding': [3, 4], 'shifted_holding': [5, 6, 7, 8, 9]},
        'holding_metadata': 'Metadata-only audit before response extraction: sweeps 0..4 about -70 mV; 5..9 about -55 mV. Report strata separately; shifted condition is a transport test, not same-condition replication.',
        'prior_exposure': 'Sweep 0 late current and command already reported; no claim of wholly unseen source or independent biological replication',
        'baseline_s': [0.008, 0.013], 'extract_s': [0.008, 0.041],
        'evaluate_until_s': 0.040, 'edge_exclusion_s': 0.0002,
        'command_pulse_V': -0.010, 'command_tolerance_V': 1e-6,
        'duration_s': 0.010, 'duration_tolerance_s': 4e-5,
        'expected_rate_Hz': 50000.0,
        'tau_bounds_s': [0.00005, 0.030], 'tau_grid_size': 161,
        'models': ['zero connection substitution (diagnostic only)', 'positive conductance', 'positive conductance plus one passive exponential'],
        'model_equation': 'I_pA=Ginf_nS*U_mV+Gtrans_nS*(U_mV-lowpass_tau(U_mV)); baseline subtracted per sweep',
        'estimator': 'nonnegative least squares at fixed tau, train-only log-grid plus local bounded refinement; no ridge; all cells retained',
        'null_controls': 'zero response and static conductance, fitted to identical train samples; held-out offset recovery tests dynamics',
        'decision': {'maximum_rc_to_resistor_rmse_ratio': 0.8, 'maximum_rc_to_baseline_sd_ratio': 3.0,
                     'physical_fit': 'Ginf and Gtrans positive; tau interior to bounds; all five cells required',
                     'separate_decisions': 'absolute predictive adequacy and 20 percent RC improvement are separate; a sufficient resistor need not gain from RC'},
        'residual_rule': 'held-out sweeps pooled per cell within holding stratum; descriptive RMS only, not independent time-sample inference; adequacy and RC improvement reported separately for each cell and across all five',
        'revision_trigger': 'Failure is measurement-model insufficiency; do not subtract this fit to identify connections or retune on holdout',
        'identifiability': 'Common mode has rank one and cannot identify balanced connections. Rs,Rm,C are conditional effective circuit values; amplifier/dendrite/hidden circuit equivalence remains.',
        'claim_ceiling': 'BIO_EVIDENCE_L1 clamp response only; metric L0; no L2 without independent calibration/drift controls',
        'source_urls': ['https://github.com/AllenInstitute/neuroanalysis/blob/65e511681cfab5a02ac30298d287d565f385db13/neuroanalysis/test_pulse.py',
                        'https://alleninstitute.github.io/MIES/TPAnalysis_algorithm.html'],
        'code_sha256': sha(Path(__file__)),
        'dependency_sha256': {name: sha(HERE / name) for name in ['allen_joint_inventory.py']},
        'raw_reader_sha256': sha(Path(raw.__file__)),
    }
    save(CONTRACT, contract)
    print('FROZEN', CONTRACT.name, sha(CONTRACT), flush=True)


def pulse_basis(t, onset, offset, amplitude_mV, tau_s):
    """Exact causal rectangular-input response; samples at their acquisition time."""
    age_on = np.maximum(t - onset, 0.)
    age_off = np.maximum(t - offset, 0.)
    active_on = (t >= onset).astype(float)
    active_off = (t >= offset).astype(float)
    u = amplitude_mV * (active_on - active_off)
    transient = amplitude_mV * (active_on * np.exp(-age_on / tau_s)
                                - active_off * np.exp(-age_off / tau_s))
    return np.column_stack([u, transient])


def fit_rc(records, contract):
    target = np.concatenate([r['current'][r['mask']] for r in records])

    def solve(log_tau):
        tau = float(np.exp(log_tau))
        design = np.concatenate([pulse_basis(r['time'], r['onset'], r['offset'], r['amplitude_mV'], tau)[r['mask']] for r in records])
        coef, _ = nnls(design, target)
        return float(np.mean((design @ coef - target) ** 2)), coef

    bounds = np.log(contract['tau_bounds_s'])
    grid = np.linspace(*bounds, contract['tau_grid_size'])
    errors = [solve(x)[0] for x in grid]
    best = int(np.argmin(errors))
    log_tau = grid[best]
    if 0 < best < len(grid) - 1:
        opt = minimize_scalar(lambda x: solve(x)[0], bounds=(grid[best-1], grid[best+1]), method='bounded',
                              options={'xatol': 1e-10})
        if opt.success and opt.fun <= errors[best]:
            log_tau = opt.x
    mse, coef = solve(log_tau)
    u = np.concatenate([pulse_basis(r['time'], r['onset'], r['offset'], r['amplitude_mV'], np.exp(log_tau))[r['mask'], 0] for r in records])
    static = max(0., float(np.dot(u, target) / np.dot(u, u)))
    physical = bool(np.all(coef > 0) and bounds[0]+1e-6 < log_tau < bounds[1]-1e-6)
    effective = None
    if physical:
        rs = 1e9 / float(coef.sum())
        rm = 1e9 / float(coef[0]) - rs
        effective = {'Rs_MOhm': rs/1e6, 'Rm_MOhm': rm/1e6,
                     'Cm_pF': float(np.exp(log_tau) * (1/rs + 1/rm) * 1e12)}
    return {'Ginf_nS': float(coef[0]), 'Gtrans_nS': float(coef[1]), 'tau_ms': float(np.exp(log_tau)*1000),
            'static_G_nS': static, 'train_rmse_pA': float(np.sqrt(mse)), 'physical_interior': physical,
            'conditional_effective_circuit': effective, 'grid_train_mse_min': min(errors)}


def note_fields(note, device):
    if isinstance(note, bytes):
        note = note.decode()
    out = {}
    for line in str(note).split('\r'):
        prefix = f'HS#{device}:'
        if line.startswith(prefix):
            line = line[len(prefix):]
        elif line.startswith('HS#'):
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            if key in ('Epochs', 'RsComp Enable', 'RsComp Correction', 'Whole Cell Comp Enable',
                       'Fast compensation capacitance', 'Slow compensation capacitance', 'Series Resistance',
                       'Membrane Cap', 'LPF Cutoff', 'V-Clamp Holding Level', 'OperatingModeString'):
                out[key] = value.strip()
    return out


def extract(reader, c):
    records = []
    carried = {cell['device']: {} for cell in c['cells']}
    with h5py.File(reader, 'r') as f:
        for sweep in c['train_sweeps'] + c['holdout_sweeps']:
            found = {}
            for section, group in [('acquisition', 'acquisition/timeseries'), ('command', 'stimulus/presentation')]:
                for name in sorted(f[group]):
                    if not name.startswith(f'data_{sweep:05d}_'):
                        continue
                    node = f[group][name]
                    if 'electrode_name' not in node:
                        continue
                    meta = describe(node)
                    if meta['device'] not in carried:
                        continue
                    key = (section, meta['device'])
                    if key in found:
                        raise ValueError('Duplicate sweep/electrode binding')
                    found[key] = meta
            for cell in c['cells']:
                device = cell['device']
                acq, cmd = found['acquisition', device], found['command', device]
                assert (acq['unit'], cmd['unit']) == ('A', 'V')
                assert all(acq[k] == cmd[k] for k in ('start', 'rate', 'samples'))
                assert acq['rate'] == c['expected_rate_Hz']
                carried[device].update(note_fields(f[acq['path']].attrs.get('comment', ''), device))
                carried[device].update(note_fields(f[cmd['path']].attrs.get('comment', ''), device))
                fs = acq['rate']
                a, b = [round(x*fs) for x in c['extract_s']]
                time = np.arange(a, b) / fs
                baseline = (time >= c['baseline_s'][0]) & (time < c['baseline_s'][1])
                command = np.asarray(f[cmd['path']+'/data'][a:b], float) * cmd['conversion'] + cmd['offset']
                assert len(command) == b-a and np.isfinite(command).all()
                command_baseline = float(command[baseline].mean())
                command -= command_baseline
                active = np.flatnonzero(command < c['command_pulse_V']/2)
                assert len(active) > 0 and np.all(np.diff(active) == 1) and active[-1]+1 < len(time)
                onset, offset = time[active[0]], time[active[-1]+1]
                amplitude = float(command[active].mean())
                ideal = np.zeros(len(command)); ideal[active] = amplitude
                assert abs(amplitude-c['command_pulse_V']) <= c['command_tolerance_V']
                assert np.max(np.abs(command-ideal)) <= c['command_tolerance_V']
                assert abs(offset-onset-c['duration_s']) <= c['duration_tolerance_s']
                current = np.asarray(f[acq['path']+'/data'][a:b], float) * acq['conversion'] + acq['offset']
                assert len(current) == b-a and np.isfinite(current).all()
                current *= 1e12
                baseline_mean = float(current[baseline].mean())
                baseline_sd = float(current[baseline].std())
                current -= baseline_mean
                edge = c['edge_exclusion_s']
                mask = (((time >= onset+edge) & (time < offset-edge)) | (time >= offset+edge)) & (time < c['evaluate_until_s'])
                records.append({'sweep': sweep, **cell, 'time': time, 'current': current, 'mask': mask,
                                'amplitude_mV': amplitude*1000, 'onset': onset, 'offset': offset,
                                'baseline_mean_pA': baseline_mean, 'baseline_sd_pA': baseline_sd,
                                'command_baseline_V': command_baseline,
                                'metadata': dict(carried[device]), 'acquisition': acq, 'command': cmd})
            starts = [r['acquisition']['start'] for r in records if r['sweep'] == sweep]
            assert len(set(starts)) == 1
            print('EXTRACTED_SWEEP', sweep, flush=True)
    return records


def analyze(records, c):
    results = []
    for cell in c['cells']:
        rr = [r for r in records if r['device'] == cell['device']]
        train = [r for r in rr if r['sweep'] in c['train_sweeps']]
        fit = fit_rc(train, c)
        metrics = []
        accumulators = {name: {'rc': [], 'static': [], 'zero': [], 'noise': [], 'traces': []} for name in c['holdout_strata']}
        for r in rr:
            basis = pulse_basis(r['time'], r['onset'], r['offset'], r['amplitude_mV'], fit['tau_ms']/1000)
            prediction = basis @ np.array([fit['Ginf_nS'], fit['Gtrans_nS']])
            static = basis[:, 0] * fit['static_G_nS']
            mask = r['mask']
            err, serr, zerr = (prediction-r['current'])[mask], (static-r['current'])[mask], r['current'][mask]
            late = (r['time'] >= .023) & (r['time'] < .025)
            metrics.append({'sweep': r['sweep'], 'split': 'train' if r['sweep'] in c['train_sweeps'] else 'holdout',
                            'rmse_rc_pA': float(np.sqrt(np.mean(err**2))), 'rmse_resistor_pA': float(np.sqrt(np.mean(serr**2))),
                            'rmse_zero_pA': float(np.sqrt(np.mean(zerr**2))), 'baseline_sd_pA': r['baseline_sd_pA'],
                            'baseline_mean_pA': r['baseline_mean_pA'], 'late_delta_current_pA': float(r['current'][late].mean()),
                            'command_baseline_V': r['command_baseline_V'],
                            'amplitude_mV': r['amplitude_mV'], 'onset_s': r['onset'], 'offset_s': r['offset'],
                            'acquisition': r['acquisition'], 'command': r['command'], 'metadata': r['metadata']})
            if r['sweep'] in c['holdout_sweeps']:
                stratum = next(name for name, ids in c['holdout_strata'].items() if r['sweep'] in ids)
                acc = accumulators[stratum]
                acc['rc'].extend(err); acc['static'].extend(serr); acc['zero'].extend(zerr)
                acc['noise'].append(r['baseline_sd_pA']**2)
                acc['traces'].append(np.column_stack([r['current'], prediction, static]))
        holdout, traces = {}, {}
        for name, acc in accumulators.items():
            rc, resistor, zero = [float(np.sqrt(np.mean(np.square(acc[k])))) for k in ('rc', 'static', 'zero')]
            noise_rms = float(np.sqrt(np.mean(acc['noise'])))
            ratio, noise_ratio = rc/resistor, rc/noise_rms
            adequate = fit['physical_interior'] and noise_ratio <= c['decision']['maximum_rc_to_baseline_sd_ratio']
            incremental = ratio <= c['decision']['maximum_rc_to_resistor_rmse_ratio']
            holdout[name] = {'rc_rmse_pA': rc, 'resistor_rmse_pA': resistor, 'zero_rmse_pA': zero,
                             'rc_to_resistor': ratio, 'baseline_sd_rms_pA': noise_rms,
                             'rc_to_baseline_sd': noise_ratio, 'rc_prediction_adequate': bool(adequate),
                             'rc_improves_resistor': bool(incremental),
                             'resistor_prediction_adequate': bool(resistor/noise_rms <= c['decision']['maximum_rc_to_baseline_sd_ratio'])}
            mean_trace = np.mean(acc['traces'], axis=0)
            traces[name] = {'time_ms': (rr[0]['time'][::5]*1000).tolist(),
                            'mean_current_pA': mean_trace[::5, 0].tolist(), 'mean_rc_pA': mean_trace[::5, 1].tolist(),
                            'mean_resistor_pA': mean_trace[::5, 2].tolist()}
        results.append({**cell, 'fit': fit, 'sweeps': metrics, 'holdout': holdout, 'traces': traces})
    return results


def run(fetch):
    if OUTPUT.exists():
        raise FileExistsError('Preserve existing result')
    c = json.loads(CONTRACT.read_text(encoding='utf-8'))
    assert sha(Path(__file__)) == c['code_sha256']
    assert sha(HERE/'allen_spatial_recordings_result.json') == c['inventory_sha256']
    assert all(sha(HERE/name) == digest for name, digest in c['dependency_sha256'].items())
    assert sha(Path(raw.__file__)) == c['raw_reader_sha256']
    cache = BASE/'raw_ranges'/EXT
    manifest = json.loads((cache/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['remote'] == c['remote']
    raw.URL, raw.CACHE = c['remote']['url'], cache
    raw.LIMIT = sum(b['bytes'] for b in manifest['blocks'].values()) + 32*1024*1024
    with (raw.CachedRanges() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote == c['remote']
        records = extract(reader, c)
        provenance = {'remote': reader.remote, 'blocks': reader.manifest['blocks'] if fetch else reader.used,
                      'new_bytes': getattr(reader, 'downloaded_this_session', 0),
                      'cache_scope': 'existing NWB range cache, missing bytes only; no duplicate full source'}
    results = analyze(records, c)
    verdict = {name: {key: all(r['holdout'][name][key] for r in results)
                      for key in ('rc_prediction_adequate', 'resistor_prediction_adequate', 'rc_improves_resistor')}
               for name in c['holdout_strata']}
    result = {'contract_sha256': sha(CONTRACT), 'code_sha256': sha(Path(__file__)),
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'h5py': h5py.__version__},
              'provenance': provenance, 'cells': results, 'verdict': verdict,
              'metric_verdict': 'NOT_EVALUATED_COMMON_MODE_INPUT_HAS_RANK_ONE',
              'claim_ceiling': c['claim_ceiling'],
              'limitations': [c['identifiability'], c['prior_exposure'],
                              'Estimated constants include unresolved amplifier, dendrite, leak and unobserved-network effects.',
                              'Baseline subtraction uses only pre-pulse current in each holdout; no post-pulse refitting.',
                              'Descriptive repeat errors are not animal-level replication or independent sample p-values.',
                              'Fit failure is not evidence for a CE-specific residual or refutation of all fixed-point models.']}
    save(OUTPUT, result)
    print(json.dumps({'verdict': verdict, 'new_bytes': provenance['new_bytes'],
                      'cells': [{**{k:r[k] for k in ('cell_id', 'device')}, 'fit':r['fit'], 'holdout':r['holdout']} for r in results]}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--fetch-missing', action='store_true')
    args = parser.parse_args()
    freeze() if args.freeze else run(args.fetch_missing)
