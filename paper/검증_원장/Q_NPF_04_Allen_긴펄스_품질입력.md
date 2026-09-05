# 긴 펄스 품질 입력과 기준선 복원 한계

긴 펄스 24기록에서 holding과 bridge 보정 설정을 확인했다. 그러나 앞선 반복 자극에 사용한 notebook 지연 기반 기준선 복원법은 이 프로토콜에서 빈 구간을 반환했다. 검사 통과 0/24는 이 복원법으로 품질을 판정하지 못했다는 결과이며, 모든 파형이 불량하거나 발화 후보가 무효라는 결론이 아니다.

## 확인한 메타데이터

같은 sweep의 `EntrySourceType=0` 행에서 마지막 유한값을 취하고 global 열을 적용했다. sweep 사이 값을 이월하지 않았다. 다음 값은 전극별로 시행 82–89 동안 동일했다.

| 전극 | 기존 세포 번호 | I-Clamp holding level(pA) | Bridge Bal Value(저장 숫자) |
|---|---|---:|---:|
| 2 | 3 | −362.564 | 16.910866 |
| 4 | 5 | +1.165 | 18.437118 |
| 5 | 6 | −48.373 | 14.713065 |

24기록 모두 clamp mode는 1, holding enable과 bridge enable은 1이었다. Bridge 값의 단위와 실제 적용식은 이번 점검에서 확정하지 않았다. `Series Resistance` 저장값은 모두 0이었지만 실제 접근저항이 0이라는 뜻으로 해석하지 않는다. 같은 source type에서 `TP Peak Resistance`, `TP Steady State Resistance`, `USER_F Rheo E Sweep QC` 값은 모두 결측이었다. 다른 notebook 행 유형에도 없다는 뜻은 아니다.

따라서 [저장 명령](Q_NPF_04_Allen_긴펄스_실제명령.md)이 자극 밖에서 0이라는 사실을 전체 주입 전류가 0이라는 사실로 바꾸면 안 된다. holding과 저장 DA 명령을 제작자가 어떻게 합성하는지 확인해야 한다. 임의로 holding을 더하거나 빼서 역치를 보정하지 않았다.

## 기준선이 비어 있었던 이유

`Delay onset auto`, `Delay onset user`, `Delay termination`이 모두 0이었다. 기존 반복 자극 검사에서 쓴 지연 기반 영역 정의를 그대로 적용하면 기준선 표본이 없다. 결과 JSON의 `baseline_voltage`, `baseline_noise` 실패 항목은 값이 범위를 벗어났기 때문이 아니라 기준선 값이 `None`이기 때문에 발생했다.

24개 파형의 유한성·0 표본 비율·clamp·holding 범위에서는 별도 실패가 없었다. 다만 이것만으로 전체 QC를 통과했다고 할 수 없다. 원본에 자극 전후 데이터는 존재하므로 제작자의 긴 펄스 기준선 선택 경로를 확인할 여지는 남아 있다. 결과를 통과시키려고 임의의 조용한 구간을 선택하지 않는다.

## 구현과 판정

첫 실행은 HDF5 열 인덱스가 오름차순이어야 한다는 제약에서 중단됐다. 원 코드와 계약을 보존하고, 열을 정렬해 읽은 뒤 메모리에서 요청 순서로 되돌리는 별도 코드를 실행했다. 품질 문턱·대상 파형·메타데이터 의미는 바꾸지 않았다. 재실행의 신규 다운로드는 0바이트였다.

발화 후보 결과는 유지하되 품질 확인된 역치나 내재 이득으로 승격하지 않는다. 다음에는 제작자 `MiesRecording`의 command/holding 합성, 긴 펄스 baseline 계산 및 `qc_recordings` 경로를 확인한다. 같은 상태의 연결 반응과 결합하려면 시간적 세포 대응도 여전히 필요하다.

## 근거

- [완료한 계약](../../verify/Q-NPF-04/allen_synphys/long_pulse_recording_qc_ordered_contract.json)
- [열 순서를 수정한 코드](../../verify/Q-NPF-04/allen_synphys/long_pulse_recording_qc_ordered.py)
- [24기록의 설정·결측·판정](../../verify/Q-NPF-04/allen_synphys/long_pulse_recording_qc_ordered_result.json)
- [보존한 최초 코드](../../verify/Q-NPF-04/allen_synphys/long_pulse_recording_qc.py)

완료 계약 SHA-256: `2a5314bc53802db3919370f4451b5c0081eaa7c9acdf2f01abb822932175b2ed`.
