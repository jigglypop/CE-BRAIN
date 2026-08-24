# BA-OBS-ID1 연구 계약 — 유한 계량족의 동역학적 식별성 탈출 정리

Status: COMPLETE

Mode: full mathematics + deterministic synthetic witness

PREDECESSOR: `_workspace/ce/brain-finite-observation-metric-nonidentifiability-20260824`

CE_RUN: `_workspace/ce/brain-finite-observation-metric-identifiability-escape-20260824`

## 1. 질문과 판본 경계

BA-OBS-NOGO1은 유한 수동 관측의 점별 pullback만으로는 무한차원 ambient metric과
ambient dimension을 식별할 수 없음을 증명했다. 이 run은 그 결론을 지우거나 우회하지
않는다. 대신 다음의 더 좁은 질문을 사전등록한다.

> 무한차원 상태공간은 허용하되, 미지의 계량을 gauge가 고정된 유한 매개변수족으로
> 제한하고 알려진 동역학과 개입을 통해 관측할 때, 어떤 충분조건이 그 매개변수의
> 국소 식별성을 보장하는가?

이 run의 양성 결과는 임의의 무한차원 계량 복원이 아니라 **동결된 유한 계량족 내부의
국소 구조 식별성**만 뜻한다.

## 2. 선행 증거 동결

| 선행 산출 | SHA-256 | 판정 | 보존하는 주장 | 재시도 금지 조건 |
|---|---|---|---|---|
| `../brain-finite-observation-metric-nonidentifiability-20260824/00-contract.md` | `dba35c1704f9730e9e0660a02be2a2a0ee313ae9786bf90bd139b6840bf0b12f` | PASS | 문제의 정의역과 수동 관측 경계 | 동일한 유한 수동 map만으로 ambient 복원을 주장하지 않는다. |
| `../brain-finite-observation-metric-nonidentifiability-20260824/11-math.md` | `9b191659ae6b81a496371b670348e5ceaa3087820aeb8cf634a2b87eecc76699` | PASS | finite pullback의 kernel/rank 퇴화와 무한 hidden-metric witness | 본 run의 정리는 반드시 유한 계량족과 동역학·개입을 가정한다. |
| `../brain-finite-observation-metric-nonidentifiability-20260824/20-audit.md` | `73ad5bc6cba712bd3f7d400f0bfeaed3deb7d0529aeb656e57007d21d8c15ac9` | PASS | no-go의 형식 지위와 해석 금지선 | 의식·자아·3+1차원 결론으로 승격하지 않는다. |
| `../brain-finite-observation-metric-nonidentifiability-20260824/31-validation.md` | `485f888f2c6b63d92c410f5236543a3fb6e6ff4d7fd70c7b1f8844e20bd1c246` | PASS | 선행 run의 기계 검증 경계 | 기계 PASS를 경험적 뇌 증거로 읽지 않는다. |
| `../brain-finite-observation-metric-nonidentifiability-20260824/40-final-report.md` | `1c4d0dd051a0fcf6c0fd8cdb70300fb7da89cc9567e5b1026b695ab1209e055d` | PASS | observable quotient만 식별된다는 최종 결론 | 부모 no-go를 삭제하거나 약화하지 않는다. |

## 3. 일반 설정

**[정의]** 상태공간은 실 Hilbert 공간 $\mathcal H$이며 유한차원일 필요가 없다.
미지의 계량은 열린 집합 $\Theta\subset\mathbb R^p$ 위의

$$
\vartheta\longmapsto G(\vartheta)
$$

로 제한한다. 각 $G(\vartheta)$는 bounded, self-adjoint, coercive한 strong metric
operator이고, 중복 매개변수와 대칭은 사전에 gauge-fix되어 있다. $\vartheta$는 기준
계량에 대한 무차원 좌표다.

알려진 초기조건과 개입 $u^{(e)}$, 알려진 계량-결합 동역학, 알려진 관측 연산자를
합쳐 실험 $e=1,\ldots,E$의 표준화 출력 $\widetilde y_e$를 만든다. 이에 따른 forward
map을

