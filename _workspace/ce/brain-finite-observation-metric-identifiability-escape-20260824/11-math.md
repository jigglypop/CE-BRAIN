# BA-OBS-ID1 mathematics lane — 동역학적 식별성 탈출 정리

Status: COMPLETE

Verdict: PASS after math-verifier revision 1

P0: none.  
P1: none after scope correction.

## 1. 감사한 가정

계약의 매개변수 정의역 $\Theta\subset\mathbb R^p$는 참값 $\vartheta_*$를 포함하는
열린 집합이다. 닫힌 구간 $[-1.5,1.5]$는 수치 optimizer의 탐색 범위일 뿐 T3의
정의역이 아니다. 가중행렬 $R_e:[0,T_e]\to\mathbb R^{r_e\times r_e}$는 강측정
가능하고 대칭이며, $\vartheta$와 무관하게 고정되고

$$
0<r_-I\preceq R_e(\tau)\preceq r_+I<\infty
$$

를 만족한다. 따라서

$$
\langle f,g\rangle_{\mathcal Y,R}
=\sum_e\int_0^{T_e}f_e(\tau)^\top R_e(\tau)^{-1}g_e(\tau)\,d\tau
$$

는 표준 $L^2$ 내적과 동치인 Hilbert 내적이다. Forward map
$\Phi:\Theta\to\mathcal Y$가 이 위상에서 $C^1$이라는 가정은 알려진 동역학의
well-posedness와 parameter differentiability를 포함한다.

## 2. [정리 T3] 양의 정부호 Gramian은 국소 구조 식별성을 보장한다

**명제.** 계약의 가정 아래 $\mathcal I(\vartheta_*)\succ0$이면
$\Phi$는 $\vartheta_*$의 어떤 근방에서 단사다. 식별 대상은 gauge가 고정된 유한
계량족의 좌표뿐이다.

**증명.** 다음 bounded derivative를 둔다.

$$
A:=D\Phi_{\vartheta_*}:\mathbb R^p\longrightarrow\mathcal Y.
$$

표준기저를 $e_a$라 하면 $Ae_a$의 실험 $e$ 성분은 민감도 열
$S_{e,\cdot a}$다. 따라서 모든 $v\in\mathbb R^p$에 대해

$$
\begin{aligned}
\|Av\|_{\mathcal Y,R}^2
&=\sum_e\int_0^{T_e}
v^\top S_e(\tau)^\top R_e(\tau)^{-1}S_e(\tau)v\,d\tau\\
&=v^\top\mathcal I(\vartheta_*)v.
\end{aligned}
$$

즉 Euclidean–weighted-Hilbert adjoint를 쓰면

$$
\mathcal I(\vartheta_*)=A^*A.
$$

$\mathcal I\succ0$이므로 $Av=0$이면 $v=0$이고 $A$는 단사다. 이제

$$
L:=\mathcal I(\vartheta_*)^{-1}A^*:\mathcal Y\longrightarrow\mathbb R^p
$$

를 정의한다. $A^*$와 유한행렬 $\mathcal I^{-1}$가 bounded이므로 $L$도 bounded이고

$$
LA=\mathcal I^{-1}A^*A=I_p.
$$

$\Psi:=L\circ\Phi:\Theta\to\mathbb R^p$는 $C^1$이며
$D\Psi_{\vartheta_*}=I_p$다. 유한차원 inverse function theorem에 따라
$\vartheta_*$의 어떤 열린 근방 $U$에서 $\Psi|_U$가 단사다. 만약
$\vartheta_1,\vartheta_2\in U$에서 $\Phi(\vartheta_1)=\Phi(\vartheta_2)$이면
$\Psi(\vartheta_1)=\Psi(\vartheta_2)$이고, 따라서
$\vartheta_1=\vartheta_2$다. 그러므로 $\Phi|_U$도 단사다. $\square$

