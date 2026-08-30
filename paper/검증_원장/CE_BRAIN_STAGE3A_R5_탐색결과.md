# CE-BRAIN Stage 3A R5 탐색 결과

## 판정

`EXPLORATORY_REPRESENTATION_TENSION`

이 판정은 “국소 뇌 기하가 존재하지 않는다”는 반증이 아니다. 사전등록 Stage 3A는 표본수 문턱을 통과하지 못했고, R5는 그 뒤 수행한 탐색 분석이다. 따라서 후보 생성에는 쓸 수 있지만 Stage 4를 허가하거나 포유류 뇌의 기하를 확정할 수 없다.

## 실제 분석량

- template node 299개, 적격 stimulus event 428개
- development 10,766간선·62개체, 양성 782간선
- confirmation 4,631간선·28개체, 양성 288간선
- development에도 있던 common pair 1,686행
- development에서 보지 않은 source 1,121행

원래 확인 계약의 최소량은 development 20,000, confirmation 10,000, common pair 5,000이었다. 따라서 확인적 Stage 3A는 `coverage stop`이다.

## 후보 경쟁

공통 간선에서 log loss는 F 0.252183, R 0.252775, S 0.258160, O 0.258470, null 0.261009, graph 0.364343 순이었다. F는 null보다 평균 3.38% 나았지만 bootstrap 95% 하한이 -1.05%였고, R도 평균 3.15% 개선에 하한 -1.36%였다. F가 R보다 나은 정도는 0.234%뿐이며 하한 -0.899%라 방향성 기하의 승리로 볼 수 없다.

처음 보는 source에서는 O 0.216820, S 0.219111, null 0.219833, F 0.226991, R 0.227788 순이었다. O의 null 대비 개선은 1.37%이고 하한 -1.27%라 일반 연산자도 확립되지 않았다. F와 R은 오히려 null보다 나빴다.

## 공리 진단

- 3개체 이상에서 양방향으로 반복된 pair는 3개뿐이었다. 절대 방향차 중앙값은 0.025였지만 표본이 너무 작다.
- 3개체 이상 반복된 directed pair는 102개, 완성된 directed triad는 125개뿐이었다. 계약 문턱 1,000개에 못 미쳐 삼각부등식은 `NOT_IDENTIFIABLE`이다.
- 그러므로 local Riemannian-like, directional Finsler, switching, graph, general operator 중 어느 것도 독립 확인 승자로 승격되지 않는다.

## 쉬운 말 결론

가까운 뉴런끼리 잘 전달된다는 단순 지도 R과, 방향까지 고려한 지도 F가 기존에 본 자극에서는 약간 도움을 줬다. 하지만 둘의 차이는 사실상 작고 불확실했다. 더 중요한 것은 처음 보는 자극원으로 옮기면 그 이점이 사라졌다는 점이다. 즉 현재 데이터는 하나의 국소 거리법칙이 새 위치에도 그대로 통한다고 보여주지 못한다.

이 실패의 핵심은 두 가지다. 첫째, 국소 기하의 예측력이 약하고 일반화되지 않았다. 둘째, 대칭성과 삼각부등식을 시험할 반복 양방향 간선·삼각형 자체가 너무 적다. 따라서 현재 정확한 표현은 “국소 기하가 거짓”이 아니라 **“국소 기하가 아직 확립되지 않았고, 현재 표본에서는 표현 긴장이 남았다”**이다.

## 재현 영수증

- manifest SHA-256: `a58093907ab70c8fd849688db2b177a910bf6d300731f53f7fc23958a654ba9f`
- result SHA-256: `fc8979a2bfb3929084ed9b09d477819b3578d3db41bb5306346aa347f3a78d94`
- validation SHA-256: `c1bfb2f020fd7a507cd87f11c98a3c7cbd2856676b46bef95cd296667069adba`
- raw recomputation: `PASS`
- Stage 4 authorized: `false`

## 다음 최소 증명 의무

새 데이터에서 source별 반복을 늘리고, confirmation에 3개체 이상 반복된 directed pair와 완성 triad를 충분히 확보한 뒤 R/F/S/O를 다시 사전등록한다. 특히 held-out source에서 null보다 5% 이상 개선하고 신뢰구간 하한이 0보다 커야 후보를 유지한다. Riemannian-like 후보는 별도로 삼각부등식 문까지 통과해야 한다.
