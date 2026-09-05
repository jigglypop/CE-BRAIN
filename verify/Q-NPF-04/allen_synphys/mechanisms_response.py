"""사전에 기록한 기준으로 RL127의 S2 반응 차이를 계산한다."""
import json
from pathlib import Path
import numpy as np
from mechanisms_symbolic_reader_v3 import MechanismsReaderV3
from rowland_sessions import ExactReads
from rowland_symbolic_reader import array
from randi_target_response import HERE, save, sha


def window_mask(t, bounds):
    return (t >= bounds[0]) & (t < bounds[1])


def response(trials, pre, post):
    assert pre.any() and post.any() and not np.any(pre & post)
    return trials[:, post, :].mean(axis=1, dtype=np.float64)-trials[:, pre, :].mean(axis=1, dtype=np.float64)


def main():
    contract_path = HERE/'mechanisms_RL127_response_contract.json'
    c = json.loads(contract_path.read_text(encoding='utf-8'))
    path = Path('data/external/cortical_propagation_2023/2021-02-18_RL127.pkl')
    assert sha(path) == c['payload_sha256']
    gate = json.loads((HERE/'mechanisms_RL127_complete_check_v2.json').read_text(encoding='utf-8'))
    assert gate['passed'] and gate['payload_sha256'] == c['payload_sha256']
    fixture = np.zeros((2, 6, 3)); fixture[:, 3:5, :] = 2
    assert np.all(response(fixture, np.array([1,1,0,0,0,0],bool), np.array([0,0,0,1,1,0],bool)) == 2)
    names = {'projecting': 'photostim_s', 'non_projecting': 'photostim_r', 'sham': 'spont'}
    with path.open('rb') as f:
        root = MechanismsReaderV3(ExactReads(f,path.stat().st_size),path).load()
        assert f.tell() == path.stat().st_size
        values = {name: root.state[key].state for name,key in names.items()}
        trials = {name: array(v['all_trials'][0]) for name,v in values.items()}
        means = {name: array(v['raw'][0]).mean(axis=1) for name,v in values.items()}
        s2 = array(values['sham']['cell_s2'][0]).astype(bool)
        s1 = np.asarray(values['sham']['cell_s1'][0],dtype=bool)
        assert s2.shape == s1.shape == (2334,) and not np.any(s1&s2)
        for name,v in values.items():
            assert np.array_equal(array(v['cell_s2'][0]).astype(bool),s2)
            assert not np.any(array(v['targeted_cells']).astype(bool)&s2)
            assert trials[name].shape == (2334,182,100) and np.isfinite(trials[name]).all()
        author = np.ones(2334,dtype=bool)
        positive = np.ones(2334,dtype=bool)
        for name in names:
            author &= np.max(np.abs(trials[name]),axis=(1,2)) <= 10
            positive &= means[name] > 0
        masks = {'all': s2, 'author': s2&author, 'author_positive': s2&author&positive}
        shared = np.stack(list(means.values())).mean(axis=0,dtype=np.float64)
        rows = []
        for axis in ('nominal','stored'):
            for window in c['windows']:
                deltas = {}; frame_indices = {}
                for name,v in values.items():
                    t = (np.arange(182)-v['pre_frames'])/v['fps'] if axis == 'nominal' else array(v['time'])
                    pre = window_mask(t,c['baseline']); post = window_mask(t,window)
                    assert not post[v['pre_frames']:v['pre_frames']+v['duration_frames']].any()
                    deltas[name] = response(trials[name],pre,post)
                    frame_indices[name] = {'pre':np.flatnonzero(pre).tolist(),'post':np.flatnonzero(post).tolist()}
                for mask_name,mask in masks.items():
                    assert mask.any()
                    for norm in ('original','shared'):
                        if norm == 'shared' and mask_name != 'author_positive': continue
                        series = {}
                        for name in names:
                            delta = deltas[name][mask]
                            if norm == 'shared': delta = delta*(means[name][mask]/shared[mask])[:,None]
                            assert np.isfinite(delta).all()
                            series[name] = delta.mean(axis=0)
                        summaries = {name:{'mean':float(x.mean()),'first50':float(x[:50].mean()),'last50':float(x[50:].mean()),'trial_values':x.tolist()} for name,x in series.items()}
                        contrasts = {}
                        for a,b in [('projecting','non_projecting'),('projecting','sham'),('non_projecting','sham')]:
                            contrasts[a+'-'+b] = {k:summaries[a][k]-summaries[b][k] for k in ('mean','first50','last50')}
                        rows.append({'axis':axis,'window':window,'mask':mask_name,'normalization':norm,
                                     'cell_n':int(mask.sum()),'cell_indices':np.flatnonzero(mask).tolist(),
                                     'frames':frame_indices,'conditions':summaries,'contrasts':contrasts})
    result = {'contract_sha256':sha(contract_path),'code_sha256':sha(Path(__file__)),
              'payload_sha256':c['payload_sha256'],'gate_sha256':sha(HERE/'mechanisms_RL127_complete_check_v2.json'),
              's2_n':int(s2.sum()),'author_removed_s2':int(sum(s2&~author)),
              'positive_removed_after_author_s2':int(sum(s2&author&~positive)), 'rows':rows,
              'claim_ceiling':c['claim_ceiling'],'limits':c['limitations']}
    save('mechanisms_RL127_response_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','limits')},ensure_ascii=True))
    for row in rows:
        print(json.dumps({k:row[k] for k in ('axis','window','mask','normalization','cell_n','contrasts')}))


if __name__ == '__main__': main()
