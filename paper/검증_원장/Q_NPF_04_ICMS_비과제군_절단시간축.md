# 비과제 ICMS 기록의 절단·연결 시간축

**공개 처리 코드에는 자극 주변을 잘라 이어 붙이는 단계가 있다.** 따라서 NWB의 약 10초 시행 간격을 원실험의 실제 간격으로 해석하면 안 된다. 선택한 네 파일에는 연속 검출 범위를 확인할 원신호나 unit 관측 구간이 없어, 자극 전후 발화 endpoint는 아직 계산하지 않았다.

## 출처와 새로 확인한 점

[파형 감사](Q_NPF_04_ICMS_비과제대조_파형불일치.md)에 이어 보유 저자 코드를 읽었다. `processing/control/stage1_sort.py`는 자극 시작 전후 각 5초를 원래 기록 경계 안에서 잘라 연결하고, 자극 시각을 연결된 시간축으로 옮긴다. 결과를 `condensed_trials.csv`에 저장한 뒤 50Hz 자극 설정으로 전처리한다.

`processing/util/load_control.py`의 MAT 기반 경로에는 영전류 행을 제거하는 코드가 있다. MAT가 없는 대체 경로는 NEV 펄스 간격으로 시행을 구성하고 survey 전류를 배정한다. 따라서 **선택한 NWB에 catch가 없다는 사실과 원실험에 catch가 없었다는 주장은 다르다.** 이전 감사의 파일 내 catch 0개 관측은 유지하되 실험 전체의 부재로 확대하지 않는다.

두 코드의 Git blob을 보유 저자 저장소 트리와 대조했다. `stage1_sort.py`는 CRLF를 LF로 바꾼 비교값이 일치했고, `load_control.py`는 원본 바이트가 일치했다. 로컬 파일 자체는 수정하지 않았으며 원본 SHA-256과 비교 정규화 방식을 결과에 남겼다. 이 일치는 코드 출처의 증거이며 각 NWB의 실제 실행 이력을 증명하지 않는다.

## 기록 범위 확인 결과

네 파일 모두 acquisition 그룹이 비어 있고 `units/obs_intervals`, `intervals/invalid_times`, 이름에 `condensed_trials`가 들어간 경로는 없었다. 첫 자극 묶음 사이 간격 중앙값은 모두 10초였다. ICMS45·54는 모든 간격이 정확히 10초였으며, ICMS48·56은 작은 차이가 있었다. 이는 연결 시간축과 양립하지만 변환 과정의 증명은 아니다.

또한 세션 설명은 비과제 기록이라고 명시하지만 공통 `general/experiment_description`은 행동 훈련을 서술한다. 코호트 구분에는 세션별 설명과 원문의 대조군 정의를 사용하고 공통 설명만으로 이 동물들을 훈련군으로 재분류하지 않는다.

## 판정과 다음 조건

이번 질문은 기록된 자극 전후 창이 실제 검출 가능한 구간인지였다. 원자료 경계·절단 구간·NWB 변환의 연결 정보는 아직 충분히 확인하지 못했다. 발화 최솟값과 최댓값으로 연속 검출을 가정하거나 없는 관측을 발화 0으로 처리하지 않는다. 상태는 `POSTTRAIN_RESPONSE_NOT_EVALUATED_PENDING_OBSERVATION_SUPPORT`, 등급은 입력 감사 `BIO_EVIDENCE_L0`다. 생물학적 반증이나 전체 연구의 중단 판정은 아니다.

다음에는 보유 파일·공식 저장소에서 `condensed_trials.csv`, 원래 구간 길이 또는 NWB 변환 코드를 찾는다. 같은 파일을 다시 받는 것은 이 공백을 해결하지 못한다. 해당 정보가 없으면 이 원신호 재분석 경로의 한계를 명시하고, 저자가 제공한 반응 요약의 정의와 보유 여부를 별도로 점검한다. 전체 뇌 인과 구조는 미확립이다.

## 재현 자료

- [출처 감사 코드](../../verify/Q-NPF-04/allen_synphys/icms_passive_clock_provenance.py)
- [소스 해시·정규화·시간 범위 감사](../../verify/Q-NPF-04/allen_synphys/icms_passive_clock_provenance_result.json)

실행: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/icms_passive_clock_provenance.py`. 저자 소스 대응과 네 파일의 스키마를 확인했다. 신규 다운로드나 기존 봉인 결과 변경은 없었다.
