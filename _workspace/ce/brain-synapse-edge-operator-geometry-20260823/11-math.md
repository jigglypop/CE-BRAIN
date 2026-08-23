# BA-SRM4 수학 검증 — 간선 연산자 상태공간과 관측 몫

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-synapse-edge-operator-geometry-20260823`

## 결론 먼저

**[조건부 정리]** 적절히 완비한 간선별 history Hilbert 공간에서 유한 개의
whitened 관측을 미분하면 pullback은 양의 준정부호(PSD) 유한계수 연산자이며,
그 관측이 국소적으로 구별하는 것은 전체 상태가 아니라
$$
\mathscr H_E/\ker DM_x
$$
의 유한차원 몫이다. 따라서 이것은 무한차원 synapse-state 표현의 *가능한
정의*와 유한 관측의 식별 한계를 함께 주지만, 무한차원 SPD Riemann metric의
복원이나 생물학적 기전의 증명은 주지 않는다.

아래 조건을 만족할 때에만 ``간선 속성이 관측 차원을 하나 더 늘린다''는 말을
쓸 수 있다: 그 속성의 whitened sensitivity가 기존 속성 sensitivity들의 닫힌
선형공간 밖에 있어야 한다. 단순히 새 열을 추가하거나 raw coefficient 수가
늘어나는 것은 충분하지 않다.

## 1. 정의와 전제의 고정

간선 집합 $E$는 이번 데이터 분석에서는 유한하다고 둔다. 각 간선마다
$p_e,q_e<\infty$이고, $\rho:(-\infty,0]\to(0,\infty)$는 가측이며 거의 모든
곳에서 양수인 가중치라고 둔다. 다음과 같이 둔다.

$$
L^2_\rho=
\left\{h:(-\infty,0]\to\mathbb R^{q_e}:\int_{-\infty}^0\rho(s)\|h(s)\|_2^2\,ds<\infty\right\},
$$

$$
\langle h,k\rangle_\rho=\int_{-\infty}^0\rho(s)h(s)^\top k(s)\,ds,
\qquad
\mathcal H_e=\mathbb R^{p_e}\oplus L^2_\rho,
\qquad
\mathscr H_E=\bigoplus_{e\in E}\mathcal H_e.
$$

유한 $E$와 위의 양의 가중치 아래 $L^2_\rho$, 각 $\mathcal H_e$, 그리고
$\mathscr H_E$는 Hilbert 공간이다. $E$를 무한으로 확대하려면 direct sum은
$$
\left\{(x_e)_{e\in E}:\sum_e\|x_e\|_{\mathcal H_e}^2<\infty\right\}
$$
로 명시해야 하며, 단순 Cartesian product는 이 norm에서 Hilbert 상태공간이라는
결론을 주지 않는다. 또한 ``fading memory''는 $L^2_\rho$라는 표기만으로 자동
성립하지 않는다. 시간 이동 반군이 유계이고 과거가 멀어질수록 관측 함수가
연속적으로 약해진다는 별도 가정이 필요하다.

관측은 $M:U\subset\mathscr H_E\to\mathbb R^m$가 $x$에서 Fréchet 미분 가능,
$R(x)\in\mathbb R^{m\times m}$ 대칭 양의 정부호라고 가정한다. 이때
$$
A_x=R(x)^{-1/2}DM_x:\mathscr H_E\to\mathbb R^m,
\qquad
\mathcal G_x=A_x^*A_x=DM_x^*R(x)^{-1}DM_x.
$$

이는 local Gaussian measurement model의 Fisher-type information operator일 뿐,
실제 noise가 Gaussian이라는 생물학적 주장까지 포함하지 않는다.

## 2. 유한 관측 pullback과 quotient no-go

**정리 1 [조건부 정리].** 위 전제에서 $\mathcal G_x$는 self-adjoint PSD이고
rank$(\mathcal G_x)$=rank$(A_x)\le m$이다. 또한
$$
\ker\mathcal G_x=\ker A_x=\ker DM_x.
$$
따라서 $\mathcal G_x$가 정의하는 내적은 몫공간
$\mathscr H_E/\ker DM_x$에서만 양의 정부호이고, 그 차원은 rank$(DM_x)$ 이하이다.

*증명.* 임의의 $v\in\mathscr H_E$에 대해
$$
\langle v,\mathcal G_xv\rangle=\|A_xv\|_2^2\ge0.
$$
그러므로 PSD이다. 이 식의 좌변이 0일 필요충분조건은 $A_xv=0$이고,
$R^{-1/2}$가 가역이므로 $DM_xv=0$이다. $A_x$의 codomain이 $m$차원이어서
rank$(A_x)\le m$이며 $\ker(A_x^*A_x)=\ker A_x$로부터 rank 등식이 따른다.
동일한 coset에만 의존하는 quadratic form이 몫에 유도되고, 그 induced form은
kernel을 제거했으므로 양의 정부호이다. □

**따름정리 1 [no-go].** $\mathscr H_E$가 무한차원이고 $m<\infty$이면
$\ker DM_x$는 무한차원이다. 따라서 $\mathcal G_x$는 전체
$\mathscr H_E$에서 SPD일 수 없고, 어떤 유한-output experiment도 그 점에서
전체 history state의 국소 일대일 복원을 보장하지 못한다.

*이유.* finite-rank map의 quotient range는 유한차원이다. 무한차원 domain이
유한차원 quotient를 가지면 kernel은 무한차원이다.

**완전 반례 (전체 SPD 주장에 P0).** $\mathscr H=\ell^2$,
$M(x)=x_1$, $R=1$로 두면
$$
\mathcal G=\operatorname{diag}(1,0,0,\ldots).
$$
이는 history coefficient가 무한히 많아도 첫 계수만 보므로 $e_2,e_3,\ldots$에서
0이다. 따라서 ``무한 history space이므로 관측 pullback도 무한차원 Riemann
metric''이라는 부모 주장은 거짓이다. BA-SRM4 계약의 quotient 서술은 이 반례와
양립하며 유지된다.

관측 차원이 유한하지 않은 경우에도 no-go가 자동으로 사라지지 않는다. 예를 들어
compact injective $A:\ell^2\to\ell^2$, $A e_k=k^{-1}e_k$는 injective이나
$A^*A$의 고유값 $k^{-2}$가 0으로 수렴한다. inverse는 unbounded라 안정적인
SPD metric/복원 결론이 아니다. 따라서 ``더 많은 time samples''도 noise,
conditioning, measurement operator의 범위를 별도로 고정하지 않으면 탈출구가
아니다.

## 3. 간선 속성의 조건부 차원 증가

기존 속성 direction 집합을 $S\subset\mathscr H_E$, 새 속성 direction을
$u\in\mathscr H_E$라 하자. $z_v=A_xv\in\mathbb R^m$를 whitened sensitivity라
두면 다음이 성립한다.

**명제 2 [조건부 정리].** 기존 모델의 observable tangent span을
$\mathcal Z_S=\overline{\operatorname{span}}\{z_v:v\in S\}$라 두면, $u$를
추가한 hard observable rank는 정확히 다음일 때 하나 증가한다.
$$
z_u\notin\mathcal Z_S.
$$

*증명.* finite-dimensional codomain에서 span에 한 벡터를 추가할 때 rank 증가량은
0 또는 1이다. 그 벡터가 기존 span 밖이면 1, 안이면 0이다. closure는 향후
infinite output 또는 limiting basis로 일반화해도 같은 문장을 유지하려고 넣은
것이며, 현재 finite $m$에서는 ordinary span과 같다. □

이는 ``attribute가 정보 그 자체일 수 있다''는 직관의 측정가능한 형태다. 다만
direction $u$가 이미 선택한 chart/basis에 따라 바뀌므로, 속성별 기여는 사전
고정한 typed parameterization과 같은 group-conditional comparison 안에서만
보고한다.

**반례.** $M(a,b)=a+b$, $R=1$이면 두 raw attribute가 있어도
$z_{(1,0)}=z_{(0,1)}=1$이므로 rank는 1이다. 반대로 $M(a,b)=(a,b)$이면 rank는
2다. raw edge 수 또는 attribute 열 수는 observable dimension이 아니다.

## 4. hard rank, raw dimension, effective dimension

raw representation dimension은 저장한 coefficient/attribute 수이고, hard rank는
rank$(A_x)$이다. 둘은 encoding과 threshold에 의존해 다르다. noise-aware
effective dimension은 별도의, coordinate-gauge가 고정된 positive trace-class
operator $\widetilde G$에 대해서만 정의한다.

$$
d_{\rm eff}(\lambda)=\operatorname{Tr}\!\left[\widetilde G(\widetilde G+\lambda I)^{-1}\right]
=\sum_{k\ge1}\frac{\mu_k}{\mu_k+\lambda},
\qquad \lambda>0.
$$

여기서 $\mu_k\ge0$은 $\widetilde G$의 고유값이며, $\lambda$는 이 고유값과
동일한 무차원 information scale이다.

**정리 3 [조건부 정리].** $\widetilde G\succeq0$가 trace-class이면 위 급수는
유한하고
$$
0\le d_{\rm eff}(\lambda)\le\frac{\operatorname{Tr}(\widetilde G)}{\lambda},
$$
이며 $\lambda$에 대해 단조 감소한다. finite rank $r$이면
$d_{\rm eff}(\lambda)\le r$, $\lambda\downarrow0$에서 $r$로 수렴한다.

*증명.* $0\le\mu/(\mu+\lambda)\le\mu/\lambda$를 합하면 상한과 수렴이
따른다. 각 summand의 도함수는 $-\mu/(\mu+\lambda)^2\le0$이다. finite-rank의
0 아닌 항 각각은 1로 수렴한다. □

**P0 반례: trace-class 없는 경우.** $\widetilde G=I$ on $\ell^2$이면 모든
$\mu_k=1$이고
$$
\sum_{k=1}^\infty\frac1{1+\lambda}=\infty.
$$
따라서 계약의 `UNDEFINED_EFFECTIVE_DIMENSION` stop은 필수다. 유한 관측의
$A_x^*A_x$ 자체는 finite rank라 trace-class지만, history discretization을 바꾸어
reference whitening을 도입한 뒤의 $\widetilde G$가 자동으로 trace-class인 것은
아니다. 그 whitening/prior와 basis limit를 receipt로 고정해야 한다.

**좌표 불변성의 정확한 범위.** 동일 Hilbert metric을 보존하는 unitary rechart
$U$ 아래 $\widetilde G'=U^*\widetilde G U$이면 spectrum과
$d_{\rm eff}$는 불변이다. 일반 invertible rescaling $S$에서 단순히
$\widetilde G'=S^*\widetilde G S$로 바꾸면 고유값도 바뀌므로 불변이 아니다.
불변성을 원하면 parameter covariance/metric도 함께 push-forward하여 generalized
eigenvalue problem으로 바꾸거나, discovery fold에서 고정한 dimensionless reference
chart만 사용해야 한다. 이 점이 scale/rechart adverse control의 수학적 이유다.

**혼동 반례.** $n$개의 raw coefficient를 갖는
$A=(1,1,\ldots,1)\in\mathbb R^{1\times n}$은 raw dimension $n$, hard rank 1,
그리고 $\widetilde G=A^\top A$일 때
$$
d_{\rm eff}(\lambda)=\frac{n}{n+\lambda}.
$$
따라서 $n$을 차원이라고 보고하거나, $\lambda$를 바꾼 값을 hard rank라고
부르는 것은 모두 오류다.

## 5. 식 문법과 무차원성 감사

계약의 Volterra candidate
$$
M_o(h,c)=\beta_{o0}+\sum_a\beta_{oa}\Phi_a(h,c)
+\sum_{a\le b}\beta_{oab}\Phi_a(h,c)\Phi_b(h,c)
$$
는 다음 조건에서만 단위적으로 허용된다.

| 항 | 요구되는 무차원화 | 판정 |
|---|---|---|
| history time | $s/T_0$, lag $\tau/T_0$ | 필수 |
| IC command | $I/I_0$, 별도 type indicator | 필수 |
| VC command | $V/V_0$, 별도 type indicator | 필수 |
| voltage/current response | source-mode 별 $V/V_0$ 또는 $I/I_0$ | 필수 |
| exponential kernel | $\exp[-(s-\tau)/\theta]$에서 $s,\tau,\theta$ 모두 시간 또는 모두 $T_0$로 나눈 값 | 필수 |
| norm/RKHS penalty | reference Hilbert norm 또는 prior precision로 무차원화 | 필수 |
| $R^{-1/2}DM$ | output과 covariance를 같은 typed unit으로 whiten | 필수 |
| $\widetilde G,\lambda$ | 동일한 무차원 reference information scale | 필수 |

$\Phi_a$를 모두 무차원 causal basis로 고정하면 $M_o$도 standardized output일 때
$\beta$들은 무차원이다. 원 단위 output을 직접 쓰면 $\beta$는 output 단위를
가져야 하며 서로 다른 IC/VC 채널을 같은 coefficient로 묶을 수 없다. $\rho$의
단위는 $\int\rho(s)\|h(s)\|^2ds$가 dimensionless norm이 되도록 정한다. 예컨대
$h$가 이미 무차원이면 $\rho$는 $1/T$ 단위이며 $\rho(s)=T_0^{-1}\bar\rho(s/T_0)$로
써야 한다. 이에 실패하면 `STOP_DIMENSIONLESS`다.

## 6. 발견 사항과 재현 명령

- P0: 전체 history Hilbert 공간에서 strict SPD metric 또는 전체 상태 복원을
  주장하는 경로는 정리 1의 finite-rank no-go로 금지된다.
- P0: trace-class/reference chart를 receipt로 고정하지 않은 effective-dimension
  수치는 정의되지 않는다.
- P1: $\rho$가 fading memory를 실제로 유도하는 dynamical condition인지, 그리고
  $M$의 Fréchet differentiability가 해당 typed empirical feature map에서 성립하는지는
  source/schema/implementation lane이 확인해야 한다.
- P2: hard rank의 수치 cutoff는 수학적 rank가 아니다. singular-value threshold,
  bootstrap, group unit을 confirmation 전에 고정해야 한다.

위 선형대수 항등식은 다음 최소 계산으로 재현 가능하다(데이터 접근 불필요).

```powershell
.codex\hooks\python.cmd python -c "import numpy as np; A=np.ones((1,5)); G=A.T@A; print(np.linalg.matrix_rank(A), np.linalg.eigvalsh(G)); print(5/(5+1.0))"
```

기대 출력의 rank는 `1`, 고유값은 하나만 양수이며 $d_{\rm eff}(1)=5/6$이다.

