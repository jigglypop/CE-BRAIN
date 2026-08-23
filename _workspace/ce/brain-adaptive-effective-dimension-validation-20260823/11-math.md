# BA-SRM6 수학 레인 — resolvent 유효차원과 관측 quotient

Status: COMPLETE

Date: 2026-08-23

## 1. 핵심 정의의 정확한 지위

`[정의]` $G\succeq0$를 유한 관측공간의 dimensionless covariance operator,
$\lambda>0$를 dimensionless resolution scale이라 하자.

$$
S_\lambda=G(G+\lambda I)^{-1},
\qquad
d_{\rm eff}(G;\lambda)=\operatorname{tr}S_\lambda.
$$

$d_{\rm eff}$는 scale-dependent spectral degrees of freedom다. 매끄러운 다양체의
위상적 차원, hard rank 또는 fractal dimension이 아니다. 따라서
$d_{\rm eff}=3.7$은 “3.7차원 Riemannian manifold”를 뜻하지 않는다.

## 2. resolvent 정리

**정리 1 [유한 관측공간].** $G=G^*\succeq0$이고 $\lambda>0$이면
$S_\lambda$는 PSD contraction이며

$$
0\preceq S_\lambda\preceq I,
\qquad
0\le d_{\rm eff}(G;\lambda)\le\operatorname{rank}G.
$$

또한 $d_{\rm eff}$는 $\lambda>0$에서 매끄럽고 단조 감소한다.

증명. Spectral theorem으로 $G=U\operatorname{diag}(\mu_k)U^*$,
$\mu_k\ge0$라 쓰면

$$
S_\lambda
=U\operatorname{diag}\!\left(\frac{\mu_k}{\mu_k+\lambda}\right)U^*.
$$

각 eigenvalue가 $[0,1)$에 있으므로 operator inequality와 rank bound가 나온다.
또한

$$
\frac{d}{d\lambda}d_{\rm eff}(G;\lambda)
=-\sum_k\frac{\mu_k}{(\mu_k+\lambda)^2}\le0.
$$

$G\ne0$이면 부등식은 strict하다. 끝.

따라서

$$
\lim_{\lambda\downarrow0}d_{\rm eff}=\operatorname{rank}G,
\qquad
\lim_{\lambda\uparrow\infty}d_{\rm eff}=0.
$$

연속값은 hard rank를 임의의 실수로 바꾼 것이 아니라, 각 mode를
$\mu_k/(\mu_k+\lambda)$만큼 부드럽게 세어 얻는다.

## 3. 무한차원 조건과 반례

**정리 2 [조건부].** Hilbert 공간에서 $G$가 positive self-adjoint trace class이면
$S_\lambda$도 trace class이고

$$
d_{\rm eff}(G;\lambda)
\le\frac{\operatorname{tr}G}{\lambda}<\infty.
$$

증명. 모든 $\mu_k\ge0$에 대해
$\mu_k/(\mu_k+\lambda)\le\mu_k/\lambda$이고
$\sum_k\mu_k<\infty$이므로 비교판정한다. 끝.

Compact만으로는 충분하지 않다. $G=I$이면
$S_\lambda=(1+\lambda)^{-1}I$라서 trace가 무한하다. 더 약한 반례로
$\mu_n=1/n$인 positive compact operator도

$$
\sum_n\frac{\mu_n}{\mu_n+\lambda}
\sim\frac1\lambda\sum_n\frac1n=\infty
$$

다. 이번 실제분석은 $N\times N$ 표본 covariance에만 식을 적용한다. BA-SRM5의
infinite-history 공간 전체가 이 operator로 관측됐다고 주장하지 않는다.

## 4. 좌표변환 감사

**정리 3.** Orthogonal/unitary $Q$에 대해

$$
d_{\rm eff}(QGQ^*;\lambda)=d_{\rm eff}(G;\lambda).
$$

이는 $QGQ^*$가 $G$와 같은 spectrum을 갖기 때문이다. 일반 $GL(N)$ congruence에는
성립하지 않는다. 예를 들어 $G=\operatorname{diag}(1,4)$와 $\lambda=1$이면
$d_{\rm eff}=1.3$이다. $T=\operatorname{diag}(2,1)$로 바꾸면
$TGT^{\mathsf T}=\operatorname{diag}(4,4)$이고 $d_{\rm eff}=1.6$이다.

따라서 이번 수치는 train에서 고정한 neuronwise standardized basis와 그 직교
회전 안에서만 해석한다. 일반 선형 좌표불변성이 필요하면 train-only reference
metric $C\succ0$를 고정하고

$$
B_t=C^{-1/2}G_tC^{-1/2}
$$

의 generalized spectrum을 써야 한다. $C$의 shrinkage와 conditioning은 새 계약의
자유도다.

## 5. finite observed spectral inner product

$0<\epsilon\le1$에 대해

$$
A_{\lambda,\epsilon}
=\epsilon I+(1-\epsilon)S_\lambda
$$

라 두면

$$
\epsilon I\preceq A_{\lambda,\epsilon}\preceq I.
$$

