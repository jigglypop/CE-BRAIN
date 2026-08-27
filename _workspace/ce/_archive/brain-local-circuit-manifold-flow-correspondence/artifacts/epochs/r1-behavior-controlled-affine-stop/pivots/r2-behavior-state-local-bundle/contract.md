# 구조 피벗 계약: R2 행동 상태별 국소 bundle

Status: COMPLETE

Mode: light empirical pivot / outcome-informed development

반례 식별자: `r1-behavior-controlled-affine-stop`

구조 지문: `behavior-only-chart-conditioned-piecewise-triangular-affine-bundle-with-explicit-chart-controls`

구조 변경 종류: `interaction`

바뀌는 항: `global_operator_family_to_behavior_chart_specific_base_fiber_operators`

## 질문과 주장 상한

이미 열린 DANDI `001701` 한 세션에서 전역 또는 연속적으로 행동 조절된 하나의
affine-fiber 연산자 대신, 행동만으로 정한 네 chart마다 서로 다른 국소 tangent와
삼각 affine 연산자를 쓰면 100 ms 뒤 집단 발화 예측이 사전 고정 대조군보다
나아지고 각 국소 fiber가 수축하는지를 묻는다. R2의 양성 판정도
outcome-informed 단일 세션 L2 개발 적합도일 뿐이며 독립 확인이나 생물 기전
증거가 아니다.

## PREDECESSOR_EVIDENCE

| 선행 결과 | 증거 | 판정 | 보존하는 좁은 주장 | 재시도 금지 |
|---|---|---|---|---|
| R0 global affine fiber | `artifacts/epochs/real-dandi-001701/{20-audit.md,31-validation.md}` | `EMPIRICAL FAIL` | 같은 관측계에서 persistence를 넘는 한-step 예측성은 있다 | 전역 affine 식의 차원·ridge·문턱·split 재조율 금지 |
| R1 behavior-controlled affine fiber | `artifacts/epochs/real-global-affine-fiber-fail/pivots/r1-behavior-controlled-fiber/{report.md,audit.md}` | `STOP` | 실제 행동 정렬은 10초 이동 행동보다 정보가 있으나 후보 우위와 수축은 없다 | R1 feature·endpoint·문턱 구제 금지 |
| confirmation source | DANDI `001695@0.260319.2023` | `SEALED / UNOPENED` | 결과가 없는 provenance 상태만 보존 | R2 탐색·구제·확인에 열지 않음 |

R1 witness는 후보 NMSE `0.9610331`, full-VAR+input `0.9607531`,
base+input `0.9563235`, $q_{\max}=1.1061971$이다. 이 수치는 R2의 계수,
chart 수, 차원 또는 문턱을 선택하는 데 사용하지 않는다.

## 실제 뇌 발견 하네스 필드

