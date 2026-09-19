"""Offline, exploratory measurement audit; no synaptic-amplitude ground truth.

Compare the preserved local post-pre operator with pre-window-only linear
extrapolation, including source-stimulus-free pseudo events in the recovery gap.
No model fitting across sweeps, selection by response, downloads, or old writes.
"""
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / 'data/external/allen_synphys_r21/raw_ranges/1574292898.139'
PRE = (-.008, -.003)
POST = (.002, .008)
GAP_OFFSETS = (.020, .040, .060, .080, .100)
TARGETS = ('positive', 'negative')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def window_times(fs):
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError('Positive finite sampling rate required')
    pre, post = np.arange(*PRE, 1 / fs), np.arange(*POST, 1 / fs)
    if len(pre) < 3 or len(post) < 2:
        raise ValueError('Insufficient window samples')
    return pre, post


def measure(voltage, fs, center):
    """Return microvolt contrasts; baseline slope uses only pre-event values."""
    v = np.asarray(voltage, dtype=float)
    if v.ndim != 1 or not np.isfinite(center):
        raise ValueError('One-dimensional voltage and finite center required')
    tp, tq = window_times(fs)
    ip, iq = (center + tp) * fs, (center + tq) * fs
    if ip.min() < 0 or iq.max() >= len(v) - 1:
        raise ValueError('Window outside available trace')
    # Match the interpolation and np.arange convention of the preserved result.
    xp = np.interp(ip, np.arange(len(v)), v) * 1e6
    xq = np.interp(iq, np.arange(len(v)), v) * 1e6
    if not np.isfinite(xp).all() or not np.isfinite(xq).all():
        raise ValueError('Nonfinite window value')
    centered = tp - tp.mean()
    slope = float(np.dot(centered, xp - xp.mean()) / np.dot(centered, centered))
    old = float(xq.mean() - xp.mean())
    correction = slope * float(tq.mean() - tp.mean())
    return dict(old_uV=old, linear_uV=old - correction,
                pre_slope_uV_per_ms=slope / 1000,
                correction_uV=correction,
                pre_mean_uV=float(xp.mean()), post_mean_uV=float(xq.mean()))


def noise_geometry(fs):
    """Ideal independent *window-sample* noise; not an empirical noise estimate."""
    tp, tq = window_times(fs)
    centered = tp - tp.mean()
    delta = float(tq.mean() - tp.mean())
    old_variance = 1 / len(tp) + 1 / len(tq)
    extra = delta ** 2 / float(np.dot(centered, centered))
    return dict(pre_samples=len(tp), post_samples=len(tq),
                mean_separation_ms=delta * 1000,
                old_weight_norm_squared=old_variance,
                linear_weight_norm_squared=old_variance + extra,
                variance_ratio=(old_variance + extra) / old_variance,
                sd_ratio=float(np.sqrt((old_variance + extra) / old_variance)),
                assumption='Independent equal-variance resampled window values; '
                'ignores voltage autocorrelation and interpolation covariance. '
                'This is operator geometry, not measured physiological noise.')


