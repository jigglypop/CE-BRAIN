"""도착한 첫 블록의 raw→dfof 변환을 셀 묶음별로 독립 대조한다."""
import argparse
import json
from pathlib import Path
import numpy as np
from mechanisms_symbolic_reader_v2 import MechanismsReaderV2
from rowland_symbolic_reader import Symbol, array
from randi_target_response import HERE, save, sha


def compare(raw, stored):
    assert raw.shape==stored.shape and raw.ndim==2
    maximum=0.;bad=0;negative=0;zero=0;nonfinite=0
    for start in range(0,len(raw),32):
        values=raw[start:start+32]
        mean=values.mean(axis=1,keepdims=True)
        negative+=int(np.sum(mean<0));zero+=int(np.sum(mean==0))
        with np.errstate(divide='ignore',invalid='ignore'):
            expected=(values-mean)/mean
        actual=stored[start:start+32]
        finite=np.isfinite(expected)&np.isfinite(actual)
        nonfinite+=int(np.sum(~finite))
        if finite.any():maximum=max(maximum,float(np.max(np.abs(expected[finite]-actual[finite]))))
        bad+=int(np.sum(~np.isclose(expected,actual,rtol=1e-6,atol=1e-6,equal_nan=False)))
    return {'max_absolute_difference_finite':maximum,'mismatched_elements':bad,
            'nonfinite_comparison_elements':nonfinite,'negative_mean_cells':negative,
            'zero_mean_cells':zero,'passed':bad==0 and nonfinite==0}


def self_test():
    raw=np.tile(np.array([[2,4,6],[-2,-4,-6]],dtype=np.float32),(20,1))
    expected=(raw-raw.mean(axis=1,keepdims=True))/raw.mean(axis=1,keepdims=True)
    assert compare(raw,expected)['passed']
    altered=expected.copy();altered[-1,-1]+=0.01
    assert compare(raw,altered)['mismatched_elements']==1
    assert not compare(np.zeros((2,3),dtype=np.float32),np.zeros((2,3)))['passed']


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--self-test',action='store_true');args=cli.parse_args()
    self_test()
    if args.self_test:
        print('Comparator positive, corruption, zero-denominator checks PASS');return
    base=Path('data/external/cortical_propagation_2023')
    path=base/'2021-02-18_RL127.pkl'
    if not path.exists():path=path.with_suffix('.pkl.partial')
    with path.open('rb') as stream:
        reader=MechanismsReaderV2(stream,path)
        try:
            root=reader.load()
            assert not stream.read(1)
            values=root.state['photostim_r'].state;complete=True
        except EOFError:
            complete=False
            stacks=[s for s in reader.metastack if any(isinstance(v,str) and v=='stim_start_frames' for v in s)]
            # A later partial block must never be mistaken for the first block.
            first=[v for v in reader.memo.values() if isinstance(v,Symbol) and v.reference==('utils.interareal_analysis','interarealAnalysis') and isinstance(v.state,dict)]
            if first:values=first[0].state
            elif len(stacks)==1:values=dict(zip(stacks[0][::2],stacks[0][1::2]))
            else:print('PENDING: first block metadata not available');return
        if not values.get('dfof') or not isinstance(values['dfof'][0].state,tuple):
            print(json.dumps({'status':'PENDING','snapshot_bytes':reader.limit,'reason':'first dfof array incomplete'}));return
        raw=array(values['raw'][0]);stored=array(values['dfof'][0])
        assert raw.shape==(2334,22986), 'Unexpected first block; inspect identity'
        result=compare(raw,stored)
        result.update({'snapshot_bytes':reader.limit,'full_pickle_read':complete,'raw_shape':list(raw.shape),
                       'code_sha256':sha(Path(__file__)),'helper_sha256':sha(base/'vape_utils_funcs.py'),
                       'scope':'first photostim_r raw/dfof pair; not biological validation'})
        save('mechanisms_RL127_normalization_check.json',result);print(json.dumps(result))


if __name__=='__main__':main()
