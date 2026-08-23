# BA-SRM7 형식 지위 감사

Status: COMPLETE

Gate: BLOCKED

Date: 2026-08-23

## 1. 판정

BA-SRM7의 무한 과거 상태공간, bounded Volterra edge의 충분조건, 관측 PSD operator와
resolvent 유효차원에는 구현을 영구 금지할 P0 수학 반례가 없다. 공개 원코드와 raw
red/green channel에서 출발하는 인과 측정 개정도 22개 recording 모두에서 primary와
red unit을 남겼다.

그러나 behavior를 읽기 전에 동결한 split별 최소 100개의 feature-common anchor
조건을 네 recording이 만족하지 못했다. 따라서 실제 행동 endpoint, model fit,
validation 선택과 held-out score를 열 수 없다.

최종 지위는 다음과 같다.

> `COMPLETE / SOURCE_ROOTED_INPUT_STOP`

이것은 생물학적 음성 결과나 식의 예측 실패가 아니다. source-rooted causal 입력은
구성됐지만, 이 판본의 hard-gapㆍwindowㆍsplit 계약과 네 기록의 clock/missingness가
공통 표본 수 게이트에서 양립하지 않았다는 입력 적격성 음성 결과다.

## 2. 동결 증거

| 증거 | SHA-256 | 판정 |
|---|---|---|
| `00-contract.md` | `61e6436db9fc7b92225484b612c9cf09129c2e786789cca4afca32d3e463b3c3` | COMPLETE; staged lock와 fail-closed 규칙 |
| `10-sources.md` | `038b35dfbdfd83a3cf579bf8e029beb83b77ae93dd998bc9597f9a853d9719c6` | COMPLETE; 공개 코드 revision과 원자료 출처 고정 |
| `11-math.md` | `c16d7923898af3f636935a4843ba8485b32da2e3f4ab4c013c8a08ae07ab7f64` | COMPLETE; HilbertㆍVolterraㆍPSDㆍresolvent 감사 |
| `12-routes.md` | `eaae2c5c49135771171637f9afae7171b773f1ab80d17a9d40553cb9a049b7dd` | COMPLETE; 세 측정 경로와 대조군 비교 |
| `artifacts/source-lock.json` | `d1f8063ffa823bff78d316b070327eb4358ce74a7247a19aa6f32f76b099e280` | archiveㆍ코드 provenance lock |
| `artifacts/math-spotcheck.json` | `4290b0b9cbef67f18e79e3005f246015fa11a37b556088386fa49c8c058a7d1f` | 수치 spot check PASS |
| `artifacts/input_audit.py` | `a5bd9961c867d8f4707a41649cc865558f7570626abf7feb6186911b41f40b27` | behavior 선행 접근을 차단한 입력 감사기 |
| `artifacts/neural-input-lock.json` | `f5bb9d56fe339f7e2451299e493d6e6982ac8db8bcc646f785aa29c9b6568769` | behavior-independent neural lock; FAIL |
| `artifacts/input-audit.json` | `bbb2382ef510a8323ba9b14b1aaa7f653d675fecbe6f34f48d61f3385586c51f` | 최종 staged receipt; `input_passed=false` |

입력 감사 apparatus의 변경 이력도 삭제하지 않았다. attempt-00은 failed neural lock 뒤
behavior field의 이름과 shape를 읽었지만 값 요약ㆍ적합ㆍ점수 계산은 하지 않았다.
attempt-01부터 failed lock 뒤 behavior load 자체를 건너뛰었고, 최종본은 clock,
prefix, $r_\star$와 anchor ID hash까지 계약 필드를 완결했다.