def check_commands(inventory, events_by_sweep):
    """Use the existing hash-checking, strictly offline NWB reader."""
    import h5py
    sys.path.insert(0, str(HERE.parent / 'fixed_points_metric'))
    from allen_joint_inventory import OfflineRanges, describe

    manifest_before = sha(CACHE / 'manifest.json')
    checks = []
    with OfflineRanges(CACHE) as reader:
        with h5py.File(reader, 'r') as nwb:
            for sweep in range(37, 57):
                meta = inventory[sweep]
                events = events_by_sweep[sweep]
                fs = meta['nodes']['pre']['rate']
                lo = round(events[0]['command_start_s'] * fs)
                hi = round((events[-1]['command_start_s'] + .150) * fs)
                for target in TARGETS:
                    node = meta['nodes'][target]
                    device = int(node['electrode'].split('_')[-1])
                    path = f'/stimulus/presentation/data_{sweep:05d}_DA{device}'
                    command = nwb[path]
                    desc = describe(command)
                    assert desc['unit'] == 'A' and desc['device'] == device
                    assert desc['rate'] == node['rate'] == fs
                    assert desc['start'] == node['start_s']
                    assert desc['samples'] == node['samples']
                    acquisition = nwb[node['path']]['data']
                    assert float(acquisition.attrs.get('offset', 0)) == 0
                    assert float(acquisition.attrs['conversion']) == node['conversion']
                    values = np.asarray(command['data'][lo:hi], dtype=float)
                    physical = values * desc['conversion'] + desc['offset']
                    assert len(values) == hi - lo and np.isfinite(physical).all()
                    assert np.all(physical == 0), 'Target command is not zero'
                    checks.append(dict(sweep=sweep, target=target, metadata=desc,
                                       sample_bounds=[lo, hi], samples=len(values),
                                       constant_A=0., transitions=0))
        provenance = dict(remote=reader.remote, used_blocks=reader.used,
                          missing_blocks=sorted(reader.missing))
    assert manifest_before == sha(CACHE / 'manifest.json')
    provenance.update(manifest_sha256=manifest_before, checks=checks,
                      reader_sha256=sha(HERE.parent / 'fixed_points_metric/allen_joint_inventory.py'),
                      base_reader_sha256=sha(HERE / 'raw_metadata.py'),
                      caveat='Stored DA waveform excludes separately recorded holding settings; '
                      'zero DA is not absence of biological input or total clamp current.')
    return provenance


def summarize(rows):
    output = []
    for target in TARGETS:
        for kind in ('actual', 'gap_control'):
            for half, low, high in [('all', 37, 56), ('early', 37, 46), ('late', 47, 56)]:
                selected = [r for r in rows if r['target'] == target and r['kind'] == kind
                            and low <= r['sweep'] <= high]
                methods = {}
                for method in ('old', 'linear'):
                    a = np.array([r[method + '_uV'] for r in selected])
                    methods[method] = dict(mean_uV=float(a.mean()), median_uV=float(np.median(a)),
                                          rms_uV=float(np.sqrt(np.mean(a * a))),
                                          p10_uV=float(np.quantile(a, .1)),
                                          p90_uV=float(np.quantile(a, .9)))
                per_sweep = []
                for sweep in range(low, high + 1):
                    rr = [r for r in selected if r['sweep'] == sweep]
                    per_sweep.append(dict(sweep=sweep, **{
                        method + '_rms_uV':float(np.sqrt(np.mean([r[method + '_uV'] ** 2 for r in rr])))
                        for method in ('old', 'linear')}))
                output.append(dict(target=target, kind=kind, half=half,
                                   sweeps=high-low+1, windows=len(selected), **methods,
                                   rms_ratio=methods['linear']['rms_uV']/methods['old']['rms_uV'],
                                   sweeps_lower_linear_rms=sum(r['linear_rms_uV'] < r['old_rms_uV']
                                                              for r in per_sweep), per_sweep=per_sweep))
    return output


