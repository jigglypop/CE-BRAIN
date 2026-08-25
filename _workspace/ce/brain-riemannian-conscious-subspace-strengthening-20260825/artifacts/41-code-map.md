# 코드 전체 대조: 기존 unified metric과 강화된 history-edge subspace

Status: COMPLETE

## 결론

기존 코드는 고정된 유한 그래프 위의 nodewise SPD metric, 경로 길이와 routing을 구현한다. 이번 이론의 history Hilbert 공간, 일반 Riesz calculus, directed drift, 순간 의식 차원은 기존 코드에 구현되어 있지 않았다. 따라서 기존 클래스의 의미를 넓히지 않고 `history_edge_subspace.py`에 유한 L0 수학 seam을 분리 구현했다.

## 기존 구현의 정확한 범위

| 대상 | 기존 코드 | 판정 |
|---|---|---|
| topology | `unified_metric.py`의 adjacency를 boolean edge mask로 고정 | 연결 여부는 표현하지만 연속 adjacency weight는 저장하지 않는다. |
| node metric | `UnifiedMetricState.metric`의 nodewise SPD 행렬 | 유한 그래프 metric의 구현이며 history-space operator가 아니다. |
| deformation | `metric_deformation`, `apply_source_metric` | $G-G_{ref}$와 convex SPD update이며 $\sum b_eD_e^*K_eD_e$는 아니다. |
| routing | endpoint-average edge length와 Dijkstra shortest path | 유한 metric graph analogue다. continuum geodesic, connection, curvature는 아니다. |
| metric learning | `CovariantMetricFlow.update`의 AIRM rank-one update | $\dot x=-A^{-1}\nabla V+Sx+R$ dynamics나 mobility bookkeeping은 없다. |
| history | 별도 synthetic leaky-history benchmark | scalar benchmark이며 history Hilbert direct sum이 아니다. |
| Riesz/subspace | 기존 구현 없음 | contour resolvent, gap, rank stability가 없었다. |
| concentration/effective dimension | dimensionless registry의 scalar surrogate | 단위 계약만 있었고 numerical API는 없었다. |

## 새 유한 L0 seam

`reality_stone/python/reality_stone/clarus/history_edge_subspace.py`는 다음을 구현한다.

1. `FiniteEdgeMetric`: coercive symmetric baseline과 `EdgeContribution(D,K,b)`를 검사하고 $A(b)=A_0+\sum bD^TKD$를 계산한다.
2. `PerturbationCertificate`: 실제 finite spectral norm, 정리 상계 $\sum|\Delta b|\|D\|^2\|K\|$, $m_0$, 상계비 $\eta$와 충분조건 $\eta<1$을 분리한다.
3. `topology_with_deleted_edges`: adjacency 삭제를 metric availability 변경과 별도 입력으로 처리한다.
4. `spectral_subspace`: symmetric 또는 residual로 인증된 real-normal finite matrix의 고립 cluster만 받는다. 일반 nonnormal 입력은 거부하며 결과를 일반 Riesz 사영이라고 부르지 않는다.
5. `ConcentrationCertificate`: 입력 사영의 symmetry/idempotence residual을 기록하고 허용된 근사 입력을 정준 직교 사영으로 만든 뒤 $\operatorname{tr}(QCQ)/\operatorname{tr}C$를 계산한다.
6. `effective_dimension`: $\sum\mu/(\mu+\lambda)$, `positive_spectrum_rank`, threshold 기반 `numerical_hard_rank`를 서로 다른 필드로 반환한다.
7. `mobility_scale`: $X_0^2/(V_0t_0)$를 계산하되 실제 생물학 calibration이라고 해석하지 않는다.

## 경계 입력에서 발견하고 수정한 결함

초기 구현 감사에서 다음 결함을 반례로 찾아 수정했다.

- 근사 대칭 입력을 원본 그대로 저장해 self-adjoint가 깨질 수 있던 문제: 허용 범위 안에서 정준 대칭화한다.
- 작은 음의 고유값을 그대로 받아 $d_{eff}<0$이 될 수 있던 문제: 허용 roundoff band만 PSD cone으로 투영하고 그 아래는 거부한다.
- $d_{eff}$는 작은 양의 모드를 세지만 threshold rank는 세지 않아 상계가 깨지던 문제: positive-spectrum rank와 numerical rank를 분리한다.
- near-real complex eigenvalue 한쪽을 실수 mode처럼 셀 수 있던 문제: ambiguity band를 거부하고 켤레쌍을 일대일·중복도까지 검사한다.
- 근사 projector의 오차를 숨기던 문제: symmetry/idempotence residual과 정준 projector를 certificate에 노출한다.

## 검증 상태

`tests/test_history_edge_subspace.py`는 coercivity, baseline-free kernel, 섭동 상계, topology/metric 분리, symmetric/real-normal subspace, nonnormal 및 near-real 거부, 반복 켤레쌍, PSD roundoff 경계, 두 rank 규약, concentration certificate, mobility를 겨냥한다. 독립 수학 리뷰와 형식 감사는 이 테스트 설계 및 코드를 `Gate: PASS`로 판정했다.

정책 허용 Python 3.14.2를 hook이 발견한 뒤 이 pytest는 17/17 통과했다. Python/Numpy와 PowerShell L0 fixture도 각각 두 번 동일하게 통과했다. dimensionless focused 결과도 20/20 통과했으며, SymPy가 없는 backend의 formula 결과는 `PASS_SYNTAX_ONLY`와 `SYNTAX_ONLY_HEURISTIC`를 노출한다. OpenBLAS 기본 worker 메모리 실패는 harness가 numerical thread 수를 1로 고정해 해결했다. 전체 package doctor는 torch facade 부재로 실패하지만 standalone finite module 결과와는 분리된다.

## 남은 구현 경계

- infinite-dimensional history operator와 domain/closedness 처리
- general infinite-dimensional Riesz calculus, analytic contour error bound, full-contour pseudospectral certification
- 실제 flow에서 normal hyperbolicity/dichotomy 추정
- 생물학적 $F_{bio}$, measurement mapping, mobility/time-scale calibration
- 독립 실데이터에서 후보 rank menu와 matched controls 검정

## 최종 finite nonnormal contour seam

`reality_stone/python/reality_stone/clarus/finite_riesz.py`는 기존 normal-only API와 분리된 유한 원형 contour 근사다. exact $P$를 주장하지 않고 $P_N,P_{2N}$, raw sampled separation/resolvent, 무차원 normalized residual, realified rank, oblique approximation과 구분된 직교 $Q_N$을 노출한다. `spectral_reference_scale`은 $U,c,r$와 같은 단위의 필수 입력이고 `quadrature_error_bound`는 `None`이다.

`tests/test_finite_riesz.py`는 oblique 3×3 fixture, 단위 재스케일, contour crossing, coarse quadrature rank guard, 켤레 rotation, pseudospectral adversary를 겨냥하며 순차 실행 6/6 통과했다. 최종 focused 스냅샷은 contour 6/6, history-edge 17/17, dimensionless 20/20 PASS다. 병렬 실행의 MemoryError는 순차 실행으로 대체된 resource 사건일 뿐 모델 검증 실패가 아니다.
