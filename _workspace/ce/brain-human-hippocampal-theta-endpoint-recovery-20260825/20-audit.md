# 복구 preimplementation 감사

Status: COMPLETE

Gate: PASS

Authorization: ENDPOINT_RECOVERY1_ONLY

00/10/11/12는 COMPLETE이고 R3 별도 successor recovery만 허용한다. raw/network,
producer, source loader 실행은 승인하지 않는다.

구현은 predecessor `endpoint_progress.json`, `source_witness.npz`, `raw_result.json`,
`analysis_lock.json`, `execution_lock.json`을 수정·덮어쓰기·복사하지 않아야 한다. terminal
progress의 `IMPLEMENTATION_STOP`, `ENDPOINT_FULL1`, 18 rows, exact import error를 다시
확인하고, 모든 고정 input hash를 recovery analysis lock에 결박해야 한다.

successor에는 recovery 전용 progress와 frozen validator exact schema용 validator progress를
분리한다. validator는 `check_predecessor=True`로 `require_complete=False`와
`require_complete=True` 두 번 모두 통과해야 한다. 두 호출 사이와 final receipt commit 뒤
predecessor artifact를 재해시한다. 실패나 drift가 있으면 `RECOVERY_STOP`으로 끝내고
receipt를 만들지 않는다.

최종 revision 2는 immutable pre-COMPLETE/COMPLETE validator artifact, recursive
type-exact 비교, 두 frozen-validator 재실행, default execution lock only, orphan receipt
거부를 구현했다. executor `e51f4adb69e15a01f88f7948a1641959b7c338550c658340a695663e58b1c98a`,
tests `90759468b8a0542fce65273b4808eb2cbd2d81e595f657fef87b2cef77b7ae74`,
execution lock `0acea44be1fef668430b55fd492255b318127a9f437244d10f9aaf3c073123d1`가
안정 스냅샷이다. 독립 수학·상태·적대 감사는 P0/P1 없이 PASS를 반환했고 focused tests는
`5 passed`였다. 따라서 raw/network/producer 실행 없이 `ENDPOINT_RECOVERY1` 한 번만
승인한다. 성공해도 수치와 claim ceiling은 선행 run과 동일하다.
