# BA-OBS-DISC1 연구 계약 — 실제 인간 CCEP 전기·기하 response kernel 발견

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-human-ccep-restricted-active-response-20260824`

## 0. 질문과 판본 경계

이 run은 선행 BA-OBS-ID3가 endpoint를 계산·직렬화하지 않았던 OpenNeuro
`ds003708`의 calibration 151 unordered pairs만 사용한다. 원시 BrainVision 파일은
multiplexed이므로 그 byte range 안에 모든 receiver channel이 함께 있었지만, 이 151쌍의
response endpoint와 아래 식의 적합도는 아직 계산되지 않았다. 따라서 이 pool을
`ENDPOINT_BLIND / RAW_BYTES_PREVIOUSLY_TRAVERSED`라고 부르며 “완전히 보지 않은 새 데이터”라고
과장하지 않는다.

질문은 다음 하나다.

> 한 환자의 실제 전기자극 CCEP에서, 전기 회로의 국소 선형화로부터 나온 저차
> Green/heat/cable kernel이 단순 시간곡선보다 아직 열지 않은 receiver-pair의 반응 에너지를
> 더 잘 예측하는가? 그렇다면 어떤 제한된 식이 살아남는가?

이 run은 식의 **발견·빠른 제거·중간 검증·최종 검증**을 순서대로 수행한다. 뇌의 전체
Riemannian metric, 무한차원 상태공간, 의식, 자아 또는 AGI를 검증하지 않는다.

## 1. 생물학적 출발식과 관측식

짧은 시간창에서 막·시냅스 전류를 operating point 주위로 선형화하면 유한 관측 절단에서

$$
C\dot v(t)=-\bigl(L_g+J_{\rm ion}\bigr)v(t)+B u(t)
$$

를 출발식으로 둘 수 있다. $C$는 capacitance, $L_g$는 conductance/network Laplacian,
$J_{\rm ion}$은 선형화된 막·시냅스 항이다. 고정 계수라는 가정은 이번 짧은 CCEP 창의
국소 근사일 뿐이다. 충격 입력에 대한 형식해는

$$
v(t)=\exp[-C^{-1}(L_g+J_{\rm ion})t]C^{-1}Bq
$$

이고 실제 전극이 읽는 값은

$$
y^{\rm obs}(t)=C_{\rm ref}R v(t)+a_{\rm stim}(t)+c_{\rm common}(t)+\eta(t)
$$

다. $C_{\rm ref}R$은 전극·체적전도·reference montage를, $a_{\rm stim}$은 자극 artifact를,
$c_{\rm common}$은 공통 성분을 포함한다. 따라서 fitted kernel은 neural operator 그 자체가
아니라 이 측정사슬을 통과한 **observed response kernel**이다.

## 2. Source lock과 대상

- Dataset: OpenNeuro `ds003708`, derivative v1.0.2, `sub-01/ses-ieeg01`, task CCEP run 01.
- Acquisition subset: status `good`, `6.0 mA`, 선행 계약의 24 bipolar stimulation/receiver sites.
- Signal object: 2,899,637,088-byte BrainVision float32 object.
- ETag: `9832a1868bff527620c3cec91df4bb81-3`.
- VersionId: `ekxCFJH.NE2DhaUDkQ_Nc0iIxeHeLgF4`.
- Sampling: 2048 Hz; 89 channels; 255 eligible stimulation epochs.
- Metadata SHA-256와 BrainVision marker/event off-by-one crosswalk은 선행 BA-OBS-ID3의
  source lock을 그대로 재검증한다. 하나라도 다르면 `SOURCE_IDENTITY_STOP`이다.

환자는 임상적으로 electrode가 삽입된 단일 epilepsy subject다. MNI 좌표는 실제 axonal
geodesic이 아니라 관측 가능한 거리 대리변수다.

## 3. Endpoint-blind 24→48→39→40 split

선행 calibration 151 unordered pairs만 취한다. 공유 contact가 있거나 bipolar-center MNI
거리가 15 mm 미만인 pair는 선행 계약에서 이미 제외되었다. 분할은 signal을 읽지 않고
MNI 거리와 pair 이름으로만 만든다.

1. 151 pairs를 bipolar-center Euclidean distance 순으로 정렬해 크기
   `38/38/38/37`의 네 contiguous distance strata로 나눈다.
2. 각 stratum 안에서

   ```text
   SHA256("BA-OBS-DISC1::ds003708-v1.0.2::<site-a>::<site-b>")
   ```

   digest의 lexicographic order로 정렬한다. `site-a/site-b`는 선행 24-site list index
   순서를 따른다.
3. 각 stratum에서 D0에 `6/6/6/6`, D1에 `12/12/12/12`, D2에 `10/10/10/9`,
   D3에 남은 `10/10/10/10`을 배정한다.
4. 한 unordered pair의 두 방향은 항상 같은 stage다.

동결된 manifest SHA-256은
`16bcdeb0c86b5fb7894ad6c766d1ef390e36b040e47d70b0d38ec953e04edb42`다.
Split-list SHA-256은 다음과 같다.

| stage | pairs | split-list SHA-256 | MNI distance min/median/max (mm) |
|---|---:|---|---|
| D0 discovery | 24 | `0fbddb902c6fa5cfa3e50aed4ba4e4f4f3b1f64c1241cc75a3bbb88775fbdb13` | 15.551 / 37.097 / 72.784 |
| D1 fast-kill | 48 | `c172ca78a7b36776cf8f79879a846af61945717afce1f30cf77efe0b88406751` | 16.357 / 35.613 / 78.317 |
| D2 intermediate | 39 | `4c82cc45b0b2b51e4e8882a94cd9812811886b650045d4ada86d214bf4b1a5a6` | 16.517 / 36.132 / 66.876 |
| D3 final holdout | 40 | `340b36c86fe61dd35d55f5cc31057b6db1aa183cceaafd5f19d3a6d92d11b2c3` | 15.391 / 36.203 / 74.366 |

D0만 먼저 계산한다. D1은 D0 winner가 존재할 때, D2는 D1 gate가 통과할 때, D3는 D2
gate가 통과할 때만 각각 한 번 연다. 실패한 stage 뒤의 endpoint를 계산·직렬화하지 않는다.

## 4. Trial half와 무차원 waveform energy

각 stimulation site의 good trials을 onset 순으로 놓고 even trial을 half A, odd trial을 half
B로 둔다. Trial마다 $[-500,-5]$ ms baseline mean을 뺀다. 첫 10 ms는 모든 endpoint에서
제외한다.

고정 time bins와 대표시간은 다음과 같다.

| bin | interval (ms) | $t_k$ (ms) |
|---|---:|---:|
| 0 | [10,18) | 14 |
| 1 | [18,30) | 24 |
| 2 | [30,50) | 40 |
| 3 | [50,80) | 65 |
| 4 | [80,120] | 100 |

Receiver pair $r=(c_1,c_2)$, source $s$, half $h$에서 contact baseline scale
$\sigma_{csh}$와 bipolar scale $\sigma^{\rm bip}_{rsh}$는 같은 half의 모든 baseline residual
sample로 계산한다. Half-average waveform을 $\bar V$라 할 때

$$
E^{\rm mean}_{r\leftarrow s,h,k}
=\left[\frac1{2|I_k|}\sum_{c\in r}\sum_{t\in I_k}
\left(\frac{\bar V_{c\leftarrow s,h}(t)}{\sigma_{csh}}\right)^2\right]^{1/2},
$$

$$
E^{\rm bip}_{r\leftarrow s,h,k}
=\left[\frac1{|I_k|}\sum_{t\in I_k}
\left(\frac{\bar V_{c_1\leftarrow s,h}(t)-\bar V_{c_2\leftarrow s,h}(t)}
{\sigma^{\rm bip}_{rsh}}\right)^2\right]^{1/2}.
$$

둘 다 무차원이다. 적합 target은 $z=\log(E+10^{-6})$이고 floor도 무차원이다. Nonfinite,
nonpositive scale 또는 빠진 bin은 `APPARATUS_OR_EVOCATION_STOP`이다. Prestimulus matched
control은 같은 폭의 다섯 bin을 $[-250,-140]$ ms 안에 시간 이동해 계산하며 식 선택에는
사용하지 않고 evocation gate에만 쓴다.

## 5. D0 apparatus gate

D0 식 탐색 전에 두 readout 각각에서 다음을 모두 요구한다.

1. 48 directed edges × 5 bins × 2 halves가 모두 정의됨;
2. 48 directed edges의 5-bin 값을 하나로 펼친 pooled repeatability
   $\rho_S(\{E_{e,A,k}\}_{48\times5},\{E_{e,B,k}\}_{48\times5})\ge0.40$;
3. median poststimulus $E$ / median prestimulus-control $E\ge1.25$;
4. 255 cached epochs가 exact range identity와 finite float32 decode를 만족.

실패하면 후보식 적합 없이 stop한다. 이 gate를 본 뒤 bin, floor, site, scale을 바꾸지 않는다.

## 6. 동결된 후보식 문법

$x=t/(50\,\mathrm{ms})$, $r=\ell/(50\,\mathrm{mm})$로 둔다. 모든 exp/log 인자는
무차원이다. $\ell$은 두 bipolar center의 MNI Euclidean distance다. 각 식은 mean과
bipolar readout에 별도로 적합하지만 **식의 구조는 하나**를 선택한다.

### B0: geometry-free temporal baseline

$$
\widehat z=\beta_0+\beta_1\log x+\beta_2x.
$$

### CABLE: exponential distance attenuation

$$
\widehat z=\beta_0+\beta_1\log x+\beta_2x-a r,\qquad a\ge0.
$$

### H-Q: Riemannian short-time heat-kernel truncation

$$
\widehat z=\beta_0-\frac q2\log x-\kappa\frac{r^2}{x}-\lambda x,
\qquad \kappa,\lambda\ge0.
$$

`H-Q1`, `H-Q2`, `H-Q3`, `H-Q4`, `H-Q8`, `H-Q16`은 $q$를 각각 고정한다.
`H-QFREE`는 $q\in[0,20]$을 연속적으로 적합한다. 여기서 $q$는 측정사슬·시간 basis와
섞인 **effective kernel-shape exponent**이며, bridge 없이 신경 상태공간의 차원이라고
부르지 않는다.

### H-PQFREE: anomalous distance exponent

$$
\widehat z=\beta_0-\frac q2\log x-\kappa\frac{r^p}{x}-\lambda x,
\quad q\in[0,20],\ p\in[0.5,4],\ \kappa,\lambda\ge0.
$$

### H-DELAY: finite propagation delay

$$
x'=x-\delta r,
\qquad
\widehat z=\beta_0-\frac q2\log x'-\kappa\frac{r^2}{x'}-\lambda x',
$$

for $x'>0$, with $q\in[0,20]$, $\delta\in[0,0.20]$, $\kappa,\lambda\ge0$.
관측 bin 중 하나라도 $x'\le0$이면 floor로 숨기지 않고 그 fit을 infeasible로 기각한다.
$\delta$의 물리 단위 해석은 ms/mm이며 이 범위는 5 m/s 이상의 apparent speed에 해당한다.

### H-ANISO: diagonal local metric proxy

$$
\ell_g^2=\Delta X^\top G\Delta X,
\qquad
G=\operatorname{diag}(e^{g_x},e^{g_y},e^{-g_x-g_y}),
$$

$$
\widehat z=\beta_0-\frac q2\log x
-\kappa\frac{\ell_g^2/(50\,\mathrm{mm})^2}{x}-\lambda x,
$$

with $g_x,g_y\in[-1.5,1.5]$. Determinant-one 제약은 거리척도와 $\kappa$의 중복을
막는다. 이것은 MNI 좌표 위 diagonal proxy이지 brain-wide metric 복원이 아니다.

### H-DIR-PC: one-axis directed/non-normal correction

24 site centers의 endpoint-blind 첫 principal axis를

$$
u_1=(0.2520471813,-0.7312327918,-0.6338539441)
$$

로 고정한다(좌표분산 설명률 0.69314944). H-QFREE에

$$
+\gamma\,u_1^\top(X_r-X_s)/(50\,\mathrm{mm}),\qquad \gamma\in[-2,2]
$$

를 더한다. 이 항은 reciprocal 방향에서 부호가 바뀌는 저차 directionality proxy이며
Riemannian metric 항이 아니다.

### H-ANISO-DIR와 BIEXP

`H-ANISO-DIR`은 위 anisotropy와 directed PC 항을 함께 둔다. 최대 자유계수는 7이다.
별도 cable/synapse-shape 후보는

$$
\widehat E=10^{-6}+A e^{-ar}
\left[e^{-x'/\theta_d}-e^{-x'/\theta_r}\right]_+,
$$

with $A>0$, $a\ge0$, $x'=x-\delta r$, $0<\theta_r<\theta_d\le4$,
$\delta\in[0,0.20]$이다. `BIEXP`의 score도 $\log\widehat E$에서 계산한다.

총 후보는 B0를 포함해 15개다. Node별 gain, pair별 gain/delay, 24-node low-rank factor,
window 선택, unrestricted symbolic regression은 D0 표본에서 거의 lookup이 되므로 금지한다.

## 7. 적합·score·D0 winner 규칙

잔차 $e=z-\widehat z$에 고정 Huber loss

$$
\rho_{0.5}(e)=
\begin{cases}
e^2/2,&|e|\le0.5,\\
0.5(|e|-0.25),&|e|>0.5
\end{cases}
$$

를 쓴다. Bound-constrained robust least squares는 endpoint 전에 고정한 12개 deterministic
multi-start와 시작점 grid, 허용범위, 최대 반복수를 쓴다. 비선형 후보의 각 fold-fit은
best three admissible starts의 loss가 상대오차 $10^{-4}$ 안이고 prediction RMS 차이가
$10^{-3}$ 이하여야 하며, best fit의 numerical Jacobian이 상대 SVD tolerance $10^{-8}$에서
full column rank이고 condition number가 $10^8$ 이하여야 한다. 자유 structural parameter가
허용범위 폭의 $10^{-4}$ 안으로 경계에 붙은 fit은 식별되지 않은 것으로 센다.

**[Revision 1, actual endpoint 개방 전 수치범위 명시]** 구현의 유한 탐색범위를 다음처럼
고정한다. 이는 fixture 결과나 실제 CCEP endpoint를 본 뒤 정한 값이 아니다.

- intercept $\beta_0$와 BIEXP의 $\log A$: $[-30,30]$;
- B0/CABLE의 $\beta_{\log t},\beta_t$: 각각 $[-50,50]$;
- attenuation/diffusion/decay $a,\kappa,\lambda$: $[0,50]$;
- 앞서 명시한 $q\in[0,20]$, $p\in[0.5,4]$, $g_x,g_y\in[-1.5,1.5]$,
  $\gamma\in[-2,2]$, $\delta\in[0,0.20]$을 유지한다. 지연 fit의 실제 upper bound는
  모든 training cell에서 $x'=x-\delta r>0$이 되도록 이 범위 안에서만 더 줄어든다;
- BIEXP는 $\theta_r\in[0.01,3.9]$와 보조변수 $f\in[0.001,0.999]$를 사용해
  $\theta_d=\theta_r+f(4-\theta_r)$로 parameterize한다. 따라서
  $0<\theta_r<\theta_d<4$가 자동으로 성립한다.

이 upper bound에 닿는 candidate는 성공으로 세지 않고 위 boundary-identifiability gate에서
기각한다. Revision은 math-verifier `1/2`로 기록하며 D0 endpoint는 여전히 unopened이다.

D0의 각 distance stratum에서 salted-hash 순번을 이용해 6 folds(각 fold 4 pairs)를 만든다.
정확히 fold $j$는 네 stratum 각각의 $j$번째 D0 pair 하나씩을 포함한다.
두 방향은 같은 fold다. 한 fold에서 half A의 나머지 pair로 적합해 half B의 held-out pair를
score하고, 반대로 half B로 적합해 half A를 score한다. 이는 edge와 trial-half를 동시에
바꾸지만, 동일 stimulation trial이 여러 receiver pair에 공유된다는 점은 없애지 못한다.

Readout $m$에 대해

$$
I_m=1-\mathcal L_{\rm candidate,m}/\mathcal L_{\rm B0,m}
$$

를 계산한다. 후보는 모든 fold가 finite하고 위 multi-start·Jacobian·경계 식별성 gate를
모든 fold에서 통과하며, bipolar $I_{\rm bip}>0$, 6개 fold 중 최소 4개에서 bipolar
paired loss가 B0보다 작을 때만 생존한다. 생존자 중 $I_{\rm bip}$가 최대인 후보를 고르되,
최대값과 0.01 이내면 자유계수가 적은 후보, 그 다음 lexical name 순으로 고른다. Mean
readout $I_{\rm mean}$은 선택 tie-break에 쓰지 않고 reference sensitivity 진단으로 남긴다.
생존자가 없으면 `D0_NO_GEOMETRIC_EQUATION_SURVIVED`로 stop한다.

## 8. D1/D2/D3 sequential prediction gate

Stage $j$의 prediction은 그 전 stage까지의 endpoint만 사용해 numerical parameter를 적합한
뒤, 아직 열지 않은 stage의 두 halves에 적용한다. 식 구조, bounds, bin, loss, threshold는
D0 winner 이후 바꾸지 않는다.

- D1은 D0-only fit으로 예측한다.
- D1이 통과하면 같은 winner의 숫자만 D0+D1에서 한 번 재적합해 D2를 예측한다.
- D2가 통과하면 숫자만 D0+D1+D2에서 한 번 재적합해 D3를 예측한다.
- 실패 stage의 값을 이용한 구조 변경·재시도는 이 run에서 금지한다.

각 readout에서 observation loss difference를 source stimulation site별로 먼저 평균해
$\Delta_s=\mathcal L_{B0,s}-\mathcal L_{W,s}$를 만든다. 동일 source trial을 여러 edge가
공유하므로 pair를 독립 표본으로 세지 않는다. 고정 seed의 4,096회 source-site cluster
bootstrap은 해당 stage에 실제 등장한 source set을 equal-weight resample해 $\bar\Delta$의
percentile 95% interval을 만든다. Pair와 half를 추가로 iid resample하지 않으며 stage별
`n_source`를 기록한다. 또 stage 안에서 unordered pair의 geometry descriptor tuple

$$
\bigl(r,\Delta X,u_1^\top(X_r-X_s)\bigr)
$$

전체를 joint하게 1,024회 salted permutation한다. Train-stage parameter fit은 고정하고
held-out descriptor tuple만 바꾸어

$$
p_{\rm geom}=\frac{1+\#\{\bar\Delta_{\rm perm}\ge\bar\Delta_{\rm obs}\}}{1025}
$$

를 계산한다. Primary bipolar gate는 세 조건을 모두 요구한다.

1. $\bar\Delta_{\rm bip}>0$;
2. cluster-bootstrap 95% lower bound $>0$;
3. $p_{\rm geom}\le0.05$.

D1 또는 D2가 이 gate를 실패하면 다음 stage를 열지 않는다. Mean readout은 matched
reference diagnostic이며 final label을 나누지만 bipolar gate를 대신하지 않는다.

D3 final label은 같은 규칙으로 한 번만 정한다.

- bipolar와 mean 모두 gate 통과:
  `HELD_OUT_OBSERVED_KERNEL_PREDICTION_PASS_REFERENCE_CONCORDANT`;
- bipolar만 통과:
  `HELD_OUT_OBSERVED_KERNEL_PREDICTION_PASS_REFERENCE_SENSITIVE`;
- bipolar 실패:
  `HELD_OUT_OBSERVED_KERNEL_PREDICTION_NOT_CONFIRMED`.

어떤 pass도 $G$, $L_g$, axonal geodesic 또는 무한차원 manifold의 식별을 뜻하지 않는다.
Pass가 직접 지지하는 문장은 오직 “MNI geometry descriptor를 조건으로 한 제한된 observed
CCEP response prediction이 geometry-free B0보다 해당 held-out stage에서 개선되었다”이다.

## 9. Fixtures, controls와 stop 조건

실제 D0 endpoint 전에 같은 code path로 다음을 통과해야 한다.

1. source lock·range length·wrong hash·marker alignment fail-closed;
2. analytic heat-kernel synthetic에서 generating family가 B0보다 우수하고 D0 selection으로
   복구됨;
3. geometry-independent synthetic에서 geometric candidate false selection $\le7/256$;
4. reference-common-mode injection은 mean만 개선시키고 bipolar primary gate를 속이지 않음;
5. D1 barrier 실패 fixture에서 D2/D3 receipt가 생성되지 않음;
6. split manifest와 fold assignment가 한 pair의 두 방향을 갈라놓지 않음;
7. 모든 exp/log 인자의 무차원성 및 $G\succ0$, $\det G=1$ 확인;
8. pair bootstrap이 아니라 source-cluster bootstrap만 primary interval에 쓰임.

Matched controls는 B0, contact-mean versus bipolar, prestimulus energy, distance-label
permutation, fixed-q versus free-q, symmetric versus directed-PC, isotropic versus diagonal
anisotropic candidate다.

## 10. 뇌/AGI 필수 필드

- **BIO_STARTING_MECHANISM:** $6$ mA, $200\,\mu$s biphasic SPES가 유발한 human iEEG
  CCEP; 짧은 창의 passive/linearized electrical network response.
- **CE_DELTA:** scalar reciprocity proxy 하나가 아니라, 전기 semigroup에서 유도한 여러
  저차 Green/cable/heat 후보식을 endpoint-blind 실제 pair prediction으로 빠르게 제거한다.
- **MEASUREMENT_MODEL:** $C_{\rm ref}R\exp[-C^{-1}(L_g+J_{\rm ion})t]B$ + stimulation
  artifact + common/reference component + noise; mean/bipolar matched readout.
- **DATA_PROVENANCE:** OpenNeuro `ds003708` derivative v1.0.2; exact S3 VersionId/ETag,
  six metadata SHA-256, marker/event crosswalk, 255 version-bound ranges.
- **DATA_SPLIT:** 선행 endpoint-unused 151 pairs를 distance-stratified salted hash로
  D0/D1/D2/D3=`24/48/39/40`; unordered pair와 양방향은 같은 stage.
- **OBSERVABLES:** five-bin dimensionless RMS response energy, prestimulus control,
  half-repeatability, Huber predictive loss, $I_m$, source-cluster $\bar\Delta$/CI,
  geometry-permutation $p$.
- **RESIDUAL_RULE:** log-energy Huber residual; source-trial 공유 때문에 source-site cluster
  aggregate/bootstrap; pair-iid CI 금지.
- **FALSIFIER:** D0 생존식 없음, D1/D2 bipolar sequential gate 실패, 또는 D3 bipolar
  held-out gate 실패면 해당 식 경로를 kill한다.
- **MATCHED_CONTROLS:** B0, mean/bipolar, prestimulus, geometry permutation, fixed/free $q$,
  symmetric/directed, isotropic/anisotropic.
- **MODEL_SELECTION:** D0 6-fold cross-half edge CV 안에서만 15식 구조 선택. 이후 구조
  변경 금지; 통과 stage의 numerical parameter만 다음 예측 전에 누적 재적합.
- **REVISION_TRIGGER:** 실패 stage를 보고 식·window·threshold를 바꾸려면 새 run과 아직
  쓰지 않은 외부 subject/pool이 필요하다. 이 run의 D3가 소비되면 `ds004457` 다환자
  replication만 독립 승격 경로다.
- **CLAIM_CEILING:** SINGLE_SUBJECT_HUMAN_CCEP / ENDPOINT_BLIND_PAIR_DISCOVERY_AND_SEQUENTIAL_HELD_OUT_PREDICTION / OBSERVED_LOW_DIMENSIONAL_RESPONSE_KERNEL_ONLY / NO_AMBIENT_OR_INFINITE_DIMENSIONAL_RIEMANNIAN_METRIC_RECOVERY / NO_AXONAL_GEODESIC_IDENTIFICATION / NO_POPULATION_GENERALIZATION / NO_CONSCIOUSNESS_SELF_HIPPOCAMPUS_OR_AGI_VALIDATION.

## 11. 실행 순서와 불가역성

1. contract → source/math/routes lanes → audit Gate PASS;
2. fixtures와 split manifest receipt;
3. version-bound raw epoch cache 생성·감사 후 D0 endpoint 한 번;
4. D0 winner가 있을 때만 D1;
5. D1 pass일 때만 D2;
6. D2 pass일 때만 D3 one-shot;
7. stable snapshot status audit → validation/final report → ledger/README 순서.

원시 cache는 ignored `data/external/ba_obs_disc1_ds003708/`에 두고 Git 산출물로 취급하지
않는다. 각 stage receipt에는 실제로 계산한 pair list, 이전 receipt SHA-256, code SHA-256,
source range manifest SHA-256, fit parameter, loss, cluster index hash와 permutation index
hash를 기록한다. 뒤 stage가 열리지 않았으면 그 receipt의 부재 자체를 검증한다.
