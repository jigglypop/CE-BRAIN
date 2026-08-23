# BA-SRM7 연구 계약 — source-locked causal measurement와 연속 유효차원 검증

Status: COMPLETE

Date: 2026-08-23

Mode: full

PREDECESSOR: `_workspace/ce/brain-adaptive-effective-dimension-validation-20260823`

CE_RUN: `_workspace/ce/brain-adaptive-effective-dimension-validation-v2-20260823`

## 1. 질문과 판본 경계

BA-SRM6은 무한 history Hilbert 공간과 유한 관측 quotient를 분리하고, 관측
공분산의 resolvent trace를 연속 유효 자유도로 정식화했다. 그러나 primary neural
field를 `Ratio2`로 두고 calibration-prefix finite fraction 0.75를 요구한 입력 규칙은
두 recording에서 eligible neuron 0개를 만들어 endpoint 개봉 전에 중지됐다.

BA-SRM7은 이 실패 뒤 여는 새 개발 판본이다. 허용하는 구조 변경은 하나뿐이다.

> `MEASUREMENT_REVISION_1`: 원저자 archived preprocessing에서 실제 prediction 입력인
> motion-corrected $I$와 timepoint-level majority-missing rule을 source-lock하고,
> 미래 행동을 보지 않는 causalㆍtrain-calibrated 측정 연산과 reliability weighting으로
> 바꾼다.

$W$, $h$, $\lambda$ grid, recording split, seed, endpoint, model menu, ridge grid,
pass boundary는 BA-SRM6에서 바꾸지 않는다. 이번 규칙은 BA-SRM6의 입력 missingness를
본 뒤 제안됐으므로 결과가 좋아도 독립 확인이 아니라 developmental evidence다.
BA-SRM6의 neuron별 0.75 `Ratio2` rule은 삭제하지 않고 matched sensitivity로 남긴다.

시험 질문은 다음 세 가지다.

1. `[조건부 정리 후보]` 관측 PSD operator의 resolvent trace는 정수가 아닌 연속
   유효 자유도를 주며, 무한차원에서는 trace-class 조건 아래 유한한가.
2. `[산출 후보]` causal measurementㆍdropoutㆍnoise가 있는 정답-known 합성 및
   real-background 주입에서 같은 observed-level quantity를 사전 오차 안에 회복하는가.
3. `[예측]` source-locked public *C. elegans* calcium에서 네 soft spectral feature가
   같은 정보ㆍ용량의 대조군보다 held-out future locomotion 예측에 증분값을 갖는가.

의식, 해마 index, synaptic edge, causal routing, 인간 또는 AGI는 이 데이터의
시험 대상이 아니다.

## 2. PREDECESSOR_EVIDENCE

| artifact | SHA-256 | 상태 | 보존하는 좁은 주장 | 재사용 금지 |
|---|---|---|---|---|
| BA-SRM6 `12-routes.md` | `75f8cc7607afbdd9269da643239c499a7af632df6471a75ce2c8d951ca848c40` | COMPLETE | basis-fixed observed quotient, generalized reference metric, directed dynamics는 서로 다른 경로 | covariance를 directed edge로 해석 |
| BA-SRM6 `31-validation.md` | `c35b7aa144cb7e88ac794bdb70ef6d763a734be92bc4bb700e2a74b43666267a` | `INPUT_CONTRACT_STOP` | archiveㆍschemaㆍsplitㆍhorizon PASS, Ratio2 unit viability FAIL | score 0 또는 생물학적 FAIL로 재해석 |
| BA-SRM6 `40-final-report.md` | `e7495bc4a308d2f4e516960ce09f04fd6923864db2bb4ce055ee4670fe2e8424` | `FORMALIZATION_COMPLETE / REAL_ENDPOINT_UNOPENED` | resolvent 유효차원과 실뇌 전 L0 검증 사다리 | 미실행 $R^2$를 양성ㆍ음성 결과로 기입 |
| BA-SRM6 input receipt | `52e804ff910bcee5dfb431dc193016c014bf6262a0055d7960795da1c74e7caf` | STOP | 두 실패 recording의 Ratio2 max finite fraction 0.6546448, 0.6309922 | 같은 판본에서 threshold 하향 |
| brain route ledger | `c888990b2045a5ca00683da79c2de8ddea23a81bd028bbf37da7e6797313472a` | ACTIVE | BA-SRM6은 입력 계약 STOP이고 후속 source-lock 필요 | 의식ㆍ해마ㆍAGI 승격 |

BA-SRM4의 hard rank 4는 계속 discovery control일 뿐 prior가 아니다. BA-SRM5의
loop-to-4 no-go와 infinite-to-4 lossless compression no-go도 그대로 유지한다.

## 3. 후보 선택과 기각 경로

| 순위 | 후보 | 선택 판정 | 독립 falsifier |
|---:|---|---|---|
| 1 | source-rooted causal $I$ + reliability-weighted soft spectrum | SELECTED | mask-only, red, GFP, fixed-$d$, time reversal, phase randomization, behavior shift |
| 2 | archived symmetric `I_smooth_interp_crop_noncontig` 그대로 사용 | DIAGNOSTIC ONLY | centered Gaussian filter가 $t$ 뒤 신호를 읽으므로 $t+h$ causal prediction의 primary로 금지 |
| 3 | `Ratio2` threshold를 0.60으로 하향 | REJECTED | BA-SRM6 input을 본 뒤 정한 outcome-informed cutoff이고 source code에 근거 없음 |
| 4 | pairwise-complete covariance | REJECTED | 일반적으로 PSD가 아니어서 resolvent metric의 정의역을 깨뜨림 |
| 5 | red `R2` 또는 GFP로 primary 대체 | REJECTED | nuisance control을 endpoint로 바꾸는 것 |
| 6 | 실패 recording 삭제 | REJECTED | splitㆍ포함 기준의 사후 변경 |

