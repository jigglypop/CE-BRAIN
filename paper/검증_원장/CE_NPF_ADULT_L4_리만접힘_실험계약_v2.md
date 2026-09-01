<!-- 도메인: ce-brain-bio -->

# CE-NPF 성체 L4 리만접힘 실험계약 v2

Status: `SCHEMA_FREEZE_CANDIDATE / EXECUTION_NOT_AUTHORIZED / BIO_EVIDENCE_L0`

계약 개정일: 2026-09-02

Machine contract:
[`adult_l4_riemann_fold_contract_v2.json`](../6_뇌/국소회로_상태다양체_흐름_대응/repro/adult_l4_riemann_fold_contract_v2.json)

Machine contract SHA-256: `93b09e6de6f8f26e9fad336cf713c98d49d8d4b2e3ea994b91c6adde5c7afe43`

`STATUS_SENTINEL=SCHEMA_FREEZE_CANDIDATE`

`L4_GATE_EVALUATED=false`

`BIOLOGICAL_ENDPOINT_EVALUATED=false`

`EXECUTION_AUTHORIZED=false`

`CLAIM_CEILING=BIO_EVIDENCE_L0`

이 문서의 운용 상수와 exact 식은 machine contract가 정본이다. 이 문서는 그 계약을
사람이 감사할 수 있게 설명한다. v1 독립감사는 `BLOCKER 8 / DO_NOT_FREEZE`였고,
이 v2는 그 오류를 닫기 위한 후보이지 실험 결과가 아니다. 새 공개자료 다운로드는
필요하지 않다.

## 0. 목표, 현재 상태, 다음 gate

- **최종 목표:** 성체 M1의 고정된 source-state chart와 동일 접촉·동일 postsynaptic
  cell 집합에서, 무작위 contact-efficacy 변화가 국소 predictive Fisher geometry를
  변형하고 사전고정한 생물학적 상태가 그 변형과 별도 행동의 인과적 공동변화를
  만드는지 판정한다.
- **이번 하위 목표:** 자극기 좌표를 신경상태로 오인하지 않고, 좌표불변 접힘량,
  가역 동일접촉 조작·rescue, 인과상태와 측정량의 분리, holdout·검정력을 결과 전
  계약으로 고정한다.
- **현재 상태:** 조건부 정보기하 수학과 개별 생물학적 부품 근거만 있다. 통합 실험,
  생물 endpoint, L4 gate는 전부 미평가다.
- **목표 이탈 방지:** 청소년기 고정, 물리적 Lorentz 시공간, 피질의 해부학적 주름,
  AGI 성능은 이 계약의 endpoint가 아니다.
- **다음 gate:** §4의 가역 동일접촉 도구와 §8의 장치 gate가 실제 development
  cohort에서 결과 방향을 보지 않고 통과해야만 confirmation을 열 수 있다. 현재는
  그 도구가 통합 검증되지 않아 `REVERSIBLE_SAME_CONTACT_TOOL_STOP`이다.

## 1. v1 감사에서 무엇을 폐기했는가

| v1 문제 | v2 조치 |
|---|---|
| 광자극 진폭을 $z$라 부름 | 장치 명령 $a$와 독립 측정 neural state $z$를 분리 |
| matrix-log의 whitened basis와 원 chart 축을 혼합 | 방향별 길이비의 log로 좌표불변 scalar 정의 |
| 계산된 $m=s(g)$를 causal state로 취급 | 생물 상태 $M$과 측정량 $g,m$을 분리하고 `do(M)`만 허용 |
| 전체 출력분포 RESTORE 대 ORTHOGONAL만 비교 | `RESTORE>OFF`, `RESTORE>ORTHOGONAL`, `ORTHOGONAL≈OFF`, arm interaction을 모두 요구 |
| spine voltage를 곧바로 weight로 부름 | presynaptic event, parent-dendrite common mode와 no-event를 분리한 contact transmission efficacy로 제한 |
| AS-PaRac1 축소 뒤 전역 재학습을 rescue로 허용 | 구조보존 양방향 동일접촉 도구와 별도 sham/passive recovery를 요구 |
| 90% grid와 중앙 patch 선택 | 같은 25개 state target 전부를 사전 고정하고 25/25 요구 |
| N=28을 SESOI 보장력으로 오기 | 효과검정과 equivalence를 분리하고 결합 power를 다시 계산 |
| 등록 목표 N와 대체·ITT가 모순 | screen을 먼저 끝내고 exact N을 무작위화하며 이후 대체 금지 |
| validator가 상태·식·임의 threshold 변이를 허용 | exact schema·식·범위·hash·적대 변이 검사를 v2 validator에 결박 |

따라서 v1의 `PASS`는 과학 gate 통과가 아니며, v2에서도 validator 성공은 오직
`CONTRACT_SCHEMA_PASS`를 뜻한다.

## 2. 현재 생물 자료가 주는 것과 주지 않는 것

