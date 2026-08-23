# BA-SRM8 연구 계약 — 물리시간 mask-aware 유효차원과 다단계 식 선별

Status: COMPLETE

Date: 2026-08-23

Mode: full

PREDECESSOR: `_workspace/ce/brain-adaptive-effective-dimension-validation-v2-20260823`

CE_RUN: `_workspace/ce/brain-physical-time-effective-dimension-funnel-20260823`

## 1. 질문과 구조 변경

BA-SRM7은 source-rooted raw red/green 입력과 causal unit eligibility를 22개 recording
모두에서 구성했지만, retained index의 60-sample window 안에 큰 clock gap이 하나라도
있으면 anchor 전체를 버리는 규칙 때문에 네 recording의 split별 최소 100 anchor
게이트에서 멈췄다. behavior는 열지 않았고 model과 score는 존재하지 않는다.

BA-SRM8이 허용하는 구조 변경은 하나의 묶음이다.

> `PHYSICAL_TIME_MASKED_PSD_1`: majority-bad timepoint를 압축해 hard-gap window를
> 만드는 대신 원래 물리 clock 위에 missingness mask와 비음수 causal weight를 두고,
> weighted PSD covariance와 effective sample size로 관측 정보를 계산한다.

이 변경은 BA-SRM7 neural input을 본 뒤 제안됐다. 따라서 이 corpus에서 성공해도
독립 확인이 아니라 developmental evidence다. behavior를 본 뒤 kernel, threshold,
candidate 또는 split을 바꾸지 않는다.

검증 질문은 다음과 같다.

1. `[조건부 정리 후보]` 비음수 물리시간 weight와 bounded robust map으로 만든 weighted
   covariance는 missingness와 irregular clock 아래에서도 PSD인가.
2. `[산출 후보]` 많은 후보 식 가운데 observed-level truth를 회복하지 못하거나 artifact에
   반응하는 식을 behavior 이전의 싼 gate에서 빠르게 제거할 수 있는가.
3. `[예측]` 살아남은 단 하나의 soft spectral 식이 sealed held-out future locomotion에서
   같은 row와 용량의 최선 대조군보다 증분 예측값을 갖는가.

synaptic edge, directed loop, hippocampal index, consciousness와 AGI는 시험 대상이 아니다.

## 2. PREDECESSOR_EVIDENCE

| artifact | SHA-256 | 보존하는 좁은 결론 | 재사용 금지 |
|---|---|---|---|
| BA-SRM7 `20-audit.md` | `1fa69758ab705028a908c2dff7c8e0f72f1f4b8fe86e41a7141417f1261f4763` | 수학 P0 없음, `SOURCE_ROOTED_INPUT_STOP` | 생물학적 음성으로 해석 |
| BA-SRM7 `31-validation.md` | `8369748ffef0dcfcb77aa694cb3add049985d2726ba622523d752dab3ac081c7` | 22개 unit eligibility PASS, 4개 anchor gate FAIL | 미실행 score를 0으로 기입 |
| BA-SRM7 `40-final-report.md` | `4e3b1be2f9f5dc9cdfdd3323887433c2337ee24b4a73bf86757d762afdd59451` | infinite history와 finite observed quotient의 분리 | loopㆍ의식 해석 |
| BA-SRM7 final input receipt | `bbb2382ef510a8323ba9b14b1aaa7f653d675fecbe6f34f48d61f3385586c51f` | source/archive/schema/clock/unit PASS, common anchor FAIL | 같은 판본에서 hard-gap 완화 |
| brain route ledger | `d5ebb241f777e38facab37e20ec4a34c6b7166fea2586d65bb589ec6ec366115` | BA-SRM7 formal/empirical 지위 정본 | 미검증 주장 승격 |

BA-SRM7에서 실패한 anchor count `214/42/33`, `372/107/48`, `23/8/0`,
`555/53/159`는 수정하지 않고 matched diagnostic로 보존한다.

## 3. 데이터ㆍsource lock

Hallinen et al. eLife 논문 DOI `10.7554/eLife.66135`, OSF 데이터 DOI
`10.17605/OSF.IO/DPR3H`, PredictionCode revision
`ca59416112a9c10a8d6a3179092a7d3c888bcd4e`를 재사용한다. 세 archive bytes/hash와
공개 코드 파일 hash는 `artifacts/source-lock.json`에 다시 고정한다. OSF license
field가 null이므로 raw/derived 데이터를 commit하거나 재배포하지 않는다.

`artifacts/source-lock.json` SHA-256은
`234bac2c67e98a8a0745ef412745b5c360d4d5751d73c14f290c15f1d80ad495`다.

