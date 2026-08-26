# BA-OBS-ID4 연구 계약 — 다환자 CCEP 상호성의 reference-robust 재현

Status: COMPLETE

Mode: full real-brain interventional validation

CE_RUN: `_workspace/ce/brain-human-ccep-reference-robust-replication-20260825`

PREDECESSOR: `_workspace/ce/brain-human-ccep-restricted-active-response-20260824`

Signal state at freeze: OpenNeuro/GitHub snapshot tree와 BIDS metadata만 열었고 MEF3 신호 sample은 열지 않았다.

## 1. 질문과 주장 상한

선행 단일 환자 `ds003708`에서는 A-CAR contact-mean 상호성 proxy가 기각됐지만 bipolar
readout은 기각되지 않아 `REFERENCE_SENSITIVE_OR_INCONCLUSIVE`로 닫혔다. 이번 run은
그 결과를 본 뒤 식이나 창을 맞추지 않고, 사전 지목된 독립 5환자 자료 `ds004457`에서
다음 두 대안을 구별한다.

1. common-reference 성분이 apparent directionality의 주원인이면 bipolar readout의
   reciprocal discrepancy가 contact-mean보다 환자별로 작아진다.
2. 방향성 있는 transfer가 reference에 강건하면 같은 환자에서 contact-mean과 bipolar가
   함께 reciprocal proxy를 기각한다.

이 run은 유한 observed CCEP magnitude의 필요조건 proxy만 시험한다. Riemannian metric,
geodesic, axonal path, ambient neural dimension, 의식, 자아, 기억 또는 AGI는 관측하지 않는다.

## 2. 선행 증거 잠금

| predecessor | evidence | status | 보존 결과 | 재시도 금지 |
|---|---|---|---|---|
| BA-OBS-ID3 | `brain-human-ccep-restricted-active-response-20260824/31-validation.md`; route-ledger ID3 행 | `REFERENCE_SENSITIVE_OR_INCONCLUSIVE` | 단일 환자 A-CAR는 $R=1.8848874$, $p_R=1/8193$였고 bipolar는 $R=1.1852950$, $p_R=674/8193$였다. | `ds003708`의 consumed confirmation, 창, threshold 또는 readout을 재조정하지 않는다. |
| BA-OBS-DISC2R | route-ledger BA-OBS-DISC2R 행; hardened v2 receipt SHA-256 `743f54b7cb35f206b505b8b8f5ebd31e4db5aba5626138dfce220c8fd8b4efeb` | `PASS_FINAL` | 74명 patient-disjoint bipolar observed-kernel에서 단순 Euclidean distance attenuation이 시간 기준식보다 좁게 우수했다. | 그 환자와 endpoint를 독립 재현으로 재사용하거나 biological metric으로 승격하지 않는다. |
| BA-OBS-NOGO1 | route-ledger BA-OBS-NOGO1 행 | local mathematical no-go | finite passive observation은 ambient metric과 dimension을 식별하지 못한다. | finite CCEP matrix를 ambient/infinite-dimensional metric으로 읽지 않는다. |

## 3. 생물 입력, CE proxy와 측정모형

**BIO_STARTING_MECHANISM.** 공개 protocol은 병상 휴식 중 약 $0.2\,\mathrm{Hz}$의
$6\,\mathrm{mA}$, $200\,\mu\mathrm{s}$ biphasic single-pulse stimulation과
$2048\,\mathrm{Hz}$ intracranial recording이다. 자극 site $s$, contact $c$, trial $k$에서

$$
V^{\rm obs}_{c\leftarrow s,k}(t)
=C_{\rm ref}R_c[H_s*u_s](t)+a_{csk}(t)+\eta_{csk}(t)
$$

로 둔다. $H_s$는 causal response, $R_c$는 electrode/volume-conduction readout,
$C_{\rm ref}$는 reference transform, $a$는 stimulation artifact다.

**CE_DELTA / 시험할 proxy P1.** aligned finite input/readout에서 early magnitude matrix를
self-adjoint mobility compression처럼 직접 읽을 수 있다면 필요한 가장 좁은 proxy는

$$
A_{r\leftarrow s}=A_{s\leftarrow r}
$$

이다. P1은 정리가 아니라 **[공리: 모델 선택]**이며, 그 기각은 이 observed proxy만 죽인다.

