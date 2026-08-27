# 국소 회로에서 상태다양체와 흐름으로 가는 조건부 대응: 연구 계약

Status: COMPLETE

## Constructive successor (authoritative extension)

The no-go results below delimit arbitrary inputs; they are not the endpoint of
this run. Epoch `artifacts/epochs/constructive-affine-fiber/` proves the positive
class

$$
G,W\xrightarrow{\mathrm{declared\ local\ realization}}(P,A,c),\qquad
\Phi(z,y)=(Pz,Ay+c(z)),
$$

with $\|A\|_2\le q<1$ and $q\sup\|DP^{-1}\|<1$. It constructs the unique $C^1$
invariant graph $M$, restricted dynamics, an exact continuous-time field $b$
when a base generator $f$ is supplied, quantitative stability, and a
cost-conditioned metric $g_M$ when a base cost $G_Z$ is supplied. Biological
realization remains UNVERIFIED.

Mode: full

## 질문과 주장 상한

첨부된 「뉴런–동적 기하 가설」의 마지막 명제

$$
(G,W,\Phi)\Longrightarrow(M,b)
$$

를 무조건적 생물학 명제가 아니라 정확한 수학 명제로 판정한다. 목표는 다음 세
항목이다.

1. 국소 회로 자료가 상태 벡터장과 유일한 국소 흐름을 정하는 충분조건을 증명한다.
2. 접근 가능 집합이 매끄러운 불변다양체가 되는 추가조건을 밝히고, 그 조건 아래
   $(M,b)$ 대응을 증명한다.
3. 추가 가정 없이 $M$ 또는 회로 비용 계량 $g$가 따라온다는 강한 명제에는 완전한
   반례를 제시한다.

주장 상한은 **조건부 수학 정리와 반례**다. 실제 뇌의 회로가 이 조건을 만족한다는
경험적 주장, 의식 동일시, 실제 신경 계량의 식별은 이 계약의 결론이 아니다.

## 정의역과 기호

- $G=(V,E)$: $N<\infty$인 유향 그래프. $j\to i\notin E$이면 $i$번째 국소 법칙은
  $x_j$에 의존하지 않는다.
- $W=(w_{ij})$: 고정 또는 시간의존 edge parameter. 물리 단위가 있는 경우 각 입력은
  계약된 기준척도로 정규화한다.
- $X\subseteq\mathbb R^N$: 열린 population state chart.
- $F_{G,W}:X\times I\to\mathbb R^N$: 국소 회로 연속시간 법칙,
  $\dot x=F_{G,W}(x,t)$.
- $\Phi_{G,W}:X\to X$: 이산시간 국소 갱신 법칙.
- $M\subset X$: $C^r$ embedded submanifold 후보.
- $b_t=F_{G,W}(\cdot,t)|_M$: tangency가 성립할 때의 제한 벡터장.
- $\varphi_{t,s}$: $b$의 유일한 국소 flow/evolution family.

## 동결한 정리 후보

**T1 (회로→벡터장→흐름).** $F_{G,W}$가 $x$에 대해 locally Lipschitz이고 $t$에
대해 연속이면 각 초기값에 유일한 최대해가 존재한다. 따라서 $(G,W,F)$는 정의역과
종료시각까지의 국소 evolution family를 정한다. cocycle 식은 세 map이 모두 정의되는
공통 자연 정의역에서만 주장한다.

**[철회된 부모 T2/T3].** 비닫힌 embedded image에도 ambient 최대 존재구간 전체의
불변성을 주장한 원래 문장은 `RETRACTED`다. $X=\mathbb R$, $M=(0,1)$, $F=1$이
완전 반례이며 `artifacts/epochs/t2-open-manifold-escape/`에 잠겨 있다.

**T2-R1 (불변다양체 제한; 반례 뒤 대체).** $M$이 닫힌 $C^1$ embedded이고 모든 $(x,t)\in M\times I$에
대해 $F_{G,W}(x,t)\in T_xM$이면 T1의 해는 존재하는 동안 $M$에 머물며
$b_t=F_{G,W}|_M$가 $M$ 위의 유일한 국소 흐름을 정한다.

**T3-R1 (잠재상태/등변 임베딩 대응; 반례 뒤 대체).** $Z$가 $d$차원 $C^r$ 다양체, $e:Z\to X$가
proper $C^r$ embedding, $f_t$가 $Z$의 locally Lipschitz $C^{r-1}$ 벡터장이고

$$
F_{G,W}(e(z),t)=D e_z f_t(z)
$$

이면 $M=e(Z)$는 닫힌 불변다양체이고 공통 최대 존재구간에서 $b_t=e_*f_t$다. 반대로 $b_t$가 $M$에 접하면
$f_t=(D e)^{-1}b_t\circ e$가 유일하다.

**T4 (정상쌍곡 불변그래프 경로).** 고정점/궤도 주변의 동결 split에서 (i) graph
class가 complete이고 transform이 $q<1$ contraction이며, (ii) bunching이 fixed
graph를 $C^1$으로 올리고 그 image가 $X$에서 closed embedded graph임을 보장하며,
(iii) 해당 tube의 공통 flow 존재구간에서 flow가 같은 graph class를 보존하고 graph
transform과 commute하면 그 공통 존재구간에 유일한 continuous-flow invariant graph
$M$이 생기고 T2-R1이 적용된다. 이 정리는 선행 CE graph-transform 정리의 조건부
재사용만 허용하며 실제 neural spectral gap을 가정하지 않는다.