공개 predictor의 입력은 `I_smooth_interp_crop_noncontig`이고, 공개 코드의 Gaussian은
centered symmetric다. BA-SRM8의 causal filter, 물리시간 kernel, quality weight,
robust map과 $n_{\rm eff}$는 모두 `[공리: 분석자 측정 개정]`이며 published method라고
부르지 않는다.

recording outer role은 BA-SRM7의 11 GCaMP와 11 GFP train/validation/held-out 배치를
그대로 쓴다. primary target은 `behavior.v`의 $h=6$ 미래값, secondary descriptive
target은 `behavior.pc1_2[:,0:2]`다.

## 4. source-rooted causal 관측

official cut 이후의 원래 raw clock grid를 유지한다. manual exclusion과
`flagged_volumes`는 timepoint 삭제가 아니라 해당 sample의 mask 0으로 표현한다.
photobleaching fit과 neuron별 red-to-green OLS는 recording raw first-60%에서 finite,
unflagged pair만 읽는다. 이후 전체 grid에는 동결한 parameter만 적용한다. one-sided
Gaussian은 $\sigma=5$, lag $0,\ldots,20$만 쓴다.

processed first-60%에서 raw $I$ finite sample이 60개 이상이고 causal signal standard
deviation이 $10^{-12}$보다 큰 neuron만 남긴다. prefix meanㆍscale과 finite fraction
$\pi_i$를 고정하고

$$
D=\operatorname{diag}(\sqrt{\pi_1},\ldots,\sqrt{\pi_N}),\qquad
z_{i,j}=\frac{\bar I_{i,j}-\widehat\mu_i}{\widehat\sigma_i}
$$

로 둔다. nonfinite $z_{i,j}$는 0, finite mask는 $m_{i,j}=1$로 쓴다. timepoint quality는

$$
q_j=\frac1N\sum_{i=1}^N m_{i,j}\in[0,1]
$$

다. manual exclusionㆍflagged timepoint는 $q_j=0$이다. behavior, target 또는 뒤
screening block은 이 단계의 parameter에 들어가지 않는다.

## 5. 물리시간 weighted PSD operator

recording prefix의 median positive clock step을 $\tau_0$로 두고

$$
u_{tj}=\frac{t_t-t_j}{\tau_0},\qquad
\delta_j=\min\!\left(3,\frac{t_j-t_{j-1}}{\tau_0}\right)
$$

로 무차원화하고 첫 sample에는 $\delta_0=1$을 둔다. $t_j\le t_t$인 current/past
sample만 허용한다. candidate $f$의
kernel $K_f\ge0$, quality exponent $\gamma_f\in\{1,2\}$에 대해

$$
a^{(f)}_{tj}=K_f(u_{tj})q_j^{\gamma_f}\delta_j,\qquad
w^{(f)}_{tj}=\frac{a^{(f)}_{tj}}{\sum_{k\le t}a^{(f)}_{tk}}.
$$

$\delta_j$의 cap 3은 긴 미관측 구간을 바로 뒤 한 sample이 대표하지 못하게 하는
분석자 규칙이다. 이 판본은 gap barrier가 아니라 `SOFT_GAP_DOWNWEIGHTING`을 선택한다.
gap 전 neural past는 보간되지 않고 실제 경과시간 $u$만큼 kernel에서 감쇠된 뒤 남는다.
따라서 gap을 가로질러 생물학적 연속성이 관측됐다고 주장하지 않는다. clock이
nonfinite 또는 non-increasing이면 recording input을 중지한다.

candidate robust map $R_f$를 적용한

$$
x_j^{(f)}=R_f\!\left(D[m_j\odot z_j]\right),\qquad
\bar x_t^{(f)}=\sum_jw^{(f)}_{tj}x_j^{(f)}
$$

와

$$
n_{{\rm eff},t}^{(f)}=
\frac{(\sum_ja^{(f)}_{tj})^2}{\sum_j(a^{(f)}_{tj})^2}
=\frac1{\sum_j(w^{(f)}_{tj})^2}
$$

를 정의한다. $n_{\rm eff}<8$, 양의 weight가 두 개 미만, 분모 nonfinite면 그 anchor만
`ABSTAIN_INSUFFICIENT_INFORMATION`이다. 나머지는

$$
G_t^{(f)}=
\frac{\sum_jw^{(f)}_{tj}
(x_j^{(f)}-\bar x_t^{(f)})(x_j^{(f)}-\bar x_t^{(f)})^{\mathsf T}}
{1-\sum_j(w^{(f)}_{tj})^2}\succeq0
$$

로 둔다. pairwise-complete denominator와 negative kernel weight는 금지한다.
$n_{\rm eff}\ge8$은 covariance 집중도와 분모 안정성 gate일 뿐 행동 예측력이나
생물학적 정보량이 충분하다는 조건이 아니다.