선택 경로도 source code의 생물학적 동일성을 주장하지 않는다. archived code의
photobleachingㆍred/green decorrelationㆍmissingness convention을 측정 출발점으로 쓰고,
future-prediction leakage를 막기 위한 causal modification을 명시적 분석자 선택으로 둔다.

## 4. BIO_STARTING_MECHANISM

숨은 신경활동 $a_i(t)$는 calcium indicator, motion, photobleaching, red/green gain과
noise를 거쳐 raw channels로 관측된다.

$$
\begin{aligned}
R_{i,t}^{\rm raw}&=\mathcal R_i[a_i,m_t,p_t]+\epsilon^R_{i,t},\\
G_{i,t}^{\rm raw}&=\mathcal G_i[(k_i*a_i)(t),m_t,p_t]+\epsilon^G_{i,t}.
\end{aligned}
$$

이 역문제는 public fluorescence만으로 식별되지 않는다. 따라서 spike, membrane
voltage, synaptic current 또는 anatomical edge를 복원했다고 쓰지 않는다.

행동 기준식은 BA-SRM6과 같은 네 lag ridge AR이다.

$$
\widehat b^{\rm AR}_{t+h}
=\alpha+\sum_{\ell\in\{0,1,3,6\}}\beta_\ell b_{t-\ell},
\qquad h=6\ \text{volumes}.
$$

## 5. 무한 history 공간과 edge operator의 형식화

각 관측 unit $i$의 causal history를

$$
\mathcal H_i=L^2\!\left(( -\infty,0],
e^{2s/\tau_h}\frac{ds}{\tau_h};\mathbb R^{p_i}\right),
\qquad
\mathcal H=\bigoplus_{i=1}^{N}\mathcal H_i
$$

에 둔다. $h_{i,t}(s)$는 $s\le0$인 과거 입력ㆍ활동ㆍ측정 상태다. $\mathcal H$는
유한 $N$에서도 무한차원이다. $h_{i,t}$의 서로 다른 물리량 성분은 각각 사전 고정한
reference scale로 나눈 무차원 coordinate이고 $\tau_h$만 시간 단위를 갖는다.
edge는 스칼라 $W_{ij}$가 아니라 bounded causal
Volterra operator 후보

$$
(K_{ij}h_i)(s)=\int_{-\infty}^{s}k_{ij}(s,u;\xi_{ij,t})h_i(u)\,du
$$

로 쓴다. $\xi_{ij,t}$는 delay, efficacy, plastic state, neuromodulatory context 같은
edge state다. 표시한 적분만으로 boundedness가 따라오지는 않는다. 각 고정 $\xi$에서

$$
\int_{-\infty}^{0}\int_{-\infty}^{s}
\|k_{ij}(s,u;\xi)\|_F^2e^{2(s-u)/\tau_h}\,du\,ds<\infty
$$

인 weighted Hilbert--Schmidt 조건을 충분조건으로 가정한다. $K_{ij}(\xi)$는 고정
$\xi$에서 $h$에 대해 bounded linear이고 $\xi\mapsto K_{ij}(\xi)$의 연속성은 별도
가정이다. 유한 길이 directed loop $\gamma=(i_1,\ldots,i_m,i_1)$의 return operator는

$$
L_\gamma=K_{i_mi_1}K_{i_{m-1}i_m}\cdots K_{i_1i_2}
$$

다. 이 정의는 loop가 존재함을 표현할 뿐 rank 4, 의식 또는 해마 주소를 산출하지
않는다. 위 조건 아래 $L_\gamma$는 bounded operator의 유한 합성이므로 bounded다.
이번 자료는 $K_{ij}$나 $L_\gamma$를 식별하지 않는다.

강한 Riemann metric 후보는 $x\in\mathcal H$마다 bounded self-adjoint operator
$\mathcal A_x$가 존재해

$$
g_x(u,v)=\langle u,\mathcal A_xv\rangle_{\mathcal H},
\qquad
m\|u\|^2\le g_x(u,u)\le M\|u\|^2
$$

를 만족하고 $x\mapsto\mathcal A_x$가 operator norm에서 매끄러운 경우에만 쓴다.
이것은 형식 조건이며 아래 calcium operator가 이를 입증하지 않는다.

## 6. MEASUREMENT_MODEL — 이번 판본의 단일 구조 변경

### 6.1 source lock

원저자 code는 `leiferlab/PredictionCode` revision
`ca59416112a9c10a8d6a3179092a7d3c888bcd4e`로 고정한다.
`utility/data_handler.py` SHA-256은
`69c2ff90f1aa98a04e5b4b89c7e2319b176db0dfd1a012c9b6eff54c5d6b89bd`,
`utility/get_all_recordings.py`는
`b26d0d0d9c05c2ebc3123cbdde23429225fa0d20265977ef6e09dacee488a863`다.
그 predictor는 `Ratio2`가 아니라 `I_smooth_interp_crop_noncontig`를 쓴다.

### 6.2 train-calibrated causal signal

