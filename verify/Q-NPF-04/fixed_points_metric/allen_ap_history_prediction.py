"""Fixed-point AP-conditioned PSP prediction; new IC windows, old bytes reused."""
import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, HERE, OfflineRanges, describe, raw, sha

ROOT = HERE.parents[2]
INVENTORY = HERE.parent / 'allen_synphys/next_donor_recording_inventory_result.json'
IDENTITY = HERE / 'allen_differential_annotations_result.json'
CONTRACT = HERE / 'allen_ap_history_contract.json'
RESULT = HERE / 'allen_ap_history_result.json'
EXT = '1630015960.701'
BINS = np.array([[.002, .004], [.004, .006], [.006, .008],
                 [.008, .010], [.010, .012], [.012, .014]])
BASELINE = np.array([-.008, -.003])


def save(path, obj):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)


def freeze():
    source = json.loads(IDENTITY.read_text(encoding='utf-8'))
    manifest = json.loads((BASE / 'raw_ranges' / EXT / 'manifest.json').read_text())
    save(CONTRACT, dict(
        created_utc=datetime.now(timezone.utc).isoformat(), code_sha256=sha(Path(__file__)),
        inputs={str(p.relative_to(ROOT)): sha(p) for p in (INVENTORY, IDENTITY, HERE/'allen_joint_inventory.py', Path(raw.__file__))},
        execution=dict(python=platform.python_version(), executable=sys.executable, numpy=np.__version__, h5py=h5py.__version__,
                       runner='.codex/hooks/python.cmd', runner_sha256=sha(ROOT/'.codex/hooks/python.cmd')),
        remote=manifest['remote'], cells=source['cells'], pair_ids=[121538, 121566],
        objective_chain='fixed neuronal positions -> AP-conditioned directed PSP dynamics -> calibrated conductance -> independently observed directional cost metric',
        question='Does fixed efficacy, depression or facilitation predict later same-cell PSPs and a different input frequency?',
        preparation='mouse VisP, experiment4863, two already-labeled excitatory pairs; not a connection-discovery sample',
        bio_starting_mechanism='C dV/dt=-gL(V-EL)+I_syn; AP-triggered PSP kernel. Depression resource recurrence is the fast-inactivation reduction of Tsodyks-Markram1997, doi:10.1073/pnas.94.2.719.',
        ce_delta='A073/A074 history-dependent efficacy versus constant efficacy. Positive spatial mobility mapping A017 is deferred until conductance and independent cost observations are calibrated.',
        data_provenance='Allen synphys r2.1; Campagnola2022 doi:10.1126/science.abj5861; existing fixed remote NWB version and DB-linked point identities',
        prior_exposure='Pair121538 IC36..101 metadata and producer kinetics were inspected earlier; raw IC36..81 event responses were not analyzed in previous local scripts. Producer fitted kinetics are NOT used as parameters. Pair labels were known. This is a new within-recording forecast, not independent validation of producer labels.',
        split=dict(train=list(range(36, 56)), temporal=list(range(56, 77)), frequency=list(range(77, 82))),
        measurement_model='NWB conversion/offset and electrode_name identity; identical clocks. Six 2ms post-AP bins minus[-8,-3)ms baseline. Predict same baseline subtraction including residual earlier PSPs, without filtering or deconvolution of the measured trace.',
        command_rule='Exactly12 positive pulses >100pA above median command in[0,.01)s; durations1.4..1.7ms. First7 intervals20ms (36..76) or50ms (77..81). Source0 onsets additionally match DB within1sample.',
        ap_rule='Upward -20mV crossing, following peak >=0mV within2ms, local positive slope>=20V/s, refractory2ms. Exactly one candidate in each command[-.5,+8)ms and no extra qualifying candidates within entire train; no postsynaptic release-success filtering.',
        quality='Post command constant within0.05pA across train. Pre/post ADC finite. Post pretrain[-.1,-.01)s mean in[-75,-65]mV, no post voltage >=-20mV in sampled PSP bins. These define the small-PSP operating domain; every exclusion is retained.',
        observables='AP fidelity, six baseline-subtracted PSP bins (mV), no-input control bins, baseline potential/noise, per-sweep MSE. One animal/recording; pulses are not independent animals.',
        controls='Zero prediction; constant-efficacy kernel with its own training fit; pre-input quiet pseudo-events .15+.025*k seconds, k0..11, with all five commands required quiet. Quiet events are descriptive noise controls, not randomized sham or a guarantee against post-stimulus drift.',
        models=dict(kernel='unit-peak difference of exponentials, causal nonnegative lag',
                    latency_ms=[0, .5, 1, 1.5, 2, 3, 4], rise_ms=[.5, 1, 2, 4], decay_ms=[8, 16, 32, 64],
                    depression_U=[.1, .3, .5, .7, .9], depression_tau_s=[.05, .15, .5, 1.5, 5],
                    facilitation_F=[.25, .5, 1, 2], facilitation_tau_s=[.02, .05, .1, .3, 1],
                    amplitude='one nonnegative peak PSP scale per pair, fitted only on train; initial resource1 and initial facilitation0 at each train',
                    facilitation='q_n=1+F*sum_{m<n}exp(-(t_n-t_m)/tau); phenomenological efficacy, NOT a release probability'),
        model_selection='Training MSE only selects each model kernel/grid parameters and amplitude. No held-out refit or per-sweep outcome-derived gains. Cross-pulse kernel overlap is included in ALL models.',
        estimand='Within-recording predictive MSE gain over zero and over constant efficacy, per pair and held-out stratum; no causal effect estimand',
        residual_rule='Necessary predictive gate: >=10 train, >=10 temporal, >=3 frequency usable sweeps, lower MSE than zero and than constant in BOTH held-out strata; temporal per-sweep paired-gain bootstrap95%lower bound >0 for both comparisons. Bootstrap10000 seed4863. This gate is necessary, not sufficient for mechanism or L2 claims.',
        falsifier='Failure of held-out gain prevents selecting history-dependent efficacy from this record; AP/command/operating-state failures prevent the specified PSP model test, not existence of a synapse.',
        revision_trigger='Keep this result and split immutable; failed feature shape, state drift or unreliable AP detection motivates a separately labeled model/measurement revision.',
        claim_ceiling='BIO_EVIDENCE_L1 bounded AP/PSP observations. No causal STP identification, calibrated synaptic conductance, independently measured g, whole-circuit reconstruction or whole-brain claim.',
    ))
    print('FROZEN', CONTRACT.name, sha(CONTRACT), flush=True)


