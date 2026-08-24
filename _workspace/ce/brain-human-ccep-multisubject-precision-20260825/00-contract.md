# BA-OBS-DISC2 연구 계약 — 74명 실제 인간 CCEP의 다피험자 전기·기하 response kernel

Status: COMPLETE

Implementation: PENDING

Scientific endpoint: UNOPENED

PREDECESSOR: `_workspace/ce/brain-human-ccep-equation-discovery-20260824`

## 0. 질문, 목적, 주장 경계

이 run은 OpenNeuro `ds004080` v1.2.4의 실제 인간 ECoG single-pulse electrical
stimulation(SPES) 자료에서 다음 질문 하나를 순차 검증한다.

> 짧은 CCEP 구간의 전기적 Green/cable/heat 근사에서 유도한, 사전 고정된 저차
> fsaverage 기하 후보가 동일한 시간·나이·source calibration을 가진 geometry-free
> baseline보다 **아직 보지 않은 환자**의 bipolar response energy를 더 잘 예측하는가?

이것은 한 환자 안의 edge 보간이 아니다. 74명을 완전히 분리해 D0에서 구조를 고르고,
D1/D2에서 빠르게 제거하고, D3의 30명에게 한 번만 일반화한다. 성공하더라도 직접 지지하는
것은 측정사슬을 통과한 `OBSERVED_MULTI_SUBJECT_CCEP_RESPONSE_KERNEL`뿐이다. 실제 axonal
geodesic, 생물학적 conductance metric, fiber orientation, 무한차원 상태공간, 의식·자아·해마
hash 또는 AGI는 이 자료만으로 식별하지 않는다.

### PREDECESSOR_EVIDENCE

| 선행 단계 | artifact / SHA-256 | 판정 | 보존 가능한 좁은 주장 | 재사용·재시도 금지 |
|---|---|---|---|---|
| DISC1 D0, `ds003708`, 1명, 24 pairs | `artifacts/d0-receipt.json` / `ea666cf14b4cc5de829ba9e151ef1879012019754a79ffeb92fdca17d42d4355` | `PASS_SELECTION_ONLY` | CABLE이 15식 중 선택됐고 bipolar 개선률 0.05211, 6 fold 중 4 승이었다. | 확인 증거로 승격 금지; 이번 후보 축소에만 사용 |
| DISC1 D1, 48 held-out pairs, 24 sources | `artifacts/d1-receipt.json` / `cc275936b1ffe281238f853ef73394eaba11bb852c2c252930b2b28f05c23ded` | `PASS_INTERMEDIATE` | 평균 개선 0.03630; 95% CI [0.01139, 0.06097], permutation p=0.000976였다. | 효과 크기·분산 planning에만 사용 |
| DISC1 D2, 39 held-out pairs, 24 sources | `artifacts/d2-receipt.json` / `023a86a73173921544cc4145df7e76e3fca3f97da4f97cd82a2589a10431ed1a` | `STOP_NOT_CONFIRMED` | 평균 개선 0.02352였지만 95% CI [-0.00576, 0.04930]으로 source 일반화가 불안정했다. | D2를 보고 같은 판본 식/window/threshold 변경 금지 |
| DISC1 D3, 40 pairs | receipt 없음; barrier는 DISC1 code `af70dc054714fccc496bd50a8e25139bd7e4b28dc7a5ddd3acc7a008a36bd8da` | `UNOPENED` | 값이 없다는 사실만 보존한다. | 어떤 재튜닝·확인에도 개방 금지 |

DISC1의 식·창·threshold를 고쳐 같은 D3에 재시도하지 않는다. 이번 판본은 별도 dataset,
별도 환자 split, 별도 계약을 사용한다.

## 1. 전기적 출발식

### 1.1 비선형·기억 의존 계

`[공리/생물물리 출발점]` 막전압, 이온 gate, 시냅스 상태와 전도 경로를 묶은 상태를
$q(t)$라 하고, 자연 상태공간을 Hilbert/Banach 공간 $\mathcal H$로 둔다. 시냅스가 과거
spike·전압·상태의 함수라면 일반식은

