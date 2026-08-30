# CE-BRAIN Phase 2C 공통 상태축 독립 확인 계약

Status: `LOCKED_PRE_RESULT / ENDPOINT_UNOPENED`

## 1. 질문

Phase 2가 유지한 rank-1 분리가능 후보가 새 동물의 낮은 전류에서도 실제 awake→isoflurane 전달 대비를 예측하는가? 이를 0효과, raw global gain, 시간 드리프트, recovery 대조와 함께 판별한다.

이 계약은 기하를 직접 시험하지 않는다. 공통 상태축과 recovery가 독립 동물에서 모두 확인될 때만 Stage 3을 허가한다.

## 2. 데이터 역할과 독립성

- 개발 동물: 521885, 521886. 두 동물의 EEG 결과는 이미 열린 상태다.
- 미개봉 확인 동물: 521887, 20 μA, awake/isoflurane/recovery.
- 고정판: DANDI `000458@0.230317.0039`.
- 확인 자산 UUID: `ec27a42e-098f-418e-b5e6-1424d5bbdb90`.
- 확인 자산 바이트: `428192135`.
- 확인 자산 SHA-256: `716e5372de827ab0a72fae5036045527f5e884bcc5a48215bba278fbb516521e`.

세 동물의 공통 유효 EEG 열만 쓴다.

```text
0, 1, 2, 3, 5, 20, 22, 23, 24, 25, 26, 27, 28, 29
```

## 3. 521887 source-only 스키마 잠금

- EEG shape: `9261311×30`, int16, conversion `1.9499999284744263e-07 V/count`.
- timestamp gap: index `97470`의 2-sample gap과 index `2354430` 뒤의 약 102.323초 block gap.
- awake는 `[97471,2354431)`, isoflurane/recovery는 `[2354431,9261311)` 연속구간에서 따로 필터링한다.
- 첫 gap 이전 또는 추출창이 경계를 넘는 awake trial 9개는 endpoint와 무관하게 제외한다.
- 최종 split: awake 95/95, isoflurane 150/150, recovery 150/150 development/confirmation.
- gap 외 timestamp 상대 jitter 상한은 `3e-5`다.

## 4. 전처리

Phase 2와 동일하게 0.1–100 Hz 3차 zero-phase Butterworth, 0–2 ms artifact substitution, 공통채널 CAR, -500~-10 ms baseline, 2–498 ms/2 ms grid를 쓴다. 파형은 `249×14=3486`차원이다. 각 trial을 L2 정규화한 파형을 주 분석에 쓰고 raw 정규화 전 파형은 global-gain 대조에만 쓴다.

짝수 trial ID는 target 보정, 홀수 ID는 완전 확인이다.

## 5. 공통 상태축과 예측

개발 동물 `a∈{521885,521886}`의 20 μA 정규화 상태 대비를

$$
\delta_a=m_{a,iso}-m_{a,awake}
$$

로 둔다. 두 대비의 최적 rank-1 축 `v`를 구하고 평균 개발 대비와 내적이 양수가 되도록 방향을 고정한다.

521887 짝수 trial의 대비 `\delta_dev`에서 크기

$$
b_{dev}=\delta_{dev}^{\top}v
$$

만 보정한다. 확인 예측은 `\hat\delta=b_dev v`다. 홀수 trial 대비 `\delta_conf`에 대해

$$
I_0=\frac{\|\delta_{conf}\|^2-\|\delta_{conf}-\hat\delta\|^2}{\|\delta_{conf}\|^2}
$$

와 signed cosine `C=(\delta_conf^Tv)/\|\delta_conf\|`를 계산한다.

## 6. 불확실성·대조·판정

- 1,999회 cell-wise bootstrap, `PCG64(20260902)`.
- 홀수 awake/isoflurane 라벨 999회 permutation, `PCG64(20261902)`.
- raw 확인 평균에서 nonnegative awake→isoflurane gain `alpha`와 상대 residual `R` 계산.
- recovery `Q=D(awake,recovery)/D(awake,isoflurane)` 및 1,999회 bootstrap upper 97.5% 계산.
- 홀수 확인 trial의 시간 전반/후반에서 `I0>0`, `C>0` 부호 유지 여부 확인.

`STATE_AXIS_AND_RECOVERY_SUPPORTED` 조건:

1. `I0≥0.10`, bootstrap 95% 하한 `>0`;
2. `C≥0.30`, bootstrap 95% 하한 `>0`;
3. 상태 label permutation `p≤0.01`;
4. raw global-gain residual `R≥0.10`;
5. recovery `Q≤0.75`, bootstrap `Q_upper_97_5<1`;
6. 시간 전반/후반 모두 `I0>0`, `C>0`.

1–4와 6은 통과하지만 5가 실패하면 `STATE_AXIS_SUPPORTED_RECOVERY_NOT_ESTABLISHED`다. 나머지 유효 결과는 `STATE_AXIS_NOT_ESTABLISHED`, 무결성 실패는 `PHASE2C_APPARATUS_STOP`이다.

## 7. 다음 경로

- `STATE_AXIS_AND_RECOVERY_SUPPORTED`: Stage 3 metric/graph/operator 계약 개방.
- `STATE_AXIS_SUPPORTED_RECOVERY_NOT_ESTABLISHED`: 3×3 미개봉 동물에서 recovery 축을 우선 재검증.
- `STATE_AXIS_NOT_ESTABLISHED`: 공통 상태축을 닫고 개체 이질성·비정상 연산자 경로로 이동.

통과하더라도 “국소 뇌 기하가 증명됐다”고 말하지 않는다. Stage 3을 시험할 자격만 생긴다.

## 8. 실행 전 영수증

- 분석기: `examples/brain/ce_brain_phase2c_state_axis.py`
- 집중 테스트: `tests/test_ce_brain_phase2c_state_axis.py`, `8 passed`
- source-only schema receipt: `078c69a9a1cd8195cc184c0311e49bfd6f9aca9e0c1aad74216ea19d32b51a7d`
- 확인 endpoint 개봉 상태: `false`

계약·분석기·테스트와 세 원자료 해시는 manifest에 고정한다. 결과를 본 뒤 이 계약을 수정하지 않고 결과·해석은 별도 정본 문서에 기록한다.