- Hayashi-Takagi et al. 2015는 성체 M1의 task-tagged spine 축소와 운동행동
  손상을 보였지만, 구조를 보존한 동일접촉의 양방향 효능 조작·복구를 보이지 않았다:
  [Nature](https://doi.org/10.1038/nature15257).
- paCaMKII는 in-vivo single-spine potentiation의 후보 성분이지만 AS-PaRac1과 결합한
  성체 M1 동일접촉·행동 rescue가 아니다:
  [Nature Communications](https://doi.org/10.1038/s41467-021-21025-6).
- Rais & Wiegert 2026은 성체 same-spine 기능·구조 종단을,
  Chen et al. 2025는 holographic source mapping과 postsynaptic current calibration을
  각각 지지한다: [Nature Communications](https://doi.org/10.1038/s41467-026-71332-z),
  [Nature Neuroscience](https://doi.org/10.1038/s41593-025-02024-y).

이 자료들은 장치의 부품 근거다. 서로 다른 동물·영역·cohort를 이어 붙여
$\Theta\to g\to Y$의 L4 합성증거로 세지 않는다.

## 3. 주장 범위와 causal objects

v2의 DAG는 다음처럼 측정량과 생물상태를 분리한다.

$$
Z^-_\Theta\to\Theta,\qquad
a\to z,\qquad
(z,\Theta)\to M\to O_{\rm future},\qquad
M\to Y,\qquad
Z_M\to M,\qquad
Z^+_\Theta\to\Theta.
$$

여기에 $\Theta\to O_{\rm future}$, $\Theta\to Y$, $Z_M\to O_{\rm future}$,
$Z_M\to Y$와 사전 공변량 $U_{\rm pre}\to(M,O_{\rm future},Y)$를 명시적으로
감사한다. 즉 DAG가 완전매개나 controller exclusion을 선결하지 않는다.

정보계량과 접힘 요약은

$$
g_{i,t,k}(z)=I_z[p_{i,t,k}(O_{\rm future}\mid z,h,c)],
\qquad
m_{i,k}^G=s_{\rm pre}(g_{i,\rm PRE,BASELINE},g_{i,\rm POST,k})
$$

여기서 $k\in\{\mathrm{STATE\_OFF},\mathrm{STATE\_RESTORE},
\mathrm{STATE\_ORTHOGONAL}\}$이다. main mechanism endpoint는
$m_{i,\mathrm{STATE\_OFF}}^G$이고 state-controller 대비는 같은 animal의 세
$m_{i,k}^G$를 쓴다.

이를 **측정**한다. $g$와 $m_{i,k}^G$는 생물학적 물질이나 직접 조작변수가 아니다.
`do(g)`와 `do(m)`는 금지하고, 사전고정한 postsynaptic predecision state $M$에만
무작위 assigned-target intervention을 한다. `m=q(M)`의 held-out 국소식별성과
nuisance-state 동등성이 실패하면 metric-specific mediation을 주장하지 않는다.

통과 뒤 허용되는 가장 강한 문장도 다음으로 한정한다.

> 명시한 성체 M1 preparation의 고정 source-state와 동일 contact/cell 집합에서,
> contact efficacy 조작이 output-relative predictive Fisher geometry를 바꾸었고,
> 별도로 무작위화한 생물상태 $M$이 geometry-linked 변화와 과제행동의 인과적
> 공동회복을 만들었다.

이는 완전매개, 전뇌 다양체, 물리적 시공간 곡률을 뜻하지 않는다.

## 4. 동일접촉 미시변수와 가역 조작

### 4.1 baseline denominator

randomization 전에 각 contact를

```text
animal/FOV/source_cell_or_bouton/post_cell/dendrite/spine
```

으로 잠그고 그 집합을 $C_0$라 한다. exact 8 postsynaptic cells 모두가 $C_0$ contact를
하나 이상 가진다. 부모 dendrite가 두 구조채널에서 보이는데 spine이 연속 두 stack에서
사라지면 biological loss이며 $I_{\rm present}=0$, $\Theta=0$으로 남긴다. survivor
분석에서 제외하지 않는다. dendrite나 sensor 자체가 보이지 않으면 technical NA이며
0으로 코딩하지 않는다. 새로 생기거나 재출현한 spine은 새 ID이므로 rescue가 아니다.

과제별 집합 $C_{A0},C_{B0}$는 겹치지 않는 task-tag window와 functional source mapping을
둘 다 통과한 contact로 randomization 전에 잠근다. dual-tag contact는 두 primary 집합에서
모두 제외한다. development gate는 target-tag recall simultaneous LCL $\ge0.80$,
off-target activation과 tag-overlap simultaneous UCL $\le0.15$, presynaptic source
identity overlap LCL $\ge0.80$을 요구한다. 이 값은 문헌의 효과크기가 아니라 장치
식별 threshold다.

### 4.2 직접 contact transmission efficacy

각 source $p$와 spine $s$에 대해

$$
\Theta_{p,s}
=E[Q_{\rm spine}-Q_{\rm parent}\mid
\text{verified source event }p,h,c]
-E[Q_{\rm spine}-Q_{\rm parent}\mid
\text{matched no-event},h,c]
$$

를 쓴다. presynaptic AP 또는 release, 고정 monosynaptic latency window,
parent-dendrite/somatic common mode, nearest non-target source와 opsin-negative 대조를
동시에 기록한다. morphology나 AS-PaRac1 intensity만으로 통과할 수 없다. held-out
direct calibration 또는 source→same-spine identity가 실패하면 각각
`THETA_DIRECT_ASSAY_STOP`, `SOURCE_CONTACT_IDENTITY_STOP`이다.

동물별 summary는 task별 baseline denominator를 유지한다.

$$
\bar\Theta^{(q)}_{i,t}=|C_{q0}|^{-1}
\sum_{s\in C_{q0}}I_{{\rm present},s,t}\Theta_{i,s,t},
\qquad q\in\{A,B\}.
$$

main $\Theta$ endpoint는 $C_{A0}$의 $\bar\Theta^{(A)}$이고 $C_{B0}$는 고정
specificity control이다. 전체 $C_0$ 평균으로 TARGET_A와 OFFTARGET_B를 섞지 않는다.

rescue에서는 signed mean의 과소·과대복구 상쇄를 금지한다.

randomization 전 각 contact에 같은 estimator를 쓴 8개 독립 repeatability block을
기록한다. block마다 verified-source-event 40 trials와 matched-no-event 40 trials를 쓴다.

$$
\sigma_{i,s,\rm repeat}
=\sqrt{\frac1{7}\sum_{b=1}^{8}
(\Theta_{i,\rm PRE,s,b}-\bar\Theta_{i,\rm PRE,s,\cdot})^2},
\qquad
\delta_{i,s,\rm contact}=0.5\sigma_{i,s,\rm repeat}.
$$

두 값은 어떤 arm 공개나 randomization보다 먼저 고정한다. $\sigma$가 0, 음수,
비유한이면 floor나 pooled-contact SD를 넣지 않고 `THETA_REPEATABILITY_STOP`이다.

$$
R^\Theta_i=|C_{A0}|^{-1}\sum_{s\in C_{A0}}
\frac{|\Theta_{i,\rm RESCUE,s}-\Theta_{i,\rm PRE,s}|}
{\sigma_{i,s,\rm repeat}},
$$

$$
F^\Theta_i=|C_{A0}|^{-1}\sum_{s\in C_{A0}}
\mathbf 1\{|\Theta_{i,\rm RESCUE,s}-\Theta_{i,\rm PRE,s}|
\le\delta_{i,s,\rm contact}\}.
$$

$|C_{A0}|\ge20$을 사전 적격조건으로 둔다. 동물별
$C_i^\Theta=I[F_i^\Theta\ge0.90\land |C_{A0}|\ge20]$를 만들고,
$R^\Theta_i$의 one-sample upper-margin test와
$\Pr(C_i^\Theta=1)$의 one-sided exact Clopper--Pearson LCL $\ge0.90$을 서로 다른
atomic test로 요구한다. 구조소실 contact는 rescue failure이며 새 contact로 대체하지
않는다.

### 4.3 아직 없는 핵심 도구

primary 도구는 같은 $C_0$ contact에서 구조를 보존한 채 $\Theta$를 낮췄다가 다시
올리는 `BIDIRECTIONAL_STRUCTURE_PRESERVING_SAME_CONTACT_EFFICACY_TOOL`이어야 한다.
development에서 다음을 실제로 통과해야 한다.

1. 동일 contact에서 양방향 $\Theta$ 변화.
2. structural survival의 sham equivalence.
3. neighbor·off-target $\Theta$ equivalence.
4. depression·potentiation 파장의 spectral independence.
5. awake adult M1에서 반복 가능성.

현재 공개 근거는 이 통합을 닫지 못한다. 그러므로 이 v2는 이 항목에서 이미
`REVERSIBLE_SAME_CONTACT_TOOL_STOP`이고 실행 비허가다.

## 5. actuator, neural-state chart, mediator, output의 분리

### 5.1 $a$는 장치 명령이고 $z$가 신경상태다

$$
\Phi_{i,t}(a;h,c)
=E[Z_{\rm trial}\mid do(A=a),h,c,i,t].
$$

- $a=(a_A,a_B)$는 `ACTUATOR_LOG`의 광세기·펄스·좌표다.
- $z=(z_A,z_B)$는 같은 source cell/axon ID를 별도 `SOURCE_STATE_CHANNEL`로 읽어
  development에서 고정한 encoder로 얻는다.
- encoder 입력에는 $a,O,\Theta,M,Y$, arm, POST outcome을 넣지 않는다.
- actuator repeatability metric
  $c_{a,i}=\operatorname{diag}[\operatorname{Var}_{\rm PRE}(a)]^{-1}$를 먼저 고정한다.
  모든 point와 PRE/POST에서
  $c_{a,i}^{-1}(D_a\Phi)^Tr_i(D_a\Phi)$의 generalized singular-value-squared를 쓴다.
  minimum simultaneous 95% LCB $\ge0.20$, condition-number UCB $\le10$이어야 한다.
- 네 상태 각각에서
  $D^A_{i,k}=\max_{j\le25}\operatorname{ELPD}_{\rm heldout}
  [p(O\mid z,a,h,c)-p(O\mid z,h,c)]$를 구한다. 각 upper 95% bound가
  $0.5$ SD와 $0.01$ nat/trial보다 모두 작아야 한다. PRE SD가 0.02 nat/trial을
  넘으면 physical margin power가 부족하므로 `ATOMIC_TEST_POWER_STOP`이다. 이 네
  direct-path decisions는 TARGET_A의 primary 네 상태에서 평가해 §9 atomic ledger에
  포함한다.

실패하면 $I_a[p(O\mid a)]$라는 actuator-response pullback만 말할 수 있고 neural-state
metric 주장은 중단한다.

PRE의 5×5 actuator grid로 얻은

$$
P_i=\{z_{ij}=\Phi_{i,\rm PRE}(a_j):j=1,\ldots,25\}
$$

를 물리적 state target으로 잠근다. POST에는 $a$를 재보정해 같은 $z_{ij}$를 실현한다.
한 점이라도 PRE/POST image의 공통부분에 없으면 patch를 줄이지 않고
`STATE_TARGET_OVERLAP_STOP`이다.

### 5.2 생물 mediator $M$

고정된 8 postsynaptic cell의 입력 후·출력 전 상태를

$$
M=B_M^TX_{\rm post}[0,50\ \mathrm{ms}]
$$

로 정의한다. $B_M$은 development neural data만으로 고정하며 행동, arm, 효과방향,
confirmation output을 쓰지 않는다. `STATE_RESTORE`는 confirmation SHAM 출력분포가
아니라 같은 동물의 randomization 전 $M_{\rm pre}(z,h,c)$를 겨냥한다.

$r_{M,i}(z)=[\Sigma^{M}_{i,\rm PRE,repeat}(z)]^{-1}$를 randomization 전에 고정하고

$$
d^M_{i,k}=\frac1{25}\sum_{j=1}^{25}
\|M_{i,\rm POST,k}(z_{ij})-M_{i,\rm PRE}(z_{ij})\|_{r_{M,i}},
$$

$$
P^M_{i,k}=\frac1{25}\sum_{j=1}^{25}
\langle u^M_{i,\rm restore}(z_{ij}),
M_{i,\rm POST,k}(z_{ij})-M_{i,\rm POST,OFF}(z_{ij})
\rangle_{r_{M,i}}
$$

를 exact state endpoint로 쓴다. RESTORE는 $d^M$에서 OFF와 ORTHOGONAL을 모두
이겨야 하고, ORTHOGONAL과 OFF의 restore-axis projection $P^M$은 paired
equivalence해야 한다.

$M\to m^G$ 국소다리도 문자열로 가정하지 않는다. model/controller development
animals의 randomized subthreshold $M$ perturbation만으로 per-target fold contribution
$\ell=e_A-e_B$를 예측하는 고정 $C^2$ 모형
$q_{\rm dev}(M,z,h,c)$를 적합한다. 같은 development data와 intrinsic $z$ basis를
쓰되 $M$만 뺀 null $q^0_{\rm dev}(z,h,c)$를 같은 시점에 함께 고정한다. 행동,
confirmation arm/outcome, 효과방향은 입력에서 제외한다. confirmation에서는 다시
적합하지 않고

$$
L_{i,k}=\frac1{25}\sum_j\left[
(\ell_{i,k}(z_j)-q^0_{\rm dev}(z_j,h,c))^2-
(\ell_{i,k}(z_j)-q_{\rm dev}(M_{i,\rm POST,k}(z_j),z_j,h,c))^2
\right]
$$

를 sealed heldout score improvement로 쓴다. OFF, RESTORE, ORTHOGONAL 세 상태에서
각각 $L_{i,k}>0$을 검정한다. 별도로
$B_{i,k}=\min_{j\le25}|D_{u^M_{\rm restore}}q_{\rm dev}(M_{i,\rm POST,k}(z_j),z_j,h,c)|$
를 만들고 세 상태 각각의 simultaneous 95% LCB가 standardized fold/standardized
$M$ 단위로 0.20 이상이어야 한다. PRE $\operatorname{SD}(B_{i,k})\le0.40$이 아니면
0.20 physical threshold의 power가 부족하므로 STOP한다. heldout score 3개와 derivative
3개를 각각 atomic ledger에 넣으며, 어느 하나라도 실패하면
`M_TO_METRIC_LOCAL_IDENTIFICATION_STOP`이다.

### 5.3 exact future output

동일한 8 postsynaptic cells를 사전고정한 $F_A,F_B$ 각 4개로 나누고

$$
O_{\rm future}
=\left(
\mathbf 1[N_{F_A}(50,150\ \mathrm{ms})>0],
\mathbf 1[N_{F_B}(50,150\ \mathrm{ms})>0]
\right)
$$

를 쓴다. 관측공간은 $\Omega=\{00,01,10,11\}$, base measure는 counting measure다.
PRE/POST에서 cell, threshold, window, alphabet을 바꾸지 않는다. 한 cell이라도 잃으면
대체·차원축소 없이 해당 animal metric은 ITT missing이다.

시간창은 $W_H=[-200,-100)$, $W_Z=[-100,0)$, $W_M=[0,50)$,
$W_O=[50,150)$ ms로 고정한다.

### 5.4 실행 가능한 Task-A/B 행동 endpoint

Task A는 cue A 뒤 lever target $L_1\to L_2\to L_3$, Task B는 cue B 뒤
$L_3\to L_2\to L_1$ 순서다. cue 뒤 2,000 ms 안에 세 target zone을 정해진 순서로
모두 통과하고 out-of-order crossing이 없을 때만 success=1이다. 각
task×time×state-condition의 분모는 정확히 40 randomized cue trials다.

lever coordinate는 randomization 전에 보정한 normalized displacement
$x\in[-1,1]$이며 1 kHz 이상으로 읽는다. 구간은
$L_1=[-0.90,-0.60]$, $L_2=[-0.15,0.15]$, $L_3=[0.60,0.90]$로 고정한다.
entry time은 인접 sample 사이 linear interpolation으로 얻은 첫 inward boundary
crossing 뒤 30 ms 이상 연속 체류한 시점이다. 아직 차례가 아닌 뒤쪽 zone에 먼저
들어가면 즉시 out-of-order failure다. cue 전 200 ms 이상 Task A는
$x\in[-1.00,-0.95]$, Task B는 $x\in[0.95,1.00]$에 있어야 하며 실패하면
non-initiation으로 고정 분모에서 0점 처리한다.

$$
Y^{(q)}_{i,t,k}=\frac1{40}\sum_{\ell=1}^{40}
\mathbf 1\{\mathrm{success}^{(q)}_{i,t,k,\ell}\},
\qquad q\in\{A,B\}.
$$

단위는 proportion $[0,1]$이다. non-initiation, timeout, incorrect trial은 고정 분모에서
failure로 센다. lever hardware나 clock 자체가 소실되면 trial을 지우지 않고 animal
endpoint technical NA/ITT missing으로 처리한다. main mechanism endpoint는
$\Delta Y^{(q)}_{i,\rm OFF}=Y^{(q)}_{i,\rm POST,OFF}-Y^{(q)}_{i,\rm PRE,BASELINE}$다.
task-specificity는 TARGET_A 안의
$S_i=\Delta Y^{(A)}_{i,\rm OFF}-\Delta Y^{(B)}_{i,\rm OFF}$로 고정한다. state와
rescue의 primary 행동은 모두 Task A이며 각각 $Y^{(A)}_{i,\rm POST,k}$와
$Y^{(A)}_{i,\rm POST,RESCUE\ ARM,RESTORE}$다. geometry probe light는 없지만
randomized state controller는 해당 조건대로 켜진다.

각 behavior estimand는 자기 자신의 blinded pre-randomization animal SD를 stratum fixed
effects와 함께 고정한다. paired estimand는 자기 endpoint의 inert-controller repeat
difference SD를 별도로 고정한다. 행동은 metric이나 controller training에 넣지 않는다.

## 6. 동물별 predictive Fisher와 좌표불변 접힘

### 6.1 raw metric

$$
s_{i,t,k}(o;z,h,c)=\partial_z\log p_{i,t,k}(o\mid z,h,c),
$$

$$
g_{i,t,k}(z)=\sum_{h,c}Q_{i0}(h,c)
\sum_{o\in\Omega}p_{i,t,k}(o\mid z,h,c)
s_{i,t,k}s_{i,t,k}^{T}.
$$

$Q_{i0}(h,c)$는 randomization 전 baseline에서 잠그고 PRE/POST에 같이 쓴다. 각 target의
96 trials는 48 calibration/48 sealed holdout으로 고정한다. primary estimator는
동물별 4-fold cross-fit held-out raw score outer product다. ridge, eigenvalue clipping,
동물 pooling으로 SPD를 만들 수 없다. working regularized metric은 controller 진단에만
쓰며 G4와 $m_{i,k}^G$에는 쓰지 않는다. likelihood family는 고정 $r_i$의
Laplace--Beltrami heat-kernel basis와 $\overline U_i$의 Neumann boundary condition을
쓰는 four-category multinomial-logit $C^2$ 모형이다. basis rank, penalty, bandwidth,
$h,c$ effects는 development에서만 고정한다. confirmation parameter는
animal×time×state condition별 calibration trials에서만 fit하고 score는 sealed holdout에서
평가한다. saturation은 frozen censoring likelihood로 남기거나 식별 실패 시 animal
endpoint missing으로 처리한다. held-out calibration/residual band가 실패하면 모형을
고쳐 구제하지 않고 새 v3 계약으로 정지한다.

네 output category의 simultaneous held-out 95% probability lower bound가 모두
0.01 이상이어야 한다. pseudocount나 softmax의 형식적 positivity로 support를
통과시키지 않는다.

### 6.2 invariant SPD gate

STATE_CHANNEL의 PRE repeatability 관측모형
$q_{i,\rm PRE}(Z_{\rm obs}\mid z,h,c)$는 구조를 development에서 고정하고 동물별
parameter는 randomization 전 repeat에서만 적합한다. 그 score Fisher

$$
r_i(z)=\sum_{h,c}Q_{i0}(h,c)E_q\!\left[
\partial_z\log q_{i,\rm PRE}\,
(\partial_z\log q_{i,\rm PRE})^T
\right]
$$

를 animal-level cross-fit heldout raw outer product로 정의하고 POST에서 갱신하지
않는다. covariance inverse나 componentwise/log-Euclidean tensor interpolation,
ridge, eigenvalue clipping은 $r_i$를 만들 수 없다. 이 Fisher 정의 때문에 $r_i$는
일반적인 smooth chart change에서 진짜 $(0,2)$ tensor로 변환한다. SPD와 conditioning은

$$
\det[g_{i,t,k}(z_j)-\lambda r_i(z_j)]=0
$$

의 generalized eigenvalue로 판정한다. PRE/POST 25점 전부에서 simultaneous 95% LCB
$\lambda_{\min}\ge0.02$, UCB/LCB condition number $\le50$을 요구한다. 24/25,
중앙 3×3, 결과를 본 patch 축소는 실패다.

$z=\phi(\tilde z)$, $J=\partial z/\partial\tilde z$이면

$$
\tilde g=J^TgJ,\qquad
\tilde r=J^TrJ,\qquad
\tilde u=J^{-1}u
$$

를 동시에 변환한다.

### 6.3 invariant fold

$D_a\Phi_{i,\rm PRE}$의 두 column을 $r_i$에 대해 Gram--Schmidt해 물리적 vector field
$u_A,u_B$로 잠근다. 방향별 log stretch는

$$
e_{i,k,d}(z_j)=\frac12\log
\frac{u_{i,d}(z_j)^Tg_{i,\rm POST,k}(z_j)u_{i,d}(z_j)}
{u_{i,d}(z_j)^Tg_{i,\rm PRE,BASELINE}(z_j)u_{i,d}(z_j)}.
$$

고정 atomic measure $\mu_{i0}=25^{-1}\sum_{j=1}^{25}\delta_{z_{ij}}$에 대해

$$
m_{i,k}^G=\frac1{25}\sum_{j=1}^{25}
[e_{i,k,A}(z_{ij})-e_{i,k,B}(z_{ij})]
$$

를 state-condition별 fold summary로 쓴다. main mechanism에는 $k=\mathrm{OFF}$를
쓰고 controller contrast에는 세 $k$를 각각 쓴다. 이는 chart-invariant한 output-relative
방향 변형이며 물리적 곡률이 아니다.

### 6.4 sampled grid, open patch, Finsler

정적 5×5 결과만으로 허용되는 것은 25개 state에서의 predictive Fisher geometry다.
$P_i$와 열린 영역을 같은 것으로 놓지 않는다. 5×5의 16 quadrilateral을 사전고정한
diagonal로 나눈 32-triangle complex의 interior를 $U_i$로 정의한다. 열린 patch에는
고정 $r_i$의 Levi--Civita connection을 쓴다. $\overline U_i$는 비교점 사이 unique
shortest $r_i$-geodesic을 갖는 geodesically convex set이어야 한다. 이를 32 cell의
Riemannian energy에 대한 interval-Newton uniqueness·positive second variation과
boundary inward-convexity interval로 검증한다. fiber가 다른 두 점의 tensor를 직접
빼지 않고 그 geodesic의 $r_i$-parallel transport로 비교한다. 거리는

$$
d_{r_i}(z,z')=\inf_{\gamma:z\to z'}\int_0^1
\sqrt{\dot\gamma(s)^Tr_i(\gamma(s))\dot\gamma(s)}\,ds
$$

로 고정한다.

$$
A_{i,t,k}(z)=r_i(z)^{-1}g_{i,t,k}(z),
$$

$$
h_{U,i}=\sup_{z\in\overline U_i}\min_j d_{r_i}(z,z_{ij}),
$$

$$
L_{A,i,t,k}=\sup_{z\ne z'}
\frac{\|\Pi^r_{z'\to z}A_{i,t,k}(z')\Pi^r_{z\to z'}
-A_{i,t,k}(z)\|_{\mathrm{op},r_i}}
{d_{r_i}(z,z')}.
$$

$U_i$가 공집합·퇴화 complex가 되는 것을 막기 위해 32개 triangle 모두의
$r_i$-inradius simultaneous 95% LCB $\ge0.05$, total $r_i$-area LCB $\ge0.25$,
$0<\operatorname{LCB}(h_{U,i})\le\operatorname{UCB}(h_{U,i})\le0.50$을 요구한다.
실패하면 `REFERENCE_PATCH_GEODESIC_CONVEXITY_STOP`이며 아래 extension 식을 평가하지
않는다.

$r_i$는 위 PRE repeatability likelihood의 intrinsic Fisher tensor field다. output
likelihood도 $r_i$-intrinsic heat-kernel basis로 적합하여 component spline의 chart
dependence를 쓰지 않는다. $L_A$ UCB는 intrinsic likelihood coefficient confidence
set의 32-cell interval arithmetic와 9×9 lattice 중 25 anchor를 제외한 56 sealed
interleaved targets로 검증한다. 열린 patch certificate는 모든 time/state condition에서

$$
\min_j\operatorname{LCB}\lambda_{\min}(A_{i,t,k}(z_{ij}))
-\operatorname{UCB}(L_{A,i,t,k})h_{U,i}
=:\rho^{\rm LCB}_{i,t,k}>0
$$

의 uniform extension certificate가 추가로 통과해야 한다. 동물별
$C^{\rm GEO}_{i,t,k}=I[\text{patch nondegenerate, common support, generalized condition,
coordinate covariance, }\rho^{\rm LCB}_{i,t,k}>0,\text{ reference patch certified}]$를
만들고 BASELINE/OFF/RESTORE/ORTHOGONAL 각각에서
$\Pr(C^{\rm GEO}_{i,t,k}=1)$의 one-sided exact Clopper--Pearson LCL $\ge0.90$을
TARGET_A의 네 상태에서 요구한다. 이는 4 atomic tests다. SHAM/OFFTARGET_B는 sampled-grid
controls로만 쓰며 그 arm에 열린-patch 주장을 확장하지 않는다. 현재는 미평가이므로
`open_patch_claim_authorized=false`다.

정적 Fisher가 quadratic이라는 사실만으로 Finsler를 기각하지 않는다. frozen 5×5 grid의
TARGET_A의 정확한 central 3×3 targets와 BASELINE/OFF/RESTORE/ORTHOGONAL에
$0^\circ,90^\circ,45^\circ,-45^\circ,22.5^\circ,67.5^\circ$의 여섯 frozen axes와
각 양·음 방향 ordered arrival를 endpoint·duration·energy·reset history·context와
함께 맞춘다. $22.5^\circ,67.5^\circ$ axes가 $n=4$의 sine/cosine phase를 모두
식별하므로 harmonic design rank는 6이다. base model
$p_R(O_{\rm future}\mid z,h,c,v^Tg v)$에는 Riemann quadratic term만 넣는다. exact
alternative $p_D(O_{\rm future}\mid z,v,h,c)$에는 동일 base에
$\{\cos\theta,\sin\theta,\cos3\theta,\sin3\theta,\cos4\theta,\sin4\theta\}$를
모두 더한다.

state $k$와 harmonic $h$마다 full model과 drop-$h$ model의 heldout log-score gain을
9 targets에서 구하고
$D_{i,k,h}=\max_{j\in\mathrm{central}\ 3\times3}D_{i,k,h,j}$를 쓴다. target 평균을
쓰지 않아 국소 방향효과가 상쇄되지 않는다. 6 harmonics×4 states의 24 components
각각에서 upper 95% bound가 $0.5$ SD 미만이면서 $0.01$ nat/trial 미만이어야 한다.
pre-randomization $\operatorname{SD}(D_{i,k,h})\le0.02$ nat/trial이어야 physical
margin이 적어도 $0.5$ SD가 되며, 아니면 `ATOMIC_TEST_POWER_STOP`이다. 이 24 tests는
§9에 포함한다.
통과해도 배제하는 것은 이 사전고정 angular competitor뿐이며 모든 가능한 Finsler
geometry를 배제했다고 주장하지 않는다.

## 7. 세 단계 무작위 개입

### 7.1 mechanism intervention

main randomization은 `TARGET_A:SHAM:OFFTARGET_B=3:1:1`이다.

- `TARGET_A`: $C_{A0}$의 task-A contact를 구조보존 도구로 약화.
- `SHAM`: 기능불능 construct와 동일 광·시간.
- `OFFTARGET_B`: 같은 수·에너지의 task-B contact 조작.

### 7.2 mediator-state intervention

각 animal은 outcome-blind Williams-balanced 순서로 다음 세 조건을 경험한다.

- `STATE_OFF`: target-effective state displacement가 없는 energy/heat matched control.
- `STATE_RESTORE`: 같은 animal의 $M_{\rm pre}$ 방향을 복원.
- `STATE_ORTHOGONAL`: photon dose, cell 수, timing, induced-spike norm을 맞추되
  fixed reference metric에서 restore displacement와 직교.

다음을 모두 요구한다.

1. `RESTORE>OFF`와 `RESTORE>ORTHOGONAL` for $M$ target distance, $m_{i,k}^G$, $Y_A$.
2. `ORTHOGONAL≈OFF` for $M$ restore-axis projection, $m_{i,k}^G$, $Y_A$.
3. controller arm interaction은 결과 뒤 endpoint를 고르지 않고 다음 세 개를 모두 쓴다.
   $[(d^M_{\rm OFF}-d^M_{\rm RESTORE})_{\rm TARGET_A}-
   (d^M_{\rm OFF}-d^M_{\rm RESTORE})_{\rm SHAM}]>0$,
   $[(m^G_{\rm RESTORE}-m^G_{\rm OFF})_{\rm TARGET_A}-
   (m^G_{\rm RESTORE}-m^G_{\rm OFF})_{\rm SHAM}]>0$,
   $[(Y_{A,\rm RESTORE}-Y_{A,\rm OFF})_{\rm TARGET_A}-
   (Y_{A,\rm RESTORE}-Y_{A,\rm OFF})_{\rm SHAM}]>0$.
   세 interaction atomic tests가 전부 통과해야 한다.
4. controller 동안 원 $\Theta$와 source $z$의 equivalence.
5. photon, heat, pupil, arousal, locomotion, stimulated-cell count, induced-spike count,
   latency nuisance kernel equivalence.

achieved $m$ 범위에 사후 conditioning하지 않는다. carryover/washout이 development에서
실패하면 parallel 계약을 새로 만들며 이 v2 confirmation은 열지 않는다.

### 7.3 independent same-contact rescue randomization

TARGET_A animal을 `SAME_CONTACT_RESTORE`, `RESCUE_SHAM`, `PASSIVE_RECOVERY`로 다시
1:1:1 무작위화한다. primary rescue는 같은 $C_{A0}$에서 signed mean이 아니라
$R_i^\Theta$ absolute contact error의 upper-equivalence와 $F_i^\Theta$ contact-fidelity
animal-pass fraction의 exact LCL $\ge0.90$을 별도 atomic test로 함께 요구한다.
$m_{i,k}^G,Y_A$는 두 rescue control 모두에 대한
방향 회복으로 별도 conjunction을 이룬다. “baseline equivalence 또는 방향 회복”처럼
OR 조건으로 구제하지 않는다. retraining이나 global re-potentiation은 새 synapse와
다른 회로를 바꾸므로 동일접촉 rescue가 아니다.

## 8. cohort, holdout, ITT

### 8.1 development

tool-validation 최대 12 animals와 model/controller 최대 24 animals를 분리해 총 36을
넘지 않는다. 전자는 같은 contact의 양방향 $\Theta$ fidelity와 구조생존·neighbor effect를
읽을 수 있지만 그 animal을 model 또는 confirmation에 재사용하지 않는다. 후자는 apparatus,
safety, measurement error, state encoder, intrinsic likelihood structure, controller
fidelity·carryover, randomized subthreshold $M\to\ell$ local-map fidelity, open-patch
derivative-bound 방법과 nuisance threshold만 정한다. task/behavior 효과와 main
mechanism-to-geometry 방향을 보거나 confirmation threshold를 맞추는 데 쓰지 않는다.

### 8.2 confirmation enrollment

- pre-randomization screen cap: 680 animals.
- 모든 QC를 먼저 끝낸 뒤 exact 540 eligible animals를 randomize한다.
- main arms: TARGET_A 324, SHAM 108, OFFTARGET_B 108.
- TARGET_A의 second randomization: rescue 세 arm 각 108.
- 540을 확보하지 못하면 `ELIGIBILITY_CAP_STOP`이다.
- randomization 뒤 대체는 없다. 모든 animal은 ITT에 남는다.

confirmation의 controller target은 같은 animal의 intervention 전 $M_{\rm pre}$와
development-frozen algorithm에서만 온다. confirmation SHAM의 post-learning output은
target·모형 선택에 쓸 수 없다. trial holdout과 development→confirmation animal holdout을
서로 다른 것으로 기록한다.

primary endpoint에 technical NA가 단 하나라도 생기면 imputation으로 PASS를 만들지 않고
즉시 `MISSINGNESS_STOP`이며 primary decision을 내리지 않는다. 정지 뒤 endpoint-specific
worst-case bounds는 설명용으로만 보고하며 PASS나 재개 근거가 될 수 없다. biological
contact loss는 parent가 보이면 예정대로 $\Theta=0$/rescue failure이지 technical NA가
아니다. cell 교체·차원축소, replacement, 결과 뒤 N 증가는 모두 금지한다. 이
zero-missingness 규칙 때문에 complete randomized cell은 정확히 108이어야 한다.

## 9. 검정력과 estimand 규칙

기존 N=28은 폐기한다. v2의 randomized atomic parallel cell은 108 animals이고 6개
controller sequence에 정확히 18 animals씩 배정한다. any technical NA는 STOP이므로
complete N은 108이며 모든 power receipt는 더 보수적인 N=100을 사용한다.

각 endpoint의 standardized effect는 그 endpoint 자체의 blinded pre-randomization
repeatability SD를 stratum 안에서 고정해 쓴다. SD가 0이거나 불안정하면 pooled
post-outcome SD로 바꾸지 않고 `ATOMIC_TEST_POWER_STOP`이다.

t/TOST receipt는 animal 간 독립과 stratum residual의 Gaussian sampling model을
사전가정한다. $R^\Theta$는 latent contact expectation에서 만든 animal-level endpoint이며
contact를 독립 표본으로 세지 않는다. 이 sampling model이 arm 공개 전 audit에서 실패하면
rank test로 사후 전환하지 않고 `T_MODEL_ASSUMPTION_STOP`과 새 계약을 요구한다.

| test family | frozen null/design | N | power |
|---|---|---:|---:|
| directional between-arm | $H_0:d\le0$, design alternative $d=0.7$ | 100/group | 0.9994953050 |
| directional paired | $H_0:d\le0$, design alternative $d=0.5$ | 100 pairs | 0.9995509176 |
| paired equivalence | TOST, margin $\pm0.5$ SD, true design effect 0 | 100 pairs | 0.9991018353 |
| one-sample upper margin | $H_0:\mu\ge0.5$ SD, true design effect 0 | 100 | 0.9995509176 |
| one-sample lower directional/margin | $H_0:d\le0$, design alternative $d=0.5$ | 100 | 0.9995509176 |
| exact pass fraction | CP LCL null 0.90, design pass fraction 0.995 | 100; pass if $x\ge96$ | 0.9998414008 |

설계 alternative는 PASS threshold나 SESOI가 아니다. PASS는 frozen 방향 또는 TOST
CI 조건으로 판정한다. 따라서 설계 alternative보다 작은 양의 효과도 CI가 0을 넘으면
통과할 수 있다. $\pm0.5$ SD equivalence는 정확한 0을 증명하지 않고
moderate-or-larger change를 배제할 뿐이다.

exact atomic ledger는 29 estimand ID를 83 tests로 펼친다. actuator direct path는
4개, $\Theta,z$ controller invariance는 각 2개, 세 controller interaction은 3개,
8 nuisance 변수의 RESTORE/OFF·ORTH/OFF는 16개, $M\to\ell$ heldout local-map과
derivative는 각 3개, $R^\Theta/F^\Theta$는 2개, 두 rescue-control 대비는 각 2개,
open patch state gate는 4개, ordered-path state×harmonic components는 24개다. ledger
범위는 모든 post-randomization confirmatory decision이다. pre-randomization
eligibility·measurement QC는 별도 STOP gate이고, G4/G4B의 structural components는 네
$C^{\rm GEO}$ decisions 안에 conjunction으로 들어간다. 83 tests의
conjunction에 대해 dependence를 가정하지 않는 failure
union bound는

$$
1-83(1-0.9991018352612542)=0.9254523266840968
$$

이다. 분석계획이 83개를 넘으면 sample을 결과 뒤 늘리지 않고 새 계약으로 STOP한다.
primary logic은 intersection--union conjunction이며 한 endpoint 양성으로 다른 실패를
구제하지 않는다.

machine contract의 29 estimand ID, atomic count, 방향, equivalence margin이 exact 정본이다. 특히
v1의 achieved-$m$ 사후 clamp `E_DIRECT`는 삭제했다.

## 10. PASS, STOP, 주장 상한

다음은 모두 필요하다.

1. `G0`: construct·protocol·analysis·환경 source lock과 기관 승인.
2. `G1`: spectral, safety, nonplastic probe, identity, measurement precision.
3. `G2`: actuator/state 분리, source rank, 같은 25 state target, direct-path 대조.
4. `G3`: same-contact source-conditioned $\Theta$와 baseline denominator.
5. `G4`: animal-level raw Fisher, 25/25 generalized SPD, 좌표 공변성, ordered paths.
6. `G4B`: 열린 local patch를 말하려면 uniform extension certificate.
7. `G5`: randomized $\Theta$가 $m_{i,\rm OFF}^G$를 바꾸는 두 control 대비.
8. `G6`: geometry-linked 변화와 별도 task-specific behavior.
9. `G7`: randomized $M$의 RESTORE/OFF/ORTHOGONAL conjunction과 exclusion controls.
10. `G8`: same-contact $\Theta$ rescue와 sham/passive controls.
11. `G9`: development/confirmation holdout, power, ITT, missingness, causal audit.

하나라도 빠지면 가장 약한 화살표에서 멈춘다. sampled grid만 통과하고 G4B가 실패하면
열린 국소 Riemann patch는 미확립이다. controller exclusion은 모든 대조를 통과해도
명시한 nuisance 범위 안의 조건부 가정이다. 따라서 유한 실험은 경험적 L4 지지를 줄 수
있지만 논리학적 의미의 “뇌 시공간 완전증명”이나 물리적 Lorentz 시공간 증명을 만들지
못한다.

## 11. 현재 판정

현재는 다음 두 선행조건이 실제로 없다.

1. adult M1에서 검증된 구조보존 양방향 same-contact efficacy tool.
2. 그 도구와 SOURCE/THETA/MEDIATOR/OUTPUT 여섯 채널을 한 preparation에서 분리한
   development receipt.

그러므로 현 판정은

```text
SCHEMA_FREEZE_CANDIDATE
REVERSIBLE_SAME_CONTACT_TOOL_STOP
EXECUTION_NOT_AUTHORIZED
BIO_EVIDENCE_L0
```

이다. 이는 가설이 반증됐다는 뜻이 아니라, 현재 자료와 장치로 완전한 causal closure를
실행할 수 없다는 정확한 기술적 결론이다.
