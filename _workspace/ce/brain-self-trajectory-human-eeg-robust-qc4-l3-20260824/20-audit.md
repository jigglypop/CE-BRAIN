# BA-SRM4-L3 stable-snapshot audit

Status: COMPLETE

Gate: PASS

Scope: PRE-IMPLEMENTATION AUTHORIZATION ONLY

## Frozen snapshot

| item | SHA-256 |
|---|---|
| `00-contract.md` | `04ea2bb2166916120bebf25c546646dd59f4bd20b4c97c4e9ba5de28f70a174d` |
| `10-sources.md` | `207ccb209276ab85435b2b864571e4511306f1b966ff6d24b36aa2023120f6ff` |
| `11-math.md` | `898960658ada3a181f2da1e9e87414135508e7e7a301ff609b0d98332c5acece` |
| `12-routes.md` | `fb82f423ac8c928bcacad0d63deb073ad7668e2a55ceca1e51ba1054c31c5fa8` |

## Gate findings

P0는 없다. BA-SELF1/2/3의 실패는 apparatus QC 실패로만 봉인되어 있고 뇌 동역학·자아·path 효과의 결과로 재사용되지 않는다. 새 R4는 유한 artifact를 bounded transform으로 다루고, 같은 관측·baseline에 area 하나만 추가한 $M_0/M_1$ 비교를 고정했다.

Cable/current equation은 출처가 있는 생물물리 출발 모형이다. $L^2_\rho$ history, causal $C^\infty$ conductance functional, smooth coercive infinite-dimensional metric은 `[공리: 모델 선택]`으로 남아 있다. EEG에서 neuron edge나 ambient metric을 복원하는 다리는 `[미완성]`이고 claim ceiling이 그 승격을 금지한다.

무차원 audit는 전압·시간·conductance·current·capacitance 기준척도, $\tanh(u/4)$, $\log p_k$, whitened area와 ridge penalty를 포함한다. CAR와 physical channelwise gain의 비가환성이 공개됐고 불변성 gate는 공통 gain·offset 또는 post-CAR orthogonal equivariance로 제한됐다.

단순 area sign reversal은 invalid matched null로 제거됐다. 마지막 increment를 고정한 20개 deterministic order shuffle은 endpoint, displacement, energy와 causal velocity를 보존하고 area만 바꾸며 매번 $M_1$을 refit한다. 이는 artificial contrast이고 p-value나 causal null이 아니다.

Signal-blind funnel은 D2-M 100 pair를 R0/R1/R2의 10/20/70으로 나누고, stage 실패 시 뒤 split을 열지 않는다. Pair마다 task/rest 두 design row가 있지만 독립 표본 수는 pair다. R0 $n=10,p=5$, R1 최대 $n=30,p_{active}\le19$이고 명시된 sample guard가 있다. zero loss denominator, zero-variance feature, nonfinite scale은 fail-closed한다.

## Residual P1

- scalp EEG는 neuron-level edge conductance, 실제 infinite-dimensional metric, hippocampal hash, self 또는 consciousness를 식별하지 못한다.
- robust scaling과 bounded transform은 자신의 scale을 키우는 넓은 artifact를 숨길 수 있으므로 saturation fraction과 predecessor QC를 diagnostic으로 보존해야 한다.
- B1과 D2-M은 같은 `sub-02` recording 계열이다. R2-LARGE는 held-out window validation이지 독립 subject/recording replication이 아니다.
- task/rest row는 같은 pair 안에서 상관될 수 있다. row 수는 design guard에만 쓰고 pair-clustered loss를 함께 보고해야 한다.
- `0.01` loss margin은 무차원 practical effect-size threshold이지 유의확률이 아니다.
- $M_1>M_0$이어도 augmented-state no-go 때문에 self가 존재론적으로 path라는 결론은 나오지 않는다.

## Authorization boundary

이 PASS는 implementation과 P0/A0 apparatus validation을 시작할 수 있다는 뜻뿐이다. 실제 EEG endpoint receipt가 없으므로 수치 PASS, 뇌 검증 성공 또는 생물학적 mechanism confirmation을 선언할 수 없다. 구현은 frozen snapshot과 10/20/70 access order를 hash-lock해야 한다.