$$
\Phi:\Theta\to
\mathcal Y:=\bigoplus_{e=1}^{E}
L^2([0,T_e],\mathbb R^{r_e}),
\qquad
\Phi(\vartheta)=(\widetilde y_e(\cdot;\vartheta))_{e=1}^{E}
$$

로 쓴다. 시간 $\tau=t/t_*$, 종료시각 $T_e$, 출력 $\widetilde y_e$는 모두
무차원이다. $\Phi$는 참값 $\vartheta_*$ 근방에서 $C^1$이라고 가정한다.

**[정의]** 민감도와 가중 민감도 Gramian은

$$
S_e(\tau;\vartheta)
=\frac{\partial\widetilde y_e(\tau;\vartheta)}{\partial\vartheta}
\in\mathbb R^{r_e\times p},
$$

$$
\mathcal I(\vartheta)
=\sum_{e=1}^{E}\int_0^{T_e}
S_e(\tau;\vartheta)^\top R_e(\tau)^{-1}
S_e(\tau;\vartheta)\,d\tau
$$

로 정의한다. $R_e:[0,T_e]\to\mathbb R^{r_e\times r_e}$는 강측정 가능하고 대칭이며
$\vartheta$와 무관하게 사전 고정된 표준화 출력의 무차원 가중행렬이다. 어떤
$0<r_-\le r_+<\infty$에 대해 거의 모든 $\tau$에서
$r_-I\preceq R_e(\tau)\preceq r_+I$를 만족한다. 따라서 가중 $L^2$ 내적은 표준
$L^2$ 내적과 동치이고 $\mathcal I$도 무차원이다.

## 4. 증명할 명제

**[정리 후보 T3: 유한 계량족의 국소 식별성]** 위 가정에서

$$
\mathcal I(\vartheta_*)\succ0
$$

이면 $\Phi$는 $\vartheta_*$의 어떤 근방에서 단사다. 즉 알려진 동역학·초기조건·개입
아래에서 $\vartheta_*$는 동결된 계량족 내부에서 국소 구조 식별 가능하다.

증명 의무는 다음과 같다.

1. 모든 $v\in\mathbb R^p$에 대해
   $v^\top\mathcal I v=\|D\Phi_{\vartheta_*}v\|_{\mathcal Y,R}^2$임을 보인다.
2. $\mathcal I\succ0$가 $D\Phi_{\vartheta_*}$의 단사성과 동치임을 보인다.
3. 민감도 벡터가 생성하는 유한차원 부분공간으로의 bounded 선형 readout $L$을
   구성하여 $D(L\circ\Phi)_{\vartheta_*}=I_p$로 만든다.
4. 유한차원 inverse function theorem을 $L\circ\Phi$에 적용해 $\Phi$의 국소
   단사성을 결론낸다.
5. 이 결론이 임의의 ambient metric, 전역 식별성, model correctness를 보장하지 않음을
   명시한다.

**[따름정리 후보 C2: 잔차 0에서의 고립 국소 최소점]** $\Phi$가 $C^2$이고

$$
\mathcal L(\vartheta)
=\frac12\|\Phi(\vartheta)-\Phi(\vartheta_*)\|_{\mathcal Y,R}^2
$$

이면 $\nabla^2\mathcal L(\vartheta_*)=\mathcal I(\vartheta_*)$이다. 따라서 T3의
조건 아래 $\vartheta_*$는 고립된 strict local minimizer다.

**[경계 명제]** $\mathcal I$가 singular이면 kernel 방향은 일차 민감도로 식별되지
않는다. 이것만으로 고차항 식별성이나 전역 비식별성까지 결론내리지는 않는다.

## 5. 구성적 무한차원 witness

**[정의]** 명시적 상태공간은

$$
\mathcal H=\mathbb R^2\oplus\ell^2,
\qquad q=(x,z,w),
$$

이고, 한 매개변수 계량족과 시간 의존 potential을

$$
G_\theta=\operatorname{diag}(1,e^\theta)\oplus I_{\ell^2},
\qquad \theta\in\mathbb R,
$$

