# BA-OBS-DISC2R 실제 뇌 D0 사전 상태 감사

Status: COMPLETE

## 판정

`PASS_TO_OPEN_D0_AFTER_RECEIPT_SEAL`.

독립 read-only 감사자는 retry run-lock
`d70f83387143145bb1c40258c1f1a3974c168c30c677d2f67cc5819ffdccd291`을
직접 검증했다. 최초 형식 판정은 `STOP`이었으나, 이는 과학·수학·구현 결함이
아니라 runner가 요구하는 `preimplementation-audit-receipt.json`이 아직 없었기
때문이다. 이 문서와 그 영수증은 감사 결과만 봉인하며 잠긴 과학 입력을
변경하지 않는다.

## 감사 범위와 결과

| 항목 | 독립 판정 |
|---|---|
| retry run-lock | 지정 SHA 일치 및 잠긴 파일 검증 통과 |
| 상속된 과학 입력 | predecessor의 source/split manifest, fixture, 모델, raw-range 규약, 전압 endpoint를 해시로 고정하여 그대로 상속 |
| 변경 범위 | `event_sample_crosswalk`를 event lookup이 아니라 record-level sample-delta histogram으로 해석하는 linkage 교정 하나뿐 |
| linkage 의미론 | metadata generator가 만드는 `{"0": electrical_event_count}`와 일치 |
| sealed trial 일치 | 74 participants, 592 sources, 5,920 selected trials 전부에서 event index, zero-based anchor, orientation 및 자극 metadata 일치 |
| 변조 방어 | histogram 변조와 anchor `+1` 변조를 raw range 이전에 거부 |
| 집중 테스트 | `3/3 PASS` |
| predecessor 실패 위치 | `_ordered_trials()` 내부이며 `fetch_trial`과 HTTP range 요청보다 앞 |
| predecessor endpoint 상태 | range receipt, endpoint, endpoint receipt, D0 result가 모두 없음 |
| retry endpoint 상태 | D0 marker, endpoint, result, failure가 모두 없음 |
| wrapper 경계 | mutable stage state만 retry root로 돌리고, scientific manifest와 numerical implementation은 predecessor hash로 고정 |

## 형식 지위

- `[검증 산출]` 링크 교정판은 실제 raw voltage를 읽기 전의 provenance·수치·단계
  장벽을 통과했다.
- `[검증 산출]` 본 receipt가 봉인되면 허용되는 다음 동작은 D0 apparatus open
  하나뿐이다.
- `[미완성]` 실제 CCEP 전압 endpoint와 모델 적합 결과는 아직 생성되지 않았다.
- `[주장 제한]` 이후 성공하더라도 결론은 held-out human SPES CCEP의 관측-kernel
  예측에 한정한다. 생물학적 리만 계량, 무한차원 상태공간, 의식·자아·해마·AGI를
  직접 검증했다고 승격하지 않는다.

## 독립 감사자의 절차 STOP 해소

독립 감사자의 substantive 판정에는 P0 또는 P1 결함이 없었다. 유일한 차단은
`PREIMPLEMENTATION_AUDIT_MISSING`이었다. 따라서 이 감사 문서를 해시한
`preimplementation-audit-receipt.json`을 생성하면 바로 그 누락만 닫히며,
run-lock 또는 잠긴 입력은 다시 쓰지 않는다.
