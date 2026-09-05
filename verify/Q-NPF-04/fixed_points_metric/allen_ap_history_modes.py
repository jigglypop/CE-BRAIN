"""Handle recorded clamp-mode transitions without changing the frozen PSP model."""
import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
import allen_ap_history_prediction as old

HERE, ROOT, BASE = old.HERE, old.ROOT, old.BASE
CONTRACT = HERE/'allen_ap_history_modes_contract.json'
RESULT = HERE/'allen_ap_history_modes_result.json'


def freeze():
    c = json.loads(old.CONTRACT.read_text(encoding='utf-8'))
    c['parent_contract_sha256'] = old.sha(old.CONTRACT)
    c['parent_code_sha256'] = old.sha(Path(old.__file__))
    c['code_sha256'] = old.sha(Path(__file__))
    c['adapter_created_utc'] = datetime.now(timezone.utc).isoformat()
    c['interrupted_attempt'] = dict(session_id=7243, exit_code=1, last_complete_sweep=63,
        failed_sweep=64, error='AssertionError: every ADC assumed V, but device1 is A in raw sweep64',
        result_written=False, model_fit_started=False,
        exposure='Previously read36..63 feature calculations are replayed unchanged; no fitted models/holdout MSE were generated. Later raw response features remain unopened at adaptation time.')
    c['adjustment'] = 'Keep both target cells in IC (V/A) as required for PSPs. Explicitly exclude a pair if either target mode changes. Auxiliary cells may be VC (A/V), retained as a reported context change. Quiet-command tolerance is0.05pA for IC or0.001mV for VC. Do not assume all five cells keep one mode.'
    c['unchanged'] = 'All identities,46 sweep split, AP detector, PSP bins, state domain, efficacy/kernel grids, fit, MSE and necessary gate unchanged. No reclassification of prior model outcomes; none existed.'
    c['initial_cache_blocks'] = json.loads((BASE/'raw_ranges'/old.EXT/'manifest.json').read_text())['blocks']
    old.save(CONTRACT, c)
    print('FROZEN_MODE_ADAPTER', old.sha(CONTRACT))


def inspect_modes(f, sweep):
    nodes = {}
    for group, kind in [('acquisition/timeseries', 'voltage'), ('stimulus/presentation', 'command')]:
        for key in f[group]:
            if key.startswith(f'data_{sweep:05d}_') and 'electrode_name' in f[group][key]:
                node = old.describe(f[group][key])
                assert (kind, node['device']) not in nodes
                nodes[kind, node['device']] = node
    assert set(nodes) == {(k, d) for k in ('voltage', 'command') for d in (0, 1, 3, 5, 6)}
    assert len({(n['rate'], n['start'], n['samples']) for n in nodes.values()}) == 1
    modes = {}
    for d in (0, 1, 3, 5, 6):
        units = (nodes['voltage', d]['unit'], nodes['command', d]['unit'])
        assert units in [('V', 'A'), ('A', 'V')]
        modes[d] = 'ic' if units == ('V', 'A') else 'vc'
    return nodes, modes


def extract(f, sweep, pair, db_record, nodes, modes):
    pre, post = pair['pre_device'], pair['post_device']
    if modes[pre] != 'ic' or modes[post] != 'ic':
        return dict(sweep=sweep, pair_id=pair['pair_id'], usable=False, exclusion='target_clamp_mode_changed',
                    modes=modes, nodes={f'{k}_{d}': n for (k, d), n in nodes.items()})
    # Reuse the frozen extraction verbatim whenever its all-IC premise holds.
    if all(v == 'ic' for v in modes.values()):
        result = old.extract(f, sweep, pair, db_record)
        result['modes'] = modes
        return result
    fs = nodes['voltage', pre]['rate']
    command = old.mean_window(f, nodes['command', pre], 0, nodes['command', pre]['samples']/fs, 1e12)
    base = np.median(command[:round(.01*fs)])
    active = command > base+100
    starts = np.flatnonzero(np.diff(active.astype(int), prepend=0) == 1)
    stops = np.flatnonzero(np.diff(active.astype(int), append=0) == -1)+1
    r = dict(sweep=sweep, pair_id=pair['pair_id'], usable=False, modes=modes, rate_Hz=fs,
             start_s=nodes['voltage', pre]['start'], command_pulse_count=len(starts),
             nodes={f'{k}_{d}': n for (k, d), n in nodes.items()})
    if len(starts) != 12 or len(stops) != 12:
        r['exclusion'] = 'not12_command_pulses'; return r
    onsets = starts/fs
    r.update(command_onsets_s=onsets.tolist(), command_amplitudes_pA=[float(command[a]-base) for a in starts],
             command_duration_ms=((stops-starts)/fs*1000).tolist())
    assert np.max(np.abs(np.diff(onsets[:8])-(.02 if sweep <= 76 else .05))) <= 1/fs+1e-9
    assert np.all((stops-starts)/fs >= .0014) and np.all((stops-starts)/fs <= .0017)
    if pre == 0:
        assert np.max(np.abs(onsets-np.array([p['onset_time'] for p in db_record['pulses']]))) <= 1/fs+1e-9
        r['producer_spike_counts'] = [p['n_spikes'] for p in db_record['pulses']]
        r['producer_alignment_available'] = [p['first_spike_time'] is not None for p in db_record['pulses']]
    left, right = round((onsets[0]-.01)*fs)/fs, round((onsets[-1]+.02)*fs)/fs
    v = old.mean_window(f, nodes['voltage', pre], left, right, 1e3)
    detected = left+old.spike_indices(v, fs)/fs
    associated = [detected[(detected >= t-.0005) & (detected < t+.008)] for t in onsets]
    r['spike_counts_per_command'] = [len(a) for a in associated]
    r['all_detected_spike_times_s'] = detected.tolist()
    if len(detected) != 12 or any(len(a) != 1 for a in associated):
        r['exclusion'] = 'AP_fidelity_or_extra_AP'; return r
    spikes = np.array([a[0] for a in associated])
    r['spike_times_s'] = spikes.tolist()
    r['command_to_threshold_ms'] = ((spikes-onsets)*1000).tolist()
    pc = old.mean_window(f, nodes['command', post], onsets[0]-.1, right, 1e12)
    b = old.mean_window(f, nodes['voltage', post], onsets[0]-.1, onsets[0]-.01, 1e3)
    r.update(post_command_span_pA=float(np.ptp(pc)), post_baseline_mV=float(b.mean()), post_baseline_sd_mV=float(b.std(ddof=1)))
    if np.ptp(pc) > .05:
        r['exclusion'] = 'postsynaptic_command_not_constant'; return r
    r['psp_bins_mV'], peak = old.features(f, nodes['voltage', post], spikes)
    r['post_peak_in_bins_mV'] = peak
    for d in (0, 1, 3, 5, 6):
        scale, tol = (1e12, .05) if modes[d] == 'ic' else (1e3, .001)
        q = old.mean_window(f, nodes['command', d], .14, .445, scale)
        assert np.ptp(q) <= tol
    r['quiet_bins_mV'], _ = old.features(f, nodes['voltage', post], .15+np.arange(12)*.025)
    if not (-75 <= b.mean() <= -65) or peak >= -20:
        r['exclusion'] = 'post_operating_domain'; return r
    r['usable'] = True
    return r