$$
V_u(x,z,w)
=\frac12(x-z)^2+\frac\kappa2z^2-u(\tau)z
+\frac12\|w\|_{\ell^2}^2,
\qquad \kappa=0.30
$$

로 고정한다. 모든 변수는 기준 스케일로 정규화되어 무차원이다. 입력은
$u\in L^\infty([0,T])$로 두고 해는 Carathéodory 의미로 취한다. metric gradient flow
$q'=-G_\theta^{-1}\nabla V_u$와 관측 $y=x$는

$$
\begin{aligned}
x'&=z-x,\\
z'&=e^{-\theta}\bigl(x-(1+\kappa)z+u(\tau)\bigr),\\
w'&=-w,\\
y&=x.
\end{aligned}
$$

초기조건은 $q(0)=0$이다. $w=0$은 불변이므로 수치 witness는 정확히 그
2차원 invariant subsystem만 적분한다. 이는 ambient 공간을 유한차원으로 바꾸는 것이
아니라, 고정된 무한 spectator block에는 미지수가 없음을 이용하는 것이다.

각 고정 $\theta$에서 $G_\theta$는 strong metric이고, 수치 탐색의 compact 구간
$[-1.5,1.5]$에서는 coercivity 상수도 균일하다.

**[정리 후보 W1: 명시적 탈출 witness]** $u(\tau)=u_0\ne0$가
$[0,\epsilon)$에서 상수이면

$$
y'(0+)=0,
\qquad
y''(0+)=e^{-\theta}u_0,
\qquad
\theta=-\log\!\left(\frac{y''(0+)}{u_0}\right).
$$

여기서 두 미분은 계단 입력에 대한 우미분이다. 따라서 정확한 연속 출력에서는 이 한
매개변수족이 전역 식별된다. log의 인자는 양의
무차원 비율이다. 반면 $u\equiv0$, $q(0)=0$이면 모든 $\theta$에서 $y\equiv0$이므로
Gramian은 0이고 식별은 실패한다. 이 active/passive 쌍이 no-go의 가정을 실제로 무엇이
깨는지 보여야 한다.

## 6. 동결된 수치 검증

수치 검증은 증명의 대체물이 아니라 W1의 결정론적 재현 영수증이다. 경험적 뇌 데이터는
사용하지 않는다.

- 참값: $\theta_*\in\{-1.20,-0.40,0.30,1.10\}$.
- 시간: $T=4.0$, $\Delta\tau=0.005$, 모든 경계는 grid에 정렬한다.
- 적분: 각 step에서 입력이 상수인 4차 Runge--Kutta 선형 전이식을 사용한다.
- TRAIN-A: $u=1.0$ on $[0,0.60)$, $u=-0.30$ on $[1.50,2.00)$, 나머지 0.
- TRAIN-B: $u=-0.70$ on $[0.30,1.00)$, $u=0.90$ on $[2.20,3.00)$, 나머지 0.
- HOLDOUT-C: $u=0.50$ on $[0,0.40)$, $u=-1.00$ on $[1.00,1.70)$,
  $u=0.25$ on $[3.00,3.50)$, 나머지 0.
- NEGATIVE-ZERO: TRAIN과 같은 시간·초기조건에서 $u\equiv0$.
- 추정: $[-1.5,1.5]$의 241점 고정 grid에서 TRAIN-A/B 합동 SSE 최소점을 찾고,
  인접 grid 간격 안에서 80회 golden-section refinement를 수행한다. tie는 더 작은
  $\theta$를 택한다. 다른 model selection은 금지한다.
- 민감도: $h=10^{-5}$ 중앙차분으로 TRAIN-A/B의 $S=\partial y/\partial\theta$를
  계산하고 $\widehat{\mathcal I}=\sum_{e,n}S_{e,n}^2\Delta\tau$로 적분한다.

**DATA_SPLIT:** TRAIN-A/B만 매개변수 추정에 사용하며 HOLDOUT-C는 추정 완료 후 1회
평가한다. NEGATIVE-ZERO는 음성 대조군이며 추정 성능 점수에 합치지 않는다.

