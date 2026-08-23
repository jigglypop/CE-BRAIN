# BA-SRM6 연구 계약 — 연속 유효차원과 실제 전뇌 칼슘자료 검증

Status: COMPLETE

Date: 2026-08-23

Mode: full

PREDECESSOR: `_workspace/ce/brain-conscious-moment-index-geometry-20260823`

CE_RUN: `_workspace/ce/brain-adaptive-effective-dimension-validation-20260823`

## 1. 질문과 판정 범위

BA-SRM5는 신경계의 causal-history 상태가 무한차원 Hilbert 공간일 수 있음을
정식화했지만, loop가 숫자 4를 선택한다는 주장은 반례로 제거했다. 이번 연구는
그 빈자리에 정수가 아닌 연속 유효차원을 넣고 다음 세 질문만 시험한다.

1. `[정리 후보]` 양의 trace-class operator의 resolvent로 정의한 유효차원이
   연속이고 좌표 회전에 불변이며 regularization scale에 단조적인가.
2. `[산출 후보]` 알려진 spectrum을 가진 합성자료와 real-background
   semi-synthetic 주입에서 그 유효차원을 사전 고정 오차 안에서 회복하는가.
3. `[예측]` 실제 *C. elegans* 전뇌 칼슘자료에서 이 연속 유효차원의 시간 변화가
   과거 행동만 쓴 기준선과 고정 차원·단순 spectrum 요약보다 미래 locomotion을
   더 잘 예측하는가.

세 번째 질문이 통과해도 의식, 해마, 해부학적 간선, 인과 routing 또는 AGI를
입증하지 않는다. 이 자료에는 hippocampus가 없고 conscious report나 개입이 없다.
여기서 `순간`은 점이 아니라 칼슘 측정과 covariance 추정이 허용하는 고정된
약 10초 causal window다.

## 2. 선행 증거 잠금

### PREDECESSOR_EVIDENCE

| artifact | SHA-256 | 상태 | 이번 run에서 허용되는 재사용 | 재사용 금지 |
|---|---|---|---|---|
| BA-SRM5 `00-contract.md` | `3252b2ffdaec7a645806ab1b7c92a7b010ea357e31be87dc76ddc5d64921fbd1` | `COMPLETE` | 무한 history 공간과 finite observation quotient의 구분 | 숫자 4를 prior로 사용 |
| BA-SRM5 `10-sources.md` | `a98c3794d61c376cc6f53cfd3eb2a6ee84d712f8ff7309a4c977baba03bafcf8` | `COMPLETE` | calcium·hippocampal 자료 후보와 측정 한계 | 구성요소 근거를 결합기전 증거로 승격 |
| BA-SRM5 `11-math.md` | `9595a9d133e178698c2cafcfe65ba28b96e505af4642c12e61f3788808b3af2c` | `COMPLETE` | strong metric의 coercivity 조건과 loop-to-4 no-go | recurrent loop에서 고정 rank 도출 |
| BA-SRM5 `12-routes.md` | `267d4facecea344863d6d8d1f8f0edcc76f7845c6cebc4b12cad3a7f599381ec` | `COMPLETE` | fixed-d, dimension-free, high-dimensional matched controls | BA-SRM4의 hard rank 4 재사용 |
| BA-SRM5 `20-audit.md` | `62a7f2fa712ad27c9fec03e446a01f172d6330dcded53698db0527c0b3ca4448` | `Gate: PASS` | successor에 필요한 source/data/split/control 조건 | empirical validation이 이미 끝났다고 서술 |
| BA-SRM5 `31-validation.md` | `918f3b280478b43dfc74be6b8b82d8c044c2ec57850edbb68d498d2263767e37` | `SKIPPED` | `NO_EMPIRICAL_VALIDATION`이라는 음성 경계 | 생물학적 수치 생성 |
| BA-SRM5 `40-final-report.md` | `dce9d6524b7f7d1e05792805710005b4058ff86fdf798410e1da5da8f5021540` | `COMPLETE / EMPIRICAL_INSTANTIATION_BLOCKED` | 연속 유효차원이 필요한 문제 설정 | fixed-4 consciousness 주장 |