## 6. 정확히 48개의 후보 grammar

kernel specification은 다음 여덟 개다. 모든 parameter는 무차원이며 formula ID의
일부다.

| family | fixed specifications |
|---|---|
| EXP | $K(u)=e^{-u/\theta}$, $\theta\in\{2,10\}$ |
| BIEXP | $K(u)=\tfrac12e^{-u/\theta_1}+\tfrac12e^{-u/\theta_2}$, $(\theta_1,\theta_2)\in\{(1,8),(4,32)\}$ |
| POWER | $K(u)=(1+u/\theta)^{-p}$, $(\theta,p)\in\{(2,1.5),(8,2)\}$ |
| COMPACT | $K(u)=\exp[-1/(1-(u/L)^2)]$ for $0\le u<L$, otherwise 0, $L\in\{4,16\}$ |

POWER의 $p>1$은 연속 무한 과거에서 적분 가능하게 한다. 각 kernel에
$\gamma\in\{1,2\}$와 다음 세 robust map을 곱한다.

$$
r(x)=\frac{\|x\|_2}{\sqrt N},\qquad c=3,
$$

$$
R_{\rm id}(x)=x,\qquad
R_{\rm Hub}(x)=
\begin{cases}
x\min(1,c/r(x)),&r(x)>0,\\
0,&r(x)=0,
\end{cases}
$$

$$
R_{\tanh}(x)=
\begin{cases}
x\,\tanh(r(x)/c)/(r(x)/c),&r(x)>0,\\
0,&r(x)=0.
\end{cases}
$$

따라서 후보 수는 $8\times2\times3=48$이다. ambient isotropic shrinkage는 rank를
인위적으로 full로 만들어 기존 $d_{\rm eff}/r_\star\le1$ 정규화를 깨므로 primary
grammar에서 제외하고 diagnostic로만 둔다.

각 후보는 canonical JSON manifest와 SHA-256을 behavior 개봉 전에 고정한다. 후보를
추가ㆍ삭제하거나 parameter를 바꾸면 새 run이다. 탈락 후보는 같은 run에서 부활하지
않는다. POWER는 현재 anchor까지의 full causal tail을 쓰며 임의 truncate하지 않는다.
각 manifest row는 kernel support/tail rule과 calibration 범위를 기록한다.

동결 산출은 다음과 같다.

| artifact | SHA-256 |
|---|---|
| `artifacts/candidate_manifest.py` | `b96f5cbc9b4531ada6516b633f1e1d555bb0da912ecf76dd3d6eb92e5f2c6577` |
| `artifacts/candidate-manifest.json` | `58280bb9759549b9f285e95135b5320e44f1d317adf347a065319f367a3e6a0c` |
| `artifacts/candidate-manifest-receipt.json` | `cdb1dc8ccdbca5808613ade8f5a3ce946087e720611a40193ca8198c5d53651d` |

manifest의 canonical compact-content SHA-256은
`37c04ab2b59e4dcba64311f570526ae83a21e4ea59a03c18b479bceb9e05374b`이며 candidate
count 48과 unique ID 검사를 통과했다.

## 7. 연속 유효차원 feature

양의 weight sample 수 $n_{+,t}=|\{j:a_{tj}>0\}|$를 original time anchor마다 세고

$$
r_{\star,t}=\min(N,n_{+,t}-1),\qquad
c_G^{(f)}=\operatorname{median}_{0\le t<\lfloor0.70T\rfloor}
\frac{\operatorname{tr}G_t^{(f)}}{r_{\star,t}}.
$$

abstain anchor는 median에서 제외하되 usable covariance를 압축한 뒤 그 목록의 70%를
쓰지 않는다. $r_\star$에도 numerical matrix-rank tolerance를 쓰지 않는다.
$c_G\le10^{-12}$ 또는 nonfinite면 candidate가 abstain한다. primary $\lambda=1$에서

$$
\widetilde G_t^{(f)}=G_t^{(f)}/c_G^{(f)},\qquad
S_t^{(f)}=\widetilde G_t^{(f)}(\widetilde G_t^{(f)}+I)^{-1},
$$

$$
d_{\rm eff}^{(f)}(t)=\operatorname{tr}S_t^{(f)},\qquad
Q_t^{(f)}=d_{\rm eff}^{(f)}(t)/r_{\star,t}.
$$

$0\le Q_t\le1$이다. $\tau_0$와 first-70% feature RMS만으로

$$
V_t^{(f)}=\frac{Q_t^{(f)}-Q_{t-1}^{(f)}}{(t_t-t_{t-1})/\tau_0},
$$

