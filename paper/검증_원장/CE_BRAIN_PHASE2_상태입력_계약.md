# CE-BRAIN Phase 2 상태×입력 판별 계약

Status: `LOCKED_PRE_RESULT / ENDPOINT_UNOPENED`

## 1. 질문과 주장 상한

고정 해부학에서 관측한 EEG 전달 파형이 상태와 입력의 분리가능 객체인지, 아니면 자극 전류에 따라 상태 효과의 의미가 달라지는 조건부 객체인지 판별한다.

- M1, 분리가능 후보: trial 크기를 제거한 표현에서 상태 대비의 방향은 하나이고 전류는 그 크기만 바꾼다.
- M2, 상호작용 후보: 상태 대비가 전류의 함수로 변한다.

이 계약이 통과해도 말할 수 있는 것은 두 생쥐의 MOs 자극·EEG 측정공간에서 `awake→isoflurane` 전달 대비가 전류 조건부라는 것뿐이다. 해부학적 간선, 거리, 리만 계량, 의식 기전은 주장하지 않는다.

## 2. 선행 결과와 독립성

- `521885`는 기존 Stage 2에서 이미 결과가 열린 개발 동물이다. 이 계약에서 독립 확증으로 세지 않는다.
- `521886`은 이 계약을 작성하는 동안 NWB 메타데이터와 trial 표만 읽었다. EEG `data` 값은 미개봉 확인 endpoint다.
- 기존 Stage 2의 전처리와 trial별 L2 정규화를 계승한다. 확인 결과를 본 뒤 채널, 시간창, 필터, 모형, seed, 문턱을 바꾸지 않는다.

## 3. 데이터 잠금

판본: DANDI `000458@0.230317.0039`.

| 역할 | 동물 | asset UUID | 바이트 | SHA-256 |
|---|---|---|---:|---|
| outcome-known 개발 | 521885 | `6ab37be4-adfe-4bea-a031-eb1a2b0782a8` | 312139546 | `b80cd3a375ead36c05c451f562e92947573cd0679a30ffd573a04e44339b0171` |
| 미개봉 확인 | 521886 | `d77558e6-1b16-49c2-9f61-885d63701331` | 504307581 | `a799afdf771a5f629e19312d37714b0990418cef0d2b7425b46e17574678fcb6` |

두 자산의 공통 유효 ElectricalSeries 열만 사용한다.

```text
0, 1, 2, 3, 4, 5, 9, 20, 22, 23, 24, 25, 26, 27, 28, 29
```

대상 trial은 `is_valid=true`, `estim_target_region=MOs`, `stimulus_description=biphasic`, 전류 `20/50/100 μA`다. 521885는 awake/isoflurane, 521886은 awake/isoflurane/recovery를 갖는다. 짝수 trial ID는 개발·보정, 홀수 ID는 확인이다.

## 4. 고정 전처리

1. EEG 샘플링률은 2500 Hz, NWB conversion을 적용해 μV로 바꾼다.
2. 각 자산의 등록된 단일 2-sample timestamp gap 뒤 연속구간만 사용한다: 521885 gap 왼쪽 index `125307`, 521886 `151674`.
3. gap 이외 timestamp 상대 jitter 상한은 각각 `2e-5`, `3e-5`다. 이 차이는 EEG 값을 열지 않은 source-only 감사에서 고정했다.
4. 자극 시작 `[0,5)` 다섯 샘플을 `[-5,0)`으로 채운다.
5. 연속 신호에 3차 zero-phase Butterworth 0.1–100 Hz bandpass를 적용한다.
6. 공통 16채널 CAR 후 trial별 `-500~-10 ms` 평균을 뺀다.
7. `2~498 ms`를 2 ms 간격으로 뽑아 `249×16=3984`차원 파형을 만든다.
8. 각 trial 파형을 양의 L2 norm으로 나눈다. 비유한값·0 norm은 apparatus stop이다.

## 5. M1/M2의 실행 정의

동물 `a`, 전류 `u`의 정규화 trial 평균을 `m_{a,s,u}`라 하고 상태 대비를

$$
\delta_a(u)=m_{a,\mathrm{iso},u}-m_{a,\mathrm{awake},u}
$$

로 정의한다.

각 held-out 전류 `u*`마다 521885의 나머지 두 전류 `u1,u2`만 이용한다.

