"""Inspect current commands for all later IC protocols, without reading responses.

This is an input census, not a preregistration or a small-signal response test.
Stored notebook response summaries for these sweeps have already been exposed.
"""
import json
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, raw, sha, text
from electrical_star_vc_inputs import settings

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'electrical_star_ic_input_census_result.json'
DEVICES = [0, 1, 2, 4, 5, 6, 7]
SWEEPS = list(range(16, 89))


def segments(values, rate):
    cuts = np.r_[0, np.flatnonzero(np.abs(np.diff(values)) > .005) + 1, len(values)]
    return [dict(start_s=float(a / rate), end_s=float(b / rate), duration_s=float((b-a) / rate),
                 command_pA=float(np.mean(values[a:b])), sd_pA=float(np.std(values[a:b])))
            for a, b in zip(cuts[:-1], cuts[1:])]


def direction_summary(values, rate):
    # The 7x7 Gram calculation avoids allocating a large full SVD.
    gram = values @ values.T / values.shape[1]
    singular = np.sqrt(np.maximum(np.linalg.eigvalsh(gram)[::-1], 0))
    threshold = max(1e-4, 1e-6 * singular[0])
    active = np.abs(values) > .005
    solo = active.sum(axis=0) == 1
    return dict(singular_rms_pA=singular.tolist(), rank=int(np.sum(singular > threshold)),
        rank_threshold_pA=float(threshold), peak_positive_pA=np.maximum(values.max(axis=1), 0).tolist(),
        peak_negative_pA=np.minimum(values.min(axis=1), 0).tolist(),
        solo_positive_duration_s_by_device=[float(np.sum(solo & (row > .005)) / rate) for row in values],
        solo_negative_duration_s_by_device=[float(np.sum(solo & (row < -.005)) / rate) for row in values])


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    code_hash = sha(Path(__file__))
    protocol_path = HERE / 'electrical_star_all_protocols_result.json'
    protocol = json.loads(protocol_path.read_text(encoding='utf8'))
    records = {(r['kind'], r['sweep'], r['device']): r for r in protocol['records']}
    labels = {}
    for row in protocol['textual_records']:
        fields = row['fields']
        sw = [int(float(v)) for v in fields.get('SweepNum', []) if v]
        lab = sorted({v for v in fields.get('Stim Wave Name', []) if v})
        if sw and lab:
            labels[sw[0]] = lab
    cache = BASE / 'raw_ranges' / '1552517188.758'
    manifest = json.loads((cache / 'manifest.json').read_text())
    initial_bytes = sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL, raw.CACHE, raw.LIMIT = protocol['provenance']['remote']['url'], cache, initial_bytes + 32*1024*1024
    results = []
    with raw.CachedRanges() as reader:
        assert reader.remote == protocol['provenance']['remote']
        with h5py.File(reader, 'r') as f:
            for sweep in SWEEPS:
                commands, channels = [], []
                for device in DEVICES:
                    cmd, adc = records['command', sweep, device], records['acquisition', sweep, device]
                    assert cmd['unit'] == 'A' and adc['unit'] == 'V'
                    assert all(cmd[k] == adc[k] for k in ['samples', 'rate', 'start'])
                    assert cmd['path'].startswith('/stimulus/presentation/')
                    node = f[cmd['path']]
                    values = (np.asarray(node['data'][()], dtype=float) * cmd['conversion'] + cmd['offset']) * 1e12
                    assert np.isfinite(values).all()
                    baseline = float(np.median(values[:100]))
                    commands.append(values - baseline)
                    channels.append(dict(device=device, acquisition_path=adc['path'], command_path=cmd['path'],
                        baseline_command_pA=baseline, segments=segments(values, cmd['rate']),
                        incremental_instrument_settings=settings(adc['attributes'].get('comment', ''), device)))
                commands = np.asarray(commands)
                rate = cmd['rate']
                after = commands[:,int(round(.05*rate)):]
                assert after.shape[1] > 0
                result = dict(sweep=sweep, protocol_labels=labels[sweep], devices=DEVICES,
                    rate=rate, samples=cmd['samples'], channels=channels,
                    all_time=direction_summary(commands, rate), after_50ms=direction_summary(after, rate))
                results.append(result)
                summary = result['after_50ms']
                print('INPUT', sweep, labels[sweep][0], 'rank', summary['rank'],
                      'min_pA', min(summary['peak_negative_pA']), 'max_pA', max(summary['peak_positive_pA']),
                      'new_bytes', reader.downloaded_this_session, flush=True)
        provenance = dict(remote=reader.remote, initial_cached_bytes=initial_bytes,
            new_download_bytes=reader.downloaded_this_session, blocks=reader.manifest['blocks'])
    assert sha(Path(__file__)) == code_hash
    result = dict(code_sha256=code_hash, protocol_sha256=sha(protocol_path),
        metadata_reader_sha256=sha(HERE/'allen_joint_inventory.py'),
        settings_reader_sha256=sha(HERE/'electrical_star_vc_inputs.py'), raw_reader_sha256=sha(Path(raw.__file__)),
        scope='Only stimulus/presentation command data arrays, IC sweeps 16..88; acquisition arrays never opened',
        exposure='Existing numerical notebook extraction includes response and QC summaries; these are not pristine holdouts',
        sweeps=results, provenance=provenance,
        limitations=['Input rank and polarity do not establish subthreshold membrane response or stationarity',
            'Per-sweep rank and per-device solo pulses concern recorded current commands, not calibrated delivered currents',
            'Incremental comments may omit unchanged instrument settings',
            'Early common TP is excluded from after_50ms summaries, but the full command segments remain available'],
        claim_ceiling='BIO_EVIDENCE_L0 intervention eligibility only')
    with OUTPUT.open('x', encoding='utf8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print('DONE', 'new_bytes', provenance['new_download_bytes'], 'sha256', sha(OUTPUT), flush=True)


if __name__ == '__main__':
    main()
