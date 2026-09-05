"""첫 블록의 완성된 시각 배열에서 이벤트와 프레임의 대응을 확인한다."""
from pathlib import Path
import numpy as np
from mechanisms_symbolic_reader_v2 import MechanismsReaderV2
from rowland_symbolic_reader import array
from randi_target_response import save,sha,HERE


def main():
    p=Path('data/external/cortical_propagation_2023/2021-02-18_RL127.pkl.partial')
    with p.open('rb') as f:
        reader=MechanismsReaderV2(f,p)
        try:reader.load()
        except EOFError:pass
        else:raise AssertionError('Use full payload workflow after completion')
        candidates=[s for s in reader.metastack if any(isinstance(v,str) and v=='stim_start_frames' for v in s)]
        assert len(candidates)==1
        v=dict(zip(candidates[0][::2],candidates[0][1::2]))
        clock=array(v['frame_clock']);stim=array(v['stim_times']);idx=array(v['stim_start_frames'][0])
        assert np.array_equal(np.searchsorted(clock,stim,side='right')-1,idx)
        assert len(stim)==len(idx)==100 and np.all(np.diff(clock)>0)
        assert np.all(clock[idx]<=stim) and np.all(stim<clock[idx+1])
        lag=stim-clock[idx]
        expected=int(np.ceil(v['stim_dur']/1000*v['fps'])+1)
        assert expected==v['duration_frames']==4
        result={'code_sha256':sha(Path(__file__)),'reader_sha256':sha(HERE/'mechanisms_symbolic_reader_v2.py'),
                'parent_sha256':sha(HERE/'mechanisms_RL127_prefix_metadata.json'),
                'snapshot_bytes':reader.limit,'block':'photostim_r','full_payload_verified':False,
                'n_stim':len(stim),'all_preceding_frame_indices_match':True,
                'lag_samples_minmax':[float(lag.min()),float(lag.max())],
                'frame_gap_samples_min_median_max':np.quantile(np.diff(clock),[0,.5,1]).tolist(),
                'stim_gap_samples_unique':np.unique(np.diff(stim)).tolist(),
                'duration_ms_source_interpretation':v['stim_dur'],'artifact_duration_frames':expected,
                'clock_samples':clock.tolist(),'stim_samples':stim.tolist(),'stored_indices':idx.tolist(),
                'limits':['전체 신경 배열과의 대응은 아직 미검증','획득 시계 주파수는 아직 독립 확인하지 않음']}
    save('mechanisms_RL127_prefix_clock_result.json',result)
    print('100 event/frame correspondences PASS; full neural array pending')


if __name__=='__main__':main()
