# 리만 부분공간과 의식 순간 모델 강화: 최종 보고서

Status: COMPLETE

Date: 2026-08-25

Final verdict: **FORMAL_STRENGTHENING_COMPLETE / CONDITIONAL_THEOREMS_ONLY / POWERSHELL_AND_PYTHON_NUMPY_L0_PASS / FINITE_RIESZ_6_PASS / HISTORY_EDGE_17_PASS / DIMENSIONLESS_20_PASS_WITH_EXPLICIT_SYNTAX_ONLY_LEVEL / PACKAGE_TORCH_PREREQUISITE / EMPIRICAL_IDENTIFICATION_OPEN**

## 초록

이 run은 점을 먼저 고정하고 간선의 세기와 제거가 상태공간의 국소 비용을 바꾼다는 직관을 history Hilbert 공간의 operator metric으로 정식화했다. Coercive baseline과 norm summability 아래에서는 강한 Riemann metric과 간선 섭동 경계를 증명할 수 있다. 고립 spectral cluster는 Riesz 사영으로 유한 rank 부분공간을 정의하지만, recurrent loop 자체는 rank 4 또는 4--6을 선택하지 않는다. 비직교 Riesz 사영으로 정의했던 집중도는 완전 반례 때문에 폐기하고 직교 사영 $Q_d$를 쓰는 $c_d^\perp$로 교체했다. 따라서 현재 결과는 “거대 상태공간 안의 순간적 저차원 후보”를 검증 가능한 수학 가설로 만든 것이며, 인간 의식의 차원을 확정한 결과가 아니다. PowerShell과 Python/Numpy L0 witness는 각각 두 번 동일하게 통과했고 새 finite module의 focused test는 17/17, dimensionless focused test는 20/20 통과했다. SymPy 없는 parser 결과는 `PASS_SYNTAX_ONLY`로 기계적으로 제한되며, torch package facade와 실제 뇌 식별은 별도 범위로 남는다.

## 동기 서사와 범위

CE의 물리 서사는 끼임(환경이 선택을 강제함), 접힘(비선택 성분이 history와 숨은 상태로 보존됨), 암흑 표현(그 접힌 양의 우주론적 readout)으로 읽는다. 이번 뇌 모델은 앞의 두 단계에 대응하는 수학 후보다. 현재 상태 $x$에서 가능한 이동의 비용을 계량으로 나타내는 것이 끼임이고, node 상태와 edge history를 함께 보존하는 Hilbert 공간이 접힘이다. 암흑 표현은 별도의 우주론 bridge이며 이 run의 뇌 정리나 실증 결과가 아니다.

## 정의와 핵심 정리

상태공간은

$$
\mathcal H=\bigoplus_{v\in V}\mathbb R^{p_v}\oplus
\bigoplus_{e\in E}L^2_{\rho_e}(( -\infty,0],\mathbb R^{q_e})
$$

이고, 점 $x$를 고정한 국소 metric operator 후보는

$$
A_x(b)=A_{0,x}+\sum_e b_eD_e^*K_e(x)D_e,
\qquad g_x^{(b)}(u,v)=\langle u,A_x(b)v\rangle
$$

이다. $A_{0,x}\succeq m_0I$ ($m_0>0$), $K_e\succeq0$, bounded $D_e$, 그리고 $\sum_e\|D_e\|^2\|K_e\|<\infty$이면

$$
m_0I\preceq A_x(b)\preceq
\left(M_0+\sum_e\|D_e\|^2\|K_e\|\right)I.
$$

따라서 필요한 국소 smoothness 아래 $g$는 strong Riemann metric이다. Baseline coercivity가 없으면 이 결론은 거짓이다. 실제로 $A_0=0$, $D=(1,-1)$, $K=1$이면 $D^*KD$는 $(1,1)$ 방향의 kernel을 갖는다.

간선 가중치가 $b$에서 $b'$로 변할 때

