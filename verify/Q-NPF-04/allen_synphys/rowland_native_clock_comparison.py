"""원래 획득 시각을 사용한 동일 집합·확장 집합의 탐색적 대비."""
import json
from pathlib import Path
import numpy as np
from rowland_sessions import read_sessions
from rowland_symbolic_reader import array
from rowland_prestate_adjustment import fit, synthetic_check
from randi_target_response import HERE, save, sha


def main():
    parents=['rowland_native_clock_audit_result.json','rowland_prestate_adjustment_result.json']
    save('rowland_native_clock_comparison_contract.json', {
        'question':'원래 시각 사용과 보존 시행 추가가 세션별 반응 대비를 바꾸는가',
        'code_sha256':sha(Path(__file__)), 'parents':{p:sha(HERE/p) for p in parents},
        'dependencies':{p:sha(HERE/p) for p in ['rowland_sessions.py','rowland_symbolic_reader.py','rowland_prestate_adjustment.py']},
        'groups':['기존 유한 행동시각 집합','같은 집합에서 원래 시각 사용','전체 보존 catch/test에서 원래 시각 사용'],
        'time':'원래 획득 sample 값; 선형 표준화 공변량으로만 사용, 초 단위 임계값 없음',
        'endpoint':'기존 명목 pre[180:225], post[285:330] S2 세포 평균 변화',
        'models':['무보정','시각+S1 pre+S2 pre 보정'],
        'selection':'모든 11세션 보고; 행동 라벨로 추가 제외하지 않음',
        'limits':['사후 기술적 대비; 인과효과나 독립 검증 아님','실제 프레임 정렬 독립 확인 불가'],
        'claim_ceiling':'BIO_EVIDENCE_L1'})
    prior={(r['mouse'],r['run']):r for r in json.loads((HERE/parents[1]).read_text(encoding='utf-8'))['rows']}
    ss,status=read_sessions(Path('data/external/cortical_propagation_2023/sessions_lite_flu_2022-08-11.pkl'))
    assert status['pickle_complete'] and len(ss)==11
    synthetic_check(); rows=[]
    for s in ss:
        r=prior[(s['mouse'],s['run_number'])]
        idx=array(s['nonnan_trials']);stim=array(s['photostim'])
        native=array(s['tstart_galvo'])[idx];galvo=array(s['galvo_ms'])[idx]
        y=array(s['behaviour_trials']);s1=array(s['s1_bool']);s2=array(s['s2_bool'])
        assert s['frequency']==30 and s['pre_frames']==240 and y.shape[2]==420
        pre=y[:,:,180:225].mean(axis=2);post=y[:,:,285:330].mean(axis=2)
        a=pre[s1].mean(axis=0);b=pre[s2].mean(axis=0)
        delta=(post[s2]-pre[s2]).mean(axis=0)
        allmask=np.isin(stim,[0,1]);oldmask=allmask & np.isfinite(galvo)
        assert np.array_equal(idx[oldmask],r['original_indices'])
        for values,key in [(delta,'s2_delta'),(a,'s1_pre'),(b,'s2_pre')]:
            assert np.allclose(values[oldmask],r[key],atol=1e-12,rtol=0)
        assert np.isfinite(native[allmask]).all() and np.all(np.diff(native[allmask])>0)
        models={}
        for name,mask,clock in [('old_behavior',oldmask,galvo),('old_native',oldmask,native),('all_native',allmask,native)]:
            t=(stim[mask]==1).astype(float)
            z=np.column_stack([clock[mask]-clock[mask][0],a[mask],b[mask]])
            models[name]={'raw':fit(delta[mask],t,[]),'adjusted':fit(delta[mask],t,z)}
        assert abs(models['old_behavior']['raw']['coefficient']-r['raw']['coefficient'])<1e-12
        assert abs(models['old_behavior']['adjusted']['coefficient']-r['time_prestate']['coefficient'])<1e-12
        added=allmask & ~oldmask
        rows.append({'mouse':s['mouse'],'run':s['run_number'],'added_indices':idx[added].tolist(),
                     'added_delta':delta[added].tolist(),'added_stim':stim[added].tolist(),
                     'test_n':int(sum(stim[allmask]==1)),'catch_n':int(sum(stim[allmask]==0)),
                     'models':models,'original_indices':idx[allmask].tolist(),
                     'native_samples':native[allmask].tolist(),'test':(stim[allmask]==1).astype(int).tolist(),
                     's1_pre':a[allmask].tolist(),'s2_pre':b[allmask].tolist(),'s2_delta':delta[allmask].tolist()})
    assert sum(len(r['added_indices']) for r in rows)==7
    save('rowland_native_clock_comparison_result.json',{'contract_sha256':sha(HERE/'rowland_native_clock_comparison_contract.json'),'rows':rows})
    for r in rows:
        print(r['mouse'],r['run'],len(r['added_indices']),*[round(r['models'][g][m]['coefficient'],9) for m in ['raw','adjusted'] for g in ['old_behavior','old_native','all_native']])


if __name__=='__main__':main()
