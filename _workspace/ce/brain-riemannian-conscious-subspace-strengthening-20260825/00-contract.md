# Research contract — 고차원 history–리만 기하와 순간 저차원 부분공간 강화

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-conscious-moment-index-geometry-20260823`

Date: 2026-08-25

## 1. 연구 질문과 범위

이 run은 다음 결합 후보를 상세한 정의·정리·반례·무차원 측정식으로 강화한다.

1. 신경계의 현재 상태와 간선별 연속 과거를 separable weighted history Hilbert space에 둔다.
2. 한 상태점 $x$를 고정한 뒤 기준 계량과 간선 contrast operator의 합으로 국소 strong Riemann metric 후보를 정의한다.
3. 간선 세기 변화와 간선 절단이 계량, 도달 가능성, 경로 비용에 주는 효과를 서로 다른 명제로 분리한다.
4. 방향성 연결은 대칭 계량이 아니라 동역학 generator에 두고, 계량 gradient와 비가역 drift를 분리한다.
5. 짧은 시간창의 tangent return operator가 고립된 $d$차원 spectral subspace를 선택할 조건과 섭동 안정성을 정리한다.
6. $d$를 4로 고정하지 않고 $d\in\{1,2,3,4,5,6,8,10,12\}$ 후보군에서 비교할 관측량을 정의한다.
7. hard observable rank, noise-aware effective dimension, manifold/ambient dimension을 분리한다.
8. 유한 수동 관측의 quotient no-go와 능동 개입 아래 제한적·완전 계량 식별 정리를 한 논리 사슬로 연결한다.

이 run의 목표는 수학적 후보 체계의 강화와 L0 수치 witness다. 새 공개 뇌 데이터 적합, 의식 차원 추정, 생물학적 메커니즘 승격은 범위 밖이다.

## 2. 대상·기호·정의역

- $V$: 유한 또는 가산 node 집합.
- $E$: 유한 또는 가산 directed edge 집합.
- $a_v\in\mathbb R^{p_v}$: node $v$의 현재 무차원 상태.
- $h_e\in L^2_{\rho_e}(( -\infty,0],\mathbb R^{q_e})$: edge $e$의 무차원 history state.
- $\mathcal H$: node 상태와 edge history의 Hilbert direct sum.
- $x\in U\subset\mathcal H$: 국소 기하를 평가하는 고정 상태점.
- $D_e:\mathcal H\to\mathcal Y_e$: bounded edge contrast/transport observation operator.
- $K_e(x)$: $\mathcal Y_e$ 위 bounded self-adjoint positive-semidefinite edge weight operator.
- $b_e\in[0,1]$: 무차원 edge availability. $b_e=0$은 해당 edge 항의 제거다.
- $A_{0,x}$: bounded self-adjoint coercive baseline metric operator.
- $A_x(b)=A_{0,x}+\sum_e b_eD_e^*K_e(x)D_e$.
- $g_x^{(b)}(u,v)=\langle u,A_x(b)v\rangle_{\mathcal H}$.
- $F_{\rm bio}$: 출처가 고정된 생물 기준 동역학을 나타내는 자리표시자. 이 run은 새 생물 계수를 정하지 않는다.
- $\Delta F_{\rm CE}$: metric gradient, edge-history coupling, directed drift를 분리한 CE 후보 추가항.
- $\Phi_{t,t+\Delta}$: 무차원 시간창 $\bar\Delta=\Delta/t_0$의 flow.
- $U_t^\Delta=D\Phi_{t,t+\Delta}(x_t)$: tangent return operator.
- $P_t^{(d)}$: 고립 spectral cluster의 Riesz projection.
- $G_t^{\rm obs}=J_t^*W_tJ_t$: 무차원 관측 pullback Gram operator.
- $d_{\rm eff}(\lambda)=\operatorname{tr}[\widetilde G_t(\widetilde G_t+\lambda I)^{-1}]$: 무차원 noise-aware effective dimension; $\lambda>0$.

## 3. PREDECESSOR_EVIDENCE

| 선행 결과 | 고정 상태 | 보존할 좁은 주장 | 이번 run의 재시도 금지·사용 규칙 |
|---|---|---|---|
| `brain-conscious-moment-index-geometry-20260823` | `CONCEPTUAL_FORMALIZATION_COMPLETE / EMPIRICAL_INSTANTIATION_BLOCKED` | history Hilbert space와 조건부 strong metric, Riesz rank-$d$ 후보, loop가 4를 강제하지 않는 no-go | loop$\Rightarrow4$, 4D lossless recovery, literal hippocampal hash를 되살리지 않는다. |
| `brain-synapse-edge-operator-geometry-20260823` | discovery candidate; validation/confirmation sealed | Allen discovery IC→IC finite observed quotient에서 ex/in hard rank 4, $d_{\rm eff}(1)$ 중앙값 3.2945/3.5620 | 이를 의식·ambient 차원으로 승격하지 않고 새 data fit에 사용하지 않는다. |
| `brain-adaptive-effective-dimension-validation-v2-20260823` | source-rooted input stop; real endpoint unopened | causal PSD quotient와 continuous $d_{\rm eff}$ 정의 | 표본 gate 뒤 threshold/window를 바꾸어 기존 endpoint를 재개하지 않는다. |
| `brain-finite-observation-metric-nonidentifiability-20260824` | mathematical local no-go complete | finite passive observation은 pointwise quotient만 식별하며 ambient metric·dimension은 식별하지 못한다. | 숫자 4 또는 낮은 rank로 ambient/의식 차원을 고정하지 않는다. |
| `brain-finite-observation-metric-identifiability-escape-20260824` | theorem + deterministic synthetic witness | gauge-fixed finite metric family는 known intervention과 positive Gramian 아래 국소 식별 가능 | finite-family 전제를 임의 ambient metric 복원으로 확대하지 않는다. |
| `brain-complete-active-metric-tomography-20260824` | theorem + L0 deterministic synthetic validation | countably complete exact active quadratic response는 arbitrary bounded strong metric을 유일 식별 | 실제 뇌가 complete basis force·reset·exact response를 제공한다고 가정하지 않는다. |
| `brain-human-ccep-equation-discovery-20260824` | candidate killed at D2 | 한 환자 CCEP의 cable 후보는 D1 뒤 D2 source-cluster CI가 0을 지나 확인되지 않았다. | D3을 열거나 같은 split에서 식·창·threshold를 고치지 않는다. |
| `brain-human-ccep-multisubject-precision-20260825` | implementation pre-range stop | 과학 endpoint가 열리지 않아 경험적 업데이트가 0이다. | 구현 오류를 과학 결과로 해석하지 않는다. |

## 4. BIO_STARTING_MECHANISM

기준식은 새 생물 법칙을 주장하지 않고, 선행 run에서 채택한 일반 상태·관측 분해만 유지한다.

$$
dX_t
=F_{\rm bio}(X_t,u_t;\theta_{\rm bio})\,dt
+\Delta F_{\rm CE}(X_t,H_t;\phi)\,dt
+\Sigma(X_t)\,dW_t.
$$

$F_{\rm bio}$의 구체적 이온·시냅스·전도식과 계수는 실제-data successor contract에서 1차 출처와 함께 고정한다. 이번 run에서 생물 파라미터를 만들거나 적합하지 않는다.

## 5. CE_DELTA 후보

### 5.1 강화 계량 후보

$$
A_x(b)
=A_{0,x}
+\sum_{e\in E}b_eD_e^*K_e(x)D_e,
\qquad
g_x^{(b)}(u,v)=\langle u,A_x(b)v\rangle_{\mathcal H}.
$$

이 식이 strong Riemann metric을 정의한다는 주장은 다음 조건에 한정한다:
$A_{0,x}\succeq m_0I$ ($m_0>0$), $K_e(x)\succeq0$, 그리고 국소적으로
$\sum_e\|D_e\|^2\|K_e(x)\|<\infty$이며 필요한 차수까지 미분항도
operator norm으로 국소 균등 수렴한다. 이 조건이 없으면 위 식은 PSD
quadratic form 후보일 뿐이다. 특히 edge 연결성이나 양의 edge weight만으로
coercivity를 주장하지 않는다.

### 5.2 가역 기하와 방향성 drift의 분리

$$
\Delta F_{\rm CE}(x,h)
=-M_x(b)\nabla_{\mathcal H}\mathcal V(x,h)
+S_x(b)x
+R_x(h),
\qquad M_x(b)=A_x(b)^{-1}.
$$

$S_x^*=-S_x$만으로 energy-neutrality를 주장하지 않는다. 중립성이 필요한 경우
$D\mathcal V(x)[S_xx]=0$을 별도 가정하며, 일반적인 energy identity는
$$
\frac{d\mathcal V}{dt}
=-\langle\nabla\mathcal V,A_x^{-1}\nabla\mathcal V\rangle
+\langle\nabla\mathcal V,S_xx\rangle
+\langle\nabla\mathcal V,R_x(h)\rangle
$$
이다.

$S_x$는 비자기수반일 수 있는 directed transport generator이고, $R_x$는 bounded history-memory forcing 후보다. $S_x$를 metric으로 부르지 않는다.

### 5.3 순간 저차원 후보

$$
P_t^{(d)}
=\frac{1}{2\pi i}\oint_{\Gamma_d}(zI-U_t^\Delta)^{-1}\,dz,
\qquad
z_t^{(d)}=\chi_{t,d}(P_t^{(d)}\zeta_t).
$$

recurrent/loop 구조는 특정 $d$를 강제하지 않는다. 후보군 비교에서 선택된 rank도
관측된 spectral subspace의 rank일 뿐, 의식의 필연적 차원으로 해석하지 않는다.

$d$는 데이터 전에 고정한 후보군에서 비교하며 4 또는 4–6을 공리로 넣지 않는다.

### 5.4 집중도와 유효차원 후보

상태 covariance 또는 관측 precision을 나타내는 positive trace-class operator $C_t$에 대해

$$
c_d^\perp(t)=\frac{\operatorname{tr}(Q_t^{(d)}C_tQ_t^{(d)})}{\operatorname{tr}C_t}
$$

여기서 $Q_t^{(d)}$는 $\operatorname{Ran}P_t^{(d)}$ 위의 직교 사영이고,
$C_t\succeq0$는 trace class이며 $\operatorname{tr}C_t>0$이다. 일반 비직교
Riesz 사영 $P$에 대해 $\operatorname{tr}(PCP)/\operatorname{tr}C\in[0,1]$이라고
주장하지 않는다.

를 순간 spectral concentration으로 둔다. 별도로 관측 quotient의 effective dimension은

$$
d_{\rm eff}(t;\lambda)
=\operatorname{tr}\!\left[
\widetilde G_t(\widetilde G_t+\lambda I)^{-1}
\right]
$$

로 둔다. $c_d^\perp$, hard rank, $d_{\rm eff}$를 같은 양으로 취급하지 않는다.

## 6. 증명·반례 요구사항

수학 lane은 최소한 다음을 판정해야 한다.

1. $A_x(b)$의 boundedness, self-adjointness, coercivity와 smoothness 충분조건.
2. edge weakening/removal 아래 metric operator perturbation bound 및 local length bound.
3. $A_{0,x}$가 coercive하지 않을 때 disconnection이 degeneracy를 만들 수 있는 반례.
4. 방향성 drift와 metric의 분리 및 energy derivative에서 skew/self-adjoint 성분의 역할.
5. spectral contour gap 아래 $P_t^{(d)}$의 rank 보존과 perturbation bound.
6. loop 존재가 $d=4$ 또는 $4\le d\le6$을 강제하지 않는 선행 no-go 보존.
7. $c_d^\perp\in[0,1]$, $d_{\rm eff}$의 경계·단조성·rank 관계 및 trace-class 조건.
8. 유한 관측 quotient no-go와 finite-family/complete-active 식별 정리가 모순 없이 접합되는지.
9. infinite/high-dimensional open set을 $d$차원으로 lossless encode할 수 없다는 no-go 보존.
10. 모든 exp, log, resolvent parameter, probability, fixed-point core의 무차원성.

## 7. MEASUREMENT_MODEL

이번 run은 새 데이터를 열지 않는다. successor 실제-data 계약의 최소 관측식만 고정한다.

$$
y_k=\mathcal M(X_{t_k};\psi)+\varepsilon_k,
\qquad
\varepsilon\sim\mathcal D(0,\Sigma_y).
$$

관측값은 채널별 기준척도 $S_y$로 $\widetilde y=S_y^{-1}(y-y_0)$로 무차원화한다. $J_t=D\widetilde{\mathcal M}_{X_t}$와 $W_t$에서 $G_t^{\rm obs}=J_t^*W_tJ_t$를 만들며, 이는 ambient metric이 아니라 관측 pullback이다.

## 8. DATA_PROVENANCE와 DATA_SPLIT

새 외부 데이터: 없음.

선행 보고서의 frozen 결과와 hash만 인용한다. Allen validation/confirmation, CCEP D3, 의식 실기록 endpoint는 열지 않는다. L0 witness는 고정 seed의 합성 operator fixture만 사용하며 empirical split을 흉내 내어 생물학적 주장을 만들지 않는다.

## 9. OBSERVABLES

L0 witness에서만 다음을 사용한다.

- baseline coercivity margin;
- operator perturbation norm;
- local squared-length perturbation;
- Riesz projector rank와 projector perturbation norm;
- orthogonalized concentration $c_d^\perp$;
- hard rank와 $d_{\rm eff}(\lambda)$;
- disconnected-degeneracy adverse control;
- finite passive blind-tail witness.

모든 값은 무차원 operator 또는 동일 기준척도로 정규화된 vector에서 계산한다.

## 10. RESIDUAL_RULE과 MODEL_SELECTION

이 run의 수치 구현은 정리의 유한차원 witness만 검사한다. 식 선택이나 파라미터 적합을 하지 않는다. analytic identity와 numerical result의 절대오차 또는 operator-norm residual을 보고하며 tolerance는 구현 전에 `31-validation.md`의 계획에 고정한다.

순간 차원의 실제-data successor는 동일 nuisance·시간창·parameter budget에서 $d$ 후보를 비교하고, held-out $\Delta\mathrm{ELPD}>2SE$ 없이는 특정 $d$를 선택하지 않는다.

## 11. FALSIFIER와 MATCHED_CONTROLS

1. baseline coercivity 없이 허용 edge를 제거했을 때 kernel이 생기면 보편적 strong-metric 보존 주장을 기각한다.
2. contour가 spectrum과 교차하거나 gap이 닫힐 때 rank 안정성을 주장하지 않는다.
3. 동일 관측 quotient를 만드는 서로 다른 ambient metric/차원 witness는 passive full-recovery 주장을 계속 기각한다.
4. 실제 successor에서 $d=4$ 또는 $4\le d\le6$이 dimension-free·고차원 모델을 독립 holdout에서 이기지 못하면 fixed-low-d route를 기각한다.
5. recurrent intervention이 matched feedforward control보다 $P_t^{(d)}$ 안정성을 선택적으로 낮추지 않으면 loop-selection 해석을 기각한다.
6. metric deformation 없이 adjacency만 바꾼 control과 adjacency 고정·metric만 바꾼 control을 분리한다.

## 12. REVISION_TRIGGER

수학적 반례가 나오면 보편 부모 주장을 제거하고 정확히 좁힌 충분조건 정리만 보존한다. 수치 witness 실패는 먼저 구현·정밀도·정규화 문제를 감사하며, 정리의 전제를 충족하는 정확 witness에서도 실패할 때만 수학 lane으로 되돌린다. 새 실제 데이터에 맞춘 식 변경은 이 run에서 허용하지 않는다.

## 13. CLAIM_CEILING

허용 상한:

`FORMAL_STRENGTHENING_OF_HISTORY_HILBERT_EDGE_METRIC_AND_VARIABLE_RANK_SPECTRAL_SUBSPACE / CONDITIONAL_THEOREMS_AND_COUNTEREXAMPLES / DIMENSIONLESS_L0_WITNESS_ONLY`

금지되는 상위 주장:

- 인간 또는 동물 의식이 4차원, 4–6차원 또는 임의의 고정 $d$라는 주장;
- Allen hard rank 4를 ambient manifold 또는 의식 차원으로 승격하는 주장;
- 실제 뇌의 전체 strong Riemann metric을 복원했다는 주장;
- edge deletion을 곧바로 smooth Riemann curvature와 동일시하는 주장;
- recurrent loop가 특정 차원을 필연적으로 만든다는 주장;
- 해마 sparse address를 lossless 또는 cryptographic hash로 부르는 주장;
- simulator 통과를 생물학적 메커니즘·자아·AGI 증거로 바꾸는 주장.
