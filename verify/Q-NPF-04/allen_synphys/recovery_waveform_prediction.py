"""Retrospective, offline forward prediction of same-cell recovery waveforms.

Fit only sweeps37..46 / initial eight pulses. No local post-event baseline fit,
inverse filtering, new downloads, or overwrite of prior research artifacts.
"""
import argparse
import hashlib
import itertools
import json
import platform
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / 'data/external/allen_synphys_r21/raw_ranges/1574292898.139'
OUT = ROOT / 'data/local/allen-synphys-analysis/recovery-waveform-v1'
TARGETS = ('positive', 'negative')
METHODS = ('zero', 'offset', 'constant', 'depression', 'facilitation')
TRAIN_SWEEPS = tuple(range(37, 47))
TEMPORAL_SWEEPS = tuple(range(47, 57))
BIN_SAMPLES = 50  # 0.5 ms averages at the original 100 kHz clock.
KERNEL_GRID = tuple(itertools.product((0., .5, 1., 1.5, 2., 3., 4.), (.5, 1., 2., 4.), (8., 16., 32., 64., 128.)))
HISTORY_GRID = [('constant', 0., 1.)]
HISTORY_GRID += [('depression', u, tau) for u in (.1, .3, .5, .7, .9) for tau in (.05, .15, .5, 1.5, 5.)]
HISTORY_GRID += [('facilitation', f, tau) for f in (.25, .5, 1., 2.) for tau in (.02, .05, .1, .3, 1.)]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def array_sha(array):
    return hashlib.sha256(np.ascontiguousarray(array, dtype='<f8').tobytes()).hexdigest()


def efficacy(times, name, strength=0., tau=1.):
    times = np.asarray(times, dtype=float)
    if times.ndim != 1 or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError('Finite increasing spike times required')
    if name not in ('constant', 'depression', 'facilitation') or tau <= 0 or strength < 0:
        raise ValueError('Invalid history model')
    if name == 'depression' and strength > 1:
        raise ValueError('Depression utilization must be at most one')
    q = np.ones(len(times))
    for n in range(1, len(times)):
        decay = np.exp(-(times[n]-times[n-1])/tau)
        if name == 'depression':
            q[n] = 1 - (1 - (1-strength)*q[n-1])*decay
        elif name == 'facilitation':
            q[n] = 1 + (q[n-1]-1+strength)*decay
    return q


def kernel_norm(rise, decay):
    if not 0 < rise < decay:
        raise ValueError('Require 0 < rise < decay')
    peak = np.log(decay/rise)/(1/rise-1/decay)
    return np.exp(-peak/decay)-np.exp(-peak/rise)


def exponential_bin_mean(delta, tau, fs=100000, samples=BIN_SAMPLES):
    """Exact mean on the original sample lattice, including causal onset bins."""
    if tau <= 0 or fs <= 0 or samples < 1:
        raise ValueError('Positive scale and sample count required')
    delta = np.asarray(delta, dtype=float)
    first = np.clip(np.ceil(-delta*fs - 1e-8), 0, samples)
    count = samples-first
    start = np.maximum(delta+first/fs, 0.)
    return np.exp(-start/tau)*np.expm1(-count/(fs*tau))/np.expm1(-1/(fs*tau))/samples


def kernel_basis(left_times, spikes, lag, rise, decay, fs=100000, samples=BIN_SAMPLES):
    if lag < 0:
        raise ValueError('Nonnegative latency required')
    delta = np.asarray(left_times)[:, None] - np.asarray(spikes)[None, :] - lag
    return (exponential_bin_mean(delta, decay, fs, samples)
            - exponential_bin_mean(delta, rise, fs, samples))/kernel_norm(rise, decay)


