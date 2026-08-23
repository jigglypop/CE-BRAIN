# BA-SRM5 최종 보고서 — 무한차원 순환 기하, 순간 4차원 후보, 해마 색인

Status: COMPLETE

Date: 2026-08-23

Final verdict: `CONCEPTUAL_FORMALIZATION_COMPLETE / EMPIRICAL_INSTANTIATION_BLOCKED`

## 초록

본 연구는 간선마다 과거 의존 상태를 둔 무한차원 신경계에서 반복 회로가 한 순간의
저차원 좌표를 선택하고, 해마가 그 좌표를 분산 피질 기억의 주소로 사용한다는 가설을
수식화했다. Countable history direct sum에는 균등 coercive self-adjoint operator가 있을
때에만 strong Riemann metric이 생긴다. 반복 회로의 tangent return operator에 고립된
algebraic multiplicity 4의 spectrum이 있으면 rank-4 Riesz projection을 정의할 수 있지만,
loop의 존재만으로 숫자 4는 나오지 않는다. 해마의 `hash`는 암호학적 hash가 아니라 충돌
가능한 희소 주소로 좁히면 기존 hippocampal indexing·pattern separation/completion과
양립하지만, 주소가 버린 정보를 되살리지는 못한다. 따라서 결합 가설은 수학적으로 가능한
후보이나 실제 의식·고정 4차원·해마 입력 구조는 모두 미검증이며, 고정된 실기록 계약이 없어
데이터 적합을 열지 않았다.

## 1. 문제의 핵심

사용자 아이디어에는 서로 다른 세 층이 들어 있다. 첫째, 시냅스와 영역 간 간선은 현재의
스칼라 하나가 아니라 과거 자극·스파이크·전압에 반응하는 함수다. 둘째, 이 무한차원
상태에서 반복 회로가 짧은 시간 동안 몇 개의 느린 방향만 남길 수 있다. 셋째, 그 방향을
감각과 기억이 공유하는 주소로 쓰고 해마가 해당 피질 패턴을 빠르게 다시 찾을 수 있다.

이 세 층을 분리해야 한다. 무한차원 상태가 존재한다고 해서 순간 좌표가 4차원인 것은
아니다. 반복회로가 있다고 해서 네 모드가 선택되는 것도 아니다. 해마가 색인 역할을 한다는
근거가 있어도 그 색인의 입력이 4차원 의식 좌표라는 결론은 나오지 않는다. 이번 연구의
기여는 이 세 연결고리를 각각 반증 가능한 식으로 바꾼 것이다.

여기서 한 순간은 수학적 길이 0의 점이 아니다. spectrum과 recurrent return을 추정할 수
있는 짧은 분석 창 $\Delta/\tau_0$를 뜻한다. 창 길이와 기준 시간 $\tau_0$는 후속 데이터
계약에서 결과 전에 고정해야 한다.

## 2. 무한차원 간선 history 공간

### 2.1 정의

영역 집합을 $V$, directed edge 집합을 $E$라 하자. 영역 $v$의 유한 현재 상태를
$a_v\in\mathbb R^{p_v}$, 간선 $e$의 과거 상태를
$h_e(\theta)\in\mathbb R^{q_e}$, $\theta\le0$로 쓴다. `[정의]` 전체 상태공간은

$$
\mathcal H
=\left\{(a_v,h_e):
\sum_{v\in V}\lVert a_v\rVert_2^2
+\sum_{e\in E}\int_{-\infty}^{0}
\rho(\theta)\lVert h_e(\theta)\rVert_2^2d\theta<\infty
\right\}.
$$

$V,E$가 countable이고 각 $p_v,q_e$가 유한이면 이는 weighted $L^2$들의
$\ell^2$-direct sum이다. 무한차원은 뉴런 수를 형식적으로 무한히 늘렸기 때문이 아니라,
각 간선이 연속적인 과거 함수를 상태로 가지기 때문에 이미 생긴다. 다만 $\rho>0$이라는
조건만으로 fading memory가 보장되지는 않는다. time-shift semigroup의 유계성과 먼 과거에
대한 관측 functional의 감쇠가 별도로 필요하다.

### 2.2 간선으로 결합된 metric

`[공리: 모델 선택]` 기준 metric operator $A_{0,x}$, edge contrast/transport operator
$D_e$, symmetric positive operator $K_e(x)$를 둔다.

$$
A_x=A_{0,x}+\sum_{e\in E}D_e^*K_e(x)D_e,
\qquad
g_x(u,v)=\langle u,A_xv\rangle_{\mathcal H}.
$$