$$
\|A(b')-A(b)\|\le
\epsilon_x:=\sum_e|b'_e-b_e|\|D_e\|^2\|K_e\|.
$$

$\epsilon<m_0$이면 metric과 국소 길이는 이에 비례해 제어된다. 다만 $b_e=0$으로 graph reachability가 바뀌는 사건은 연속적인 metric deformation과 동일하지 않으며, 이를 곧바로 curvature라고 부를 수 없다.

## 방향성, 순간 부분공간, 차원

후보 dynamics

$$
\dot x=-A_x^{-1}\nabla\mathcal V+S_xx+R_x(h)
$$

는 symmetric metric과 directed drift를 분리한다. 정확한 energy identity는

$$
\frac{d\mathcal V}{dt}=-\langle\nabla\mathcal V,A_x^{-1}\nabla\mathcal V\rangle
+\langle\nabla\mathcal V,S_xx\rangle+\langle\nabla\mathcal V,R_x(h)\rangle.
$$

$S^*=-S$만으로 두 번째 항이 사라지지 않는다. 중립성이 필요하면 $D\mathcal V(x)[S_xx]=0$을 별도로 요구해야 한다.

복소화된 bounded linearization $U_t^\Delta$에서 contour $\Gamma_d$가 유한 algebraic multiplicity $d$의 cluster를 고립시키면

$$
P_t^{(d)}=\frac{1}{2\pi i}\oint_{\Gamma_d}(zI-U_t^\Delta)^{-1}dz
$$

는 rank-$d$ Riesz 사영이다. $R=\sup_{z\in\Gamma}\|(zI-U)^{-1}\|$와 $R\|E\|<1$ 아래

$$
\|P(U+E)-P(U)\|\le
\frac{\operatorname{len}(\Gamma)}{2\pi}
\frac{R^2\|E\|}{1-R\|E\|}
$$

이며 rank가 보존된다. 이것이 “순간 저차원”의 증명 가능한 핵심이다. 그러나 loop가 특정 $d$를 강제하지는 않는다. 반복 recurrent block은 무한 multiplicity를 만들 수 있고, loop가 없는 diagonal system도 임의의 유한 center rank를 가질 수 있다.

따라서 $d\in\{1,2,3,4,5,6,8,10,12\}$는 사전고정 비교 menu다. 4--6은 현재 결과가 아니며, 미래에 rank 4가 선택돼도 그것은 관측된 후보 spectral subspace이지 곧바로 의식의 본질적 차원이 아니다.

실수 뇌 상태에 복소 spectral 계산을 사용할 때는 rank 규약도 고정해야 한다. 실수 고유값은 algebraic multiplicity 그대로 세고, 비실수 고유값은 켤레쌍 하나가 복소 multiplicity $m$마다 실수 $2m$차원을 만든다:

$$
d_{\mathbb R}=\sum_{\lambda\in\mathbb R}m_{\rm alg}(\lambda)
+2\sum_{\operatorname{Im}\lambda>0}m_{\rm alg}(\lambda).
$$

또한 Riesz 부분공간만으로 비선형 느린 다양체가 자동으로 생기지는 않는다. $C^r$ flow, 시간에 따른 invariant splitting, bounded projection, uniform exponential dichotomy 또는 normal-hyperbolicity gap, 충분히 작은 nonlinear remainder가 있을 때에만 graph transform이 contraction이 되어 중심 bundle에 접하는 국소 $C^{r-1}$ invariant graph를 준다. gap이 닫히거나 projection이 발산하거나 remainder가 크면 이 결론은 중단된다. 실제 뇌 기록이 이 가정을 만족한다는 증거는 아직 없다.

## 수정된 집중도와 유효차원

Riesz 사영은 일반적으로 비직교다. 실제 반례에서 $\operatorname{tr}(PCP)/\operatorname{tr}C=3/2$이므로 그 양을 $[0,1]$ 집중도로 쓰는 부모식은 폐기했다. 올바른 bounded observable은 $\operatorname{Ran}P_d$ 위의 직교 사영 $Q_d$를 이용한

$$
c_d^\perp=\frac{\operatorname{tr}(Q_dC Q_d)}{\operatorname{tr}C},
\qquad 0\le c_d^\perp\le1
$$

이다. 여기에는 $C\succeq0$, trace class, $\operatorname{tr}C>0$이 필요하다.

관측 pullback의 effective dimension은

$$
d_{\rm eff}(\lambda)=\operatorname{tr}[\widetilde G(\widetilde G+\lambda I)^{-1}]
=\sum_j\frac{\mu_j}{\mu_j+\lambda}
$$

이다. 이는 hard rank 이하이고 $\lambda$에 따라 감소하지만 ambient dimension, manifold dimension, consciousness dimension과는 다른 양이다. 고차원 open set을 더 낮은 유한차원으로 lossless하게 수동 복원하는 것은 rank-nullity와 국소 위상차원 때문에 불가능하다. 가능한 것은 many-to-one quotient prediction 또는 가정과 개입을 추가한 제한된 active identification이다.

## 구현, 재현성과 미완성 다리

감사 승인 식 세 개—$c_d^\perp$, 각 mode의 $\mu/(\mu+\lambda)$, $\eta_{\rm edge}=\epsilon_A/m_0$—를 dimensionless registry와 focused regression test에 추가했다. 모든 비는 같은 단위의 양끼리 나눈다. 물리 좌표를 $x=X_0\widetilde x$, $\mathcal V=V_0\widetilde{\mathcal V}$, $t=t_0\widetilde t$로 둘 때

$$
\mu_0=\frac{X_0^2}{V_0t_0}
$$

를 사용하면 $\dot x=-\mu_0A^{-1}\nabla_x\mathcal V$가 무차원 gradient flow로 바뀐다. 이 식은 차원 대수의 닫힘이며 $X_0,V_0,t_0$의 실제 생물학적 보정값을 제공하지는 않는다.

새 `history_edge_subspace.py`는 기존 `UnifiedMetricCore`의 의미를 바꾸지 않고 유한 L0 seam을 구현한다. Coercive baseline과 PSD edge contribution, adjacency와 metric availability의 분리, $\epsilon_A/m_0$ 충분조건, 대칭 또는 수치적으로 인증된 real-normal spectral subspace, 직교 집중도, effective dimension, mobility scale을 제공한다. 입력 허용오차는 숨기지 않는다. 대칭·PSD 정준화, normality·invariance·input-canonicalization residual, concentration의 symmetry·idempotence residual을 certificate로 기록하며, `positive_spectrum_rank`와 threshold 기반 `numerical_hard_rank`를 구분한다. 이는 일반 비정규 Riesz calculus가 아니다.

별도 `finite_riesz.py`는 유한 실수행렬의 비정규 원형 contour에 대해 $P_N$과 $P_{2N}$을 계산하고 sampled separation·resolvent norm, refinement·idempotence·commutator·imaginary residual, realified numerical rank와 직교 range projector $Q_N$을 함께 반환한다. 필수 `spectral_reference_scale`은 $U,c,r$와 같은 spectral unit을 가져 strict residual과 margin을 무차원화한다. 결과 지위는 `FINITE_A_POSTERIORI_CONTOUR_APPROXIMATION`이고 `quadrature_error_bound=None`이다. 따라서 exact $P$나 analytic-strip 오차 증명을 가장하지 않으며, 일반 무한차원 Riesz calculus도 여전히 범위 밖이다.

의존성 없는 `artifacts/spot_checks.ps1`와 Python/Numpy `artifacts/spot_checks.py`는 각각 두 번 실행되어 동일 JSON과 exit code 0을 냈다. Python 실제 operator norm은 $1.5244997998398395$로 PowerShell의 엄밀한 상계 $1.8$ 이하였고, 두 구현은 kernel, Riesz rank $2\to2$, projector 차이, 비직교 집중도 $1.5$, 직교 수정값 $0.5$, $d_{\rm eff}=1.5$에서 일치했다. `tests/test_history_edge_subspace.py`는 17/17, `tests/test_dimensionless.py`는 20/20 통과했다. SymPy가 없는 환경의 formula check는 backend와 evidence level을 노출한 `PASS_SYNTAX_ONLY`이며 symbolic proof로 승격하지 않는다. OpenBLAS 기본 worker 메모리 실패는 harness가 BLAS/OMP thread를 1로 고정하도록 수정해 재현 가능하게 닫았다. package doctor는 torch facade 부재로 실패한다. 이 실행들은 대수·구현 일치성 증거이며 operator 정리의 일반 증명이나 실뇌 검증을 대신하지 않는다.

## 후속 검증 경로와 반증 조건

네 경로는 구조적으로 구분된다. R1은 gauge를 고정한 유한 SPD family를 known intervention으로 식별하며 Gramian rank, coercivity, held-out 이득이 없으면 실패다. R2는 전체 $d$ menu를 비용에 포함해 recurrent perturbation과 matched feedforward control을 비교하며 recurrent-specific 안정성 차이와 held-out 승자가 없으면 실패다. R3는 passive observation quotient의 예측력만 raw/PCA/CCA/random projection 및 blind-tail control과 비교하며 독립 이득이 없으면 실패다. R4는 adjacency deletion, continuous metric deformation, matched-norm, sham을 분리하며 reachability·coercivity·held-out dynamics를 구별하지 못하면 실패다.

## 최종 판정

수학적으로 강화된 결과는 다음과 같다: coercive baseline이 있는 edge-operator 합은 strong local metric을 만들고, 작은 edge-weight 변화는 metric cost를 제어하며, 고립 spectral cluster는 순간 rank-$d$ 부분공간을 안정적으로 정의한다. 반대로 edge 연결성만으로 metric을 보장한다는 주장, skew drift가 자동으로 energy-neutral이라는 주장, loop가 4--6차원을 강제한다는 주장, 비직교 Riesz 집중도가 $[0,1]$이라는 주장은 폐기됐다.

그러므로 현재의 가장 정확한 설명은 “거대 history 상태공간 속에서 과제와 시간창에 따라 유한 rank 부분공간이 순간적으로 두드러질 수 있다”이다. “인간 의식은 4--6차원이다”는 아직 예측 후보이며 관측·식별·생물학 bridge가 남아 있다.

## 재현 자료

- 계약: `00-contract.md`
- 수학과 반례: `11-math.md`
- 독립 후속 경로: `12-routes.md`
- 형식 감사: `20-audit.md` (`Gate: PASS`)
- 구현과 검증 상태: `30-implementation.md`, `31-validation.md`
- 코드 대조와 구현 경계: `artifacts/41-code-map.md`
- 유한 L0 모듈과 집중 테스트: `reality_stone/python/reality_stone/clarus/history_edge_subspace.py`, `tests/test_history_edge_subspace.py`
- 유한 비정규 contour 모듈과 집중 테스트: `reality_stone/python/reality_stone/clarus/finite_riesz.py`, `tests/test_finite_riesz.py`
- 상세 독자 문서: `docs/6_뇌/12_리만부분공간_의식순간_강화.md`
- 동결 주장 원장: `docs/검증_원장/리만부분공간_의식순간_주장원장.md`

## 최종 contour–Riesz addendum

Theorem 10과 R5는 exact Riesz projector $P$와 원형 사다리꼴 근사 $P_N,P_{2N}$을 분리한다. 새 `finite_riesz.py`는 sampled separation·resolvent norm, refinement·idempotence·commutator·imaginary residual, realified numerical rank와 직교 range projector $Q_N$을 반환한다. 필수 `spectral_reference_scale`은 $U,c,r$와 같은 spectral unit을 가지며 strict residual을 무차원화한다. 지위는 `FINITE_A_POSTERIORI_CONTOUR_APPROXIMATION`, `quadrature_error_bound=None`이다. 이는 analytic-strip 오차 증명, full-contour pseudospectral 보증, 일반 무한차원 Riesz calculus가 아니다.

최종 순차 focused 결과는 contour 6/6, history-edge 17/17, dimensionless 20/20 PASS다. 병렬 Python 프로세스에서 발생한 MemoryError는 순차 실행으로 해소된 역사적 resource 사건이며 식·fixture·assertion을 바꾸지 않았다. 다섯 번째 후보 경로 R5는 contour enclosure, conjugation closure, resolvent, residual, rank 또는 필요한 analytic bound가 충족되지 않으면 `NONNORMAL_RIESZ_NOT_CERTIFIED`로 끝난다. 이 addendum은 앞의 오래된 “finite nonnormal runtime 없음” 표현을 대체하지만, 실뇌·의식·고정 4–6차원 식별을 승격하지 않는다.
