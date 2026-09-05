"""확보한 생성 소스의 기저선·아티팩트 변환만 합성 배열로 확인한다."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from randi_target_response import HERE,save,sha


def main():
    source=Path('data/external/cortical_propagation_2023/vape_interareal_analysis.py')
    tree=ast.parse(source.read_text(encoding='utf-8'))
    methods={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}
    node=methods['_baselineFluTrial']
    scope={'np':np}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope)
    original=np.array([[2.,4.,90.,91.,10.,12.],[1.,3.,70.,71.,8.,9.]])
    before=original.copy()
    result=scope['_baselineFluTrial'](SimpleNamespace(pre_frames=2),original,4)
    assert np.array_equal(original,before)
    assert np.allclose(result[:,:2].mean(axis=1),0)
    assert np.array_equal(result[:,2:4],np.zeros((2,2)))
    assert np.allclose(result[:,4:],[[7,9],[6,7]])
    save('mechanisms_preprocessing_audit_result.json',{
        'source_sha256':sha(source),'code_sha256':sha(Path(__file__)),
        'synthetic_baseline_and_zero_fill_pass':True,
        'method_lines':{n:[methods[n].lineno,methods[n].end_lineno] for n in ['addShamPhotostim','_baselineFluTrial','_makeFluTrials']},
        'required_payload_checks':['실제 sham 획득 여부를 원래 파일·메타데이터로 대조',
                                   '복사된 시각·표적의 일치를 독립 대조 증거로 쓰지 않음',
                                   '프레임 축·pre_frames·duration_frames·아티팩트 구간 확인',
                                   '불완전 시행 제거 전후 시각과 배열 인덱스 대응 확인'],
        'limits':['확보한 소스 판본의 구현 확인이며 역사적 실행 증명 아님',
                  'RL127 전체 파일의 구조·생물학적 반응은 미검증']})
    print('Synthetic preprocessing check PASS; session audit pending')


if __name__=='__main__':main()