$$
\mathcal C(q)\dot q(t)
=\mathcal F\!\left(q(t),q_{(-\infty,t]};\Xi\right)
+\mathcal B_s u_s(t)
$$

처럼 기억 의존 연산자가 되며 $\mathcal H$는 유한차원일 필요가 없다. 이 식은 이번
자료로 무한차원을 증명한다는 뜻이 아니라, 단일 scalar $W_{ij}$보다 넓은 출발공간을
명시하는 공리다.

### 1.2 짧은 CCEP 창의 Fréchet 선형화

`[산출/조건부]` resting operating point $q_*$ 부근의 120 ms 구간에서 선형화하면

$$
\mathcal C_*\dot v(t)
=-\mathcal A_*v(t)+\mathcal B_s Q_s\delta(t),
\qquad
v(t)=e^{-t\mathcal C_*^{-1}\mathcal A_*}
\mathcal C_*^{-1}\mathcal B_sQ_s .
$$

$\mathcal C_*$는 유효 capacitance, $\mathcal A_*$는 막 누설·축삭/시냅스 전도·network
coupling을 함께 가진 국소 연산자다. 실제 계의 비선형성은 사라진 것이 아니라 이번 짧은
intervention 창에서의 국소 근사 오차로 잔차에 남는다.

국소 chart에서 $\mathcal A_*$의 대칭·확산 성분을

$$
\mathcal A_*\simeq
-|G|^{-1/2}\partial_a
\left(|G|^{1/2}D G^{ab}\partial_b\right)+\Lambda
$$

로 근사할 수 있을 때 short-time Green kernel은 조건부로

$$
K(t;X_d,X_s)
\propto t^{-q/2}
\exp\!\left[-\frac{d_G^2(X_d,X_s)}{4Dt}-\Lambda t\right]
$$

형태를 갖는다. 반면 cable attenuation은 leading order에서 $\exp(-a d_G)$를 준다.
이번 자료의 자유 시간항 $\beta_{\log t}\log t$와 $-q\log t/2$가 정확히 중복되므로
$q$는 적합하지 않으며 잠재 차원이라고 해석하지 않는다.

### 1.3 측정 연산자

`[정의]` 전극이 읽는 값은

$$
y^{\rm obs}(t)=C_{\rm ref}R\,v(t)
+a_{\rm stim}(t)+c_{\rm common}(t)+\eta(t).
$$

$C_{\rm ref}R$은 전극 sampling, volume conduction, channel reference를, $a_{\rm stim}$은
자극 artifact를, $c_{\rm common}$은 공통 성분을 포함한다. 따라서 fitted kernel은
$\mathcal A_*$ 자체가 아니다. Primary는 두 수신 contact의 차인 bipolar readout이며,
contact-mean은 reference sensitivity 진단이다.

## 2. Source lock

`[경험식/원천 고정]`

- Dataset: OpenNeuro `ds004080`, snapshot `1.2.4`, DOI
  `10.18112/openneuro.ds004080.v1.2.4`, CC0, BIDS 1.6.0.
- Official Git tree SHA: `c4fd7418883e33b024292468eb14da1649f51aae`; 1,182 entries,
  74 subjects, 117 BrainVision recordings.
- 112 recordings are 2048 Hz and 5 are 512 Hz. 시간은 반드시 run별 JSON sampling rate로
  계산한다.
- 모든 117 recording의 `.eeg/.vhdr/.vmrk` annex pointer, actual header/marker SHA-256,
  S3 Content-Length/ETag/VersionId, first-64-byte HTTP 206 response, float32 multiplexed byte
  geometry, channels/events/JSON 정합성을 통과했다.
- 117/117 event tables에서 `sample_start = round(onset × fs)`인 zero-based crosswalk가
  성립한다.
