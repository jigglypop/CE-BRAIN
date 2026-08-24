# BA-OBS-ID3 최종 보고서 — 실제 인간 CCEP의 제한된 상호성 검증

Status: COMPLETE

Result: REFERENCE_SENSITIVE_OR_INCONCLUSIVE

## 초록

BA-OBS-ID2의 무한차원 metric tomography 정리는 실제 뇌가 제공하지 않는 countably
complete exact oracle를 전제로 하므로, 이번 연구는 인간 뇌에서 관측 가능한 더 작은
필요조건만 시험했다. OpenNeuro `ds003708`의 단일 epilepsy patient CCEP에서 결과를
보기 전에 24개 bipolar sites, 255개 eligible trials, 42 development pairs와 52
confirmation pairs를 동결했다. Development에서 A-CAR contact-mean과 bipolar readout이
모두 반복성·early evocation gate를 통과했다. Confirmation에서는 A-CAR mean이 강한
방향 비대칭을 보였지만 bipolar 대조는 사전 기각 조건을 만족하지 않아 최종 판정은
`REFERENCE_SENSITIVE_OR_INCONCLUSIVE`다. 이는 실제 인간 뇌의 유한 관측응답에 관한
조건부 결과이며, 리만 metric·무한차원·의식·자아·해마 hash 또는 AGI의 검증이 아니다.

## 1. 질문을 실제 측정으로 줄이는 방법

전체 brain state space를 $\mathcal X$라 하고 양의 self-adjoint mobility를
$M=G^{-1}$라 하더라도, electrode가 직접 읽는 것은 $M$이 아니다. 이번 자료의 최소
측정모형은

$$
V_{c\leftarrow s}^{\rm obs}(t)
=C_{\rm ref}R_c[H_s*u_s](t)+a_{cs}(t)+\eta_{cs}(t)
$$

이다. $H_s$는 자극 뒤 causal neural response, $R_c$는 electrode와 volume-conduction
readout, $C_{\rm ref}$는 reference transform, $a$는 stimulation artifact다. 한 관측
전압만으로 이 항들과 $G$를 분리할 수 없다.

**[공리: 시험한 모델 선택 P1]** 같은 24개 bipolar pair를 input과 output 좌표로
정렬한 observed early-magnitude matrix가 하나의 aligned self-adjoint compression을
직접 반영한다면, 가장 좁은 필요조건 후보는

$$
P1:\qquad A_{r\leftarrow s}=A_{s\leftarrow r}
$$

이다. P1은 BA-OBS-ID2에서 산출되는 정리가 아니다. 특히 early maximum, baseline
normalization과 A-CAR contact-magnitude average는 linear operator coefficient가 아니므로
P1의 지위는 처음부터 **naive observed-magnitude reciprocity proxy**로 제한했다.

## 2. 동결한 관측량과 반증식

**[정의]** 각 trial에서 $[-500,-5]\,\mathrm{ms}$ baseline mean을 뺀다. 같은
source/half의 baseline residual SD를 $\sigma_{csh}$라 하고, 첫 $10\,\mathrm{ms}$를
artifact 구간으로 제외한 뒤

$$
Z_{c\leftarrow s}^{(h)}
=\max_{10\le t\le50\,{\rm ms}}
\frac{|\overline V_{c\leftarrow s}^{(h)}(t)|}{\sigma_{csh}}
$$

를 계산했다. Primary A-CAR response는 receiver pair 두 contact의 $Z$ 평균이고,
matched control은 두 contact를 먼저 뺀 bipolar waveform에 같은 계산을 적용한 값이다.
모든 값은 무차원이다.

**[경험식]** 두 양의 response의 차이를

$$
d(x,y)=\frac{|x-y|}{x+y+10^{-12}}
$$

로 두고, 같은 방향 split-half noise와 반대 방향 cross-half 차이를 각각

$$
u_{rs}=\frac12\left[d(A_{r\leftarrow s}^A,A_{r\leftarrow s}^B)
+d(A_{s\leftarrow r}^A,A_{s\leftarrow r}^B)\right],
$$

$$
v_{rs}=\frac12\left[d(A_{r\leftarrow s}^A,A_{s\leftarrow r}^B)
+d(A_{r\leftarrow s}^B,A_{s\leftarrow r}^A)\right]
$$

로 정의했다. Primary discrepancy ratio는

$$
R=\frac{\operatorname{median}v+10^{-12}}
{\operatorname{median}u+10^{-12}}
$$

다.

Raw $R$만 쓰면 두 방향의 noise SD가 다를 때 reciprocal signal도 거짓 기각할 수 있다.
실제로 small-noise 근사에서 그 null ratio는

