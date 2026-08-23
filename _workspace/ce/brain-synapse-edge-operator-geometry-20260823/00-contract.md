# BA-SRM4 연구 계약 — 시냅스 간선 연산자 기하와 데이터 기반 식 발견

Date: 2026-08-23

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-synapse-functional-quotient-qc2-20260823`

## 1. 연구 질문과 주장 상한

이 판본은 시냅스를 단일 스칼라 가중치가 아니라 과거 자극·스파이크·막전압·세포 상태에
반응하는 인과 연산자로 본다. 질문은 두 가지다.

1. 각 간선의 정적 속성과 과거 의존 kernel 중 무엇이 미래 시냅스 반응에 독립적인 정보를
   제공하는가?
2. 그 정보가 유한 관측 아래 만드는 quotient의 hard rank와 noise-aware effective dimension은
   얼마인가?

사용자 아이디어는 후보식의 구조 prior로 받을 수 있다. 그러나 discovery 데이터로 만든 식은
항상 `[경험식]`이며, 이 계약에서 봉인한 독립 confirmation을 통과하기 전에는 `[예측]`이나
생물학적 법칙으로 승격하지 않는다.

`CLAIM_CEILING`: 최대 L3 후보. 대상은 Allen Synaptic Physiology의 ex vivo mouse V1
multipatch event population이다. whole-brain, in-vivo cognition, 기억의 충분조건, AGI 구현,
또는 관측되지 않은 무한차원 상태공간의 완전 복원은 주장하지 않는다.

## 2. PREDECESSOR_EVIDENCE

| 판본 | 상태 | 고정 증거 | 이번 판본이 상속하는 규칙 |
|---|---|---|---|
| A6 property loop | 완료 | final SHA-256 `5940bf3fb54f442cdbdc202afa44924367ff802d40c129004abc0240a7e088a4` | $J^TGJ$는 full-rank에서만 SPD이며 rank loss에서는 PSD다. |
| BA-SRM2 functional quotient | 완료 | final SHA-256 `e5d9fbc3373d584175b0edee583bbb4f89753019f01727e5bfa02eec37387fe9` | history-dependent synapse는 무한차원일 수 있으나 유한 관측은 quotient만 식별한다. |
| BA-SRM3 source-corrected QC2 | `INVALIDATED_CLAMP_UNIT_CONTRACT`로 종료 | final SHA-256 `b88ca4fc9569726f0168b94202cec387a9c769c26d216784c49d098a641351eb`; gate `PASS` | IC의 presynaptic command는 A, VC는 V인데 하나의 current/pA 좌표로 혼합했다. 이전 operator/rank/model 수치는 해석하지 않는다. development와 confirmation은 열리지 않았다. |
| BA-SRM1 pulse-slot route | 반례로 폐기 | BA-SRM2가 기록 | 비어 있는 `stim_pulse.qc_pass`를 12개 유효 pulse의 증거로 쓰지 않는다. |

이 표는 이전 실패를 성공으로 고쳐 쓰지 않는다. BA-SRM4는 clamp mode를 typed channel로
분리하고, 새로운 데이터 split과 새로운 판본에서만 다시 시작한다.

## 3. 세 층의 분리

### BIO_STARTING_MECHANISM

검증할 출발점은 repeated presynaptic activation에 따른 short-term synaptic dynamics다.
release probability, vesicle depletion/recovery, facilitation, postsynaptic response와 recording
state가 후보 메커니즘이지만, 어느 항을 mechanistic baseline에 넣을지는 `10-sources.md`에서
1차 출처와 실제 source field를 함께 확인한 뒤 고정한다. 확인 전에는 `[미완성]`이다.

### CE_DELTA

간선 $e$의 상태를 유한 정적 좌표와 fading-memory history의 직합으로 둔다.

$$
\mathcal H_e
=\mathbb R^{p_e}\oplus
L^2_\rho\!\left(({-\infty},0];\mathbb R^{q_e}\right),
\qquad
\mathscr H_E=\bigoplus_{e\in E}\mathcal H_e.
$$

$\rho$는 과거가 무한한 norm을 만들지 않도록 하는 양의 fading weight다. 이것은 실제 뇌가
특정 Hilbert 공간 그 자체라는 공리가 아니라, history-dependent edge operator를 비교하기 위한
후보 표현이다. 유한 기록에서는 $\mathscr H_E$ 전체가 아니라 측정 연산자의 kernel을 나눈
quotient만 식별 가능하다.

### MEASUREMENT_MODEL

$$
Y=M(x)+\varepsilon,
\qquad
\mathbb E[\varepsilon\mid x]=0,
\qquad
\operatorname{Cov}(\varepsilon\mid x)=R(x).
$$

current clamp(IC)와 voltage clamp(VC)는 같은 숫자 채널로 합치지 않는다. presynaptic IC command는
$I/I_0$, VC command는 $V/V_0$이고 별도의 type indicator와 별도의 scaler를 갖는다.
postsynaptic response도 recording mode와 source unit을 보존한다. 서로 다른 물리량 사이의 결측은
0 대입이 아니라 structural missingness로 취급한다.

고정 기준은
$T_0=1\,\mathrm{ms}$, $V_0=1\,\mathrm{mV}$,
$I_0=1\,\mathrm{pA}$, $R_0=1\,\mathrm{M\Omega}$,
$C_0=1\,\mathrm{pF}$, $L_0=100\,\mu\mathrm m$,
$\Theta_0=310\,\mathrm K$다. exp, log, kernel, 거리, 고정점에 들어가는 모든 인자는 이 기준이나
discovery-fold 내부 scale로 먼저 무차원화한다.

## 4. DATA_PROVENANCE와 오염 경계

원자료는 다음 pinned DB만 사용한다.

- path: `C:\Users\dongh\OneDrive\Desktop\Clarus-Equation\data\external\allen-synphys\raw\synphys_r2.1_medium.sqlite`
- bytes: `11125997568`
- SHA-256: `dbf19786f9e0d0d73c26351dc29d69ef8c10a2e67e32e19ac73034a5624d48c5`
- 이전 source manifest SHA-256: `4ddb4a52294a55b011c5118a02432ca28c057ca5b5ebb63d8d7c945923aa62c2`
- 이전 eligible manifest SHA-256: `74d6d3b142e48d7906305e133983b91cc8227a40748335985414e674dd1fd81c`
- clamp audit receipt SHA-256: `b18d23a4c1d3ef31ba5522724a17d98cedfd71eeef546b14951e608cfd5540b8`

clamp audit에서 eligible sequence 1,383개와 16,596 event row가 확인되었다. postsynaptic
recording은 전부 IC였고 presynaptic recording은 excitatory 713 IC/16 VC, inhibitory
641 IC/13 VC였다. 이 수치는 support 진단일 뿐 모델 성능이나 차원 증거가 아니다.

`SEEN`: DB hash/schema, group key, clamp mode/unit, 행 수와 결측 구조, discovery bucket,
그리고 과거 판본의 train 접촉 group.

`UNSEEN`: validation과 confirmation group의 response value, residual, score, rank spectrum,
선택 결과. 계약·후보 grammar·threshold를 동결하기 전에 이 값을 집계하지 않는다.

## 5. DATA_SPLIT

가능한 가장 높은 안정적 독립 단위인 donor/specimen group identity를 source schema에서 먼저
확정한다. 동일 biological source에 속할 가능성이 있는 slice, pair, recording, sequence는
반드시 같은 split에 둔다. donor가 식별 불가능하면 specimen 단위를 쓰고, 그 한계를 claim
ceiling에 기록한다.

`GROUP_KEY_RESOLUTION` (source/schema-only, validation/confirmation 접촉 전): pinned DB의
`slice.lims_specimen_name`은 donor가 아니라 LIMS의 "slice specimen" 이름이다. 4,276개
`slice` row가 4,259개 이름으로 묶이고, 16개 중복 이름이 33개 row를 덮는다. 그러므로
$g=\texttt{slice.lims\_specimen\_name}$을 보수적인 slice-specimen equivalence class로 쓰고,
`slice.ext_id`는 row identity와 predecessor 매핑에만 쓴다. donor/animal identity는
`UNRESOLVED_IDENTITY_KEY`이며 donor-held-out 주장은 금지한다.

group key $g$를 확정한 뒤 다음 고정 규칙을 적용한다.

```text
bucket = uint64_be(SHA256('BA-SRM4-GROUP-SPLIT-V1:' + g)[0:8]) mod 10
discovery/train       = 0..5
validation/development = 6..7
test/confirmation      = 8..9
```

과거 BA-SRM2/3 train에서 한 번이라도 response outcome이 계산된 group은 hash bucket과 무관하게
`discovery-contaminated`로 강제한다. 한 donor도 split을 가로지를 수 없다. untouched validation과
confirmation의 group 수 및 E/I/clamp support가 사전 최소치를 만족하지 못하면
`BLOCKED_SPLIT_SUPPORT`로 종료하고 더 작은 단위로 누수를 정당화하지 않는다.

- discovery: 후보식 생성, preprocessing, term screening, hyperparameter 탐색 전용.
- validation: 후보 구조 하나, active term, covariance family, $d_{\rm eff}$ regularization scale을
  선택하는 데 한 번 사용한다.
- confirmation: 최종 동결 뒤 한 번만 연다.

validation outcome을 본 뒤 새 아이디어나 새 항을 추가하면 현재 confirmation을 열지 않고 새
run-id와 새 split salt로 분리한다.

## 6. 데이터 기반 후보식 grammar

주 후보는 order 2 이하 sparse causal Volterra 식이다.

$$
M_o(h,c)=\beta_{o0}
+\sum_a\beta_{oa}\Phi_a(h,c)
+\sum_{a\le b}\beta_{oab}\Phi_a(h,c)\Phi_b(h,c).
$$

$\Phi_a$는 discovery에서만 고정한 무차원 causal basis다. 미래 pulse와 target-derived feature는
입력에 넣지 않는다. active group은 최대 20개이고, hierarchy 원칙에 따라 interaction이 남으면
그 parent main effect도 남긴다. 비교 기준은 다음 셋이다.

1. discovery-only FPCA/RKHS 또는 RBF nonparametric reference;
2. `10-sources.md`에서 실제 field와 단위가 검증된 mechanistic short-term-plasticity baseline;
3. constant, linear, raw-RBF adverse controls.

사용자 아이디어는 다음 다섯 항목으로 번역될 때만 후보 grammar에 들어간다.

1. 상태변수 또는 history functional;
2. source unit과 무차원화 기준;
3. 원인에서 결과로 향하는 시간 순서;
4. 보존량·대칭·단조성 같은 구조 prior;
5. 아이디어와 독립적인 falsifier.

필요 변수가 DB에 없거나 finite observation 아래 서로 구별되지 않으면 식을 억지로 맞추지 않고
`UNIDENTIFIABLE_IDEA`로 원장화한다.

## 7. 연산자 기하와 세 종류의 차원

노이즈 whitening 뒤 pullback information operator를

$$
\mathcal G_x=DM_x^*R(x)^{-1}DM_x
$$

로 둔다. edge $e$의 좌표 또는 basis 방향 $\xi_{e\alpha}$와 edge $f$의 방향
$\xi_{f\beta}$ 사이 정보 block은

$$
G_{e\alpha,f\beta}
=\left\langle
R^{-1/2}\partial_{\xi_{e\alpha}}M,
R^{-1/2}\partial_{\xi_{f\beta}}M
\right\rangle
$$

이다. 한 edge attribute가 관측 차원을 하나 늘리는 필요충분 조건은 그 whitened sensitivity가
나머지 sensitivity들의 closed span 밖에 있는 것이다. 단순 edge 수나 feature 수는 이 조건을
대신하지 못한다.

반드시 다음 세 양을 분리해 보고한다.

1. raw representation dimension: 기록한 edge attribute/history coefficient의 개수;
2. hard observable rank: $\operatorname{rank}(R^{-1/2}DM_x)$;
3. noise-aware effective dimension.

reference covariance 또는 prior로 whitening한 양의 trace-class operator
$\widetilde G$의 eigenvalue를 $\mu_k$라 하면

$$
d_{\rm eff}(\lambda)
=\operatorname{Tr}\!\left[\widetilde G(\widetilde G+\lambda I)^{-1}\right]
=\sum_k\frac{\mu_k}{\mu_k+\lambda}.
$$

$\lambda$ 하나를 사후 선택하지 않고
`{1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100}` 전체 곡선을 보고한다. trace-class 조건이나
reference whitening이 성립하지 않으면 $d_{\rm eff}$를 계산하지 않고 `UNDEFINED_EFFECTIVE_DIMENSION`
으로 종료한다.

## 8. OBSERVABLES

동일한 group weighting으로 다음을 고정한다.

- group-level log predictive density;
- 16개 future-response coordinate의 standardized error와 calibration;
- whitened Jacobian singular spectrum과 hard rank;
- 위 grid의 $d_{\rm eff}(\lambda)$ 곡선;
- edge/channel group을 조건부로 추가했을 때의 sensitivity span 및 rank increment;
- LIMS slice-specimen group bootstrap interval;
- clamp-mode swap, time-order shuffle, missingness, scale/rechart adverse controls.

정확한 16-coordinate target과 complete-case/partial-likelihood 선택은 source lane에서 event schema와
단위를 확인한 후 `10-sources.md`에 고정한다. confirmation을 보기 전에 고정하지 못하면
`BLOCKED_TARGET_DEFINITION`이다.

## 9. RESIDUAL_RULE과 증거 사슬

모든 후보는 같은 target, 같은 group weighting, 같은 frozen residual covariance/denominator로
비교한다. discovery score는 식을 생성하는 도구일 뿐 증거가 아니다. validation은 식 하나를
선택하고 버린 후보를 되살리지 않는다. confirmation의 1차 통계는 group-paired
$\Delta\mathrm{ELPD}$와 그 group bootstrap/standard error다.

증거 사슬은 항상

```text
D(data) -> I(inference) -> P(prediction) -> C(control) -> B(boundary) -> T(status)
```

순서로 기록한다. 중간 어느 연결이 끊기면 더 높은 지위를 주장하지 않는다.

## 10. MODEL_SELECTION과 confirmation unlock

discovery에서는 group-nested cross-validation만 쓴다. validation은 다음을 한 번에 고정한다.

- 최종 후보식 하나와 active term;
- residual covariance family;
- effective-dimension regularization scale 또는 전체 곡선 해석 규칙;
- abstention/support 경계.

동점은 더 낮은 order, 더 적은 active group, 더 낮은 effective dimension 순으로 고른다.
estimated degrees of freedom은 discovery group 수의 절반 미만이어야 하고 active term 수는 독립
discovery group 수보다 작아야 한다.

confirmation은 다음 여섯 조건을 모두 만족할 때만 연다.

1. unit/schema/split receipt가 PASS;
2. validation에서 constant, linear, source-verified mechanistic baseline, raw-RBF 각각보다
   $\Delta\mathrm{ELPD}>2SE$;
3. time shuffle와 clamp-mode swap에서 그 이점이 소멸;
4. group bootstrap에서 rank와 $d_{\rm eff}$ 해석이 안정적;
5. coordinate permutation, 허용된 scale change, affine rechart control 통과;
6. validation 접촉 이후 식·항·threshold·target·split 변경이 없음.

하나라도 실패하면 confirmation은 봉인된 채 `STOP_BEFORE_CONFIRMATION`이다.

## 11. FALSIFIER와 MATCHED_CONTROLS

핵심 falsifier는 다음과 같다.

- history/order를 보존하지 않는 time shuffle이 같은 성능과 차원을 유지한다;
- IC/VC command type을 맞바꿔도 결과가 유지된다;
- edge attribute를 제거해도 conditional sensitivity span과 held-out score가 변하지 않는다;
- coordinate rescale 또는 equivalent rechart만으로 rank/$d_{\rm eff}$ 결론이 바뀐다;
- raw nonparametric control은 이기지만 더 단순한 선형/기계 baseline을 이기지 못한다;
- LIMS slice-specimen bootstrap에서 부호나 차원 순서가 반복적으로 뒤집힌다.

matched controls는 같은 row, 같은 split, 같은 target, 같은 covariance score를 사용한다. 상수,
선형, source-verified mechanistic, raw-RBF, history ablation, static-attribute ablation,
time shuffle, clamp swap, missingness-mask-only를 포함한다.

## 12. REVISION_TRIGGER와 아이디어 수용 절차

다음 사건은 수정이 아니라 새 판본 trigger다.

- validation outcome을 본 뒤 새 항이나 새 사용자 아이디어를 추가함;
- donor보다 낮은 단위로 split해야 함;
- target/QC/unit/clamp schema가 바뀜;
- effective-dimension reference나 $\lambda$ 해석을 바꿈;
- source-verified mechanism이 현재 grammar 밖의 필수 상태를 요구함.

아이디어를 받으면 먼저 `plausible / unidentifiable / contradicted / already-contained` 중 하나로
판정하고, plausible일 때만 위 다섯 항목과 falsifier를 갖춘 후보식으로 쓴다. 데이터 적합도가
높다는 이유만으로 기전적 해석을 부여하지 않는다.

## 13. CLAIM_CEILING의 구체적 문장

성공 시 허용되는 최대 문장은 다음과 같다.

> 고정된 ex vivo mouse-V1 multipatch population과 고정된 측정 모형에서, 특정 typed
> edge-history 방향들이 미래 시냅스 반응의 유한 관측 quotient에 독립적인 정보를 더했으며,
> 그 quotient의 hard rank와 noise-aware effective-dimension 곡선이 독립 confirmation에서
> 지정된 controls보다 안정적이었다.

무한차원 가능성은 상태 표현의 구조적 결과이지, 유한 데이터로 무한 rank를 관측했다는 뜻이
아니다. 확인 결과가 양성이어도 실제 전체 신경계의 차원, 의식, 일반지능 또는 AGI 충분조건으로
외삽하지 않는다.

## 14. STOP 규칙

- `STOP_SOURCE`: source field의 생물학적 의미나 단위를 1차 출처와 schema에서 고정할 수 없음.
- `BLOCKED_SPLIT_SUPPORT`: 오염되지 않은 LIMS slice-specimen validation·confirmation support 부족.
- `BLOCKED_TARGET_DEFINITION`: 미래 response target과 QC rule을 outcome 접촉 전에 고정 못함.
- `STOP_DIMENSIONLESS`: 서로 다른 clamp unit이 합쳐지거나 kernel/log 인자가 차원 있음.
- `UNDEFINED_EFFECTIVE_DIMENSION`: trace-class/reference 조건 불충족.
- `STOP_BEFORE_CONFIRMATION`: validation unlock 조건 중 하나라도 실패.
- `INVALIDATED`: leakage, unit mixing, future-variable input, manifest/hash 불일치가 발견됨.

STOP은 음성 산출이며 결과를 성공으로 재서술하지 않는다. confirmation이 닫힌 경우 그 상태와
재개 조건을 최종 보고서에 명시한다.