| 필드 | 동결 선언 |
|---|---|
| `BIO_STARTING_MECHANISM` | `units/spike_times`는 시간가변 집단 발화율이 내는 extracellular point event로 취급한다. 생물 기준선은 train-only 분산 안정화 count에 대한 first-order full population predictor $x_{t+1}=Rx_t+S\phi_t+r+\epsilon_t$다. 이는 세포 기전식이 아니라 관측 해상도에서의 통계적 예측 기준선이며 그보다 강한 생물학적 해석을 금지한다. |
| `CE_DELTA` | 전역 $R$ 또는 전역 fiber family 대신 행동-only chart $s_t=c(\phi_t)\in\{1,2,3,4\}$와 chart별 tangent $U_i$, base 연산자 $B_i$, normal fiber 연산자 $A_i$를 추가한다. 이 구조는 R0/R1 결과를 본 뒤 제안된 `[경험식]`이다. |
| `MEASUREMENT_MODEL` | 선행 계약과 동일하게 100 ms non-overlap spike count, train 구간 0.1 Hz unit retention, $\sqrt{n+3/8}$, unitwise train mean/scale을 사용한다. 행동은 NWB Position 2D, head direction의 sine/cosine, 100 ms backward velocity 2D로 만든 $\phi_t\in\mathbb R^6$이다. head-direction unit metadata가 degree면 radian으로 바꾸고 radian이면 그대로 쓰며, 둘 다 아니면 fail-closed한다. 위치·방향은 bin center에 보간하고 train valid bin의 mean/scale만 사용한다. |
| `DATA_PROVENANCE` | DANDI `001701@0.260120.0303`, DOI `10.48324/dandi.001701/0.260120.0303`; asset UUID `3f3d0b16-9b3e-42ac-a5e6-327829df1116`; path `sub-BaggySweatpants/sub-BaggySweatpants_ses-BaggySweatpants-DY15-g1_behavior+ecephys.nwb`; 12,967,760 bytes; SHA-256 `5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3`. |
| `DATA_SPLIT` | 전체 완전 bin의 앞 50% train, 다음 25% development, 마지막 25% chronological evaluation이다. 경계 또는 ElectricalSeries gap을 넘는 row는 버린다. 이 asset은 R0/R1에서 이미 열렸으므로 마지막 25%도 독립 holdout 또는 confirmation이라 부르지 않는다. 다만 R2 chart·basis·계수·모형 선택은 이 계약 뒤 train/development에만 결박하고 evaluation R2 endpoint는 한 번만 계산한다. DANDI 001695는 열지 않는다. |
| `OBSERVABLES` | 모든 모형의 동일-row one-step NMSE, R2와 세 primary comparator의 상대 개선율, 2,000회 100-bin paired moving-block bootstrap 95% 구간, chart별 row 수와 NMSE, $q_i$와 $q_{\max}$, 100-bin shifted-chart 결과, chart transition count, tangent projector 거리와 principal angle을 보고한다. |
| `RESIDUAL_RULE` | 동일 evaluation row와 $D=\sum_{t\in E}\|x_{t+1}-\bar x_{\rm train}\|_2^2$ 분모를 사용한다. R2 양성은 세 primary comparator 각각보다 NMSE가 1% 이상 낮고 paired improvement CI 하한이 모두 0보다 커야 한다. 모든 chart의 보수적 fiber certificate $q_i^{\rm ub}<1$과 real-chart NMSE가 shifted-chart NMSE보다 낮다는 조건도 동시에 요구한다. 하나라도 실패하면 `STOP`이다. |
| `FALSIFIER` | 세 우위 gate 중 하나의 실패, $q_i^{\rm ub}\ge1$, chart support gate 실패, shifted chart가 real chart와 같거나 우수함, 또는 evaluation 전에 neural outcome이 chart 구성에 들어간 사실이 후보를 죽인다. |
| `MATCHED_CONTROLS` | (1) global full-VAR+input, (2) 동일 chart를 쓰는 local full-VAR+input, (3) 하나의 global tangent/fiber를 쓰는 matched triangular model이 primary다. global base+input, input-only, persistence와 train mean은 secondary다. 100-bin shifted chart는 adverse control이다. 모든 ridge menu와 intercept 관례는 동일하다. |
| `MODEL_SELECTION` | chart 수 $K=4$와 구성 알고리즘은 고정한다. R2와 global matched fiber의 $d\in\{2,4,8\}$, 모든 ridge $\lambda\in\{10^{-4},10^{-3},10^{-2},10^{-1},1,10\}$만 development SSE로 고른다. exact tie는 작은 $d$, 큰 $\lambda$다. local/global full VAR은 같은 lambda grid를 독립 선택한다. evaluation 기반 reselection은 없다. |
| `REVISION_TRIGGER` | D/I/P/C/B 오류만 endpoint를 바꾸지 않는 최소 수리를 허용한다. 유효한 T 잔차 또는 gate 실패 뒤에는 chart 수, feature, bin, split, threshold, endpoint, seed를 바꾸지 않는다. 후속은 R3 또는 R4의 별도 구조 계약이어야 한다. |
| `CLAIM_CEILING` | 최대 `[경험 비교: outcome-informed single-session L2 development]`. PASS도 행동-indexed piecewise predictor의 적합도만 뜻한다. smooth manifold, tangent bundle의 생물학적 실재, continuous flow, causal attraction, Riemannian metric, memory, consciousness, self 또는 AGI를 주장하지 않는다. |

## 행동 chart의 outcome-blind 고정

행동 feature는

$$
\phi_t=(p_t^x,p_t^y,\sin\theta_t,\cos\theta_t,v_t^x,v_t^y)
$$

이다. train valid row만으로 각 열을 표준화한다. $K=4$ deterministic
farthest-first Lloyd partition을 다음 순서로 고정한다.

1. 첫 중심은 표준화 train 행동의 평균에 가장 가까운 row이며 동률은 이른 시간이다.
2. 다음 중심은 기존 중심까지의 최소 제곱거리가 가장 큰 row이며 동률은 이른 시간이다.
3. nearest-centroid label과 centroid mean 갱신을 label이 멈추거나 100회가 될 때까지 반복한다. 거리 동률은 작은 label이다. 100회 안에 label이 멈추지 않으면 `CHART_NOT_CONVERGED`로 STOP한다.
4. 빈 chart가 생기면 `EMPTY_CHART`로 STOP한다. 마지막 중심은 6개 좌표의 사전식 순서로 다시 label한다.
5. development/evaluation/shift control은 이 train 중심에 nearest-centroid로만 배정한다. neural $x_t$, target, 오차 또는 R0/R1 결과는 chart 생성에 들어가지 않는다.

각 chart는 train predictor row가 $N+7$개보다 많고 development와 evaluation
predictor row가 각각 100개 이상이어야 한다. 여기서 $N$은 train-only retained unit
수다. 이 조건은 local full-VAR+input의 predictor 수보다 train row가 많게 하는
식별 가능성 gate다. 하나라도 실패하면 $K$나 기준을 바꾸지 않고
`INSUFFICIENT_CHART_SUPPORT`로 STOP한다.

## R2 후보식