이 식이 “리만 metric이 간선으로 연결된다”는 문장을 정확히 바꾼 형태다. Directed edge의
방향은 보통 비자기수반 generator와 flow에 들어간다. Riemann metric은 대칭이어야 하므로
directed adjacency 자체를 metric으로 부를 수 없다.

**정리 1 [조건부].** $x\mapsto A_x$가 operator norm에서 매끄럽고
$A_x=A_x^*$이며, 어떤 $0<m\le M<\infty$에 대해

$$
mI\preceq A_x\preceq MI
$$

가 성립한다고 하자. 또한 edge sum이 bounded self-adjoint operator로 국소 균등
수렴한다고 하자. 그러면 $g$는 $\mathcal H$ 위의 strong Riemann metric이다.

증명. Self-adjointness에서 대칭성이 나오고, coercivity에서
$g_x(u,u)\ge m\lVert u\rVert^2>0$이 나온다. 상계와 국소 균등 수렴은 $g_x$의 유계성과
smooth dependence를 보장한다. 따라서 $g_x$가 만드는 norm은 원 Hilbert norm과
동등하다. □

이 조건이 없으면 edge sum은 발산하거나 kernel을 남길 수 있다. 그 경우에는 quadratic
form 또는 degenerate pseudometric만 남으며 strong Riemann metric이라고 부르지 않는다.

## 3. 반복 회로와 순간 rank-4 후보

### 3.1 return operator와 Riesz projection

`[정의]` 실제 생물 기준 동역학과 새 가설 항을 다음처럼 분리한다.

$$
d\xi_t
=F_{\rm bio}(\xi_t,u_t;\theta_{\rm bio})dt
+\Delta F_{\rm CE}(\xi_t;\phi)dt
+G(\xi_t)dW_t.
$$

분석 창 $\Delta$ 동안의 flow를 $\Phi_{t,t+\Delta}$라 하고, local tangent return을

$$
U_t^\Delta=D\Phi_{t,t+\Delta}(\xi_t)
$$

로 둔다. Graph closed walk, SCC membership, recurrent return, Levi-Civita holonomy는 서로
다른 대상이다. Edge map이 실제로 주어졌을 때에만 closed walk
$\gamma=(e_1,\ldots,e_k)$에 대해 $R_\gamma=F_{e_k}\circ\cdots\circ F_{e_1}$와
$DR_\gamma$를 정의할 수 있다. 이 return을 기하학적 holonomy라고 부르려면 invertible
parallel transport와 metric compatibility가 더 필요하다.

`[정의]` $U_t^\Delta$의 spectrum에서 네 real directions에 해당하는 cluster가 다른
spectrum과 contour $\Gamma_4$로 분리된다고 하자. Complexification에서

$$
P_t^{(4)}
=\frac{1}{2\pi i}\oint_{\Gamma_4}
(zI-U_t^\Delta)^{-1}dz
$$

를 정의한다. Complex conjugate pair는 real 2차원으로 세며, 최종 range의 real rank가
4인지 확인한다.

**정리 2 [조건부].** $U_t^\Delta$가 bounded이고 $\Gamma_4$가 spectrum을 가르지 않으며
contour 내부 algebraic multiplicity가 real rank 4라면 $P_t^{(4)}$는 bounded rank-4
projection이다. Bounded invertible rechart $T$에서는
$P'^{(4)}=TP^{(4)}T^{-1}$이므로 spectral rank는 보존된다.

이는 선형 spectral subspace 정리다. Nonlinear 4D slow/center manifold를 주장하려면
uniform spectral gap, normal hyperbolicity 또는 exponential dichotomy, nonlinearity의
regularity와 $P_t$의 시간 안정성이 더 필요하다.

### 3.2 loop에서 숫자 4가 나오지 않는 반례

**정리 3 [no-go].** Recurrent loop의 존재는 rank-4 spectral subspace의 필요조건도
충분조건도 아니다.

증명. $\ell^2(\mathbb N;\mathbb R^2)$의 각 블록에

$$
\dot a_n=-a_n+b_n,
\qquad
\dot b_n=-b_n+a_n
$$

을 두면 모든 블록이 명시적인 2-cycle이다. 그러나 generator의 $0$과 $-2$ eigenspace는
각각 무한 중복도이므로 고립된 rank-4 cluster가 없다. 반대로 loop가 없는 diagonal
system $\dot x_1=\cdots=\dot x_4=0$, $\dot x_k=-x_k$ for $k>4$는 rank-4 center
subspace를 가진다. □

