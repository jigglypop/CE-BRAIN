# R2 사전구현 형식 감사

Status: COMPLETE

Gate: PASS

감사 snapshot은 `contract.md`, `10-sources.md`, `11-math.md`, `12-routes.md`,
`13-dimensionless.md`, parent counterexample/portfolio와 R0/R1 predecessor다.
`report.md`는 아직 `IN_PROGRESS`이므로 결과 판정에는 사용하지 않았다.

| Claim ID | 계약 주장 | 실제 지위 | 근거와 경계 | 판정 |
|---|---|---|---|---|
| R2-C1 | 행동-only $K=4$ chart 정의 | `[공리: 모델 선택]` | `contract.md`의 deterministic train-only partition | 정합 |
| R2-C2 | chart별 tangent/fiber 식 | `[경험식]` | R0/R1 결과 뒤 제안된 interaction pivot | 정합; 독립 예측 아님 |
| R2-C3 | $q_i^{\rm ub}$ 수축 상한 | `[산출: 조건부]` | `11-math.md`의 projector norm 부등식 | 식 정합; biological attraction 아님 |
| R2-C4 | 세 comparator·1%·paired CI gate | `[예측: R2 내부 사전고정]` | R2 endpoint 전 contract freeze | 정합; joint 95% 주장 금지 |
| R2-C5 | tangent angle/distance | `[산출: descriptive diagnostic]` | train-only $U_i$의 projector 계산 | curvature/metric 승격 금지 |
| R2-C6 | R2 PASS의 의미 | `[경험 비교: outcome-informed L2 ceiling]` | 001701은 R0/R1에서 이미 열림 | independent holdout/confirmation 표현 금지 |

## 반례·계보·봉인

R1 positive parent는 `counterexample.json`에서 `RETRACTED`와
`COUNTEREXAMPLE_LOCKED`로 보존됐다. portfolio는 interaction/state/measurement를
각각 바꾸는 세 fingerprint와 adverse control을 갖고 R2를 결과 전에 선택했다.
R2는 global R1의 threshold·seed·endpoint 재시도가 아니다.

DANDI 001701 identity와 hash는 predecessor receipt와 일치한다. DANDI
`001695@0.260319.2023`은 contract, portfolio와 predecessor source 모두에서
`SEALED/UNOPENED`이며 R2 구현·scoring 범위 밖이다. evaluation 재선택 금지와
neural outcome의 chart construction 유입 금지가 명시돼 있다.

## 발견

열린 P0/P1은 없다. 수학 초안의 비수렴 처리, NMSE 분모, shifted support,
transition 방향 모호성 네 건은 결과 접근 전에 계약에서 닫혔다.

P2는 두 건이다.

1. source lane에서 live DANDI API DNS 재조회가 불가능했다. 구현은 download 직후
   exact 12,967,760 bytes와 SHA-256을 다시 검증해야 한다.
2. dimensionless skill이 지목한 `docs/참조/무차원_감사_수학.md`가 현재 tree에 없다.
   route-local normalized-variable check는 통과했지만 이 문서 경로 불일치는 남는다.

## 승인 구현 범위

R2 route 디렉터리 안의 단일 분석기, focused synthetic test, source receipt,
aggregate result와 짧은 implementation/validation/report만 허용한다. predecessor
파일, DANDI 001695, archive 상태, R0/R1 endpoint를 변경하지 않는다. byte/hash,
train-only chart/basis, support, selection-before-evaluation과 temp deletion assertion은
필수다.
