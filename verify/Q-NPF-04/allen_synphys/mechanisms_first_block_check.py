"""완전히 구성된 첫 블록에서 100개 시행의 추출을 재현한다."""
import json
import pickle
from pathlib import Path
import numpy as np
from mechanisms_symbolic_reader_v3 import MechanismsReaderV3
from rowland_sessions import ExactReads
from rowland_symbolic_reader import Symbol,array
from randi_target_response import HERE,save,sha


class BlockReady(Exception):pass


class FirstBlockReader(MechanismsReaderV3):
    dispatch=MechanismsReaderV3.dispatch.copy()

    def build(self):
        pickle._Unpickler.load_build(self)
        obj=self.stack[-1]
        if isinstance(obj,Symbol) and obj.reference==('utils.interareal_analysis','interarealAnalysis'):
            # Parent dictionary is not built yet; confirm the pending field name.
            assert len(self.stack)>=2 and self.stack[-2]=='photostim_r'
            self.block=obj;self.object_end=self.stream.tell();raise BlockReady()

    dispatch[pickle.BUILD[0]]=build


def main():
    path=Path('data/external/cortical_propagation_2023/2021-02-18_RL127.pkl.partial')
    if not path.exists():path=path.with_suffix('')
    with path.open('rb') as stream:
        reader=FirstBlockReader(ExactReads(stream,path.stat().st_size),path)
        try:reader.load()
        except BlockReady:pass
        v=reader.block.state
        data=array(v['dfof'][0]);trials=array(v['all_trials'][0]);starts=array(v['stim_start_frames'][0])
        pre,post=v['pre_frames'],v['post_frames'];duration=v['duration_frames']
        assert trials.shape==(2334,pre+post,100) and len(starts)==100
        maxdiff=0.;mismatch=0;finite=True
        for i,start in enumerate(starts):
            assert start-pre>=0 and start+post<=data.shape[1]
            trace=data[:,start-pre:start+post]
            expected=trace-trace[:,:pre].mean(axis=1,keepdims=True)
            expected[:,pre:pre+duration]=0
            actual=trials[:,:,i]
            finite=finite and bool(np.isfinite(actual).all())
            mismatch+=int(np.sum(~np.isclose(actual,expected,rtol=1e-6,atol=1e-6)))
            maxdiff=max(maxdiff,float(np.max(np.abs(actual-expected))))
        time=array(v['time'])
        assert time.shape==(pre+post,) and np.all(np.diff(time)>0)
        result={'code_sha256':sha(Path(__file__)),'reader_sha256':sha(HERE/'mechanisms_symbolic_reader_v3.py'),
                'first_block_end':reader.object_end,'snapshot_bytes':reader.limit,'full_payload_verified':False,
                'trial_shape':list(trials.shape),'pre_frames':pre,'post_frames':post,'artifact_frames':duration,
                'all_100_windows_in_bounds':True,'all_stored_trial_values_finite':finite,
                'mismatched_elements':mismatch,'max_absolute_difference':maxdiff,
                'passed':finite and mismatch==0,'time_first':float(time[0]),'time_last':float(time[-1]),
                'time_at_pre_index':float(time[pre]),
                'limits':['저장 배열의 처리 재현이며 원시 영상과의 물리적 정렬 증명은 아님']}
        save('mechanisms_RL127_first_block_check.json',result);print(json.dumps(result))


if __name__=='__main__':main()
