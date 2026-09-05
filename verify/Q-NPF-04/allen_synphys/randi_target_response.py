"""기존 두 첫 세션의 표적별 반응 대비. 사후 탐색이며 sham 인과검정이 아니다."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
BASE = ROOT / 'data/external/randi_2023_osf_e2syt'
REV = '1dbc5e0a2b609d54bc9b1c90c73d4e3bf183d3c7'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, obj):
    payload = json.dumps(obj, ensure_ascii=False, allow_nan=False, indent=2) + '\n'
    p = HERE / name
    if p.exists():
        assert p.read_text(encoding='utf-8') == payload
    else:
        with p.open('x', encoding='utf-8') as f:
            f.write(payload)
    return p


def main():
    source_files = {}
    for src in ('pumpprobe/Funatlas.py', 'pumpprobe/Fconn.py',
                'scripts/fconnectivity/figures/paper/reminder_exporting_data.txt'):
        raw = subprocess.check_output(['git', '-C', str(BASE / 'pumpprobe'), 'show', f'{REV}:{src}'])
        dest = BASE / ('source_' + src.replace('/', '_'))
        if dest.exists():
            assert dest.read_bytes() == raw
        else:
            with dest.open('xb') as f:
                f.write(raw)
        source_files[src] = {'path': str(dest.relative_to(ROOT)), 'sha256': sha(dest)}
    files = [BASE / cohort / f'0_{key}.txt'
             for cohort in ('exported_data', 'exported_data_unc31')
             for key in ('gcamp', 't', 'stim_volume_i', 'stim_neurons', 'labels', 'ds_name')]
    contract = {'question': '동일 세포의 직접 표적 시행과 다른 표적 시행 반응의 탐색적 대비',
                'selection': '두 cohort의 session 0; 실패 시 다른 세션으로 교체하지 않음',
                'source_revision': REV, 'source_files': source_files,
                'inputs': {str(p.relative_to(ROOT)): sha(p) for p in files},
                'code_sha256': sha(Path(__file__)),
                'pre_seconds': [-10, -2], 'post_seconds': [2, 10],
                'windows': 'half-open; 전체 창 확보; 다른 자극이 [-10,10)에 있으면 제외',
                'quality': '모든 창 표본 유한, 자극 전 평균 양수; 음수 대상 제외; 첫 -2 이후 제외',
                'measurement': '(자극 후 평균 - 전 평균) / 전 평균; 원 export signal 사용',
                'comparison': '세포별 직접 표적 평균 dF/F - 다른 표적 평균 dF/F; 양쪽 1회 이상',
                'split': '기존 검토 자료의 탐색; 독립 holdout 아님',
                'claim_ceiling': 'BIO_EVIDENCE_L1; 직접 연결·sham 효과·유전자형 인과효과 아님',
                'interpreter': sys.executable, 'numpy': np.__version__}
    save('randi_target_response_contract.json', contract)
    results = []
    for cohort in ('exported_data', 'exported_data_unc31'):
        folder = BASE / cohort
        y = np.loadtxt(folder / '0_gcamp.txt')
        t = np.loadtxt(folder / '0_t.txt')
        ev = np.loadtxt(folder / '0_stim_volume_i.txt', dtype=int)
        targets = np.loadtxt(folder / '0_stim_neurons.txt', dtype=int)
        labels = (folder / '0_labels.txt').read_text(encoding='utf-8').splitlines()
        assert y.shape == (len(t), len(labels))
        assert np.all(np.diff(t) > 0) and np.all(np.diff(ev) > 0)
        assert len(ev) == len(targets) and np.all((ev >= 0) & (ev < len(t)))
        ts = t[ev]
        bubble = np.flatnonzero(targets == -2)
        end = int(bubble[0]) if len(bubble) else len(ev)
        changes, used_targets, trial_records = [], [], []
        for k, (time, target) in enumerate(zip(ts, targets)):
            if k >= end or not 0 <= target < y.shape[1]:
                continue
            if time - 10 < t[0] or time + 10 > t[-1]:
                continue
            if np.any((np.arange(len(ts)) != k) & (ts >= time - 10) & (ts < time + 10)):
                continue
            pre = y[(t >= time - 10) & (t < time - 2)]
            post = y[(t >= time + 2) & (t < time + 10)]
            assert len(pre) and len(post)
            baseline = pre.mean(axis=0)
            valid = np.isfinite(pre).all(axis=0) & np.isfinite(post).all(axis=0) & (baseline > 0)
            change = np.full(y.shape[1], np.nan)
            change[valid] = (post.mean(axis=0)[valid] - baseline[valid]) / baseline[valid]
            changes.append(change)
            used_targets.append(target)
            trial_records.append({'event': k, 'target': int(target), 'valid_cells': int(valid.sum())})
        assert changes, cohort
        changes, used_targets = np.array(changes), np.array(used_targets)
        cells = []
        for cell in np.unique(used_targets):
            finite = np.isfinite(changes[:, cell])
            direct = changes[finite & (used_targets == cell), cell]
            other = changes[finite & (used_targets != cell), cell]
            if len(direct) and len(other):
                cells.append({'local_cell': int(cell), 'atlas_label_unvalidated': labels[cell],
                              'direct_n': len(direct), 'other_n': len(other),
                              'direct_mean': float(direct.mean()), 'other_mean': float(other.mean()),
                              'contrast': float(direct.mean() - other.mean())})
        assert cells, cohort
        results.append({'cohort': cohort, 'session': 0, 'events_retained': len(changes),
                        'cells_comparable': len(cells), 'positive_contrasts': sum(c['contrast'] > 0 for c in cells),
                        'median_contrast': float(np.median([c['contrast'] for c in cells])),
                        'trials': trial_records, 'cells': cells})
    save('randi_target_response_result.json', {'contract_sha256': sha(HERE / 'randi_target_response_contract.json'),
                                            'results': results})
    print(json.dumps([{k: v for k, v in r.items() if k not in ('trials', 'cells')} for r in results]))


if __name__ == '__main__':
    main()