| 보존 판본 | input SHA-256 | neural-lock SHA-256 | 지위 |
|---|---|---|---|
| attempt-00 | `33b53190ab695ffca7d0733a3378cb144dc56017df94c1ae46d8504eab383f35` | `4ea47d78cee5941cbd7eb7f409292e63f59cdb6d493d6aa8f93b60f887b815bf` | shape metadata 선행 접근; score 없음 |
| attempt-01 | `605a4d3cab45c14d6fe934ed80ded904737879174ab261eb85a89f347b12162f` | `561f81240b7b40ec4807bb5fd580686f60ec963675d0f927ced7656bd8babc08` | behavior load 차단; 명시 필드 보강 전 |

## 3. 입력 감사 결과

세 archive의 bytes/hash, 공개 코드 hash, 22개 MAT raw schema, retained clock의 strict
monotonicity와 positive step, raw/processed calibration prefix는 모두 통과했다. 모든
recording에서 primary와 red causal unit이 남았고 $r_\star=59$였다. split별 원본 raw
volume anchor ID 목록은 behavior와 독립적으로 hash됐다.

실패는 네 recording의 feature-common anchor 하한뿐이다.

| outer 역할 | recording | train | validation | test | 실패 split |
|---|---|---:|---:|---:|---|
| train | `BrainScanner20200130_105254` | 214 | 42 | 33 | validation, test |
| train | `BrainScanner20200309_151024` | 372 | 107 | 48 | test |
| validation | `BrainScanner20200310_141211` | 23 | 8 | 0 | train, validation, test |
| held-out | `BrainScanner20200310_142022` | 555 | 53 | 159 | validation |

영수증의 핵심 상태는 다음과 같다.

- `eligibility_passed=true`;
- `feature_common_anchors_passed=false`;
- `input_passed=false`;
- `neural_lock_created_before_behavior=true`;
- `behavior_schema_after_lock=SKIPPED_NEURAL_LOCK_FAIL`;
- `behavior_values_scored=false`, `model_fit=false`;
- `validation_opened=false`, `test_opened=false`, `endpoint_opened=false`.

## 4. 수학ㆍ주장 지위

가중 history Hilbert space와 edge kernel 조건은 `[조건부 정리]`다. 각 edge가 명시한
weighted Hilbert--Schmidt 충분조건을 만족할 때 Volterra operator와 유한 loop product가
bounded다. 조건 없는 모든 history-response edge의 boundedness는 주장하지 않는다.

유한 관측공간의 reliability-weighted covariance $G\succeq0$에 대해

$$
S_\lambda=\widetilde G(\widetilde G+\lambda I)^{-1},\qquad
d_{\mathrm{eff}}(\lambda)=\operatorname{tr}S_\lambda
$$

는 `[정리ㆍ정의]`다. $d_{\mathrm{eff}}$는 연속값일 수 있지만 비정수 리만 다양체
차원이 아니라 관측 quotient의 scale-dependent effective degrees of freedom이다.
causal fluorescence quotient와 reliability weighting은 원코드와 raw channel에 근거한
`[공리: 분석자 측정 개정]`이지 published preprocessing의 동일 재현이 아니다.

future locomotion에 대한 incremental prediction은 `[예측: UNVERIFIED]`다. synaptic
edge, directed loop, hippocampal hash, consciousness와 AGI 해석은 현재 관측으로
식별되지 않으므로 `[미완성/차단]`이다.

## 5. 허가ㆍ금지와 후속 조건

Gate가 BLOCKED이므로 제품 core, L0-B/L0-C runner, behavior model과 score를 구현하거나
실행하지 않는다. 같은 판본에서 anchor 하한, split, hard-gap 또는 common-row 정책을
완화하는 것도 금지한다.

후속 판본은 새 계약에서 physical-time causal weights와 mask-aware PSD covariance를
정의하고, 실제 behavior를 열기 전에 합성 irregular-clockㆍblock-dropout과
behavior-blind real-background injection으로 장치를 검증해야 한다. 그 새 입력식이
사전 동결한 gate를 통과할 때에만 단계적 행동 검증으로 진행한다.

Gate 결론: **BLOCKED — successor contract required**.