**MEASUREMENT_MODEL.** 원 MEF3 contact voltage에서 signal-blind good channel만 사용한다.
각 trial baseline에서 stimulated contacts와 bad/non-iEEG channels를 제외하고 channel별
분산을 계산해 낮은 75% channel의 pointwise mean을 common reference로 뺀 값을
`CAR75`라 고정한다. Receiver pair 두 contact의 magnitude 평균이 `mean`, 두 contact를
먼저 뺀 waveform이 `bip`이다. `CAR75` channel 선택은 baseline만 사용하며 post-stimulus
값을 보지 않는다. 이 두 readout은 $H_s$, $R_c$, $C_{\rm ref}$를 분리 식별하지 않는다.

## 4. 데이터 provenance와 용량 계약

- Dataset: OpenNeuro `ds004457`, frozen snapshot `v1.0.2`, DOI
  `10.18112/openneuro.ds004457.v1.0.2`, CC0, BIDS iEEG/MEF3.
- Primary paper: Huang et al., *Journal of Neuroscience* (2023), DOI
  `10.1523/JNEUROSCI.1325-22.2023`.
- Cohort: `sub-1`--`sub-5`, 각 1 CCEP session/run.
- Snapshot tree와 작은 BIDS metadata는 signal 전에 열었다. source lane이 blob content의
  SHA-256, commit/tag identity, protocol과 measurement fields를 별도로 잠근다.
- 전체 dataset, zip, git-annex, MRI/freesurfer derivative와 전체 MEF3 channel을 받지 않는다.
- signal 단계가 허가되면 `.tmet/.tidx`와 필요한 trial-window compressed block만 읽고,
  raw payload는 receipt hash를 계산한 직후 폐기한다. 저장 가능한 것은 metadata manifest,
  byte-range receipt, 소형 endpoint와 결과뿐이다.
- random-window MEF3 decoder가 exact sample/time/unit 검증 fixture를 통과하지 못하면
  `APPARATUS_MEF3_RANDOM_ACCESS_STOP`; 전체 11 GB download로 우회하지 않는다.

## 5. Metadata-only eligibility와 환자 split

환자별 site는 다음을 모두 만족해야 한다.

1. `status=good`, `6.0 mA`, biphasic event가 10개 이상;
2. 두 contact가 channels TSV에서 good iEEG이고 electrodes TSV 좌표가 finite;
3. canonical node는 channels TSV 순서로 정렬한 unordered contact pair다;
4. 같은 canonical node가 두 stimulation polarity label로 나타나면 그 node 전체를 제외한다.

두 node가 contact를 공유하거나 midpoint distance가 $15\,\mathrm{mm}$ 미만이면 unordered
reciprocal pair에서 제외한다. 이 규칙으로 signal을 보지 않고 확인한 후보 수는 환자별
$431,244,502,264,308$개다. `sub-5`에서는 역방향으로 함께 기록된 `RK1-RK2` canonical
node를 제외했다. 이 수치는 endpoint가 아니라 apparatus admissibility다.

환자 순서는

$$
\operatorname{SHA256}(\texttt{ds004457-v1.0.2|subject})
$$

전체 digest의 사전식 순서로 고정한다. `sub-1`, `sub-5`를 development, `sub-4`, `sub-3`,
`sub-2`를 confirmation으로 둔다. Confirmation signal은 development gate 통과 전에는
읽지 않는다. 각 환자 내부 eligible unordered pair는
`SHA256(snapshot|subject|canonical-node-a|canonical-node-b)` 첫 byte로 나누어
$0$--$191$ development/apparatus, $192$--$255$ held-out pair로 고정한다. 환자 confirmation
stage에서는 parameter fitting이나 구조 선택 없이 held-out pair만 최종 판정에 쓴다.

각 site의 good trials은 onset 순 0-based even/odd index로 half A/B에 배정한다.

## 6. 무차원 관측량

**[정밀도 수정 v4: signal 전 lexical-ULP sample-grid 잠금]** BIDS `onset` lexeme는
binary `float`가 아니라 exact decimal $x$로 읽는다. $q=2048x$가 정수이면 그 값을
sample offset으로 채택한다. 정수가 아니면 원문 lexeme의 decimal exponent $e$에서
$b=2048\,10^e/2$ samples를 계산하고, 닫힌 구간 $[q-b,q+b]$에 정수가 정확히 하나
있을 때만 그 정수를 $n_0$로 채택한다. 정수가 없거나 둘 이상이면 fail closed한다.
이는 hash-locked TSV의 마지막 decimal place가 nearest rounding이라는 source-representation
공리를 명시한 것이며 생물학적 timing 정밀도 주장이 아니다. 같은 stimulation site의 두
행이 같은 $n_0$로 매핑되면 순서를 임의로 정하지 않고 fail closed한다. 이 v4 수정은
`sub-5`의 eligible 344행 중 331행을 단순 exact-integrality 규칙이 거부한다는 signal-blind
metadata 반례 뒤 고정했다(예: `415.5825195 s`는 $q=851112.9999360$,
$b=0.0001024$ sample이므로 유일한 $n_0=851113$). 유효 onset은 session sample index
$n_0$로 정렬하며,
microsecond 반올림값을 정렬 진실로 사용하지 않는다. `.tidx` block 선택과 이후 epoch
절단은 sample index로 수행한다. uUTC가 decoder query에 필요한 경우에만 block의
$(t_b,n_b)$에서 rational map