def run(fetch):
    if RESULT.exists():
        raise FileExistsError('Preserve result')
    c = json.loads(CONTRACT.read_text(encoding='utf-8'))
    parent = json.loads(old.CONTRACT.read_text(encoding='utf-8'))
    assert c['code_sha256'] == old.sha(Path(__file__))
    assert c['parent_contract_sha256'] == old.sha(old.CONTRACT)
    assert c['parent_code_sha256'] == old.sha(Path(old.__file__)) == parent['code_sha256']
    for k in ('split', 'models', 'ap_rule', 'command_rule', 'residual_rule'):
        assert c[k] == parent[k]
    for path, digest in c['inputs'].items():
        assert old.sha(ROOT/path) == digest
    assert c['execution']['executable'] == sys.executable and c['execution']['python'] == platform.python_version()
    assert c['execution']['numpy'] == np.__version__ and c['execution']['h5py'] == h5py.__version__
    assert c['execution']['runner_sha256'] == old.sha(ROOT/c['execution']['runner'])
    identity = json.loads(old.IDENTITY.read_text(encoding='utf-8'))
    cells = {r['cell']: r for r in identity['cells']}
    pairs = []
    for p in identity['pairs']:
        if p['pair_id'] in c['pair_ids']:
            a, b = cells[p['pre_cell_id']], cells[p['post_cell_id']]
            d = np.array(b['position'])-a['position']
            pairs.append(dict(pair_id=p['pair_id'], pre_cell=p['pre_cell_id'], post_cell=p['post_cell_id'],
                pre_device=a['device'], post_device=b['device'], displacement_m=d.tolist(),
                soma_distance_um=float(np.linalg.norm(d)*1e6), direction_unit=(d/np.linalg.norm(d)).tolist()))
    inventory = json.loads(old.INVENTORY.read_text(encoding='utf-8'))['pairs'][0]
    db = {int(r['post']['sweep']): r for r in inventory['records']}
    cache = BASE/'raw_ranges'/old.EXT
    before = json.loads((cache/'manifest.json').read_text())
    assert before['remote'] == c['remote']
    old.raw.URL, old.raw.CACHE = c['remote']['url'], cache
    old.raw.LIMIT = sum(v['bytes'] for v in before['blocks'].values())+128*1024*1024
    records = []
    with (old.TrackedRanges() if fetch else old.OfflineRanges(cache)) as reader:
        assert reader.remote == c['remote']
        with h5py.File(reader, 'r') as f:
            for sweep in sorted(sum(c['split'].values(), [])):
                nodes, modes = inspect_modes(f, sweep)
                for pair in pairs:
                    records.append(extract(f, sweep, pair, db[sweep], nodes, modes))
                print('AP_MODES', sweep, modes, [(r['pair_id'], r.get('exclusion', 'usable')) for r in records[-2:]], flush=True)
        provenance = dict(remote=reader.remote, used_blocks=reader.used,
            new_blocks={k: v for k, v in reader.manifest['blocks'].items() if k not in before['blocks']})
    summaries = [old.summarize([r for r in records if r['pair_id'] == p['pair_id']], c, p) for p in pairs]
    result = dict(contract_sha256=old.sha(CONTRACT), code_sha256=old.sha(Path(__file__)), provenance=provenance,
                  records=records, summaries=summaries, claim_ceiling=c['claim_ceiling'])
    old.save(RESULT, result)
    print(json.dumps([dict(pair=s['pair']['pair_id'], usable=s['usable_counts'], exclusions=s['exclusion_counts'],
                          models=s['models'], gate=s['predictive_gate']) for s in summaries], indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('action', choices=['freeze', 'run']); p.add_argument('--fetch', action='store_true')
    args = p.parse_args()
    freeze() if args.action == 'freeze' else run(args.fetch)
