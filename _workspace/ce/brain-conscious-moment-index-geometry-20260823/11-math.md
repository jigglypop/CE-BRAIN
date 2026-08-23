# BA-SRM5 수학 검증 — history metric, rank-4 projection, index 한계

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-conscious-moment-index-geometry-20260823`

## 판정

**[조건부 정리]** 계약의 history-space metric, rank-4 Riesz projection, 그리고
4D quantized index는 각각 추가 전제 아래 잘 정의될 수 있다. 그러나 반복회로,
BA-SRM4의 finite-output hard rank 4, 혹은 hippocampal sparse address만으로
``의식 순간은 4차원'' 또는 lossless common 4D code라는 결론은 나오지 않는다.
현재는 데이터가 열리지 않은 conceptual run이므로 모든 생물학적 연결은
[공리: 물리 사상][미완성]이다.

## 1. countable history sum과 metric

각 vertex의 $p_v,q_e<\infty$ 및 양의 가측 $\rho$에 대해 countable $V,E$의 올바른
공간은 다음 $\ell^2$-direct sum이다.

$$
\mathcal H=\left\{(a_v,h_e):
\sum_{v\in V}\|a_v\|_2^2+
\sum_{e\in E}\int_{-\infty}^0\rho(\theta)\|h_e(\theta)\|_2^2d\theta<\infty\right\}.
$$

각 $L^2_\rho$는 Hilbert이고, 위 norm을 쓰면 countable direct sum도 Hilbert이다.
단순 product는 이 결론을 주지 않는다. ``fading memory''는 $\rho>0$만으로는
성립하지 않으며, time-shift semigroup의 유계성 및 멀어진 과거에 대한 observation
functional의 연속적 감쇠를 별도로 가정해야 한다.

**정리 1 [조건부].** $x\mapsto A_x$가 operator-norm에서 매끄럽고,
$A_x=A_x^*$이며 어떤 $0<m\le M<\infty$에 대해
$$
mI\preceq A_x\preceq MI
$$
이면 $g_x(u,v)=\langle u,A_xv\rangle_\mathcal H$는 strong Riemannian metric이다.
간선 합은 예를 들어 $\sum_e\|D_e^*K_e(x)D_e\|<\infty$가 국소적으로 균등해야
bounded self-adjoint operator로 수렴한다. 이보다 약하면 quadratic form으로만
정의될 수 있으며, metric이라고 부르지 않는다.

directed recurrent generator $L_x$는 보통 비자기수반이며 $L_x\ne L_x^*$일 수 있다.
따라서 방향성은 generator/flow에, 대칭 양의 metric은 $A_x$에 속한다. $L_x$ 또는
directed adjacency 자체를 $g$라고 부르면 symmetric bilinear Riemann metric의 정의를
위반한다.

## 2. rank-4 spectral/slow projection

$U_t^\Delta=D\Phi_{t,t+\Delta}(\xi_t)$가 bounded이고 $\Gamma_4$가 spectrum을
가르지 않는 resolvent contour이며 내부 spectral subspace의 algebraic multiplicity가
4이면
$$
P_t^{(4)}=\frac1{2\pi i}\oint_{\Gamma_4}(zI-U_t^\Delta)^{-1}dz
$$
는 bounded projection이고 rank 4다. 실제 slow/metastable manifold 해석에는 이보다
강한 normal-hyperbolicity 또는 exponential dichotomy, 4개 mode와 나머지 spectrum의
uniform gap, 그리고 $t$에 따른 projection의 안정성이 필요하다. spectral projection의
존재만으로 nonlinear invariant/center manifold가 4차원이라는 결론은 나오지 않는다.

**완전 반례 P0 (loop ⇒ 4D).** $\ell^2(\mathbb N;\mathbb R^2)$의 각 블록에 다음
bounded generator를 둔다.
$$
\dot a_n=-a_n+b_n,
\qquad
\dot b_n=-b_n+a_n,
\qquad n\in\mathbb N.
$$
각 $(a_n,b_n)$은 명시적인 recurrent 2-cycle이고, generator의 $0$ 및 $-2$ 고유공간은
각각 무한 중복도다. 따라서 time-$\Delta$ map의 $1$ 및 $e^{-2\Delta}$도 무한
중복도이며, isolated rank-4 spectral cluster는 없다. 반대로 loop 없는
$\dot x_1=\cdots=\dot x_4=0$, $\dot x_k=-x_k$ ($k>4$)는 rank-4 center subspace를
가지지만 loop가 필요하지 않다.
그러므로 loops는 rank-4의 필요조건도 충분조건도 아니다.

좌표 불변성도 제한적이다. bounded invertible rechart $T$에서
$U'=TUT^{-1}$이면 isolated spectral projection은
$$
P'=TP T^{-1}
$$
이고 rank는 불변이다. 그러나 관측 chart의 SVD hard-rank, thresholded PCA rank,
또는 비가역 many-to-one encoder의 rank는 일반 $GL$ rechart와 noise scaling에
불변이 아니다. BA-SRM4의 hard rank 4는 finite pulse-output quotient의, tolerance와
chart에 의존하는 진단이며 이 run의 spectral rank 4 증거가 아니다.

## 3. common index와 lossless-compression no-go

각 $\pi_{r,t}:\mathcal H_r\to\mathbb R^4$가 연속이고 local derivative가 rank 4일 수는
있다. 다만 아래 no-go는 $\pi$가 연속이고, ``lossless local coordinate''가 열린
neighborhood 사이의 continuous inverse(특히 differentiable chart이면 local diffeomorphism)를
가진다는 가정 아래의 명제다. 이 조건에서 $\mathcal H_r$의 열린 부분이
infinite-dimensional 또는 단순히 5차원 이상이면 $\pi_{r,t}$는 그런 injective local chart가
될 수 없다: differentiable 경우 derivative kernel이 존재하고, 일반 연속 chart도 local
topological dimension을 보존해야 한다. 따라서 common 4D는
관측 목적에 따른 quotient/equivalence class일 수만 있고 원 감각 pattern의 lossless
복원이 아니다. 이 결론은 BA-SRM4 finite-output quotient no-go와 같은 방향이다.

``지역마다 many-to-one이지만 shared R4''는 정의로는 허용된다. empirical claim이 되려면
각 modality-held-out decoder가 modality-specific 및 unrestricted latent controls보다
고정 target에서 우세하고, 그 map이 반복/perturbation에 안정적이어야 한다.

## 4. sparse hippocampal address의 정보 한계

결정론적 $h=f(\bar z,\bar c,\bar\tau)$에 대해 임의 target $Y$에 data-processing
inequality가 성립한다.
$$
I(Y;h)\le I(Y;\bar z,\bar c,\bar\tau).
$$
따라서 address가 index 정보의 손실 없는 증폭기가 될 수 없다. $m_h$ bit 중 정확히
$s$가 1인 code의 주소 수는 $\binom{m_h}{s}$ 이하이므로, $N$ episode를 hash하면
pigeonhole principle상 $N>\binom{m_h}{s}$에서 collision은 필연이다. $N$이 작아도
similarity argmax의 tie/collision, threshold margin, cue/context dependence를 별도로
측정해야 한다. cryptographic hash와 동등하다는 해석은 category error다.

Riesz contour는 real Hilbert space의 complexification $\mathcal H_\mathbb C$에서 정의한다.
real-valued state에 ``rank 4''를 쓸 때에는 contour가 conjugate spectrum에 대해 닫혀 있고,
복소 conjugate pair는 실 2차원으로 세어 projection range가 실 좌표로 4차원임을 확인해야
한다. 그렇지 않으면 complex algebraic multiplicity 4와 real coordinate count 4를 혼동한다.

## 5. 무차원성 감사

| 항 | 조건 | 판정 |
|---|---|---|
| history norm | $\rho(\theta)d\theta\|h\|^2$가 무차원; $\theta/\tau_0$ 사용 | 조건부 |
| flow window | $\Delta/\tau_0$ | 필수 |
| resolvent | $z$와 $U_t^\Delta$는 같은 무차원 spectral scale; 또는 $\tau_0L$의 resolvent | 필수 |
| spectral gap/cutoff | singular/eigenvalue ratio 또는 고정 무차원 reference scale | 필수 |
| quantizer | $\bar z=S_z^{-1}(z-z_0)$ 및 $\varepsilon$ 무차원 | 필수 |
| sparse address | $B_z\bar z+B_c\bar c+B_\tau\bar\tau-\vartheta$ 무차원 | 필수 |
| cosine similarity | nonzero dimensionless vectors; zero norm은 abstain | 필수 |
| exp kernel | $\exp[-(t-s)/\tau]$의 ratio만 사용 | 필수 |

정규화되지 않은 time, voltage, firing-rate, 또는 calcium units를 resolvent threshold,
exponential, sparsity threshold에 섞으면 `STOP_DIMENSIONLESS`다.

## 6. P0/P1 및 허용 결론

- P0: loop만으로 4D를 주장하거나 BA-SRM4 hard rank 4를 의식/whole-brain rank로
  승격하는 부모 주장은 반례로 기각한다.
- P0: 4D index에서 원 감각 상태의 lossless recovery를 주장하는 경로는 finite-map
  no-go와 deterministic data-processing inequality로 기각한다.
- P1: countable edge sum의 uniform boundedness/coercivity, spectral contour/gap,
  nonlinear manifold 조건, chart/gauge, quantizer margin은 아직 공리이며 데이터로
  고정되지 않았다.
- P1: $\chi_t$가 projection range를 어떤 4D chart로 보낼지와, region maps의 common
  alignment는 별도 정의·측정모형이 필요하다.

재현 가능한 유한 반례: $U=\operatorname{diag}(1,1,1,1,1/2,1/3,\ldots)$는 rank-4
Riesz projection을 갖지만 loop 의미가 없고, $U=\operatorname{diag}(1,1,1,1,1,1/2,\ldots)$는
같은 종류의 시스템에서 rank 5다. 따라서 rank 값은 observation 이전의 독립 가정/검정
대상이다.