따라서 “루프를 돌면 의식이 4차원으로 고정된다”에서 살아남는 문장은 다음뿐이다.
반복 동역학의 return operator가 독립적으로 네 개의 안정된 느린 mode를 보일 경우,
그 range를 순간 4차원 후보로 시험할 수 있다.

### 3.3 의식 사상

Local dimensionless chart displacement를

$$
\zeta_t
=S_\xi^{-1}\left(\varphi_t(\xi_t)-\varphi_t(\bar\xi_t)\right)
$$

라 한다. `[공리: 물리 사상][미완성]` 순간 의식 내용 후보를

$$
z_t=\chi_t(P_t^{(4)}\zeta_t)\in\mathbb R^4
$$

로 둔다. 이 식에서 4는 시공간 차원이 아니고, 네 축을 시각·청각·촉각·시간처럼
사전에 이름 붙이지 않는다. Bounded coordinate change에서 네 축은 회전·혼합될 수 있고,
불변인 후보는 isolated subspace의 rank다.

후속 측정에서 쓸 수 있는 `[미완성]` moment gate의 최소 형태는

$$
\mathfrak m_4(t)
=\mathbf 1\!\left[\operatorname{rank}P_t^{(4)}=4\right]
\mathbf 1\!\left[\operatorname{gap}_0(U_t^\Delta)\ge\gamma_g\right]
\mathbf 1\!\left[d_{\rm Gr}(P_t^{(4)},P_{t-\Delta}^{(4)})\le\gamma_p\right].
$$

$\operatorname{gap}_0$, Grassmann distance, $\gamma_g$, $\gamma_p$는 모두 무차원이어야
하며 아직 수치가 없다. 이 gate를 conscious/unconscious matched trials에 적용하고
$d\in\{1,2,3,4,5,6,8,10,12\}$를 동일 조건에서 비교하기 전에는 4를 선택할 수 없다.
BA-SRM4의 pulse-response hard rank 4는 이 선택에 사용할 수 없다.

## 4. 부위마다 다른 형상과 공통 칸

영역 $r$마다 상태공간 $\mathcal H_r$와 metric $g_r$가 달라도 된다. 필요한 것은
영역들이 서로 같은 형상이라는 주장이 아니라, 관측 목적에 맞는 many-to-one map

$$
\pi_{r,t}:\mathcal H_r\longrightarrow\mathcal Z_t\cong\mathbb R^4
$$

이다. 서로 다른 영역 상태의 disjoint union에서

$$
x_r\sim_t x_s
\quad\Longleftrightarrow\quad
\pi_{r,t}(x_r)=\pi_{s,t}(x_s)
$$

로 equivalence relation을 정의할 때 공통 관측 quotient라는 말이 정확해진다. Smooth
quotient manifold가 되려면 constant rank와 smooth closed-kernel bundle이 더 필요하다.

Dimensionless 좌표 $\bar z_t=S_z^{-1}(z_t-z_0)$를 cell에 양자화하면

$$
q_t=Q_\varepsilon(\bar z_t)
$$

가 사용자가 말한 “해당 칸 index” 후보가 된다. 같은 $q_t$는 현재 관측 목적에서 같은
class라는 뜻이지, 시각·청각·촉각의 원 패턴이 같다는 뜻이 아니다.

**정리 4 [no-go].** Infinite-dimensional 또는 local dimension이 5 이상인 상태의 열린
부분을 continuous local inverse를 가진 4D chart로 lossless encode할 수 없다.

Differentiable map이면 derivative에 kernel이 남고, 일반 continuous local chart도 local
topological dimension을 보존해야 한다. 따라서 shared 4D는 손실 있는 quotient 또는
task-relative sufficient statistic 후보일 수만 있다. 원 감각 세부를 되살리려면 별도의
피질 저장소와 decoder가 필요하다.

## 5. 해마는 scalar hash가 아니라 희소 주소 후보

Teyler와 DiScenna의 hippocampal memory-indexing theory는 해마가 사건 때 활성화된
neocortical array의 index를 만들고, 그 index의 재활성화가 cortical array를 다시
활성화한다고 제안했다. DG/CA3 실기록은 pattern separation/completion을 지지하고,
DG engram 개입은 특정 fear-memory expression에서 sparse ensemble 재활성화의 인과적
역할을 보였다. 이 근거들은 사용자의 직관과 가깝지만, literal hash나 4D 입력을 직접
보인 것은 아니다.

`[공리: 모델 선택][미완성]` 허용 가능한 주소식은 scalar hash보다 sparse vector다.

$$
h_t
=\mathsf{Sparse}_{s}
\left(B_z\bar z_t+B_c\bar c_t+B_\tau\bar\tau_t-\vartheta\right)
\in\{0,1\}^{m_h}.
$$