$$
\frac{\sqrt2\sqrt{\sigma_1^2+\sigma_2^2}}{\sigma_1+\sigma_2}
$$

이며 최대 $\sqrt2$에 접근한다. 그래서 site·half별 실제 trial resampling residual은
그대로 보존하고 네 방향·half의 log-location만 reciprocal하게 맞춘 restricted null
$R_0$를 8,192회 생성했다. Tail area는

$$
p_R=\frac{1+\#\{R_0\ge R_{\rm obs}\}}{8193}
$$

이며 population p-value가 아니라 이 환자와 site set에 조건부인 resampling tail이다.
각 readout에서 $R>1.25$와 $p_R\le0.025$가 동시에 성립하고, 두 readout이 모두 그
조건을 만족할 때만 reference-robust P1 기각으로 동결했다.

## 3. Source와 split

자료는 OpenNeuro `ds003708` derivative v1.0.2의 $2048\,\mathrm{Hz}$, 89-channel
BrainVision iEEG다. S3 object length, multipart ETag, VersionId와 events, channels,
electrodes, VHDR, VMRK, derivative README의 SHA-256을 먼저 고정했다. Raw anchor는
BrainVision marker position minus one이며 425 events와 marker의 off-by-one crosswalk도
decode 전에 검사했다.

Signal-independent eligibility 뒤 24 sites와 245 unordered pairs가 남았다. Frozen
site-list index order로 hash를 계산해 calibration/development/confirmation을
151/42/52로 나눴다. Calibration endpoint는 식 선택에 사용하지 않았다. 255개 eligible
epoch를 version-bound HTTP range로 읽었고 총 139,528,860 bytes의 각 range에서 status
206, exact Content-Range, ETag, VersionId, byte count와 SHA-256을 기록했다.

## 4. 구현 전 반례와 apparatus 검증

합성 gate는 원 통계가 실제로 취약한 조건과 교정 통계의 방어력을 함께 검사했다.

| synthetic condition | Gaussian | centered $t_5$ | frozen gate |
|---|---:|---:|---|
| reciprocal, heteroscedastic composite false refutation | 1/256 | 0/256 | 각 $\le7/256$ — PASS |
| uncalibrated raw $R>1.25$, mean | 61/256 | 61/256 | 적어도 한 사례 필요 — PASS |
| uncalibrated raw $R>1.25$, bipolar | 80/256 | 62/256 | 적어도 한 사례 필요 — PASS |
| directed $\log(1.6)$ power | 256/256 | 256/256 | 각 $\ge205/256$ — PASS |

이 결과는 restricted-null 구현의 false-positive와 power sanity check일 뿐 실제 뇌의
증거가 아니다. 별도 손계산 fixture는 contract의 cross-half $v$가 same-half 구현과
실제로 다른 값을 내는지 고정했다.

Development 42 pairs에서는 두 readout 모두 사전 gate를 넘었다.

| readout | split-half Spearman | median early / prestimulus | directed endpoints | result |
|---|---:|---:|---:|---|
| A-CAR contact-mean | 0.6267085 | 1.9538596 | 84 | PASS |
| bipolar difference | 0.5180520 | 1.3527095 | 84 | PASS |

따라서 자극 유발반응과 최소 반복성은 확인됐고 confirmation 계산이 허가됐다.

## 5. 실제 인간 뇌 confirmation

**[경험 결과]** 52 confirmation pairs와 8,192 restricted-null resamples의 결과는
다음과 같다.

| readout | $R_{\rm obs}$ | null tail count | $p_R$ | $R>1.25$ | $p_R\le0.025$ |
|---|---:|---:|---:|---:|---:|
| A-CAR contact-mean | 1.8848874 | 0 | 0.0001220554 | yes | yes |
| bipolar difference | 1.1852950 | 673 | 0.08226535 | no | no |

A-CAR contact-mean에서는 reciprocal 방향 차이가 split-half noise에 비해 크고 restricted
null과도 양립하기 어려웠다. 그러나 common component를 제거하는 bipolar readout에서는
raw effect threshold와 conditional tail threshold를 모두 넘지 못했다. 두 readout의
indicator가 각각 true와 false이므로, 동결 규칙에 따른 유일한 판정은

$$
\boxed{\texttt{REFERENCE\_SENSITIVE\_OR\_INCONCLUSIVE}}
$$

이다.

## 6. 무엇이 실패했고 무엇이 남았는가

이 결과는 P1을 reference-robust하게 기각하지 못했다. 동시에 P1을 지지하지도 않는다.
관측된 A-CAR 비대칭이 neural directionality인지, common-reference/volume-conduction
성분인지, contact-magnitude aggregation의 결과인지는 이번 한 자료로 분리되지 않는다.
Bipolar에서 효과가 약해졌다는 사실은 measurement model을 생략하고 observed matrix를
self-adjoint mobility로 직접 읽는 것이 위험하다는 실증적 경고다.

**[미완성]** 다음 항목은 전혀 닫히지 않았다.

1. 여러 환자에서 같은 reference-sensitive pattern이 재현되는가;
2. signed waveform 또는 transfer-function 수준에서도 reciprocity가 깨지는가;
3. 여러 stimulation amplitude에서 선형 regime이 존재하는가;
4. 합·차 active query로 polarization identity를 실제 구현할 수 있는가;
5. finite observed response에서 ambient/infinite-dimensional $G$를 식별할 추가 가정은
   무엇인가;
6. low-dimensional present-world manifold, 의식, 자아의 시간 경로 또는 해마 hash가
   이 전기생리량과 어떤 식으로 연결되는가.

**[예측: 다음 독립 판본]** `ds004457` 다환자 CCEP를 새 source lock과 독립 split로
사전등록할 때, A-CAR 비대칭이 common-reference 영향이라면 bipolar effect가 환자마다
체계적으로 더 작아야 한다. 반대로 두 reference에서 같은 signed transfer asymmetry가
반복되면 naive self-adjoint observed-response proxy에 더 강한 반증이 된다. 어느 경우도
그 자체로 brain metric의 존재나 부재를 증명하지 않는다.

## 7. 실패 이력의 감사

이번 run은 숫자를 성공으로 고쳐 쓰지 않고 구현 오류를 분리했다.

1. 첫 scalar synthetic fixture의 30/256, 17/256 stop은 actual site mapping과 두
   readout을 구현하지 않아 `IMPLEMENTATION_INVALID`로 폐기했다.
2. 첫 unversioned range 시도는 endpoint나 receipt를 만들기 전에 종료했고 어떤
   development/confirmation도 허가하지 않았다.
3. 첫 confirmation은 $v$를 same-half로 잘못 indexing해 `IMPLEMENTATION_INVALID`로
   폐기했다.
4. 최종 수치는 cross-half regression fixture, corrected synthetic gate, development
   barrier, version-bound 255-range reacquisition SHA match 뒤 한 번 직렬화한 결과다.

이 이력 때문에 최종 결론의 강도가 높아지는 것은 아니다. 다만 어떤 숫자가 유효하고
어떤 숫자가 폐기됐는지는 재현 가능하게 구분된다.

## 8. 재현 경로와 증거

실행 entry point는 `artifacts/ba_obs_id3.py`이며 Windows system Python은
`.codex/hooks/python.cmd`로 고정했다. Current implementation SHA-256은
`239861b1c78c671ad5f57d6906451a12a57cf8ec3581a09829a4e6061374bd3b`다.
유효 실행 순서는 `fixtures` → `source-plan` → `real-development` → `range-audit` →
`confirmation`이었다. 이 run의 confirmation은 이미 소비됐으므로 같은 run을 retune하거나
다시 confirmation하는 대신 후속 연구를 새 계약으로 만든다.

핵심 receipt는 다음과 같다.

- `artifacts/fixture-receipt.json`;
- `artifacts/source-plan-receipt.json`;
- `artifacts/real-development-receipt.json`;
- `artifacts/range-audit-receipt.json`;
- `artifacts/confirmation-receipt.json`.

Confirmation의 ordered reacquisition-record SHA-256은
`ccc18836493d7c52117faeb11210c13371c53683dd697e321788abb0e899f2ea`, shared
resampling-index SHA-256은
`352d4ed84f4c8bc86b3563ebbbca6d2e19e91230b459eb9c76af5453f07982db`다.
전체 pytest는 실행하지 않았다. 변경된 독립 연구 artifact에 대해 source parse,
동결 synthetic gate, real development, range audit, confirmation과 `git diff --check`만
실행했다.

## 참고문헌

1. OpenNeuro, `ds003708` v1.0.2, DOI
   [10.18112/openneuro.ds003708.v1.0.2](https://doi.org/10.18112/openneuro.ds003708.v1.0.2),
   accessed 2026-08-24.
2. Miller, Müller, Hermes, “Basis profile curve identification to understand electrical
   stimulation effects in human brain networks,” *PLoS Computational Biology* (2021),
   [doi:10.1371/journal.pcbi.1008710](https://doi.org/10.1371/journal.pcbi.1008710),
   accessed 2026-08-24.
3. Keller et al., “Corticocortical evoked potentials reveal projectors and integrators in
   human brain networks,” *Journal of Neuroscience* (2014),
   [doi:10.1523/JNEUROSCI.4289-13.2014](https://doi.org/10.1523/JNEUROSCI.4289-13.2014),
   accessed 2026-08-24.
