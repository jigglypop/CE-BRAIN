"""Join seven VC sweeps to released measurement state; default offline.

The immutable medium cache is extended only in a separate, 128 KiB overlay.
Command reconstruction and baseline IR drop are not measured membrane voltage.
"""
import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import platform

from vc20hz_source_inputs import HERE, ROOT, LayeredRanges, sha
from medium_recording_lookup import ReadVFS, apsw

BASE = ROOT/'data/external/allen_synphys_r21/medium_ranges'
OVERLAY = ROOT/'data/external/allen_synphys_r21/vc20hz_medium_ranges/1574292898.139'
BASE_SHA = '8f7f88ae8b62f67312c9f34616bc2feb280cc7b24db62a59b5b8a7c44d057bab'
INPUT_SHA = '2f22c6fad05f33ee03ae5d6d39f56d706c883da2207b057692295d8ff333b087'
DEPENDENCIES = {
    'vc20hz_source_inputs.py': '2a10fbf34a3c15b0f33765baf6b335249ebb06647d47cda6429b4d6b123227cb',
    'medium_recording_lookup.py': '0d2ee2f4a52cc21bbcf940b8c5642ffcb66f458d72aaf78bc3d4b69a85b6edf9',
    'raw_metadata.py': '5aa32fce7a19372183cf304ecf70bcd1d168dc723ffcffbc74f0711d83db50ae',
}
CHANNELS = {2: 'AD2', 4: 'AD8', 5: 'AD9'}
FIELDS = {
    'r': ('id', 'sync_rec_id', 'electrode_id', 'start_time', 'sample_rate', 'device_name', 'stim_name', 'stim_meta'),
    'p': ('id', 'recording_id', 'clamp_mode', 'patch_mode', 'baseline_potential', 'baseline_current',
          'baseline_noise_stdev', 'nearest_test_pulse_id', 'qc_pass', 'access_adj_baseline_potential'),
    't': ('id', 'recording_id', 'electrode_id', 'start_index', 'stop_index', 'baseline_current',
          'baseline_potential', 'access_resistance', 'access_resistance_lowpass', 'input_resistance',
          'capacitance', 'time_constant'),
}
JOIN = ('SELECT '+', '.join(f'{a}.{k} AS {a}_{k}' for a, fields in FIELDS.items() for k in fields)+
        ' FROM recording r INDEXED BY ix_recording_sync_rec_id'
        ' LEFT JOIN patch_clamp_recording p INDEXED BY ix_patch_clamp_recording_recording_id ON p.recording_id=r.id'
        ' LEFT JOIN test_pulse t ON t.id=p.nearest_test_pulse_id'
        ' WHERE r.sync_rec_id=? AND r.electrode_id IN (?,?,?)')


def query(db, sql, args=()):
    cursor = db.cursor()
    result = cursor.execute(sql, args)
    try:
        keys = [d[0] for d in cursor.get_description()]
    except apsw.ExecutionCompleteError:
        return []
    return [dict(zip(keys, row)) for row in result]


def indexed_query(db, sql, args, plans):
    plan = query(db, 'EXPLAIN QUERY PLAN '+sql, args)
    if not plan or any('SCAN ' in row['detail'].upper() for row in plan):
        raise ValueError('Unbounded table scan refused')
    plans.append(dict(sql=sql, arguments=list(args), plan=plan))
    return query(db, sql, args)


def split_join(row):
    return {a: {k: row[a+'_'+k] for k in fields} for a, fields in FIELDS.items()}


def stimulus_items(node):
    yield node
    for child in node.get('items', []):
        yield from stimulus_items(child)


def positive_schedule(items, command):
    expected = []
    for item in items:
        args = item.get('args', {})
        if args.get('amplitude', 0) <= 0:
            continue
        if item.get('type') == 'SquarePulseTrain':
            expected.extend((args['start_time']+k*args['interval'], args['pulse_duration'], args['amplitude'])
                            for k in range(args['n_pulses']))
        elif item.get('type') == 'SquarePulse':
            expected.append((args['start_time'], args['duration'], args['amplitude']))
    actual = sorted((x for x in command['all_command_intervals'] if x['delta_min_V'] > 0),
                    key=lambda x: x['start_s'])
    expected.sort()
    if not expected or len(expected) != len(actual):
        return dict(matches=False, expected_pulses=len(expected), actual_pulses=len(actual))
    start_error = max(abs(e[0]-a['start_s']) for e, a in zip(expected, actual))
    duration_error = max(abs(e[1]-a['duration_s']) for e, a in zip(expected, actual))
    amplitude_error = max(abs(e[2]-a[k]) for e, a in zip(expected, actual)
                          for k in ('delta_min_V', 'delta_max_V'))
    amplitudes_match = all(math.isclose(e[2], a[k], rel_tol=1e-6, abs_tol=1e-9)
                           for e, a in zip(expected, actual) for k in ('delta_min_V', 'delta_max_V'))
    return dict(matches=start_error <= 2/command['rate'] and duration_error <= 2/command['rate'] and amplitudes_match,
                expected_pulses=len(expected), actual_pulses=len(actual), max_start_error_s=start_error,
                max_duration_error_s=duration_error, max_amplitude_error_V=amplitude_error)