$\bar c_t$는 맥락, $\bar\tau_t$는 시간 또는 phase의 무차원 좌표다. 저장된 episode
주소 $h_\nu$ 중 partial cue와 가장 가까운 항목을

$$
\widehat\nu_t
=\underset{\nu}{\operatorname{argmax}}
\frac{\langle h_t,h_\nu\rangle}
{\lVert h_t\rVert_2\lVert h_\nu\rVert_2}
$$

로 찾고, 실제 세부 패턴은 $D_r(\widehat\nu_t)$가 피질에서 재활성화한다고 둔다.
Zero-norm code에서는 abstain해야 한다. DG-like separation은 collision을 줄이는 역할,
CA3-like recurrence는 partial cue를 complete하는 역할의 후보가 된다.

이 code를 similarity-preserving이라고 부르려면 latent distance와 address distance의
triplet order error 및 collision rate가 random sparse, semantic-only, cortical-only,
time-shuffled controls보다 낮아야 한다. 현재 $m_h,s$, codebook, seed, threshold와 tie
policy가 없으므로 그 성질은 아직 주장할 수 없다.

**정리 5 [정보 no-go].** 결정론적 $h=f(\bar z,\bar c,\bar\tau)$에 대해

$$
I(Y;h)\le I(Y;\bar z,\bar c,\bar\tau)
$$

가 성립한다. 또한 정확히 $s$ bit가 켜지는 $m_h$ bit code는 최대
$\binom{m_h}{s}$개의 주소만 가지므로 episode 수가 이를 넘으면 collision이 필연이다.
해마 주소는 검색을 빠르게 하거나 noise에 강하게 만들 수 있지만, 4D bottleneck이 버린
정보를 새로 만들 수 없다.

## 6. 가능성 판정

| 사용자 아이디어의 부분 | 현재 판정 | 이유 |
|---|---|---|
| 간선 history 때문에 상태가 무한차원 | 수학적으로 가능 | weighted history Hilbert space가 자연스럽다 |
| 간선 결합이 Riemann metric을 구성 | 조건부 가능 | symmetric positive, 수렴, coercivity가 필요하다 |
| recurrent loop가 순간 저차원 subspace를 선택 | 가능성 있음 | spectral gap이 있으면 가능하지만 loop 자체로는 차원이 정해지지 않는다 |
| 그 순간 차원이 정확히 4 | 현재 근거 없음 | BA-SRM4의 4는 독립 증거가 아니며 다른 $d$와 비교하지 않았다 |
| 부위별 다른 형상이 공통 칸을 공유 | 손실 있는 quotient로 가능 | lossless common chart는 no-go다 |
| 해마가 빠른 검색용 index 역할 | 기존 이론·실험과 가장 가까움 | indexing theory, separation/completion, engram evidence가 구성요소를 지지한다 |
| 해마가 4D 의식 좌표의 literal hash | 미검증·literal 해석 기각 | sparse address와 cryptographic hash는 다르다 |
| 전체 결합이 의식의 메커니즘 | 미완성 | 단일 dataset·개입·측정 bridge가 없다 |

따라서 가능성이 가장 높은 핵심은 “해마가 분산 피질 패턴의 희소 포인터다”이다. 가장
위험한 핵심은 “그 포인터 앞단이 정확히 4차원 의식 subspace다”이다. 후자는 아직 숫자 4를
고르는 독립 근거가 없다.

## 7. 관측 근거와 중립 비교

Fahrenfort, Scholte와 Lamme의 masking EEG 연구에서는 conscious report와 recurrent
visual signature가 연관됐다. 이는 보편적 의식 기전의 인과적 충분조건이 아니다.
Churchland 등의 monkey motor-cortex 실기록은 structured low-dimensional population
dynamics의 가능성을 보였지만, 의식이나 dimension 4를 다루지 않았다.

Teyler와 DiScenna의 indexing theory는 hippocampal pointer라는 개념을 직접 제안했다.
Neunuebel과 Knierim의 DG/CA3 simultaneous recording은 degraded cue 아래의 separation과
completion을 회로 수준에서 지지했다. Liu 등의 optogenetic DG engram reactivation은
mouse fear task에서 sparse tagged ensemble의 recall sufficiency를 지지했지만, ensemble이
기억 전체이거나 인간 의식과 같다는 뜻은 아니다.

Norman 2019/2021 human iEEG 자료는 hippocampus-cortex reinstatement를 시험할 후속 후보지만,
schema·전극 coverage·subject/session identity·behavioral report·preprocessing receipt를
아직 확인하지 않았다. 이 자료만으로 consciousness rank-4까지 한 번에 검정할 수도 없다.
따라서 현재 관측 비교는 구성요소의 외부 근거를 정리한 것이며 결합 가설의 validation이
아니다.