chart $i$의 train neural mean을 $\mu_i$라 하고, chart train rows의 centered
$x_t$에 대한 상위 $d$ right singular vectors를 열로 갖는
$U_i\in\mathbb R^{N\times d}$를 쓴다. 모든 양은 train-only다.

$$
z_t^{(i)}=U_i^\top(x_t-\mu_i),
\qquad
y_t^{(i)}=(I-U_iU_i^\top)(x_t-\mu_i).
$$

$h_t^{(i)}=(z_t^{(i)},\phi_t)$라 두고 chart별로

$$
z_{t+1}^{(i)}=(B_i\;D_i)h_t^{(i)}+d_i,
$$

$$
\widetilde y_{t+1,j}^{(i)}
=a_{ij}y_{t,j}^{(i)}+\beta_{ij}^\top h_t^{(i)}+e_{ij},
$$

$$
\widehat y_{t+1}^{(i)}
=(I-U_iU_i^\top)\widetilde y_{t+1}^{(i)},
\qquad
\widehat x_{t+1}=\mu_i+U_i\widehat z_{t+1}^{(i)}
+\widehat y_{t+1}^{(i)}
$$

를 적합한다. intercept는 벌점하지 않고 나머지 계수에는 같은 ridge $\lambda$를
쓴다. $A_i=\operatorname{diag}(a_{i1},\ldots,a_{iN})$이고 normal projection의
연산자 노름은

$$
\left\|(I-U_iU_i^\top)A_i\big|_{\operatorname{im}(I-U_iU_i^\top)}\right\|_2
\le q_i^{\rm ub}:=\max_j|a_{ij}|
$$

이므로, clipping 없이 $q_i^{\rm ub}<1$을 보수적 수축 certificate로 쓴다.
이 부등식은 local tangent의 실제 생물학적 존재를 증명하지 않는다.

## 대조 모형

Primary comparator는 다음 세 개다.

1. global full-VAR+input:
   $x_{t+1}=Rx_t+S\phi_t+r$.
2. chart-matched local full-VAR+input:
   $x_{t+1}=R_ix_t+S_i\phi_t+r_i$ when $s_t=i$.
3. global matched tangent/fiber: 위 R2 식을 $K=1$, global train mean과 global
   train PCA basis로 적합한다.

Secondary comparator는 R1의 global base+input, input-only, persistence와 train
mean이다. primary 우위 세 개만 R2 양성 gate에 들어간다. local full VAR은
partition 자체가 주는 이득과 triangular contracting-fiber 구조를 분리한다.

## 불확도와 adverse control

모든 primary 비교는 evaluation row별 squared-error 차이를 사용해 seed `1701`,
block 100 bin, 2,000회 moving-block bootstrap을 한다. 연속 run이 100 row보다
짧으면 그 block을 만들지 않으며 전체 evaluation row가 300 미만이거나 후보 block이
3개 미만이면 양성 판정을 금지한다.

shifted-chart 대조는 각 split 안에서 chart label만 100 bin 뒤로 민다. wrap은
없고 각 split의 첫 100 row를 버린다. 행동 feature $\phi_t$와 neural target은
옮기지 않는다. 이동 label로 local mean, tangent, 계수, $d$, $\lambda$를 train /
development에서 전부 다시 적합하고, real 후보도 동일하게 줄인 evaluation row에
재채점한다. 이동 label에도 동일한 chart support gate를 적용한다. shifted NMSE가
real NMSE 이하이면 R2는 STOP이다.

## 국소 tangent 진단의 지위

chart 쌍마다 $U_i^\top U_j$의 singular value에서 principal angle을 계산하고

$$
d_{ij}=\frac{\|U_iU_i^\top-U_jU_j^\top\|_F}{\sqrt{2d}}
$$

를 보고한다. train에서 두 방향을 합한 실제 전이가 20회 이상인 unordered chart
쌍을 adjacent로 표시하고
evaluation transition count도 함께 기록한다. 이 값들은 descriptive diagnostic이다.
큰 각도, 작은 각도 또는 행동 거리와의 상관 어느 것도 R2 PASS나 곡률·리만 계량
주장으로 승격하지 않는다.

## 자원·실행·중단 규칙

NWB는 소유한 임시 디렉터리에 내려받아 byte/SHA-256을 재검증하고 계산 뒤
삭제한다. 저장소에는 source receipt, aggregate result, 코드와 작은 합성 fixture
결과만 남긴다. R2 endpoint를 실행한 뒤 유리한 chart 수, feature, $d$ menu,
lambda menu, 수축 문턱, 비교군 또는 분모로 바꾸지 않는다.

판별 예측: behavior-only local bundle이 세 primary comparator 모두보다 1% 이상
좋고 paired CI 하한이 양수이며 모든 $q_i^{\rm ub}<1$이고 real chart가 shifted
chart보다 좋아야 한다.

중단 조건: 위 조건 하나라도 실패하거나 source/support/leakage gate가 실패하면
R2를 `STOP`으로 닫고 DANDI 001695를 열지 않는다.
