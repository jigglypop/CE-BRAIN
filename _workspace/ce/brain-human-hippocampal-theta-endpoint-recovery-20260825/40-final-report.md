# 인간 해마 iEEG 재분석 run 인계

Status: IN_PROGRESS

DOCS_PAPER: docs/6_뇌/06_인간해마_세타자극_iEEG_재분석/00_논문목차.md

## 현재 결론

version-pinned 실제 인간 iEEG 원자료 18개, 723,560,000바이트의 지정 끝점 계산과
복구 검증은 완료됐다. 임상 기준전극의 시행별 평균 후기 대비는
$33.643\ \mu\mathrm V$였지만 인접 양극성 기준전극에서는
$2.532\ \mu\mathrm V$였다. 따라서 현재 보존되는 결론은 기준전극에 민감한
기술적 관측이며, 국소 해마 발생원·인과 효과·CE·AGI의 증명이 아니다.

## 증거 경로

- 수치 원장: `35-result-ledger.md`
- 전수 끝점 표: `artifacts/endpoint_summary.csv`
- 원자료 복구 영수증: `artifacts/recovery_receipt.json`
- 완료 검증 witness: `artifacts/validator_complete.json`

## 활성 epoch 통합

- 반례: `reference-sensitive-local-source`
- 선택 경로: `montage-decomposition`
- 계약: `artifacts/epochs/reference-sensitive-local-source/pivots/montage-decomposition/contract.md`
- 결과: `artifacts/epochs/reference-sensitive-local-source/pivots/montage-decomposition/report.md`
- 상태: 원자료 관측연산자 계산 구현 수정·검증 중

계산이 끝나면 결과의 부호와 무관하게 위 목차의 제5장과 제6장에 통합하고 이
인계 상태를 갱신한다. 논문 본문은 이 run에 복제하지 않는다.