def frequency_response(lag, rise, decay, frequency=50.):
    """Normalized amplitude and continuous phase of the fixed kernel, not data FFT."""
    kernel_norm(rise, decay)
    omega = 2*np.pi*frequency
    return dict(frequency_Hz=frequency,
                amplitude_over_DC=float(1/np.sqrt((1+(omega*rise)**2)*(1+(omega*decay)**2))),
                phase_degrees=float((-omega*lag-np.arctan(omega*rise)-np.arctan(omega*decay))*180/np.pi),
                group_delay_ms=float(1000*(lag+rise/(1+(omega*rise)**2)+decay/(1+(omega*decay)**2))))


def fit_affine_basis(x, y, weights, nonnegative=True):
    """Weighted OLS of b+A*x; each candidate uses the same training-only offset."""
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = x[:, None]
    y, w = np.asarray(y, float), np.asarray(weights, float)
    if x.shape[0] != len(y) or w.shape != y.shape or np.any(w < 0) or w.sum() <= 0:
        raise ValueError('Bad regression shapes or weights')
    w = w/w.sum()
    xm, ym = w@x, float(w@y)
    centered = x-xm
    xx = np.sum(w[:, None]*centered**2, axis=0)
    xy = np.sum(w[:, None]*centered*(y-ym)[:, None], axis=0)
    a = np.divide(xy, xx, out=np.zeros_like(xy), where=xx > 1e-20)
    if nonnegative:
        a = np.maximum(0., a)
    b = ym-a*xm
    mse = np.sum(w[:, None]*(y[:, None]-b-x*a)**2, axis=0)
    return a, b, mse


def spike_crossings(v, fs):
    """Independent source fidelity check; not a new max-slope alignment rule."""
    v = np.asarray(v)*1000
    crossings = np.flatnonzero((v[:-1] < -20) & (v[1:] >= -20))+1
    accepted = []
    for i in crossings:
        if accepted and (i-accepted[-1])/fs < .002:
            continue
        a, b = max(0, i-round(.001*fs)), min(len(v), i+round(.002*fs)+1)
        if b-a >= 3 and np.max(v[i:b]) >= 0 and np.max(np.diff(v[a:b]))*fs/1000 >= 20:
            accepted.append(int(i))
    return np.asarray(accepted, dtype=int)


