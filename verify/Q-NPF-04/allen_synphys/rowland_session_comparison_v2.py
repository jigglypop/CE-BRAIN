"""완성된 추가 세션에 첫 세션과 같은 명목 창·행동 점검을 적용한다."""
import argparse
import hashlib
import json
import numpy as np
from rowland_sessions import read_sessions
from rowland_first_session import BASE
from rowland_symbolic_reader import array
from rowland_lick_overlap import scalar
from randi_target_response import HERE, save, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mouse')
    parser.add_argument('run', type=int)
    args = parser.parse_args()
    assert args.mouse.isalnum()
    path = BASE / 'sessions_lite_flu_2022-08-11.pkl'
    if not path.exists():
        path = path.with_suffix('.pkl.partial')
    sessions, status = read_sessions(path)
    selected = [(s, m) for s, m in zip(sessions, status['sessions'])
                if s['mouse'] == args.mouse and s['run_number'] == args.run]
    assert len(selected) == 1, 'Requested session not complete'
    s, meta = selected[0]
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        left = meta['object_end']
        while left:
            block = stream.read(min(left, 4 * 1024 * 1024))
            assert block
            digest.update(block)
            left -= len(block)
    stem = f'rowland_{args.mouse}_run{args.run}_clock_filtered'
    save(stem + '_contract.json', {
        'question': '추가 세션에서도 같은 명목 S2 대비와 행동 겹침이 나타나는가',
        'mouse': args.mouse, 'run': args.run,
        'selection': '도착한 추가 세션; 첫 세션 결과를 보고 정한 탐색적 비교',
        'prefix_bytes': meta['object_end'], 'prefix_sha256': digest.hexdigest(),
        'code_sha256': sha(HERE / 'rowland_session_comparison_v2.py'),
        'dependencies_sha256': {n: sha(HERE / n) for n in
                                ['rowland_sessions.py', 'rowland_symbolic_reader.py', 'rowland_lick_overlap.py']},
        'baseline_seconds': [-2, -.5], 'response_seconds': [1.5, 3],
        'frame_shifts': [-1, 0, 1], 'window_rule': 'half-open; 30Hz nominal frame coordinates',
        'endpoint': 'S2 세포별 후 평균-전 평균을 세포 간 평균; test-catch',
        'groups': 'photostim=0 catch, 1 test, 2 easy; easy는 주 대비 제외',
        'clock_exclusion_rule': 'Exclude nonfinite galvo_ms from group endpoints; retain original indices and failed v1 contract',
        'exclusions': '보존 시행 전체; 직접 S2 표적 또는 대응 실패시 중단',
        'limits': ['같은 마우스는 독립 복제 아님', '실제 프레임·보상 시각 미확인',
                   '비무작위 연구; 행동 조건화한 인과효과 아님', '전체 파일 무결성 미확인'],
        'claim_ceiling': 'BIO_EVIDENCE_L1 exploratory within preparation'})
    fields = ['behaviour_trials', 'is_target', 's1_bool', 's2_bool', 'trial_subsets',
              'photostim', 'outcome', 'decision', 'nonnan_trials', 'galvo_ms', 'autorewarded',
              'filter_ps_array', 'filter_ps_time']
    data = {k: array(s[k]) for k in fields}
    y, targets, stim = data['behaviour_trials'], data['is_target'], data['photostim']
    nc, nt, nf = y.shape
    assert y.shape == targets.shape == (s['n_cells'], s['n_trials'], s['n_times'])
    assert s['frequency'] == 30 and nf == 420 and s['pre_frames'] == 240
    assert s['art_gap_start'] == s['art_gap_stop'] == 240
    assert data['s2_bool'].shape == (nc,) and data['s2_bool'].any()
    assert np.array_equal(data['s1_bool'], ~data['s2_bool'])
    assert not targets[data['s2_bool']].any() and np.all(targets == targets[:, :, :1])
    for k in ['trial_subsets', 'photostim', 'outcome', 'decision', 'nonnan_trials', 'autorewarded']:
        assert data[k].shape == (nt,)
    assert np.isin(stim, [0, 1, 2]).all()
    assert np.array_equal(stim == 0, data['trial_subsets'] == 0)
    assert np.array_equal(stim == 2, data['trial_subsets'] == 150)
    assert not targets[:, stim == 0].any()
    assert np.array_equal(data['decision'], np.isin(data['outcome'], ['hit', 'fp']).astype(int))
    idx = data['nonnan_trials']
    assert np.all(np.diff(idx) > 0) and idx.min() >= 0 and idx.max() < len(data['galvo_ms'])
    eligible = np.isfinite(data['galvo_ms'][idx])
    assert eligible.any() and np.all(np.diff(data['galvo_ms'][idx][eligible]) > 0)
    assert len(s['spiral_lick']) == len(data['galvo_ms'])
    first = s['first_lick'].state
    assert first[1] == (nt,) and isinstance(first[4], list) and len(first[4]) == nt
    licks = [array(s['spiral_lick'][i]) for i in idx]
    for i, v in enumerate(licks):
        assert v.ndim == 1 and np.isfinite(v).all() and np.all(v >= 0) and np.all(np.diff(v) >= 0)
        assert scalar(first[4][i]) == (float(v[0]) if len(v) else None)
    time = (np.arange(nf) - s['pre_frames']) / 30
    assert np.array_equal(data['filter_ps_array'], np.arange(nf))
    assert np.allclose(data['filter_ps_time'] - time, 1 / 30, atol=1e-12)
    pre = np.flatnonzero((time >= -2) & (time < -.5))
    post = np.flatnonzero((time >= 1.5) & (time < 3))
    signal = y[data['s2_bool']]
    assert len(pre) == len(post) == 45
    results = []
    for shift in [-1, 0, 1]:
        before, after = signal[:, :, pre + shift], signal[:, :, post + shift]
        assert np.isfinite(before).all() and np.isfinite(after).all()
        delta = (after.mean(axis=2) - before.mean(axis=2)).mean(axis=0)
        overlap = np.array([np.any((v >= 1500 + shift * 1000 / 30) &
                                   (v < 3000 + shift * 1000 / 30)) for v in licks])
        groups = {}
        for name, code in [('catch', 0), ('test', 1), ('easy', 2)]:
            mask = (stim == code) & eligible
            assert mask.any()
            groups[name] = {'n': int(mask.sum()), 'mean_s2_delta': float(delta[mask].mean()),
                            'lick_overlap': int(overlap[mask].sum()),
                            'autorewarded': int(data['autorewarded'][mask].sum())}
        results.append({'shift_frames': shift, 'groups': groups,
                        'test_minus_catch': groups['test']['mean_s2_delta'] - groups['catch']['mean_s2_delta'],
                        's2_delta_by_trial': delta.tolist(), 'lick_overlap_by_trial': overlap.tolist()})
    result = {'contract_sha256': sha(HERE / (stem + '_contract.json')),
              'mouse': args.mouse, 'run': args.run, 's1_cells': int(data['s1_bool'].sum()),
              's2_cells': int(data['s2_bool'].sum()), 'trials': nt,
              'analysis_eligible': eligible.tolist(), 'excluded_original_indices': idx[~eligible].tolist(),
              'analysis_trials': int(eligible.sum()), 'original_trials': len(data['galvo_ms']), 'original_indices': idx.tolist(),
              'photostim': stim.tolist(), 'outcome': data['outcome'].tolist(),
              'offsets': results, 'complete_file_verified': False}
    save(stem + '_result.json', result)
    print(json.dumps({**{k: result[k] for k in ['mouse', 'run', 's1_cells', 's2_cells', 'trials', 'original_trials', 'analysis_trials', 'excluded_original_indices']},
                      'offsets': [{k: v for k, v in r.items() if not k.endswith('_by_trial')} for r in results]}))
    for v in data.values():
        if isinstance(v, np.memmap):
            v._mmap.close()


if __name__ == '__main__':
    main()