- 좌표 sidecar의 실제 표기는 117/117 `fsaverage`, mm, MNI305-derived surface
  transformation이다. README의 MNI152 표현보다 run sidecar를 우선하며 이 좌표를
  `fsaverage/MNI305-derived proxy`라고 부른다.
- 자극은 모두 0.2 Hz, 1 ms monophasic이고 선택 pool의 전류는 4/6/7/8 mA다. 원 논문
  acquisition protocol에 따라 27명은 5 pulse 뒤 polarity를 뒤집었다. `A-B`와 `B-A`를
  같은 해부학적 bipolar source로 묶되 각 trial의 원 orientation을 보존한다.
- manual global artifact와 겹치는 trial, out-of-bounds trial, bad/non-ECoG contact,
  좌표 없음, `silicon=yes`, `soz=yes` source/receiver, source와 contact를 공유하는 receiver,
  center distance <15 mm를 endpoint 전에 제외했다. metadata-valid source 3,213개는 clean
  trial ≥10, receiver ≥6을 만족한다. 실제 experiment selection은 receiver ≥16인 3,202개만
  허용하고, 각 subject가 그중 source ≥8을 가져 74명 전부가 endpoint-eligible이다.

고정 산출물은 다음과 같다.

| 산출물 | SHA-256 / 값 |
|---|---|
| metadata audit code | `cffcc8e7e0fc3d82ef28ff9403b6a774b52bff6c95ae60faa911698f1ad404ca` |
| metadata audit receipt | `d96d716e8c1c5662d4e46af311f26a645201ef7a075f52681c21d7067db55ba8` |
| metadata source manifest | `9ed8cb9d7a12cf293f8a899aa9a04de7951109b0fad0505e08ebe93f9e11b3c3` |
| eligible source count | 3,213 |
| split builder code | `502e62de85bdaf1d1dca832ce2e50551f974e753c832b60dd42fb5469c972f9b` |
| endpoint-blind split manifest | `d4b03a984f03529c870df6d2c62034443b08611ddacd3cfe4244067bb5ff96f7` |
| split receipt | `ea6e39bb94245fae2d4e2f96d60681024f7ac8b2354f1fb4f6cb1d959ed8ee68` |

두 manifest와 receipt 모두 `scientific_endpoint_opened=false`에서 생성됐다.

## 3. 피험자·source·receiver·trial 분할

### 3.1 피험자 단계

74명을 `(age, participant_id)`로 정렬해 크기 `19/19/18/18`의 연속 age strata로 나눈다.
각 stratum 안에서

```text
SHA256("BA-OBS-DISC2::ds004080-v1.2.4::participant::<participant_id>")
```

순으로 배정한다.

| 단계 | 피험자 | stratum별 | source | 평가 edge | 역할 |
|---|---:|---:|---:|---:|---|
| D0 | 24 | 6/6/6/6 | 192 | 2,304 | 후보 구조 선택 |
| D1 | 8 | 2/2/2/2 | 64 | 768 | small fast-kill |
| D2 | 12 | 3/3/3/3 | 96 | 1,152 | medium gate |
| D3 | 30 | 8/8/7/7 | 240 | 2,880 | final one-shot |

한 사람의 모든 session/run/source/receiver/trial은 한 단계에만 속한다. D0은 6 folds이며
각 fold는 네 age strata에서 한 명씩, 총 4명을 test로 둔다. fold 목록도 split manifest에
고정돼 있다.

### 3.2 피험자 내부 선택

각 피험자에서 receiver ≥16인 source를 source/site/record ID의 salted hash로 정렬해 정확히
8개를 사용한다. 각 source의 receiver를 거리순 네 strata로 나눈 뒤 stratum 안의 salted
hash로 1개 anchor와 3개 evaluation receiver를 고른다. 따라서 source마다 anchor 4개,
평가 12개이고 두 집합은 완전히 분리된다.