def spike_indices(v_mV, fs):
    crossings = np.flatnonzero((v_mV[:-1] < -20) & (v_mV[1:] >= -20)) + 1
    accepted = []
    for i in crossings:
        if accepted and (i-accepted[-1])/fs < .002:
            continue
        a, b = max(0, i-round(.001*fs)), min(len(v_mV), i+round(.002*fs)+1)
        if b-a < 3:
            continue
        # mV/sample * samples/s /1000 = V/s.
        if np.max(v_mV[i:b]) >= 0 and np.max(np.diff(v_mV[a:b]))*fs/1000 >= 20:
            accepted.append(int(i))
    return np.array(accepted, dtype=int)


def efficacy(times, model, strength=0., tau=1.):
    times = np.asarray(times, float)
    if model == 'constant':
        return np.ones(len(times))
    out = np.ones(len(times))
    for n in range(1, len(times)):
        decay = np.exp(-(times[n]-times[n-1])/tau)
        if model == 'depression':
            out[n] = 1-(1-(1-strength)*out[n-1])*decay
        elif model == 'facilitation':
            out[n] = 1+(out[n-1]-1+strength)*decay
        else:
            raise ValueError(model)
    return out


def kernel_integral(t, rise, decay):
    t = np.maximum(np.asarray(t, float), 0.)
    peak = np.log(decay/rise)/(1/rise-1/decay)
    norm = np.exp(-peak/decay)-np.exp(-peak/rise)
    return (decay*(-np.expm1(-t/decay))-rise*(-np.expm1(-t/rise)))/norm


def kernel_basis(times, lag, rise, decay):
    """Exact window means, including baseline tails from EVERY prior AP."""
    times = np.asarray(times, float)
    delta = times[:, None, None]-times[None, None, :]-lag
    lo = delta+BINS[None, :, 0, None]
    hi = delta+BINS[None, :, 1, None]
    mean = (kernel_integral(hi, rise, decay)-kernel_integral(lo, rise, decay))/(hi-lo)
    blo, bhi = delta+BASELINE[0], delta+BASELINE[1]
    baseline = (kernel_integral(bhi, rise, decay)-kernel_integral(blo, rise, decay))/(bhi-blo)
    return (mean-baseline).reshape(-1, len(times))


