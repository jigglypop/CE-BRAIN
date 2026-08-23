# BA-SRM8 형식 지위 감사

Status: COMPLETE

Gate: PASS

Date: 2026-08-23

## 1. 판정

BA-SRM8의 physical-time mask-aware weighted covariance, 정확히 48개인 후보 manifest,
behavior-blind apparatus gate와 70/2/3/2.5/2.5/20 funnel을 안정 판본에서 감사했다.

P0: 없음. historical F1-v3/v4/v5는 documented full-$T$, ceil-boundary, constant-truth/provenance 문제로 superseded됐고, self-contained F1-v6과 valid F0-v3만 현재 F1 promotion source다.  
P1: 없음.

final math re-audit와 status re-audit는 PASS이며, frozen validation vector 36개 array의 mismatch는 0이다. F2-A만 synthetic apparatus로 실행하도록 허가한다. F2-A는 아직 실행되지 않았고, 이 허가는 생물학적 성공ㆍbehavior/model 결과 또는 그 해석을 허가하지 않는다.

## 2. 동결 증거

| artifact | SHA-256 | 판정 |
|---|---|---|
| `00-contract.md` | `29b8507351f049fa3d5cf5ff6f4bc1135d12c3b499bc27a06fad081c48d2e158` | COMPLETE; exclusive boundaries, F1-v6와 exact F2 DGP 동결 |
| `10-sources.md` | `683b63fd68908052b9000d9175ed9862d4763d5a70578de194d1b8d70ac0a52b` | COMPLETE; source와 analyst successor 분리 |
| `11-math.md` | `dd9bb4f2c5680a26dd9f74fe748db77c6152a4985767010c46325ed0b78506d9` | COMPLETE; PSDㆍresolvent와 F1-v6/exact-DGP 지위 |
| `12-routes.md` | `11a60afcedf333634f2cb19ec13fc6cd8adeb9bf602620a2124d9fbc2fc59099` | COMPLETE; F1-v6 route와 staged funnel |
| `artifacts/source-lock.json` | `234bac2c67e98a8a0745ef412745b5c360d4d5751d73c14f290c15f1d80ad495` | publication/data/code provenance |
| `artifacts/candidate-manifest.json` | `58280bb9759549b9f285e95135b5320e44f1d317adf347a065319f367a3e6a0c` | exact 48 candidates |
| `artifacts/candidate-manifest-receipt.json` | `cdb1dc8ccdbca5808613ade8f5a3ce946087e720611a40193ca8198c5d53651d` | countㆍuniqueㆍcanonical hash PASS |
| `artifacts/f0-receipt-v3.json` | `86b70828449889c1f3bfaf9422a0e41b01655d83bcd7d1c067b3d8da796b1ab7` | valid F0-v3 apparatus receipt |
| `artifacts/run_f1_v6.py` | `3ab7eb89d49ae3845a72e5808f0cf9423014f520b961fe7551576be22f1c2be7` | self-contained final F1 runner |
| `artifacts/f1-receipt-v6.json` | `8cbdaed43fc861c4696a41a3fd84331fd41727622d848e123b635d8c9ae11cca` | 12 `ABSTAIN`, 32 `PROMOTE`, 4 `DROPPED_BUDGET`; order locked; behavior/model false |
| `artifacts/f2-config-v4.json` / receipt | `9248c9fac975ea70ac034d11e45be70eff7abccb13b65eae7be7010850e2de47` / `a4b1da7b6feb62b65768b993eda682470a20f3e77e41142e656347d8d5d5c7a9` | pre-F2 config only; numerical F2 execution false |
| `artifacts/f2_common_v2.py` / fixture-v3 | `12200f0f6d2d2db61d1000c40a39049123b5f1e2023ef439f9763ad69794f605` / `6346c57cbdc7c8b564b316aca0ba06008ac01c9e66035b7794f8c472612592bf` | generator/source closure; no candidate $Q$, F2 gate, behavior/model result |

manifest canonical compact-content SHA-256은
`37c04ab2b59e4dcba64311f570526ae83a21e4ea59a03c18b479bceb9e05374b`다.

## 3. 수학 gate

비음수 normalized weight와 두 개 이상의 양의 sample에서

$$
G_t=\frac{\sum_jw_{tj}(x_j-\bar x_t)(x_j-\bar x_t)^\mathsf T}
{1-\sum_jw_{tj}^2}\succeq0
$$

다. $n_{\rm eff}\ge8$은 denominator와 weight concentration의 apparatus 하한이지
행동 예측이나 생물학적 정보의 충분조건이 아니다. negative weight,
pairwise-complete denominator와 future-centered filter는 core에서 금지됐다.