$$
t(n)=t_b+\frac{(n-n_b)10^6}{2048}\;\mu\mathrm{s}
$$

를 쓰고 query 양 끝을 바깥쪽 `floor/ceil`로 넓힌 뒤, 반환된 guard sample을 exact
index로 제거한다. 이 표현 오차는 block 접근용 보수적 guard일 뿐 endpoint 정렬 오차가
아니다. 한 epoch window가 연속한 두 `.tidx` block을 가로지를 때에는 sample index가
정확히 이어지고, **다음 block의 공식 RED flag bit 0 (`0x01`, discontinuity)가 꺼져
있어야 한다.** Block별 `number_of_samples / fs`와 두 integer-uUTC start의 차이를
같다고 강제하지 않는다. 실제 LA1에는 2049-sample block 다음 2047-sample block이
`999999 microseconds` 간격으로 이어지는 flag-clear 경계가 있어, 그 등식은 유효한
sample-contiguous partition을 잘못 거부한다.

Endpoint decoder는 stored sample index 구간과 반환 cardinality/index identity를 직접
검증해야 한다. uUTC uniform-grid reader만 존재하고 sample-index equivalence fixture가
없으면 `APPARATUS_MEF3_SAMPLE_INDEX_STOP`이며 development signal을 열지 않는다.

물리 구간에 sample center가 포함되는 half-open index convention을 고정한다. 따라서
`2048 Hz`에서 acquisition guard `[-500,+50] ms`는
`[n0-1024,n0+103)`, baseline `[-500,-5] ms`는
`[n0-1024,n0-10)`, early `[10,50] ms`는 `[n0+21,n0+103)`,
prestimulus `[-250,-210] ms`는 `[n0-512,n0-430)`이다. 이 수정은 실제
onset `82.52587890625 s * 2048 Hz = 169013 samples`처럼 sample-aligned지만
integer-microsecond가 아닌 유효 event를 보존한다. Window의 물리 의미, split,
threshold, readout과 outcome rule은 바뀌지 않는다.

각 trial에서 $[-500,-5]\,\mathrm{ms}$ baseline mean을 빼고, half 안에서 waveform을
평균한다. 같은 contact/site/half baseline residual SD를 $\sigma_{csh}$라 한다.

$$
Z_{c\leftarrow s}^{(h)}
=\max_{10\,\mathrm{ms}\le t\le50\,\mathrm{ms}}
\frac{|\overline V_{c\leftarrow s}^{(h)}(t)|}{\sigma_{csh}}.
$$

`mean`은 receiver contact 두 개의 $Z$ 평균이고 `bip`은 두 contact 차분 waveform에 같은
연산을 적용한다. Prestimulus control은 $[-250,-210]\,\mathrm{ms}$다. 모두 무차원이다.

$$
d(x,y)=\frac{|x-y|}{x+y+10^{-12}},
$$

$$
u_{rs}=\frac12\left[d(A_{r\leftarrow s}^{A},A_{r\leftarrow s}^{B})
+d(A_{s\leftarrow r}^{A},A_{s\leftarrow r}^{B})\right],
$$

$$
v_{rs}=\frac12\left[d(A_{r\leftarrow s}^{A},A_{s\leftarrow r}^{B})
+d(A_{r\leftarrow s}^{B},A_{s\leftarrow r}^{A})\right],
$$

$$
R_i^{(m)}=\frac{\operatorname{median}v_i^{(m)}+10^{-12}}
{\operatorname{median}u_i^{(m)}+10^{-12}}.
$$

이전과 같은 site/half shared-index trial resampling, log-residual centering과 reciprocal-location
restricted null을 $B=8192$회, root seed `4457`로 계산한다.