원저자의 raw-channel 단계와 같은 변수 `rRaw`, `gRaw`, `rPhotoCorr`, `gPhotoCorr`를
쓴다. 다만 parameter fit은 recording-local first-60% calibration prefix만 읽는다.
순환 정의를 피하기 위해 prefix를 둘로 나눈다. `raw calibration prefix`는 official
cut과 manual exclusion을 적용한 raw clock sequence에서 majority-missing rule을 적용하기
전 첫 $\lfloor0.60T_{\rm raw}\rfloor$개다. photobleaching과 red→green regression은
이 raw prefix에서만 fit한다. 그 fit으로 valid map을 만든 뒤 retained sequence의 첫
$\lfloor0.60T_{\rm valid}\rfloor$개를 `processed calibration prefix`라 하고, neuron
eligibilityㆍ$D_r$ㆍmeanㆍstandard deviationㆍ$c_G$와 feature RMS는 여기서 fit한다.

1. raw $R,G$를 `hasPointsTime` 길이와 official cut volume으로 자른다.
2. prefix에서만 12.6 s median-filtered exponential photobleaching curve를 fit하고
   전체 시간에 외삽한다. source와 같은 6 volume/s, odd window 77을 쓴다. train에서
   exponential fit이 flat보다 나쁘면 그 neuron/channel은 identity correction을 쓴다.
   bounded nonlinear fit이 exceptionㆍnonfinite curve를 내도 한 번의 identity fallback만
   쓰고 recording별 count를 입력 영수증에 남긴다. 다른 초기값 탐색이나 결과 후 refit은
   금지한다.
3. `rPhotoCorr` 또는 `gPhotoCorr`가 NaN인 동일 위치를 각각 NaN으로 만들고 source의
   `close_nan_holes` morphology를 적용한다. `flagged_volumes`가 있으면 그대로 NaN 처리한다.
4. 각 neuron에서 prefix finite pair만으로

$$
(\widehat\beta_i,\widehat c_i)
=\arg\min_{\beta,c}\sum_{t\in\mathrm{cal},\,m_{i,t}=1}
\left(G_{i,t}-\beta R_{i,t}-c\right)^2
$$

   를 적합하고 $I_{i,t}=G_{i,t}-\widehat\beta_iR_{i,t}-\widehat c_i$를 만든다.
5. pre-interpolation mask는 $m_{i,t}=\mathbf1\{I_{i,t}\in\mathbb R\}$다. source와
   같이 $N^{-1}\sum_i(1-m_{i,t})<0.5$인 timepoint만 허용한다.
6. future leakage를 막기 위해 centered Gaussian 대신 $\sigma=5$ volume,
   $L=20$ volume인 causal normalized convolution을 쓴다.

$$
\bar I_{i,t}=
\frac{\sum_{\ell=0}^{L}e^{-\ell^2/(2\sigma^2)}m_{i,t-\ell}I_{i,t-\ell}}
     {\sum_{\ell=0}^{L}e^{-\ell^2/(2\sigma^2)}m_{i,t-\ell}}.
$$

분모가 0이면 그 sample은 nonfinite다. causal filter, prefix fit, standardization 중 어느
단계도 $t$ 뒤 neural value 또는 future behavior를 읽지 않는다. 원저자의 symmetric
Gaussian interpolation은 source-reproduction diagnostic으로만 계산하고 모델 점수에는
넣지 않는다.

여기서 `causal`은 calibration prefix가 끝난 뒤의 validationㆍheld-out scored anchor에
대해, current/past neural sample과 이미 동결된 prefix parameter만 사용한다는 뜻이다.
prefix 전체로 parameter를 맞추므로 prefix 내부 anchor를 online-causal 성능으로
채점하지 않는다. outer-train prefix는 coefficient fit용 calibration sample일 뿐이다.

각 recording의 prefix에서 raw $I$ finite sample이 최소 $W=60$개이고 causal
$\bar I$의 prefix standard deviation이 $10^{-12}$보다 큰 neuron만 남긴다. 이는
fraction cutoff가 아니라 정의된 covariance와 scale을 계산하기 위한 최소 표본 조건이다.
남은 neuron의 prefix finite fraction을 $\pi_i$라 하고

$$
D_r=\operatorname{diag}(\sqrt{\pi_1},\ldots,\sqrt{\pi_N})
$$

를 recording마다 한 번 고정한다. $\bar I$의 nonfinite는 그 neuron의 prefix mean으로
대체하고 prefix meanㆍstandard deviation으로 $z_{i,t}$를 만든다. validationㆍheld-out
recording도 자기 first-60% neural prefix로 같은 무감독 변환만 보정하며 behavior,
ridge, model family 또는 결과를 보지 않는다.

### 6.3 clock와 split leakage gate

official exclusion interval과 cut volume을 적용한다. retained time sequence에서
첫 12 volume을 버리고, history 시작부터 target까지 $\Delta t\le0$ 또는
$\Delta t>3\operatorname{median}(\Delta t>0)$인 anchor를 버린다. 60/20/20 split
경계를 window 또는 target이 가로지르면 버리고 양쪽 12 volume을 embargo한다.
한 source timepoint는 인접 gap 양쪽 anchor에 중복 복구되지 않는다.

## 7. CE_DELTA — reliability-weighted observed operator

길이 $W=60$ causal window의 표준화 신호를
$Z_t=[z_{t-W+1},\ldots,z_t]$라 하고
$H=I-W^{-1}\mathbf1\mathbf1^{\mathsf T}$라 한다. primary PSD operator는

$$
G_t=\frac1{W-1}D_rZ_tHZ_t^{\mathsf T}D_r\succeq0.
$$

$D_r$는 고정된 train-only reliability weight다. 이 식은 missingness에 대한 unbiased
latent covariance 추정량이라는 주장을 하지 않는다. source-rooted interpolated signal의
신뢰도가 낮은 channel을 고정적으로 약화한 **observed reliability-weighted covariance**다.

