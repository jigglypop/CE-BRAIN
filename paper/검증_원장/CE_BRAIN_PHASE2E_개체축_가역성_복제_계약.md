# CE-BRAIN Phase 2E 개체축·가역성 독립 복제 계약

Status: `DRAFT_PRE_RESULT`

## 1. 목표와 정렬 점검

- **최종 목표:** 상태에 따라 변하는 국소 전달구조를 검증한 뒤 metric/graph/operator 후보를 경쟁시킨다.
- **이번 하위 목표:** Phase 2D의 개체 내부 rank-1 상태축이 새 다중전류 동물에서 재현되고, recovery에서 awake 쪽으로 되돌아오는지 확인한다.
- **필요성:** 개체축과 가역성이 모두 확인되지 않으면 안정된 상태공간을 전제하는 Stage 3 기하 경쟁은 시기상조다.
- **계보 점검:** 인간 CCEP나 outcome-known MICrONS 결과는 이 판정에 사용하지 않는다. 이 계약은 DANDI 상태 사다리의 Phase 2E다.

## 2. 미개봉 자산

- DANDI `000458@0.230317.0039`, subject `551399`.
- asset UUID `942c7978-09e1-41f6-a2eb-00f0a70ddfde`.
- bytes `11687836529`.
- SHA-256 `a949ca38d1b2c55b32c694bff8c9ce73195ec6c84a9d58f61cc9ce456ba14029`.
- EEG `17173504×30`, int16, conversion `1.9499999284744263e-07`, timestamp gap 없음, 상대 jitter 상한 `3e-5`.

awake/isoflurane/recovery × 40/60/80 μA의 MOs biphasic valid trial을 쓴다. 짝수 trial은 개발, 홀수 trial은 완전 확인이다.

| 상태 | 전류 | 개발 | 확인 |
|---|---:|---:|---:|
| awake | 40/60/80 | 57/56/67 | 61/64/53 |
| isoflurane | 40/60/80 | 57/56/67 | 62/64/53 |
| recovery | 40/60/80 | 114/112/134 | 125/128/106 |

## 3. 측정공간과 전처리

Phase 2D 확인 동물과 551399가 공유하는 다음 10개 EEG 열을 사용한다.

```text
5, 20, 22, 23, 24, 25, 26, 27, 28, 29
```

0.1–100 Hz 3차 Butterworth zero-phase 필터, 자극 직후 5 sample artifact substitution, CAR, -500~-10 ms baseline, 2–498 ms grid를 그대로 쓴다. 결과는 `249×10=2490`차원이며 trial별 L2 정규화한다.

## 4. 개체축 복제

짝수 awake/isoflurane trial의 전류별 대비 `δ_dev(u)`로 rank-1 축 `v_I`를 만든다. 홀수 대비 `δ_conf(u)`를 다음 세 후보로 채점한다.

- `Z`: `p_Z(u)=0`.
- `I`: `p_I(u)=[δ_dev(u)^Tv_I]v_I`.
- `K`: `p_K(u)=δ_dev(u)`.

오차는 세 전류 평균 제곱거리다. `I`가 `Z`보다 10% 이상 개선되고 bootstrap 95% 하한이 0보다 크며, `K`의 `I` 대비 개선이 같은 지지 문턱을 넘지 않아야 개체축이 복제된다.

## 5. recovery 가역성

홀수 trial에서 전류별

$$
Q(u)=\frac{\|\mu_R(u)-\mu_A(u)\|}{\|\mu_I(u)-\mu_A(u)\|}
$$

를 계산한다. 세 전류 모두 `Q≤0.75`, bootstrap 97.5% 상한 `<1`이어야 가역성이 확립된다. recovery 홀수 trial을 시간순 전반/후반으로 나눈 두 진단에서도 각 전류 `Q<1`이어야 한다.

## 6. 불확실성과 대조

- 모든 상태×전류×split cell 독립 재표집 1,999회, `PCG64(20260904)`.
- 홀수 awake/isoflurane label permutation 전류별 999회, seed `20261904+current`.
- 홀수 raw mean global-gain residual `R(u)` 보고.
- awake/isoflurane 확인 trial 시간 전반/후반에서 I/K/Z 순위를 보고.

## 7. 사전 판정

1. 개체축과 recovery 조건 모두 통과: `INDIVIDUAL_AXIS_AND_RECOVERY_REPLICATED`, `stage3_authorized=true`.
2. 개체축만 통과: `INDIVIDUAL_AXIS_REPLICATED_RECOVERY_NOT_ESTABLISHED`, Stage 3 미허가.
3. 개체축 실패: `INDIVIDUAL_AXIS_NOT_REPLICATED`, Stage 3 미허가.
4. provenance/schema/preprocessing/manifest/recompute 실패: `PHASE2E_APPARATUS_STOP`.

양성이라도 이 한 동물은 개체별 좌표의 두 번째 사례일 뿐, 모든 동물의 보편 좌표를 뜻하지 않는다. Stage 3이 허가되면 먼저 **개체 내부** metric/graph/operator 경쟁만 허용하며 anatomy-blind Stage 4는 별도 게이트다.
