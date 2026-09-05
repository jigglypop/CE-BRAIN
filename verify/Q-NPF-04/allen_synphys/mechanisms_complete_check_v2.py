"""수집 완료 후 세 조건의 파일 무결성과 전처리를 한 번에 검증한다."""
import json
from pathlib import Path
import numpy as np
from mechanisms_symbolic_reader_v3 import MechanismsReaderV3
from mechanisms_normalization_check import compare
from rowland_sessions import ExactReads
from rowland_symbolic_reader import array
from randi_target_response import HERE, save, sha


def check_trials(data, trials, starts, pre, post, duration):
    assert trials.shape == (len(data), pre + post, len(starts))
    bad = 0
    maximum = 0.0
    for i, start in enumerate(starts):
        assert start - pre >= 0 and start + post <= data.shape[1]
        trace = data[:, start-pre:start+post]
        expected = trace - trace[:, :pre].mean(axis=1, keepdims=True)
        expected[:, pre:pre+duration] = 0
        actual = trials[:, :, i]
        assert np.isfinite(actual).all() and np.isfinite(expected).all()
        bad += int(np.sum(~np.isclose(actual, expected, rtol=1e-6, atol=1e-6)))
        maximum = max(maximum, float(np.max(np.abs(actual-expected))))
    return {'mismatched_elements': bad, 'max_absolute_difference': maximum, 'passed': bad == 0}


def self_test():
    data = np.arange(40, dtype=np.float32).reshape(2, 20)
    starts = np.array([5, 12])
    trials = np.stack([data[:, s-2:s+4]-data[:, s-2:s].mean(axis=1, keepdims=True) for s in starts], axis=2)
    trials[:, 2:3, :] = 0
    assert check_trials(data, trials, starts, 2, 4, 1)['passed']
    trials[1, 5, 1] += 1
    assert check_trials(data, trials, starts, 2, 4, 1)['mismatched_elements'] == 1


def main():
    self_test()
    base = Path('data/external/cortical_propagation_2023')
    path = base/'2021-02-18_RL127.pkl'
    receipt_path = base/'mechanisms_RL127_download_receipt.json'
    if not path.exists() or not receipt_path.exists():
        print('PENDING: complete payload and receipt required; synthetic checks PASS')
        return
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    assert path.stat().st_size == receipt['bytes'] == 1861537717
    digest = sha(path)
    assert digest == receipt['sha256']
    with path.open('rb') as stream:
        reader = MechanismsReaderV3(ExactReads(stream, path.stat().st_size), path)
        root = reader.load()
        end = stream.tell()
        assert end == path.stat().st_size and not stream.read(1)
        assert root.state['sheet_name'] == '2021-02-18_RL127'
        blocks = {}
        reference_ids = None
        for name in ('photostim_r', 'photostim_s', 'spont'):
            v = root.state[name].state
            raw = array(v['raw'][0]); data = array(v['dfof'][0])
            trials = array(v['all_trials'][0]); starts = array(v['stim_start_frames'][0])
            ids = np.asarray(v['cell_id'][0], dtype=np.int64)
            assert ids.shape == (2334,) and len(np.unique(ids)) == len(ids)
            if reference_ids is None: reference_ids = ids
            assert np.array_equal(ids, reference_ids)
            assert raw.shape == data.shape == (2334, 22986) and len(starts) == 100
            clock = array(v['frame_clock']); stim = array(v['stim_times'])
            assert np.all(np.diff(clock) > 0) and len(stim) == len(starts)
            assert np.array_equal(np.searchsorted(clock, stim, side='right')-1, starts)
            normalization = compare(raw, data)
            reconstruction = check_trials(data, trials, starts, v['pre_frames'], v['post_frames'], v['duration_frames'])
            assert normalization['passed'] and reconstruction['passed']
            blocks[name] = {'normalization': normalization, 'trials': reconstruction,
                            'trial_shape': list(trials.shape), 'clock_n': len(clock),
                            'cell_ids_equal': True, 'preceding_frame_match': True}
    result = {'code_sha256': sha(Path(__file__)), 'payload_sha256': digest,
              'download_receipt_sha256': sha(receipt_path), 'object_end': end,
              'blocks': blocks, 'passed': True,
              'limits': ['Local checksum matches download receipt; no independent server checksum',
                         'Preprocessing validation does not establish biological causality or sham provenance']}
    save('mechanisms_RL127_complete_check_v2.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