이 증명은 무한차원 출력공간에 역함수정리를 직접 적용하지 않는다. 유한 매개변수의
민감도 span을 읽는 bounded map $L$로 먼저 $\mathbb R^p$에 내린 뒤 보통의
역함수정리를 적용한다.

## 3. [따름정리 C2] zero-residual loss의 고립 국소 최소점

$\Phi$가 $C^2$이고

$$
\mathcal L(\vartheta)
=\frac12\|\Phi(\vartheta)-\Phi(\vartheta_*)\|_{\mathcal Y,R}^2
$$

라고 하자. $r(\vartheta)=\Phi(\vartheta)-\Phi(\vartheta_*)$로 두면 좌표별로

$$
\partial_a\mathcal L
=\langle\partial_a\Phi,r\rangle_{\mathcal Y,R},
$$

$$
\partial_{ab}^2\mathcal L
=\langle\partial_a\Phi,\partial_b\Phi\rangle_{\mathcal Y,R}
+\langle\partial_{ab}^2\Phi,r\rangle_{\mathcal Y,R}.
$$

참값에서는 $r(\vartheta_*)=0$이므로 두 번째 항이 사라지고

$$
\nabla^2\mathcal L(\vartheta_*)=A^*A=\mathcal I(\vartheta_*).
$$

T3의 조건이면 Hessian이 양의 정부호이므로 표준 2차 충분조건에 따라
$\vartheta_*$는 고립된 strict local minimizer다. 잔차가 0이 아닐 때는
$\langle\partial_{ab}^2\Phi,r\rangle$ 항을 버릴 수 없으므로 이 등식은 주장하지 않는다.

## 4. [경계] singular Gramian이 뜻하는 것

$\mathcal I$는 항상 positive semidefinite이고

$$
v^\top\mathcal I v=0\quad\Longleftrightarrow\quad Av=0.
$$

따라서 singularity는 어떤 $v\ne0$에 대해

$$
\Phi(\vartheta_*+sv)=\Phi(\vartheta_*)+o(s)
$$

인 일차 blind direction이 있다는 뜻이다. 이것은 양의 정부호 충분조건의 실패이지
전역 또는 고차 비식별성의 증명이 아니다. 예를 들어
$\Phi(\theta)=\theta^3$은 $\theta_*=0$에서 Gramian이 0이지만 국소 단사다.

## 5. [정리 W1] 무한차원 ambient 공간의 구성적 탈출 witness

상태공간과 metric을

$$
\mathcal H=\mathbb R^2\oplus\ell^2,
\qquad
G_\theta=\operatorname{diag}(1,e^\theta)\oplus I_{\ell^2}
$$

로 둔다. 각 고정 $\theta\in\mathbb R$에서 $G_\theta$는 bounded,
self-adjoint, coercive이고

$$
\min(1,e^\theta)\|h\|^2
\le\langle h,G_\theta h\rangle
\le\max(1,e^\theta)\|h\|^2.
$$

수치 구간에서는 하한 $e^{-1.5}\approx0.223130$과 상한
$e^{1.5}\approx4.481689$가 모든 $\theta$에 공통이다. Potential의 $(x,z)$ Hessian은

$$
\begin{pmatrix}1&-1\\-1&1+\kappa\end{pmatrix}
$$

이고 leading principal minor가 1, determinant가 $\kappa=0.30>0$이므로 양의
정부호다. $w$ block Hessian은 identity다.

$u\in L^\infty([0,T])$에서 벡터장은 상태에 대해 bounded linear이고 시간에 대해
measurable forcing이므로 유일한 absolutely-continuous Carathéodory 해가 존재한다.
Hilbert 기준 gradient는

$$
\nabla V_u=(x-z,(1+\kappa)z-x-u,w)
$$

이므로 $q'=-G_\theta^{-1}\nabla V_u$는