현재 route ledger의 계약 전 SHA-256은
`d3d1760185f772ef4446c48ab4ab4d5a3ca9c8f15f569d866f5e7ddaf2aa1c62`다.
BA-SRM3의 clamp-unit 혼합 결과는 계속 비해석 상태이고, BA-SRM4의 hard rank 4는
새 데이터의 비교 대조군일 뿐 선행 양성 근거가 아니다.

## 3. BIO_STARTING_MECHANISM

이 run은 완성된 단일 뉴런 방정식을 출발점으로 삼지 않는다. 출발점은
Hallinen et al.의 동시 전뇌 칼슘·locomotion 측정과 다음의 제한된 관측 기전이다.
숨은 신경활동 $a_i(t)$가 calcium-indicator kernel $k_i$를 거쳐 fluorescence에
기여하고, motion·photobleaching·채널 gain과 측정잡음이 함께 관측된다.

$$
y_{i,t}=\mathcal P_i\!\left[(k_i*a_i)(t),r_{i,t},g_{i,t},m_t\right]
       +\varepsilon_{i,t}.
$$

$\mathcal P_i$의 역은 공개 `Ratio2`만으로 식별되지 않는다. 따라서 spike
deconvolution, firing rate, synaptic current 또는 anatomical edge를 추정하지 않는다.
예측 기준식은 미래 행동 $b_{t+h}$에 대한 과거 행동 autoregression이다.

$$
\widehat b^{\rm AR}_{t+h}
=\alpha+\sum_{\ell\in\{0,1,3,6\}}\beta_\ell b_{t-\ell}.
$$

이 식은 생물학적 기전 동일성 주장이 아니라 CE 추가항의 incremental predictive
value를 측정하는 사전 고정 기준선이다.

## 4. CE_DELTA — 연속 유효차원

한 recording 안에서 train 구간만으로 neuron별 위치와 scale을 고정한 무차원
칼슘벡터를 $x_t\in\mathbb R^N$라 한다. 길이 $W=60$ volume인 causal window를
$X_t=[x_{t-W+1},\ldots,x_t]$로 두고 window mean을 제거한다. 표본 PSD operator는

$$
G_t=\frac{1}{W-1}X_tH X_t^{\mathsf T},
\qquad
H=I-\frac1W\mathbf 1\mathbf 1^{\mathsf T}.
$$

$r_\star=\min(N_{\rm kept},W-1)$를 train neuron-selection 뒤 고정하고, train windows에서

$$
c_G=\operatorname{median}_{t\in\mathrm{train}}
\frac{\operatorname{tr}G_t}{r_\star}
$$

를 고정한다. $c_G\le0$ 또는 유한하지 않으면 해당 recording은 abstain한다.
$\widetilde G_t=G_t/c_G$와 dimensionless $\lambda>0$에 대해 `[정의]`

$$
S_{t,\lambda}
=\widetilde G_t(\widetilde G_t+\lambda I)^{-1},
\qquad
d_{\rm eff}(t;\lambda)=\operatorname{tr}S_{t,\lambda}
=\sum_k\frac{\mu_{k,t}}{\mu_{k,t}+\lambda}.
$$

$\mu_{k,t}$는 $\widetilde G_t$의 eigenvalue다. 유한 관측공간에서 위 식은 항상
유한하다. 무한 Hilbert 공간으로 확장할 때는 $\widetilde G_t$가 positive
self-adjoint trace class여야 하며 compact만으로는 충분하지 않다. 예를 들어
$G=I$이면 $S_\lambda=(1+\lambda)^{-1}I$의 trace는 무한이다. 위상적 manifold dimension과 hard
rank는 정수지만 $d_{\rm eff}$는 연속 유효 자유도다. primary scale은
$\lambda=1$이고, sensitivity curve는 결과와 무관하게
$\lambda\in\{0.1,0.3,1,3,10\}$ 전체를 보고한다. 어느 $\lambda$도 endpoint로
선택하지 않는다.

Finite observation quotient에서 regularized spectral inner product 후보는

$$
A_{t,\lambda,\epsilon}
=\epsilon I+(1-\epsilon)S_{t,\lambda},
\qquad
g_{t,\lambda,\epsilon}(u,v)
=u^{\mathsf T}A_{t,\lambda,\epsilon}v,
$$

$\epsilon=10^{-3}$로 고정한다. $\epsilon I$는 관측으로 발견한 biology가 아니라
analyst regularization prior다. 이 metric을 infinite-history 전체나 structural
connectome metric으로 승격하지 않는다.