def model_grid(c):
    rows = [('constant', 0., 1.)]
    rows += [('depression', u, tau) for u in c['depression_U'] for tau in c['depression_tau_s']]
    rows += [('facilitation', f, tau) for f in c['facilitation_F'] for tau in c['facilitation_tau_s']]
    return rows


def fit_models(records, config):
    if not records:
        return {}
    times = [np.array(r['spike_times_s']) for r in records]
    y = np.array([r['psp_bins_mV'] for r in records]).reshape(len(records), -1)
    grid = model_grid(config)
    weights = np.array([[efficacy(t, *g) for g in grid] for t in times]).transpose(0, 2, 1)
    best = {}
    for lag_ms in config['latency_ms']:
        for rise_ms in config['rise_ms']:
            for decay_ms in config['decay_ms']:
                basis = np.array([kernel_basis(t, lag_ms/1000, rise_ms/1000, decay_ms/1000) for t in times])
                x = np.einsum('sbn,sng->sbg', basis, weights)
                xx = np.sum(x*x, axis=(0, 1))
                xy = np.sum(x*y[:, :, None], axis=(0, 1))
                amplitudes = np.maximum(0., xy/np.maximum(xx, 1e-30))
                mse = np.mean((y[:, :, None]-x*amplitudes)**2, axis=(0, 1))
                for i, (name, strength, tau) in enumerate(grid):
                    if name not in best or mse[i] < best[name]['train_mse_mV2']:
                        best[name] = dict(model=name, strength=strength, tau_s=tau, lag_ms=lag_ms,
                                          rise_ms=rise_ms, decay_ms=decay_ms,
                                          amplitude_mV=float(amplitudes[i]), train_mse_mV2=float(mse[i]))
    return best


def predict(record, model):
    times = np.array(record['spike_times_s'])
    return model['amplitude_mV'] * (kernel_basis(times, model['lag_ms']/1000, model['rise_ms']/1000,
                                               model['decay_ms']/1000) @ efficacy(times, model['model'], model['strength'], model['tau_s']))


def mean_window(f, node, lo, hi, scale):
    fs = node['rate']
    a, b = round(lo*fs), round(hi*fs)
    if not (0 <= a < b <= node['samples']):
        raise ValueError('window outside record')
    v = (np.asarray(f[node['path']+'/data'][a:b], float)*node['conversion']+node['offset'])*scale
    if not np.isfinite(v).all():
        raise ValueError('nonfinite ADC')
    return v


def features(f, node, centers):
    values, peaks = [], []
    for center in centers:
        baseline = mean_window(f, node, center+BASELINE[0], center+BASELINE[1], 1e3).mean()
        bins = [mean_window(f, node, center+lo, center+hi, 1e3) for lo, hi in BINS]
        values.append([float(v.mean()-baseline) for v in bins])
        peaks.extend(float(v.max()) for v in bins)
    return values, max(peaks)