$$
\kappa_t^{(f)}=
\frac{\|S_t^{(f)}-S_{t-1}^{(f)}\|_F}{\sqrt{r_{\star,t}}},\qquad
M_t^{(f)}=\exp[-(V_t/\sigma_V)^2-(\kappa_t/\sigma_\kappa)^2]
$$

를 만든다. candidate predictor에는 정확히 $(Q,V,\kappa,M)$ 네 scalar만 추가한다.
$M$은 안정도 proxy이지 consciousness score가 아니다.

## 8. 70/10/20 temporal lock

각 recording의 behavior-independent original clock anchor를 시간 순서대로 다음처럼
분할한다.

| 구간 | 누적 위치 | 용도 |
|---|---:|---|
| calibration/train | 0--70% | measurementㆍscaleㆍridge fit, 내부 blocked CV |
| SMALL | 70--72% | 2% gross screen |
| MID | 72--75% | 3% independent screen |
| LARGE-A | 75--77.5% | 2.5% champion selection |
| LARGE-B | 77.5--80% | 2.5% champion recheck |
| FINAL | 80--100% | sealed one-shot confirmation |

target horizon과 stage 경계에는 양쪽 $h+12=18$ volume을 제외한다. FINAL 앞에는
60-volume embargo를 둔다. natural causal state가 앞 구간의 neural past를 쓰는 것은
허용하지만, SMALL 이후에는 coefficient, scale, kernel, ridge, threshold를 다시 fit하지
않는다.

behavior 개봉 전 `artifacts/neural-stage-lock.json`에 candidate별 stage anchor raw-volume
ID hash와 공통 row를 기록한다. SMALL/MID/LARGE 각 block은 GCaMP non-held-out recording
cluster가 최소 7개, cluster당 8 common row 이상, pooled common row 100개 이상이어야
한다. 이 세 값은 각각 최소 cluster 수, covariance가 실제 계산되는 최소 row, gross
ranking coverage를 검사한다. stage score는 recording마다 먼저 하나로 집계하므로
window row를 독립 표본으로 세지 않는다. selection 유효 cluster 수는 common row가
있는 recording 수이며 최소 7이다.

FINAL은 두 GCaMP held-out recording 각각 common row 100개 이상이어야 한다. candidate
coverage는 같은 stage base anchor의 95% 이상이어야 한다. 이 하한 중 하나라도 부족하면
score를 보지 않고 candidate `ABSTAIN`; survivor가 0이면 `PHYSICAL_TIME_INPUT_STOP`이다.
SMALL/MID/LARGE는 ranking 전용이고 작은 block에서 confidence interval, p-value 또는
생물학적 효과 주장을 만들지 않는다.

## 9. 싼 검증부터 비싼 검증으로 가는 funnel

후보 상태는 `INVALID_KILL`, `FUTILITY_KILL`, `DROPPED_BUDGET`, `ABSTAIN`, `PROMOTE`로
구분한다. 수학ㆍ누출ㆍPSD 위반은 영구 kill이고, 표본 부족은 식의 음성 결과가 아니라
abstain이다.

| 단계 | behavior | 최대 후보 | 비용과 절대 gate | 다음 최대 |
|---|---:|---:|---|---:|
| F0 static/property | 0% | 48 | $T=48,T_{\rm cal}=33$; causality, concrete PSD, 무차원성, zero/nonfinite fail-closed, one warmup 뒤 median-5 micro runtime $\le4\times$ `EXP-10/gamma-1/identity` | 48 |
| F1 micro synthetic | 0% | 48 | $N=8,T=192,T_{\rm cal}=134,T_D=115$, 4 seeds; median Spearman $\ge0.75$, NMAE $\le0.25$ | 32 |
| F2-A/B/C/D stress synthetic | 0% | 32 | 8-seed successive-halving screen, then independent 32-seed confirmation | at most 16 |
| F2R real-background | 0% | at most 16 confirmed | behavior-blind phase-randomized train calcium injection | 8 |
| SMALL | 2% | 8 | gross futilityㆍcoverageㆍsimple controls | 4 |
| MID | 3% | 4 | recording consistencyㆍmatched controls | 2 |
| LARGE-A | 2.5% | 2 | practical effectㆍadverse controls | 1 |
| LARGE-B | 2.5% | 1 | 독립 재확인; 실패 시 runner-up 금지 | 1 또는 0 |
| FINAL | 20% | 1 | sealed full controls와 one-shot 판정 | PASS/FAIL |

F0은 첫 hard failure에서 candidate의 나머지 검사를 중단한다. runtime은 기준 candidate와 각 candidate를 한 번 warmup한 뒤 독립된 다섯 번의 측정 중앙값으로 비교한다. 전처리, mask, standardized
trace와 stage rows는 candidate hash를 key로 cache하고 survivor만 다음 stage에서 계산한다.
full 10,000-resample bootstrap은 FINAL 전에는 실행하지 않는다.