$$
r_{\star,r}=\min(N_{{\rm kept},r},W-1),
\qquad
c_{G,r}=\operatorname{median}_{t\in\mathrm{cal}(r)}
\frac{\operatorname{tr}G_{r,t}}{r_{\star,r}}.
$$

$c_{G,r}$가 nonfinite 또는 $\le10^{-12}$이면 recording $r$을 abstain한다. 이후
한 recording 안의 식에서는 표기를 줄이기 위해 $r_{\star,r},c_{G,r}$의 subscript
$r$을 생략한다.

$$
\widetilde G_t=G_t/c_G,
\qquad
S_{t,\lambda}=\widetilde G_t(\widetilde G_t+\lambda I)^{-1},
$$

$$
d_{\mathrm{eff}}(t;\lambda)=\operatorname{tr}S_{t,\lambda},
\qquad q_t=d_{\mathrm{eff}}(t;1)/r_\star.
$$

primary $\lambda=1$이고 sensitivity grid는 $\{0.1,0.3,1,3,10\}$다. grid endpoint를
보고 늘리거나 최선 $\lambda$를 고르지 않는다. observed inner product는

$$
A_{t,\lambda}=10^{-3}I+(1-10^{-3})S_{t,\lambda}
$$

로 정의하지만 predictor에는 넣지 않고 PSDㆍconditioning property만 검사한다.

동일 recording의 고정 neuron basis에서

$$
\kappa_t=\frac{\|S_{t,1}-S_{t-1,1}\|_F}{\sqrt{r_\star}},
\qquad
\nu_t=\frac{q_t-q_{t-1}}{(t_t-t_{t-1})/\tau_0},
$$

$$
\mathcal M_t=\exp\!\left[-(\kappa_t/\sigma_\kappa)^2
                         -(\nu_t/\sigma_\nu)^2\right].
$$

$\tau_0$는 recording prefix의 median positive clock step이고,
$\sigma_\kappa,\sigma_\nu$는 같은 recording prefix anchor의 RMS다. 각 scale이
nonfinite 또는 $\le10^{-12}$이면 그 recording을 abstain한다. $\mathcal M_t$는 의식 점수가 아니라
spectral-stability feature다.

CE predictor는 AR에 정확히 네 scalar를 더한다.

$$
\widehat b^{\rm CE}_{t+h}=\widehat b^{\rm AR}_{t+h}
+\gamma_q q_t+\gamma_\nu\nu_t+\gamma_\kappa\kappa_t+\gamma_M \mathcal M_t.
$$

무차원 규칙은 다음처럼 동결한다. $z,D,H,G/c_G,S,q,\kappa,\nu$는 무차원이다.
causal Gaussian의 $\ell/\sigma$는 둘 다 volume count의 비이고, photobleaching
$\exp(-bt)$에서는 $b$가 inverse time, $t$가 time이다. $\Delta t/\tau_0$,
$\kappa/\sigma_\kappa$, $\nu/\sigma_\nu$도 무차원이다. 따라서 $\mathcal M$의
exponential과 spectral entropy의 $\log\rho_k$만 transcendental core에 들어간다.
무차원 통과는 물리적 정당성이나 생물학적 동일성을 뜻하지 않는다.

## 8. DATA_PROVENANCE와 split

Primary source는 Hallinen et al., *eLife* 2021,
DOI `10.7554/eLife.66135`; OSF `10.17605/OSF.IO/DPR3H`; code revision은 §6.1이다.
OSF license field가 null이므로 rawㆍderived recordings와 upstream source copy는
gitignored `data/external/`에서 local analysis만 하고 commitㆍ재배포하지 않는다.

BA-SRM6에서 byte-lock한 세 archive를 그대로 재사용한다.

| 역할 | bytes | SHA-256 |
|---|---:|---|
| AML310/AKS297.51 GCaMP | 348,444,164 | `144126ee9a49d311c3393deea434e1a0963d55de35318e25d98d48f9c175250a` |
| AML32 GCaMP | 1,218,075,251 | `6b71a6ba1a5d2f1ef3bf9661e845e1e52634bae217fc0c2630a83fca07daed63` |
| AML18 GFP | 1,409,801,111 | `588d7666f4e8afebad1ab9b8483244a6de0303251d862425522c2b8dd78bbd82` |

GCaMP outer split은 BA-SRM6과 동일하다.

| 역할 | recordings |
|---|---|
| train 7 | `BrainScanner20200130_105254`, `BrainScanner20200130_110803`, `BrainScanner20170424_105620`, `BrainScanner20170610_105634`, `BrainScanner20170613_134800`, `BrainScanner20180709_100433`, `BrainScanner20200309_151024` |
| validation 2 | `BrainScanner20200310_141211`, `BrainScanner20200309_153839` |
| held-out 2 | `BrainScanner20200310_142022`, `BrainScanner20200309_162140` |

GFP split도 동일하다: train
`BrainScanner20200116_145254`, `BrainScanner20200116_152636`,
`BrainScanner20200204_102136`, `BrainScanner20200310_153952`,
`BrainScanner20200311_100140`, `BrainScanner20200929_140030`,
`BrainScanner20200929_143439`; validation
`BrainScanner20210503_122703`, `BrainScanner20210503_135244`; held-out
`BrainScanner20210503_151831`, `BrainScanner20210503_154404`다.

