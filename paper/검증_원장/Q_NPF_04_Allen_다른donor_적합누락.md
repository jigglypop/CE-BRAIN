# 다른 donor의 pulse별 적합 누락

다른 donor 581866의 pair 116053에서 전체 180개 pulse를 조사했다. 모두 기준선이 있었지만 적합은 IC 44개에만 있었다. IC의 일부 첫 자극·회복 첫 자극은 발화 수가 1이어도 정렬 시각이 없었고, VC는 연결의 전류 파형 파라미터가 없었다. 누락을 무반응이나 연결 부재로 해석할 수 없다.

## 질문과 범위

[다른 donor 첫 반응](Q_NPF_04_Allen_다른donor_첫반응.md)에서 QC 통과인데도 적합이 없는 기록을 발견했다. 뇌 연결 기전을 판별할 실제 분모를 확정하기 위해 같은 pair의 모든 pulse_response를 조회했다. clamp 모드·진폭·QC에 따라 제외하지 않았다.

응답 ID의 유일성, 기준선 기록 외래키, 기존 첫 반응 5개의 ID·기준선·적합 개수를 검사했다. 총 15기록×12pulse=180개이며, 기존 범위 캐시를 재사용하고 196,608바이트를 추가 조회했다.

## 누락의 위치

| 기록 그룹 | pulse 수 | 기준선 있음 | 발화 정렬 시각 있음 | 적합 있음 |
|---|---:|---:|---:|---:|
| VC 20 Hz, 10기록 | 120 | 120 | 120 | 0 |
| IC SRecovery 716321·716323 | 24 | 24 | 24 | 24 |
| IC SRecovery 716325·716327 | 24 | 24 | 20 | 20 |
| IC 20 Hz 716337 | 12 | 12 | 0 | 0 |
| 전체 | 180 | 180 | 164 | 44 |

VC에서는 저장된 synapse의 `psc_rise_time`과 `psc_decay_tau`가 모두 없다. 제작자 적합은 해당 모드의 지연·상승·감쇠와 발화 정렬 시각이 필요하다. IC 20 Hz 기록은 발화 시각이 없고 기록·흥분성 QC도 실패다.

QC를 통과한 IC SRecovery의 누락 4개는 기록 716325와 716327의 pulse_number 0·8, 즉 첫 자극과 회복 첫 자극이다. 모두 `n_spikes=1`이지만 `first_spike_time=NULL`이었다. 발화 후보 개수와 유효한 최대 기울기 시각은 다른 조건이다. 그 밖의 10개 pulse는 각 기록에서 적합을 갖는다.

전체 180행에 대해 기준선·모드별 속도 파라미터·발화 정렬 시각의 보유 조건과 적합 행의 존재를 대조했으며 불일치가 없었다. 이는 검사한 소스의 필요조건과 일관된다는 뜻이고, 과거 작업 로그를 보고 원인을 직접 확정한 것은 아니다. 시각이 누락된 원시 파형의 이유는 아직 확인하지 않았다.

## 판정과 다음 조건

첫 반응이 2개만 계산된 이유를 기록 전체의 적합 실패나 기준선 부족으로 단정하면 잘못이다. 누락이 첫 자극과 회복 첫 자극에 모이므로, 계산 가능한 pulse만 모아 단기 가소성·회복을 추정하면 관측 선택 문제가 생길 수 있다. 이 분석은 입력 적격성과 누락 검사이며 생물학적 증거 등급을 올리지 않는다.

다음에는 해당 4개의 시냅스전 원시 파형을 확인해 발화 시각을 정할 수 없는 이유를 조사한다. 새 검출 규칙을 쓰면 개발 분석으로 명시하고 원래 누락을 덮어쓰지 않는다. 누락된 첫 반응을 후속 pulse로 대체하거나 0으로 채우지 않는다. 전체 뇌 구조와 연결 기전의 독립 확인은 여전히 미완료다.

## 재현 근거

- [전체 조회 계약](../../verify/Q-NPF-04/allen_synphys/different_donor_fit_coverage_contract.json)
- [pulse·기준선·적합 조회 코드](../../verify/Q-NPF-04/allen_synphys/different_donor_fit_coverage.py)
- [180개 기록과 그룹별 분모](../../verify/Q-NPF-04/allen_synphys/different_donor_fit_coverage_result.json)
- [입력 필요조건과 적합 존재 대조](../../verify/Q-NPF-04/allen_synphys/different_donor_fit_eligibility_check.json)
- [제작자 적합 필요조건 코드](../../verify/Q-NPF-04/allen_synphys/source_snapshots/aisynphys__pulse_response_strength.py)

실행: `.codex/hooks/python.cmd python verify/Q-NPF-04/allen_synphys/different_donor_fit_coverage.py`.