- M1: 두 개발 대비의 최적 rank-1 축 `v`를 구해 `\delta(u)\approx b(u)v`로 분해하고, 두 계수 `b(u1),b(u2)`를 `u*`로 선형 보간 또는 외삽한다. 즉 매뉴얼의 `A(s)B(u)`를 벡터 파형에 적용한 실행형이다.
- M2: 두 개발 전류를 잇는 선형 상태×전류 상호작용을 `u*`로 보간 또는 외삽한다.

$$
\hat\delta_2(u^*)
=\delta(u_1)+\frac{u^*-u_1}{u_2-u_1}
[\delta(u_2)-\delta(u_1)].
$$

검사 표적은 521886 홀수-ID awake/isoflurane trial의 `\delta_{521886}(u*)`다. 그러므로 각 fold는 **새 동물이며 동시에 개발에서 제외된 새 전류**다.

오차는

$$
e_k(u^*)=\|\delta_{521886}(u^*)-\hat\delta_k(u^*)\|_2^2
$$

이고, 주 통계량은 세 전류 평균에서의 M1 대비 M2 상대 개선율이다.

$$
I=\frac{\bar e_1-\bar e_2}{\bar e_1}.
$$

## 6. 불확실성·대조·판정

- 각 source 상태×전류 cell과 target 확인 cell 안에서 독립 재표집하는 1999회 bootstrap을 쓴다.
- seed는 NumPy `PCG64(20260901)`로 고정한다.
- `STATE_INPUT_INTERACTION_SUPPORTED`: `I≥0.05`, bootstrap 95% 하한 `>0`, 세 전류 중 적어도 두 전류에서 `e2<e1`.
- `STATE_INPUT_SEPARABLE_RETAINED`: `I≤-0.05`, bootstrap 95% 상한 `<0`, 세 전류 중 적어도 두 전류에서 `e1<e2`.
- 그 밖의 유효 결과는 `STATE_INPUT_NOT_ESTABLISHED`다.
- provenance, schema, timestamp, split count, 파형, norm, manifest, 재계산 불일치는 `PHASE2_APPARATUS_STOP`이다.

대조 결과는 주 판정을 바꾸지 않고 해석 상한을 제한한다.

1. 521886 짝수 trial로 같은 동물 내부 leave-one-current-out을 계산한다.
2. 각 상태×전류 cell을 시간 전반/후반으로 나눠 M2 우위 부호가 유지되는지 본다.
3. recovery에서 `Q(u)=D(awake,recovery)/D(awake,isoflurane)`를 전류별로 보고한다.
4. 조건 평균 대비를 다시 단위 norm으로 바꾼 shape-only 결과를 보고해 크기와 방향 효과를 구분한다.

주 판정이 상호작용을 지지하더라도 대조가 심하게 불안정하면 `state×input 조건부 전달`까지만 남기고 geometry Stage 3 승격은 보류한다.

## 7. 결과별 다음 경로

- 상호작용 지지 + 대조 안정: 동일 전달행렬에서 R/F/G/S/O 후보를 경쟁시키는 Stage 3 계약을 연다.
- 상호작용 지지 + 대조 불안정: block drift·SNR·비정상 연산자 분해를 먼저 수행한다.
- 분리가능 유지: 상태×입력 강한 경로를 닫고 상태 주효과 또는 global gain 모형으로 축소한다.
- 미확립: 개체 이질성, 시간 드리프트, 비선형 dose-response를 서로 다른 사전등록 분기로 판별한다.

## 8. 실행 전 영수증

- 분석기: `examples/brain/ce_brain_phase2_state_input.py`
- 집중 테스트: `tests/test_ce_brain_phase2_state_input.py`
- FAST 검증: `11 passed`
- source-only schema receipt SHA-256: `d98f1c4c2c0090dfe59f640ebf6fab1a585ba8c502ca1cce3830c671f6cd1618`
- 확인 endpoint 개봉 상태: `false`

계약·분석기·테스트의 해시와 두 원자료의 해시는 실행 manifest에 묶는다. 결과에 따라 갱신해야 하는 상태 원장은 manifest 대상에서 제외한다. 고정된 세 파일 중 하나라도 바뀌면 실행기는 결과 계산을 거부한다.
