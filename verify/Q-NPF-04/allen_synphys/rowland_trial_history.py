"""보존된 전체 시행 배정과 분석용 부분집합을 대조한다."""
from pathlib import Path
import json
import numpy as np
from rowland_sessions import read_sessions
from rowland_symbolic_reader import array
from randi_target_response import save, sha, HERE


def runs(values):
    cuts = np.r_[0, np.flatnonzero(np.diff(values)) + 1, len(values)]
    return [{'start': int(a), 'stop': int(b), 'type': int(values[a]), 'length': int(b-a)}
            for a, b in zip(cuts[:-1], cuts[1:])]


def main():
    assert [r['length'] for r in runs(np.array([0,0,1,2,2,2]))] == [2,1,3]
    sessions, status = read_sessions(Path('data/external/cortical_propagation_2023/sessions_lite_flu_2022-08-11.pkl'))
    assert status['pickle_complete'] and len(sessions) == 11
    rows = []
    for s in sessions:
        nested = s['subsets'].state
        nominal, outcomes = array(nested['trial_subsets']), array(nested['outcome'])
        idx, galvo = array(s['nonnan_trials']), array(s['galvo_ms'])
        assert len(nominal) == len(outcomes) == len(galvo) == len(nested['trial_info'])
        assert np.array_equal(nominal[idx], array(s['trial_subsets']))
        assert np.array_equal(outcomes[idx], array(s['outcome']))
        assert np.isin(nominal, [0,5,10,20,30,40,50,150]).all()
        stim = np.where(nominal == 0, 0, np.where(nominal == 150, 2, 1))
        kept = np.zeros(len(stim), dtype=bool); kept[idx] = True
        eligible = kept & np.isfinite(galvo)
        groups = {}
        for name, code in [('catch',0),('test',1),('easy',2)]:
            mask = stim == code
            groups[name] = {'original': int(mask.sum()), 'exported': int((mask & kept).sum()),
                            'eligible': int((mask & eligible).sum()),
                            'excluded_indices': np.flatnonzero(mask & ~eligible).tolist()}
        consecutive = runs(stim)
        early = []
        for i in idx:
            lick = array(s['spiral_lick'][i])
            if outcomes[i] == 'hit' and len(lick) and lick[0] < 150:
                early.append(int(i))
        rows.append({'mouse': s['mouse'], 'run': s['run_number'], 'groups': groups,
                     'original_nominal': nominal.tolist(), 'original_outcomes': outcomes.tolist(),
                     'exported_indices': idx.tolist(), 'eligible_indices': np.flatnonzero(eligible).tolist(),
                     'max_same_type_run': max(r['length'] for r in consecutive),
                     'runs_over_three': [r for r in consecutive if r['length'] > 3],
                     'exported_hit_first_lick_under_150ms_indices': early})
    result = {'question': '보존된 전체 시행의 연속 배정 제한과 제외 대응',
              'code_sha256': sha(Path(__file__)),
              'parents': {n: sha(HERE/n) for n in ['rowland_assignment_audit_result.json','rowland_complete_payload_validation.json']},
              'sessions': rows,
              'limits': ['보존된 전체 기록 이전의 누락 여부는 미확인',
                         '연속 제한 일치는 무작위 발생기나 조건부 배정 확률의 증명이 아님',
                         '빠른 핥기 표지는 보존 자료 기준이며 논문 최종 분석의 포함 여부를 뜻하지 않음']}
    save('rowland_trial_history_result.json', result)
    for r in rows:
        print(json.dumps({k:v for k,v in r.items() if k in ['mouse','run','groups','max_same_type_run','runs_over_three','exported_hit_first_lick_under_150ms_indices']}))


if __name__ == '__main__':
    main()
