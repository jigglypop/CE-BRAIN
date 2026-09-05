# Allen VC 평균의 원파형 재현

## 질문과 판정

신경 연결을 추론하기 전에 평균 반응의 측정 경로를 신뢰할 수 있는지 확인했다. 기존 선택 분모 검사 다음으로, mouse VisP L5의 donor593646, pair121538에서 제작자 저장 VC 평균을 보유 원파형으로 재구성했다. 두 전압 조건 모두 고정한 수치 일치 기준을 통과했다. 이는 **L0 측정 경로 재현**이며 연결의 인과성이나 CE 통합 사슬의 증거 등급을 올리지 않는다.

## 자료와 방법

Allen SynPhys r2.1의 기존 DB·NWB 캐시를 재사용했다. [이전 선택 분모](../../verify/Q-NPF-04/allen_synphys/producer_average_membership_result.json)의 후보를 각 조건 60개씩 모두 사용했다. 이번 성공 실행의 새 다운로드는 0바이트다. [원장](../../ledger/data_registry.md)에 출처와 보유 위치를 관리한다.

명령 시작 10 ms 전부터 최대 50 ms 또는 다음 명령 시작까지 절단하고 20 kHz로 변환했다. 공개 제작자 `PulseResponseList` 클래스의 기준선 처리와 발화 정렬을 그대로 실행한 뒤 `TSeriesList.mean()`으로 평균했다. 기준선은 명령 전 최대 5 ms의 histogram mode다. 비교를 맞추기 위한 추가 이동이나 기준선 보정은 하지 않았다.

기준은 분모·배열 길이 일치, 시작시각 차이 1e-12초 이하, 모든 샘플에서 절대 허용오차 1e-14 A와 상대 허용오차 1e-3이다. [고정 계약](../../verify/Q-NPF-04/allen_synphys/producer_vc_average_reconstruction_v2_contract.json)과 [실행 코드](../../verify/Q-NPF-04/allen_synphys/producer_vc_average_reconstruction_v2.py)에 입력 해시·규칙을 남겼다. 사용한 공개 소스와 과거 실제 제작 환경의 동일성은 확인하지 못했다.

## 결과

| 유지 전압 | 반응 수 | 평균 샘플 수 | 시작시각 (초, 발화 기준) | 최대 절대 오차 (pA) | 통과 샘플 |
|---|---:|---:|---:|---:|---:|
| −70 mV | 60 | 997 | −0.010450 | 6.856e-8 | 997/997 |
| −55 mV | 60 | 1000 | −0.010250 | 2.292e-7 | 1000/1000 |

두 조건 모두 개별 절단의 시작시각도 DB 값과 일치했다. [결과 영수증](../../verify/Q-NPF-04/allen_synphys/producer_vc_average_reconstruction_v2_result.json)에 120개 반응 ID, 시각, 배열 해시와 오차를 기록했다. 오프라인 재실행에서 결과와 배열이 같음을 확인했다.

첫 구현은 NWB 세션 기준 시작시각을 시행 내부 자극 시각과 혼용해 첫 절단에서 빈 배열 오류로 종료했다. 평균 비교에 도달하지 않았다. [실패 기록](../../verify/Q-NPF-04/allen_synphys/producer_vc_average_reconstruction_failure.json)과 원 코드·계약을 보존했다. 수정 판본은 시행 시작을 0초로 두며 비교 기준은 유지했다.

## 해석과 다음 진행 조건

원래 질문인 두 VC 평균의 재현 여부에는 답했다. 현재 고정 소스 경로로 해당 평균을 수치적으로 재현할 수 있다는 증거가 생겼다. 이 결과는 과거 환경의 모든 처리나 개별 반응의 역사적 선택을 유일하게 증명하지 않는다.

제작자 평균 자체는 독립적인 연결 정답이 아니다. −70 mV 평균의 저장 QC 실패와 −55 mV 평균의 저장 QC 통과도 이번 수치 일치로 변경되지 않는다. 앞서 실패한 대조구간 기반 연결 분류 기준 역시 복구되지 않는다.

다음은 같은 입력 위에서 고정 짧은 구간 평균과 제작자 파형 적합 진폭이 서로 무엇을 측정하는지 구분하는 것이다. 적합의 수동 지연·부호 조건과 QC를 먼저 명시해야 하며, 적합 성공을 독립 연결 발견으로 세면 안 된다. 독립 구조·개입 정답과 동일 단위의 통합 인과사슬은 여전히 미확립이다.

검증 명령: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/producer_vc_average_reconstruction_v2.py --verify`.