같은 recording의 neuron basis에서 다음 dimensionless 변화량을 둔다.

$$
q_t=\frac{d_{\rm eff}(t;1)}{r_\star},
\qquad
\kappa_t=\frac{\lVert S_{t,1}-S_{t-1,1}\rVert_F}
{\sqrt{r_\star}},
$$

$$
\nu_t=\frac{q_t-q_{t-1}}{(t_t-t_{t-1})/\tau_0},
\qquad
\tau_0=\operatorname{median}_{\rm train}(t_t-t_{t-1}).
$$

Train 구간의 positive RMS $\sigma_\kappa,\sigma_\nu$를 고정하고 둘 중 하나가
0 또는 nonfinite이면 moment score는 abstain한다. 그렇지 않으면 `[정의]`

$$
M_t=\exp\!\left[-\left(\frac{\kappa_t}{\sigma_\kappa}\right)^2
                  -\left(\frac{\nu_t}{\sigma_\nu}\right)^2\right].
$$

$M_t$는 soft spectral 안정성 점수일 뿐 의식 점수가 아니다. 보고용 numerical
rank는 float64 eigenvalue에 대해
$r_\eta(G)=\#\{k:\mu_k>10^{-10}\mu_1\}$로 따로 계산하며 $c_G$나 $q_t$에
사용하지 않는다. CE predictor는
기준식에 정확히 네 특징 $(q_t,\nu_t,\kappa_t,M_t)$를 더한다.

$$
\widehat b^{\rm CE}_{t+h}
=\widehat b^{\rm AR}_{t+h}
+\gamma_q q_t+\gamma_\nu\nu_t+\gamma_\kappa\kappa_t+\gamma_M M_t.
$$

## 5. MEASUREMENT_MODEL

- primary neural field: `heatDataMS.mat::Ratio2`, shape $N\times T$;
- matched nuisance field: `R2`, 동일 shape와 timebase;
- clock: `hasPointsTime`, neural volume clock;
- primary output: `behavior.v` at $h=6$ volumes, 약 0.99 s;
- secondary outputs: `behavior.pc1_2[:,0]`, `behavior.pc1_2[:,1]` at the same horizon;
- `behavior.ethogram`은 label 의미가 source-locked되지 않았으므로 endpoint로 쓰지 않는다;
- `acorr`, `cgIdx`, `XYZcoord`는 structural edge·cell identity로 사용하지 않는다.

각 recording의 chronological 첫 60%를 `recording-local calibration prefix`로
정의하고 그 구간에서만 neuron별 finite fraction, mean, standard deviation,
$c_G$, $\tau_0$, $\sigma_\kappa$, $\sigma_\nu$를 추정한다. Finite fraction이
0.75 미만이거나 train standard deviation이 $10^{-12}$ 이하인 neuron은 제외하고,
남은 nonfinite 값은 그 neuron의 train mean으로 대체한다. test 값은 어떤
preprocessing·normalization·scale 선택에도 들어가지 않는다.

Recording마다 neuron 수와 identity가 달라 raw-neuron 위치·scale을 다른 animal에서
이식할 수 없다. 고정되는 것은 이 calibration 절차와 threshold이며, validation 및
held-out recording에도 자신의 앞 60%에서 동일한 무감독 변환만 추정한다. 이 prefix의
outcome으로 coefficient·model·ridge·$d$·threshold를 고르지 않는다. 따라서 결과는
zero-shot animal 일반화가 아니라 calibration-prefix가 허용된 temporal generalization이다.

공식 cut volume과 공식 exclusion interval을 적용하고 첫 12 volume을 버린다.
전체 history-to-future interval 안에 $\Delta t\le0$ 또는
$\Delta t>3\operatorname{median}(\Delta t>0)$가 있으면 anchor를 버린다.
Chronological 60/20/20 경계에서 causal window와 미래 target이 한 split 안에
완전히 들어오는 anchor만 쓰고 경계 양쪽 12 volume을 추가 embargo한다.

## 6. DATA_PROVENANCE

Primary source는 Hallinen et al., *eLife* 2021, DOI
`10.7554/eLife.66135`와 public OSF node `dpr3h`다. 계약 시점의 official OSF API
receipt는 `artifacts/osf-input-prereg.json`에 고정한다. OSF node의 license field는
`null`이므로 raw data를 commit·재배포하지 않고 이 검증을 위한 local analysis와
인용만 수행한다.

