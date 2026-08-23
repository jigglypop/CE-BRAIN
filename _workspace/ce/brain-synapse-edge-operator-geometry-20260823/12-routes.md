# BA-SRM4 대안 경로 비교

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-synapse-edge-operator-geometry-20260823`

## 범위와 판정 기준

이 문서는 같은 typed input, 같은 `slice.lims_specimen_name` LIMS slice-specimen
동치류-held-out split, 같은 future-response target,
같은 covariance score를 쓰는 세 후보군을 비교한다. 어떤 후보도 validation 또는
confirmation outcome을 읽지 않았다. 아래 ``우세''는 아직 [미완성]이며, 유일한
허용 판정은 계약의 frozen validation selection과 paired confirmation
$\Delta\mathrm{ELPD}$다.

## Route A — sparse causal Volterra

$$
M_o(h,c)=\beta_{o0}+\sum_a\beta_{oa}\Phi_a(h,c)
+\sum_{a\le b}\beta_{oab}\Phi_a(h,c)\Phi_b(h,c).
$$

**강점.** history basis와 interaction group을 명시하므로 어느 typed edge-history
direction이 conditional span을 실제로 늘렸는지 추적할 수 있다. active group을
20 이하로 제한하고 hierarchy를 강제하면 해석 가능한 낮은 자유도 후보가 된다.

**취약점/가장 강한 falsifier.** discovery nested-CV에서 선택된 sparse 후보가
validation에서 raw-RBF 또는 FPCA/RKHS reference보다 $\Delta\mathrm{ELPD}>2SE$를
보이지 못하면, ``낮은 차수 causal interaction이 충분하다''는 route는 기각된다.
time shuffle에서도 같은 이득이면 causal history 해석은 기각된다. 자유도는
선택된 group, basis width, interaction 수를 포함해 세며 validation 후 변경은
새 run이다.

## Route B — FPCA/RKHS 또는 RBF 비모수 reference

history를 discovery-only FPCA score 또는 fixed typed RBF feature로 바꾸어
regularized map을 적합한다. 이는 biology claim이 아니라 smooth/high-capacity
prediction reference다.

**강점.** sparse Volterra가 놓친 높은 차수 또는 비국소 history dependence의
상한선 역할을 한다. 높은 prediction score가 있더라도 그 자체가 관측 가능한
생물학적 state variable을 찾아냈다는 결론은 아니다.

**취약점/가장 강한 falsifier.** 같은 group-held-out score에서 이 reference가
constant/linear보다 개선하지 못하면 flexible history route 전체가 지지되지 않는다.
반대로 raw-RBF가 Volterra보다 우세하면 Volterra의 해석 주장은 기각되지만,
RBF가 ``무한차원 synapse''를 증명하는 것은 아니다. time shuffle, clamp-mode swap,
missingness-mask-only가 같은 성능이면 feature capacity/leakage route로 판정한다.
자유도는 kernel bandwidth, FPCA component 수, penalty를 discovery nested-CV 안에서
선택한 경우에만 세며, effective degrees of freedom은 독립 discovery LIMS slice-specimen
동치류 group의 절반
미만이어야 한다.

## Route C — source-verified mechanistic short-term-plasticity baseline

완료된 `10-sources.md`가 field 단위와 실제 event semantics, source-baseline template를
고정했으므로, release,
depletion/recovery, facilitation과 typed recording map을 명시한 낮은-parameter
mechanistic baseline을 사용한다. 이 route의 parameter는 상태의 편리한 summary이지
직접 관측한 vesicle/release state가 아니다.

**강점.** source-anchored dynamics와 causal direction을 선행 선언하게 하므로,
순수 predictor보다 생물학적으로 강한 반증 가능성을 제공한다.

**취약점/가장 강한 falsifier.** source-verified baseline이 정확한 schema/unit을
만족한 상태에서 동일 held-out score로 simpler constant/linear에 이기지 못하거나,
sparse/FPCA reference에 계속 열세라면 그 *특정* mechanistic parameterization은
기각한다. 이는 short-term plasticity 일반 또는 history-space 정의의 기각이 아니다.
이 route는 source-locked template 상태이나 아직 empirical fitting을 하지 않았으며,
source field/단위 receipt가 무효화되면 `STOP_SOURCE`이고 fitting을 시작하지 않는다.

## 공통 adverse controls와 선택 규칙

세 route 모두 다음 control에 동시에 견뎌야 한다.

- constant와 linear: history/edge attribute가 없는 하한선
- raw-RBF: 유연성만으로 생기는 이득의 상한선
- history ablation과 static-attribute ablation: 어느 정보군이 필요한지 확인
- time-order shuffle: 미래/순서 누출 및 causal-history 해석 반증
- IC/VC typed-channel swap: clamp 단위 혼합의 재발 반증
- missingness-mask-only: mode/missingness가 outcome proxy인 경우 반증
- `slice.lims_specimen_name` group bootstrap: row 수가 아닌 DB에서 식별 가능한
  비고유 LIMS slice-specimen 동치류 단위의 불확실성

관측 공간 route의 가장 강한 공통 falsifier는 다음이다: typed unit, group split,
target, covariance를 고정한 뒤 history-aware 후보가 모든 단순 control과 raw-RBF를
상대로 validation에서 우세하지 못하거나, time shuffle/clamp swap 뒤에도 우세가
남는 경우다. 이때 ``간선 history가 예측 가능한 독립 차원을 제공한다''는
empirical claim을 올리지 않는다.

## 수학적 대안 및 한계

Route A/B/C의 어떠한 승리도 finite-output no-go를 피하지 못한다. 승리는 오직
관측 quotient에서의 predictive comparison이며, full $\mathscr H_E$ recovery 또는
infinite-dimensional SPD metric을 뜻하지 않는다. 무한 basis를 쓰는 B route에서는
regularized reference operator가 trace-class인지 확인하지 못하면
`UNDEFINED_EFFECTIVE_DIMENSION`이고 $d_{\rm eff}$ 비교를 중단한다.

이 세 route는 서로 다른 구조 가정(희소 저차 상호작용 / smooth flexible map /
source-anchored state dynamics)을 갖기 때문에 동일한 threshold, seed, decoder만
바꾼 재시도가 아니다. 다만 outcome을 본 뒤 후보군이나 kernel bank를 늘리면
look-elsewhere 자유도가 달라지므로 새 contract와 split salt가 필요하다.

## 상태

대안 경로의 수학적 비교는 완료했다. Route C는 `10-sources.md`가 COMPLETE여서
source-locked baseline template가 고정됐지만, 아직 empirical fitting/validation은 하지 않은
[미완성] 상태다. split과 bootstrap의 최고 단위는 비고유
`slice.lims_specimen_name` LIMS slice-specimen 동치류이고, `slice.ext_id`는 고유 row identity일
뿐이다. donor/animal identity는 UNRESOLVED이므로 donor-held-out을 주장하거나 그보다 약한
LIMS 동치류 분할을 donor-held-out으로 대체하는 것은 금지한다. 어떤 route도 confirmation에
접근하지 않았으며, 현재 수학 레인은 biological or AGI claim을 허가하지 않는다.
