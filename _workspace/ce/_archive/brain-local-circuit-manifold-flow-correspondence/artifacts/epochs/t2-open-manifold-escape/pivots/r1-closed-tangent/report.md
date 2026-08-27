# 구조 피벗 결과: r1-closed-tangent

Status: COMPLETE

## 선택 결과

비닫힌 embedded manifold에 tangency만 요구한 부모 T2는
`counterexample.json`의 $X=\mathbb R$, $M=(0,1)$, $F=1$ witness로 철회했다.
선택 경로는 $M$이 ambient $X$에서 닫힌 embedded submanifold이고
$F(x,t)\in T_xM$인 경우다.

`11-math.md`의 T2-R1은 T1의 locally uniform Lipschitz/uniqueness 조건 아래 이
가정이 ambient 최대 존재구간 전체의 invariance와 유일한 제한 흐름
$b_t=F(\cdot,t)|_M$를 준다는 것을 증명한다. `20-audit.md`의 최종 독립 재감사는
`Gate: PASS`이며, open-interval adverse control은 새 closedness 가정에서 정확히
배제된다.

## 지위와 경계

결과는 `[조건부 정리]`다. 닫힌 후보 manifold, tangency, 또는 실제 neural
constitutive field가 관측됐다는 경험 결과가 아니다. proper latent embedding과
정량 graph-transform은 `12-routes.md`의 독립 대안으로 남고, 실제 뇌 재개에는
source-locked $F$, measurement model, held-out tangency/flow 검사가 필요하다.