def run():
    inputs = {name: HERE / filename for name, filename in dict(
        train='recovery_train_responses_result.json', targets='ic_full_recording_qc_result.json',
        inventory='ic_extended_inventory_result.json').items()}
    data = {name:json.loads(path.read_text(encoding='utf-8')) for name, path in inputs.items()}
    inv = {r['sweep']:r for r in data['inventory']['selected']}
    receipts = {(r['sweep'], r['target']):r for r in data['targets']['analysis']['records']}
    events = {sw:sorted([r for r in data['train']['records'] if r['sweep'] == sw],
                       key=lambda r:r['pulse']) for sw in range(37, 57)}
    for values in events.values():
        assert [r['pulse'] for r in values] == list(range(1, 13))
        assert all(len(r['spikes']) == 1 for r in values)
    commands = check_commands(inv, events)
    rows, assets, errors = [], [], []
    for sw in range(37, 57):
        fs = inv[sw]['nodes']['pre']['rate']
        assert fs == 100000
        source_path = CACHE / f'recovery_train_sources/{sw}.npz'
        receipt_path = source_path.with_suffix('.json')
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        assert sha(source_path) == receipt['sha256']
        assets.append(dict(path=source_path.relative_to(ROOT).as_posix(), sha256=receipt['sha256'],
                           receipt_sha256=sha(receipt_path)))
        with np.load(source_path, allow_pickle=False) as z:
            current = z['current']
        assert len(current) == inv[sw]['nodes']['pre']['samples']
        centers = [r['command_start_s'] + r['spikes'][0]['max_slope_time'] for r in events[sw]]
        pseudo = [centers[7] + offset for offset in GAP_OFFSETS]
        for center in pseudo:
            assert center + PRE[0] > events[sw][7]['command_start_s'] + events[sw][7]['duration_ms']/1000
            assert center + POST[1] < events[sw][8]['command_start_s']
            lo, hi = int(np.floor((center + PRE[0])*fs)), int(np.ceil((center + POST[1])*fs)) + 1
            assert np.all(current[lo:hi] == 0), 'Source command overlaps a control window'
        for target in TARGETS:
            receipt = receipts[sw, target]
            target_path = ROOT / receipt['array_path']
            assert sha(target_path) == receipt['array_sha256']
            assets.append(dict(path=target_path.relative_to(ROOT).as_posix(), sha256=receipt['array_sha256']))
            with np.load(target_path, allow_pickle=False) as z:
                voltage = z['voltage']
            assert len(voltage) == inv[sw]['nodes'][target]['samples']
            for pulse, center in enumerate(centers, 1):
                value = measure(voltage, fs, center)
                errors.append(abs(value['old_uV'] - events[sw][pulse-1]['responses'][target]))
                rows.append(dict(sweep=sw, target=target, kind='actual', pulse=pulse,
                                 center_s=center, **value))
            for offset, center in zip(GAP_OFFSETS, pseudo):
                rows.append(dict(sweep=sw, target=target, kind='gap_control', offset_ms=offset*1000,
                                 center_s=center, **measure(voltage, fs, center)))
    assert len(rows) == 680 and len(errors) == 480 and max(errors) < 1e-5
    return dict(question='Is a pre-window-only affine baseline extrapolation stable in the recovery gap?',
                status='Exploratory measurement audit, not a synaptic-amplitude or learning estimate',
                selection='All sweeps37..56, all12 detected events, both targets; no exclusions',
                units=dict(voltage_input='V', results='uV', time='seconds', command='A'),
                windows_s=dict(pre=PRE, post=POST), gap_offsets_s=GAP_OFFSETS,
                formulas=dict(old='mean(post)-mean(pre)',
                              linear='old-pre_slope*(mean(post_time)-mean(pre_time))'),
                grouping='Twenty repeated sweeps of one source and two targets in one experiment; '
                'windows and raw samples are not independent biological replicates',
                limits=['Gap controls have no source command, but residual and spontaneous activity remain.',
                        'RMS is magnitude relative to zero, not error against known biological truth.',
                        'Early/late summaries are descriptive checks, not unseen holdout validation.',
                        'Linear extrapolation is not a fitted membrane filter or Fourier deconvolution.',
                        'Positive/negative are retained database target labels, not voltage signs.'],
                source_sha256={k:sha(v) for k,v in inputs.items()}, code_sha256=sha(__file__),
                runtime=dict(python=platform.python_version(), numpy=np.__version__),
                input_assets=assets, command_verification=commands,
                old_response_reproduction=dict(count=len(errors), max_abs_error_uV=max(errors)),
                ideal_noise_geometry=noise_geometry(100000), records=rows, summary=summarize(rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE / 'recovery_baseline_extrapolation_result.json')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f'Preserve prior output: {args.output}')
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(args.output), sha256=sha(args.output),
                          reproduction=result['old_response_reproduction'],
                          noise=result['ideal_noise_geometry'],
                          controls=[{k:v for k,v in r.items() if k != 'per_sweep'}
                                    for r in result['summary'] if r['kind'] == 'gap_control']), indent=2))


if __name__ == '__main__':
    main()
