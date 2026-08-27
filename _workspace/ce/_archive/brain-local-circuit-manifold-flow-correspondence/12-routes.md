# 대안 경로 — 무조건 화살표의 구조적 수리

Status: COMPLETE

## Constructive successor selection

Epoch `artifacts/epochs/constructive-affine-fiber/12-routes.md` selects the
affine contracting-fiber route. It is analytically closed and supplies explicit
$M$, restricted dynamics, exact continuous lift, sensitivity, and a
cost-conditioned metric. An NHIM claim remains open because tangent/normal
domination is not assumed.

T2의 비닫힌 다양체 반례를 결과 뒤 문구 수정으로 숨기지 않고
`artifacts/epochs/t2-open-manifold-escape/`에 잠갔다. 아래 경로는 서로 다른
구조적 추가물을 사용한다.

| 경로 | 추가 구조 | 조건부 결론 | kill condition |
|---|---|---|---|
| R1 닫힌 level-set/tangency **[선택]** | 닫힌 embedded $M$과 $F(x,t)\in T_xM$; level-set이면 submersion $h$와 $Dh_xF=0$ | ambient 존재구간 전체의 불변성, $b=F|_M$ | 닫힌 $M$의 tangent locally Lipschitz field가 ambient endpoint 전에 이탈 |
| R2 proper latent equivariance | proper $e:Z\hookrightarrow X$, latent $f$, $F\circ e=De\,f$ | 공통 최대 존재구간의 $M=e(Z)$와 conjugate flow; $f,F$ complete일 때만 전시간 | equivariance residual, nonproper escape 또는 latent uniqueness 실패 |
| R3 normal-hyperbolic graph | tube, split, $q<1$ graph contraction, bunching, continuous-flow class 보존 | 유일한 invariant graph와 제한 flow | gap/bunching/collar/commutation 중 하나라도 실패 |
| R4 discrete/hybrid 유지 | $\Phi(M)\subseteq M$만 증명 | $(M,\Phi|_M)$; $b$ 주장은 하지 않음 | autonomous embedding을 주장하면서 orientation/injectivity/isotopy gate 실패 |

R1을 선택한 이유는 원문이 원하는 동일 ambient state 안의 $(M,b)$를 가장 적은
추가 구조로 보존하기 때문이다. R2는 latent coordinates가 실제로 주어질 때의 독립
구성이고, R3은 spectral gap을 측정할 수 있을 때의 독립 구성이다. threshold·TopK·
branching raw update에는 R4가 기본이며 continuous $b$를 억지로 보간하지 않는다.

실제 neural 연구 재개에는 source-locked $F$, chart/constraint, tangency residual,
held-out tube와 gap 또는 proper latent map이 필요하다. 현재는 어느 경로도 실제 뇌
자료로 검증되지 않았다.
