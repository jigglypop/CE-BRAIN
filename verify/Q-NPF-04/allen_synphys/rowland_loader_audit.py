"""저자 로더의 확인한 단일 메서드만 격리해 라벨 변환을 대조한다."""
import ast
import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from rowland_sessions import read_sessions
from rowland_symbolic_reader import array
from rowland_lick_overlap import scalar
from randi_target_response import save, sha


def main():
    base = Path('data/external/cortical_propagation_2023')
    source = base / 'author_linear_model.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    methods = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'too_sooner']
    assert len(methods) == 1
    scope = {}
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(source), 'exec'), scope)
    method = scope['too_sooner']

    def apply(outcomes, licks):
        session = SimpleNamespace(n_trials=len(outcomes), first_lick=licks, outcome=outcomes.copy())
        with contextlib.redirect_stdout(io.StringIO()):
            method(SimpleNamespace(session=session))
        return session.outcome

    synthetic = np.array(['hit','hit','hit','miss','hit'], dtype='U4')
    assert apply(synthetic, [149,150,None,None,151]).tolist() == ['too_','hit','too_','miss','hit']
    sessions, status = read_sessions(base/'sessions_lite_flu_2022-08-11.pkl')
    assert status['pickle_complete'] and len(sessions) == 11
    rows = []
    for s in sessions:
        outcomes = array(s['outcome'])
        licks = [scalar(v) for v in s['first_lick'].state[4]]
        after = apply(outcomes, licks)
        expected = np.array([o == 'hit' and (v is None or v < 150) for o,v in zip(outcomes,licks)])
        assert np.array_equal(outcomes != after, expected)
        idx, stim = array(s['nonnan_trials']), array(s['photostim'])
        galvo = array(s['galvo_ms'])
        rows.append({'mouse': s['mouse'], 'run': s['run_number'],
                     'changed_original_indices': idx[expected].tolist(),
                     'missing_lick_hit_indices': [int(i) for i,o,v in zip(idx,outcomes,licks) if o=='hit' and v is None],
                     'changed_by_type': {name:int((expected & (stim==code)).sum()) for name,code in [('catch',0),('test',1),('easy',2)]},
                     'changed_eligible_test': int((expected & (stim==1) & np.isfinite(galvo[idx])).sum()),
                     'retained_array_length': len(after), 'output_label': 'too_'})
    result = {'source_sha256': sha(source), 'code_sha256': sha(Path(__file__)),
              'method': 'LinearModel.too_sooner', 'threshold_ms':150,
              'operation': 'outcome label mutation only; no array deletion in this method',
              'sessions': rows,
              'limits': ['전체 로더 실행·논문 최종 분석 재현 아님',
                         '저자 주석의 누락 핥기 원인을 독립 검증하지 않음',
                         '배정 생성 코드는 아직 확보하지 못함']}
    save('rowland_loader_audit_result.json',result)
    print(json.dumps({'sessions': len(rows), 'changed':sum(len(r['changed_original_indices']) for r in rows),
                      'missing_lick_hit':sum(len(r['missing_lick_hit_indices']) for r in rows),
                      'eligible_test':sum(r['changed_eligible_test'] for r in rows)}))


if __name__ == '__main__':
    main()