F0 concrete PSD gate는 각 candidate의 실제 구현이 만든 모든 valid covariance의 최소
고유값을 검사한다. causality gate는 original first-70% 경계 뒤의 value와 mask/quality를
함께 교란하고, 동결 $c_G$와 그보다 앞선 모든 $Q_t$가 $10^{-12}$ 안에서 불변인지
확인한다. zero와 nonfinite 입력이 명시적으로 fail-closed하는지도 직접 호출한다.

F1의 clean truth와 noisy estimate는 같은 dropout mask, 같은 prefix-fixed $D$, clock,
candidate와 physical-time weight를 쓴다. 차이는 clean/noisy value뿐이며 각각 original
zero-based $0\le t<T_{\rm cal}=\lfloor.70T\rfloor$의 exclusive 경계에서 자기 $c_G$를 fit한다. F1에서는 $T_{\rm cal}=134$, $T_D=115$다. recovery anchor는 $A_s=\{t:Q_t^{\rm truth},\widehat Q_t\text{ 모두 finite}\}$이며, $|A_s|$는 최소 100개여야
하고, 그보다 적으면 score 0이 아니라 `ABSTAIN`이다. F1의 고정 오차는 normalized $Q$의

$$
\operatorname{NMAE}^Q_s=\frac1{|A_s|}\sum_{t\in A_s}
|\widehat Q_t-Q_t^{\rm truth}|
$$

다. range normalization은 금지한다. Spearman은 average-rank 정의를 쓰며 clean truth가
constant면 `ABSTAIN`이다.

F1의 유일한 promotion source는 self-contained v6 runner와 receipt다. v6은 합성 raw trace에 noise를 더한 뒤 clean/noisy 각각이 자기 first-60% masked finite prefix에서 $\mu,\sigma$를 다시 fit해 z-score하고, noise SD는 prefix pooled RMS/4로 고정한다. shared $D$, mask, clock과 original-index exclusive $c_G$ 규칙을 유지한다. runner SHA-256은 `3ab7eb89d49ae3845a72e5808f0cf9423014f520b961fe7551576be22f1c2be7`, receipt SHA-256은 `8cbdaed43fc861c4696a41a3fd84331fd41727622d848e123b635d8c9ae11cca`다. v6은 12 `ABSTAIN`, 32 `PROMOTE`, 4 `DROPPED_BUDGET`이며 promoted set과 manifest-lexical tie order를 동결한다. valid F0-v3 receipt SHA-256은 `86b70828449889c1f3bfaf9422a0e41b01655d83bcd7d1c067b3d8da796b1ab7`다. v3/v4/v5는 각각 documented full-$T$, ceil-boundary, constant-truth/provenance 문제로 보존만 하고 superseded하며 promotion source가 아니다.

F2는 $N=12,T=768,T_{\rm cal}=537,T_D=460$ synthetic trace의 behavior-blind successive-halving screen이다. $T_{\rm cal}=\lfloor.70T\rfloor=537$와 $T_D=\lfloor.60T\rfloor=460$는 모두 zero-based exclusive 경계다. clean/noisy 각각은 자기 first-60% masked finite prefix에서 $\mu,\sigma$를 fit하고, shared $D$, mask, clock을 쓰며 $c_G$만 각 original-index exclusive calibration boundary에서 따로 fit한다. recovery anchor는 $A=\{t:Q_t^{\rm truth},Q_t^{\rm est}\text{ 모두 finite}\}$이고 모든 scored seed는 $|A|\ge100$이어야 한다. 아니면 candidate는 `ABSTAIN`이다. truth $Q$는 latent brain dimension이 아니라 같은 candidate의 clean observed operator 값이다.

F2 DGP는 다음과 같이 동결한다. base increment는 zero-based `dt[1:]\sim U(.75,1.25)`이고 `dt[0]=0`이다. `1..T-1`에서 without-replacement로 뽑아 sort한 distinct index 세 곳의 increment를 순서대로 $U(4,8)$ draw로 바꾼 뒤 $c=\operatorname{cumsum}(dt)$로 clock을 만든다. $\tau_0=\operatorname{median}(dt[1:])$다. nonzero smooth route에서는 fresh seed matrix $A_{\rm g}$에서 skew matrix $B=(A_{\rm g}-A_{\rm g}^\mathsf T)$를 redraw하여 $\|B\|_2>10^{-12}$인 첫 draw만 $B\leftarrow B/\|B\|_2$로 정규화하고,
$$
U_t=\operatorname{expm}\!\left[.35\sin(2\pi t/256)B\right],\qquad
\mu_k(t)=\exp\!\left[-\frac{k-1}{3.5+2\sin(2\pi t/384)}\right],
$$
$$
x_t=U_t\operatorname{diag}(\sqrt{\mu(t)})\xi_t,\quad \xi_t\sim N(0,I),
$$
$$
y_t=(1-a_t)x_t+a_ty_{t-1},\qquad a_t=\exp(-\Delta t_t/6).
$$
여기서 `scipy.linalg.expm`, C-order `float64`, spectral norm을 쓴다. raw $y_t$를 반환하고 기존 prefix preprocessing을 적용한다. estimate noise는 Gaussian이며 SD는 해당 scenario의 raw-clean first-60% prefix pooled RMS/4다. artifact sigma는 raw-clean prefix population standard deviation (`ddof=0`)이다. linear quantile은 `numpy.quantile(method="linear")`다.