모델 coefficient는 outer-train recording의 first-60% anchors로 fit한다. ridge와
fixed-$d$는 outer-validation recording의 middle-20%에서 선택한다. 선택 규칙을 적용한
뒤 outer-held-out last-20%를 조건 없이 한 번 연다. validation 성능이 나쁘다는 이유로
test 개봉을 취소하지 않는다. behavior lagㆍtargetㆍ각 model family 네 feature의 공통
meanㆍscale은 outer-train calibration anchors에서만 fit한다.

### 8.1 staged input lock

behavior target을 읽기 전에 source/code/archive hash, 22 MAT raw schema, cutㆍexclusion,
clock monotonicity, raw/processed prefix, primaryㆍred causal eligibility, $r_{\star,r}$,
$\mathcal D$와 behavior-independent feature-common anchor ID를
`artifacts/neural-input-lock.json`에 기록하고 SHA-256을 동결한다. 이 lock이 모든
recording에서 schemaㆍeligibility와 split별 최소 100 feature-common anchor를 통과한 뒤에만
`behavior` struct를 load한다. 그 다음 단계도 field nameㆍshapeㆍclock-length alignment만
기록하고 value summary, correlation, fit 또는 score는 계산하지 않는다.

최종 `artifacts/input-audit.json`에는 `neural_lock_created_before_behavior=true`,
`behavior_values_scored=false`, `model_fit=false`, `validation_opened=false`,
`test_opened=false`를 명시한다. 어느 recording이 실패하면
`SOURCE_ROOTED_INPUT_STOP`으로 닫고 thresholdㆍsplitㆍrecording을 바꾸지 않는다.

## 9. 뇌 실데이터 endpoint 전 검증

### L0-A analytic/property gate

Float64 상대오차 $10^{-10}$에서 다음을 모두 요구한다.

1. $G\succeq0$, $0\preceq S_\lambda\preceq I$;
2. $0\le d_{\rm eff}\le\operatorname{rank}G$와 $\lambda$ 단조 감소;
3. 이미 구성한 $G$를 $QGQ^{\mathsf T}$로 바꾸는 orthogonal rechart에서만
   $d_{\rm eff}$ 불변; coordinate-wise missingness로 $D_r$를 다시 만드는 raw-data
   pipeline 전체의 chart invariance와 일반 $GL(N)$ 불변은 주장하지 않음;
4. $A\succ0$, condition number $\le10^3$;
5. zero, nonfinite, negative-spectrum, insufficient-prefix input의 명시적 abstain;
6. causal convolution의 출력이 입력의 같은 시점과 과거에만 의존함;
7. pairwise-complete non-PSD adverse matrix가 core에 들어오면 fail-closed;
8. expㆍscaleㆍrate의 모든 인자가 무차원.

### L0-B synthetic recovery gate

관측 channel 12, $W=96$, 길이 $T=768$, frozen seeds
$20260823,\ldots,20260854$를 쓴다. seed마다 표준정규 행렬에서 만든 skew-symmetric
$B_s$를 spectral norm 1로 정규화하고

$$
Q_t=\exp\!\left[0.35\sin(2\pi t/256)B_s\right],
\qquad
\mu_k(t)=\exp\!\left[-\frac{k-1}{3.5+2\sin(2\pi t/384)}\right]
$$

로 smooth covariance를 만든다. $x_t=Q_t\operatorname{diag}(\sqrt{\mu_k(t)})\xi_t$,
$\xi_t\sim\mathcal N(0,I)$이고 causal calcium trace는

$$
y_t=(1-a)x_t+ay_{t-1},\qquad a=e^{-1/6},\quad y_0=x_0
$$

다. 각 channel에는 독립적으로 길이 $\lfloor0.30T\rfloor$인 dropout block 하나를
두며 시작점은 같은 seed에서 uniform integer로 뽑는다. noise 표준편차는 clean
$y$를 channel×time으로 demean한 pooled RMS의 $1/4$로 고정해
`signal RMS / noise SD = 4`로 정의한다.

dropout mask에서 얻은 fixed $D_r$를 clean truth와 noisy estimate에 똑같이 쓴다.
truth의 meanㆍstandard deviation과 $c_G$는 clean first-60%에서, estimate의 값들은
noisy/dropout first-60%에서 각각 fit한다. truth는 숨은 neural dimension이 아니라
noiseㆍdropout 전 **clean observed calcium trace**에 fixed observed reliability를 적용한
rolling resolvent trace다. seed $s$의 eligible anchor $A_s$에서

$$
\operatorname{NMAE}_s=
\frac1{|A_s|r_\star}\sum_{t\in A_s}
\left|\widehat d_{{\rm eff},t}-d_{{\rm eff},t}^{\rm truth}\right|
$$

로 오차를 정의한다.

dynamic rotating case의 estimated-vs-truth Spearman seed median $\ge0.90$,
NumPy `quantile(method="linear")` 5th percentile $\ge0.75$,
normalized MAE median $\le0.15$를 요구한다. zero, stationary isotropic full-rank,
hard-rank jump, rotating basis, time reversal, 30% dropout과 causal convolution을 각각
고정 control로 실행한다. pure zero는 `ABSTAIN_EXPECTED`여야 한다. stationary isotropic
control은 $Q_t=I,\mu_k(t)=1$이고 constant truth 때문에 Spearman gate에서 제외한다.
median normalized absolute error $\le0.15$와 $\operatorname{sd}(q_t)\le0.05$만 요구한다.
rotation-only control은 $\mu_k=\exp[-(k-1)/3.5]$를 고정하고 위 dynamic $Q_t$만 쓴다.
hard-rank jump는 $Q_t=I$이고 $t<384$에서 $\mu_{1:2}=1$, $t\ge384$에서
$\mu_{1:8}=1$, 나머지는 0으로 두며 dynamic case와 같은 convolutionㆍnoiseㆍdropout을
적용한다. $|\nu|$ 최대 anchor가 $[384-W,384+W]$ 안에 있어야 한다.