def extract(f, sweep, pair, db_record):
    nodes = {}
    for group, kind in [('acquisition/timeseries', 'voltage'), ('stimulus/presentation', 'command')]:
        for key in f[group]:
            if key.startswith(f'data_{sweep:05d}_') and 'electrode_name' in f[group][key]:
                node = describe(f[group][key])
                assert node['unit'] == ('V' if kind == 'voltage' else 'A')
                nodes[kind, node['device']] = node
    pre, post = pair['pre_device'], pair['post_device']
    assert set(nodes) == {(k, d) for k in ('voltage', 'command') for d in (0, 1, 3, 5, 6)}
    assert len({(n['rate'], n['start'], n['samples']) for n in nodes.values()}) == 1
    fs = nodes['voltage', pre]['rate']
    command = mean_window(f, nodes['command', pre], 0, nodes['command', pre]['samples']/fs, 1e12)
    base = np.median(command[:round(.01*fs)])
    active = command > base+100
    starts = np.flatnonzero(np.diff(active.astype(int), prepend=0) == 1)
    stops = np.flatnonzero(np.diff(active.astype(int), append=0) == -1)+1
    record = dict(sweep=sweep, pair_id=pair['pair_id'], rate_Hz=fs, start_s=nodes['voltage', pre]['start'],
                  command_pulse_count=len(starts), nodes={f'{kind}_{device}': n for (kind, device), n in nodes.items()}, usable=False)
    if len(starts) != 12 or len(stops) != 12:
        record['exclusion'] = 'not12_command_pulses'; return record
    onsets = starts/fs
    record['command_onsets_s'] = onsets.tolist()
    record['command_amplitudes_pA'] = [float(command[a]-base) for a in starts]
    record['command_duration_ms'] = ((stops-starts)/fs*1000).tolist()
    expected = .02 if sweep <= 76 else .05
    assert np.max(np.abs(np.diff(onsets[:8])-expected)) <= 1/fs+1e-9
    assert np.all((stops-starts)/fs >= .0014) and np.all((stops-starts)/fs <= .0017)
    if pre == 0:
        assert np.max(np.abs(onsets-np.array([p['onset_time'] for p in db_record['pulses']]))) <= 1/fs+1e-9
        record['producer_spike_counts'] = [p['n_spikes'] for p in db_record['pulses']]
        record['producer_alignment_available'] = [p['first_spike_time'] is not None for p in db_record['pulses']]
    left = round((onsets[0]-.01)*fs)/fs
    right = round((onsets[-1]+.02)*fs)/fs
    pre_v = mean_window(f, nodes['voltage', pre], left, right, 1e3)
    detected = left+spike_indices(pre_v, fs)/fs
    associated = [detected[(detected >= t-.0005) & (detected < t+.008)] for t in onsets]
    record['spike_counts_per_command'] = [len(a) for a in associated]
    record['all_detected_spike_times_s'] = detected.tolist()
    if len(detected) != 12 or any(len(a) != 1 for a in associated):
        record['exclusion'] = 'AP_fidelity_or_extra_AP'; return record
    spikes = np.array([a[0] for a in associated])
    record['spike_times_s'] = spikes.tolist()
    record['command_to_threshold_ms'] = ((spikes-onsets)*1000).tolist()
    post_command = mean_window(f, nodes['command', post], onsets[0]-.1, right, 1e12)
    record['post_command_span_pA'] = float(np.ptp(post_command))
    baseline = mean_window(f, nodes['voltage', post], onsets[0]-.1, onsets[0]-.01, 1e3)
    record['post_baseline_mV'] = float(baseline.mean())
    record['post_baseline_sd_mV'] = float(baseline.std(ddof=1))
    if np.ptp(post_command) > .05:
        record['exclusion'] = 'postsynaptic_command_not_constant'; return record
    values, peak = features(f, nodes['voltage', post], spikes)
    record['psp_bins_mV'] = values
    record['post_peak_in_bins_mV'] = peak
    quiet = .15+np.arange(12)*.025
    for device in (0, 1, 3, 5, 6):
        q = mean_window(f, nodes['command', device], .14, .445, 1e12)
        assert np.ptp(q) <= .05
    record['quiet_bins_mV'], _ = features(f, nodes['voltage', post], quiet)
    if not (-75 <= baseline.mean() <= -65) or peak >= -20:
        record['exclusion'] = 'post_operating_domain'; return record
    record['usable'] = True
    return record


def bootstrap_gain(values):
    values = np.asarray(values, float)
    if not len(values):
        return None
    rng = np.random.default_rng(4863)
    boot = values[rng.integers(0, len(values), size=(10000, len(values)))].mean(axis=1)
    return dict(mean_mV2=float(values.mean()), ci95_mV2=np.quantile(boot, [.025, .975]).tolist(),
                n_sweeps=len(values), assumption='sweep resampling; serial dependence can make this interval optimistic')


def summarize(records, contract, pair):
    groups = {k: [r for r in records if r['sweep'] in sweeps and r['usable']] for k, sweeps in contract['split'].items()}
    models = fit_models(groups['train'], contract['models'])
    output = dict(pair=pair, all_sweeps=len(records), usable_counts={k: len(v) for k, v in groups.items()}, models=models,
                  exclusion_counts={}, scores={}, predictive_gate={})
    for r in records:
        if not r['usable']:
            label = r['exclusion']; output['exclusion_counts'][label] = output['exclusion_counts'].get(label, 0)+1
    for group, rows in groups.items():
        scored = []
        for r in rows:
            y = np.array(r['psp_bins_mV']).ravel()
            entry = dict(sweep=r['sweep'], zero=float(np.mean(y*y)), quiet=float(np.mean(np.array(r['quiet_bins_mV'])**2)))
            for name, model in models.items():
                prediction = predict(r, model)
                entry[name] = float(np.mean((y-prediction)**2))
            scored.append(entry)
        if not scored:
            output['scores'][group] = dict(n=0); continue
        scores = {k: float(np.mean([r[k] for r in scored])) for k in ['zero', 'quiet']+list(models)}
        output['scores'][group] = dict(n=len(scored), mse_mV2=scores, per_sweep=scored,
            gain_vs_zero={name: bootstrap_gain([r['zero']-r[name] for r in scored]) for name in models},
            gain_vs_constant={name: bootstrap_gain([r['constant']-r[name] for r in scored]) for name in models if name != 'constant'})
    sufficient = all(len(groups[k]) >= n for k, n in [('train', 10), ('temporal', 10), ('frequency', 3)])
    for name in ('depression', 'facilitation'):
        passed = sufficient and name in models
        if passed:
            for group in ('temporal', 'frequency'):
                s = output['scores'][group]
                passed = passed and s['mse_mV2'][name] < min(s['mse_mV2']['zero'], s['mse_mV2']['constant'])
            temporal = output['scores']['temporal']
            passed = passed and temporal['gain_vs_zero'][name]['ci95_mV2'][0] > 0 and temporal['gain_vs_constant'][name]['ci95_mV2'][0] > 0
        output['predictive_gate'][name] = bool(passed)
    return output


