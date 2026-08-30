# CE-BRAIN Phase 2D 개체축·전류별 연산자 판별 계약

Status: `LOCKED_PRE_RESULT`

잠금 근거: 확인 파형을 열지 않은 schema-only 점검 `32d3dd372928cc7521cca50de2371e8f6c0f6f7965403706a1a3efb00fdfaeb1`, 집중 단위시험 `7 passed`. 자산의 전체 trial 표는 1,440행이며, 아래 판정에 들어오는 awake/isoflurane valid trial의 짝수/홀수 수가 사전 표와 일치했다. recovery 360행은 모두 무효이고 그 밖의 무효 행도 `is_valid` 필터로 제외한다.

## 1. 질문

공통 상태축이 실패한 뒤 남은 세 설명을 새 다중전류 동물에서 경쟁시킨다.

- `Z`: 확인 가능한 상태 대비가 없다.
- `G`: 앞선 동물들에서 학습한 공통 상태축이 있다.
- `I`: 동물마다 다르지만 한 동물 안에서는 전류를 가로지르는 rank-1 상태축이 안정적이다.
- `K`: 같은 동물 안에서도 전류마다 상태 대비 방향이 다른 일반 연산자다.

## 2. 미개봉 확인 자산

- DANDI `000458@0.230317.0039`, subject `569070`.
- asset UUID `7b2e1a9c-0900-4f5d-9be7-a2dcb2ca5cb3`.
- bytes `1124308400`.
- SHA-256 `c985835d707fa688de39968b3f2645150a7d67818ae7c81a9bd8c746d4c5202b`.
- awake/isoflurane의 20/40/60 μA MOs biphasic valid trial을 쓴다.
- recovery trial 360개는 NWB에서 모두 `is_valid=false`이므로 결과와 무관하게 제외한다.

확인 자산 EEG는 `22065920×30`, int16, 2500 Hz이며 timestamp gap은 없다. gap 외 상대 jitter 상한은 `3e-5`다. 짝수/홀수 trial 수는 다음과 같다.

| 상태 | 전류 | 개발 | 확인 |
|---|---:|---:|---:|
| awake | 20 | 52 | 60 |
| awake | 40 | 54 | 58 |
| awake | 60 | 63 | 46 |
| isoflurane | 20 | 57 | 63 |
| isoflurane | 40 | 56 | 64 |
| isoflurane | 60 | 67 | 53 |

## 3. 공통 측정공간

개발 동물 521885·521886·521887과 확인 동물 569070이 모두 공유하는 EEG 열만 사용한다.

```text
0, 1, 5, 20, 22, 23, 24, 25, 26, 27, 28, 29
```

전처리는 앞 계약과 동일한 0.1–100 Hz 필터, artifact substitution, CAR, baseline, 2–498 ms grid다. 결과 파형은 `249×12=2988`차원이고 trial별 L2 정규화를 적용한다.

## 4. 학습과 완전 확인

확인 동물 짝수 trial로만 후보를 학습하고 홀수 trial 대비를 채점한다. 전류별 상태 대비를 `δ_dev(u)`, `δ_conf(u)`로 쓴다.

- `Z`: `p_Z(u)=0`.
- `G`: 앞선 세 동물의 20 μA 대비로 만든 외부 rank-1 축 `v_G`; `p_G(u)=[δ_dev(u)^Tv_G]v_G`.
- `I`: 확인 동물의 세 `δ_dev(u)`로 만든 rank-1 축 `v_I`; `p_I(u)=[δ_dev(u)^Tv_I]v_I`.
- `K`: `p_K(u)=δ_dev(u)`.

모델 오차는

$$
E_M=\frac13\sum_{u\in\{20,40,60\}}\|\delta_{conf}(u)-p_M(u)\|_2^2
$$

이고 A가 B보다 나은 상대 개선은 `(E_B-E_A)/E_B`다.

## 5. 불확실성과 대조

- 모든 source·target 상태×전류 cell을 독립 재표집하는 1,999회 bootstrap, `PCG64(20260903)`.
- target 홀수 awake/isoflurane label permutation을 전류별 999회, seed `20261903+current`.
- raw mean global-gain residual `R(u)`를 전류별 보고.
- target 확인 trial을 각 cell의 시간 전반/후반으로 나눠 같은 모델 순위를 보고.

## 6. 판정

모든 ‘지지’는 해당 상대 개선 `≥0.10`이고 bootstrap 95% 하한 `>0`이어야 한다.

1. `CURRENT_SPECIFIC_OPERATOR_SUPPORTED`: K가 I와 Z를 모두 지지 문턱으로 이긴다.
2. `INDIVIDUAL_AXIS_SUPPORTED`: I가 G와 Z를 모두 이기고, K의 I 대비 개선이 지지 문턱을 넘지 않는다.
3. `GLOBAL_AXIS_PARTIAL`: G가 Z를 이기고, I의 G 대비 개선이 지지 문턱을 넘지 않는다.
4. `NO_STABLE_STATE_MODEL`: G/I/K 모두 Z보다 관측 오차가 크거나 같다.
5. 그 밖의 유효 결과: `HETEROGENEITY_OPERATOR_TENSION`.
6. provenance/schema/preprocessing/manifest/recompute 실패: `PHASE2D_APPARATUS_STOP`.

세 전류 label permutation이 모두 `p≤0.05`이고 각 `R≥0.10`인지도 보고하지만 후보 선택 문턱을 사후 변경하지 않는다.

## 7. 다음 경로

- K 지지: metric보다 전류 조건부 transition operator를 우선한다.
- I 지지: 개체별 좌표 정렬과 recovery-bearing 3×3 동물 복제를 먼저 한다.
- G 부분 지지: 공통축 반례와의 이질성 원인을 분석한다.
- 무안정/긴장: block drift·비정상 연산자 분기를 연다.

이 자산은 유효 recovery가 없으므로 어떤 양성 결과도 Stage 3을 즉시 허가하지 않는다.
