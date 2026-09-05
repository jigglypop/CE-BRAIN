# Q-NPF-04 — 전체 기록 기준선의 복원 경로

작성일: 2026-09-05. 지위: 소스 호환성과 원본 메타데이터 점검. 생물학적 연결의 추가 확증은 아니다. [추가 20개 시행](Q_NPF_04_Allen_IC_추가20시행.md)의 양의 평균 반응을 해석하기 위한 품질 복원 단계다.

## 확인한 차이

고정한 Allen QC와 데이터 파이프라인은 `baseline_noise_stdev`를 요구하지만, 고정한 neuroanalysis `PatchClampRecording`은 `baseline_rms_noise`를 제공한다. 이름을 자동 연결하지 않았다. 두 판본을 조합한 실행을 원 DB 생성 과정의 정확한 재현으로 부를 수 없다는 구체적인 호환성 문제다. 기존의 독립 spike 검출 결과를 반박하는 결과는 아니다.

Allen의 다중 세포 래퍼에는 공통 비자극 구간을 반환하는 속성이 있다. 그러나 다른 속성은 원 기록 객체에 위임한다. 원 래퍼 클래스의 AST를 그대로 실행한 최소 예에서 래퍼의 `baseline_regions`와 위임된 `baseline_data`가 서로 다른 객체의 구간을 사용할 수 있음을 재현했다. 가상 부모 객체로 Python 호출 경로만 검증했으며 실제 reader 전체나 생리 신호를 재현한 시험은 아니다.

따라서 “모든 채널의 자극 후 100ms를 제외한 공통 구간이 곧 기존 계산의 기준선이다”라고 단정할 수 없다. 실제 원 DB 생성 판본은 여전히 미확인이다. 이를 해결하지 않은 전체 QC 통과 주장을 하지 않는다.

## 원본에서 복원한 입력

기존 NWB notebook 캐시에서 시행 32–56번의 두 표적, 총 50건을 읽었다. sweep 유형 기록만 선택하고 같은 시행 안의 마지막 유한 값을 사용했으며, 전 채널 공통 열을 적용했다. 시행 사이 값을 임의로 이어 채우지 않았다. 신규 원본 전송은 0바이트였다.

고정 MIES reader의 notebook 방식으로 얻은 기준선 구간은 시작 후 0.05–0.55초와 기록 종료 전 1초다. 전체 길이는 3.78402·4.15902·4.90902·5.34752·7.28601초로 달라 끝 구간도 달랐다. 같은 프로토콜 이름이라고 전체 시간 구성이 동일한 것은 아니다.

모두 IC 모드였다. 기록된 유지 전류 범위는 양성 표적 −20.06∼5.37pA, 음성 표적 −350.32∼−318.49pA다. 이 값은 실제 기록 메타데이터이며 전압 반응 차이의 원인이나 연결 강도로 해석하지 않는다. bridge 설정도 결과에 보존했지만 접근저항의 독립 측정을 대체하지 않는다.

## 다음 진행 조건

원래 질문인 연결 구조의 신뢰성에는 아직 충분히 답하지 못했다. 이번에 확인한 것은 원 제작자 QC를 곧바로 호출할 수 있다는 전제가 성립하지 않고, 기준선 정의와 판본을 명시해야 한다는 점이다. 연결 자체와 이전 양의 평균 차이는 이 소스 점검으로 반증되지 않았다.

다음 계산은 위 notebook 구간의 전압 분포와 전체 기록의 누락을 확인하는 **명시적 재구성 QC**로 진행할 수 있다. 원 제작자의 공식 QC와 구분하고, 전체 기록을 읽기 전에는 짧은 반응창의 품질을 전체에 대입하지 않는다. 원 판본을 찾으면 그 기준과 별도로 대조한다. 전체 뇌 구조의 완료 판정이나 증거 등급 상승은 하지 않았다.

## 근거와 검증

- [소스 감사 결과](../../verify/Q-NPF-04/allen_synphys/baseline_source_audit_result.json), [실행 가능한 감사](../../verify/Q-NPF-04/allen_synphys/baseline_source_audit.py)
- [기준선 메타데이터 50건](../../verify/Q-NPF-04/allen_synphys/ic_baseline_metadata_result.json), [추출 코드](../../verify/Q-NPF-04/allen_synphys/ic_baseline_metadata.py)
- [Allen 데이터 모델](https://github.com/AllenInstitute/aisynphys/blob/b187927abf1e8df46d11b47eeb88c8e2c76aee3c/aisynphys/data/data.py), [Allen 파이프라인](https://github.com/AllenInstitute/aisynphys/blob/b187927abf1e8df46d11b47eeb88c8e2c76aee3c/aisynphys/pipeline/multipatch/dataset.py)
- [고정 MIES reader](../../verify/Q-NPF-04/allen_synphys/qc_sources/miesnwb_pinned.py), [데이터 원장](../../ledger/data_registry.md): 추가 소스 3개 판본·해시 등록

재현 검사 `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/baseline_source_audit.py` 통과. 검증 범위는 소스 구조와 최소 호출 예이며 생물학적 정확도 검증이 아니다.
