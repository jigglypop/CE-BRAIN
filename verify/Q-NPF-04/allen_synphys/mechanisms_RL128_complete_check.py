"""RL128의 실제 배열 크기로 수집·전처리·조건 간 대응을 검사한다."""
import json
from pathlib import Path
import numpy as np
from mechanisms_complete_check_v2 import check_trials, self_test
from mechanisms_normalization_check import compare
from mechanisms_symbolic_reader_v3 import MechanismsReaderV3
from rowland_sessions import ExactReads
from rowland_symbolic_reader import Symbol, array
from randi_target_response import HERE, save, sha


def vector(value):
    return array(value) if isinstance(value, Symbol) else np.asarray(value)


def main():
    self_test()
    contract_path = HERE/'mechanisms_RL128_replication_contract.json'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    base = Path('data/external/cortical_propagation_2023')
    path = base/contract['dataset']
    receipt_path = base/'mechanisms_RL128_download_receipt.json'
    if not path.exists() or not receipt_path.exists():
        print('PENDING: complete payload and receipt required; synthetic checks PASS')
        return
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    assert path.stat().st_size == receipt['bytes'] == contract['expected_bytes']
    assert receipt['revision'] == contract['revision']
    digest = sha(path); assert digest == receipt['sha256']
    with path.open('rb') as stream:
        root = MechanismsReaderV3(ExactReads(stream,path.stat().st_size),path).load()
        end = stream.tell(); assert end == path.stat().st_size and not stream.read(1)
        assert root.state['sheet_name'] == path.stem
        blocks = {}; reference = None
        for name in ('photostim_r','photostim_s','spont'):
            v = root.state[name].state
            assert all(len(v[key]) == 1 for key in ('raw','dfof','all_trials','cell_id','cell_s1','cell_s2'))
            raw = array(v['raw'][0]); data = array(v['dfof'][0]); trials = array(v['all_trials'][0])
            ids = vector(v['cell_id'][0]); s1 = vector(v['cell_s1'][0]); s2 = vector(v['cell_s2'][0])
            assert ids.ndim == 1 and len(ids) > 0 and len(np.unique(ids)) == len(ids)
            assert s1.shape == s2.shape == ids.shape
            assert np.isin(s1,[0,1]).all() and np.isin(s2,[0,1]).all()
            assert not np.any(s1.astype(bool)&s2.astype(bool))
            current = (ids,s1,s2)
            if reference is None: reference = current
            assert all(np.array_equal(a,b) for a,b in zip(reference,current))
            assert raw.ndim == 2 and raw.shape == data.shape and raw.shape[0] == len(ids)
            starts = array(v['stim_start_frames'][0]); clock = array(v['frame_clock']); stim = array(v['stim_times'])
            assert len(starts) == len(stim) == 100 and np.all(np.diff(clock)>0)
            assert np.array_equal(np.searchsorted(clock,stim,side='right')-1,starts)
            fps = v['fps']; pre = v['pre_frames']; post = v['post_frames']; duration = v['duration_frames']
            assert np.isfinite(fps) and fps > 0 and pre > 0 and post > 0
            assert duration == int(np.ceil(v['stim_dur']/1000*fps)+1)
            normalization = compare(raw,data)
            reconstruction = check_trials(data,trials,starts,pre,post,duration)
            assert normalization['passed'] and reconstruction['passed']
            targets = vector(v['targeted_cells']).astype(bool)
            assert targets.shape == ids.shape and not np.any(targets&s2.astype(bool))
            blocks[name] = {'raw_shape':list(raw.shape),'trial_shape':list(trials.shape),
                            'fps':fps,'pre_frames':pre,'post_frames':post,'duration_frames':duration,
                            's1_n':int(s1.sum()),'s2_n':int(s2.sum()),'target_n':int(targets.sum()),
                            'clock_n':len(clock),'normalization':normalization,'trials':reconstruction,
                            'cell_identity_and_regions_match':True,'preceding_frame_match':True}
    result = {'code_sha256':sha(Path(__file__)),'contract_sha256':sha(contract_path),
              'payload_sha256':digest,'receipt_sha256':sha(receipt_path),'object_end':end,
              'blocks':blocks,'passed':True,
              'helper_sha256':{name:sha(HERE/name) for name in ('mechanisms_complete_check_v2.py','mechanisms_normalization_check.py','mechanisms_symbolic_reader_v3.py')},
              'limits':['Local file validation only; biological contrasts and independent sham provenance not established']}
    save('mechanisms_RL128_complete_check.json',result)
    print(json.dumps(result))


if __name__ == '__main__': main()
