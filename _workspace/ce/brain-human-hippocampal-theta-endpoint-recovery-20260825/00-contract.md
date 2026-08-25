# 인간 해마 iEEG endpoint 무다운로드 복구 계약

Status: COMPLETE

Mode: light successor, transaction-authority recovery only

PREDECESSOR: `_workspace/ce/brain-human-hippocampal-theta-full-endpoint-20260825`

## 질문과 범위

선행 `ENDPOINT_FULL1`은 18/18 version-pinned OpenNeuro 객체 723,560,000 bytes를 모두
검증하고 `source_witness.npz`와 `raw_result.json`을 원자적으로 기록했지만, producer가
독립 validator를 package import하는 마지막 단계에서 `ModuleNotFoundError: No module
named 'examples'`로 종료됐다. 원 progress의 `IMPLEMENTATION_STOP`은 수정하거나
성공으로 재분류하지 않는다.

이 successor의 유일한 질문은 고정된 선행 witness와 result를 네트워크·raw 재실행 없이
동일한 독립 validator로 pre-COMPLETE와 COMPLETE 상태에서 다시 검증하여 별도 복구
receipt를 만들 수 있는가이다. endpoint 정의, QC, 포함 대상, reference, estimand,
window, bootstrap seed/draw, LOO, paired 계산과 수치 결과는 변경하지 않는다.

## 고정 입력

| 입력 | SHA-256 | 요구 상태 |
|---|---|---|
| predecessor analysis lock | `a55e605fec8a8e84bf783dcec7ad853315207f6633b783c55ca2921d9c62d431` | exact |
| predecessor execution lock | `aefbec437279519bd568e77ffc0f5a01b1795b24843acb178abfdc9a1f57aa6b` | exact |
| selected-trace witness | `2a5a9328cab95f6a484a76af5c7e34deccbace52a9eb5a00241ee08f0d2e58ae` | 36 arrays, 18 objects |
| raw result | `cd3aaff53b1db1dba97f92812f529f066c870ac968bdd7a27f0b9ad4c0a8585d` | `RAW_COMPLETE`, 18 records/files |
| terminal predecessor progress | `2a1f1e3a4730c04b3d79426d592c4b3c071fe4088c2953b2afa87dfefe11ae90` | `IMPLEMENTATION_STOP`, 18 rows, exact import error |
| producer | `cfe53970f2d88473c946eb20feb1976fe5926f108899ace5cc88d36f4ca065e8` | read-only provenance |
| independent validator | `40e78a2491c371fb638f21e19ea6e8ff2caff414010c409a7a7475f54a432197` | execution authority |
| focused tests | `2142131018ccbd6ad7653229dcac0345bba31326a816b6186c93152f67a326d2` | predecessor evidence |

## 거래 `ENDPOINT_RECOVERY1`

1. 선행 progress·witness·result·두 lock·validator의 경로와 SHA를 exact 확인한다.
2. 선행 progress가 `IMPLEMENTATION_STOP`, attempt `ENDPOINT_FULL1`, 18 completed rows,
   exact `ModuleNotFoundError: No module named 'examples'`인지 확인한다.
3. 선행 result의 18 records를 그대로 담은 별도 `recovery_progress.json`을
   `IN_PROGRESS`, attempt `ENDPOINT_FULL1`로 원자 기록한다.
4. frozen validator를 module-safe 경로로 불러 `require_complete=False`로 선행
   result/witness와 새 progress를 검증한다.
5. 새 progress를 `COMPLETE`로 바꾸고 선행 witness/result SHA를 결박한 뒤
   `require_complete=True` 검증을 수행한다.
6. 두 검증이 모두 참일 때만 `recovery_receipt.json`을 원자 기록하고 readback한다.

기존 선행 artifact는 어느 것도 수정하지 않는다. prior recovery progress 또는 receipt가
있으면 재실행하지 않는다. 네트워크와 원자료 loader는 호출하지 않는다. validator용
progress에는 validator exact schema 밖의 recovery metadata를 넣지 않는다.

## 종료·반증 조건

입력 SHA, terminal status/error/18 rows, source identity metadata, witness manifest,
QC mask/reason, endpoint leaf, aggregate leaf, execution lock, progress/result hash 중 하나라도
다르거나 두 validator 호출 중 하나라도 거짓이면 `RECOVERY_STOP`으로 끝내며 권위 receipt를
만들지 않는다. 수치가 불리한 것은 실패 조건이 아니다.

성공 authority는 선행 `raw_result.json` + 선행 `source_witness.npz` + 새
`recovery_progress.json` + 새 `recovery_receipt.json`의 결합이다. 원 선행 progress는
계속 `IMPLEMENTATION_STOP`이고 독립적인 실패 기록으로 보존된다.

## 주장 상한

성공해도 동일 공개자료의 7명 epilepsy-surgery participant에 대한 post-hoc descriptive,
author-intended technical endpoint일 뿐이다. exact MATLAB/FieldTrip/`fitlme` replication,
독립 표본 확인, causal stimulation effect, 일반 인구 추론, 기억·의식·CE·AGI 증거가
아니다. raw-to-witness가 단일 frozen decoder라는 provenance P2도 유지된다.