resolvent $S=\widetilde G(\widetilde G+I)^{-1}$는 contraction이고
$0\le d_{\rm eff}\le r_\star$, $0\le Q\le1$이다. $V$, $\kappa$와 $M$의 모든 ratio와
exp 인자는 prefix scale로 무차원화됐다. ambient isotropic shrinkage가 rank bound를
깨뜨리는 반례 때문에 primary 48개에서 제외됐다.

## 4. candidate와 gap 지위

kernel specification 8, quality exponent 2, robust map 3의 곱은 정확히 48개다.
순서ㆍtailㆍcalibrationㆍtieㆍstage cap이 manifest에 고정됐다. POWER는 full causal tail,
COMPACT는 $u<L$ support를 쓴다.

gap route는 barrier나 interpolation이 아니다. `SOFT_GAP_DOWNWEIGHTING`은 gap 전 sample을
실제 경과시간만큼 감쇠하고, $\delta$를 3에서 cap해 gap 뒤 한 sample이 미관측 구간 전체
질량을 대표하지 못하게 한다. 이를 생물학적 연속성의 관측으로 해석하지 않는다.

## 5. selection과 inference gate

SMALL/MID/LARGE-A/LARGE-B는 서로 다른 chronological 2/3/2.5/2.5% block이고
ranking-only다. window score를 독립 표본으로 세거나 p-valueㆍ생물학적 주장을 만들지
않는다. recording별 loss를 먼저 집계하며 최소 7 recording cluster, cluster당 8 row,
pooled 100 row, candidate coverage 95%를 모두 요구한다.

LARGE-B를 통과한 champion 하나만 FINAL 20%를 연다. final statistic은 두 held-out
recording의 paired $\Delta R^2$ 중 최솟값이다. moving-block length는 training
autocorrelation에서만 고정한다. recording 두 개이므로 animal-population inference가
아니며 최대 지위는 `BIO_EVIDENCE_L3_DEVELOPMENTAL_HELD_OUT`이다.

## 6. 허가 범위와 fail-closed 조건

다음 항목은 동결한 순서다. F0-v3/F1-v6은 완료됐고 final math/status re-audit는 PASS다. 이 gate가 허가하는 새 실행은 F2-A synthetic apparatus 하나뿐이다.

1. F0-v3 property/runtime과 F1-v6 prefix-only recovery (완료; final re-audit PASS);
2. F2-A synthetic apparatus (허가; 32개 후보, behavior 미사용);
3. F2-B/C/D successive-halving과 독립 confirmation (F2-A receipt 뒤 별도 gate 전까지 미허가);
4. F2R behavior-blind real-background injection (confirmation survivor만; 미허가);
5. neural-stage lock 생성;
6. 70/2/3/2.5/2.5/20 funnel과 단계별 receipt;
7. LARGE-B champion 하나의 FINAL one-shot.

manifestㆍstage-lockㆍfinal-lock hash 불일치, 후보/threshold/kernel/ridge 변경, common-row
하한 실패, PSDㆍcausalityㆍdimensionless 실패, survivor 0 또는 mandatory control 실패는
즉시 중지 조건이다. FINAL 실패 뒤 runner-up을 같은 20%에서 열 수 없다.

synaptic edge, directed loop, hippocampal hash, consciousness와 AGI는 계속
`UNSUPPORTED / BLOCKED`다.

구현 감사에서 발견된 attempt-00 및 이전 F1-v3/v4/v5 문제는 superseded provenance로 보존한다. 이 판본은 valid F0-v3 (`86b70828449889c1f3bfaf9422a0e41b01655d83bcd7d1c067b3d8da796b1ab7`)과 self-contained F1-v6 runner (`3ab7eb89d49ae3845a72e5808f0cf9423014f520b961fe7551576be22f1c2be7`), receipt (`8cbdaed43fc861c4696a41a3fd84331fd41727622d848e123b635d8c9ae11cca`)만 promotion source로 쓴다. F1-v6의 set은 12 `ABSTAIN`, 32 `PROMOTE`, 4 `DROPPED_BUDGET`이고 v6 order로 lock됐다. final math/status re-audit는 PASS이며 frozen validation vector 36개 array의 mismatch는 0이다. F2 config-v4/generator/fixture는 source closure이고 F2-A numerical execution은 아직 없다. 이 gate의 다음 허가는 behavior 없는 F2-A synthetic apparatus뿐이다.

Gate 결론: **PASS — F2-A synthetic apparatus만 허가; F2-A/F2R/behavior의 수치 성공ㆍ생물학적 해석은 아직 없음**.
