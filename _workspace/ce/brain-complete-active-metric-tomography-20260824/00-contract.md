# BA-OBS-ID2 연구 계약 — 완전 능동 probe에 의한 무한차원 계량 tomography

Status: COMPLETE

Mode: full mathematics + deterministic synthetic operator-tomography witness

PREDECESSOR: _workspace/ce/brain-finite-observation-metric-identifiability-escape-20260824

CE_RUN: _workspace/ce/brain-complete-active-metric-tomography-20260824

## 1. 질문과 목표

BA-OBS-NOGO1은 finite passive observation이 arbitrary ambient metric을 식별하지
못한다는 정리다. BA-OBS-ID1은 gauge-fixed finite metric family와 informative
intervention 아래 positive-definite sensitivity Gramian이 local family-coordinate
identifiability를 보장함을 증명했다. 이번 run은 다음 두 제한을 더 제거한다.

1. 매개변수 공간을 유한차원으로 제한하지 않는다.
2. 결론을 국소 단사성에 제한하지 않는다.

질문은 다음과 같다.

> 실 separable Hilbert 공간의 임의 bounded strong metric에 대해, 알려진 능동
> force를 가하고 onset response를 완전하게 읽을 수 있다면 metric 전체를 전역적으로
> 유일하게 복원할 수 있는가? 유한하고 noisy한 probe에서는 무엇을 오차경계와 함께
> 복원할 수 있는가?

참인 finite-passive no-go는 삭제하지 않는다. 이 run에서 no-go가 사라지는 regime은
정확한 countably complete active response를 사용할 때뿐이다.

## 2. 선행 증거 동결

| 선행 산출 | SHA-256 | 판정 | 보존하는 주장 | 이번 run의 추가점 |
|---|---|---|---|---|
| BA-OBS-ID1 contract | 224c2a6701144cca089dd2a60054e443401b8ec4a1c28095281b947e412fbdc1 | PASS | finite-family active escape의 정의역과 금지선 | arbitrary strong metric으로 정의역을 넓힌다. |
| BA-OBS-ID1 math | 982574ca384336329a557249e58304d102d2711c979b05468b004cc7be05573f | PASS | $\mathcal I\succ0$이면 local injectivity | global monotonicity와 complete active tomography를 별도로 증명한다. |
| BA-OBS-ID1 audit | 66d8334b0d5c844569ae7aac85b38238a79787448c6f7a036d423abb5a01f361 | PASS | no-go와 finite-family escape의 양립 | finite probe의 남는 kernel을 계속 보존한다. |
| BA-OBS-ID1 validation | c74e50ef601904dead2ee1729685fe4e5f9ff34c69d4dcbd421141f8907bfe20 | PASS | four-truth synthetic trajectory recovery | 다른 mechanism인 operator tomography를 새로 검증한다. |
| BA-OBS-ID1 final | d4d0ce3992f302a1fea3a75ede6fa27bfb1331c14fdbed65ab5e23135757550b | PASS | local finite-family claim ceiling | finite-family/locality restriction을 제거하되 active-completeness 가정을 전면화한다. |
| brain route ledger | 4534e4313d190253adfbce50196b17e9305330345ea11dc9eaeeea3ce04310f0 | PASS | 현재 주장·수치·금지선 | BA-OBS-ID2 완료 뒤 별도 행으로만 추가한다. |

동일한 finite passive map, finite feature rank, EEG channel count 또는 finite probe만으로
arbitrary metric을 정확 복원한다고 주장하는 경로는 선행 no-go 때문에 금지한다.

## 3. 무차원화와 active response model

**[정의]** 실제 상태·시간·force를 기준 스케일 $q_*$, $t_*$, $f_*$로 나누어

$$
\bar q=\frac{q_{\rm phys}}{q_*},
\qquad
\tau=\frac{t}{t_*},
\qquad
\bar f=\frac{f_{\rm phys}}{f_*}
$$

로 둔다. 이후 bar는 생략한다. 물리 mobility를 $M_{\rm phys}$라 하면

$$
M=\frac{t_*f_*}{q_*}M_{\rm phys},
\qquad
G=M^{-1}
$$

로 정의한다. 따라서 $q$, $\tau$, $f$, $M$, $G$는 모두 무차원이다.

**[정의]** $\mathcal H$는 실 separable Hilbert 공간이고
$(e_n)_{n\ge1}$은 고정된 complete orthonormal basis다. 미지 metric은

$$
g_-I\preceq G\preceq g_+I,
\qquad
0<g_-\le g_+<\infty
$$

를 만족하는 arbitrary bounded, self-adjoint, coercive operator다. Mobility
$M=G^{-1}$는

