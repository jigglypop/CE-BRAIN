"""두 번째 완성 블록의 시행과 표적을 검증한다."""
import json
import pickle
from pathlib import Path
import numpy as np
from mechanisms_symbolic_reader_v3 import MechanismsReaderV3
from rowland_sessions import ExactReads
from rowland_symbolic_reader import Symbol,array
from randi_target_response import HERE,save,sha


class Ready(Exception):pass


class TwoBlockReader(MechanismsReaderV3):
    dispatch=MechanismsReaderV3.dispatch.copy()

    def build(self):
        pickle._Unpickler.load_build(self)
        obj=self.stack[-1]
        if isinstance(obj,Symbol) and obj.reference==('utils.interareal_analysis','interarealAnalysis'):
            name=self.stack[-2]
            assert name in ('photostim_r','photostim_s')
            if name=='photostim_r':self.first=obj
            else:
                self.second=obj;self.object_end=self.stream.tell();raise Ready()

    dispatch[pickle.BUILD[0]]=build


def main():
    path=Path('data/external/cortical_propagation_2023/2021-02-18_RL127.pkl.partial')
    if not path.exists():path=path.with_suffix('')
    with path.open('rb') as f:
        reader=TwoBlockReader(ExactReads(f,path.stat().st_size),path)
        try:reader.load()
        except Ready:pass
        a=reader.first.state;v=reader.second.state
        data=array(v['dfof'][0]);trials=array(v['all_trials'][0]);starts=array(v['stim_start_frames'][0])
        pre,post,duration=v['pre_frames'],v['post_frames'],v['duration_frames']
        assert trials.shape==(2334,pre+post,100) and len(starts)==100
        maximum=0.;bad=0
        for i,start in enumerate(starts):
            assert start-pre>=0 and start+post<=data.shape[1]
            trace=data[:,start-pre:start+post]
            expected=trace-trace[:,:pre].mean(axis=1,keepdims=True)
            expected[:,pre:pre+duration]=0
            actual=trials[:,:,i];assert np.isfinite(actual).all()
            bad+=int(sum((~np.isclose(actual,expected,rtol=1e-6,atol=1e-6)).flat))
            maximum=max(maximum,float(np.max(np.abs(actual-expected))))
        targets=array(v['targeted_cells']);first_targets=array(a['targeted_cells'])
        image=np.zeros((v['frame_x'],v['frame_y']),dtype=np.uint16);cells=np.zeros_like(image)
        areas=np.array([array(x) for x in v['target_areas']]);image[areas[:,:,1],areas[:,:,0]]=1
        for i,(x,y) in enumerate(zip(v['cell_x'][0],v['cell_y'][0])):cells[array(x),array(y)]=i+1
        ids=np.unique(cells*image)[1:]-1;reconstructed=np.zeros(len(targets),dtype=bool);reconstructed[ids]=True
        assert np.array_equal(reconstructed,targets)
        s1=np.asarray(v['cell_s1'][0],dtype=bool)
        result={'code_sha256':sha(Path(__file__)),'second_block_end':reader.object_end,'snapshot_bytes':reader.limit,
                'full_file_verified':False,'trial_shape':list(trials.shape),'pre_frames':pre,'post_frames':post,
                'artifact_frames':duration,'mismatched_elements':bad,'max_absolute_difference':maximum,'passed':bad==0,
                'target_coordinates':len(v['target_coords']),'target_roi_n':int(targets.sum()),
                'target_s1_n':int(sum(targets&s1)),'target_s2_n':int(sum(targets&~s1)),
                'target_mask_reconstructed':True,'overlap_with_first_roi_n':int(sum(targets&first_targets)),
                'target_indices':np.flatnonzero(targets).tolist(),
                'limits':['투사 표지의 독립 검증이나 신경 효과의 증명은 아님']}
        save('mechanisms_RL127_second_block_check.json',result);print(json.dumps(result))


if __name__=='__main__':main()
