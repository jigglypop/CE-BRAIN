# BA-SRM6 형식 지위 감사

Status: COMPLETE

Gate: BLOCKED

Date: 2026-08-23

## 1. 판정

BA-SRM6의 수학적 장치와 검증 설계에는 구현을 영구 금지할 P0 반례가 없다. 그러나
동결 계약이 실제 GCaMP endpoint를 열기 전에 요구한 입력 적격성 검사에서 두 기록의
primary `Ratio2` unit 수가 0이 되었다. 따라서 이 판본 전체에는 `Gate: PASS`를 줄 수
없고, 실제 모델 적합ㆍvalidation 선택ㆍheld-out 점수 산출은 금지한다.

최종 지위는 다음과 같다.

> `COMPLETE / EMPIRICAL_INSTANTIATION_BLOCKED`

이 판정은 가설이 거짓이라는 생물학적 음성 결과가 아니다. 사전등록한 측정ㆍ결측
규칙이 이 corpus의 두 기록에 적용 불가능하다는 **입력 계약 음성 결과**다.

## 2. 감사한 동결 증거

| 증거 | SHA-256 | 판정 |
|---|---|---|
| `00-contract.md` | `0ba568f4e616baa4b02972dad437e9b9003501b649abdec1b8acd510ad236c16` | COMPLETE; endpoint 전 중지 규칙 포함 |
| `10-sources.md` | `41c887c0f78b0007e340a2664fdd876a1195018922f7eddb3fd7b65b841a3dcb` | COMPLETE; Hallinen/OSF와 해석 한계 확인 |
| `11-math.md` | `ec4711dc4e54862c08a7bf4225d5f5094076b85a5b8e8f0b99719c299908f1af` | COMPLETE; resolvent 유효차원과 no-go 검증 |
| `12-routes.md` | `75f8cc7607afbdd9269da643239c499a7af632df6471a75ce2c8d951ca848c40` | COMPLETE; basis-fixedㆍreference-metricㆍdirected route 비교 |
| `artifacts/osf-input-prereg.json` | `96d31082b5125d4095235e47a1698bb1d704e70df530737f00b357f2094d6897` | 입력 식별자ㆍ크기ㆍ해시 사전 고정 |
| `artifacts/input_audit.py` | `a9762cac457dd969c38b138c6d51289381d049bd83e0d65d926e21b52d42ce1c` | endpoint 비개봉 입력 감사기 |
| `artifacts/input-audit.json` | `52e804ff910bcee5dfb431dc193016c014bf6262a0055d7960795da1c74e7caf` | 입력 감사 영수증; `input_passed=false` |

## 3. 입력 감사 결과

세 archive는 동결한 bytes와 SHA-256에 모두 일치했다. 22개 MAT 파일은 필요한
`Ratio2`, `R2`, `hasPointsTime`, `behavior.v`, `behavior.pc1_2`를 포함했고, recording
split membership와 미래 horizon 가용성도 통과했다.

실패한 것은 계약 §5의 primary `Ratio2` unit rule이었다. 각 기록의 chronological
첫 60%에서 neuron별 finite fraction이 0.75 이상이어야 했으나 다음 두 기록에는
통과 unit이 하나도 없었다.

| 역할 | recording | median finite fraction | maximum | passing units |
|---|---|---:|---:|---:|
| outer train | `BrainScanner20200130_105254` | 0.634973 | 0.654645 | 0 / 128 |
| outer validation | `BrainScanner20200310_141211` | 0.618172 | 0.630992 | 0 / 116 |

같은 기록의 red channel `R2`는 각각 128개와 116개 unit이 기준을 통과하지만, 계약에서
`R2`는 nuisance control이다. 이를 GCaMP primary `Ratio2` 대신 쓰는 것은 endpoint
교체이므로 허용하지 않는다.

영수증의 상태 비트는 다음과 같다.

- `archive_passed=true`
- `schema_passed=true`
- `split_membership_passed=true`
- `horizon_availability_passed=true`
- `unit_viability_passed=false`
- `input_passed=false`
- `endpoint_opened=false`
- `model_fit=false`
- `scores_computed=false`

## 4. 수학적 지위

다음은 이 판본에서 닫힌 조건부 정리다. 유한 관측공간에서 $G\succeq0$와
$\lambda>0$이면

$$
S_\lambda=G(G+\lambda I)^{-1},\qquad
d_{\mathrm{eff}}(\lambda)=\operatorname{tr}S_\lambda
=\sum_k\frac{\mu_k}{\mu_k+\lambda}
$$

이고 $0\le d_{\mathrm{eff}}\le\operatorname{rank}G$이며 $\lambda$에 대해 연속ㆍ단조
감소한다. 무한 Hilbert 공간에서 trace를 유한하게 하려면 $G$가 positive
self-adjoint trace class여야 한다. compact만으로는 충분하지 않다.

이 $d_{\mathrm{eff}}$는 정수가 아닌 값을 가질 수 있지만 위상적ㆍ리만 다양체의
비정수 차원이 아니다. 관측 calcium covariance의 scale-dependent effective degrees
of freedom이다. 또한 $A=\epsilon I+(1-\epsilon)S$는 관측 quotient 위의 분석자
정규화 inner product이지 뇌의 내재 metric으로 검증된 것이 아니다. covariance는
시간 순서와 directed edge를 버리므로 시냅스 방향ㆍ해마 indexㆍ의식 moment를
식별하지 못한다.

## 5. 허가 범위와 중지 범위

L0-A analytic/property test, L0-B synthetic recovery, L0-C real-background
semi-synthetic apparatus test는 원리상 실제 endpoint 없이 구현할 수 있다. 그러나
CE research workflow는 전체 Gate PASS 뒤에만 제품 코드를 수정하도록 요구한다.
따라서 BA-SRM6에서는 입력 감사기와 영수증만 남기고 core 구현도 successor로 넘긴다.

금지한 작업은 다음과 같다.

- real GCaMP feature/model fit;
- validation recording을 이용한 ridge 또는 fixed-$d$ 선택;
- held-out recording score와 $\Delta R^2$ 산출;
- 기준 0.75를 같은 판본에서 낮추거나 eligibility 정의를 바꾸는 일;
- `R2` 또는 GFP를 primary endpoint로 대체하는 일;
- 입력 중지를 가설 지지ㆍ기각으로 해석하는 일.

## 6. 대안 검토와 재개 조건

단순히 0.75를 사후에 낮추는 길, red channel로 primary를 바꾸는 길, 실패 기록을
삭제하는 길은 모두 outcome-informed 변경이라 기각했다. 허용 가능한 재개 경로는
새 successor 계약뿐이다.

후속 판본은 먼저 원저자 공개 코드의 exact revision과 Ratio2 결측 처리법을
source-lock해야 한다. 그 근거로 measurement rule을 **endpoint를 열기 전에** 하나로
고정하고, BA-SRM6의 0.75 rule을 matched sensitivity로 그대로 보존해야 한다. 새 입력
게이트와 L0-A→L0-B→L0-C를 모두 통과한 뒤에만 real fit을 시작한다.

Gate 결론: **BLOCKED — successor contract required**.