def diagnose(recording, patch, pulse, command):
    """Retain missingness; never equate a matching recording ID with embedded TP."""
    issues = []
    items = list(stimulus_items(recording['stim_meta']))
    holding = [x['args']['amplitude'] for x in items
               if x.get('type') == 'Offset' and x.get('args', {}).get('units') == 'V']
    if len(holding) != 1:
        issues.append('holding_offset_not_unique')
    holding_v = holding[0] if len(holding) == 1 else None
    is_vc = patch['id'] is not None and patch['clamp_mode'] == 'vc'
    if not is_vc:
        issues.append('missing_or_non_vc_patch')
    if patch['qc_pass'] != 1:
        issues.append('minimal_qc_not_passed')
    if holding_v is not None and is_vc and (patch['baseline_potential'] is None or not math.isclose(
            holding_v, patch['baseline_potential'], rel_tol=0, abs_tol=1e-9)):
        issues.append('holding_baseline_disagreement')
    tp_meta = [x['args'] for x in items if x.get('type') == 'SquarePulse'
               and x.get('args', {}).get('description') == 'test pulse']
    a, b = pulse['start_index'], pulse['stop_index']
    same_electrode = pulse['id'] is not None and pulse['electrode_id'] == recording['electrode_id']
    same_recording = pulse['id'] is not None and pulse['recording_id'] == recording['id']
    valid_window = a is not None and b is not None and 0 <= a < b <= command['samples']
    negative = [x for x in command['all_command_intervals'] if x['delta_max_V'] < 0]
    covered = valid_window and len(negative) == 1 and a <= negative[0]['start_index'] < negative[0]['stop_index'] <= b
    meta_matches = len(tp_meta) == 1 and len(negative) == 1 and all((
        abs(tp_meta[0]['start_time']-negative[0]['start_s']) <= 1/command['rate'],
        abs(tp_meta[0]['duration']-negative[0]['duration_s']) <= 1/command['rate'],
        math.isclose(tp_meta[0]['amplitude'], negative[0]['delta_min_V'], rel_tol=1e-6, abs_tol=1e-9),
    ))
    embedded = bool(same_electrode and same_recording and covered and meta_matches)
    if not embedded:
        issues.append('embedded_test_pulse_not_established')
    schedule = positive_schedule(items, command)
    if not schedule['matches']:
        issues.append('positive_command_metadata_disagreement')
    resistance = pulse['access_resistance_lowpass']
    # The released producer uses the TP baseline current, not the recording's
    # quiet-region current. These are different observed quantities.
    current, potential = pulse['baseline_current'], patch['baseline_potential']
    estimate = (potential-resistance*current if is_vc and all(
        x is not None for x in (resistance, current, potential)) else None)
    stored = patch['access_adj_baseline_potential']
    residual = estimate-stored if estimate is not None and stored is not None else None
    if residual is not None and abs(residual) > 1e-10:
        issues.append('baseline_ir_drop_formula_disagreement')
    absolute = [dict(x, commanded_min_V=holding_v+command['initial_command_V']+x['delta_min_V'],
                     commanded_max_V=holding_v+command['initial_command_V']+x['delta_max_V'])
                for x in command['all_command_intervals']] if is_vc and holding_v is not None else []
    return dict(issues=issues, holding_command_V=holding_v, positive_command_schedule=schedule,
        embedded_test_pulse=dict(confirmed=embedded, same_electrode=same_electrode,
            same_recording=same_recording, indices_cover_raw_negative_pulse=bool(covered),
            stimulus_metadata_matches=bool(meta_matches), metadata=tp_meta),
        baseline_ir_drop_estimate_V=estimate, baseline_ir_drop_formula_residual_V=residual,
        baseline_ir_drop_current_source='test_pulse.baseline_current',
        command_intervals=absolute, series_compensation_settings='not available in these DB tables',
        membrane_voltage='not independently measured; baseline estimate only')


