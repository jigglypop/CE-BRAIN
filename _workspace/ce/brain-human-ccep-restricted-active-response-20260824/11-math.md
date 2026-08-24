# BA-OBS-ID3 mathematics lane — 제한된 CCEP 상호성의 조건부 반증식

Status: COMPLETE

## 1. 무엇을 시험하며 무엇을 시험하지 않는가

BA-OBS-ID2에서 복원되는 것은 complete quadratic query가 주어진 self-adjoint positive
operator $M=G^{-1}$다. 이번 CCEP 자료의 finite observed response는

$$
A_{r\leftarrow s}
=\mathcal N_r\mathcal M
\left(C_{\rm ref}R_r[H_s*u_s]+a_{rs}+\eta_{rs}\right)
$$

꼴이다. 여기서 $\mathcal M$은 early-window maximum magnitude, $\mathcal N_r$은
baseline normalization이다. 둘 다 원 neural operator의 matrix coefficient를 그대로
반환하지 않는다. 그러므로

$$
P1:\quad A_{r\leftarrow s}=A_{s\leftarrow r}
$$

는 BA-OBS-ID2의 정리가 아니라 aligned input/readout, equal gain, fixed reference와
short-window response를 추가로 채택한 **모델 선택 공리이자 naive observed-magnitude
proxy**다. P1의 실패는 이 직접 대응만 기각한다. P1의 비기각은 $M$, $G$, 차원 또는
의식을 확인하지 않는다.

## 2. Finite allocation의 독립 재계산

동결한 24 sites에서 가능한 unordered pair는

$$
\binom{24}{2}=276
$$

개다. Shared contact 또는 midpoint distance $<15\,\mathrm{mm}$인 31개를 제외하면
245개가 남고, retained minimum distance는 $15.3912\,\mathrm{mm}$다. Hash input의
$(a,b)$를 frozen site list에서 $\operatorname{index}(a)<\operatorname{index}(b)$인 순서로
고정하면 calibration/development/confirmation은 정확히 151/42/52다.

이 순서를 lexical sort로 잘못 바꾸면 150/46/49가 된다. 따라서 label 자체만으로
"정렬"한다고 쓰는 것은 P0 재현 오류였고, 계약은 list-index order와 lexical-sort 금지를
명시하도록 수정됐다.

## 3. 기존 raw ratio의 이분산 반례

각 방향의 true reciprocal response가 같은 $A>0$이고 half estimator noise의 표준편차가
$\sigma_1,\sigma_2$라고 하자. Small-noise Gaussian 근사에서 normalized disagreement의
분모를 $2A$로 둘 수 있다. 같은 방향 두 half의 차이는 표준편차
$\sqrt2\sigma_i$, 서로 다른 방향의 차이는 $\sqrt{\sigma_1^2+\sigma_2^2}$다. 따라서

$$
\frac{\mathbb E[v]}{\mathbb E[u]}
\approx
\frac{\sqrt2\sqrt{\sigma_1^2+\sigma_2^2}}
{\sigma_1+\sigma_2}.
$$

$\sigma_1=\sigma_2$이면 1이지만 scale ratio가 커지면 $\sqrt2$에 접근한다. 즉 true
P1에서도 기존 threshold 1.25를 넘을 수 있다. Baseline-z, nonlinear maximum과 서로
다른 site별 trial count가 실제로 이분산성을 만든다. 그러므로 raw $R>1.25$나 iid
pair-bootstrap interval만으로 P1을 기각하는 규칙은 P0 실패다.

## 4. 방향별 noise를 보존한 restricted null

각 site $s$, half $h$, resample $b$에서 실제 trial 수만큼 replacement draw를 하고 같은
index를 그 site의 모든 receiver에 공유한다. 이 규칙은 source trial이 공유되어 생기는
edge covariance를 보존하지만, 서로 다른 site나 환자의 독립 표본을 새로 만들지는 않는다.
매 draw마다 baseline correction, baseline SD, early maximum과 readout을 원 함수로 다시
계산한다.

Raw $A_e^{(h,m)}>0$를 확인한 뒤, 모두 무차원인

$$
L_e^{(h,m)}=\log(A_e^{(h,m)}+\epsilon),
\qquad \epsilon=10^{-12}
$$

를 쓴다. Bootstrap log residual에서 bootstrap 평균을 빼면

$$
\frac1B\sum_{b=1}^B e_e^{(h,m,b)}=0
$$

이 정확히 성립한다. Pair $q=\{r,s\}$의 네 방향·half log response 평균
$\bar L_q^{(m)}$를 공통 location으로 강제하고 각 방향·half residual을 다시 더하면

$$
L_{0,e}^{(h,m,b)}=\bar L_q^{(m)}+e_e^{(h,m,b)}
$$