$$
m_-I\preceq M\preceq m_+I,
\qquad
m_-=\frac1{g_+},
\qquad
m_+=\frac1{g_-}
$$

를 만족한다.

**[공리: 합성 측정모형 A1]** 각 질의 $f$마다 서로 독립적으로 같은 reset state를
준비하고, 알려진 constant linear potential

$$
V_f(q)=-\langle f,q\rangle
$$

를 가하면 metric gradient flow의 onset velocity는

$$
q'(0+)=M f
$$

이고, apparatus는 다음 scalar response를 정확히 읽는다.

$$
Q_G(f)=\langle f,q'(0+)\rangle
=\langle f,Mf\rangle.
$$

$Q_G$는 무차원이다. T5의 완전 식별은 countable set $\mathscr D$의 **모든**
$f$에 대해 이 reset과 exact onset readout을 수행할 수 있다는 이상적 완전성 가정을
포함한다. A1은 실제 뇌에서 확립된 측정모형이 아니라 이 수학·합성 tomography
run의 독립 공리다.

## 4. 증명할 일반 전역 정리

**[정리 후보 T4: fixed readout 아래 global stable identifiability]**
$\mathcal X,\mathcal Y$를 실 Hilbert 공간, $\Theta\subset\mathcal X$를 열린 convex
집합, $\Phi:\Theta\to\mathcal Y$를 $C^1$ map이라 하자. Bounded linear readout
$L:\mathcal Y\to\mathcal X$와 $\mu>0$가 존재하여 모든 $\vartheta\in\Theta$와
$h\in\mathcal X$에 대해

$$
\left\langle D(L\circ\Phi)_\vartheta h,h\right\rangle
\ge\mu\|h\|_{\mathcal X}^2
$$

이면 모든 $\vartheta_1,\vartheta_2\in\Theta$에 대해

$$
\|\Phi(\vartheta_1)-\Phi(\vartheta_2)\|_{\mathcal Y}
\ge
\frac{\mu}{\|L\|}
\|\vartheta_1-\vartheta_2\|_{\mathcal X}
$$

가 성립한다. 따라서 $\Phi$는 전역 단사이고 inverse는 image 위에서 Lipschitz다.
이 정리는 $\mathcal X$가 무한차원이어도 성립해야 한다.

증명 의무는 line segment 위 Banach-space fundamental theorem of calculus와
Cauchy--Schwarz만으로 닫는다. $L=0$은 $\mu>0$와 양립할 수 없으므로 별도
경계 문제가 아니다.

## 5. 임의 strong metric의 complete active tomography

**[정의]** countable active query set을

$$
\mathscr D=
\{e_i:i\ge1\}
\cup
\{e_i+e_j,e_i-e_j:1\le i<j<\infty\}
$$

로 둔다.

**[정리 후보 T5: global arbitrary-metric tomography]** 두 strong metrics
$G_1,G_2$가 A1 아래 모든 $f\in\mathscr D$에 대해 같은 response를 만들면
$G_1=G_2$다. 각 mobility matrix coefficient는

$$
\langle e_i,Me_i\rangle=Q_G(e_i),
$$

$$
\langle e_i,Me_j\rangle
=\frac14\left[
Q_G(e_i+e_j)-Q_G(e_i-e_j)
\right],
\qquad i<j,
$$

로 복원된다. 따라서 countably complete exact active response는 finite-family prior
없이 arbitrary strong metric을 전역적으로 유일하게 식별한다.

증명 의무는 real polarization identity, complete basis, bounded-operator continuity,
$M=G^{-1}$의 유일성을 모두 명시하는 것이다.

## 6. 유한 probe 절단과 수렴

**[정의]** $P_N$을 $\operatorname{span}\{e_1,\ldots,e_N\}$으로의 orthogonal
projection이라 한다. 첫 $N$개 방향에 대한 정확히 $N^2$개 scalar query로
$P_NMP_N$을 복원하고, 다음 completion을 정의한다.

$$
M_N=P_NMP_N+(I-P_N),
\qquad
G_N=M_N^{-1}.
$$

**[따름정리 후보 C3: strong recovery]** 각 $M_N$은 uniformly bounded and
coercive이며

$$
M_N\xrightarrow[N\to\infty]{\rm strong}M,
\qquad
G_N\xrightarrow[N\to\infty]{\rm strong}G.
$$

Operator-norm convergence는 추가 compactness/decay 없이 주장하지 않는다.

**[정의]** $B=M-I$의 basis coefficient를 $b_{ij}=\langle e_i,Be_j\rangle$라
한다. 어떤 $s>0$와 dimensionless $C_s<\infty$에 대해