ROT10은 이 smooth route에 irregular clock, MCAR10%, estimate noise를 적용한다. MISS30/MISS50은 같은 route에 각각 MCAR30%/50%를 적용하며 MISS50은 descriptive only다. BLOCK30은 ROT10에 더해 channel마다 독립적으로 길이 $\lfloor.3T\rfloor$의 mask-zero contiguous block 하나를 둔다. ART10은 ROT10에 estimate-only Bernoulli 1% entry impulse를 더하며, 부호는 독립 $\pm1$, 크기는 해당 scenario raw-clean prefix pooled sigma의 $10$배다. JUMP는 $U_t=I$, $t_*=384$ 전에는 $\mu_{1:2}=1$, 뒤에는 $\mu_{1:8}=1$, 나머지는 0으로 하고 irregular clockㆍMCAR10%ㆍnoise를 적용한다. ISO_NULL은 $U_t=I$, 모든 $\mu_k=1$에 irregular clockㆍMCAR10%ㆍnoise를 적용한다. ZERO_NULL은 raw $y=0$, additive noise 없음, declared mask/clock으로 실행하며 expected abstain이다. REVERSE는 독립 생성한 ROT10 clean/noisy/mask의 values와 mask를 역순으로 놓고 $c'_j=c_{T-1}-c_{T-1-j}$로 increasing check-clock을 만들며 recovery에만 쓴다. original/reverse equality는 요구하지 않는다. calibration seed와 evaluation seed는 이 같은 generator를 쓰되 scenario/base-seed hash가 달라 RNG stream이 겹치지 않는다.

null calibration seed는 $S_{\rm cal}=20261001,\ldots,20261016$이다. 각 candidate $f$의 threshold는 ISO_NULL estimate에서만
$$
\theta_f=Q_{0.95}^{\rm linear}\left(|V_{\rm est}|\right),\qquad
V_{\rm est}(t)=\frac{Q_{\rm est}(t)-Q_{\rm est}(t-1)}{(c_t-c_{t-1})/\tau_0},
$$
로 동결한다. derivative anchor는 $B=\{t:t\in A,\ t-1\in A\}$이며 $V_{\rm est}$는 $B$에서만 정의한다. ISO_NULL 또는 JUMP에서 $|B|<100$이면 candidate는 `ABSTAIN`이다. FAR는 $|V_{\rm est}|>\theta_f$의 seed별 fraction이며 estimate $Q$만으로 계산한다. JUMP detection은 $t_*=384$의 $\pm96$ 안에서 $|V_{\rm est}|$의 argmax가 있고 그 maximum이 $\theta_f$를 넘는 경우다. truth $Q$는 NMAE와 Spearman 계산에만 쓴다.

모든 F2 난수 substream은 UTF-8 `SHA256("BA-SRM8-F2-SH-v2|<scenario>|<base_seed>|<stream>")`의 first 8 bytes를 big-endian `uint64` seed로 써서 분리한다. stream은 `clock_base`, `clock_gap_indices`, `clock_gap_sizes`, `skew:<redraw_index>`, `latent`, `noise`, `mask_mcar`, `block_start`, `artifact_select`, `artifact_sign`이다. array는 C-order `float64`; draw shape는 순서대로 clock base $(T-1,)$, gap index $(3,)$, gap size $(3,)$, skew $(N,N)$, latent/noise/mask/artifact select/artifact sign $(N,T)$, block start $(N,)$다. 비교는 MCAR에서 `rng>=p`, artifact selection에서 `rng<.01`, artifact sign에서 `rng<.5`이면 $-1$이다. calibration과 evaluation은 이 substream 규칙을 공유하되 scenario/base-seed가 달라 stream이 겹치지 않는다. `E_A=20261101..20261108`, `E_B=20261109..20261116`, `E_C=20261117..20261124`, `E_D=20261125..20261132`이다. stage ranking은 $E=$ISO를 포함해 numerical NMAE가 정의된 scenario별 median NMAE의 최대값(오름차순), $R=$Spearman이 정의된 non-null recovery scenario별 median Spearman의 최소값(내림차순; F2-A에서는 JUMP만), frozen ISO FAR(오름차순), runtime(오름차순), manifest ID 순서다. expected-abstain ZERO는 $E,R$에 넣지 않는다. cap 밖의 유효 후보는 `DROPPED_BUDGET`이며 실패가 아니다.