| 역할 | OSF file ID | official download | bytes | required SHA-256 |
|---|---|---|---:|---|
| GCaMP, 4 recordings; archive name AML310, internal root AKS297.51 | `5fe26e73c05e2d009b1cec0f` | `https://osf.io/download/evhrg/` | 348,444,164 | `144126ee9a49d311c3393deea434e1a0963d55de35318e25d98d48f9c175250a` |
| GCaMP, 7 recordings | `5fe27e4066e53500b4aa8f03` | `https://osf.io/download/v8huy/` | 1,218,075,251 | `6b71a6ba1a5d2f1ef3bf9661e845e1e52634bae217fc0c2630a83fca07daed63` |
| GFP nuisance control, 11 recordings | `5fe27db666e53500b3aa6b38` | `https://osf.io/download/hsg2y/` | 1,409,801,111 | `588d7666f4e8afebad1ab9b8483244a6de0303251d862425522c2b8dd78bbd82` |

예전 tracked manifest의 AML32 direct URL은 잘못 기록됐고 official API가
`v8huy`를 가리킨다. 이번 run은 위 표만 사용한다. Fresh download의 bytes와
SHA-256이 모두 맞지 않으면 `INPUT_PROVENANCE_STOP`이고 수치 endpoint를 열지 않는다.
Raw archives와 extracted MAT는 gitignored `data/external/`에만 두고 stage/commit하지
않는다.

계약 전 참고한 이전 read-only input audit은
`C:/dev/ce/ce-runs/_workspace/ce/_archive/cloudcell-real-brain-metric-routing-20260820/artifacts/cloudcell-input-audit.md`,
SHA-256 `89f64b1a892981c9c6574802dcd73559786748e6c5a617e12e45df96c1d58b81`다.
이는 schema와 split 가능성을 알리는 선행 영수증이지 이번 endpoint 결과가 아니다.

## 7. DATA_SPLIT

GCaMP outer split은 recording ID로 다음처럼 동결한다.

| 역할 | recordings |
|---|---|
| train 7 | `BrainScanner20200130_105254`, `BrainScanner20200130_110803`, `BrainScanner20170424_105620`, `BrainScanner20170610_105634`, `BrainScanner20170613_134800`, `BrainScanner20180709_100433`, `BrainScanner20200309_151024` |
| validation 2 | `BrainScanner20200310_141211`, `BrainScanner20200309_153839` |
| within-run held-out 2 | `BrainScanner20200310_142022`, `BrainScanner20200309_162140` |

각 validation/held-out 묶음에는 AKS/AML310 한 기록과 AML32 한 기록이 있다.
GFP control의 동결 split은 train
`BrainScanner20200116_145254`, `BrainScanner20200116_152636`,
`BrainScanner20200204_102136`, `BrainScanner20200310_153952`,
`BrainScanner20200311_100140`, `BrainScanner20200929_140030`,
`BrainScanner20200929_143439`; validation
`BrainScanner20210503_122703`, `BrainScanner20210503_135244`; held-out
`BrainScanner20210503_151831`, `BrainScanner20210503_154404`다. 이번 식은 이
데이터에 처음 적용되지만 OSF corpus는 과거 다른
알고리즘의 개발에 노출됐다. 따라서 `within-run held-out`은 독립 외부 confirmation이
아니며 향후 WormID/DANDI 또는 IBL replication을 대체하지 않는다.

모델 coefficient는 outer-train recordings의 chronological 첫 60% anchor만으로
fit한다. Ridge strength와 fixed-d control은 outer-validation recordings의 가운데
20%에서 한 번 선택한다. 모든 선택 후 source·config hash를 동결한 뒤 outer-held-out
recordings의 마지막 20%를 한 번만 score한다. Semi-synthetic 주입과 null calibration은
outer-train 첫 60%만 사용한다.

모델 입력의 공통 scale은 별도로 잠근다. Behavior lag, target 및 각 model family의
네 derived feature column은 outer-train recordings의 calibration-prefix anchor를
pooling해 얻은 mean과 standard deviation으로만 표준화하고 validation/held-out에는
그 값을 그대로 적용한다. 어느 필수 column의 train scale이 $10^{-12}$ 이하이거나
nonfinite이면 해당 run은 model을 축소하지 않고 abstain한다.

