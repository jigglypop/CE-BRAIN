# 20 kHz 제작자 입력 후보 복원

보유 원시 표적 전압에서 240개 응답 구간과 240개 기준선 구간을 20 kHz로 복원했다. 응답 배열은 600 또는 1,000표본, 기준선은 400표본이다. 이는 확인한 코드 규칙에 따른 후보 입력이며 과거 DB 배열과 동일하다고 검증된 입력은 아니다.

## 규칙과 판본

[제작자 정렬 검사](Q_NPF_04_Allen_제작자정렬_배열범위.md)에서 확인한 DB 추출 시작·기준선 시작과 기존 전체 표적 전압을 사용했다. 제작자 스키마 사본의 표본률은 20 kHz다. 응답은 DB 시작부터 최대 50 ms, 다음 pulse가 먼저 오면 그 시작까지로 잘랐다. 보유 `TSeries`의 시간 절단과 2차 Bessel 저역통과 후 선형 보간을 사용했다.

기준선 길이에는 판본 한계가 있다. 기존 검출기용 campagnola/neuroanalysis `bbe61c4`의 해당 경로에서 기준선 분배 코드를 찾지 못했다. 별도 [Allen neuroanalysis 코드](https://raw.githubusercontent.com/AllenInstitute/neuroanalysis/9711704cb4ecfab82905a88c4f96e10587a11fa6/neuroanalysis/analyzers/baseline.py)의 `baseline_chunks` 기본 길이 20 ms를 확인해 사용했다. 이 판본이 과거 DB 제작 의존성과 같다는 증거는 없다. 기존 검출기 패키지를 교체하거나 수정하지 않았다.

따라서 복원 계약에 서로 다른 판본의 조합을 명시했다. 20 ms 기준선과 표본 처리 방식은 검증할 후보이며, 현재 DB에 배열이 없다는 사실을 동일성의 근거로 삼지 않는다.

## 실행 결과

| 항목 | 결과 |
|---|---|
| 응답 구간 | 240개, 30 또는 50 ms |
| 기준선 후보 구간 | 240개, 20 ms |
| 출력 표본률 | 전부 20 kHz |
| 배열 크기 | 응답 600/1,000, 기준선 400표본 |
| 압축 배열 파일 | 1,732,359바이트 |
| 원시 데이터 신규 다운로드 | 0바이트 |

원래 표적 배열의 해시, 모든 창의 범위, 출력 유한값과 표본률을 검사했다. 상수 전압의 재표본화 오차는 1e-10 V 미만임을 확인했다. 이는 필터 전체의 정확성이나 생물 파형의 보존을 독립적으로 증명하는 검사는 아니다.

## 판정과 다음 조건

제작자 적합과 비교할 후보 입력이 준비됐다. 소스·배열 복원 단계이므로 생물학적 증거 등급은 올리지 않는다. 과거 환경 재현과 적합값 일치는 미확인이다.

다음에는 동일한 템플릿·역필터링·정렬 정의로 적합값을 계산해 저장된 결과와 수치 비교한다. 일치하지 않으면 판본·절단·기준선·필터 차이를 기록하며 매개변수 조정으로 맞추지 않는다. 기존 DB 적합값을 학습·검증 양쪽의 독립 정답처럼 쓰지 않는다. 뇌 전체 구조와 통합 기전은 여전히 미확립이다.

## 재현 근거

- [후보 복원 계약](../../verify/Q-NPF-04/allen_synphys/producer_input_reconstruction_contract.json)
- [구간 추출·재표본화 코드](../../verify/Q-NPF-04/allen_synphys/producer_input_reconstruction.py)
- [480개 배열 위치·표본수·해시](../../verify/Q-NPF-04/allen_synphys/producer_input_reconstruction_result.json)
- [기준선 코드 사본](../../verify/Q-NPF-04/allen_synphys/source_snapshots/neuroanalysis_allen__baseline_distributor.py)
- [기준선 출처 판본](../../verify/Q-NPF-04/allen_synphys/source_snapshots/neuroanalysis_allen__baseline_distributor.json)

실행: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/producer_input_reconstruction.py`.
