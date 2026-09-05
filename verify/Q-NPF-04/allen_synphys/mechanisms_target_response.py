"""고정 표적 집합의 조건별 S1 형광 반응을 비교한다."""
import json
from pathlib import Path
import numpy as np
from mechanisms_response import response, window_mask
from mechanisms_symbolic_reader_v3 import MechanismsReaderV3
from rowland_sessions import ExactReads
from rowland_symbolic_reader import array
from randi_target_response import HERE, save, sha


def main():
    contract_path = HERE/'mechanisms_RL127_target_response_contract.json'
    c = json.loads(contract_path.read_text(encoding='utf-8'))
    parent = json.loads((HERE/c['parent']).read_text(encoding='utf-8'))
    path = Path('data/external/cortical_propagation_2023/2021-02-18_RL127.pkl')
    assert sha(path) == parent['payload_sha256']
    with path.open('rb') as f:
        root = MechanismsReaderV3(ExactReads(f,path.stat().st_size),path).load()
        assert f.tell() == path.stat().st_size
        keys = ('photostim_s','photostim_r','spont')
        values = {k:root.state[k].state for k in keys}
        trials = {k:array(v['all_trials'][0]) for k,v in values.items()}
        means = {k:array(v['raw'][0]).mean(axis=1) for k,v in values.items()}
        ids = np.asarray(values['spont']['cell_id'][0])
        s1 = np.asarray(values['spont']['cell_s1'][0],dtype=bool)
        masks = {k:array(values[k]['targeted_cells']).astype(bool) for k in keys[:2]}
        assert not np.any(masks[keys[0]] & masks[keys[1]])
        assert all(np.all(~mask | s1) for mask in masks.values())
        keep = np.ones(len(ids),dtype=bool)
        for k,v in values.items():
            assert np.array_equal(np.asarray(v['cell_id'][0]),ids)
            assert np.array_equal(np.asarray(v['cell_s1'][0],dtype=bool),s1)
            assert trials[k].shape == (2334,182,100) and np.isfinite(trials[k]).all()
            keep &= (np.max(np.abs(trials[k]),axis=(1,2)) <= 10) & (means[k] > 0)
        common = np.stack(list(means.values())).mean(axis=0,dtype=np.float64)
        rows = []
        for window in c['windows']:
            deltas = {}
            for k,v in values.items():
                t = (np.arange(182)-v['pre_frames'])/v['fps']
                pre = window_mask(t,c['baseline']); post = window_mask(t,window)
                assert not post[v['pre_frames']:v['pre_frames']+v['duration_frames']].any()
                deltas[k] = response(trials[k],pre,post)
            for own,mask in masks.items():
                other = next(k for k in keys[:2] if k != own)
                for selection in ('all','author_positive'):
                    selected = mask if selection == 'all' else mask&keep
                    assert selected.any()
                    for norm in ('original','shared'):
                        if norm == 'shared' and selection == 'all': continue
                        summaries = {}
                        for k in keys:
                            x = deltas[k][selected]
                            if norm == 'shared': x = x*(means[k][selected]/common[selected])[:,None]
                            assert np.isfinite(x).all()
                            y = x.mean(axis=0)
                            summaries[k] = {'mean':float(y.mean()),'first50':float(y[:50].mean()),
                                            'last50':float(y[50:].mean()),'trial_values':y.tolist(),
                                            'cell_means':x.mean(axis=1).tolist()}
                        contrasts = {label:{part:summaries[own][part]-summaries[k][part] for part in ('mean','first50','last50')}
                                     for label,k in [('own-sham','spont'),('own-other',other)]}
                        rows.append({'window':window,'target_group':own,'selection':selection,'normalization':norm,
                                     'cell_n':int(selected.sum()),'cell_indices':np.flatnonzero(selected).tolist(),
                                     'conditions':summaries,'contrasts':contrasts})
    result = {'code_sha256':sha(Path(__file__)),'contract_sha256':sha(contract_path),
              'helper_sha256':sha(HERE/'mechanisms_response.py'),'payload_sha256':parent['payload_sha256'],
              'target_n':{k:int(m.sum()) for k,m in masks.items()},
              'retained_n':{k:int(sum(m&keep)) for k,m in masks.items()},'rows':rows,'limits':c['limits']}
    save('mechanisms_RL127_target_response_result.json',result)
    print(json.dumps({'target_n':result['target_n'],'retained_n':result['retained_n']}))
    for row in rows:
        print(json.dumps({k:row[k] for k in ('window','target_group','selection','normalization','cell_n','contrasts')}))


if __name__ == '__main__': main()
