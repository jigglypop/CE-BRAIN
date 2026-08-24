# BA-OBS-DISC1 source lane — 인간 CCEP 전기 response kernel

Status: COMPLETE

## Source question

실제 인간 단일펄스 전기자극 반응을 짧은 시간의 선형 전기 Green function으로 근사하고,
거리·지연·reference가 포함된 제한된 후보식을 비교할 근거가 있는지 확인했다. 아래 source는
후보 문법을 허용할 뿐, 어떤 후보가 실제 뇌에서 참이라는 결론을 미리 주지 않는다.

## Primary and official sources

| claim | primary/official source | admitted use | boundary |
|---|---|---|---|
| 수상돌기·축삭의 passive cable은 membrane RC와 axial conductance에서 전압 확산식을 얻는다. | Rall, *Core Conductor Theory and Cable Properties of Neurons* (1977), [DOI 10.1002/j.2040-4603.1977.tb00811.x](https://doi.org/10.1002/j.2040-4603.1977.tb00811.x); Rall (1959), [DOI 10.1016/0014-4886(59)90046-9](https://doi.org/10.1016/0014-4886(59)90046-9) | $C\dot v=-(L_g+J_{\rm ion})v+Bu$의 passive/operating-point linearization 출발점 | whole-brain fixed linear law가 아니다. $J_{\rm ion}$은 상태·전압·시간에 의존할 수 있다. |
| 연결을 scalar 하나가 아니라 stimulus-history에 대한 response function/Green function으로 다룰 수 있다. | Randi & Leifer, *Measuring and modeling nonlinear neural dynamics...* (2021), [DOI 10.1103/PhysRevLett.126.118102](https://doi.org/10.1103/PhysRevLett.126.118102) | $H(t)=C_{\rm ref}R e^{-At}B$ 및 convolutional measurement grammar | C. elegans 맥락이며 인간 CCEP나 Riemannian metric의 실증이 아니다. 비선형·시간변화가 남는다. |
| weighted graph Laplacian의 heat semigroup은 $e^{-tL}$이다. | Zhang & Hancock (2008), [DOI 10.1016/j.patcog.2008.05.007](https://doi.org/10.1016/j.patcog.2008.05.007) | $e^{-tL_g}$와 short-time heat-kernel 후보 | CCEP가 순수 diffusion이라는 생리학적 증거가 아니라 비교식의 수학적 근거다. |
| neural-field 모델은 synaptic/propagation delay를 명시적으로 분리한다. | Veltz, *Interplay between synaptic delays and propagation delays...*, [DOI 10.1137/120889253](https://doi.org/10.1137/120889253) | $t-d/v$ delay와 rise–decay candidate | fitted delay는 자극 artifact·measurement delay와 혼동될 수 있다. |
| EEG/iEEG reference와 volume conduction은 공통 성분 및 zero-lag 관계를 바꾼다. | Anastasiadou et al. (2019), [DOI 10.3389/fnins.2019.00221](https://doi.org/10.3389/fnins.2019.00221) | contact-mean과 bipolar matched readout, $C_{\rm ref}R$ nuisance | bipolar는 distant/common signal도 제거할 수 있으므로 “ground truth”가 아니다. |
| `ds003708`은 한 환자의 single-pulse intracranial EEG/CCEP 공개자료다. | [OpenNeuro dataset repository](https://github.com/OpenNeuroDatasets/ds003708), [dataset DOI 10.18112/openneuro.ds003708.v1.0.0](https://doi.org/10.18112/openneuro.ds003708.v1.0.0), 원 연구 [DOI 10.1101/2021.01.24.428020](https://doi.org/10.1101/2021.01.24.428020) | 200 μs biphasic pulse, 통상 6 mA, 약 0.2 Hz의 실제 인간 intervention source | 한 환자·임상 electrode 배치다. population law나 consciousness 자료가 아니다. |

표의 DOI는 dataset family의 공개 인용이다. 이번 derivative v1.0.2 signal object의 exact
identity는 DOI 문자열이 아니라 계약에 고정한 S3 VersionId, ETag, byte length와 metadata
SHA-256가 담당한다.

## Source-rooted measurement model

허용되는 가장 강한 출발문은

$$
C\dot v=-(L_g+J_{\rm ion})v+Bu,
\qquad
y=C_{\rm ref}R v+a_{\rm stim}+c_{\rm common}+\eta
$$

이다. 첫 식은 short-window local linearization이고 둘째 식은 reference·volume conduction을
포함한 관측사슬이다. 실제 CCEP로 바로 식별되는 것은 $L_g$ 또는 $J_{\rm ion}$이 아니라
$C_{\rm ref}R e^{-C^{-1}(L_g+J_{\rm ion})t}C^{-1}B$의 제한된 readout이다.

## Admitted and prohibited inference

- **admitted:** cable attenuation, heat/diffusion, finite delay, two-timescale response,
  anisotropic MNI geometry, one-axis directionality를 서로 경쟁시키는 것;
- **admitted:** 아직 endpoint를 계산하지 않은 pair에서 geometry-conditioned prediction을
  geometry-free temporal baseline과 비교하는 것;
- **prohibited:** MNI Euclidean distance를 axonal geodesic이라고 부르는 것;
- **prohibited:** fitted $q$를 뇌 또는 의식의 실제 차원으로 동일시하는 것;
- **prohibited:** 한 환자의 pass/fail을 인간 일반, 무한차원 metric, 자아 또는 AGI로 승격하는 것.

## Source-lane disposition

`SOURCE_SUPPORTED_CANDIDATE_GRAMMAR / EMPIRICAL_SELECTION_REQUIRED`.
전기 semigroup과 measurement nuisance를 함께 포함한 후보 비교는 허용한다. 어느 식이
살아남는지는 D0 이후에만 알 수 있다.