class TrackedRanges(raw.CachedRanges):
    def __init__(self):
        super().__init__(); self.used = {}

    def block(self, start):
        data = super().block(start)
        self.used[str(start)] = self.manifest['blocks'][str(start)]
        return data


def run(fetch):
    if RESULT.exists():
        raise FileExistsError('Preserve previous result')
    c = json.loads(CONTRACT.read_text(encoding='utf-8'))
    assert c['code_sha256'] == sha(Path(__file__))
    for path, digest in c['inputs'].items():
        assert sha(ROOT/path) == digest
    assert c['execution']['executable'] == sys.executable and c['execution']['python'] == platform.python_version()
    assert c['execution']['numpy'] == np.__version__ and c['execution']['h5py'] == h5py.__version__
    assert c['execution']['runner_sha256'] == sha(ROOT/c['execution']['runner'])
    source = json.loads(IDENTITY.read_text(encoding='utf-8'))
    cells = {r['cell']: r for r in source['cells']}
    pairs = []
    for p in source['pairs']:
        if p['pair_id'] in c['pair_ids']:
            a, b = cells[p['pre_cell_id']], cells[p['post_cell_id']]
            d = np.array(b['position'])-a['position']
            pairs.append(dict(pair_id=p['pair_id'], pre_cell=p['pre_cell_id'], post_cell=p['post_cell_id'],
                              pre_device=a['device'], post_device=b['device'], displacement_m=d.tolist(),
                              soma_distance_um=float(np.linalg.norm(d)*1e6), direction_unit=(d/np.linalg.norm(d)).tolist()))
    inventory = json.loads(INVENTORY.read_text(encoding='utf-8'))['pairs'][0]
    db_records = {int(r['post']['sweep']): r for r in inventory['records']}
    cache = BASE/'raw_ranges'/EXT
    before = json.loads((cache/'manifest.json').read_text())
    assert before['remote'] == c['remote']
    raw.URL, raw.CACHE = c['remote']['url'], cache
    raw.LIMIT = sum(b['bytes'] for b in before['blocks'].values())+128*1024*1024
    records = []
    with (TrackedRanges() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote == c['remote']
        with h5py.File(reader, 'r') as f:
            for sweep in sorted(sum(c['split'].values(), [])):
                for pair in pairs:
                    records.append(extract(f, sweep, pair, db_records[sweep]))
                print('AP_TRAIN', sweep, [(r['pair_id'], r.get('exclusion', 'usable')) for r in records[-2:]], flush=True)
        provenance = dict(remote=reader.remote, used_blocks=reader.used,
                          new_blocks={k: v for k, v in reader.manifest['blocks'].items() if k not in before['blocks']})
    summaries = [summarize([r for r in records if r['pair_id'] == p['pair_id']], c, p) for p in pairs]
    result = dict(contract_sha256=sha(CONTRACT), code_sha256=sha(Path(__file__)), provenance=provenance,
                  records=records, summaries=summaries, claim_ceiling=c['claim_ceiling'])
    save(RESULT, result)
    print(json.dumps(dict(new_bytes=sum(v['bytes'] for v in provenance['new_blocks'].values()),
                         summaries=[{k: s[k] for k in ('pair', 'usable_counts', 'models', 'exclusion_counts', 'predictive_gate')} for s in summaries]), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'run'])
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    freeze() if args.action == 'freeze' else run(args.fetch)