따라서 $g_{\lambda,\epsilon}(u,v)=u^*A_{\lambda,\epsilon}v$는 유한 관측벡터
공간의 positive-definite inner product이고 condition number는 최대
$1/\epsilon$이다. 계약의 $\epsilon=10^{-3}$에서는 최대 $10^3$이다.

그러나 $\epsilon I$는 covariance kernel을 분석자가 채운 prior이고, 시간별 표본
covariance의 열만으로 smooth state-dependent Riemann metric을 입증하지 못한다.
안전한 이름은 “finite observed fluorescence quotient 위의 regularized spectral
inner product”다. Infinite history-space metric에는 operator-norm smoothness와
uniform coercivity가 별도로 필요하다.

## 6. cutoff-free 정규화와 revision 1

계약 초안은 numerical rank를 $c_G$와 $q_t$의 분모로 썼다. 이 값은 tolerance에
따라 불연속이고 계약에 cutoff가 없어서 재현 불가능했다. 데이터 endpoint를 열기 전
math-verifier revision 1에서 주 분석식을 다음처럼 고쳤다.

$$
r_\star=\min(N_{\rm kept},W-1),
\qquad
c_G=\operatorname{median}_{t\in\mathrm{train}}
\frac{\operatorname{tr}G_t}{r_\star},
$$

$$
q_t=\frac{d_{\rm eff}(t;1)}{r_\star}\in[0,1].
$$

Numerical rank는 진단용으로만

$$
r_\eta(G)=\#\{k:\mu_k>10^{-10}\mu_1\}
$$

를 보고하며 주 분석식에는 넣지 않는다. $c_G\le0$ 또는 nonfinite인 recording은
abstain한다.

## 7. 변화율과 무차원성

같은 recording의 고정 neuron basis에서

$$
\kappa_t
=\frac{\lVert S_{t,1}-S_{t-1,1}\rVert_F}{\sqrt{r_\star}},
\qquad
\nu_t
=\frac{q_t-q_{t-1}}{(t_t-t_{t-1})/\tau_0}
$$

는 무차원이다. $\kappa_t$는 rate가 아니라 adjacent selector change다.
$\tau_0$는 train median sampling interval이므로 $\nu_t$도 무차원 rate다. Train RMS
$\sigma_\kappa,\sigma_\nu>0$를 쓰면

$$
M_t
=\exp\!\left[-\left(\frac{\kappa_t}{\sigma_\kappa}\right)^2
               -\left(\frac{\nu_t}{\sigma_\nu}\right)^2\right]
\in(0,1]
$$

이고 지수 인자가 무차원이다. $M_t$는 $q,\nu,\kappa$의 비선형 stability feature지
의식 점수가 아니다.

| core 인자 | 차원 | 무차원 여부 | 정규화 |
|---|---|---|---|
| $\mu_k,\lambda$ | standardized covariance scale | yes | $G/c_G$, fixed dimensionless $\lambda$ |
| $d_{\rm eff},q$ | count, ratio | yes | $q=d_{\rm eff}/r_\star$ |
| $\kappa$ | operator ratio | yes | Frobenius norm$/\sqrt{r_\star}$ |
| $\nu$ | dimension per normalized time | yes | divide by $\Delta t/\tau_0$ |
| $\kappa/\sigma_\kappa$, $\nu/\sigma_\nu$ | ratio | yes | train-only RMS |

차원 상태: `DIMENSIONLESS_PASS`, 단 $c_G,\sigma_\kappa,\sigma_\nu$의 positive finite
gate가 필요하다.

## 8. 식별성 no-go

Window covariance $G_t$는 window 내부 시간 순서와 directed edge를 버린다. 같은
window의 sample column을 순열해도 $G_t$는 정확히 같다. 따라서 $G_t$와
$d_{\rm eff}$만으로 synaptic direction, causal routing, loop, hidden transition
operator 또는 anatomical graph를 식별할 수 없다. Fluorescence measurement도
spike/current/connectome에 대해 many-to-one다.

Synthetic recovery의 truth는 latent brain dimension이 아니라 측정·sampling·noise를
지난 observed covariance의 resolvent trace여야 한다. 실제자료 통과가 허용하는
최대 문장은 다음이다.

> 사전 고정한 observed-calcium soft spectral feature가 이 corpus의
> calibration-prefix 이후 temporal holdout에서 미래 locomotion에 incremental
> predictive value를 보였다.

## 9. 형식 지위

| 항목 | 지위 |
|---|---|
| resolvent bound·단조성·orthogonal invariance | `[정리]` |
| trace-class sufficient condition과 non-trace-class 반례 | `[정리]` |
| $r_\star,c_G,q,\kappa,\nu,M$ | `[정의]` 및 `[공리: 분석 선택]` |
| $W,h,\lambda,\epsilon$, split과 threshold | `[공리: 모델 선택]` |
| 실제 locomotion incremental prediction | `[예측]` |
| 의식·해마·구조 간선 해석 | `[미완성]`, 현재 자료에서는 차단 |

독립 math audit 판정은 `P0 없음 / P1-B revision 1에서 교정 / 나머지 P1 경계
문서화 완료`다.
