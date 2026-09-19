"""Build observed windows for the historical32 acquired cohort.

Counts describe deposited sorted events. Task and position coverage do not
establish unit-specific detection completeness. The historical cohort used a
region interpretation now under correction; this adds no neural-effect selection.
No fitting is performed here.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.io import loadmat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT/'data/external/hippocampal_reinstatement'
WINDOWS = ('precue', 'earlycue', 'latecue', 'postcue')
MOTION_COLUMNS = ('mean_x_cm', 'mean_y_cm', 'mean_speed_cm_s', 'sd_speed_cm_s',
                  'delta_x_cm', 'delta_y_cm', 'path_length_cm', 'max_speed_cm_s')
PINS = {
    HERE/'odor_place_cohort_labels_result.json': '304968b35ba65a7831ca3a4742e07500efa679834bfee362baa768e6c87b21e3',
    HERE/'odor_place_region_reference_result.json': '784bbd1190639255c6a403d6b8b17f941076440a86494d9913bc854e9c020cc1',
    DATA/'dandi001539_0.250815.1203_cohort_metadata_v1/all_assets_summary.json': '9c98884de317bce80605e70d0bd1dddfb4ecd065dc081ce6e734168687badacc',
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked(path, digest):
    path = Path(path)
    if sha(path) != digest:
        raise ValueError('Frozen input changed: '+str(path))
    return path


def unwrap(value):
    while isinstance(value, np.ndarray) and value.dtype == object and value.size == 1:
        value = value.reshape(-1)[0]
    return value


def day_slots(mat, key, day):
    days = np.asarray(mat[key], dtype=object)
    if days.ndim != 2 or days.shape[0] != 1 or not 1 <= day <= days.shape[1]:
        raise ValueError('Invalid MATLAB day axis')
    return list(np.asarray(days[0, day-1], dtype=object).reshape(-1))


def resolve_slot(slots, epoch, single_source, onsets, kind):
    if 1 <= epoch <= len(slots) and np.asarray(slots[epoch-1]).size:
        return unwrap(slots[epoch-1]), 'direct_epoch'
    if single_source and epoch > 1 and len(slots) == 1 and np.asarray(slots[0]).size:
        candidate = unwrap(slots[0])
        if kind == 'np':
            values = np.asarray(candidate, float).reshape(-1, 2)[:, 0]
            supported = np.array_equal(values, onsets)
        else:
            times = []
            for channel in np.asarray(candidate, dtype=object).reshape(-1):
                channel = unwrap(channel)
                if hasattr(channel, 'time'):
                    times.extend(np.asarray(channel.time, float).reshape(-1).tolist())
            supported = bool(times and min(times) <= onsets[0] and max(times) >= onsets[-1])
        if supported:
            return candidate, 'single_slot_verified_by_time'
    return None, 'unresolved'


def first_choice(events, offset, upper):
    """First well entry, with half-open analysis windows ending before it."""
    valid = sorted((float(t), int(side)) for t, side in events if offset < t < upper)
    if not valid:
        return None, 'no_well_entry'
    time = valid[0][0]
    sides = {s for t, s in valid if t == time}
    if len(sides) != 1:
        return None, 'simultaneous_opposite_wells'
    return (time, valid[0][1]), 'resolved'


def behavior(session, audit, dio_path, np_path):
    dio = day_slots(loadmat(dio_path, struct_as_record=False), 'dio', session['day'])
    npw = day_slots(loadmat(np_path, struct_as_record=False), 'nosepokeWindow', session['day'])
    trials = session['trials']
    epochs = audit['interval_tables']['epoch intervals']['values']
    result = [dict(choice=None, reason='unresolved_source') for _ in trials]
    source_records = []
    cursor = 0
    for source in session['sources']:
        label_path = checked(DATA/'figshare19620783_v3_labels_v1'/source['file'], source['sha256'])
        slots = day_slots(loadmat(label_path, struct_as_record=False), 'odorTriggers', session['day'])
        label = unwrap(slots[source['epoch']-1])
        onsets = np.asarray(label.allTriggers, float).reshape(-1)
        selected = trials[cursor:cursor+len(onsets)]
        np_cell, np_rule = resolve_slot(npw, source['epoch'], len(session['sources']) == 1, onsets, 'np')
        dio_cell, dio_rule = resolve_slot(dio, source['epoch'], len(session['sources']) == 1, onsets, 'dio')
        record = dict(source=source, trial_slice=[cursor, cursor+len(onsets)], np_rule=np_rule, dio_rule=dio_rule)
        if np_cell is None:
            raise ValueError('Nosepoke source unavailable')
        intervals = np.asarray(np_cell, float).reshape(-1, 2)
        expected = np.asarray([[t['start_s'], t['stop_s']] for t in selected])
        if not np.array_equal(intervals[:, 0], onsets) or not np.array_equal(intervals, expected):
            raise ValueError('Nosepoke/label/NWB times disagree')
        events = []
        if dio_cell is not None:
            channels = np.asarray(dio_cell, dtype=object).reshape(-1)
            for side in (0, 1):
                channel = unwrap(channels[side])
                times = np.asarray(channel.time, float).reshape(-1)
                states = np.asarray(channel.state).reshape(-1)
                if len(times) != len(states) or not np.isfinite(times).all() or np.any(np.diff(times) < 0):
                    raise ValueError('Invalid DIO times')
                if not set(states.tolist()) <= {0, 1}:
                    raise ValueError('Nonbinary DIO state')
                events.extend((float(t), side) for t, state in zip(times, states) if state == 1)
        for j, trial in enumerate(selected, cursor):
            epoch_row = session['task_epoch_rows'][j]
            stop = epochs['stop_time'][epoch_row]
            following = trials[j+1]['start_s'] if j+1 < len(trials) else float('inf')
            choice, reason = first_choice(events, trial['stop_s'], min(stop, following))
            if dio_cell is None:
                reason = 'unresolved_dio_epoch'
            if choice and ((choice[1] == int(trial['odor_side'] == 'right')) != trial['correct']):
                raise ValueError('Observed choice disagrees with source correctness')
            result[j] = dict(choice=choice, reason=reason, source_epoch=source['epoch'], task_epoch_row=epoch_row)
        source_records.append(record)
        cursor += len(onsets)
    if cursor != len(trials):
        raise ValueError('Source coverage incomplete')
    return result, source_records


def window_bounds(onset, offset):
    return ((onset-.5, onset), (onset, onset+.5), (offset-.5, offset), (offset, offset+.5))


def temporal_reasons(kind, start, stop, onset, offset, epoch, previous_offset, next_onset, choice_time):
    reasons = []
    if not epoch[0] <= start < stop <= epoch[1]:
        reasons.append('outside_task_epoch')
    if kind == 'precue' and start < previous_offset:
        reasons.append('overlaps_previous_nosepoke')
    if kind in {'earlycue', 'latecue'} and not onset <= start < stop <= offset:
        reasons.append('nosepoke_shorter_than_500ms')
    if kind == 'postcue' and stop > next_onset:
        reasons.append('overlaps_next_nosepoke')
    if choice_time is not None and stop > choice_time:
        reasons.append('includes_choice_or_later')
    return reasons


def position_window(times, values, start, stop, max_gap=.1):
    """Use actual half-open samples; gaps and unsupported edges are retained."""
    left, right = np.searchsorted(times, [start, stop], side='left')
    observed = times[left:right]
    reason = []
    if len(observed) < 2:
        reason.append('fewer_than_two_position_samples')
    else:
        if observed[0]-start > max_gap or stop-observed[-1] > max_gap:
            reason.append('unsupported_position_edge')
        if np.max(np.diff(observed)) > max_gap:
            reason.append('position_gap_over_100ms')
    if reason:
        return None, dict(samples=len(observed), reasons=reason)
    p = values[left:right]
    dxy = p[-1, :2]-p[0, :2]
    features = [*np.mean(p[:, :2], axis=0), np.mean(p[:, 2]), np.std(p[:, 2]),
                *dxy, np.sum(np.linalg.norm(np.diff(p[:, :2], axis=0), axis=1)), np.max(p[:, 2])]
    return np.asarray(features), dict(samples=len(observed), reasons=[],
                                     first_lag_s=float(observed[0]-start), last_lead_s=float(stop-observed[-1]),
                                     max_internal_gap_s=float(np.max(np.diff(observed))))


def unit_spikes(spikes, ends, unit_count):
    if ends.ndim != 1 or len(ends) != unit_count or not len(ends):
        raise ValueError('Spike index/unit identity length differs')
    if not np.issubdtype(ends.dtype, np.integer) or np.any(ends > len(spikes)) or np.any(ends < 0):
        raise ValueError('Invalid spike index')
    ends = ends.astype(np.int64)
    if np.any(np.diff(ends) < 0) or ends[-1] != len(spikes) or not np.isfinite(spikes).all():
        raise ValueError('Spike index or values invalid')
    units = [spikes[a:b] for a, b in zip(np.r_[0, ends[:-1]], ends)]
    if any(np.any(np.diff(values) < 0) for values in units):
        raise ValueError('Unsorted per-unit spikes')
    return units


def count_window(spikes, start, stop):
    if not np.isfinite([start, stop]).all() or stop <= start:
        raise ValueError('Invalid counting window')
    return int(np.searchsorted(spikes, stop, side='left')-np.searchsorted(spikes, start, side='left'))


def build_session(session, audit, entry):
    arrays = {}
    for key, record in entry['hdf'].items():
        path = checked(ROOT/record['path'], record['sha256'])
        if path.stat().st_size != record['bytes']:
            raise ValueError('Payload byte length changed')
        arrays[key] = np.fromfile(path, dtype=np.dtype(record['dtype_str'])).reshape(record['shape'])
    ids = audit['units']['values']['id']
    spikes = unit_spikes(arrays['/units/spike_times'], arrays['/units/spike_times_index'], len(ids))
    times = arrays['/processing/behavior/Position/SpatialSeries/timestamps']
    pos = arrays['/processing/behavior/Position/SpatialSeries/data']
    if times.ndim != 1 or pos.shape != (len(times), 3) or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError('Invalid position clock/shape')
    if not np.isfinite(pos).all():
        raise ValueError('Invalid position values')
    if entry['position_conversion'] != 1 or entry['position_offset'] != 0:
        raise ValueError('Expected pinned original position conversion')
    dio = checked(ROOT/entry['DIO']['path'], entry['DIO']['sha256'])
    npw = checked(ROOT/entry['nosepokeWindow']['path'], entry['nosepokeWindow']['sha256'])
    choices, sources = behavior(session, audit, dio, npw)
    trials = session['trials']; n = len(trials)
    counts = np.zeros((n, len(WINDOWS), len(ids)), dtype=np.int32)
    motion = np.zeros((n, len(WINDOWS), len(MOTION_COLUMNS)), dtype=float)
    valid = np.zeros((n, len(WINDOWS)), dtype=bool)
    records = []
    epochs = audit['interval_tables']['epoch intervals']['values']
    for j, (trial, observed) in enumerate(zip(trials, choices)):
        onset, offset = trial['start_s'], trial['stop_s']
        ei = observed['task_epoch_row']; epoch = (epochs['start_time'][ei], epochs['stop_time'][ei])
        prior = trials[j-1]['stop_s'] if j else -float('inf')
        following = trials[j+1]['start_s'] if j+1 < n else float('inf')
        choice = observed['choice']; ct = choice[0] if choice else None
        windows = {}
        for wi, (kind, (start, stop)) in enumerate(zip(WINDOWS, window_bounds(onset, offset))):
            reasons = temporal_reasons(kind, start, stop, onset, offset, epoch, prior, following, ct)
            feats, support = position_window(times, pos, start, stop)
            reasons.extend(support['reasons'])
            if choice is None:
                reasons.append(observed['reason'])
            windows[kind] = dict(start_s=start, stop_s=stop, reasons=reasons, position_support=support)
            if not reasons:
                valid[j, wi] = True
                motion[j, wi] = feats
                counts[j, wi] = [count_window(unit, start, stop) for unit in spikes]
        records.append(dict(**trial, choice_right=choice[1] if choice else None, choice_time_s=ct,
                            choice_reason=observed['reason'], source_epoch=observed['source_epoch'],
                            task_epoch_row=ei, windows=windows, all_windows_valid=bool(valid[j].all())))
    table = audit['electrodes']['values']
    output = dict(asset_id=session['asset_id'], identifier=session['identifier'], rat=session['rat'], day=session['day'],
                  units=len(ids), unit_ids=ids,
                  raw_unit_electrode_values=audit['units']['values']['electrodes'],
                  raw_electrode_table={k:table[k] for k in ('id', 'location', 'group_name')},
                  region_mapping_status='Unresolved in this artifact; raw unit values must not index electrode rows.',
                  sources=sources, trials=records,
                  observation_intervals_column_present='obs_intervals' in audit['units']['schema']['children'],
                  summary=dict(trials=n, choices_resolved=sum(c['choice'] is not None for c in choices),
                               choices_unresolved=sum(c['choice'] is None for c in choices),
                               valid_by_window={k:int(valid[:, i].sum()) for i,k in enumerate(WINDOWS)},
                               all_windows_valid=int(valid.all(axis=1).sum()),
                               reasons_by_window={k:dict(Counter(reason for row in records for reason in row['windows'][k]['reasons'])) for k in WINDOWS}))
    return output, dict(counts=counts, motion=motion, valid=valid)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-index', type=Path, required=True)
    parser.add_argument('--input-sha', required=True)
    args = parser.parse_args()
    result_path = HERE/'odor_place_windows_result.json'
    npz_path = ROOT/'data/local/hippocampal-reinstatement/odor-place-windows-v1/windows.npz'
    if result_path.exists() or npz_path.exists():
        raise FileExistsError('Preserve prior window output')
    for path, digest in PINS.items():
        checked(path, digest)
    index = json.loads(checked(args.input_index, args.input_sha).read_text(encoding='utf-8'))
    cohort = json.loads((HERE/'odor_place_cohort_labels_result.json').read_text(encoding='utf-8'))['sessions']
    corrected = json.loads((HERE/'odor_place_region_reference_result.json').read_text(encoding='utf-8'))['sessions']
    metadata = json.loads((DATA/'dandi001539_0.250815.1203_cohort_metadata_v1/all_assets_summary.json').read_text(encoding='utf-8'))['results']
    selected = {s['asset_id'] for s in corrected if s['eligible_for_cue_outcome_comparison']}
    inputs = {e['asset_id']:e for e in index['sessions']}
    if len(inputs) != len(index['sessions']) or set(inputs) != selected:
        raise ValueError('Expected complete historical32 input coverage, no additional outcome selection')
    audits = {s['asset_id']:s['audit'] for s in metadata}
    sessions, payload = [], {}
    for session in cohort:
        if session['asset_id'] not in selected:
            continue
        row, arrays = build_session(session, audits[session['asset_id']], inputs[session['asset_id']])
        prefix = session['identifier']
        row['npz_keys'] = {k:prefix+'_'+k for k in arrays}
        payload.update({prefix+'_'+k:v for k,v in arrays.items()})
        sessions.append(row)
        print(json.dumps(dict(identifier=prefix, **row['summary'])), flush=True)
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    with npz_path.open('xb') as stream:
        np.savez_compressed(stream, **payload)
    result = dict(schema='hippocampal.odor-place-windows.v1', source_sha256=sha(__file__),
                  test_sha256=sha(ROOT/'tests/test_odor_place_windows.py'),
                  inputs=[dict(path=p.relative_to(ROOT).as_posix(), sha256=h) for p,h in PINS.items()],
                  input_index=dict(path=str(args.input_index), sha256=args.input_sha),
                  cohort_scope='Historical32 selected by the prior region-reference artifact; its biological region interpretation is under correction.',
                  windows=list(WINDOWS), window_duration_s=.5, motion_columns=list(MOTION_COLUMNS),
                  npz=dict(path=npz_path.relative_to(ROOT).as_posix(), bytes=npz_path.stat().st_size, sha256=sha(npz_path)),
                  sessions=sessions,
                  summary=dict(sessions=len(sessions), rats=sorted({s['rat'] for s in sessions}),
                               units=sum(s['units'] for s in sessions), trials=sum(s['summary']['trials'] for s in sessions),
                               choices_resolved=sum(s['summary']['choices_resolved'] for s in sessions),
                               choices_unresolved=sum(s['summary']['choices_unresolved'] for s in sessions),
                               valid_by_window={k:sum(s['summary']['valid_by_window'][k] for s in sessions) for k in WINDOWS},
                               all_windows_valid=sum(s['summary']['all_windows_valid'] for s in sessions)),
                  limitations=['Counts describe deposited spike events, not verified unit-specific continuous observation.',
                               'Raw NWB electrode fields retained verbatim; unit values are not interpreted as electrode row indices.',
                               'Only completed trials with source labels are represented; no early-exit recovery.',
                               'Position motion proxies do not measure head direction, respiration or intention.',
                               'Early and late cue windows may overlap; they are not independent observations.',
                               'Invalid windows contain placeholder zeros in NPZ; valid mask must be applied.',
                               'No fitting, neural-effect selection, retrieval, causal-direction or Riemannian-metric claim.'])
    with result_path.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(result['summary']), flush=True)


if __name__ == '__main__':
    main()