$$
p_{R,i}^{(m)}=\frac{1+\#\{b:R_{0,i,b}^{(m)}\ge R_i^{(m)}\}}{8193},
\qquad
\phi_i^{(m)}=\mathbf1\{R_i^{(m)}>1.25,\ p_{R,i}^{(m)}\le0.025\}.
$$

## 7. Gate와 outcome-blind 판정

### 6a. [정의·공리: signal 전 측정 규약 완결 v5]

다음 항목은 관측 결과가 아니라, development signal을 열기 전에 동결한 측정 정의와
모델 선택 공리다. 선행 ID3의 baseline/half/endpoint 구현을 가능한 범위에서 그대로
보존하고 CAR75만 이번 측정모형으로 바꾼다.

1. **[정의: trial 집합과 half]** retained site의 모든 eligible good trial을 onset sample
   $n_0$ 오름차순으로 정렬한다. 같은 `(site,n0)`는 fail closed하며, 0-based 짝수/홀수를
   A/B에 넣는다. 처음 10개로 자르지 않는다.
2. **[공리: per-trial CAR75]** 각 trial의 1014-sample baseline에서 good
   `ieeg/seeg/ecog` channel 중 그 trial의 stimulated 두 contact를 제외한다. 각 channel의
   per-trial baseline sample variance(`ddof=1`)를 구하고, TSV channel order를 보조 순서로
   삼아 낮은 $k=\lfloor0.75M\rfloor$개를 고른다. cutoff 양쪽 variance가 정확히 같으면
   선택을 임의로 깨지 않고 fail closed한다. 선택된 channel의 pointwise 산술평균만 CAR로
   뺀다. 이 mask와 hash는 baseline-only pass에서 잠그며 poststimulus 값은 선택에 쓰지 않는다.
3. **[정의: baseline과 scale]** CAR 뒤 각 channel/trial의 own baseline mean을 뺀 residual을
   $x_{ech}(t)$라 한다. half $h$의 contact scale은 선행 ID3와 같은 population RMS,

$$
\sigma_{csh}=\sqrt{\frac{\sum_{e\in(s,h)}\sum_{t\in B}x_{ec}(t)^2}
{|(s,h)|\,1014}}
$$

   로 고정한다(`ddof=0`). Bipolar는 trial마다 두 baseline-corrected contact를 먼저 빼고
   같은 식을 적용한다. scale이 0 또는 nonfinite이면 fail closed한다.
4. **[정의: 두 readout]** early와 prestim 각각에서 half waveform 평균을 만든다. `mean`은
   receiver 두 contact의 $Z$를 산술평균하고, `bip`은 두 contact 차분 waveform에 한 번
   $Z$를 적용한다. CAR가 bipolar에서 상쇄되지 않으면 구현 오류로 중단한다.
5. **[정의: development gate 모집단]** 각 development 환자의 hash byte 0--191
   `development_apparatus` unordered pair를 양방향으로 펼친 고정 vector에서 readout별로
   half-A와 half-B early response의 표준 Spearman(midrank ties)을 계산한다. constant/nonfinite
   vector는 fail closed한다. Evocation은 같은 directed-edge×half vector에서
   `median(early)/median(prestim)`으로 계산하며 prestim median이 0/nonfinite이면 중단한다.
   두 readout 각각 $\rho\ge0.50$ 및 ratio $\ge1.25$여야 한다. hash byte 192--255
   held-out unordered pair는 이 수치 계산에 넣지 않고 count가 20 이상인지 만 확인한다.
6. **[정의: restricted null 재현]** confirmation에서만, 각 `(site,half)`의 실제 trial 수를
   replacement resample하고 그 draw를 모든 receiver/readout에 공유한다. child RNG는
   `default_rng(int.from_bytes(SHA256("BA-OBS-ID4|confirmation|4457|subject|site|half").digest()[:16],
   "little"))`, $B=8192$로 고정한다. 선행 ID3처럼 bootstrap log residual을 cell별로
   정확히 평균 중심화하고, unordered pair의 네 direction×half observed log 평균을 공통
   reciprocal location으로 둔 뒤 $R_0$ tail을 계산한다. draw-index SHA-256을 receipt에 남긴다.

이 여섯 항목은 **[공리: 측정·수치 규약]**이지 물리 정리가 아니다. 어느 항목도 signal을
본 뒤 바꿀 수 없다.

**Development gate.** `sub-1`, `sub-5` 각각에서 두 readout의 split-half Spearman이
$\ge0.50$, median early/prestimulus가 $\ge1.25$, 모든 planned compressed blocks와
sample/time/unit 검증이 exact, held-out reciprocal pair가 각 $\ge20$이어야 한다. 하나라도
실패하면 confirmation을 열지 않고 apparatus STOP으로 닫는다.

**Confirmation estimands.** 환자별

$$
\Delta_i=\log R_i^{(\rm mean)}-\log R_i^{(\rm bip)}
$$

와 $(\phi_i^{\rm mean},\phi_i^{\rm bip})$를 primary로 둔다. $n=3$이므로 asymptotic
population p-value를 만들지 않는다.

- 세 confirmation 환자 모두 $\Delta_i>0$이고 median $\Delta_i\ge\log(1.25)$이며
  `mean`만 기각한 환자가 2명 이상이면 `REFERENCE_SENSITIVE_PATTERN_REPLICATED`.
- 두 readout이 함께 기각된 환자가 2명 이상이고 어느 환자도 `mean`만 기각하지 않으면
  `REFERENCE_ROBUST_DIRECTIONAL_PROXY_REFUTED`.
- 두 조건 어느 것도 아니면 `HETEROGENEOUS_OR_INCONCLUSIVE`.

Prestimulus에서 같은 label이 나오거나 early/prestimulus gate가 무너지면 scientific label을
발행하지 않고 `MEASUREMENT_CONTROL_STOP`이다. 결과 뒤 threshold, split, reference,
channel set, window 또는 statistic을 바꾸지 않는다.

## 8. 합성 adverse controls

실제 signal 전에 동일 code path가 다음을 통과해야 한다.

1. reciprocal heteroscedastic Gaussian 및 centered-$t_5$ null 256 seeds에서 readout별 false
   refutation $\le7/256$;
2. 최소 75% edge에 $\log(1.6)$ 방향 gap을 준 fixture에서 detection $\ge205/256$;
3. reciprocal latent response에 shared common component만 넣으면 `mean` discrepancy가 커지고
   `bip`에서는 제거되는 reference-artifact fixture;
4. truncated block, wrong metadata hash, nonfinite/zero scale, sample/time/unit mismatch는 endpoint
   전에 fail closed;
5. development failure 뒤 confirmation serialization은 false.

Simulator 통과는 통계·decoder 장치 검증일 뿐 실제 뇌 증거가 아니다.

## 9. 뇌 연구 필수 필드 요약

- **BIO_STARTING_MECHANISM:** human $6\,\mathrm{mA}$, $200\,\mu\mathrm{s}$ biphasic SPES와 early CCEP.
- **CE_DELTA:** aligned observed response의 naive reciprocal/self-adjoint proxy P1.
- **MEASUREMENT_MODEL:** causal response + electrode/volume conduction + CAR75/bipolar reference + artifact + noise.
- **DATA_PROVENANCE:** OpenNeuro `ds004457 v1.0.2`, 5환자 BIDS MEF3; source lane hash lock 전 signal 금지.
- **DATA_SPLIT:** subject-disjoint 2 development / 3 confirmation, 환자 내부 hash-held-out pairs, even/odd trials.
- **OBSERVABLES:** dimensionless early/prestimulus response, split-half repeatability, $u,v,R,p_R,\phi,\Delta$.
- **RESIDUAL_RULE:** shared-index heteroscedastic restricted null과 patient-level fixed labels.
- **FALSIFIER:** 두 reference의 환자별 composite refutation과 사전 고정 population-pattern label.
- **MATCHED_CONTROLS:** CAR75 contact-mean/bipolar, prestimulus, split halves, reference-artifact synthetic control.
- **MODEL_SELECTION:** 없음. 식·window·threshold·split은 고정하고 confirmation에서 적합하지 않는다.
- **REVISION_TRIGGER:** MEF3 apparatus 실패는 decoder/source route만 수리한다. scientific residual 뒤 식을 바꾸려면 새 독립 dataset/epoch와 구조적으로 다른 mechanism이 필요하다.
- **CLAIM_CEILING:** FIVE_SUBJECT_HUMAN_CCEP / FINITE_OBSERVED_RECIPROCITY_REFERENCE_COMPARISON / REAL_INTERVENTIONAL_DATA / NO_BRAIN_METRIC_OR_GEODESIC_IDENTIFICATION / NO_POPULATION_WIDE_GENERALIZATION / NO_CONSCIOUSNESS_SELF_MEMORY_OR_AGI_VALIDATION.

## 10. 실행 순서

contract → source/math/routes → independent audit → metadata/MEF3 decoder fixtures → development
subjects → confirmation subjects once → ledger/docs. Raw payload는 보존하지 않고 receipt와
endpoint만 남긴다.
