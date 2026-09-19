"""Development comparison: fit VC 0..2, predict VC strata and IC without refit."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy

import passive_port_model as model

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(arrays_path, metadata_path, output):
    if output.exists():
        raise FileExistsError('Preserve the prior comparison: ' + str(output))
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    assert sha(arrays_path) == metadata['npz']['sha256']
    assert metadata['definition']['rows'] == 80
    for relative, pin in metadata['input_pins'].items():
        assert sha(ROOT / relative) == pin['sha256'], relative
    with np.load(arrays_path, allow_pickle=False) as archive:
        a = {key: archive[key] for key in archive.files}
    assert a['time_s'].shape == a['response_SI'].shape == (80, 1650)
    assert np.all(a['rate_Hz'] == 50000)
    identity = list(zip(a['mode'].tolist(), a['sweep'].tolist(), a['device'].tolist()))
    assert len(set(identity)) == len(identity)
    for j, row in enumerate(metadata['rows']):
        assert row['row'] == j
        assert identity[j] == (row['mode'], row['sweep'], row['device'])
        assert int(a['cell_id'][j]) == row['cell_id']
    output.mkdir(parents=True)
    predictions = np.full((2, 80, 1650), np.nan)
    fits, scores = [], []
    for device in sorted(set(a['device'].tolist())):
        train_rows = np.flatnonzero((a['device'] == device) & (a['mode'] == 'VC') & (a['sweep'] <= 2))
        assert a['sweep'][train_rows].tolist() == [0, 1, 2]
        records = [{'time': a['time_s'][j], 'current': a['response_SI'][j]*1e12,
                    'mask': a['eval_mask'][j], 'onset': a['onset_s'][j],
                    'offset': a['offset_s'][j], 'amplitude_mV': a['amplitude_SI'][j]*1000}
                   for j in train_rows]
        for order in (1, 2):
            fit = model.fit_vc(records, order)
            fit.update(device=int(device), cell_id=int(a['cell_id'][train_rows[0]]),
                       train_rows=train_rows.tolist())
            fits.append(fit)
            print(json.dumps({'event': 'FIT', **fit}), flush=True)
            if not fit['positive_dc']:
                fit['status'] = 'NONPOSITIVE_DC_NO_STABLE_IC_INVERSE'
                continue
            fit['status'] = 'FITTED'
            params = (fit['g0_nS'], fit['conductance_nS'], fit['tau_s'])
            modes = model.impedance_modes(*params)
            fit['inverse_modes'] = {key: value.tolist() if isinstance(value, np.ndarray) else value
                                    for key, value in modes.items()}
            fit['tau_ratio'] = float(max(fit['tau_s']) / min(fit['tau_s']))
            design = np.concatenate([model.vc_basis(r['time'], r['onset'], r['offset'],
                                                   r['amplitude_mV'], fit['tau_s'])[r['mask']]
                                     for r in records])
            fit['coefficient_design_condition_number'] = float(np.linalg.cond(design))
            for j in np.flatnonzero(a['device'] == device):
                vc = a['mode'][j] == 'VC'
                factor = 1e12 if vc else 1000
                args = (a['time_s'][j], a['onset_s'][j], a['offset_s'][j],
                        a['amplitude_SI'][j] * (1000 if vc else 1e12), *params)
                if vc:
                    prediction = model.vc_prediction(*args)
                else:
                    prediction = model.ic_prediction(*args, bridge_MOhm=a['bridge_MOhm'][j])
                assert np.isfinite(prediction).all()
                predictions[order-1, j] = prediction
                mask = a['eval_mask'][j]
                error = (prediction - a['response_SI'][j]*factor)[mask]
                baseline_sd = a['baseline_sd_SI'][j]*factor
                rmse = float(np.sqrt(np.mean(error**2)))
                sweep = int(a['sweep'][j])
                group = ('VC_train' if sweep <= 2 else 'VC_same_holding' if sweep <= 4
                         else 'VC_shifted_holding' if sweep <= 9 else 'IC_all')
                scores.append({'row': int(j), 'order': order, 'device': int(device),
                               'cell_id': int(a['cell_id'][j]), 'sweep': sweep, 'group': group,
                               'units': 'pA' if vc else 'mV', 'n': int(mask.sum()),
                               'rmse': rmse, 'bias': float(error.mean()),
                               'baseline_sd': float(baseline_sd), 'error_to_noise': rmse/baseline_sd,
                               'original_rc_rmse': metadata['rows'][j]['saved_rc_rmse_display_unit'],
                               'near_vc_holding': None if vc else bool(abs(a['baseline_mean_SI'][j]+.070) <= .005),
                               'compensated_direct_resistance_mV_per_pA': None if vc else float(
                                   modes['direct_mV_per_pA']-a['bridge_MOhm'][j]*1e-3)})
    summaries = []
    for device in sorted(set(a['device'].tolist())):
        for group in ('VC_train', 'VC_same_holding', 'VC_shifted_holding', 'IC_all', 'IC_near_holding'):
            selected = [r for r in scores if r['device'] == device and
                        (r['group'] == group or group == 'IC_near_holding' and
                         r['group'] == 'IC_all' and r['near_vc_holding'])]
            row = {'device': int(device), 'group': group, 'models': {}}
            for order in (1, 2):
                subset = [r for r in selected if r['order'] == order]
                if not subset:
                    continue
                rms = lambda key: float(np.sqrt(np.average([r[key]**2 for r in subset],
                                                           weights=[r['n'] for r in subset])))
                error, noise = rms('rmse'), rms('baseline_sd')
                row['models'][str(order)] = {'sweeps': len(subset), 'rmse': error,
                    'baseline_sd': noise, 'error_to_noise': error/noise,
                    'adequate_at_existing_3x_noise': bool(error <= 3*noise),
                    'original_rc_rmse': rms('original_rc_rmse')}
            if '1' in row['models'] and '2' in row['models']:
                row['relative_rmse_reduction_two_vs_one'] = 1-row['models']['2']['rmse']/row['models']['1']['rmse']
            summaries.append(row)
    archive_path = output / 'predictions.npz'
    np.savez_compressed(archive_path, prediction=predictions, order=np.array([1, 2]),
                        row=np.arange(80), mode=a['mode'], cell_id=a['cell_id'], sweep=a['sweep'])
    result = {'schema': 'ce.allen.passive-port-comparison.v1',
              'scope': 'Outcome-informed development on an already studied preparation; no independent confirmation.',
              'split': {'VC_fit': [0, 1, 2], 'VC_same_holding': [3, 4],
                        'VC_shifted_holding': [5, 6, 7, 8, 9], 'IC_no_refit': [10, 11, 12, 13, 14, 15]},
              'equation': 'Y(s)=g0+sum(gq*s*tauq/(1+s*tauq)); conditional IC transfer Z=1/Y minus recorded bridge.',
              'units': {'conductance': 'nS', 'VC_response': 'pA', 'IC_response': 'mV', 'tau': 's'},
              'inputs': {str(p): sha(p) for p in (arrays_path, metadata_path)},
              'sources': {str(p.relative_to(ROOT)): sha(p) for p in
                          (Path(__file__), Path(model.__file__), ROOT/'tests/test_passive_port_model.py')},
              'runtime': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
              'fits': fits, 'scores': scores, 'summary': summaries,
              'one_mode_max_abs_rmse_difference_from_original': max(
                  abs(r['rmse']-r['original_rc_rmse']) for r in scores if r['order'] == 1),
              'predictions_sha256': sha(archive_path),
              'limits': ['Known held-out outcomes informed this extension; no pristine test claim.',
                         'Command voltage and compensation settings do not independently calibrate the physical port.',
                         'Bridge/neutralization differences and operating-point drift remain.',
                         'Additional poles are effective states, not identified membrane/dendrite/electrode mechanisms.',
                         'No plasticity, connection-current, metric or whole-brain validation.']}
    with (output/'result.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({'event': 'COMPLETE', 'output': str(output), 'summary': summaries,
                      'baseline_max_delta': result['one_mode_max_abs_rmse_difference_from_original']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arrays', required=True, type=Path)
    parser.add_argument('--metadata', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run(args.arrays, args.metadata, args.output)