$$
\sum_{i,j\ge1}
\bigl(1+\max\{i,j\}\bigr)^{2s}|b_{ij}|^2
\le C_s^2
$$

인 weighted Hilbert--Schmidt decay를 추가 가정한다.

**[따름정리 후보 C4: finite/noisy bound]** 각 scalar query에

$$
|\widehat Q(f)-Q_G(f)|\le\varepsilon
$$

인 dimensionless absolute error가 있다고 하자. 대각 coefficient error는
$\varepsilon$, off-diagonal error는 $\varepsilon/2$ 이하이므로

$$
\eta_N
=\varepsilon
\sqrt{
N+\frac{N(N-1)}4
}
$$

가 raw $N\times N$ mobility block의 Hilbert--Schmidt error 상계다. 이때
polarization으로 얻은 하나의 off-diagonal 추정값을 $(i,j)$와 $(j,i)$ 성분에 같이
넣어 raw block을 명시적으로 대칭화한다. 이 대칭 raw block을 Frobenius norm에서
알려진 interval $[m_-,m_+]$로 spectral clipping한 뒤 identity tail로 연장한
operator를 $\widetilde M_N$, 그 inverse를 $\widetilde G_N$이라 하자. Clipping은
측정된 $N\times N$ block에만 적용한다. 따라서 전체 identity-tail completion의
spectral bound는 일반적으로 $[m_-,m_+]$가 아니라
$[\min(1,m_-),\max(1,m_+)]$다. 다음 경계를 증명한다.

$$
\|\widetilde M_N-M\|_{\rm op}
\le
\eta_N+\frac{C_s}{(N+1)^s},
$$

$$
\|\widetilde G_N-G\|_{\rm op}
\le
g_+\max(1,g_+)
\left[
\eta_N+\frac{C_s}{(N+1)^s}
\right].
$$

Fixed $\varepsilon>0$에서는 $\eta_N$이 증가하므로 무조건 수렴한다고 주장하지 않는다.
Exact query이거나 $\eta_N\to0$이 되도록 반복측정 오차가 줄고 truncation tail도
사라질 때만 operator-norm recovery가 따른다.

## 7. 동결된 infinite-support rank-one witness와 수치 검증

**[정의]** $\mathcal H=\ell^2$에서

$$
r=0.60,
\qquad
\beta=0.50,
\qquad
v_n=\sqrt{1-r^2}\,r^{n-1}
$$

로 둔다. $\|v\|=1$이고

$$
M=I+\beta\,v\otimes v,
\qquad
G=M^{-1}
=I-\frac{\beta}{1+\beta}\,v\otimes v.
$$

이는 finite-dimensional truncation이 아니라 genuine infinite-support rank-one
perturbation이다. Strong bounds는

$$
I\preceq M\preceq1.5I,
\qquad
\frac23I\preceq G\preceq I
$$

다. Exact response generator는

$$
Q_G(f)=\|f\|^2+\beta\langle v,f\rangle^2
$$

다.

검증 grid는 결과를 보기 전에 다음과 같이 고정한다.

- truncation sizes: $N\in\{4,8,16,32\}$;
- exact query count: 각 $N$에서 $N^2$;
- query order: $e_1,\ldots,e_N$ 뒤에 lexicographic $i<j$ 순서로
  $e_i+e_j$, $e_i-e_j$를 연속 배치한다;
- deterministic query noise: 0-based query index $k$에서
  $\delta Q_k=10^{-8}(-1)^k$;
- tail-orthogonal unit vector와 finite-invisibility adverse metric:

  $$
  w_N=\frac{r e_{N+1}-e_{N+2}}{\sqrt{1+r^2}},
  \qquad
  M^{\rm alt,N}=M+0.10\,w_N\otimes w_N;
  $$
- exact reconstruction tolerance: $10^{-12}$;
- analytic tail endpoint: $N=32$에서 mobility와 metric HS error 모두 $10^{-7}$ 이하;
- noisy raw/clipped block error는 $\eta_N+10^{-12}$ 이하;
- clipped mobility eigenvalues는 $[1,1.5]$ 안;
- finite-invisibility control은 첫 $N^2$ query에서 response 차이 $10^{-14}$ 이하,
  held-out $w_N$ query에서 차이 $0.10\pm10^{-12}$;
- exact mobility/metric HS tail은 $N=4,8,16,32$에서 strict decreasing.

Rank-one analytic tail은 cancellation을 피하도록 다음 식으로 평가한다. 먼저