F2 config-v4 SHA-256은 `9248c9fac975ea70ac034d11e45be70eff7abccb13b65eae7be7010850e2de47`, 그 receipt는 `a4b1da7b6feb62b65768b993eda682470a20f3e77e41142e656347d8d5d5c7a9`다. common generator-v2 SHA-256은 `12200f0f6d2d2db61d1000c40a39049123b5f1e2023ef439f9763ad69794f605`, fixture-v3 SHA-256은 `6346c57cbdc7c8b564b316aca0ba06008ac01c9e66035b7794f8c472612592bf`다. fixture는 deterministic pseudocode/source closure일 뿐 candidate $Q$, F2 gate, behavior 또는 model 결과가 아니다.

| screen | input $\to$ cap | seeds / scenarios | 즉시 중단 또는 futility gate |
|---|---:|---|---|
| F2-A | 32 $\to$ 24 | $E_A$: ZERO_NULL, ISO_NULL, JUMP | ZERO는 모두 `ABSTAIN_EXPECTED`여야 한다(그 외 `INVALID_KILL`). JUMP median $\rho<.80$, median NMAE$^Q>.20$, mean FAR$>.20$, 또는 detected $<4/8$이면 `FUTILITY_KILL`. |
| F2-B | 24 $\to$ 20 | $E_B$: ROT10, MISS30 | 어느 scenario라도 median $\rho<.80$ 또는 median NMAE$^Q>.20$이면 `FUTILITY_KILL`. |
| F2-C | 20 $\to$ 16 | $E_C$: BLOCK30, ART10 | 어느 scenario라도 median $\rho<.80$ 또는 median NMAE$^Q>.20$이면 `FUTILITY_KILL`. |
| F2-D | at most 16, no cap | $E_D$: REVERSE, ISO_NULL recheck | REVERSE의 median $\rho\ge.80$, median NMAE$^Q\le.20$와 ISO_NULL recheck mean FAR$\le.20$를 요구하며, 하나라도 실패하면 `FUTILITY_KILL`이다. |

MISS50은 screen ranking/gate에 넣지 않는 descriptive stress다. F2-D 뒤 survivor만 independent confirmation panel `20261201..20261232`에서 ROT10, MISS30, BLOCK30, ART10, JUMP, REVERSE를 모두 실행한다. 각 scenario는 median $\rho\ge.90$, linear $Q_{0.05}(\rho)\ge.75$, median NMAE$^Q\le.15$를 요구한다. ISO_NULL은 median NMAE$^Q\le.15$, mean FAR$\le.10$, max FAR$\le.20$; ZERO는 모두 expected abstain; JUMP는 32/32 localization과 threshold 통과를 요구한다. MISS50은 여기서도 descriptive only다. confirmation은 rerankingㆍreplacement 없이 통과/탈락만 결정하며, 통과 후보만 F2R에 갈 수 있다.

F2R은 behavior를 읽지 않은 real neural background $B$에 known observed signal $U$를

$$
Y^{(\rho)}=B+\sqrt\rho\frac{\operatorname{RMS}(B)}{\operatorname{RMS}(U)}U,
\qquad \rho\in\{0,0.5,1\}
$$

로 주입한다. $\rho=1$의 recording-median Spearman은 0.75 이상이고 $\rho=0$보다
커야 하고 NMAE는 0.25 이하여야 하며, null false alarm은 0.10 이하여야 한다.

F1과 F2의 absolute gate 통과 후보는 `(median NMAE 오름차순, median Spearman
내림차순, runtime 오름차순, formula ID)`의 사전 고정 lexicographic order로 각각
32개와 16개까지 올린다. F2R은 `(rho-1 median Spearman 내림차순, NMAE 오름차순,
false-alarm 오름차순, runtime 오름차순, formula ID)`로 8개까지 올린다. 이 순서는
behavior를 사용하지 않는다.

## 10. 행동 model, promotion과 controls

기준 model은 target의 lag $\{0,1,3,6\}$ ridge AR이고 후보 model은 같은 AR에 네 feature만
추가한다. ridge grid $\{0,0.01,0.1,1,10,100\}$는 0--70% blocked CV에서만 고른 뒤
coefficient와 함께 `candidate-lock.json`에 고정한다. 모든 비교는 stage survivor와
mandatory control의 교집합 row에서 한다.

각 recording 안의 모든 common-row loss를 먼저 평균한 뒤 recording $r$, candidate
$f$의 primary 점수는

