# BA-SELF1-L3 수학 검산 — revision 2

Status: COMPLETE

Contract SHA-256: `2b08c0fd5eb69ae6f3d096a6542e248b6d2b69da985f90c7d06071e0690be50e`

A0 receipt SHA-256: `5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7`  
Manifest SHA-256: `4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061`

## 대상과 경계

검정 대상은 EEG의 whitening quotient에서 현재·자극·명시된 순서불변 path summary를 조건부로 했을 때 2차 antisymmetric area $A$가 $100$ ms 뒤 변화 예측을 개선하는지다. `[경험식]` 파일럿이며 자아·의식·무한차원 상태를 식별하지 않는다. 이 lane은 계약, A0 metadata/header receipt와 manifest hash만 읽었고 `.eeg` 신호값은 열지 않았다.

## 1. Quotient metric과 condition number

$$
W_d=\Lambda_d^{-1/2}Q_d^\mathsf T,qquad z=W_d\widetilde v,
$$

이므로 channel-space pullback은

$$
W_d^\mathsf TW_d=Q_d\Lambda_d^{-1}Q_d^\mathsf T,qquad
h^\mathsf TW_d^\mathsf TW_dh=\|W_dh\|_2^2\ge0.
$$

따라서 full channel space에서는 rank-$d$ PSD, $\mathbb R^{63}/\ker W_d$ quotient에서는 PD이며 retained coordinate metric $g_d=I_d$는 PD다. 개정 계약의 training-fold gate

$$
\lambda_{d,\min}/\lambda_{1,\max}\ge10^{-6},qquad
\kappa_d=\lambda_{1,\max}/\lambda_{d,\min}\le10^6
$$

는 $\lambda_{1,\max}>0$에서 동치다. spectrum/rank/$\kappa$ receipt 및 all-$d$ fail-closed가 있으므로 numerical-whitening P1은 닫혔다.

## 2. Area와 reverse adverse control

$\delta_j=\Delta z_{k-L+j}$이면

$$
A=\frac12\sum_{p<q}\delta_p\wedge\delta_q.
$$

역순 increment $\delta'_j=-\delta_{L+1-j}$로 reindexing하면 $A'=-A$다. 길이와 에너지는 보존된다. Reverse feature를 새로 ridge fit하면 $B_A\mapsto-B_A$가 sign을 흡수하고 L2 penalty도 불변이므로, frozen oriented coefficient에 only $-A$를 넣는 contract adverse control은 수학적으로 필요하고 정확하다.

## 3. Expanded baseline, predictor count, and session P0 closure

$M_0$에는 current state/derivative, start/end, length/energy, increment mean, covariance, coordinatewise central $m_3,m_4$, coordinatewise range, word, condition이 있다. 이 finite list가 모든 permutation-invariant statistic을 포괄하지는 않지만, previous baseline-scope P1은 명시한 comparison 범위에서 해소되었다.

word treatment dummy는 7, condition treatment dummy는 1, intercept는 1이다. $d=4$의 exact count는

$$
p_0=1+3d+2+d+\frac{d(d+1)}2+4d+7+1=53,
\qquad
p_1=p_0+\frac{d(d-1)}2=59<75.
$$

따라서 maximum design column은 59이고 minimum development session 75보다 작다. $A$는 scalar target당 6열, $d=4$ joint output에서 24 coefficient를 추가한다. Effective df는

$$
\operatorname{df}_\lambda=
\operatorname{tr}\{X(X^\mathsf TX+\lambda P)^{-1}X^\mathsf T\}
$$

로 별도 기록하며 intercept는 standardization/penalty에서 제외한다.

revision 1의 P0였던 session dummy는 $\psi_0$와 categorical coding에서 완전히 제거됐다. session은 split 및 bootstrap strata에만 남는다. 따라서 one-session training fold에서 session column이 all-zero/all-one이 되어 intercept와 공선·zero SD가 되던 반례는 더 이상 design matrix에 적용되지 않는다. word는 두 development session 모두 8 level이 A0 receipt에서 확인되고, task/rest condition은 각 selected trial pair에 함께 존재하므로 fixed treatment dummy가 train fold에서 unseen level이 되는 계약상 반례도 없다. zero-variance non-session predictor가 생기면 silent drop이 아니라 `APPARATUS_INVALID_DESIGN`으로 fail-closed한다. **session-dummy P0는 해소되었다.**

## 4. Causal filtering과 fold-locality

501-tap causal FIR은

$$
r_n=\sum_{j=0}^{500}h_jv_{n-j}
$$

이므로 future input을 사용하지 않는다. raw warm-up 500개는 full support에 충분하고, cutoff $45$ Hz는 decimated Nyquist $125$ Hz보다 작다. group delay $250/5000=0.05$ s는 stimulus-latency convention이지 future leakage가 아니다. Robust center/scale, PCA/whitening, predictor standardization, ridge coefficient는 each training session에서만 fit하고 held-out session에는 frozen apply한다. final transform은 two-development-session fit 후 confirmation에 동결된다. 이전 causal/leakage P1은 닫혔다.

## 5. Split, bootstrap, futility

C3 bootstrap은 original-onset block을 session-stratified resample하고 하나의 sampled $(session,block_id)$를 paired task/rest, $M_0/M_1$, oriented/reverse 및 20 fixed shuffle loss 전체에 공동 적용한다. Shuffle은 bootstrap마다 재생성하지 않는다. 따라서 paired uncertainty를 보존한다.

C1/C2는 QC failure, non-positive $G_{task}$, 또는 reverse/shuffle 우위일 때만 futility STOP하며 CI/success를 산출하지 않는다. 통과시 C3의 separate 175 trials만 한 번 final CI와 success 판정에 쓰고 C1/C2 loss를 합치지 않는다. 이로써 prior bootstrap/sequential-reporting P1은 닫혔다.

A0 receipt는 `signal_values_opened=false`, current contract linkage 및 `valid_event_total_539=true`, `split_arithmetic_446_plus_93=true`를 기록한다. 수식 독립 합산은

$$
8+24+32+132+25+50+175=446,qquad 446+93=539,
$$

로 receipt/manifest와 일치한다.

## 6. State-expansion no-go

$X_t=(z_t,(z_{t-a},u_{t-a})_{0\le a\le H})$로 확장하면 history predictor는 instantaneous state function이 된다. EEG observation이 non-injective이므로 latent state/history도 quotient까지만 식별된다. 따라서 positive result도 “self is a path”를 증명하지 않는다.

## 최종 판정

| 항목 | 판정 |
|---|---|
| whitening quotient PSD/PD 및 ratio/$\kappa$ | PASS |
| $A'=-A$와 reverse refit sign equivalence | PASS |
| expanded baseline, $p_1=59<75$, effective df | PASS |
| session dummy P0 | PASS — predictor/coding에서 제거됨 |
| causal FIR, decimation, fold-local transforms | PASS |
| paired bootstrap, futility-only C1/C2, C3-only final | PASS |
| A0/manifest arithmetic $539=446+93$ | PASS |
| state-expansion no-go and claim ceiling | PASS |

**P0/P1: 없음.** 이 수학 lane 기준으로는 audit gate 재감사가 가능하다. 이는 data result나 biological/self claim의 PASS가 아니라, source-locked contract가 구현 심사로 넘어갈 수 있다는 판정이다.
