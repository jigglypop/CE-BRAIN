# 다른 개체의 반복 수와 유지 조건

마우스 donor 581866의 pair 116053에는 QC를 통과한 IC 기록이 4개 있지만 회복 간격마다 한 시행뿐이다. VC 기록은 펄스 모양이 같은 10개였으나 유지 전압이 약 −70 mV와 −55 mV로 나뉘므로 **각각 5회 반복**이다. 두 전압 조건을 합쳐 같은 조건 10회로 해석하면 잘못이다.

## 조사와 정정

[명령 기준 후세포 반응](Q_NPF_04_Allen_다른donor_명령기준반응.md)에서 두 IC 시행의 반응을 자극 전 변동과 구분하지 못했다. 남은 반복으로 비교를 개선할 수 있는지 확인하려고 기존 전체 180개 pulse_response, 15개 기록을 조사했다. 진폭·QC에 따라 기록을 제외하지 않았다.

기존 medium DB 범위 캐시만 사용해 추가 다운로드 없이 자극 진폭·길이·시각, 전후세포 기록·모드·QC·유지 상태를 조회했다. 모든 pulse의 기존 필드를 재조회 결과와 정확히 대조했고 전후 기록의 sync_rec·실험·전극을 확인했다. 펄스 길이와 간격은 1 µs로 반올림해 분류하고 원 실수값도 보존했다.

첫 분류 코드에는 모드·펄스 진폭·길이·간격만 넣고 유지 전압을 빠뜨렸다. 원파형 수집 중 DB 기준전압을 확인하자 VC 0~4번과 5~9번 시행이 다른 조건이었다. 전류 결과에 따른 분할이 아니라 유지조건의 누락을 바로잡은 것이다. 원 분류를 보존하고 [유지조건 포함 분류](../../verify/Q-NPF-04/allen_synphys/different_donor_holding_groups_inventory.json)로 해석을 대체한다. VC에는 전후 baseline_potential, IC에는 전후 baseline_current를 조건 키에 추가했다.

## 조건별 분모

| 후세포 모드 | 시행 | 펄스 간격 | 8→9 시작 간격 | 유지 전압, VC | 기록 수 | 전후 기록 QC 통과 |
|---|---|---:|---:|---:|---:|---:|
| VC | 0~4 | 50 ms | 251.505 ms | 약 −70 mV | 5 | 5 |
| VC | 5~9 | 50 ms | 251.505 ms | 약 −55 mV | 5 | 5 |
| IC | 30 | 20 ms | 126.505 ms | 해당 없음 | 1 | 1 |
| IC | 31 | 20 ms | 251.505 ms | 해당 없음 | 1 | 1 |
| IC | 32 | 20 ms | 501.505 ms | 해당 없음 | 1 | 1 |
| IC | 33 | 20 ms | 1001.505 ms | 해당 없음 | 1 | 1 |
| IC | 35 | 50 ms | 253.020 ms | 해당 없음 | 1 | 0 |

모든 기록은 12개 자극이다. VC에서는 전세포도 VC였고 약 60 mV, 1.505 ms의 자극을 사용했다. IC 30~33은 전세포도 IC이며 약 1.118 nA, 1.505 ms 자극이었다. IC 35는 약 1 nA, 앞 8개 3.020 ms·뒤 4개 3.000 ms로 다른 조건이며 발화 후보 수와 QC도 실패했다.

VC 120개는 흥분성 반응 QC, 단일 발화 후보, 발화 정렬 시각을 모두 갖췄다. IC 30·31도 각 12개 정렬 시각이 있고, IC 32·33은 각각 10개만 있다. IC 35는 0개다. 원자료의 QC 통과는 독립 발화 정답이나 측정모형의 인과적 적격성을 보증하지 않는다.

유지 전압 조건이 같아도 시간에 따른 상태 변화는 남는다. VC 후세포의 DB 기준 전류는 시행 0~4에서 약 −227~−360 pA, 시행 5~9에서 약 −262~−457 pA였다. 따라서 두 그룹 간 전류 차이를 유지 전압만의 효과로 해석하지 않는다. 여기의 유지 전압은 DB baseline_potential이며 독립적으로 교정한 막전압이 아니다.

## 다음 단계의 범위

IC 회복 조건별 반복은 하나뿐이므로 같은 조건의 반복으로 회복 변동을 추정할 수 없다. 초기 8개 자극은 공통 형태지만 뒤 조건이 달라진 기록들을 회복 반복으로 세지 않는다. 남은 IC 두 기록의 창을 조정해 기존 불분명한 결과를 구제하지 않는다.

VC는 각 전압 조건의 5회 반복에서 원전류를 기술할 수 있다. 제작자 PSC 파라미터가 없다는 사실은 원전류까지 없다는 뜻이 아니다. 단, 전류 단위·발화 기준 창·대조를 별도로 고정하고 전압 조건을 분리해야 한다. IC 전압 측정과 합치지 않는다. 이 조건 재고는 `BIO_EVIDENCE_L0`이며 전체 뇌 구조나 인과기전의 확인은 아니다.

## 근거

- [전체 조회 절차](../../verify/Q-NPF-04/allen_synphys/different_donor_protocol_repeats_contract.json)
- [조회·분류 코드](../../verify/Q-NPF-04/allen_synphys/different_donor_protocol_repeats.py)
- [원조건·QC·유지 상태](../../verify/Q-NPF-04/allen_synphys/different_donor_protocol_repeats_result.json)
- [유지조건 정정 절차](../../verify/Q-NPF-04/allen_synphys/different_donor_holding_groups_contract.json)
- [정정 분류 코드](../../verify/Q-NPF-04/allen_synphys/different_donor_holding_groups.py)

오프라인 분류 확인: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/different_donor_protocol_repeats.py --verify`. 원 분류의 재현 통과가 유지 전압 누락을 정당화하지는 않는다. 최종 해석은 유지조건 포함 분류를 따른다.