def extract():
    import h5py
    sys.path.insert(0, str(HERE.parent/'fixed_points_metric'))
    from allen_joint_inventory import OfflineRanges, MissingBlock, describe
    from reference_spike_audit import reference
    TSeries, _, detector_manifest = reference()
    from neuroanalysis.spike_detection import detect_ic_evoked_spikes

    input_files = [HERE/name for name in ('ic_recovery_inventory_result.json', 'ic_extended_inventory_result.json',
                    'ic_full_recording_qc_result.json', 'recovery_train_responses_result.json',
                    'recovery_baseline_extrapolation_result.json')]
    data = [json.loads(p.read_text(encoding='utf-8')) for p in input_files]
    inventory = {r['sweep']:r for obj in data[:2] for r in obj['selected']}
    targets = {(r['sweep'], r['target']):r for r in data[2]['analysis']['records']}
    old_events = {(r['sweep'], r['pulse']):r for r in data[3]['records']}
    manifest_before = sha(CACHE/'manifest.json')
    records, provenance, assets, eligibility = [], [], [], []
    with OfflineRanges(CACHE) as reader:
        with h5py.File(reader, 'r') as nwb:
            for sw in range(32, 57):
                meta = inventory[sw]
                fs = meta['nodes']['pre']['rate']
                assert fs == 100000
                lo = round((meta['onset_times_s'][0]-.100)*fs)
                hi = round((meta['onset_times_s'][-1]+.150)*fs)
                source_path = CACHE/f'recovery_train_sources/{sw}.npz'
                source_missing = None
                if sw >= 37:
                    receipt_path = source_path.with_suffix('.json')
                    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
                    assert sha(source_path) == receipt['sha256']
                    assets.append(dict(path=source_path.relative_to(ROOT).as_posix(), sha256=receipt['sha256'],
                                       receipt_sha256=sha(receipt_path)))
                    with np.load(source_path, allow_pickle=False) as z:
                        pre = z['voltage'][lo:hi]
                        command = z['current'][lo:hi]
                else:
                    ds = nwb[meta['command']['path']]['data']
                    command = np.asarray(ds[lo:hi],float)*float(ds.attrs['conversion'])+float(ds.attrs.get('offset',0.))
                    try:
                        ds = nwb[meta['nodes']['pre']['path']]['data']
                        pre = np.asarray(ds[lo:hi],float)*float(ds.attrs['conversion'])+float(ds.attrs.get('offset',0.))
                    except MissingBlock as error:
                        pre = None
                        source_missing = str(error)
                assert np.isfinite(command).all()
                if pre is not None:
                    assert len(pre) == hi-lo and np.isfinite(pre).all()
                active = command > command.max()/2
                starts = np.flatnonzero(np.diff(active.astype(int),prepend=0)==1)
                stops = np.flatnonzero(np.diff(active.astype(int),append=0)==-1)+1
                assert len(starts) == len(stops) == 12
                onsets = (starts+lo)/fs
                assert np.max(np.abs(onsets-np.array(meta['onset_times_s']))) <= 1/fs+1e-9
                assert np.all(command[:starts[0]] == 0)
                if pre is not None:
                    source_candidates = lo/fs+spike_crossings(pre,fs)/fs
                    assert len(source_candidates) == 12, f'Extra/missing source spikes: {sw}'
                    assert all(np.sum((source_candidates>=t-.0005)&(source_candidates<t+.008)) == 1 for t in onsets)
                spikes = []
                for pulse, (a,b) in enumerate(zip(starts,stops),1):
                    if pre is None:
                        continue
                    if sw >= 37:
                        event = old_events[sw,pulse]
                        assert abs(event['command_start_s']-(a+lo)/fs) < 1e-12
                        spike = event['command_start_s']+event['spikes'][0]['max_slope_time']
                    else:
                        left, right = a-round(.010*fs), a+round(.012*fs)
                        found = detect_ic_evoked_spikes(TSeries(pre[left:right],dt=1/fs,t0=-.010,units='V'),(0,(b-a)/fs))
                        assert len(found) == 1 and np.isfinite(found[0]['max_slope_time'])
                        spike = (a+lo)/fs+found[0]['max_slope_time']
                    spikes.append(spike-onsets[0])
                spikes = np.array(spikes)
                onsets -= onsets[0]
                left_times = (np.arange((hi-lo)//BIN_SAMPLES)*BIN_SAMPLES+lo)/fs - (starts[0]+lo)/fs
                right_times = left_times+BIN_SAMPLES/fs
                valid = left_times >= 0
                for onset, spike in zip(onsets,spikes):
                    valid &= ~((left_times < spike+.002)&(right_times > onset-.0005))
                if pre is not None:
                    initial = valid & (right_times <= spikes[7]+.018)
                    gap = valid & (left_times >= spikes[7]+.020)&(right_times <= onsets[8]-.0005)
                    recovery = valid & (left_times >= onsets[8])&(right_times <= spikes[-1]+.018)
                    tail = valid & (left_times >= spikes[-1]+.020)
                    assert initial.sum() > 200 and recovery.sum() > 100 and gap.sum() > 100
                command_info = []
                for target in TARGETS:
                    node = meta['nodes'][target]
                    device = int(node['electrode'].split('_')[-1])
                    reasons = [] if source_missing is None else ['source_full_gap_unobserved: '+source_missing]
                    try:
                        nd = nwb[f'/stimulus/presentation/data_{sw:05d}_DA{device}']
                        desc = describe(nd)
                        assert desc['unit'] == 'A' and desc['rate'] == fs and desc['start'] == node['start_s']
                        assert desc['samples'] == node['samples']
                        cmd = np.asarray(nd['data'][lo:hi],float)*desc['conversion']+desc['offset']
                        info = dict(target=target,metadata=desc,sample_bounds=[lo,hi],
                                    min_A=float(cmd.min()),max_A=float(cmd.max()),
                                    transitions=int(np.sum(np.diff(cmd)!=0)))
                        if not np.all(cmd == 0):
                            reasons.append('target_has_own_nonzero_command')
                            edges = np.flatnonzero(np.diff((cmd!=0).astype(int),prepend=0)==1)
                            info['own_command_onsets_s'] = ((edges+lo)/fs).tolist()
                        command_info.append(info)
                    except MissingBlock as error:
                        reasons.append('target_command_unobserved: '+str(error))
                        command_info.append(dict(target=target,sample_bounds=[lo,hi],missing=str(error)))
                    eligibility.append(dict(sweep=sw,target=target,included=not reasons,reasons=reasons))
                    if reasons:
                        assert sw < 37, 'Core20 cohort lost a required input'
                        continue
                    receipt = targets[sw,target]
                    path = ROOT/receipt['array_path']
                    assert sha(path) == receipt['array_sha256']
                    assets.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=receipt['array_sha256']))
                    with np.load(path,allow_pickle=False) as z:
                        voltage = z['voltage']
                    ds = nwb[node['path']]['data']
                    assert float(ds.attrs.get('offset',0.)) == 0 and float(ds.attrs['conversion']) == node['conversion']
                    baseline = float(voltage[lo:starts[0]+lo-round(.010*fs)].mean()*1e6)
                    clipped = voltage[lo:lo+len(left_times)*BIN_SAMPLES]*1e6
                    y = clipped.reshape(-1,BIN_SAMPLES).mean(axis=1)-baseline
                    assert np.isfinite(y).all()
                    records.append(dict(sweep=sw,target=target,baseline_uV=baseline,fs=fs,
                        gap_s=float(onsets[8]-onsets[7]),left_times=left_times,spikes=spikes,
                        y=y,initial=initial,gap=gap,recovery=recovery,tail=tail,valid=valid))
                provenance.append(dict(sweep=sw,sample_bounds=[lo,hi],source_voltage_sha256=array_sha(pre) if pre is not None else None,
                    source_current_sha256=array_sha(command),source_spikes=12 if pre is not None else None,
                    source_missing=source_missing,spike_times_relative_s=spikes.tolist(),
                    command_checks=command_info))
        cache_provenance = dict(remote=reader.remote,used_blocks=reader.used,missing_blocks=sorted(reader.missing))
    assert manifest_before == sha(CACHE/'manifest.json')
    return records, dict(inputs={p.relative_to(ROOT).as_posix():sha(p) for p in input_files},
        assets=assets,source_windows=provenance,eligibility=eligibility,cache=cache_provenance,cache_manifest_sha256=manifest_before,
        detector_manifest=detector_manifest,reader_sha256=sha(HERE.parent/'fixed_points_metric/allen_joint_inventory.py'),
        base_reader_sha256=sha(HERE/'raw_metadata.py'),reference_loader_sha256=sha(HERE/'reference_spike_audit.py'))


