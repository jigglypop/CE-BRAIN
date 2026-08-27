# 대안 경로 — 무조건 화살표의 구조적 수리

Status: COMPLETE

## Constructive successor selection

Epoch `artifacts/epochs/constructive-affine-fiber/12-routes.md` selects the
affine contracting-fiber route. It is analytically closed and supplies explicit
$M$, restricted dynamics, exact continuous lift, sensitivity, and a
cost-conditioned metric. An NHIM claim remains open because tangent/normal
domination is not assumed.

## 실제 자료 구조 경로 판정

전역 affine contracting-fiber 경험 모형은 DANDI `001701`의 동결 endpoint에서 `EMPIRICAL FAIL`이었다. persistence보다 시간 예측은 잘했지만 full VAR에 대한 1% 우위, bootstrap 양의 하한, 수축과 bunching을 모두 통과하지 못했다.

그 실패 뒤 사전 등록한 세 구조 피벗은 행동-조절 섬유, 행동 상태별 국소 bundle, 지연·LFP 결합 동역학이었다. 첫 번째 R1만 열었고, 이는 원 결과를 본 뒤 제안했으므로 outcome-informed 개발로 제한했다. R1도 `full VAR+input`과 `base+input`을 이기지 못하고 $q_{\max}>1$이어서 `STOP`했다. 따라서 임계값이나 차원만 다시 조율하지 않고, 확인용 DANDI `001695`도 열지 않았다. 나머지 R2/R3은 이 실패를 우회한 성공으로 간주하지 않으며 별도의 새 계약 없이는 열리지 않는다.

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