time reversal property는 original dynamic clean trace에서 고정한 meanㆍscaleㆍ$D_r,c_G$를
그대로 둔 채 $\check y_t=y_{T+1-t}$로 뒤집는다. 1-based rolling anchor에서

$$
d_{\rm eff}^{\check y}(t)=d_{\rm eff}^{y}(T-t+W),
\qquad t=W,\ldots,T
$$

를 상대오차 $10^{-10}$ 안에서 요구한다. 이 control에는 noiseㆍdropout을 넣지 않는다.
통과는 apparatus evidence만 뜻한다.

### L0-C real-background semi-synthetic gate

outer-train GCaMP first-60%의 causal $I$를 gap rule로 나눈 contiguous segment마다
channel별 phase randomize한 background $B$로 만든다. 각 segment의 DC와 짝수 길이의
Nyquist coefficient를 보존하고 positive Fourier frequency마다 독립
$\mathrm{Uniform}(0,2\pi)$ phase를 준 뒤 Hermitian symmetry를 복원한다. seed는
SHA-256(`20260823|recording_id|phase`)의 앞 64 bit다.

각 recording에서 injection seed로 생성한 Gaussian matrix의 reduced QR로 만든
$N\times8$ orthonormal $Q$, 그리고 같은 seed의
$\xi_t\sim\mathcal N(0,I_8)$와

$$
d(t)=5+3\sin(2\pi t/T_r),\qquad
\mu_k(t)=\left[1+\exp\left((k-d(t))/0.35\right)\right]^{-1}
$$

를 써 $U_t=Q\operatorname{diag}(\sqrt{\mu_k(t)})\xi_t$를 생성한다. segment별ㆍchannel별
time mean을 제거한 pooled channel×time RMS를 $\operatorname{RMS}(\cdot)$로 정의하고

$$
Y^{(\rho)}=B+\sqrt\rho\,
\frac{\operatorname{RMS}(B)}{\operatorname{RMS}(U)}U,
\qquad \rho\in\{0,0.5,1\}
$$

로 injected-to-background **RMS-squared power ratio**를 고정한다. original
pre-interpolation mask에서 고정한 $D_r$를 truth와 estimate에 똑같이 쓴다. truth는
clean $Y^{(\rho)}$ calibration prefix에서 fit한 meanㆍstandard deviation과
$c_{G,r}^{\rm clean}$를 적용한 observed rolling resolvent trace다. estimate는 같은
mask와 $D_r$를 쓰되 transformed trace의 calibration prefix에서 자기 meanㆍstandard
deviationㆍ$c_{G,r}$를 fit한다. ratio 1의 truth-recovery Spearman recording
median이 $\ge0.75$이고 ratio 0 median보다 커야 한다. nonfinite correlation은 0으로 센다.

L0-B dynamic case의 32 seed 모든 eligible anchor에서 NumPy
`quantile(method="linear")`로

$$
\theta_\nu=Q_{0.95}(|\nu_t|)
$$

를 한 번 고정한다. ratio 0인 각 eligible outer-train recording에서 strict
$|\nu_t|>\theta_\nu$인 anchor fraction이 0.01–0.10이어야 한다.

L0-A/B가 실패하면 real recording preprocessing 외의 endpoint를 열지 않는다. L0-C가
실패하면 `APPARATUS_INVALID_ON_REAL_BACKGROUND`로 끝내고 behavior를 읽거나 score하지
않는다.

## 10. OBSERVABLES, matched controls, model selection

Primary neural input은 causal $I$, primary output은 `behavior.v` at $h=6$이다.
Secondary output은 `behavior.pc1_2[:,0:2]`다. primary observable은 held-out
recording별 $R^2$, RMSE와 아래 $\Delta R^2$다. replicate unit은 recording/animal이며
window를 독립 표본으로 세지 않는다. moving-block bootstrap은 block 60, 2,000회,
seed `20260823`으로 descriptive interval만 보고한다.

모든 model은 동일한 common anchor intersection과 AR 네 특징을 쓰고 neural/spectral
특징을 정확히 네 개만 더한다. ridge grid는 $\{0,0.01,0.1,1,10,100\}$다. 각 family와
ridge의 coefficient는 pooled outer-train prefix anchor로 fit하고 두 validation recording의
primary-velocity mean $R^2$가 최대인 ridge를 고른다. tie는 큰 ridge다. `FIXED_D`만
$(d,\mathrm{ridge})$를 함께 고르며 $R^2$ tie는 작은 $d$, 그 뒤 큰 ridge 순이다.
target은 outer-train meanㆍstandard deviation으로 표준화해 fit하고 score 전에 원단위로
되돌린다.

input audit에서 behavior를 읽기 전에

$$
\mathcal D=\{d\in\{2,4,8,16,32,48\}:d<\min_r r_{\star,r}\}
$$

를 모든 GCaMP recording의 channel count로 고정한다. $d\notin\mathcal D$는
`UNAVAILABLE_BY_DESIGN`으로 selection과 common-row에서 제외한다. $4\notin\mathcal D$면
전체 empirical endpoint가 abstain한다. 필수 common-row family는 `AR`, `CE_SOFT`,
`FIXED_D`의 $d\in\mathcal D$, `FIXED_4`,
`PARTICIPATION_RATIO`, `RAW_SPECTRAL`, `CAUSAL_UNWEIGHTED`, `MASK_ONLY`,
`RED_CHANNEL`이다. diagnostic-only `SOURCE_SYMMETRIC`, `RATIO2_075`와 별도 GFP panel은
common-row abstention을 일으키지 않는다. scored block의 common anchor가 100개
미만이거나 필수 family 하나가 abstain하면 recording 전체가 abstain한다.

