# BA-SRM8 대안 경로 — 많은 식을 빠르게 죽이되 final을 보존하는 법

Status: COMPLETE

Date: 2026-08-23

## 1. 경로 판정

| 경로 | 판정 | 이유ㆍfalsifier |
|---|---|---|
| original clock + nonnegative physical-time weighted covariance | **SELECTED** | PSDㆍcausal 증명 가능; irregular gap을 soft elapsed-time decay로 처리 |
| BA-SRM7 retained-index hard 60-window | MATCHED CONTROL | source-rooted unit은 남겼지만 네 recording anchor gate 실패 |
| majority-bad frame의 선형 interpolation | REJECTED PRIMARY | 긴 결측에 분석자가 신호를 만들어 넣고 uncertainty를 숨김 |
| pairwise-complete covariance | REJECTED | 일반적으로 non-PSD라 resolvent core 정의역을 깨뜨림 |
| learned neural kernel/transformer search | DEFERRED | 22 recording에서 자유도가 너무 크고 10% selection을 빠르게 소모함 |
| Gaussian-process imputation | DEFERRED | uncertainty model 자체의 별도 계약과 큰 계산비가 필요 |
| fixed rank 4 | CONTROL ONLY | 숫자 4의 독립 근거가 없으며 연속 차원 질문을 선취함 |
| lagged directed dynamics | SEPARATE ROUTE | edge/loop를 논하려면 covariance가 아닌 interventionㆍdirected model이 필요 |

선택 경로는 published preprocessing 재현이 아니라 raw/source provenance에 뿌리를 둔
분석자 successor다.

## 2. 첫 wave의 48개 식

무제한 symbolic search 대신 하나의 식 grammar를 완전히 열거한다.

- memory 8개: EXP 2, BIEXP 2, POWER 2, COMPACT 2;
- quality 2개: $q$, $q^2$;
- robustness 3개: identity, radial Huber, radial tanh.

곱집합은 정확히 48개다. resolvent $\lambda=1$, feature 네 개, target과 ridge grid는
공통으로 고정한다. spectral functional까지 동시에 바꾸지 않는 이유는 memoryㆍmaskㆍ
robustness 중 무엇이 성능을 만든 것인지 분해하기 위해서다. 48개가 모두 apparatus에서
실패하면 participation ratio나 entropy rank를 끼워 넣어 부활시키지 않고 별도 successor
wave를 연다.

COMPACT $L=4$나 EXP $\theta=2$처럼 $n_{\rm eff}\ge8$을 구조적으로 못 넘는 식은 real
behavior 전에 즉시 제거될 가능성이 있다. 이것이 이 funnel의 의도다.

## 3. 비용 사다리

```text
48 formula
  └─ F0 property/runtime
      └─ F1-v6 micro synthetic → 최대 32
          └─ F2-A (8 seeds) → 최대 24
              └─ F2-B (8 seeds) → 최대 20
                  └─ F2-C (8 seeds) → 최대 16
                      └─ F2-D (8 seeds, no cap) → independent 32-seed confirmation
                          └─ F2R behavior-blind real background → 최대 8
                  └─ SMALL 2% → 최대 4
                      └─ MID 3% → 최대 2
                          └─ LARGE-A 2.5% → champion 1
                              └─ LARGE-B 2.5% → champion 재확인
                                  └─ FINAL 20% → PASS/FAIL one-shot
```

정적 반례와 작은 synthetic은 candidate별 첫 failure에서 중단한다. F1-v2의 full-$T$
standardization은 promotion-invalid P0이고 v3/v4/v5는 superseded다. self-contained F1-v6 receipt가 현재 promotion source다. F2는
8-seed screen 네 번으로 32→24→20→16을 만들며, 16 이하만 독립 32-seed full-panel confirmation을
받는다. MISS50은 gate/순위에 넣지 않는 descriptive stress다. expensive feature, control과 bootstrap은 survivor에만 계산한다. preprocessing과 standardized neural trace는
공유 cache를 쓰고, formula hashㆍdata hashㆍsplit hash가 모두 같을 때만 cache hit를
허용한다.