$$
x'=z-x,
\qquad
z'=e^{-\theta}\bigl(x-(1+\kappa)z+u\bigr),
\qquad
w'=-w.
$$

$w(0)=0$이면 $w(\tau)=0$이므로 2차원 subsystem은 무한차원 모델의 정확한 invariant
restriction이다. $u(\tau)=u_0\ne0$가 0의 오른쪽 근방에서 상수이고
$x(0)=z(0)=0$이면 우미분으로

$$
y'(0+)=x'(0+)=0,
$$

$$
y''(0+)=z'(0+)-x'(0+)=e^{-\theta}u_0.
$$

따라서

$$
\boxed{\theta=-\log\!\left(\frac{y''(0+)}{u_0}\right)}
$$

이고 비율은 부호가 같은 두 무차원량의 양의 비율이다. 이 exact continuous-output
witness에서는 $\theta\mapsto y$가 전역 단사다. 또한 0 근방에서

$$
\frac{\partial y(\tau;\theta)}{\partial\theta}
=-\frac12e^{-\theta}u_0\tau^2+O(\tau^3),
$$

이므로 active input의 scalar sensitivity는 양의 길이 구간에서 0이 아니고 Gramian은
양수다. 반대로 $u\equiv0$, $q(0)=0$이면 유일해가 $q\equiv0$이므로 모든 $\theta$에서
$y\equiv0$, $S\equiv0$, $\mathcal I=0$이다.

## 6. 무차원성 감사

| 식 | 감사 결과 |
|---|---|
| $e^\theta$ | $\theta$는 log metric ratio이므로 무차원이다. |
| $q'=-G^{-1}\nabla V$ | $\tau=t/t_*$와 $x,z,w,u,V,G$를 기준 스케일로 정규화했다. |
| $\mathcal I=\int S^\top R^{-1}S\,d\tau$ | $S,R,\tau$가 모두 무차원이므로 Gramian도 무차원이다. |
| $-\log(y''(0+)/u_0)$ | $\tau$가 무차원이므로 $y''$와 $u_0$는 같은 정규화 단위를 가지며 비율은 양의 무차원량이다. |
| normalized holdout loss | 분자·분모가 같은 dimensionless squared-output norm이고 floor $10^{-12}$도 무차원이다. |

Dimensionless verdict: PASS.

## 7. no-go와의 양립 및 형식 지위

BA-OBS-NOGO1은 임의의 hidden metric block이 finite passive pointwise map에서 보이지
않는다고 증명했다. T3는 그 hidden block을 데이터만으로 복원하지 않는다. 모델 가정으로
metric을 gauge-fixed finite family에 제한하고, 알려진 dynamics와 intervention으로 family
coordinate가 출력 궤적에 나타날 때만 그 좌표를 국소 식별한다. W1의 무한 spectator
metric은 고정되어 있으며 복원 대상이 아니다.

- **[정리]** T3: 위 조건 아래 증명 완료.
- **[따름정리]** C2: zero-residual 및 $C^2$ 조건 아래 증명 완료.
- **[정리]** W1: exact continuous synthetic model에서 증명 완료.
- **[예측]** 동결된 discrete validator가 active recovery와 zero-input collapse를 함께
  재현할지는 구현 전 상태다.
- **[미완성]** 실제 neural dynamics가 이 metric family를 따르는지, 실제 개입에서
  Gramian이 양의 정부호인지, 의식·자아·AGI와 연결되는지는 전혀 검증되지 않았다.

Claim ceiling:
`MATHEMATICAL_LOCAL_IDENTIFIABILITY_WITHIN_A_GAUGE_FIXED_FINITE_METRIC_FAMILY / DETERMINISTIC_SYNTHETIC_INTERVENTION_WITNESS / INFINITE_AMBIENT_SPACE_ALLOWED_BUT_NOT_RECOVERED / NO_EMPIRICAL_BRAIN_CONSCIOUSNESS_SELF_OR_AGI_VALIDATION`.