$$
\Delta R^2_{r,f}=R^2_{r,f}-\max_{c\in\mathcal C_j}R^2_{r,c},
$$

$$
J_j(f)=\operatorname{median}_r\Delta R^2_{r,f}
-0.25\operatorname{MAD}_r(\Delta R^2_{r,f})
$$

다. 따라서 $J_j$의 표본 단위는 window가 아니라 recording cluster다. absolute gate를
통과한 후보만 $J_j$ 내림차순으로 promotion cap까지 올린다. 동률은
kernel component 수가 적은 식, 그 다음 manifest ID lexical order다.

- SMALL: $J<-0.01$이면 `FUTILITY_KILL`; 나머지 중 상위 4. $J\le0$인 비승격 후보는
  `DROPPED_BUDGET`이지 과학적 반례가 아니다.
- MID: $J>0$이고 recording의 절반 이상에서 $\Delta R^2>0$인 후보만 상위 2.
- LARGE-A: $J\ge0.005$, AR 대비 normalized MSE 개선 0.5% 이상, adverse control보다
  높아야 champion 1개를 선택한다.
- LARGE-B: 같은 champion이 새 block에서 $J>0$이고 adverse control보다 높아야 FINAL
  lock을 만든다. 실패하면 runner-up을 열지 않는다.

mandatory matched controls는 AR, hard-gap BA-SRM7, fixed 4, participation ratio, raw
spectrum, mask-only, causal-unweighted, red channel이다. phase randomization, time reversal,
neural/behavior circular shift와 GFP는 adverse falsifier다. archived symmetric source
filter는 미래를 읽으므로 diagnostic-only이고 predictive score 경쟁에 넣지 않는다.

## 11. FINAL 20% one-shot

LARGE-B 뒤 `final-lock.json`에 champion formulaㆍcoefficientㆍridgeㆍpreprocessingㆍrowㆍ
targetㆍscore codeㆍcontrols의 hash를 고정한다. FINAL에는 champion 하나만 접근한다.

두 held-out GCaMP recording 각각에서 champion은 최선 matched control보다
$\Delta R^2\ge0.005$, AR보다 normalized MSE가 1% 이상 낮아야 한다. paired moving-block
bootstrap block은 0--70% training paired-loss difference의 initial-positive-sequence
autocorrelation time $\widehat\tau_{\rm int}$만으로

$$
B=\max(60,\lceil2\widehat\tau_{\rm int}\rceil)
$$

로 FINAL 개봉 전에 고정하고 10,000회 resample한다. window-level pooled interval은
금지한다. primary cluster statistic은 두 recording-level paired difference의 최솟값

$$
D_{\rm cluster}=\min_{r\in\text{held-out}}\Delta R^2_r
$$

이며 $D_{\rm cluster}\ge0.005$를 요구한다. 각 recording의 conditional moving-block
one-sided 95% lower bound도 0보다 커야 한다. recording이 두 개뿐이므로 이것을 animal
population confidence interval로 부르지 않고, 두 recording 모두에서 재현된 temporal
developmental evidence로만 쓴다. phase, reverse 또는 shift adverse control 하나라도
champion 이상이면 `TEMPORAL_ALIGNMENT_NOT_IDENTIFIED`다.

FINAL에서 coefficient refit, threshold 변경, runner-up 추가, endpoint 교체, exclusion,
새 baseline 추가는 금지한다. FINAL 실패 뒤 같은 20%로 다른 식을 시험하지 않는다.
새 식은 새 계약과 독립 corpus가 필요하다. 이 corpus가 줄 수 있는 최대 지위는
`BIO_EVIDENCE_L3_DEVELOPMENTAL_HELD_OUT`이며 보편적 뇌 이론 확인이 아니다.

## 12. 중지 규칙과 실행 순서

1. contract, source, math, alternative lane을 동결한다.
2. 독립 audit가 `Gate: PASS`를 줄 때만 한 implementation owner가 harness를 만든다.
3. F0→F1→F2→F2R을 순서대로 실행한다. 앞 단계 survivor만 다음 단계에 접근한다.
4. neural stage lock가 통과한 뒤에만 behavior 0--70%와 SMALL을 연다.
5. 각 screen receipt를 fsyncㆍSHA-256 고정한 뒤 다음 block을 한 번 연다.
6. LARGE-B가 통과한 champion 하나만 FINAL을 연다.

언제든 source/hash/schema/clock 실패, survivor 0, 공통 row 부족, synthetic apparatus 실패,
control gate 실패 또는 lock 불일치가 나면 그 지점에서 fail-closed한다. 결과를 본 뒤
비율ㆍthresholdㆍcandidate를 바꾸지 않는다.
