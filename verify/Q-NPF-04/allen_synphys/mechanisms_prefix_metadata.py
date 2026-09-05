"""수집 중 피클의 완성된 메타데이터만 별도 스냅샷으로 기록한다."""
import hashlib
import json
from pathlib import Path
import numpy as np
from mechanisms_symbolic_reader_v2 import MechanismsReaderV2
from rowland_symbolic_reader import array, Symbol
from randi_target_response import save,sha


def main():
    p=Path('data/external/cortical_propagation_2023/2021-02-18_RL127.pkl.partial')
    with p.open('rb') as stream:
        reader=MechanismsReaderV2(stream,p)
        cls=reader.find_class('builtins','range')
        assert issubclass(cls,Symbol) and cls(0,10).args==(0,10)
        try:reader.load()
        except EOFError as error:pending=str(error)
        else:raise AssertionError('Expected partial payload; use complete audit instead')
        candidates=[stack for stack in reader.metastack if any(isinstance(v,str) and v=='stim_start_frames' for v in stack)]
        assert len(candidates)==1
        values=dict(zip(candidates[0][::2],candidates[0][1::2]))
        result={'snapshot_bytes':reader.limit,'pending':pending,'complete_file_verified':False,
                'block':'photostim_r (first serialized block; chronological order not established)',
                'fps':values['fps'],'n_planes':values['n_planes'],'n_units':values['n_units'],
                'stim_dur_stored':values['stim_dur'],'duration_frames':values['duration_frames'],
                'code_sha256':sha(Path(__file__))}
        for key in ['frame_clock','stim_times','stim_start_frames']:
            value=values[key];a=array(value[0] if isinstance(value,list) else value)
            assert a.ndim==1 and np.isfinite(a).all() and np.all(np.diff(a)>0)
            result[key]={'count':len(a),'first':float(a[0]),'last':float(a[-1])}
        stream.seek(0);digest=hashlib.sha256();remaining=reader.limit
        while remaining:
            block=stream.read(min(4*1024*1024,remaining));assert block
            digest.update(block);remaining-=len(block)
        result['prefix_sha256']=digest.hexdigest()
    save('mechanisms_RL127_prefix_metadata.json',result)
    print(json.dumps(result))


if __name__=='__main__':main()