각 source에서 event 순서가 빠른 clean 10 trials만 사용한다. 모든 source에 대해
`temporal_repeatability_halves` A/B를 정확히 5/5로 만든다. orientation이 하나면 event
even/odd temporal halves일 뿐 polarity-balanced라고 부르지 않는다. 두 orientation이 각각
5회면 각 temporal half에 두 orientation을 3/2와 2/3으로 배분하고, 별도로 원 orientation
5회 대 반대 orientation 5회의 `orientation_groups`를 보존한다. Primary endpoint는 10개
전체 평균이며 두 분할은 apparatus 진단에만 쓴다.

endpoint-blind split에서 orientation source 수는 D0 `single/two=144/48`, D1 `32/32`,
D2 `49/47`, D3 `152/88`이다. 두 orientation source를 가진 participant 수는 각 단계
`6/4/6/11`이다.

## 4. 무차원 관측량

trial $e$, contact $c$의 run별 물리시간 $\tau=n/f_s$에서

$$
V'_{iec}(\tau)=V_{iec}(\tau)
-\operatorname{median}_{-1\le\tau\le-0.1}V_{iec}(\tau)
$$

로 baseline을 제거한다. receiver pair $d=(c_1,c_2)$의 bipolar trial과 robust scale은

$$
D_{iesd}(\tau)=V'_{iec_1}(\tau)-V'_{iec_2}(\tau),
$$

$$
\sigma_{isd}=1.4826\,\operatorname{MAD}
\{D_{iesd}(\tau):e=1,\ldots,10,\ -1\le\tau\le-0.1\}.
$$

$\bar D_{isd}=10^{-1}\sum_eD_{iesd}$라 하고, 고정 bin

$$
[10,18),[18,30),[30,50),[50,80),[80,120]\ {\rm ms}
$$

에서

$$
E^{\rm bip}_{isdk}
=\left[
\frac1{|I_k|}\sum_{\tau\in I_k}
\left(\frac{\bar D_{isd}(\tau)}{\sigma_{isd}}\right)^2
\right]^{1/2},
\qquad
z_{isdk}=\log(E^{\rm bip}_{isdk}+10^{-6})
$$

를 쓴다. bin 대표시간은 `14/24/40/65/100 ms`다. $E$, floor, $z$는 무차원이다.
512 Hz와 2048 Hz 모두 실제 sample time이 bin에 포함되는지로 계산하며 빈 bin은
`APPARATUS_STOP`이다. matched prestimulus control은 같은 bin 폭을 `-300 ms` 이동한
`[-290,-180] ms` 구간에서 계산한다. `-300 ms`는 두 sampling grid에서 정수 sample 이동이
아니므로 물리시간 경계를 우선하며, post/pre sample 수가 일부 bin에서 한 개 다른 것은
허용한다. 고정 기대 개수는 512 Hz에서 post `4/6/10/15/21`, pre `4/6/10/16/20`이고,
2048 Hz에서 post `16/25/41/61/82`, pre `16/25/40/62/82`다.

기하·시간·전류 기록·나이는

$$
x_k=\frac{t_k}{50\,{\rm ms}},\qquad
\Delta_{isd}=\frac{X_{id}-X_{is}}{50\,{\rm mm}},\qquad
r_{isd}=\|\Delta_{isd}\|,
$$

$$
\iota_{is}=\log\frac{I_{is}}{8\,{\rm mA}},
\qquad
\widetilde A_i=\frac{A_i-20\,{\rm yr}}{20\,{\rm yr}}
$$

로 무차원화한다. 모든 `log`와 아래 `exp`의 인자는 무차원이다. 다만 current는 source마다
상수이고 아래의 자유 source offset과 정확히 겹치므로 fitted 공통항에는 넣지 않는다. 값과
정규화는 provenance 및 후속 별도 계층모형을 위해서만 보존한다.

## 5. 공통 nuisance와 후보식

### 5.1 공통 시간·나이 항과 source offset

모든 후보가 정확히 같은

$$
T_i^\star(x)=
\beta_1\log x+\beta_2x
+\gamma_1\widetilde A_i\log x+\gamma_2\widetilde A_ix
$$

