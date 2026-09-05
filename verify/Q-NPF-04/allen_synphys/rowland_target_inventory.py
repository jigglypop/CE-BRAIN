"""명목 표적 수와 공간 마스크 ROI 수를 구분한 시행별 입력 점검."""
import json
from pathlib import Path
import numpy as np
from randi_target_response import HERE,save,sha
from rowland_sessions import read_sessions
from rowland_symbolic_reader import array
from rowland_first_session import BASE


def main():
    predpath=HERE/'rowland_forward_prediction_result.json'
    sourcepath=HERE/'rowland_prestate_adjustment_result.json'
    contract=save('rowland_target_inventory_contract.json',{
        'question':'명목 자극 표적 수와 기록 ROI 마스크 수가 같으며 기존 학습·평가에서 명목 수준이 겹치는가',
        'code_sha256':sha(Path(__file__)),'prediction_sha256':sha(predpath),'summaries_sha256':sha(sourcepath),
        'source_code_sha256':{n:sha(BASE/n) for n in ['author_Session.py','vape_run_functions.py']},
        'source_limit':'Vape 보관 판본의 공간 마스크 알고리즘 확인; 실제 export 생성의 역사적 판본 일치는 미확인',
        'mask_semantics':'GetTargets는 자극 위치 주변 마스크와 ROI 픽셀 겹침 여부; 활성화 측정 아님',
        'nominal_semantics':'trial_subsets 표지; 실제 활성 세포 수나 광출력으로 대체하지 않음',
        'selection':'기존 전체 11세션; 유효 catch/test는 원래 시행 번호로 기존 분석에 연결',
        'groups':'명목 표적 수별 mask ROI 범위, 학습·평가 표본 수, 고정된 예측의 집단별 MSE',
        'limits':['반응 기반 표본 선택 없음','명목 수 불일치를 오류로 단정하지 않음','재적합 없음',
                  '동일 명목 수가 동일 표적 identity·에너지·세포 상태를 보장하지 않음'],
        'claim_ceiling':'스키마 L0 및 기존 평가 시행의 탐색적 예측 분해 L1'})
    sessions,status=read_sessions(BASE/'sessions_lite_flu_2022-08-11.pkl');assert status['pickle_complete']
    preds={(r['mouse'],r['run']):r for r in json.loads(predpath.read_text(encoding='utf-8'))['rows']}
    sums={(r['mouse'],r['run']):r for r in json.loads(sourcepath.read_text(encoding='utf-8'))['rows']}
    rows=[]
    for s in sessions:
        key=(s['mouse'],s['run_number']);p=preds[key];summary=sums[key]
        idx=array(s['nonnan_trials']);nominal=array(s['trial_subsets']);stim=array(s['photostim'])
        targets=array(s['is_target']);s2=array(s['s2_bool'])
        assert np.all(nominal==nominal.astype(int)) and np.all(nominal>=0)
        mask_count=targets[:,:,0].sum(axis=0)
        assert not targets[s2,:,0].any() and not mask_count[stim==0].any()
        assert np.array_equal(nominal==0,stim==0) and np.array_equal(nominal==150,stim==2)
        mapping={int(i):j for j,i in enumerate(idx)}
        eligible=np.array([mapping[i] for i in summary['original_indices']])
        tr=np.array([mapping[i] for i in p['train_indices']]);ev=np.array([mapping[i] for i in p['eval_indices']])
        assert np.array_equal(stim[eligible],np.array(summary['test']))
        y=np.array(p['observed']);e0=(y-np.array(p['baseline_prediction']))**2;e1=(y-np.array(p['added_prediction']))**2
        groups=[]
        for level in np.unique(nominal[eligible]):
            selected=eligible[nominal[eligible]==level];m=nominal[ev]==level
            groups.append({'nominal':int(level),'n':len(selected),'train_n':int(np.sum(nominal[tr]==level)),
                'eval_n':int(m.sum()),'mask_roi_min':int(mask_count[selected].min()),'mask_roi_max':int(mask_count[selected].max()),
                'mask_nominal_equal_n':int(np.sum(mask_count[selected]==level)),
                'mse_baseline':float(e0[m].mean()) if m.any() else None,
                'mse_added':float(e1[m].mean()) if m.any() else None})
        rows.append({'mouse':key[0],'run':key[1],'groups':groups,
            'original_indices':idx[eligible].tolist(),'nominal_counts':nominal[eligible].tolist(),
            'mask_roi_counts':mask_count[eligible].tolist(),
            'unseen_eval_levels':sorted(set(nominal[ev].tolist())-set(nominal[tr].tolist()))})
        if isinstance(targets,np.memmap):targets._mmap.close()
    save('rowland_target_inventory_result.json',{'contract_sha256':sha(contract),'rows':rows})
    print(json.dumps([{'mouse':r['mouse'],'run':r['run'],'levels':[g['nominal'] for g in r['groups']],
      'test_n':sum(g['n'] for g in r['groups'] if g['nominal']>0),
      'mask_equal_test_n':sum(g['mask_nominal_equal_n'] for g in r['groups'] if g['nominal']>0),
      'unseen_eval_levels':r['unseen_eval_levels'],
      'train_eval':[[g['nominal'],g['train_n'],g['eval_n']] for g in r['groups']]} for r in rows]))


if __name__=='__main__':main()
