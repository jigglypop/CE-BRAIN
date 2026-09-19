"""Preserve Norman recall/ripple observations on their shared block clock.

This constructs observation tables, not ripple-to-memory assignments or an
online neural history. The author's ripple detection uses future samples.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import scipy
from scipy.io import loadmat
from scipy.io.matlab import varmats_from_mat

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / 'data/external/hippocampal_reinstatement/norman2019_recall_ripples_v1'
BEHAVIOR = ROOT / 'data/local/hippocampal-reinstatement/norman-behavior-support-v3/norman_behavior_ripple_join.json'
ACQUISITION_SHA = '0e724b7de640775269f8787edc0d15c9dd8eef74a0a66bdb3bae6fb43eb8fce5'
BEHAVIOR_SHA = 'a02e3b122d5cc6380a7bedc45e0e1958d204781dd7bcd0b88f65e0ca6e11188a'
COLUMNS = ['str', 'peak', 'fin', 'amplitude']


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked(path: Path, expected: str, size: int | None = None) -> dict:
    actual = digest(path)
    if actual != expected or (size is not None and path.stat().st_size != size):
        raise ValueError(f'Input pin mismatch: {path}')
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size, sha256=actual)


def read_ripples(path: Path, category: str) -> tuple[np.ndarray, np.ndarray]:
    data = loadmat(path, squeeze_me=False, struct_as_record=False)
    workspace = np.asarray(data['__function_workspace__'], dtype=np.uint8).tobytes()
    with path.open('rb') as stream:
        header = stream.read(128)
    pieces = varmats_from_mat(io.BytesIO(header + workspace[8:]))
    embedded = loadmat(pieces[0][1], squeeze_me=False, struct_as_record=False)['__function_workspace__']
    wrapper = embedded[0, 0].MCOS.flat[0]
    if wrapper['s2'] != b'FileWrapper__':
        raise ValueError('Unsupported MCOS layout')
    arr = wrapper['arr']
    rows = int(np.asarray(arr[4, 0]).ravel()[0])
    variables = int(np.asarray(arr[6, 0]).ravel()[0])
    names = [str(np.asarray(x).ravel()[0]) for x in np.asarray(arr[7, 0], dtype=object).ravel()]
    columns = np.asarray(arr[2, 0], dtype=object).ravel()
    if names != COLUMNS or variables != 4 or len(columns) != 4:
        raise ValueError('Unexpected ripple table columns')
    vectors = [np.asarray(x, dtype=np.float64).ravel() for x in columns]
    if any(len(v) != rows for v in vectors):
        raise ValueError('Ripple column lengths differ')
    matrix = np.column_stack(vectors)
    clock = np.asarray(data[f't_{category}'], dtype=np.float64).ravel()
    if not np.isfinite(matrix).all() or not np.isfinite(clock).all() or len(clock) < 2:
        raise ValueError('Nonfinite or absent observations')
    if not np.all(np.diff(clock) > 0) or not np.all(np.diff(matrix[:, 1]) > 0):
        raise ValueError('Non-increasing clock or duplicate/unordered ripple peak')
    if not np.all((matrix[:, 0] <= matrix[:, 1]) & (matrix[:, 1] <= matrix[:, 2]) & (matrix[:, 2] > matrix[:, 0])):
        raise ValueError('Invalid ripple interval')
    if not np.all((clock[0] <= matrix[:, 1]) & (matrix[:, 1] <= clock[-1])):
        raise ValueError('Ripple peak outside stored clock')
    return matrix, clock


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError('Preserve existing output directory')
    inputs = [checked(RAW / 'acquisition_summary.json', ACQUISITION_SHA), checked(BEHAVIOR, BEHAVIOR_SHA)]
    acquisition = json.loads((RAW / 'acquisition_summary.json').read_text(encoding='utf-8'))
    behavior = json.loads(BEHAVIOR.read_text(encoding='utf-8'))
    if acquisition['phase'] != 'complete' or len(acquisition['members']) != 64:
        raise ValueError('Acquisition is incomplete')
    by_block = defaultdict(list)
    for row_index, row in enumerate(behavior['behavior']['events_rows']):
        key = (row['subject'], row['source_category'], int(row['run']))
        onset, offset = float(row['onset_s']), float(row['offset_s'])
        if not np.isfinite([onset, offset]).all() or offset < onset:
            raise ValueError('Invalid behavior interval')
        by_block[key].append(dict(
            behavior_source_row_zero_based=row_index,
            onset_s=onset, offset_s=offset, item_label=row['label'], prompt=bool(row['prompt']),
            onset_in_behavior_domain=bool(0 <= onset <= 150), offset_in_behavior_domain=bool(0 <= offset <= 150),
            exact_current_run_item=bool(row['matched_stimulus']),
            current_run_unmatched=bool(row['current_run_unmatched']),
            cross_category=bool(row['cross_category']),
            prompt_table_label_mismatch=bool(row['prompt_table_label_mismatch'])))
    blocks, seen = [], set()
    for member in acquisition['members']:
        path = RAW / 'selected_members' / member['name']
        inputs.append(checked(path, member['sha256'], member['bytes']))
        match = re.fullmatch(r'(SUB(?:\d{2}|13b)) (faces|places) RUN ([12]) ripples\.mat', path.name)
        if not match:
            raise ValueError(f'Unexpected member name: {path.name}')
        record, category, run_string = match.groups()
        run = int(run_string)
        source_category = {'faces': 'Face', 'places': 'Place'}[category]
        key = (record, source_category, run)
        if key in seen:
            raise ValueError('Duplicate observation block')
        seen.add(key)
        matrix, clock = read_ripples(path, category)
        block_id = f'{record}/{source_category}/run{run}'
        ripples = [dict(ripple_source_row_zero_based=i, str_s=float(a), peak_s=float(b), fin_s=float(c),
                        amplitude_db_relative_median=float(d), peak_in_behavior_domain=bool(0 <= b <= 150))
                   for i, (a, b, c, d) in enumerate(matrix)]
        verbal = sorted(by_block.get(key, []), key=lambda row: (row['onset_s'], row['offset_s'], row['behavior_source_row_zero_based']))
        blocks.append(dict(block_id=block_id, record_label=record, person='SUB13' if record == 'SUB13b' else record,
                           category=source_category, run=run, ripple_input=path.relative_to(ROOT).as_posix(),
                           nominal_behavior_domain_s=[0.0, 150.0],
                           stored_ripple_clock=dict(start_s=float(clock[0]), end_s=float(clock[-1]), samples=len(clock),
                                                    minimum_step_s=float(np.min(np.diff(clock))), maximum_step_s=float(np.max(np.diff(clock)))),
                           ripples=ripples, verbal_events=verbal))
    if set(by_block) - seen:
        raise ValueError('Behavior rows without a corresponding ripple block')
    blocks.sort(key=lambda block: block['block_id'])
    counts = Counter(blocks=len(blocks), records=len({b['record_label'] for b in blocks}), persons=len({b['person'] for b in blocks}))
    for block in blocks:
        counts['ripples'] += len(block['ripples'])
        counts['ripples_in_behavior_domain'] += sum(r['peak_in_behavior_domain'] for r in block['ripples'])
        counts['verbal_events'] += len(block['verbal_events'])
        counts['prompts'] += sum(v['prompt'] for v in block['verbal_events'])
        counts['nonprompt_events'] += sum(not v['prompt'] for v in block['verbal_events'])
    expected = dict(blocks=64, records=16, persons=15, ripples=3577, ripples_in_behavior_domain=3345,
                    verbal_events=470, prompts=79, nonprompt_events=391)
    if dict(counts) != expected:
        raise ValueError(f'Observation support changed: {dict(counts)}')
    report = dict(schema='ce.norman.event-observations.v1', source_sha256=digest(Path(__file__)),
                  environment=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
                  inputs=inputs, summary=dict(counts), blocks=blocks,
                  interpretation=dict(clock='Seconds relative to each record/category/run recall block; separate blocks are not one continuous clock.',
                                      ripple_preprocessing='Retrospective offline detector; not guaranteed available at its stamped peak time.',
                                      behavioral_domain='Nominal author task interval; retained events outside it are flagged, not clipped or removed.',
                                      coverage='Stored numeric clock bounds do not prove continuous artifact-free raw acquisition.',
                                      event_identity='Source row indexes preserve provenance only; no ripple-to-verbal or ripple-to-cortical item assignment.',
                                      missing_input='Per-event cortical activity and its acquisition/preprocessing correspondence remain absent.',
                                      model='No fit, effect estimate, or online prediction; retrospective recall/search masks are not predictor features.'))
    args.output_dir.mkdir(parents=True, exist_ok=False)
    result = args.output_dir / 'norman_event_observations.json'
    with result.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    manifest = dict(source=dict(path=str(Path(__file__).resolve()), bytes=Path(__file__).stat().st_size, sha256=digest(Path(__file__))),
                    result=dict(path=result.name, bytes=result.stat().st_size, sha256=digest(result)))
    with (args.output_dir / 'manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, indent=2)
    print(json.dumps(dict(output=str(result), bytes=result.stat().st_size, sha256=digest(result), summary=dict(counts))))


if __name__ == '__main__':
    main()