**N1 (무조건 명제의 반례).** 임의의 국소 갱신법칙의 접근 가능 집합은 매끄러운
다양체일 필요가 없다. 비가역 분기/임계/프랙탈 예를 하나 이상 고정해
$(G,W,\Phi)\Rightarrow M_{\rm smooth}$를 기각한다.

**N2 (이산 map의 autonomous-flow 비포함).** 모든 $\Phi$가 같은 $M$ 위 자율
벡터장의 time-one map은 아니다. orientation-reversing map 또는 비단사 map을
witness로 사용한다. 필요하면 time-dependent isotopy 또는 mapping-torus
suspension을 별도 조건부 대안으로만 기록한다.

**N3 (계량 비식별).** $(M,b)$만으로 회로 비용 계량 $g$는 유일하지 않다.
동일한 $(M,b)$와 양립하는 서로 다른 SPD metric 두 개 이상을 명시한다.
따라서 $(G,W,\Phi)\Rightarrow(M,g,b)$에는 별도의 비용/잡음/관측 공리가 필요하다.

원래 T2/T3의 비닫힌 image 문구는 완전 반례로 철회되었다. 반례·세 대안 경로·선택
pivot은 `artifacts/epochs/t2-open-manifold-escape/`에 보존한다.

## 허용 오차와 판정 규칙

- T1--T4는 가정에서 결론까지 논리적 공백이 없을 때만 `[조건부 정리]`다.
- N1--N3는 가정을 만족하는 구체 witness와 위반 결론을 모두 제시해야 한다.
- 수치 검증은 증명이 아니라 유한 witness/회귀검사다. 허용 오차는 binary64
  상대오차 $10^{-10}$, 절대오차 $10^{-12}$로 동결한다.
- 실제 데이터 endpoint는 열지 않는다. 경험적 주장의 truth value는 `UNTESTED`다.

## 뇌 연구 필수 필드

| 필드 | 동결 내용 |
|---|---|
| `BIO_STARTING_MECHANISM` | 유한 population-state의 국소 ODE/이산 update라는 모델 클래스. 실제 뇌의 특정 기전식으로 승격하지 않는다. |
| `CE_DELTA` | 없음. 이번 연구는 첨부 가설을 정리/반례로 정규화한다. |
| `MEASUREMENT_MODEL` | 없음; 실제 기록값을 사용하지 않는다. |
| `DATA_PROVENANCE` | 첨부문 두 파일 및 저장소 선행 CE 정리. 외부 1차 출처는 정의·배경 확인에만 사용한다. |
| `DATA_SPLIT` | 해당 없음; 결정론적 수학 witness만 사용한다. |
| `OBSERVABLES` | tangency residual, flow uniqueness, manifold-rank, orientation/determinant, metric nonuniqueness witness. |
| `RESIDUAL_RULE` | 정리 가정 위반 또는 반례 witness 불성립이면 해당 주장 STOP. |
| `FALSIFIER` | N1--N3 중 하나라도 실패하거나 T1--T3에 숨은 가정이 발견되면 Gate REVISE. |
| `MATCHED_CONTROLS` | smooth invariant embedding(양성), branching/noninvertible/orientation-reversing map(음성), 두 SPD metric(비식별). |
| `MODEL_SELECTION` | 가장 약한 충분조건을 우선하며 metric 없는 $(M,b)$를 기본 결론으로 선택한다. |
| `REVISION_TRIGGER` | 완전 반례는 부모 주장을 철회하고 조건을 추가한 서로 다른 구조 경로 3개를 비교한다. |
| `CLAIM_CEILING` | L0 수학/결정론 witness. 실제 neural manifold, 생물학 기전, 의식·AGI 증명 금지. |

## PREDECESSOR_EVIDENCE

| 선행 결과 | 상태 | 보존 주장 | 이번 연구의 경계 |
|---|---|---|---|
| `brain-algorithm-route-ledger.md` BA-A6-P | `MATH_PASS / EMPIRICAL_UNTESTED` | full-rank flow derivative의 pullback은 조건부 passive metric | metric을 회로 비용이나 생물학 계량으로 승격하지 않는다. |
| 같은 원장 BA-G2 | `STOP` | SPD metric feature가 raw dynamics보다 충분하지 않았음 | $g$ 우선 경로를 반복하지 않는다. |
| `docs/6_뇌/11_리만계량_라우팅_논문.md` | 조건부 수학 + simulator 경계 | smooth branch Jacobian과 이산 경계의 비미분성을 분리 | hybrid/threshold map을 매끄러운 flow로 가정하지 않는다. |
| `brain-riemannian-conscious-subspace-strengthening-20260825` | 조건부 graph-transform 계열 완결, empirical bridge 미완성 | 수축/bunching 아래 불변그래프 경로 | 실제 neural vector field·collar·spectral gap은 새 증거 없이는 채택하지 않는다. |

## 재시도 금지와 재개 조건

- covariance inverse를 neural metric으로 재명명하지 않는다.
- graph shortest path의 근사 성공을 회로가 Riemannian metric을 계산한다는 증거로
  승격하지 않는다.
- 실제 뇌 대응을 재개하려면 동일 세션에서 source-locked 회로 변수, 측정모형,
  개입 또는 held-out flow, tangency/rank/spectral-gap 검사가 필요하다.

PREDECESSOR: `_workspace/ce/brain-algorithm-route-ledger.md` 및 위 표의 직접 선행물
