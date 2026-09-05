"""첫 세션의 명목 프레임 시간축을 한 프레임 이동해 기존 결론을 점검한다."""
import hashlib
import json
import numpy as np
from rowland_first_session import BASE, SessionReader
from rowland_symbolic_reader import array
from randi_target_response import HERE, save, sha


def main():
    path = BASE / 'sessions_lite_flu_2022-08-11.pkl'
    if not path.exists():
        path = path.with_suffix('.pkl.partial')
    with path.open('rb') as stream:
        reader = SessionReader(stream, path)
        try:
            reader.load()
        except EOFError:
            pass
    old = json.loads((HERE / 'rowland_first_session_contract.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        left = reader.first_session_end
        while left:
            block = stream.read(min(left, 4 * 1024 * 1024))
            assert block
            digest.update(block)
            left -= len(block)
    assert reader.first_session_end == old['source_prefix_bytes']
    assert digest.hexdigest() == old['source_prefix_sha256']
    save('rowland_frame_sensitivity_contract.json', {
        'question': '한 프레임 시간 정의 차이가 첫 S2 대비와 핥기 겹침을 바꾸는가',
        'selection': 'J064 run10; 기존 결과를 본 뒤 정한 민감도 점검',
        'prefix_sha256': digest.hexdigest(),
        'source_sha256': sha(BASE / 'author_Session.py'),
        'code_sha256': sha(HERE / 'rowland_frame_sensitivity.py'),
        'frame_offsets': [-1, 0, 1],
        'endpoint': '기존 45프레임 전후 창을 각각 동일하게 -1, 0, +1프레임 이동',
        'lick_endpoint': '명목 [1500,3000)ms 창을 -1/30,0,+1/30초 이동',
        'source_finding': 'get_trial_frames_single은 closest_frame_before를 index pre_frames에 둠',
        'limits': ['실제 시행별 frame clock 없음', '고정 offset은 실제 시각 오차의 엄밀한 상하한 아님',
                   '광학·행동·보상 인과 분리 아님', '첫 세션만 도착; 전체 무결성 미검증'],
        'claim_ceiling': 'BIO_EVIDENCE_L1 descriptive sensitivity'})
    s = reader.first_session
    assert s['mouse'] == 'J064' and s['run_number'] == 10 and s['frequency'] == 30
    y = array(s['behaviour_trials'])
    signal = y[array(s['s2_bool'])]
    stim = array(s['photostim'])
    idx = array(s['nonnan_trials'])
    time = (np.arange(y.shape[2]) - s['pre_frames']) / s['frequency']
    pre = np.flatnonzero((time >= -2) & (time < -.5))
    post = np.flatnonzero((time >= 1.5) & (time < 3))
    previous = json.loads((HERE / 'rowland_first_session_result.json').read_text(encoding='utf-8'))
    previous_lick = json.loads((HERE / 'rowland_lick_overlap_result.json').read_text(encoding='utf-8'))
    offsets = []
    for shift in [-1, 0, 1]:
        assert len(pre) == len(post) == 45
        assert (pre + shift).min() >= 0 and (post + shift).max() < y.shape[2]
        delta = (signal[:, :, post + shift].mean(axis=2) - signal[:, :, pre + shift].mean(axis=2)).mean(axis=0)
        assert np.isfinite(delta).all()
        lick_window = (np.array([1500., 3000.]) + shift * 1000 / s['frequency']).tolist()
        overlap = []
        for raw_index in idx:
            licks = array(s['spiral_lick'][raw_index])
            overlap.append(bool(np.any((licks >= lick_window[0]) & (licks < lick_window[1]))))
        overlap = np.asarray(overlap)
        groups = {name: {'n': int((stim == code).sum()),
                         'mean_s2_delta': float(delta[stim == code].mean()),
                         'lick_overlap': int(overlap[stim == code].sum())}
                  for name, code in [('catch', 0), ('test', 1), ('easy', 2)]}
        contrast = groups['test']['mean_s2_delta'] - groups['catch']['mean_s2_delta']
        if shift == 0:
            assert np.allclose(delta, [r['s2_delta'] for r in previous['trials']], atol=1e-12, rtol=0)
            for name in groups:
                assert groups[name]['lick_overlap'] == previous_lick['groups'][name]['response_window_lick']
        offsets.append({'shift_frames': shift, 'pre_indices': (pre + shift).tolist(),
                        'post_indices': (post + shift).tolist(), 'lick_window_ms': lick_window,
                        'groups': groups, 'test_minus_catch': contrast,
                        's2_delta_by_trial': delta.tolist()})
    result = {'contract_sha256': sha(HERE / 'rowland_frame_sensitivity_contract.json'),
              'offsets': offsets, 'nominal_result_reproduced': True,
              'actual_per_trial_frame_clock_available': 'paqio_frames' in s,
              'complete_file_verified': False}
    save('rowland_frame_sensitivity_result.json', result)
    print(json.dumps([{k: v for k, v in r.items() if k not in
                      ['s2_delta_by_trial', 'pre_indices', 'post_indices']} for r in offsets]))
    if isinstance(y, np.memmap):
        y._mmap.close()


if __name__ == '__main__':
    main()
