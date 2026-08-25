# 복구 경로 선택

Status: COMPLETE

| 경로 | 판정 | 이유 |
|---|---|---|
| R0: 원 predecessor progress를 COMPLETE로 수정 | REJECTED | 실제 terminal 실패 기록을 위조하고 기존 SHA를 파괴한다. |
| R1: 723.56MB raw transaction 재실행 | REJECTED | one-shot prior-artifact 규칙과 terminal journal을 위반한다. |
| R2: `raw_result.json`만 바로 논문 증거로 사용 | REJECTED | COMPLETE authority와 final progress binding이 없다. |
| R3: frozen witness/result의 별도 successor recovery | SELECTED | 원 실패를 보존하면서 동일 validator의 pre/final gate를 다시 충족할 수 있다. |
| R4: 결과 수치나 QC 기준을 수정해 통과 | REJECTED | outcome tuning이며 계약상 추정량 불변 조건을 위반한다. |

선택된 R3는 새 데이터 수집이나 새 endpoint 계산 경로가 아니다. module-safe import로 이미
동결된 validator를 실행하고 별도 receipt를 만드는 최소 transactional recovery다.