## 4. 상태의 의미

| 상태 | 의미 | 같은 run에서 재개 |
|---|---|---|
| `INVALID_KILL` | noncausal, non-PSD, dimensionless 위반, fail-open | 금지 |
| `FUTILITY_KILL` | 충분한 selection block에서 사전 효과 하한 실패 | 금지 |
| `DROPPED_BUDGET` | 유효하지만 promotion cap 밖 | 금지; 과학적 반례 아님 |
| `ABSTAIN` | rowㆍclusterㆍ$n_{\rm eff}$ 부족 | 결과 없음; threshold 완화 금지 |
| `PROMOTE` | 절대 gate 통과와 상대 순위 안 | 다음 block 1회 접근 |

작은 block이 약하다는 이유로 negative score를 자동 KILL하지 않는다. SMALL의
$-0.01<J\le0$ candidate가 promotion cap 밖이면 `DROPPED_BUDGET`이다. 반대로 PSDㆍ미래
누출 같은 구조 결함은 표본 수와 무관하게 즉시 kill한다.

## 5. selection leakage 대안

70% 안에서는 measurement와 ridge coefficient를 fit하고 blocked CV를 수행할 수 있다.
2% SMALL을 연 순간부터 다음은 모두 금지한다.

- 새 prompt로 식 추가;
- kernel parameter, $n_{\rm eff}$, quality exponent, robust threshold 수정;
- normalizationㆍimputationㆍreliabilityㆍridge 재적합;
- primary target 또는 horizon 변경;
- candidate별 유리한 row 선택.

screen 결과를 보고 만든 식은 같은 10%에서 새 후보로 들어올 수 없다. 새 식은 새
generation과 새 selection block 또는 독립 corpus가 필요하다. FINAL 20% 실패 후
runner-up을 시험하면 final은 더 이상 sealed confirmation이 아니므로 금지한다.

## 6. recording과 시간 일반화

2/3/2.5/2.5%는 서로 다른 chronological block이고 각 경계에 embargo가 있다. 각
recording의 row loss를 먼저 하나로 집계하고 최소 7개 recording cluster가 있을 때만
ranking한다. 그래도 같은 animal의 연속 기록이므로 selection claim일 뿐이다. FINAL은
outer-held-out GCaMP recording 두 개에서만 열고 window를 pooling하지 않은
recording-level paired statistic을 쓴다.

두 held-out recording도 보편적 animal population을 대표한다고 볼 수 없다. 성공 시
최대 결론은 “이 동결 corpus의 developmental held-out future locomotion에서 증분값이
재현됐다”이다. 독립 WormID/DANDI/IBL 또는 별도 perturbation corpus가 있어야 그보다
높은 지위로 갈 수 있다.

## 7. control route

hard-gap predecessor는 새 식이 단지 row를 더 많이 남겨 이긴 것인지 확인하는 matched
control이다. mask-only와 red는 missingness/motion artifact, GFP는 calcium-independent
artifact를 검사한다. phase, reverse와 neural/behavior shift는 temporal alignment를
깨뜨린다. 이 adverse control이 candidate를 따라가면 유효차원이 미래 행동 구조를
잡았다는 해석은 중지한다.

모든 predictor는 같은 common row, 같은 AR lag, 같은 ridge grid와 네 추가 scalar
budget을 쓴다. archived symmetric source filter는 미래 neural sample을 읽으므로
diagnostic-only다.

## 8. 권고 실행 경로

1. exact 48-candidate manifest와 source hash를 만든다.
2. behavior 없이 F0-v3/F1-v6/F2 successive-halving/독립 confirmation/F2R과 neural-stage input lock을 끝낸다.
3. survivor가 0이면 바로 run을 닫는다.
4. survivor가 있으면 70%에서 coefficient를 고정하고 SMALL부터 순서대로 한 block씩 연다.
5. LARGE-B를 통과한 하나만 final lock에 넣는다.
6. FINAL PASS/FAIL 뒤 같은 corpus에서 식을 더 시도하지 않는다.

대안 판정: **SELECT physical-time masked PSD; preserve hard-gap as control; defer learned and directed routes**.