이다. 이 null에서는 reciprocal location은 같지만 residual scale, skew, tail, trial 수와
source-shared covariance는 방향별로 유지된다. 따라서 단순 $\sigma_1\ne\sigma_2$가 만든
큰 raw $R$은 $R_0$ tail에도 나타나며 자동 기각 사유가 되지 않는다.

Conditional tail rank

$$
p_R^{(m)}=
\frac{1+\sum_{b=1}^{8192}
\mathbf 1\{R_{0,b}^{(m)}\ge R_{\rm obs}^{(m)}\}}
{8193}
$$

에는 zero p-value가 없다. $R>1.25$와 $p_R\le0.025$를 동시에 요구하는 것은 practical
raw discrepancy와 restricted-null incompatibility를 분리한다. 두 readout 모두 이
조건을 만족해야 reference-robust proxy refutation으로 분류한다. 두 test의 독립성은
가정하지 않는다.

## 5. 이 tail area의 통계적 지위

52 pairs는 24 nodes와 stimulation trials를 공유하며 환자는 한 명이다. 따라서 pair를
iid 표본으로 보는 population bootstrap, 인간 뇌 network에 대한 95% confidence interval,
population p-value는 성립하지 않는다. $p_R$의 허용된 해석은 다음뿐이다.

> 동결된 한 피험자·24 sites·52 confirmation pairs에서, 방향별/half별 경험적 trial
> residual을 유지하고 reciprocal log-location만 강제한 restricted null에 대한
> conditional resampling tail area.

Half당 5--9 trials인 작은 표본에서 residual bootstrap은 근사다. 그래서 이 수학식만으로
real verdict를 열지 않고, 실제 trial count와 $1{:}16$ noise 이분산을 넣은 256-seed
false-positive fixture와 $\log(1.6)$ directed-power fixture를 선행 gate로 둔다. 이 gate도
뇌에 관한 증거가 아니라 frozen 구현의 calibration·power sanity check다.

## 6. 무차원성과 단위 감사

| quantity | numerator unit | denominator/reference | status |
|---|---|---|---|
| $Z$, $A$, $P$ | $\mu\mathrm V$ | baseline $\sigma$ in $\mu\mathrm V$ | dimensionless |
| $d(x,y)$ | dimensionless | dimensionless sum + $10^{-12}$ | dimensionless |
| $u,v,R$ | dimensionless | dimensionless | dimensionless |
| $L=\log(A+10^{-12})$ | dimensionless | log argument dimensionless | admissible |
| $e,\bar L,R_0,p_R$ | dimensionless | dimensionless | dimensionless |
| Spearman $\rho$ | ranks | ranks | dimensionless |

Header resolution $0.1\,\mu\mathrm V$는 contact signal에 먼저 적용하고, bipolar는 같은
단위의 두 contact를 뺀 뒤 baseline SD로 나눈다. 같은 scalar resolution은 $Z$에서
상쇄되지만 decoder 단위 확인과 artifact receipt를 위해 명시적으로 적용한다.

## 7. Sample-coordinate 감사

Events 425개 모두에서

$$
\texttt{sample\_start}=\operatorname{round}(2048\,t_{\rm onset})
$$

이다. 반면 VMRK position과 `sample_start`의 차이는 201 events에서 0, 224 events에서
1이다. BrainVision marker는 1-based이므로 같은 export의 `.eeg` raw index는
`VMRK position - 1`로 고정한다. 따라서 `raw_index-sample_start` expected multiset은
$\{-1\times201,0\times224\}$다. Hash, count 또는 이 crosswalk가 다르면 signal decode
전에 멈춰야 한다. 결과를 본 뒤 1-sample shift를 골라 쓰는 것은 금지한다.

## 8. 감사 결론과 잔여 한계

| issue | original severity | resolution | residual limit |
|---|---|---|---|
| Pair ordering ambiguity | P0 | frozen-list index order와 expected 151/42/52 고정 | 다른 dataset에는 새 split 필요 |
| Raw $R$ heteroscedastic false refutation | P0 | restricted-null tail + synthetic false-positive/power gate | small-trial bootstrap은 근사 |
| Missing coordinate/marker source lock | P1 | 두 SHA-256와 crosswalk STOP 추가 | public object 자체의 생물학적 품질과 별개 |
| iid-pair CI overclaim | P1 | CI 제거, conditional tail로 하향 | population inference 없음 |
| P1을 self-adjoint theorem처럼 읽는 위험 | P1 | naive magnitude proxy로 지위 고정 | $C_{\rm ref},R,H$ 비식별성 유지 |
| $1.25$, $0.025$, fixture cutoffs | P2 | signal 전 engineering thresholds 동결 | 보편적 type-I theorem이 아님 |

수정 뒤 구현 진입 판정은 `MATH_READY_FOR_INDEPENDENT_STATUS_AUDIT`이다. 이 판정은
fixture 또는 real data PASS를 뜻하지 않는다.
