# Deterministic witness implementation

Status: COMPLETE

## Constructive successor implementation

The deterministic standard-library fixture is frozen at
`artifacts/epochs/constructive-affine-fiber/verify_constructive.py` and copied to
the canonical paper at
`docs/6_뇌/국소회로_상태다양체_흐름_대응/repro/verify_constructive.py`.
It checks one fixed $S^1$ realization with $A=\operatorname{diag}(0.2,0.4)$ and
$c(\theta)=(\sin\theta,\cos2\theta)$ against C1--C6: graph and derivative
invariance, exact fiber attraction, continuous lift parity, dimensionless
exponents, sensitivity, Lyapunov identity, and metric positivity. Details are in
`artifacts/epochs/constructive-affine-fiber/30-implementation.md`.

`artifacts/verify_correspondence.py` is a dependency-free Python standard-library
binary64 regression harness.  It implements five fixed witnesses used by the
conditional mathematics in `11-math.md` and the route boundary in `12-routes.md`.
No empirical neural data, fitted parameter, random seed, or third-party package is
used.

| Witness | Fixed construction | Regression assertion | Mathematical role |
|---|---|---|---|
| Positive closed-manifold case | `S1`, `F(x,y)=(-y,x)` | `abs(x*Fx+y*Fy) <= 1e-12` at 16 fixed points | Tangency is compatible with an invariant closed embedded manifold. |
| Open escape | `M=(0,1)`, `F=1`, `x(0)=1/2` | `x(1/2)=1` is not in `M` | Refutes no-escape from tangency alone on an open image. |
| Cusp | `Phi(u,0)=(u^2,u^3)`, `u=+/-1/8` | equal positive horizontal coordinate, nonzero opposite vertical coordinates | Exhibits the two-branch obstruction at a cusp. |
| Discrete obstruction | `Phi_minus(x)=-x`; `Phi_square(x)=x^2` | determinant `-1`; `Phi_square(-1/2)=Phi_square(1/2)` | Records orientation reversal and noninjectivity, either of which obstructs an autonomous ODE time-one map. |
| Metric nonidentifiability | `M=R2`, `b=(1,0)`, `g1=diag(1,1)`, `g2=diag(1,2)` | equal drift norm squared and `grad_g x=b`, but distinct transverse coefficients | Shows that `(M,b)` alone does not identify a metric. |

The values `1/2`, `1/8`, `1/64`, `1/512`, and the diagonal entries are exactly
binary-representable.  The circle samples invoke standard-library `sin` and `cos`,
so their tangency check is deliberately tolerance-based (`1e-12`).

## Interpretation boundary

The program is numerical regression evidence that the encoded constructions and
their finite-precision predicates have not changed.  It does not prove the
theorems or counterexamples.  The proofs remain analytic: the circle identity is
`x(-y)+y(x)=0`; the open trajectory is `x(t)=1/2+t`; the cusp has both
`(x,+x^(3/2))` and `(x,-x^(3/2))` for every local `x>0`; autonomous ODE flow maps
are injective and orientation-preserving on `R`; and the two displayed SPD
metrics differ in the transverse direction despite agreeing on the listed drift
facts.

## 실제 DANDI 구현

실제 자료 endpoint는 `artifacts/epochs/real-dandi-001701/analyze_real_dandi.py`와 `artifacts/epochs/real-global-affine-fiber-fail/pivots/r1-behavior-controlled-fiber/analyze_behavior_pivot.py`에 고정했다. 두 스크립트는 DANDI API에서 정확한 asset UUID를 받아 바이트 수와 SHA-256을 확인하고, 소유한 임시 디렉터리에서 NWB를 읽은 뒤 원 파일을 삭제한다. train-only unit retention·정규화·PCA, 시간순 train/development/test 분할, 독립 대조 모형 조율, test 선택 차단, 쌍체 block bootstrap을 구현했다.

정본 재현 코드는 `docs/6_뇌/국소회로_상태다양체_흐름_대응/repro/`에 복사했다. 원 NWB는 저장하지 않고 집계 결과와 출처 영수증만 둔다.
