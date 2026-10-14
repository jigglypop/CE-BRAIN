# CE-BRAIN Pattern-Jet

Pattern-Jet의 현재 핵심 가설은 공간 rank가 아니라 시간 이력의 고차원화다.

\[
J_K(t)=[x_t,\Delta_1(t),\ldots,\Delta_K(t)]
\]

Δ_k는 전체 loss의 역전파 delta가 아니라 현재/앞 상태와 느린 국소 상태 사이의 차이다.

## 현재 유효한 실데이터 결과

1. TEMPORAL_JET_TEST.md — 실제 시간축 C. elegans calcium trace에서 current-only / raw-lag / Pattern-Jet / parallel history / finite-difference를 leave-one-session-out으로 직접 비교.
2. temporal_results.json — 핵심 수치.
3. temporal_jet_test.py — 재현 코드.
4. PATTERN_JET_EQUATION.md — 후보식.

현재 판정:
- **다중시간척도 history state: 실데이터 지지**
- **exact serial cascade topology: 미식별**
- **synapse-by-synapse delta propagation: 미검증**
- **biological infinite-dimensional limit: 미검증**

## 폐기된 검증

RANK_TEST.md의 spatial rank 실험은 가설과 다른 대상을 계산했으므로 Pattern-Jet 검증에서 제외했다. 파일은 개발 이력 보존만을 위해 남긴다.

기존 Bergmann/Sun 필요조건 분석은 배경 증거로 유지하되, 시간축 직접 검증과 혼동하지 않는다.