를 가진다. 나이 항은 연령에 따른 시간 profile 변화가 geometry 항으로 새는 것을 줄이기
위한 nuisance이며 의식 발달식이 아니다. 자유 source offset $u_{is}$가 있으므로 global
intercept $\beta_0$와 source-constant current term $\gamma_I\iota_{is}$는 정확히 식별되지
않는다. 실제로 source-constant $c$에 대해

$$
\widehat u_{is}(\mu+c)=\widehat u_{is}(\mu)-c
$$

여서 query prediction $\mu+\widehat u$가 불변이다. 따라서 두 항은 후보에서 제거하고 source
level과 current-dependent amplitude는 $u_{is}$가 흡수한다. 이 run은 current effect를
추정하지 않는다.

새 피험자의 source gain은 evaluation을 보지 않고 anchor 4개에서만 profile한다. 후보 $m$과
global parameter $\theta$에 대해

$$
\widehat u^{(m)}_{is}(\theta)
=\arg\min_{u\in[-20,20]}\sum_{d\in A_{is},k}
\rho_{0.5}\!\left[z_{isdk}-\mu_m(x_k,\Delta_{isd};\theta)-u\right]
$$

다. $\psi_{0.5}(e)=\operatorname{clip}(e,-0.5,0.5)$로 두고
$\sum_{d,k}\psi_{0.5}(z-\mu-u)=0$을 고정 bracket `[-20,20]`에서 푼다. score가 연속
piecewise-linear이므로 20개 anchor residual의 정확한 breakpoints $r_j\pm0.5$를 정렬해 영점
구간을 찾고, 구간이면 양 끝의 midpoint를 택한다. bracket 밖 root, nonfinite 값, 또는 score
절댓값이 $10^{-10}$보다 크면 `PROFILE_STOP`이다. 모든 후보는 동일한 4 anchor, 동일한 1개
scalar nuisance, 동일한 loss를 쓴다.

### 5.2 동결 후보군

`S0` geometry-free baseline:

$$
\mu_0=T_i^\star(x).
$$

`SC` isotropic cable:

$$
\mu_{\rm C}=T_i^\star(x)-a r,\qquad a\ge0.
$$

determinant-one diagonal proxy를

$$
G(g_x,g_y)=\operatorname{diag}(e^{g_x},e^{g_y},e^{-g_x-g_y}),
\qquad
d_G=\sqrt{\Delta^\top G\Delta},
$$

로 두면 `SAC`는

$$
\mu_{\rm AC}=T_i^\star(x)-a d_G,
\qquad a\ge0,\quad g_x,g_y\in[-1,1]
$$

다. `SH0` isotropic heat coupling과 `SHA0` anisotropic heat coupling은

$$
\mu_{\rm H0}=T_i^\star(x)-\kappa\frac{r^2}{x},
\qquad \kappa\ge0,
$$

$$
\mu_{\rm HA0}=T_i^\star(x)-\kappa\frac{d_G^2}{x},
\qquad \kappa\ge0,\quad g_x,g_y\in[-1,1].
$$

이다. $\det G=1$이므로 전체 거리척도와 $a/\kappa$의 중복을 막는다. `S0⊂SC⊂SAC`와
`S0⊂SH0⊂SHA0`다. free $q$, delay, anomalous free $p$, biexponential, source-specific
attenuation random slope는 DISC1의 boundary 실패 또는 이번 anchor 수에서의 식별 불가 때문에
후보에서 제외한다.

## 6. 적합, D0 선택, 수치 식별성

Huber loss는

$$
\rho_{0.5}(e)=
\begin{cases}
e^2/2,&|e|\le0.5,\\
0.5(|e|-0.25),&|e|>0.5
\end{cases}
$$

다. training subject의 global $\theta$는 각 source anchor에서 $u_{is}$를 profile한 뒤 12개
evaluation receiver의 source-equal, subject-equal loss를 최소화한다. Test subject에서는
global $\theta$를 고정하고 anchor로 $u_{is}$만 얻어 evaluation을 예측한다.

