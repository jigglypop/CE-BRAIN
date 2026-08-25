# 구조 피벗 계약: 고정 점·지속 간선상태·중첩 순환랭크 리만 기억

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-riemannian-conscious-subspace-strengthening-20260825`

반례 식별자: `edge-metric-memory-nonidentifiability`

구조 지문: `fixed-node-weighted-interlocking-cycle-tower-v2`

## 연구 질문과 주장 상한

이 피벗은 뉴런 또는 기록 단위의 정체성을 나타내는 점을 고정하고, 간선의 지속 상태가 점 사이의 거리·각도·허용 방향을 정하는 계량을 바꾸며, 작은 순환 부분공간이 더 큰 순환 부분공간과 맞물려 올라가는 rank profile에 입력 흔적이 남는다는 가설을 검사한다. 핵심 사슬은 다음과 같다.

$$
m
\longrightarrow s(T)
\longrightarrow \mathbb A(s,b,h)
\longrightarrow \{\Pi_\ell(s)\}_{\ell=0}^{L}
\longrightarrow \widehat m.
$$

수학 목표는 이 사슬의 각 화살표가 단사이거나 국소 식별 가능한 충분조건을 증명하고, $L\to\infty$에서 어떤 weighted limit만 정의되는지 분리하는 것이다. 실증 목표는 실제 뇌 기록에서 입력 제거 뒤에도 같은 관측 사슬이 지속되고 matched biological·instantaneous-attention·fast-weight 대조보다 held-out 예측 또는 개입 반응을 개선하는지 판정하는 것이다. L0 계산만 통과하면 생물학적 기억을 증명했다고 쓰지 않는다.

## PREDECESSOR_EVIDENCE

| 선행 결과 | 보존 | 재시도 금지 |
|---|---|---|
| 기존 edge-operator 계량 정리 | coercive baseline과 PSD edge form의 합은 strong metric을 만든다 | edge 연결성만으로 coercivity를 주장하지 않는다 |
| 기존 Riesz 부분공간 정리 | 고립 spectral cluster와 gap 아래 rank가 안정된다 | loop가 특정 rank를 강제한다고 쓰지 않는다 |
| BA-G2·BA-G3D | 전역 SPD feature 또는 SPD 변화량만으로 recall을 설명하지 못했다 | global metric scalar, curvature 또는 correlation 하나를 기억과 동일시하지 않는다 |
| V9 중첩 SCC | 증가하는 finite strong graph의 direct union과 호환 동역학 정리는 살아 있다 | topology만으로 기억·수렴을 주장하지 않고, V9 task-utility STOP을 재채점하지 않는다 |
| V17 strict metric no-rescue | sign-blind metric state의 finite/countable 복제로 잃은 cue를 복원할 수 없다 | 원공간 metric-only 복제를 무한 rank 해법으로 되살리지 않는다 |
| 새 완전 반례 | 서로 다른 edge 변수는 같은 metric을, 서로 다른 metric은 같은 projector를 만들 수 있다 | gauge와 rank 조건 없이 기억의 유일성을 주장하지 않는다 |

## BIO_STARTING_MECHANISM

생물 기준식은 세 층만 채택하며, 정확한 식·단위·시간척도와 1차 출처는 source lane에서 검증한다.

1. 고정된 presynaptic/postsynaptic 정체성 위에서의 국소 synaptic efficacy 또는 conductance.
2. eligibility trace와 제3요인에 의해 갱신되는 가소성 상태.
3. 입력이 끝난 뒤 빠른 활동보다 느리게 완화되는 synaptic·structural persistence.

확립된 생물식을 특정 리만 계량이라고 부르지 않는다. 아래 $\mathbb A(s,b,h)$와 중첩 projector profile이 CE 추가 구조다.

## 정의와 CE_DELTA

고정된 점 집합을 $V=\{1,\ldots,n\}$이라 하고, 각 점의 좌표 또는 정체성 anchor를 $p_v\in\mathbb R^N$으로 둔다. 쓰기 전후에 $p_v$는 움직이지 않는다. 간선 $e=(i,j)$의 고정 contrast operator는 $D_e$이고, $B_e=D_e^*K_eD_e\succeq0$다.

각 간선은 무차원 지속 상태 $s_e$를 갖는다. 무차원 시간 $\bar t=t/t_0$, 무차원 시정수 $\bar\tau_e=\tau_e/t_0$, 무차원 eligibility $z_e$와 제3요인 $M$을 사용해 다음 개발식을 둔다.

$$
\bar\tau_{z,e}\frac{dz_e}{d\bar t}
=-z_e+\phi_e(\widetilde x,\widetilde u),
$$

$$
\bar\tau_e\frac{ds_e}{d\bar t}
=-(s_e-s_{0e})+\bar\eta_e M(\bar t)z_e(\bar t).
\tag{1}
$$

$\phi_e$, $M$, $z_e$, $s_e$, $s_{0e}$와 $\bar\eta_e$는 모두 무차원이다. 데이터에 맞춘 구체적인 $\phi_e$는 source와 measurement audit 전에는 열지 않는다.

고정 점 위의 계량 operator는 다음과 같다.

$$
A(s)=A_0+\sum_{e\in E}\kappa_{e0}\exp(s_e)B_e,
\qquad A_0\succeq m_0I,
\quad \kappa_{e0}>0.
\tag{2}
$$

지수의 인자 $s_e$는 무차원이다. anchor 두 점 사이의 snapshot 거리 후보는

$$
d_s(p_u,p_v)^2
=(p_u-p_v)^\top A(s)(p_u-p_v).
\tag{3}
$$

식 (3)은 점을 이동시키지 않고도 거리와 각도가 바뀐다는 뜻에서 이 연구가 말하는 ‘공간의 접힘’이다. $A$가 상태점에 의존하지 않는 한 snapshot 자체는 flat metric일 수 있으므로, 이 현상을 자동으로 곡률이라고 부르지 않는다.

metric-normalized 생물 선형화 또는 response operator를

$$
T(s)=A(s)^{-1/2}L_{\rm bio}(s)A(s)^{-1/2}
\tag{4}
$$

로 둔다. 대칭 $L_{\rm bio}$가 부적절한 자료에서는 source-locked return operator $U(s)$와 conjugation-closed contour를 사용한다. 고립된 rank-$d$ spectral cluster의 Riesz 사영은

$$
P_d(s)=\frac{1}{2\pi i}\oint_{\Gamma_d}
(zI-T(s))^{-1}\,dz
\tag{5}
$$

이고, 그 range에 대한 직교 사영을 $\Pi_d(s)$로 따로 쓴다. 비정규 자료에서는 $P_d$와 $\Pi_d$를 섞지 않는다.

## 전체 변수형 중첩 순환랭크 식

단일 level 식 (1)--(5)은 구성 블록일 뿐이다. 실제 후보는 증가하는 유한 graph view

$$
G_0\hookrightarrow G_1\hookrightarrow\cdots,
\qquad V_\ell\subseteq V_{\ell+1},
\quad E_\ell\subseteq E_{\ell+1}
\tag{9}
$$

와 weighted Hilbert 직접합

$$
\mathcal H_\omega
=\left\{x=(x_0,x_1,\ldots):
\sum_{\ell=0}^{\infty}\omega_\ell\|x_\ell\|_\ell^2<\infty\right\},
\qquad \omega_\ell>0
\tag{10}
$$

위에 둔다. 각 level의 oriented incidence를 $\partial_{1,\ell}$이라 하면 graph cycle space와 그 조합론적 rank는

$$
Z_\ell=\ker\partial_{1,\ell},
\qquad
\beta_\ell=\dim Z_\ell
\tag{11}
$$

이다. face boundary $\partial_{2,\ell}$을 넣는 경우 homology rank는 $\dim\ker\partial_{1,\ell}-\dim\operatorname{im}\partial_{2,\ell}$로 별도 표기한다. strong connectivity만으로 $\beta_\ell\to\infty$가 나오지 않으며, 무한히 자주 독립 cycle을 새로 추가한다는 조건이 필요하다.

level embedding을 $I_\ell:\mathcal H_\ell\to\mathcal H_{\ell+1}$로 두고, 맞물림 residual을

$$
(C_\ell x)=x_{\ell+1}-I_\ell x_\ell
\tag{12}
$$

로 정의한다. 여기서 $C_\ell$은 $\mathcal H_\omega$에서 해당 두 좌표를 읽는 전역 연산자로 이해한다. 가용성 $b_{\ell e}$, plasticity log-state $s_{\ell e}$, homeostatic log-gain $h_{\ell e}$를 분리한다. $\omega_\ell$은 직접합 내적에 이미 한 번 들어갔으므로 계량 항에 다시 곱하지 않는다. 층별 물리적 세기를 조절하는 독립 무차원 계수 $\rho_\ell>0$을 두고, 먼저 이차형식

$$
q_{s,b,h}[x,y]
=\langle x,\mathbb A_0y\rangle_\omega
+\sum_{\ell,e}\rho_\ell b_{\ell e}\kappa_{\ell e,0}
\exp(s_{\ell e}-h_{\ell e})
\langle D_{\ell e}x,K_{\ell e}D_{\ell e}y\rangle
+\sum_\ell\rho_\ell
\langle C_\ell x,W_\ell C_\ell y\rangle.
\tag{13}
$$

$\mathbb A_0\succeq m_0I$, $K_{\ell e},W_\ell\succeq0$이고 관심 상태영역에서 두 양의 form series가 국소 균등하게 norm-summable일 때 Riesz 표현정리로 $q[x,y]=\langle x,\mathbb A(s,b,h)y\rangle_\omega$인 유일한 bounded self-adjoint strong metric을 얻는다. 이번 판본은 $\rho_\ell$이 충분히 감소하는 이 강한 충분조건을 택한다. 이것은 필요조건이라고 주장하지 않는다. $s$, $h$, $\log\kappa_0$를 모두 미지수로 두면 additive gauge가 생기므로 $\kappa_0$과 baseline $h$를 calibration에서 고정한다. passive 자료에서 $b\exp(s-h)$의 곱만 보이면 세 변수를 분리하지 않는다.

방향과 지연은 대칭 계량에 숨기지 않고 return/transport operator에 둔다. 무차원 각주파수 $\bar\omega=\omega t_0$와 지연 $\bar\delta=\delta/t_0$에 대해 한 후보는

$$
\mathbb U(\bar\omega)
=\mathbb U_0
+\sum_{\ell,e}b_{\ell e}g_{\ell e}(s,h)
\exp(-i\bar\omega\bar\delta_{\ell e})R_{\ell e}
+\Gamma^\uparrow+\Gamma^\downarrow.
\tag{14}
$$

별도 phase를 지연에서 독립인 자유변수로 추가하지 않는다. 생물학적으로 독립인 phase offset이 source-locked될 때만 새 항으로 연다. 방향성은 비대칭 $R_{\ell e}$와 시간지연 개입으로 식별하며, $\mathbb A$만으로 판정하지 않는다.

각 level에서 $P_\ell(s)$와 직교 range projector $\Pi_\ell(s)$를 계산한다. 부분공간이 실제로 중첩되려면 독립 계산만으로는 부족하며

$$
\Pi_{\ell+1}I_\ell=I_\ell\Pi_\ell
\tag{15}
$$

또는 정규화된 leakage

$$
\varepsilon_\ell^{\rm nest}
=\frac{\|\Pi_{\ell+1}I_\ell-I_\ell\Pi_\ell\|}
{\max(1,\|I_\ell\|)}
\tag{16}
$$

의 사전고정 상한이 필요하다. level 간 coupling 아래 selected hierarchy가 닫히는지는

$$
\|(I-\Pi_{\ell+1})\Gamma_{\ell+1,\ell}\Pi_\ell\|,
\qquad
\|\Pi_{\ell+1}\Gamma_{\ell+1,\ell}(I-\Pi_\ell)\|
\tag{17}
$$

을 따로 보고한다.

이 계약은 다음 네 rank를 합치지 않는다.

| 기호 | 뜻 |
|---|---|
| $\beta_\ell$ | level $\ell$의 graph cycle-space 차원 |
| $d_\ell=\operatorname{rank}P_\ell$ | 선택된 동역학 spectral subspace rank |
| $k$ | 저장 입력 code 차원 |
| $d_{\rm eff}(W;\lambda)$ | 유한 측정창과 noise scale에서의 유효 관측차원 |

$\sum_\ell\beta_\ell=\infty$ 또는 $\sum_\ell d_\ell=\infty$는 모델의 형식적 무한 계층일 뿐, 유한 센서·유한 시간창에서 무한 rank를 관측했다는 뜻이 아니다. raw projector direct sum은 새 projector가 계속 붙으면 operator norm으로 수렴하지 않을 수 있다. 따라서 유한 truncation은 사전고정한 감소 가중치 $\gamma_\ell$를 쓴 readout

$$
\mathcal R_\gamma^{(L)}
=\sum_{\ell=0}^{L}\gamma_\ell O_\ell\Pi_\ell x_\ell,
\qquad
\sum_{\ell=0}^{\infty}
\frac{|\gamma_\ell|^2\|O_\ell\|^2}{\omega_\ell}<\infty
\tag{18}
$$

에 대해서만 tail bound를 주장한다. 실제 bound는

$$
\|\mathcal R_\gamma-\mathcal R_\gamma^{(L)}\|
\le
\left(
\sum_{\ell>L}\frac{|\gamma_\ell|^2\|O_\ell\|^2}{\omega_\ell}
\right)^{1/2}\|x\|_\omega
\tag{18a}
$$

이다. 이 조건 없이 $\sum|\gamma_\ell|\|O_\ell\|<\infty$만으로는 $\omega_\ell\downarrow0$일 때 커질 수 있는 $\|x_\ell\|$를 제어하지 못한다.

### 구조 후보 트리

1. **정확 direct-limit branch:** $I_\ell U_\ell=U_{\ell+1}I_\ell$을 요구한다. V9에서 nonzero boundary coupling의 generic append-zero compatibility가 거부됐으므로 가장 강한 음성대조다.
2. **coupled weighted-direct-sum branch:** 식 (10), (13), (17)을 사용한다. level 상태가 함께 존재하고 coupling leakage를 직접 인증하므로 이번 선택 경로다.
3. **projective coarse-graining branch:** surjection $\pi_{\ell+1,\ell}$과 $\pi F_{\ell+1}=F_\ell\pi$를 요구한다. coarse state가 정확한 quotient인지 판정하는 별도 경로다.
4. **history-holonomy branch:** 같은 최종 계량을 가진 순서가 다른 episode를 path-ordered transport로 구분한다. snapshot hierarchy가 순서를 잃을 때만 다음 피벗으로 연다.

## 고정할 수학 명제

### M1. 계량 기억의 전역 단사성

유한 관측 prefix의 쓰기 code $m\in\mathcal U\subset\mathbb R^k$와 full-column-rank 행렬 $C$에 대해 $s(T)=s_0+Cm$이라 하자. calibration에서 $\kappa_{e0}$과 baseline $h_e$를 고정하고 $\{B_e\}$가 선언한 edge family에서 선형 독립이면 $m\mapsto A(s_0+Cm)$는 단사다. 무한 family에서는 synthesis map의 injectivity뿐 아니라 양의 lower frame bound가 있어야 noise-stable 복원을 주장한다.

### M2. 지속성과 유효 기억시간

쓰기 종료 시점에 $s(T)-s_0=Cm$이 이미 성립하고, $T$ 뒤에 $Mz=0$이면 식 (1)에서

$$
s(t)-s_0=E(t-T)Cm,
\qquad
E_{ee}(\Delta t)=\exp(-\Delta t/\tau_e).
\tag{19}
$$

유한 $t$에서 $E$는 가역이므로 noiseless metric code의 단사성은 유지된다. 실제 유효 기억시간은 측정 design의 최소 특이값이 noise floor 아래로 내려가기 전까지로 정의한다.

### M3. 부분공간 기억의 국소 식별성

$\Pi_\ell(m)$이 각 관심 level에서 $C^1$이고 spectral gap이 열려 있다고 하자. 유한 관측 깊이 $L$의 직교 projector profile Jacobian을

$$
\mathscr J_{\Pi,L}(m_0)
=\left[
\frac{\partial}{\partial m_1}
\begin{bmatrix}\operatorname{vec}_{\rm sym}\Pi_0\\ \vdots\\ \operatorname{vec}_{\rm sym}\Pi_L\end{bmatrix},
\ldots,
\frac{\partial}{\partial m_k}
\begin{bmatrix}\operatorname{vec}_{\rm sym}\Pi_0\\ \vdots\\ \operatorname{vec}_{\rm sym}\Pi_L\end{bmatrix}
\right]
\tag{20}
$$

로 둔다. 이 rank가 $k$이면 $m_0$의 한 이웃에서 code는 유한 projector profile로 국소 식별 가능하다. 필수 차원 상한

$$
k\le\sum_{\ell=0}^{L}d_\ell(N_\ell-d_\ell)
$$

을 함께 검사하지만, 이 상한은 충분조건이 아니다. 일반 Riesz 사영 $P_\ell$은 대칭 vectorization하지 않고, $\Pi_\ell$의 derivative를 contour resolvent와 range-orthogonalization 미분으로 독립 검산한다.

### M4. 능동 관측 가능성

알려진 probe $v_l$의 quadratic response

$$
y_l=v_l^\top A(s)v_l+\varepsilon_l
\tag{21}
$$

을 사용할 때 $H_{le}=v_l^\top B_ev_l$라 두면 실제 측정 Jacobian은

$$
J_y(m)
=H\,\operatorname{diag}\!\left(
b_e\kappa_{e0}\exp[s_{0e}+(Cm)_e-h_e]
\right)C.
$$

$\operatorname{rank}J_y(m_0)=k$일 때만 code는 gauge-fixed family 안에서 국소 복원 가능하다. $\operatorname{rank}H=k$만으로는 충분하지 않다. 이 probe는 대칭 계량만 보므로 방향·지연·가소성·항상성의 개별 분해를 식별하지 않으며, 임의 ambient metric tomography도 아니다.

## MEASUREMENT_MODEL

실제 자료에서는 숨은 edge state를 직접 관측했다고 가정하지 않는다.

$$
y_{r,k}=\mathcal H_r(x(t_k),s(t_k);\psi_r)+\varepsilon_{r,k}.
$$

각 modality의 voltage, fluorescence, spike count, conductance, distance와 시간은 별도 기준척도로 무차원화한다. functional connectivity나 covariance를 실제 synaptic edge state와 동일시하지 않는다. 직접 edge 측정이 없으면 주장 상한은 ‘관측 edge-state proxy와 양립’으로 낮춘다.

## DATA_PROVENANCE와 DATA_SPLIT

source lane은 다음 순서로 실제자료 후보를 찾는다.

1. 같은 cell 또는 synapse 정체성을 쓰기 전·후에 추적하고, 활동 또는 행동 readout과 selective perturbation을 함께 가진 공개자료.
2. 구조 edge와 기능 활동이 같은 cell identity로 정렬되지만 longitudinal write가 없는 자료.
3. 고정 neuron identity와 반복 activity만 있는 자료.

첫째만 직접적인 L4 edge-memory 판별 후보가 될 수 있다. 둘째와 셋째는 각각 정적 metric compatibility 또는 functional proxy에만 사용한다. calibration/development/confirmation animal·session은 겹치지 않게 한다. 현재 run의 과거 L0 seed와 열린 인간 iEEG endpoint를 confirmation에 재사용하지 않는다.

## OBSERVABLES

- 입력 제거 뒤 유한 prefix $\Delta\mathbb A^{(L)}(t)$와 projector profile $\{\Delta\Pi_\ell(t)\}_{\ell=0}^{L}$의 지속 곡선;
- fixed-anchor 거리 변화 $d_s(p_u,p_v)/d_{s_0}(p_u,p_v)$;
- graph-cycle rank profile $\{\beta_\ell\}$, spectral rank profile $\{d_\ell\}$, nesting residual $\{\varepsilon_\ell^{\rm nest}\}$와 층간 coupling leakage;
- metric-code design $J_y$, projector-profile Jacobian $\mathscr J_{\Pi,L}$의 rank·최소 특이값·조건수;
- 감소 가중 readout $\mathcal R_\gamma^{(L)}$의 held-out code 또는 행동 proper score와 계산된 tail bound;
- edge-state permutation, cycle-basis permutation, no-third-factor, no-persistence, gap-closed, non-nested-coupling control;
- vanilla reset self-attention과 stateful fast-weight/recurrent-attention의 parameter-matched 성능;
- 가능한 자료에서는 write-edge lesion과 rescue의 차이.

## TRANSFORMER MATCHED CONTROL

비교 대상은 ‘모든 Transformer’가 아니다. 첫 대조는 frozen parameter와 reset context를 가진 vanilla self-attention이다.

$$
P(X)=\operatorname{softmax}(QK^\top/\sqrt{d_k}),
\qquad Y=P(X)V.
$$

이 attention map은 입력별 순간 상태다. 그러나 KV cache, recurrent memory, fast weights 또는 학습된 parameter update를 가진 Transformer는 지속 상태를 가질 수 있으므로 별도의 강한 대조군으로 둔다. CE 후보의 차별점은 이름이 아니라 local edge-state persistence와 선택적 edge intervention 예측이다.

## RESIDUAL_RULE과 MODEL_SELECTION

자유도에는 $k$, edge family, level 수 $L$, $\{\beta_\ell\}$, $\{d_\ell\}$, embedding·coupling family, $\{\omega_\ell,\gamma_\ell\}$, 시정수 family, spectral contour, probe design과 decoder를 모두 포함한다. 개발 자료에서만 구조를 선택한다. 동일 parameter budget의 biological baseline, raw/PCA, reset attention과 stateful fast-weight baseline을 비교한다. confirmation에서 held-out proper score 개선과 사전고정 edge perturbation 방향이 함께 재현되지 않으면 생물학적 기억 주장을 승격하지 않는다.

## REVISION_TRIGGER

한 판본에서는 한 구조만 바꾼다. $\mathbb A$ code rank가 실패하면 level 수나 spectral rank를 늘리지 않고 active-quadratic route로 이동한다. $\mathbb A$는 식별되지만 $\mathscr J_{\Pi,L}$가 실패하면 ‘metric stores / nested subspace does not identify’라는 음성대조를 잠그고 holonomy 또는 intervention route로 이동한다. nesting residual 또는 coupling leakage가 실패하면 projector를 다시 고르는 대신 exact direct-limit branch를 기각하고 coupled branch의 닫힘 실패로 기록한다. 실제 데이터 잔차로 $\phi_e$, level/rank menu, 가중치와 제외 기준을 동시에 바꾸지 않는다.

## FALSIFIER와 CLAIM_CEILING

다음 중 하나면 ‘리만 부분공간이 기억 code를 기록한다’는 현재 판본을 기각한다.

1. 어떤 사전고정 유한 관측 깊이에서도 $\operatorname{rank}\mathscr J_{\Pi,L}<k$이거나 관심 level의 spectral gap이 닫힘;
2. 입력 제거 뒤 $\Delta\mathbb A^{(L)}$와 $\{\Delta\Pi_\ell\}_{0}^{L}$가 사전고정 persistence 창보다 먼저 소실;
3. $\varepsilon_\ell^{\rm nest}$ 또는 coupling leakage가 상한을 넘는데도 중첩 부분공간이라고 불러야만 성능이 나옴;
4. edge-state 또는 cycle-basis permutation이나 matched instantaneous control과 held-out 성능이 같음;
5. 직접 edge 개입에서 metric/projector profile과 recall의 방향이 분리됨;
6. stateful fast-weight baseline이 같은 edge-intervention 현상을 더 적은 자유도로 설명함;
7. $L$을 늘릴 때 감소 가중 readout tail이 사전고정 bound대로 줄지 않음.

현재 허용 상한은 `CONDITIONAL_WEIGHTED-CYCLE-TOWER_METRIC_THEOREMS / LOCAL_PROJECTOR-PROFILE_IDENTIFIABILITY / FINITE-PREFIX_IMPLEMENTATION / REAL-DATA_ADMISSIBILITY_AUDIT`이다. 실제자료와 개입을 통과하기 전에는 ‘뇌가 무한 순환랭크를 실제로 관측한다’, ‘뇌가 공간을 접어 기억한다’, ‘Transformer보다 우월하다’, ‘의식 부분공간을 증명했다’고 쓰지 않는다.