## 8. 가장 짧은 실증 경로와 falsifier

첫 단계는 두 개의 독립 문제로 나누어야 한다. Conscious-access recording에서는 matched
seen/unseen 또는 report/no-report 조건으로 Route A의 rank-4 spectral model을
dimension-free recurrent model과 high-dimensional model에 비교한다. Hippocampus-cortex
recording에서는 sparse address distance가 cortical similarity·semantic context를 넘어서
reinstatement 대상과 latency를 예측하는지 본다. 두 시험이 각각 살아남아도 결합 메커니즘은
아니며, 마지막에는 두 현상을 동시에 기록하거나 개입하는 자료가 필요하다.

가장 강한 기각 조건은 다음과 같다.

1. Held-out dimension sweep에서 $d=4$가 다른 모든 후보보다
   $\Delta\mathrm{ELPD}>2SE$로 우세하지 않으면 fixed-4 route를 기각한다.
2. Recurrent perturbation, backward mask 또는 time reversal이 matched feedforward
   control보다 rank-4 안정성을 선택적으로 낮추지 않으면 loop-selection을 기각한다.
3. Shared 4D가 modality-specific 또는 unrestricted latent model보다 cross-modal prediction을
   개선하지 못하면 common-cell route를 기각한다.
4. Hippocampal address가 cortical/semantic similarity를 넘는 incremental information을
   주지 않으면 address route를 기각한다.
5. Address perturbation이 cortical reinstatement 대상 또는 latency를 선택적으로 바꾸지
   않으면 causal index interpretation을 올리지 않는다.

## 9. 미완성 과제와 한계

현재 active P0는 없다. Loop가 4를 강제한다는 주장, BA-SRM4 rank를 의식 차원으로
승격하는 주장, 4D lossless recovery, curvature/holonomy=memory/consciousness, literal
cryptographic hash는 반례 또는 category error로 제거했다.

후속 empirical run을 여는 데 필요한 항목은 남아 있다. $\rho$와 모든 기준 scale,
spectral rank/gap estimator, window, nuisance model, quantizer margin, $m_h,s$, address
codebook/seed, collision/tie policy, decoder를 결과 전에 고정해야 한다. 실제 dataset의
DOI/hash, schema, electrode inclusion, subject/session split, consciousness proxy와
confirmation quarantine도 필요하다. 이 항목이 없으므로 현재 구현과 data fit을
건너뛰었다.

## 10. 재현성

연구 run은 다음 경로에 있다.

```text
_workspace/ce/brain-conscious-moment-index-geometry-20260823
```

정책 우회 없이 사용한 상태 명령은 prebuilt binary의 직접 호출이다.

```powershell
$ceStatusExe = Join-Path $env:LOCALAPPDATA 'ce-research-core\release\ce-research-core.exe'
& $ceStatusExe status '_workspace\ce\brain-conscious-moment-index-geometry-20260823'
& $ceStatusExe check '_workspace\ce\brain-conscious-moment-index-geometry-20260823' final
```

이번 run에서는 Python model, simulator, dataset download, train/validation split 또는
empirical test를 실행하지 않았다. 수학 반례와 출처 판정은 `11-math.md`와
`10-sources.md`, successor resume 조건은 `20-audit.md`에 있다.

## 11. 참조

- Fahrenfort, J. J., Scholte, H. S., & Lamme, V. A. F. (2007), DOI
  `10.1162/jocn.2007.19.9.1488`, PMID `17714010`, accessed 2026-08-23.
- Churchland, M. M. et al. (2012), “Neural population dynamics during reaching,”
  DOI `10.1038/nature11129`, accessed 2026-08-23.
- Teyler, T. J., & DiScenna, P. (1986), “The hippocampal memory indexing theory,”
  DOI `10.1037/0735-7044.100.2.147`, PMID `3008780`, accessed 2026-08-23.
- Neunuebel, J. P., & Knierim, J. J. (2014), DOI
  `10.1016/j.neuron.2013.11.017`, accessed 2026-08-23.
- Bakker, A. et al. (2008), DOI `10.1126/science.1152882`, accessed 2026-08-23.
- Liu, X. et al. (2012), DOI `10.1038/nature11028`, accessed 2026-08-23.
- Norman et al. public data candidates (2019/2021), DOI
  `10.5281/zenodo.3259368` and `10.5281/zenodo.4759103`, accessed 2026-08-23;
  suitability unresolved.
