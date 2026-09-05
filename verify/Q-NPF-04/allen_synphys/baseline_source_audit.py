"""고정 소스의 기준선 API와 래퍼 위임 경로를 실행 가능한 최소 예로 점검한다."""
import ast
import json
from pathlib import Path
from reference_spike_audit import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = HERE/'baseline_source_audit_result.json'
paths = {
    'multipatch': HERE/'qc_sources/multipatch_data.py',
    'pipeline': HERE/'qc_sources/dataset_pipeline.py',
    'qc': HERE/'qc_sources/pulse_qc.py',
    'mies': HERE/'qc_sources/miesnwb_pinned.py',
    'data': ROOT/'data/external/analysis_tools/neuroanalysis_source/neuroanalysis/data.py',
}


def audit():
    trees = {k:ast.parse(p.read_text(encoding='utf-8')) for k,p in paths.items()}
    cls = next(n for n in trees['data'].body if isinstance(n,ast.ClassDef) and n.name=='PatchClampRecording')
    methods = {n.name for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert 'baseline_rms_noise' in methods and 'baseline_noise_stdev' not in methods
    qc_attrs = {n.attr for n in ast.walk(trees['qc']) if isinstance(n,ast.Attribute)}
    assert 'baseline_noise_stdev' in qc_attrs
    wrapper = next(n for n in trees['multipatch'].body if isinstance(n,ast.ClassDef) and n.name=='MultiPatchRecording')
    wrapper_methods = {n.name for n in wrapper.body if isinstance(n,ast.FunctionDef)}
    assert {'__getattr__','baseline_regions'} <= wrapper_methods
    assert 'baseline_data' not in wrapper_methods and 'baseline_potential' not in wrapper_methods
    # Execute the unchanged wrapper class AST with a minimal superclass stand-in.
    # This isolates Python delegation; it does not simulate physiology or claim full reader execution.
    namespace = {'MiesRecording':object}
    exec(compile(ast.Module(body=[wrapper],type_ignores=[]),str(paths['multipatch']),'exec'),namespace)
    class Sweep:
        def baseline_regions(self): return [('shared_quiet_start','shared_quiet_stop')]
    class Parent:
        parent = Sweep()
        baseline_regions = [('notebook_start','notebook_stop')]
        @property
        def baseline_data(self): return self.baseline_regions
    wrapped = namespace['MultiPatchRecording'](Parent())
    assert wrapped.baseline_regions == [('shared_quiet_start','shared_quiet_stop')]
    assert wrapped.baseline_data == [('notebook_start','notebook_stop')]
    return {
        'status':'SOURCE_COMPATIBILITY_GAP_CONFIRMED_NOT_BIOLOGICAL_RESULT',
        'source_sha256':{k:sha(p) for k,p in paths.items()},
        'audit_code_sha256':sha(Path(__file__)),
        'noise_api':{'qc_requires':'baseline_noise_stdev','pinned_recording_provides':'baseline_rms_noise',
                     'automatic_alias_applied':False},
        'delegation_fixture':{'wrapper_regions':wrapped.baseline_regions,'delegated_baseline_data':wrapped.baseline_data,
                              'scope':'original wrapper AST with synthetic parent; verifies method binding only'},
        'interpretation':'고정한 두 저장소 판본으로 원 제작자의 전체 QC를 재현했다고 주장할 수 없음. 기존 spike 검출 결과의 반증은 아님.',
        'next_gate':'DB 생성 판본을 확인하거나 별도 호환 계층과 기준선 정의를 명시하고 검증. 원 QC와 재구성 QC를 구분.',
    }


if __name__=='__main__':
    result=json.loads(json.dumps(audit(),ensure_ascii=False))
    if OUTPUT.exists():
        assert result==json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('BASELINE_SOURCE_AUDIT_REPRODUCED')
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream: json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_sha256','audit_code_sha256')},ensure_ascii=False,indent=2))