## 8. 뇌 실데이터 전 검증 순서

실제 calcium endpoint를 열기 전에 다음 순서로 통과해야 한다.

### L0-A analytic/property gate

1. $G\succeq0$, $0\preceq S_\lambda\preceq I$;
2. $0\le d_{\rm eff}\le\operatorname{rank}G$;
3. $\lambda_1<\lambda_2$이면 $d_{\rm eff}(\lambda_1)\ge d_{\rm eff}(\lambda_2)$;
4. orthogonal rechart $Q$에서 $d_{\rm eff}(QGQ^{\mathsf T})=d_{\rm eff}(G)$;
5. $A_{\lambda,\epsilon}\succ0$ for $\epsilon=10^{-3}$;
6. zero, nonfinite, negative-spectrum input은 fail-closed 또는 명시적 abstain;
7. 모든 exponential·normalization 인자가 무차원.

Float64 relative error boundary는 $10^{-10}$이다.

### L0-B synthetic recovery gate

관측 dimension 12, causal window 96, 32 frozen seeds에서 eigenvalue가 부드럽게
감쇠하고 유효 자유도가 연속적으로 변하는 Gaussian process를 만든다. Truth는 latent
neural dimension이 아니라 sampling·convolution·noise를 지난 관측-level 생성
covariance의 같은 resolvent trace다. Estimated-vs-truth Spearman correlation의 seed
median이 0.90 이상, 5th percentile이 0.75 이상이고 normalized MAE median이 0.15
이하여야 한다. Pure zero, stationary isotropic full-rank, hard rank jump, rotating basis,
time reversal, 30% neuron dropout, calcium-like exponential convolution을 각각 control로
실행한다. 합성 통과는 apparatus만 검증한다.

### L0-C semi-synthetic gate

Outer-train GCaMP의 phase-randomized background에 random orthogonal latent signal을
주입한다. Injected trace/background trace ratio는 $\{0,0.5,1\}$이고 latent soft
dimension은 2에서 8 사이를 연속적으로 이동한다. Truth는 주입 뒤 관측 covariance의
resolvent trace이고 SNR은 injected trace/background trace다. Ratio 1에서 truth-recovery
Spearman median이 0.75 이상이고 ratio 0보다 커야 하며, no-injection false alarm은
합성 calibration에서 고정한 $|\nu_t|$의 95th-percentile boundary를 넘는 anchor 비율로
정의해 0.01--0.10 사이여야 한다. 이 단계도
생물학적 증거가 아니다.

L0-A 또는 L0-B가 실패하면 실제 endpoint를 열지 않는다. L0-C가 실패하면
`APPARATUS_INVALID_ON_REAL_BACKGROUND`로 끝내며 real predictive score를 열지 않는다.

## 9. OBSERVABLES와 matched controls

Primary observable은 held-out recording별 future velocity $R^2$와 RMSE다. Secondary는
두 posture coefficient의 같은 값이다. Window를 독립 replicate로 세지 않고 recording을
replicate unit으로 둔다. Moving-block bootstrap block length는 60 volume이며 2,000회,
seed `20260823`으로 uncertainty만 보고한다.

각 recording·target에는 모든 model family가 공유하는 한 anchor mask만 만든다. Clock,
gap, split, target, behavior lag, primary/red spectral feature와 모든 fixed-d feature가
모두 finite인 anchor의 교집합을 AR·CE·모든 control에 그대로 적용한다. Model별 row
삭제는 금지한다. Scored block의 common anchor가 100개 미만이거나 어떤 필수 model이
abstain하면 그 recording 전체가 abstain하고 primary empirical gate는 실패한다.
Abstention을 남은 recording pooling으로 보충하지 않는다.

모든 비교 모델은 behavior AR 네 특징에 정확히 네 neural/spectral 특징을 더하고
동일 ridge grid $\{0,0.01,0.1,1,10,100\}$를 쓴다. tie는 더 큰 ridge로 정한다.

1. `CE_SOFT`: $(q,\nu,\kappa,M)$ at $\lambda=1$;
2. `FIXED_D`: $d\in\{2,4,8,16,32,48\}$의 hard projector에서 대응하는 retained
   energy, rate, projector turnover, stability score; validation에서 하나만 선택하며
   tie는 작은 $d$로 정한다;