def fit_models(records):
    """Caller passes training records only; fit never reads recovery targets."""
    training = [r for r in records if r['sweep'] in TRAIN_SWEEPS]
    assert len(training) == 10
    y = np.concatenate([r['y'][r['initial']] for r in training])
    w = np.concatenate([np.full(int(r['initial'].sum()),1/r['initial'].sum()/len(training)) for r in training])
    q = [np.array([efficacy(r['spikes'],*g) for g in HISTORY_GRID]) for r in training]
    offset = float(w@y)
    best = dict(zero=dict(model='zero',offset_uV=0.,amplitude_uV=0.,train_mse_uV2=float(w@(y*y))),
                offset=dict(model='offset',offset_uV=offset,amplitude_uV=0.,train_mse_uV2=float(w@((y-offset)**2))))
    profile = []
    for lag_ms,rise_ms,decay_ms in KERNEL_GRID:
        xx = []
        for r,weights in zip(training,q):
            basis = kernel_basis(r['left_times'][r['initial']],r['spikes'],lag_ms/1000,rise_ms/1000,decay_ms/1000)
            xx.append(basis@weights.T)
        amplitude, intercept, mse = fit_affine_basis(np.concatenate(xx),y,w,nonnegative=True)
        for i,(name,strength,tau) in enumerate(HISTORY_GRID):
            row = dict(model=name,strength=strength,tau_s=tau,lag_ms=lag_ms,rise_ms=rise_ms,
                       decay_ms=decay_ms,amplitude_uV=float(amplitude[i]),offset_uV=float(intercept[i]),
                       train_mse_uV2=float(mse[i]))
            profile.append(row)
            if name not in best or row['train_mse_uV2'] < best[name]['train_mse_uV2']:
                best[name] = row
    return best, profile