$$
a_N=\|P_Nv\|^2=1-b_N,
\qquad
b_N=r^{2N},
\qquad
c=\frac{\beta}{1+\beta},
\qquad
c_N=\frac{\beta}{1+\beta a_N}
$$

라 하면

$$
\|M-M_N\|_{\rm HS}
=\beta\sqrt{2b_N-b_N^2},
$$

$$
\|G-G_N\|_{\rm HS}
=c\sqrt{
2a_Nb_N+b_N^2+
\frac{\beta^2a_N^2b_N^2}{(1+\beta a_N)^2}
}.
$$

두 식은 각각 $\beta\sqrt{1-a_N^2}$ 및
$a_N^2(c-c_N)^2+2c^2a_Nb_N+c^2b_N^2$의 제곱근과 대수적으로 같지만,
$b_N\ll1$일 때 $1-a_N^2$와 $c-c_N$을 직접 빼서 생기는 floating-point
cancellation을 피한다.

한 gate라도 실패하면 synthetic witness는 STOP이며 식·noise·$N$·threshold를 같은
run에서 바꾸지 않는다.

## 8. 뇌/AGI 사전등록 필드

- **BIO_STARTING_MECHANISM:** NONE. A1은 실제 neural membrane/synapse 식이 아니라
  abstract metric-gradient onset experiment다.
- **CE_DELTA:** finite-family local Gramian theorem을 arbitrary strong metric의
  countably complete global active tomography와 finite/noisy error bound로 확장한다.
- **MEASUREMENT_MODEL:** reset, known dimensionless force, exact/noisy scalar onset
  power $Q_G(f)=\langle f,Mf\rangle$.
- **DATA_PROVENANCE:** 외부 데이터 없음. analytic rank-one $\ell^2$ generator와
  deterministic noise만 사용한다.
- **DATA_SPLIT:** first-$N$ basis queries는 reconstruction, tail-orthogonal $w_N$은
  completeness/adverse-control probe다. $N$ menu는 사전 고정한다.
- **OBSERVABLES:** exact/noisy block error, mobility/metric HS tail, spectral bounds,
  finite-invisibility response equality, next-basis response gap.
- **RESIDUAL_RULE:** coefficient residual과 analytic operator-tail 식만 사용하며
  결과 후 다른 norm이나 completion으로 바꾸지 않는다.
- **FALSIFIER:** T4/T5/C3/C4의 반례, A1 유도 오류, dimensionless failure, 또는
  synthetic gate 하나의 실패.
- **MATCHED_CONTROLS:** $M$과 $M^{\rm alt,N}$의 first-$N$ identical response 및
  tail-orthogonal held-out distinguishing response. $w_N\perp v$이므로 두 mobility는
  모두 $I\preceq M\preceq1.5I$ class 안에 남는다.
- **MODEL_SELECTION:** 단일 rank-one infinite-support witness, 고정 $N$ menu,
  고정 spectral interval; selection 없음.
- **REVISION_TRIGGER:** 실패 시 원 run을 STOP으로 닫고 새 run에서 구조 변경 하나만
  사전등록한다. 같은 receipt에 맞춘 threshold/noise/basis/metric 변경은 금지한다.
- **CLAIM_CEILING:** GLOBAL_IDENTIFICATION_OF_AN_ARBITRARY_STRONG_METRIC_UNDER_COUNTABLY_COMPLETE_ACTIVE_QUADRATIC_RESPONSE / GLOBAL_STABLE_IDENTIFIABILITY_UNDER_UNIFORM_STRONG_MONOTONICITY / STRONG_OPERATOR_RECOVERY_AND_HS_FINITE_NOISY_BOUND / FINITE_PASSIVE_AND_FINITE_EXACT_FULL_RECOVERY_STILL_IMPOSSIBLE / SYNTHETIC_ONLY / NO_EMPIRICAL_BRAIN_CONSCIOUSNESS_SELF_OR_AGI_VALIDATION.

## 9. 해석 금지선

결과와 무관하게 다음은 주장하지 않는다.

1. 유한한 EEG·fMRI·전극·feature가 arbitrary brain metric을 정확 복원한다.
2. 실제 뇌에서 arbitrary basis force를 reset 상태에 가할 수 있거나 onset velocity를
   완전 측정할 수 있다.
3. Countably infinite exact experiment가 finite laboratory data로 이미 수행됐다.
4. Basis choice가 생물학적으로 canonical하거나 neuron edge와 일대일이다.
5. Metric dimension, 숫자 $4$, consciousness, self, hippocampal hash 또는 AGI
   구조가 식별됐다.
6. Strong/operator-norm convergence가 곧 물리적 진실 또는 통계적 consistency다.
