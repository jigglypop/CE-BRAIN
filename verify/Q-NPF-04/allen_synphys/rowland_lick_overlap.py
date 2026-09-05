"""첫 세션의 기록된 핥기와 기존 반응 창의 겹침을 기술한다."""
import hashlib
import json
import numpy as np
from rowland_first_session import BASE, SessionReader
from rowland_symbolic_reader import Symbol, array
from randi_target_response import HERE, save, sha


def scalar(value):
    if value is None:
        return None
    assert isinstance(value, Symbol)
    assert value.reference in {('numpy.core.multiarray', 'scalar'),
                               ('numpy._core.multiarray', 'scalar')}
    dtype_symbol, payload = value.args
    assert dtype_symbol.reference == ('numpy', 'dtype')
    dtype = np.dtype(dtype_symbol.args[0]).newbyteorder(dtype_symbol.state[1])
    assert dtype.kind in 'fi' and isinstance(payload, bytes) and len(payload) == dtype.itemsize
    result = float(np.frombuffer(payload, dtype=dtype, count=1)[0])
    assert np.isfinite(result)
    return result


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
    sources = ['author_Session.py', 'vape_cacher.py', 'vape_run_functions.py', 'vape_data_import.py']
    save('rowland_lick_overlap_contract.json', {
        'question': '기존 S2 반응 창에 기록된 핥기가 겹치는가',
        'selection': 'J064 run10 전체 보존 시행; 기존 분석 후 정한 기술 점검',
        'source_prefix_sha256': digest.hexdigest(),
        'source_sha256': {name: sha(BASE / name) for name in sources},
        'code_sha256': sha(HERE / 'rowland_lick_overlap.py'),
        'windows_ms': {'early': [0, 1500], 'response': [1500, 3000]},
        'window_rule': 'half-open; 한 시행에서 하나 이상의 기록된 lick',
        'clock': '공개 cacher는 B_to_A(spiral_start)를 빼고 ms로 저장; 실제 export의 실행 revision은 미확인',
        'limits': ['보상 전달 시각 없음', 'lick 없음은 움직임 없음이 아님',
                   '행동으로 층화한 인과효과를 계산하지 않음', '전체 파일 무결성 미확인'],
        'claim_ceiling': 'BIO_EVIDENCE_L1 conditional on documented clock; no causal identification'})
    s = reader.first_session
    assert s['mouse'] == 'J064' and s['run_number'] == 10
    idx = array(s['nonnan_trials'])
    first = s['first_lick'].state
    assert first[1] == (162,) and first[2].args[0] == 'O8'
    assert isinstance(first[4], list) and len(first[4]) == len(idx)
    assert len(s['spiral_lick']) == len(array(s['galvo_ms'])) == 173
    previous = json.loads((HERE / 'rowland_first_session_result.json').read_text(encoding='utf-8'))
    rows = []
    for i, raw_index in enumerate(idx):
        licks = array(s['spiral_lick'][raw_index])
        assert licks.ndim == 1 and np.isfinite(licks).all()
        assert np.all(licks >= 0) and np.all(np.diff(licks) >= 0)
        first_value = scalar(first[4][i])
        assert first_value == (float(licks[0]) if len(licks) else None)
        prior = previous['trials'][i]
        assert prior['original_trial'] == int(raw_index)
        rows.append({**prior, 'first_lick_ms': first_value,
                     'early_lick': bool(np.any((licks >= 0) & (licks < 1500))),
                     'response_window_lick': bool(np.any((licks >= 1500) & (licks < 3000))),
                     'lick_count': len(licks)})
    groups = {}
    for name, code in [('catch', 0), ('test', 1), ('easy', 2)]:
        subset = [r for r in rows if r['photostim'] == code]
        groups[name] = {'n': len(subset), **{key: sum(bool(r[key]) for r in subset)
                       for key in ['early_lick', 'response_window_lick', 'autorewarded']},
                       'no_recorded_lick_in_trial': sum(r['lick_count'] == 0 for r in subset)}
    result = {'contract_sha256': sha(HERE / 'rowland_lick_overlap_contract.json'),
              'first_lick_matches_aligned_spiral_lick': len(rows), 'groups': groups,
              'reward_related_fields': [key for key in s if 'rew' in key],
              'test_trial_reward_delivery_timestamps_available': False,
              'source_revision_historical_execution_verified': False, 'trials': rows}
    save('rowland_lick_overlap_result.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'trials'}))


if __name__ == '__main__':
    main()
