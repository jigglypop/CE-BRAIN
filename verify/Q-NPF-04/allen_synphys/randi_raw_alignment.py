"""서버 검증된 추출 신호와 기존 export의 좌표 대응을 확인한다."""
import json
from pathlib import Path

import numpy as np

from randi_target_response import BASE, HERE, save, sha


def main():
    acquisition = json.loads((HERE / 'randi_raw_acquisition_result.json').read_text(encoding='utf-8'))
    rows = []
    for sid in ('6', '9'):
        old, new = BASE / 'exported_data', BASE / 'raw_extracted'
        matches = {}
        for key in ('t', 'stim_volume_i', 'stim_neurons', 'labels', 'ds_name'):
            a, b = old / f'{sid}_{key}.txt', new / f'{sid}_{key}.txt'
            matches[key] = a.read_bytes() == b.read_bytes()
        a, b = np.loadtxt(old / f'{sid}_gcamp.txt'), np.loadtxt(new / f'{sid}_gcamp.txt')
        row = {'session': sid, 'metadata_byte_matches': matches,
               'old_shape': list(a.shape), 'new_shape': list(b.shape),
               'old_nonfinite': int((~np.isfinite(a)).sum()), 'new_nonfinite': int((~np.isfinite(b)).sum()),
               'old_sha256': sha(old / f'{sid}_gcamp.txt'), 'new_sha256': sha(new / f'{sid}_gcamp.txt')}
        row['alignment_pass'] = all(matches.values()) and a.shape == b.shape
        if a.shape == b.shape:
            both = np.isfinite(a) & np.isfinite(b)
            row['shared_finite_values'] = int(both.sum())
            row['mean_absolute_difference_shared_finite'] = float(np.mean(np.abs(a[both] - b[both])))
            row['old_finite_new_missing'] = int((np.isfinite(a) & ~np.isfinite(b)).sum())
        rows.append(row)
    save('randi_raw_alignment_result.json', {'acquisition_sha256': sha(HERE / 'randi_raw_acquisition_result.json'),
                                           'code_sha256': sha(Path(__file__)), 'sessions': rows,
                                           'claim_ceiling': 'L0; equal metadata does not independently prove cell identity or raw extraction causality'})
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
