# 목표 완료성 감사

Status: INCOMPLETE

감사 대상 목표: 간략화된 수식을 최대한 강화하고, 후보식을 상세화하며, 빠진 부분을 증명·검증하고 코드에 반영한다.

| 요구사항 | 권위 있는 증거 | 판정 | 남은 일 |
|---|---|---|---|
| point-fixed edge metric 정식화 | `00-contract.md`, `11-math.md` Theorems 1–2 | 충족 | 실제 뇌 metric 식별은 별도 경험 문제다. |
| coercivity·summability·smoothness 조건 | `11-math.md`, canonical paper | 충족 | infinite unbounded operator/domain 확장은 범위 밖이다. |
| edge weight와 topology deletion 분리 | Theorem 2, R4, `history_edge_subspace.py` | 충족 | 실제 adjacency intervention 자료가 없다. |
| directed drift와 energy identity | Proposition 3 및 skew counterexample | 충족 | 실제 directed biological drift는 미식별이다. |
| 순간 spectral subspace와 perturbation | Theorems 4·10, normal 및 nonnormal finite certificate APIs | 조건부 충족 | exact/full-contour·analytic·infinite-dimensional 보증은 범위 밖이다. |
| real/complex rank 규약 | Convention 7 및 conjugate-pair tests | 충족 | focused Python test 17/17 통과. |
| nonlinear slow manifold | Theorem 9 graph-transform 조건부 정리 | 조건부 충족 | 실제 flow의 dichotomy/normal-hyperbolicity 가정 확인이 없다. |
| 4–6차원 주장 판정 | loop no-go, frozen full menu, R2 | 충족 | 4–6은 결과가 아니라 후보 menu다. |
| 집중도 수정 | P0-D 반례와 $c_d^\perp$, `ConcentrationCertificate` | 충족 | 실데이터 covariance 검증은 없다. |
| effective dimension·rank 분리 | Theorem 5, positive-spectrum/numerical rank API | 충족 | 관측 scale과 실제 데이터가 없다. |
| 물리 단위와 mobility | Proposition 8, `mobility_scale` | 대수 충족 / 교정 미완성 | $X_0,V_0,t_0$의 생물학적 calibration이 필요하다. |
| 후보식 R1–R5 상세화 | `12-routes.md`의 식·DOF·gauge·estimand·falsifier | 충족 | 새 데이터 계약과 독립 holdout 실행이 필요하다. |
| 코드 전체 대조 | `artifacts/41-code-map.md` | 충족 | 일반 history/Riesz runtime은 아직 없다. |
| 유한 L0 구현 | `history_edge_subspace.py`, `finite_riesz.py`, 독립 수학 리뷰, `Gate: PASS` | 충족 | 순차 focused tests 17/17 및 6/6 통과; analytic/infinite-dimensional Riesz는 범위 밖. |
| 결정론적 대수 witness | `spot_checks.ps1`, `spot_checks.py` | 충족 | 두 구현 모두 2회 동일 PASS; L0 ceiling 유지. |
| focused regression tests | `test_dimensionless.py`, `test_history_edge_subspace.py`, `test_finite_riesz.py` | 충족 | dimensionless 20/20, history 17/17, contour 6/6 PASS. Syntax fallback은 `PASS_SYNTAX_ONLY`로 제한. 병렬 MemoryError는 순차 실행으로 해소된 resource 사건이다. |
| 실제 뇌·의식 경험 검증 | `10-sources.md` SKIPPED, audit ceiling | 미충족 | provenance가 고정된 데이터·measurement model·split이 필요하다. |

## 완료 판정

형식 수학, 반례, 후보식, 상세 문서, 유한 코드, PowerShell/Python L0와 두 focused test는 강화·실행됐다. 그러나 전체 목표를 완전히 달성했다고 판정할 수는 없다. package doctor는 torch가 없고, 실제 뇌에서 metric·부분공간·차원 후보를 식별하는 경험적 bridge도 열리지 않았다. Syntax-only 결과는 symbolic proof가 아니라는 ceiling도 유지한다.

## 다음 재개 조건

1. package facade 전체 검증이 필요하면 repository contract에 맞는 torch prerequisite를 별도 승인·고정한다.
2. symbolic algebra backend 자체가 필요한 별도 연구에서는 SymPy 버전과 검증 의미를 새 계약에 고정한다. 현재 syntax/manual heuristic 결과를 symbolic proof로 부르지 않는다.

```powershell
.codex\hooks\python.cmd doctor
```

3. 실제 뇌 검증을 시작하려면 별도 successor contract에서 $F_{bio}$, measurement mapping, provenance, split, matched controls, rank menu, falsifier를 데이터 접근 전에 동결한다.