- $\beta_1,\beta_2,\gamma_1,\gamma_2\in[-20,20]$, $a,\kappa\in[0,20]$,
  $g_x,g_y\in[-1,1]$.
- 각 training set에서 query response와 공통 시간 design을 source 안에서 각각 중심화한 뒤
  rank-4 least-squares common start를 하나 계산한다. 이는 training 초기값일 뿐 score나
  held-out anchor/query에는 쓰지 않는다. `S0`는 이 start, 그 `+0.1/-0.1` perturbation, 0의
  네 starts를 쓴다. `SC/SH0`는 같은 common start에서 attenuation을
  `0.1/0.5/1/2/5`로 둔 다섯 starts를 쓴다. `SAC/SHA0`는 같은 common start에서 attenuation
  `0.1/1/5`와
  $(g_x,g_y)\in\{-0.5,0,0.5\}^2$를 교차한 27 deterministic starts를 쓴다.
- 이 starts는 basin search다. finite objective가 가장 작은 해를 normalized parameter
  좌표에서 그대로, 그리고 교대부호 방향으로 $\pm10^{-3}$ 이동한 세 점에서 다시 local
  optimize한다. 최종 수치 gate와 아래 agreement는 세 `best_basin_confirmation` 해 모두에
  적용하고, basin-search의 모든 목적값과 파라미터도 receipt에 보존한다.
- 각 L-BFGS-B local run은 `maxiter=300`, `maxfun=6000`, `ftol=10^{-12}`,
  `gtol=10^{-8}`, `maxls=80`으로 고정한다. 상한 안에 수렴하지 못한 start는 admissible로
  세지 않으며, 세 confirmation 중 하나라도 수렴하지 않으면 해당 candidate를 즉시 죽인다.
- 모든 fit과 prediction은 finite여야 한다. 수치 Jacobian은 normalized parameter coordinate에서
  $h=10^{-5}$ 중심차분을 쓰고, 각 차분점마다 anchor profile을 다시 계산한 query prediction
  $P=\mu+\widehat u$로 만든다. SVD relative tolerance $10^{-8}$에서 full rank이고 condition
  number $\le10^7$이어야 한다.
- $a/\kappa$가 $10^{-4}$ 이하이면 geometry-null collapse로, upper bound의 $10^{-5}$ 안이면
  upper-bound failure로 친다. $g_x/g_y$가 bound의 $10^{-5}$ 안이면 anisotropy 미식별이다.
- 세 admissible confirmation 해의 loss 상대차 $\le2\times10^{-4}$, prediction RMS 차 $\le5\times10^{-2}$을
  요구한다.
- 각 fit receipt에는 candidate별 anchor-profile vector SHA-256과 normalized-Jacobian singular
  values를 남긴다.

D0은 6-fold subject-blocked CV다. 후보는 6 folds 모두 수치 gate를 통과하고, subject-equal
평균 bipolar 상대개선이 최소 `0.005`이며, 6 folds 중 최소 4개에서 S0보다 좋아야 생존한다. 최대
개선 후보를 고르되 차이가 0.005 이내면 geometry 자유계수가 적은 식, 다음 lexical name을
고른다. D0에서 생존자가 없으면 `D0_NO_GEOMETRIC_EQUATION_SURVIVED`로 종료한다.

## 7. 작은→중간→최종 sequential gate

현재 단계의 query는 global parameter와 anchor nuisance 적합에 절대 쓰지 않는다. D1은 D0만,
D2는 D0+D1만, D3는 D0+D1+D2만 training으로 쓴다. 앞 단계가 통과한 뒤에만 그 query를 다음
training에 포함한다. 식 구조, bounds, bin, floor, source/receiver/trial, loss, threshold는 D0
후 바꾸지 않는다.

source loss 개선과 participant 개선은