def collect(db, inputs):
    plans = []
    lookup = lambda sql, args: indexed_query(db, sql, args, plans)
    experiments = lookup('SELECT id,ext_id FROM experiment WHERE ext_id=?', ('1574292898.139',))
    if len(experiments) != 1 or experiments[0]['id'] != 3337:
        raise ValueError('Experiment identity mismatch')
    sync = lookup('SELECT id,ext_id FROM sync_rec WHERE experiment_id=?', (3337,))
    sweeps = {int(x['ext_id']): x['id'] for x in sync if int(x['ext_id']) in range(7)}
    if set(sweeps) != set(range(7)):
        raise ValueError('Missing sync sweep')
    electrodes = lookup('SELECT id,device_id FROM electrode WHERE experiment_id=?', (3337,))
    devices = {x['id']: x['device_id'] for x in electrodes if x['device_id'] in CHANNELS}
    if devices != {26623: 2, 26625: 4, 26626: 5}:
        raise ValueError('Electrode identity mismatch')
    channel_rows = {(x['sweep'], x['channel']): x for x in inputs['records']}
    if len(channel_rows) != 42:
        raise ValueError('Duplicate or missing input channels')
    rows = []
    for sweep in range(7):
        joined = lookup(JOIN, (sweeps[sweep], *sorted(devices)))
        if len(joined) != 3 or {x['r_electrode_id'] for x in joined} != set(devices):
            raise ValueError('Missing or duplicate recording join')
        for row in sorted(joined, key=lambda x: x['r_electrode_id']):
            row = split_join(row)
            recording, patch, pulse = row['r'], row['p'], row['t']
            recording['stim_meta'] = json.loads(recording['stim_meta'])
            device = devices[recording['electrode_id']]
            command = channel_rows[sweep, 'DA'+str(device)]
            current = channel_rows[sweep, CHANNELS[device]]
            if (command['unit'], current['unit']) != ('V', 'A') or any(
                    command[k] != current[k] for k in ('start', 'rate', 'samples', 'electrode')):
                raise ValueError('Current/command identity or clock mismatch')
            if command['electrode'] != 'electrode_'+str(device):
                raise ValueError('Raw electrode identity mismatch')
            rows.append(dict(sweep=sweep, device=device, recording=recording, patch=patch,
                test_pulse=pulse, command=command, current=current,
                diagnosis=diagnose(recording, patch, pulse, command)))
    first = rows[0]
    raw_start = first['command']['start']
    db_start = datetime.fromisoformat(first['recording']['start_time'])
    for row in rows:
        db_delta = (datetime.fromisoformat(row['recording']['start_time'])-db_start).total_seconds()
        row['relative_clock_residual_s'] = db_delta-(row['command']['start']-raw_start)
        row['db_raw_relative_clock_agrees_within_10us'] = abs(row['relative_clock_residual_s']) <= 1e-5
        if not row['db_raw_relative_clock_agrees_within_10us']:
            row['diagnosis']['issues'].append('db_raw_relative_clock_disagreement')
    return dict(experiment=experiments[0], sweeps=sweeps, electrodes=devices, records=rows, query_plans=plans,
        clock_policy='Use the shared NWB current/command first-sample clock for response timing. DB start_time '
                     'comes from labnotebook TimeStamp (entry time), not first-sample starting_time. '
                     'Report its variable offset; do not substitute it for NWB times.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-download', action='store_true')
    parser.add_argument('--output', type=Path, default=HERE/'vc20hz_measurement_state_result.json')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve existing result')
    for name, digest in DEPENDENCIES.items():
        if sha(HERE/name) != digest:
            raise ValueError('Dependency changed: '+name)
    input_path = HERE/'vc20hz_source_inputs_result.json'
    if sha(input_path) != INPUT_SHA:
        raise ValueError('Frozen input changed')
    inputs = json.loads(input_path.read_text(encoding='utf-8'))
    if sha(ROOT/inputs['arrays']['path']) != inputs['arrays']['sha256']:
        raise ValueError('Frozen arrays changed')
    with LayeredRanges(BASE, OVERLAY, args.allow_download, BASE_SHA, max_new=128*1024) as reader:
        vfs = ReadVFS(reader)
        db = None
        try:
            db = apsw.Connection('remote.sqlite', flags=apsw.SQLITE_OPEN_READONLY, vfs='ce_medium_readonly')
            db.execute('pragma query_only=ON')
            db.execute('pragma temp_store=MEMORY')
            out = collect(db, inputs)
        finally:
            if db is not None:
                db.close()
            vfs.unregister()
        out['provenance'] = dict(remote=reader.remote, base_manifest_sha256=reader.base_sha,
            used_base=reader.used_base, used_overlay=reader.used_overlay,
            overlay_manifest=reader.manifest_path.relative_to(ROOT).as_posix(),
            overlay_manifest_sha256=sha(reader.manifest_path) if reader.manifest_path.exists() else None,
            downloaded_this_session=reader.downloaded, max_overlay_bytes=reader.max_new)
    if sha(BASE/'manifest.json') != BASE_SHA:
        raise ValueError('Base changed during read')
    out.update(schema='allen.vc20hz.measurement-state.v1', source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_vc20hz_measurement_state.py'),
        dependency_sha256=DEPENDENCIES, input_sha256=INPUT_SHA, arrays=inputs['arrays'],
        python=platform.python_version(), apsw=apsw.apswversion(),
        units=dict(current='A', potential='V', resistance='ohm', capacitance='F', time='s'),
        interpretation='Measurement/command state only; no identified PSC, plasticity or hippocampal mechanism.')
    serialized = json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False)
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(serialized)
    print(json.dumps(dict(records=len(out['records']), new_bytes=out['provenance']['downloaded_this_session'],
        issues=[dict(sweep=r['sweep'], device=r['device'], issues=r['diagnosis']['issues']) for r in out['records']
                if r['diagnosis']['issues']], output=str(args.output))))


if __name__ == '__main__':
    main()