def predict(record, model):
    if model['model'] in ('zero','offset'):
        return np.full_like(record['y'],model['offset_uV'])
    basis = kernel_basis(record['left_times'],record['spikes'],model['lag_ms']/1000,
                         model['rise_ms']/1000,model['decay_ms']/1000)
    return model['offset_uV']+model['amplitude_uV']*(basis@efficacy(record['spikes'],model['model'],model['strength'],model['tau_s']))


def evaluate(records, models):
    output, arrays = [], {}
    for record in records:
        sw, target = record['sweep'],record['target']
        key = f'{sw}_{target}'
        for name in ('left_times','y','initial','gap','recovery','tail','valid','spikes'):
            arrays[key+'_'+name] = record[name]
        for method,model in models[target].items():
            pred = predict(record,model)
            arrays[key+'_prediction_'+method] = pred
            for region in ('initial','gap','recovery','tail'):
                mask = record[region]
                output.append(dict(sweep=sw,target=target,method=method,region=region,
                    gap_ms=record['gap_s']*1000,bins=int(mask.sum()),
                    mse_uV2=float(np.mean((record['y'][mask]-pred[mask])**2)),
                    mean_error_uV=float(np.mean(pred[mask]-record['y'][mask]))))
    summary = []
    for target,region,cohort,method in itertools.product(TARGETS,('initial','gap','recovery','tail'),
        ('fit_sweeps','temporal','variable_gap'),METHODS):
        selected = TRAIN_SWEEPS if cohort=='fit_sweeps' else TEMPORAL_SWEEPS if cohort=='temporal' else tuple(range(32,37))
        rr = [r for r in output if r['target']==target and r['region']==region and r['method']==method and r['sweep'] in selected]
        if not rr:
            summary.append(dict(target=target,region=region,cohort=cohort,method=method,sweeps=0,rmse_uV=None,comparators={}))
            continue
        per_sweep = np.array([r['mse_uV2'] for r in rr])
        comparators = {}
        for reference in ('zero','offset','constant'):
            gains = [next(r['mse_uV2'] for r in output if r['target']==target and r['region']==region
                          and r['method']==reference and r['sweep']==row['sweep'])-row['mse_uV2'] for row in rr]
            comparators[reference] = dict(mean_gain_uV2=float(np.mean(gains)),median_gain_uV2=float(np.median(gains)),
                                          improved_sweeps=int(np.sum(np.array(gains)>0)))
        summary.append(dict(target=target,region=region,cohort=cohort,method=method,sweeps=len(rr),
                            rmse_uV=float(np.sqrt(per_sweep.mean())),comparators=comparators))
    return output, summary, arrays


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=HERE/'recovery_waveform_prediction_result.json')
    parser.add_argument('--array-output',type=Path,default=OUT/'recovery_waveform_arrays.npz')
    args = parser.parse_args()
    if args.output.exists() or args.array_output.exists():
        raise FileExistsError('Preserve prior waveform outputs')
    records, provenance = extract()
    models, profiles, phase_diagnostics = {}, {}, {}
    for target in TARGETS:
        models[target],profiles[target] = fit_models([r for r in records if r['target']==target])
        fixed = models[target]['constant']
        near = [r for r in profiles[target] if r['model']=='constant' and r['train_mse_uV2'] <= fixed['train_mse_uV2']*1.01]
        phases = [frequency_response(r['lag_ms']/1000,r['rise_ms']/1000,r['decay_ms']/1000) for r in near]
        phase_diagnostics[target] = dict(best=frequency_response(fixed['lag_ms']/1000,fixed['rise_ms']/1000,fixed['decay_ms']/1000),
            near_optimal_count=len(near),total_fixed_candidates=len(KERNEL_GRID),relative_training_mse_tolerance=.01,
            near_phase_min_degrees=min(p['phase_degrees'] for p in phases),near_phase_max_degrees=max(p['phase_degrees'] for p in phases),
            meaning='Grid sensitivity diagnostic, not a confidence set or empirical Fourier estimate; ignores fitted amplitude sign at zero.')
        print('FITTED',target,json.dumps(models[target]),flush=True)
    rows,summary,arrays = evaluate(records,models)
    args.array_output.parent.mkdir(parents=True,exist_ok=True)
    with args.array_output.open('xb') as stream:
        np.savez_compressed(stream,**arrays)
    result = dict(question='Can fixed effective voltage filtering explain recovery waveforms, and do history models improve held-out predictions?',
        scope='Same source and two targets; retrospective development using previously inspected traces; no biological mechanism identification.',
        code_sha256=sha(__file__),test_sha256=sha(ROOT/'tests/test_recovery_waveform_prediction.py'),
        runtime=dict(python=platform.python_version(),numpy=np.__version__),provenance=provenance,
        split=dict(fit_sweeps=list(TRAIN_SWEEPS),fit_region='initial eight pulses only',temporal=list(TEMPORAL_SWEEPS),
                   variable_gap_attempted=list(range(32,37)),variable_gap_included=[{'sweep':r['sweep'],'target':r['target']} for r in records if r['sweep']<37],
                   prior_exposure='Earlier analyses inspected all target traces and some summaries. Fit exclusion is computational, not blinded confirmation.'),
        measurement=dict(input='Detected source AP times, not target synaptic current',output='Target voltage uV relative to own pretrain[-100,-10)ms mean',
            bins='Exact original-lattice means of50 samples at100kHz (0.5ms); same operator on predictions',
            artifact_mask='Bins intersecting command onset-0.5ms through source spike+2ms are omitted from scores',
            regions='Initial ends spike8+18ms; gap from spike8+20ms to command9-0.5ms; recovery ends spike12+18ms; tail starts spike12+20ms',
            baseline='One common learned offset per model/target, fitted on initial train only; no target-outcome gain or offset refit in held-out sweeps',
            sign='Nonnegative kernel amplitude for excitatory source hypothesis, applied identically to unlabeled target; negative label means no reported synapse, not inhibition',
            holding='Zero stored DA does not include separately recorded holding settings or imply absent spontaneous input'),
        configuration=dict(kernel_grid_ms=KERNEL_GRID,history_grid=HISTORY_GRID,
            initial_state='Depression resource1 and facilitation0 reset per sweep; assumed, not measured',
            selection='Lowest training MSE separately per family, equal total weight per sweep; no held-out refit',
            comparison='History candidates must beat both offset-only and fixed kernels on temporal initial AND recovery regions to motivate further testing; even success is not causal identification'),
        records=[{k:v for k,v in r.items() if k not in ('left_times','spikes','y','initial','gap','recovery','tail','valid')} for r in records],
        models=models,training_profiles=profiles,phase_diagnostics=phase_diagnostics,per_sweep=rows,summary=summary,
        arrays=dict(path=args.array_output.relative_to(ROOT).as_posix(),sha256=sha(args.array_output),bytes=args.array_output.stat().st_size))
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')
    print('RESULT',args.output,sha(args.output),flush=True)
    print(json.dumps([r for r in summary if r['cohort']=='temporal' and r['region'] in ('initial','recovery')],indent=2))


if __name__ == '__main__':
    main()