1. `CE_SOFT`: $(q,\nu,\kappa,\mathcal M)$ at $\lambda=1$;
2. `FIXED_D`: $d\in\{2,4,8,16,32,48\}$ hard projector의 아래 네 특징;
3. `FIXED_4`: 숫자 4의 별도 대조군;
4. `PARTICIPATION_RATIO`: participation ratio와 rate/turnover/stability;
5. `RAW_SPECTRAL`: trace, squared trace, top-eigenvalue fraction, spectral entropy;
6. `CAUSAL_UNWEIGHTED`: $D_r=I$인 soft operator;
7. `MASK_ONLY`: $m$의 centered window covariance에서 만든 같은 네 soft features;
8. `RED_CHANNEL`: causal photobleach-corrected red signal의 같은 네 features;
9. `PHASE_RANDOMIZED`, `CIRCULAR_BEHAVIOR_SHIFT`, `TIME_REVERSED`;
10. GFP 11-recording nuisance panel;
11. `SOURCE_SYMMETRIC`: archived symmetric interpolation의 feature agreement만 보고하며
    causal predictive 경쟁에는 넣지 않는다;
12. `RATIO2_075`: BA-SRM6 eligibility를 그대로 재현하고 abstention만 보고하며 실패
    recording 삭제나 threshold 변경을 하지 않는다.

각 family의 feature map은 다음처럼 고정한다. $\mu_{1,t}\ge\cdots\ge\mu_{N,t}$는
$G_t$의 eigenvalue이고 $\eta_{\rm gap}=10^{-12}$다. $d\in\mathcal D$에서

$$
\frac{\mu_{d,t}-\mu_{d+1,t}}{\max(\mu_{1,t},10^{-12})}\le\eta_{\rm gap}
$$

이면 그 anchor는 `PROJECTOR_UNIDENTIFIED`다. 그 외에는 $P_{d,t}$가 유일하다.

$$
e_{d,t}=\frac{\sum_{k\le d}\mu_{k,t}}{\sum_k\mu_{k,t}},\quad
\dot e_{d,t}=\frac{e_{d,t}-e_{d,t-1}}{(t_t-t_{t-1})/\tau_0},
$$

$$
p_{d,t}=\frac{\|P_{d,t}-P_{d,t-1}\|_F}{\sqrt{2d}},\quad
\mathcal M_{d,t}=\exp[-(p_{d,t}/\sigma_{p,d})^2
                              -(\dot e_{d,t}/\sigma_{e,d})^2].
$$

$\sigma_{p,d},\sigma_{e,d}$는 recording prefix RMS다. `FIXED_D`의 네 특징은
$(e_d,\dot e_d,p_d,\mathcal M_d)$다. `FIXED_4`는 같은 $d=4$ map이다.

`PARTICIPATION_RATIO`는

$$
q^{\rm PR}_t=\frac{(\operatorname{tr}G_t)^2}
{r_\star\operatorname{tr}(G_t^2)},\qquad
\rho_{k,t}=\mu_{k,t}/\operatorname{tr}G_t
$$

와 $q^{\rm PR}$의 time-normalized difference $\Delta q^{\rm PR}_t$,
$\delta^\rho_t=\|\rho_t-\rho_{t-1}\|_2/\sqrt2$,
$\sigma_{\Delta q^{\rm PR}}$, $\sigma_{\rho}$로 각각 나눈 두 변화량의
prefix-RMS normalized exponential을
쓴다. zero denominator는 abstain한다. `RAW_SPECTRAL`은 정확히

$$
\left(\frac{\operatorname{tr}G}{r_\star c_G},
\frac{\operatorname{tr}(G^2)}{r_\star c_G^2},
\frac{\mu_1}{\operatorname{tr}G},
-\frac{\sum_k\rho_k\log\rho_k}{\log r_\star}\right)
$$

이고 $0\log0=0$이다.

`CAUSAL_UNWEIGHTED`는 $D_r=I$로 바꾸고 자기 prefix $c_G,\sigma_\kappa,
\sigma_\nu$를 fit한 $(q,\nu,\kappa,\mathcal M)$다. `MASK_ONLY`는 source majority-rule을
통과한 timepoint의 pre-interpolation binary mask $m_{i,t}$만 사용한다. prefix
$\pi_i$로

$$
z^m_{i,t}=\frac{m_{i,t}-\pi_i}
{\sqrt{\max[\pi_i(1-\pi_i),10^{-6}]}}
$$

를 만들고 $D=I$인 covariance에 같은 soft feature map을 적용한다. neural value는
읽지 않는다. mask covariance의 prefix $c^m_{G,r}\le10^{-12}$이면 primary core의
zero-scale abstain을 적용하지 않고 유효한 AR-equivalent 무정보 대조군으로 네 특징을
정확히 $(0,0,0,0)$으로 둔다. outer-train에서 이 feature column의 variance가 0이어도
standardized all-zero column으로 유지하고 common row를 제거하지 않는다.
`RED_CHANNEL`은 train-prefix photobleach-corrected red $R$의 own finite
mask, 동일 causal convolution, $W$-sample eligibility, reliability $D_r$, standardization과
같은 soft feature map을 쓴다. green이나 behavior를 읽지 않는다.

