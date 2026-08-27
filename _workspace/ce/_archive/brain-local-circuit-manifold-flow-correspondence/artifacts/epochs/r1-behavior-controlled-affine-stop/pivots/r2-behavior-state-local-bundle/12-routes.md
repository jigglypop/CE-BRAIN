# R1 STOP 뒤 구조 경로

Status: COMPLETE

R1의 전역 behavior-modulated affine family 실패를 threshold나 latent dimension
재조율로 반복하지 않고, 서로 다른 항을 바꾸는 세 경로를 결과 접근 전에 비교했다.

| 경로 | 구조 변경 | 새 핵심 자유도 | 독립 falsifier와 matched control | 데이터 경계 | 판정 |
|---|---|---|---|---|---|
| R2 behavior-state local bundle | interaction: global operator를 behavior-only chart별 tangent/base/fiber로 교체 | 고정 $K=4$, chart별 $U_i,B_i,A_i,C_i$; $d,\lambda$만 dev 선택 | chart-matched local full VAR, global matched fiber, 100-bin shifted chart, $q_i^{\rm ub}<1$ | 이미 열린 001701 development만; 001695 sealed | **SELECTED** |
| R3 delay+LFP coupled dynamics | state: spike delay embedding과 source-locked LFP state 추가 | 사전 고정 delay와 LFP phase/amplitude state | spike-only delay, phase-shifted LFP, timing/reference gate | LFP schema·reference·band의 새 source contract 전에는 unopened | DEFERRED |
| R4 switching count observation | measurement: Anscombe-Gaussian 대신 explicit Poisson/negative-binomial observation | latent switch, transition, count link와 overdispersion decision | matched Gaussian observation, no-switch, contiguous-block label permutation | 새 likelihood·identifiability·initialization contract 필요 | DEFERRED |

세 fingerprint는 각각 interaction/state/measurement를 바꾸므로 seed·threshold·endpoint
변형이 아니다. R2는 기존 자산의 verified Position/CompassDirection과 직접 연결되고,
chart partition을 neural outcome 없이 만들며, partition-only 이득을 local full VAR로
분리할 수 있어 선택했다. 이 선택은 R2 결과를 보기 전에 `portfolio.json`에 잠겼다.

R2가 죽어도 R3/R4가 성공했다는 뜻은 아니다. R3/R4는 각각 새 source·측정 계약과
자체 adverse control 없이는 열리지 않는다.