$$
\Delta_{is}=\mathcal L_{S0,is}-\mathcal L_{W,is},
\qquad
\Delta_i=\frac18\sum_{s=1}^{8}\Delta_{is},
\qquad
\bar\Delta=\frac1N\sum_i\Delta_i
$$

다. pair나 bin을 iid 표본으로 세지 않는다. primary bootstrap은 participant만 equal-weight로
8,192회 재표본하며 source bootstrap은 진단일 뿐이다. geometry permutation은 participant와
source, 시간값, response, anchor를 고정하고 evaluation receiver의 전체 coordinate tuple을
source 안에서 함께 섞는다.

| 단계 | permutation | 통과 조건 | 실패 시 |
|---|---:|---|---|
| D1, 8명 | 511 | $\bar\Delta>0$, 양의 $\Delta_i\ge6/8$, $p_{geom}\le0.20$ | 즉시 kill; D2/D3 미개봉 |
| D2, 12명 | 1,023 | one-sided 80% participant-bootstrap LCB $>0$, 양의 $\Delta_i\ge8/12$, $p_{geom}\le0.10$ | kill; D3 미개봉 |
| D3, 30명 | 4,095 | one-sided 97.5% LCB $>0$, 양의 $\Delta_i\ge20/30$, $p_{geom}\le0.025$ | NOT_CONFIRMED |

D1/D2는 빠른 제거 gate이지 확인 증거가 아니다. D3만 final generalization이다.

## 8. Apparatus와 adverse controls

실제 D0 후보 적합 전에 다음을 모두 통과해야 한다.

1. 선택된 1,920 D0 trial ranges가 version-locked HTTP 206, exact Content-Range/ETag/
   VersionId, expected byte count, finite little-endian float32 decode를 만족한다.
2. 192 sources × 16 receivers × 5 bins가 정의되고 baseline scale이 finite positive다.
3. 모든 192 D0 sources의 5/5 temporal-repeatability halves에서 pooled bipolar Spearman
   $\rho\ge0.30$.
4. D0의 사전 고정된 two-orientation 48 sources, 6 participants에서 orientation-specific
   5-vs-5 pooled bipolar Spearman $\rho\ge0.20$. single-orientation 144 sources는 이 gate에서
   제외하고 `ORIENTATION_ABSENT`로 기록한다. two-orientation source가 32개 또는 participant
   4명 미만이면 `POLARITY_APPARATUS_INSUFFICIENT`다.
5. median poststimulus bipolar energy / matched prestimulus energy $\ge1.25$.
6. 512/2048 Hz synthetic byte geometry, off-by-one, wrong hash/header/range가 fail-closed다.
7. analytic cable/heat fixture에서 generating family가 S0보다 낫고, geometry-null fixture에서
   D0 false selection은 64회 중 $\le2$다. 이 fixture는 확인 추론이 아니라 endpoint를 열기 전
   family-wise selector smoke gate이며, 실제 D0와 같은 fit/6-fold 선택 코드를 쓴다.
   v1 null salt에서 기존 `improvement>0` 규칙은 `4/64` false selection으로 실패했다
   (`pre-d0-fixture-receipt-v1-failed.json`, SHA-256
   `b32139e1bd10bf8ecfe1d128a202cd916c37fc25d25abaad54d04ea4f899fe30`). 네 오탐은 모두
   `SH0`이고 개선은 `0.0000614–0.004934`였으므로 마지막 사전 revision에서 최소개선을
   `0.005`로 고정했다. 이 문턱을 보지 않은 v2 salt 64회에서 다시 검증해야 하며 v1을 성공으로
   덮어쓰지 않는다.
8. anchor/evaluation leakage, subject-stage leakage, pair-iid bootstrap이 있으면 즉시 stop한다.

Final pass에는 D3 bipolar gate와 함께 matched prestimulus endpoint가 같은 D3 gate를 통과하지
않아야 한다. prestimulus도 통과하면 `NEGATIVE_CONTROL_FAIL / NOT_CONFIRMED`다. Contact-mean은
진단이며 bipolar를 대체하지 않는다. bipolar만 통과하면 `REFERENCE_SENSITIVE`, 둘 다 통과하면
`REFERENCE_CONCORDANT`를 덧붙인다.