**OBSERVABLES:** 각 참값의 절대 매개변수 오차, HOLDOUT-C normalized squared error,
active Gramian, NEGATIVE-ZERO Gramian, NEGATIVE-ZERO의 grid-loss 범위.

HOLDOUT normalized squared error는

$$
E_{\rm hold}
=\frac{\|y_{\widehat\theta}-y_{\theta_*}\|_2^2}
{\max(\|y_{\theta_*}\|_2^2,10^{-12})}
$$

로 고정한다. 모든 항은 무차원이다.

**PASS 조건:** 네 참값 모두에서 동시에

$$
|\widehat\theta-\theta_*|\le10^{-6},
\qquad E_{\rm hold}\le10^{-10},
\qquad \widehat{\mathcal I}>10^{-8},
$$

이고, NEGATIVE-ZERO에서

$$
\widehat{\mathcal I}\le10^{-20},
\qquad
\max_\theta\mathcal L_0(\theta)-\min_\theta\mathcal L_0(\theta)\le10^{-20}
$$

여야 한다. 한 항이라도 실패하면 synthetic witness 검증은 STOP이다.

## 7. 뇌/AGI 사전등록 필드

- **BIO_STARTING_MECHANISM:** NONE. 이 run은 생물학적 시냅스·막전압 모델이 아니라
  metric-coupled gradient flow의 수학·합성 witness다.
- **CE_DELTA:** finite passive no-go에 대해 gauge-fixed finite metric family, known
  dynamics, intervention, positive-definite sensitivity Gramian이라는 충분조건을 추가한다.
- **MEASUREMENT_MODEL:** 정확한 무차원 synthetic output $y=x$; 잡음, 전극 mixing,
  volume conduction, hemodynamics는 모델링하지 않는다.
- **DATA_PROVENANCE:** 저장된 외부 데이터 없음. 동결된 식과 입력으로 로컬에서 생성하는
  결정론적 궤적만 사용한다.
- **DATA_SPLIT:** 위 TRAIN-A/B, HOLDOUT-C, NEGATIVE-ZERO를 따른다.
- **OBSERVABLES:** 위의 parameter error, holdout error, active/control Gramian, control
  loss range만 사용한다.
- **RESIDUAL_RULE:** TRAIN 합동 SSE로만 적합하고 HOLDOUT residual은 판정에만 사용한다.
- **FALSIFIER:** T3 증명의 반례, W1 미분식의 오류, 무차원성 실패, 또는 동결된 PASS 조건
  하나의 실패.
- **MATCHED_CONTROLS:** 같은 상태·시간·적분기에서 입력만 0으로 둔 NEGATIVE-ZERO.
- **MODEL_SELECTION:** 단일 동결 모델, 고정 grid + golden refinement뿐이다.
- **REVISION_TRIGGER:** 실패 뒤 식·입력·문턱을 이 run에서 조정하지 않는다. 원 판본을
  STOP으로 닫고 새 CE_RUN에서 구조 변경 하나만 사전등록한다.
- **CLAIM_CEILING:** `MATHEMATICAL_LOCAL_IDENTIFIABILITY_WITHIN_A_GAUGE_FIXED_FINITE_METRIC_FAMILY / DETERMINISTIC_SYNTHETIC_INTERVENTION_WITNESS / INFINITE_AMBIENT_SPACE_ALLOWED_BUT_NOT_RECOVERED / NO_EMPIRICAL_BRAIN_CONSCIOUSNESS_SELF_OR_AGI_VALIDATION`.

## 8. 해석 금지선

다음은 결과와 무관하게 이 run에서 주장하지 않는다.

1. 임의의 무한차원 ambient metric 또는 ambient dimension을 유한 데이터로 복원했다.
2. 실제 뉴런 연결의 간선·세기·막전압 법칙이 위 gradient flow와 같다.
3. 의식이 4차원 또는 임의의 유효차원으로 고정된다.
4. 자아가 궤적 길이이고 해마가 hash라는 가설이 검증되었다.
5. 합성 식별성이 EEG, fMRI, 단일세포 기록 또는 AGI 설계를 검증한다.