adverse temporal control은 split과 gap segment 안에서만 변환한다. `PHASE_RANDOMIZED`는
L0-C와 같은 Fourier rule과 SHA-256(`20260823|recording_id|phase-control`) seed로 causal
$I$를 변환한다. `TIME_REVERSED`는 각 contiguous split segment의 causal $I$ 순서를
뒤집는다. `CIRCULAR_BEHAVIOR_SHIFT`는 neural feature를 각 split segment 길이의
$\max(1,\lfloor n/3\rfloor)$만큼 원형 이동해 behavior와 정렬을 깨뜨린다. 세 control은
원 모델과 같은 rowㆍfeature count를 쓰되, matched capacity를 위해 각각 자기
outer-train/validation에서 동일 ridge grid로 ridge를 독립 선택한다. 모든 선택은 test
개봉 전에 끝낸다.

`SOURCE_SYMMETRIC`은 causal signal과 같은 calibration anchors에서 $q,\nu,\kappa,
\mathcal M$의 column별 descriptive Spearman과 normalized MAE만 보고한다. ridge selection,
prediction score, $\Delta R^2$와 falsifier에는 들어가지 않는다.

Primary residual은

$$
\Delta R^2_r=R^2_r(\mathrm{CE\_SOFT})-
\max_{m\in\mathcal C}R^2_r(m),
$$

$$
\mathcal C=\{\mathrm{AR,FIXED\_D,FIXED\_4,PARTICIPATION\_RATIO,
RAW\_SPECTRAL,CAUSAL\_UNWEIGHTED,MASK\_ONLY,RED\_CHANNEL}\}.
$$

두 held-out GCaMP recording 모두 $\Delta R^2_r>0$이고 CE_SOFT RMSE가 best control보다
낮아야만 primary predictive gate가 통과한다. Secondary posture는 primary를 구하지
못한다.

## 11. FALSIFIER와 결과 코드

- L0 실패: `APPARATUS_NOT_VALIDATED`, behavior endpoint 미개봉;
- 새 input rule에서도 recording abstain: `SOURCE_ROOTED_INPUT_STOP`;
- CE_SOFT가 어느 held-out animal에서든 best matched control을 못 이김:
  `SOFT_DIMENSION_INCREMENT_NOT_SUPPORTED`;
- mask-only, red 또는 GFP median improvement가 CE와 같거나 큼:
  `MEASUREMENT_ARTIFACT_NOT_EXCLUDED`;
- phase-randomized, time-reversed 또는 behavior-shift가 CE와 같거나 큼:
  `TEMPORAL_ALIGNMENT_NOT_IDENTIFIED`;
- fixed 4가 validation에서 선택되지 않거나 held-out에서 우세하지 않음:
  `FIXED4_NOT_SUPPORTED`.

artifact comparison의 `improvement`는 정확히 AR 대비 $R^2$ 차이다.

$$
\delta^{\rm GCaMP}_{m}=\operatorname{median}_{r\in\text{two held-out GCaMP}}
[R^2_r(m)-R^2_r(\mathrm{AR})],
$$

$$
\delta^{\rm GFP}_{\rm CE}=\operatorname{median}_{r\in\text{two held-out GFP}}
[R^2_r(\mathrm{CE\_SOFT})-R^2_r(\mathrm{AR})].
$$

$\delta^{\rm GCaMP}_{\rm MASK}$,
$\delta^{\rm GCaMP}_{\rm RED}$ 또는 $\delta^{\rm GFP}_{\rm CE}$ 중 하나라도
$\delta^{\rm GCaMP}_{\rm CE}$ 이상이면 artifact falsifier가 발동한다. temporal adverse
control은 두 held-out GCaMP recording 중 하나에서라도 그 control $R^2$가 원래
CE_SOFT $R^2$ 이상이면 `TEMPORAL_ALIGNMENT_NOT_IDENTIFIED`다.

결과 코드는 동시에 여러 개일 수 있다. adverse control 실패를 나머지 score로 덮지
않는다. 두 held-out animal뿐이므로 window-level p-value와 population 일반화는 금지한다.

## 12. REVISION_TRIGGER와 CLAIM_CEILING

불일치는 D(차원)→I(구현)→P(정밀도)→C(convention)→B(baseline)→T(이론) 순서로
분류한다. 한 판본에서 추가 구조 변경은 금지한다. source operation parity나 명백한
코드 결함만 같은 식ㆍseedㆍthreshold 아래 고칠 수 있고, 역할당 revision은 최대 2회다.
measurement threshold, $W,h,\lambda$, split, seed, model, ridge, endpoint, pass boundary를
결과 후 바꾸려면 새 run과 독립 corpus가 필요하다.

- L0-A/B/C만 통과: `BIO_EVIDENCE_L0 / APPARATUS_ONLY`;
- public recording held-out 통과: 최대
  `BIO_EVIDENCE_L3_DEVELOPMENTAL_HELD_OUT`;
- 이 corpus가 판본 제안에 사용됐으므로 독립 confirmation이 아님;
- $d_{\rm eff}$는 continuous effective degrees of freedom이지 noninteger manifold
  dimension이 아님;
- calcium covariance는 synaptic edgeㆍcausal loopㆍ해마 hashㆍconscious moment를
  식별하지 않음;
- 다음 승격은 source-locked WormID/DANDI 또는 IBL에서 이 operatorㆍscaleㆍcontrol을
  결과 후 retune 없이 외부 재현해야 함;
- 의식과 해마 index는 conscious report/perturbation 또는 hippocampal reinstatement가
  있는 별도 계약으로만 시험함.