## 9. 필수 계약 필드

- **BIO_STARTING_MECHANISM:** human ECoG의 1 ms, 0.2 Hz, 4–8 mA monophasic SPES에 대한
  막 capacitance·전도·시냅스가 섞인 짧은 전기적 response; 비선형 기억계의 국소 선형화.
- **CE_DELTA:** 한 환자 pair 보간에서 끝내지 않고, 74명의 raw waveform을 patient-disjoint
  D0/D1/D2/D3로 나눠 cable/heat/anisotropy 후보를 실제 새로운 환자에게 순차 예측한다.
- **MEASUREMENT_MODEL:** $C_{ref}R e^{-tC^{-1}A}C^{-1}B$ + stimulation artifact + common
  reference/volume-conduction + noise; bipolar primary, contact-mean diagnostic.
- **DATA_PROVENANCE:** OpenNeuro `ds004080` v1.2.4, tree SHA, 117 annex/S3 identities,
  metadata source manifest SHA, zero-based event crosswalk.
- **DATA_SPLIT:** participant-disjoint `24/8/12/30`; subject당 8 source, source당 4 anchor +
  12 evaluation, clean trials 10; split manifest SHA 고정.
- **OBSERVABLES:** dimensionless five-bin bipolar RMS energy, contact-mean, trial-half
  repeatability, prestimulus matched control, participant-equal Huber-loss improvement,
  participant bootstrap, within-source geometry permutation.
- **RESIDUAL_RULE:** profiled anchor-only source intercept + Huber log-energy residual;
  source-equal then participant-equal; pair/bin iid inference 금지.
- **FALSIFIER:** apparatus 실패, D0 생존식 없음, D1/D2 gate 실패, D3 bipolar gate 실패,
  또는 D3 prestimulus negative-control 통과면 해당 식을 확인하지 않는다.
- **MATCHED_CONTROLS:** S0 with identical nuisance, bipolar/contact-mean, post/prestimulus,
  isotropic/anisotropic, cable/heat, within-source coordinate-tuple permutation.
- **MODEL_SELECTION:** 구조 선택은 D0 6-fold CV에서만; D1 이후 numerical refit만 허용.
- **REVISION_TRIGGER:** 실패 stage를 보고 식/window/threshold를 바꾸려면 새 run과 아직
  쓰지 않은 외부 subject dataset이 필요하다. 이 run의 뒤 stage 재사용 금지.
- **CLAIM_CEILING:** MULTI_SUBJECT_HUMAN_SPES_CCEP / PATIENT-DISJOINT_HELD-OUT_OBSERVED_KERNEL_PREDICTION / FSAVERAGE-MNI305-DERIVED_GEOMETRY_PROXY_ONLY / NO_BIOLOGICAL_METRIC_OR_GEODESIC_IDENTIFICATION / NO_INFINITE_DIMENSION_OR_CONSCIOUSNESS_SELF_HIPPOCAMPUS_AGI_VALIDATION.

## 10. 불가역 실행 순서

1. contract → sources/math/routes lanes → independent status audit;
2. dimensionless/fixture/range-parser focused tests;
3. D0 ranges와 endpoint를 한 번 열어 apparatus와 5식 선택;
4. winner가 있을 때만 D1; 통과할 때만 D2; 통과할 때만 D3;
5. stable-snapshot audit → validation/final report → ledger → 논문형 README.

raw byte payload는 Git에 쓰지 않는다. 각 range는 memory에서 decode하고 source identity,
requested byte interval, payload SHA-256, QC, endpoint receipt만 남긴다. 각 단계 receipt는
contract/source/split/code SHA-256과 이전 단계 receipt SHA-256을 연결하며, 미개봉 단계 receipt의
부재가 barrier 증거다.
