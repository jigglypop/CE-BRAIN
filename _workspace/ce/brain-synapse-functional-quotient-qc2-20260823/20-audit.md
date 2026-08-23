# BA-SRM3 pre-support audit

Date: 2026-08-23

Status: COMPLETE

Gate: PASS

Scientific verdict: `INVALIDATED_CLAMP_UNIT_CONTRACT / NO_BIOLOGICAL_EVIDENCE`

## 확인된 경계

- BA-SRM2 STOP은 보존했다.
- BA-SRM3는 별도 candidate와 별도 directory를 사용한다.
- train manifest를 재생성하거나 재표집하지 않는다.
- source correction은 official dynamics의 sign-matched response QC로 한정했다.
- 이미 본 train 집계는 contract에 공개했다.
- response-QC∩complete-target support, target MAD와 모델 score는 아직 계산하지 않았다.
- development와 confirmation은 봉인돼 있다.

## P0/P1

P0: 0.

P1은 모두 향후 empirical gate다: support 수, target scale, input rank, covariance condition,
KRR selection, local rank stability, gauge, missingness sensitivity와 controls. 이 항목이 아직
미측정이라는 사실은 실행을 허용하지만 성공 주장을 허용하지 않는다.

## 종료 감사

후속 단위 감사에서 presynaptic clamp mode가 IC와 VC로 섞였는데 extractor가 mode를
좌표에 보존하지 않은 P0 측정계약 결함이 확인됐다. 이는 rank가 작다는 경험적 결론도,
무한차원 가설이 실패했다는 결론도 허용하지 않는다. 기존 operator·rank·covariance와
score는 해석 대상에서 제외한다. development와 confirmation은 열리지 않았으므로 새
mode-aware 계약에서 사용할 수 있다. 새 계약은 데이터 분할, 식 발견 grammar, 모델 선택,
최종 test를 결과 전에 다시 고정해야 한다.
