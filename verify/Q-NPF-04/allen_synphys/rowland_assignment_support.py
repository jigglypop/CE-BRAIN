"""보고된 연속 제한 아래 두 처치가 가능한 이력의 비교 민감도."""
import json
from pathlib import Path
import numpy as np
from rowland_prestate_adjustment import fit
from randi_target_response import HERE, save, sha


def history_states(stim):
    result=['unknown_start']
    streak=0; previous=None
    for i in range(1,len(stim)):
        value=int(stim[i-1])
        streak=streak+1 if value==previous else 1
        previous=value
        result.append(f'{value}:{streak}')
    return result


def main():
    parents=['rowland_native_clock_comparison_result.json','rowland_trial_history_result.json']
    save('rowland_assignment_support_contract.json',{
        'question':'연속 배정 제한으로 test/catch 중 하나가 금지되는 이력을 제외하면 대비가 달라지는가',
        'code_sha256':sha(Path(__file__)), 'parents':{p:sha(HERE/p) for p in parents},
        'helper_sha256':sha(HERE/'rowland_prestate_adjustment.py'),
        'history':'제외 전 전체 시행 기록에서 직전 유형과 연속 길이를 계산',
        'rule':'직전 catch 3연속 또는 test 3연속 이력 제외; 최초 기록 시행은 선행 이력 미상으로 제외',
        'interpretation':'보고된 제한만 고려한 공통 배정 가능 집합; 다른 배정 제약은 미확인',
        'models':['무보정','원래 시각+S1 pre+S2 pre 보정'],
        'limits':['배정 확률을 추정하거나 1/2로 가정하지 않음','무작위화 검정 또는 인과효과 아님',
                  '이력 선택은 추정 대상을 바꾸며 기록 누락을 해결하지 않음'],
        'claim_ceiling':'BIO_EVIDENCE_L1'})
    assert history_states([0,0,0,1,2])==['unknown_start','0:1','0:2','0:3','1:1']
    outcomes=json.loads((HERE/parents[0]).read_text(encoding='utf-8'))['rows']
    histories={(r['mouse'],r['run']):r for r in json.loads((HERE/parents[1]).read_text(encoding='utf-8'))['sessions']}
    rows=[]
    for r in outcomes:
        h=histories[(r['mouse'],r['run'])]
        nominal=np.array(h['original_nominal'])
        stim=np.where(nominal==0,0,np.where(nominal==150,2,1))
        states=history_states(stim)
        for i,state in enumerate(states):
            if state!='unknown_start':
                previous,streak=map(int,state.split(':'))
                assert streak<=3 and not (streak==3 and stim[i]==previous)
        idx=np.array(r['original_indices']);t=np.array(r['test']);y=np.array(r['s2_delta'])
        selected_states=np.array(states)[idx]
        keep=~np.isin(selected_states,['unknown_start','0:3','1:3'])
        z=np.column_stack([r['native_samples'],r['s1_pre'],r['s2_pre']])
        models={}
        for name,cov in [('raw',np.empty((len(y),0))),('adjusted',z)]:
            full=fit(y,t,cov);selected=fit(y[keep],t[keep],cov[keep])
            assert abs(full['coefficient']-r['models']['all_native'][name]['coefficient'])<1e-12
            models[name]={'full':full,'selected':selected,'sign_changed':bool(full['coefficient']*selected['coefficient']<0)}
        counts={state:{'catch':int(sum((selected_states==state)&(t==0))),
                       'test':int(sum((selected_states==state)&(t==1)))} for state in sorted(set(states))}
        rows.append({'mouse':r['mouse'],'run':r['run'],'history_counts':counts,
                     'removed_original_indices':idx[~keep].tolist(),
                     'selected_indices':idx[keep].tolist(),'selected_catch':int(sum(keep&(t==0))),
                     'selected_test':int(sum(keep&(t==1))),'models':models})
    assert len(rows)==11
    save('rowland_assignment_support_result.json',{'contract_sha256':sha(HERE/'rowland_assignment_support_contract.json'),'rows':rows})
    for r in rows:print(r['mouse'],r['run'],len(r['removed_original_indices']),*[round(r['models'][m][v]['coefficient'],7) for m in ['raw','adjusted'] for v in ['full','selected']])


if __name__=='__main__':main()
