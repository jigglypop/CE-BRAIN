"""완전히 도착한 첫 세션의 대응 및 S2 반응을 탐색한다. 전체 파일은 아직 미완료일 수 있다."""
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np

from randi_target_response import ROOT, HERE, save, sha
from rowland_symbolic_reader import Reader, Symbol, array

BASE = ROOT / 'data/external/cortical_propagation_2023'


class SessionReader(Reader):
    dispatch = Reader.dispatch.copy()

    def build(self):
        pickle._Unpickler.load_build(self)
        obj = self.stack[-1]
        if isinstance(obj, Symbol) and obj.reference == ('__main__', 'SessionLite'):
            if not hasattr(self, 'first_session'):
                self.first_session = obj.state
                self.first_session_end = self.stream.tell()

    dispatch[pickle.BUILD[0]] = build


def main():
    complete = BASE / 'sessions_lite_flu_2022-08-11.pkl'
    path = complete if complete.exists() else complete.with_suffix('.pkl.partial')
    with path.open('rb') as stream:
        reader = SessionReader(stream, path)
        try:
            reader.load()
        except EOFError:
            pass
    s = reader.first_session
    assert s['mouse'] == 'J064' and s['run_number'] == 10
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        left = reader.first_session_end
        while left:
            block = stream.read(min(left, 4*1024*1024))
            assert block
            digest.update(block)
            left -= len(block)
    contract = {'question': '첫 세션에서 S1 자극 시행과 catch 시행의 S2 신호 변화는 어떠한가',
                'selection': '파일 순 첫 완전한 세션 J064 run10; 독립 확인시험 아님',
                'source_prefix_bytes': reader.first_session_end, 'source_prefix_sha256': digest.hexdigest(),
                'code_sha256': sha(Path(__file__)), 'reader_sha256': sha(HERE / 'rowland_symbolic_reader.py'),
                'pre_seconds': [-2, -.5], 'post_seconds': [1.5, 3], 'windows': 'half-open',
                'clock': '(frame_index-pre_frames)/frequency; stored filter_ps_time offset audited separately',
                'endpoint': '세포별 후 평균-전 평균을 S2 세포 간 평균; native export fluorescence units',
                'groups': 'photostim 0 catch, 1 test; 2 easy 별도 표본 수만; 행동 결과별 기술통계',
                'exclusion': '없음; 직접 S2 표적이 있으면 중단; 모든 선택 창 유한 요구',
                'limits': ['보상·lick·자극 전 상태 미통제', '전체 파일 해시 미확인',
                           '공통 입력·직접경로를 분리한 인과효과 아님', 'single mouse single session'],
                'claim_ceiling': 'BIO_EVIDENCE_L1 provisional local segment; no causal propagation confirmation'}
    save('rowland_first_session_contract.json', contract)
    fields = ['behaviour_trials','is_target','s1_bool','s2_bool','trial_subsets','photostim',
              'outcome','decision','nonnan_trials','galvo_ms','filter_ps_array','filter_ps_time','autorewarded']
    data = {key:array(s[key]) for key in fields}
    y, targets = data['behaviour_trials'], data['is_target']
    assert y.shape == targets.shape == (s['n_cells'],s['n_trials'],s['n_times'])
    nc, nt, nf = y.shape
    for key in ['trial_subsets','photostim','outcome','decision','nonnan_trials','autorewarded']:
        assert data[key].shape == (nt,)
    assert np.array_equal(data['s1_bool'], ~data['s2_bool'])
    assert data['s2_bool'].shape == (nc,) and data['s2_bool'].any()
    assert not targets[data['s2_bool']].any()
    assert np.all(targets == targets[:,:,:1])
    indices = data['nonnan_trials']
    assert np.all(np.diff(indices)>0) and indices.min()>=0 and indices.max()<len(data['galvo_ms'])
    assert np.all(np.diff(data['galvo_ms'][indices])>0)
    assert np.array_equal(data['decision'],np.isin(data['outcome'],['hit','fp']).astype(int))
    stim = data['photostim']
    assert np.array_equal(stim==0,data['trial_subsets']==0)
    assert np.array_equal(stim==2,data['trial_subsets']==150)
    assert not targets[:,stim==0,:].any()
    time = (np.arange(nf)-s['pre_frames'])/s['frequency']
    assert np.array_equal(data['filter_ps_array'],np.arange(nf))
    offset=data['filter_ps_time']-time
    assert np.allclose(offset,1/s['frequency'],atol=1e-12)
    pre=(time>=-2)&(time<-.5)
    post=(time>=1.5)&(time<3)
    signal=y[data['s2_bool']]
    assert np.isfinite(signal[:,:,pre]).all() and np.isfinite(signal[:,:,post]).all()
    delta=(signal[:,:,post].mean(axis=2)-signal[:,:,pre].mean(axis=2)).mean(axis=0)
    summaries={}
    for label,mask in [('catch',stim==0),('test',stim==1),('easy',stim==2)]:
        assert mask.any()
        summaries[label]={'n':int(mask.sum())}
        if label!='easy':
            summaries[label].update(mean=float(delta[mask].mean()),median=float(np.median(delta[mask])))
    by_outcome={str(k):{'n':int(np.sum((stim<2)&(data['outcome']==k))),
                       'mean':float(delta[(stim<2)&(data['outcome']==k)].mean())}
                for k in np.unique(data['outcome'][stim<2])}
    result={'contract_sha256':sha(HERE/'rowland_first_session_contract.json'),
            's1_cells':int(data['s1_bool'].sum()),'s2_cells':int(data['s2_bool'].sum()),
            'trial_count':nt,'original_trial_count':len(data['galvo_ms']),
            'stored_time_offset_seconds':float(offset[0]),'artifact_gap_frames':s['art_gap_stop']-s['art_gap_start'],
            'summaries':summaries,'by_outcome':by_outcome,
            'test_minus_catch':summaries['test']['mean']-summaries['catch']['mean'],
            'trials':[{'trial':i,'original_trial':int(indices[i]),'photostim':int(stim[i]),
                       'target_count_requested':int(data['trial_subsets'][i]),
                       'target_count_retained':int(targets[:,i,0].sum()),
                       'outcome':str(data['outcome'][i]),'autorewarded':bool(data['autorewarded'][i]),
                       's2_delta':float(delta[i])} for i in range(nt)],
            'complete_file_verified':False}
    save('rowland_first_session_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='trials'}))
    for v in data.values():
        if isinstance(v,np.memmap):v._mmap.close()


if __name__=='__main__':
    main()
