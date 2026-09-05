"""기존 선충 자료의 자극 ID·시각 대응을 조사한다. 생물 endpoint는 계산하지 않는다."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'data/external/randi_2023_osf_e2syt'
OUT = Path(__file__).with_name('randi_intervention_inventory_result.json')


def main():
    rows = []
    for cohort in ('exported_data', 'exported_data_unc31'):
        folder = BASE / cohort
        for timefile in sorted(folder.glob('*_t.txt'), key=lambda p: int(p.name.split('_')[0])):
            sid = timefile.name.split('_')[0]
            paths = {key: folder / f'{sid}_{key}.txt' for key in
                     ('t', 'stim_volume_i', 'stim_neurons', 'labels', 'ds_name', 'gcamp')}
            assert all(p.is_file() for p in paths.values()), paths
            t = np.atleast_1d(np.loadtxt(paths['t']))
            events_raw = np.atleast_1d(np.loadtxt(paths['stim_volume_i']))
            targets_raw = np.atleast_1d(np.loadtxt(paths['stim_neurons']))
            assert np.all(events_raw == np.floor(events_raw))
            assert np.all(targets_raw == np.floor(targets_raw))
            events, targets = events_raw.astype(int), targets_raw.astype(int)
            labels = paths['labels'].read_text(encoding='utf-8').splitlines()
            with paths['gcamp'].open(encoding='utf-8') as stream:
                ncols = len(stream.readline().split())
            assert len(events) == len(targets)
            assert np.isfinite(t).all() and np.all(np.diff(t) > 0)
            assert np.all((events >= 0) & (events < len(t)))
            known = (targets >= 0) & (targets < ncols)
            named = [i for i in targets[known] if i < len(labels) and labels[i].strip()]
            unique, counts = np.unique(targets[known], return_counts=True)
            rows.append({
                'cohort': cohort, 'session': sid,
                'source_session': paths['ds_name'].read_text(encoding='utf-8').strip(),
                'time_samples': len(t), 'signal_columns_first_row': ncols,
                'label_rows': len(labels), 'label_count_matches_signal_columns': len(labels) == ncols,
                'event_order_nonincreasing_count': int((np.diff(events) <= 0).sum()),
                'median_time_step_file_units': float(np.median(np.diff(t))),
                'events': len(events), 'local_target_in_range': int(known.sum()),
                'unknown_target_minus_one': int((targets == -1).sum()),
                'other_invalid_target': int(((~known) & (targets != -1)).sum()),
                'events_with_nonempty_atlas_label': len(named),
                'unique_local_targets': len(unique),
                'local_targets_repeated_at_least_3': int((counts >= 3).sum()),
                'metadata_sha256': {key: hashlib.sha256(path.read_bytes()).hexdigest()
                                    for key, path in paths.items() if key != 'gcamp'},
                'signal_file': paths['gcamp'].relative_to(ROOT).as_posix(),
                'signal_bytes': paths['gcamp'].stat().st_size,
            })
    result = {
        'question': '기존 자료에서 자극 대상과 기록 시각을 연결할 수 있는가',
        'claim_ceiling': 'BIO_EVIDENCE_L0',
        'status': 'LOCAL_INDEX_CANDIDATES_IDENTIFIED_NOT_SOURCE_VALIDATED',
        'limitations': ['0 기반 인덱스 해석은 아직 저자 export 코드로 검증하지 않음',
                       '신호 전체 행 수·결측·자극 충실도·sham은 미검사',
                       '비어 있지 않은 atlas 표지는 정확한 세포 동일성의 증명이 아님',
                       '세션 수를 독립 동물 수로 세지 않음',
                       '기존 UNC31 실패 판정과 분할을 변경하지 않음'],
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'sessions': rows,
        'summary': {cohort: {key: sum(row[key] for row in rows if row['cohort'] == cohort)
                            for key in ('events', 'local_target_in_range',
                                        'unknown_target_minus_one', 'other_invalid_target',
                                        'events_with_nonempty_atlas_label',
                                        'local_targets_repeated_at_least_3')}
                    for cohort in ('exported_data', 'exported_data_unc31')},
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if OUT.exists():
        assert OUT.read_text(encoding='utf-8') == payload
    else:
        with OUT.open('x', encoding='utf-8') as stream:
            stream.write(payload)
    print(json.dumps({'sessions': len(rows), 'summary': result['summary']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