3. `FIXED_4`: 숫자 4의 사전 가치를 따로 확인하는 고정 대조군;
4. `PARTICIPATION_RATIO`: $(\operatorname{tr}G)^2/\operatorname{tr}(G^2)$와 같은
   자유도의 rate/stability summaries;
5. `RAW_SPECTRAL`: trace, squared trace, top-eigenvalue fraction, spectral entropy;
6. `RED_CHANNEL`: `R2`에 동일한 CE_SOFT pipeline;
7. `PHASE_RANDOMIZED`, `CIRCULAR_BEHAVIOR_SHIFT`, `TIME_REVERSED`: train-only seed
   `20260823`으로 고정한 adverse controls;
8. GFP 11-recording nuisance panel에 동일 pipeline.

## 10. RESIDUAL_RULE, FALSIFIER, MODEL_SELECTION

Primary improvement는 각 held-out recording에서

$$
\Delta R^2_r
=R^2_r(\mathrm{CE\_SOFT})
-\max_{m\in\mathcal C}R^2_r(m),
$$

$\mathcal C=\{\mathrm{AR},\mathrm{FIXED\_D},\mathrm{FIXED\_4},
\mathrm{PARTICIPATION\_RATIO},\mathrm{RAW\_SPECTRAL},\mathrm{RED\_CHANNEL}\}$다.
CE_SOFT의 empirical predictive claim은 velocity에서 두 held-out recording 모두
$\Delta R^2_r>0$이고 RMSE도 더 낮을 때만 통과한다. Secondary posture endpoint는
별도로 보고하며 primary 실패를 구하지 못한다.

다음 중 하나면 해당 해석을 기각한다.

- CE_SOFT가 두 held-out animal 중 하나라도 best matched control을 이기지 못함:
  `SOFT_DIMENSION_INCREMENT_NOT_SUPPORTED`;
- phase-randomized/time-reversed/behavior-shift control이 실제 CE_SOFT와 같거나 우수함:
  `TEMPORAL_ALIGNMENT_NOT_IDENTIFIED`;
- red-channel 또는 GFP median improvement가 GCaMP CE_SOFT와 같거나 큼:
  `MEASUREMENT_ARTIFACT_NOT_EXCLUDED`;
- fixed $d=4$가 validation에서 선택되지 않거나 held-out에서 우세하지 않음:
  `FIXED4_NOT_SUPPORTED`;
- input/schema/time gate 실패: scientific endpoint가 아닌 `INPUT_OR_APPARATUS_STOP`.

두 held-out recording뿐이므로 window-level p-value나 population-wide 일반화를 쓰지
않는다. Bootstrap interval은 time dependence를 완전히 제거하지 못하므로 descriptive
uncertainty다. Free parameter count, usable anchor count, abstention과 exclusion을 모두
보고한다.

## 11. REVISION_TRIGGER

불일치는 D→I→P→C→B→T 순서로 분류한다. 단위·구현·정밀도·convention·baseline을
기각하기 전에는 식을 바꾸지 않는다. 한 판본에서 허용하는 구조 변경은 1건이고 수정은
최대 2회다. $W$, $h$, $\lambda$ grid, split, seed, unit rule, gap rule, model menu,
ridge grid, endpoint, pass boundary를 결과 후 변경하지 않는다. 변경이 필요하면 새 run과
새 confirmation이 필요하다.

## 12. CLAIM_CEILING

- L0-A/B/C 통과만: `BIO_EVIDENCE_L0 / APPARATUS_ONLY`;
- calibration-prefix가 허용된 public real recording의 within-recording temporal
  held-out 통과: 최대
  `BIO_EVIDENCE_L3_DEVELOPMENTAL_HELD_OUT`;
- 과거 corpus 노출과 intervention 부재 때문에 독립 confirmation·L4 기전 동일성은 금지;
- `continuous effective dimension`은 scale-dependent spectral degrees of freedom이며
  noninteger topological/Riemannian manifold dimension이 아님;
- C. elegans 결과를 인간 의식, conscious moment, 해마 index, structural edge,
  causal routing 또는 AGI로 승격하지 않음.

후속 독립 확인은 source-locked WormID/DANDI corpus 또는 exact IBL simultaneous
session에서 같은 동결 operator·scale·control을 재조정 없이 적용해야 한다. 해마 희소
색인은 Norman iEEG 같은 별도 계약에서만 시험한다.
